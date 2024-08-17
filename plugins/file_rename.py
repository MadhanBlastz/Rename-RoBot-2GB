import asyncio
from pyrogram import Client, filters, enums
from pyrogram.enums import MessageMediaType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply

from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

from helper.utils import progress_for_pyrogram, convert, humanbytes
from helper.database import db
from PIL import Image
import os
import time


@Client.on_callback_query(filters.regex('rename'))
async def rename(bot, update):
    user_id = update.data.split('-')[1]
    
    if int(user_id) not in [update.from_user.id, 0]:
        return await update.answer(f"⚠️ Hᴇʏ {update.from_user.first_name}\nTʜɪs ɪs ɴᴏᴛ ʏᴏᴜʀ ғɪʟᴇ ʏᴏᴜ ᴄᴀɴ'ᴛ ᴅᴏ ᴀɴʏ ᴏᴘᴇʀᴀᴛɪᴏɴ", show_alert=True)

    await update.message.delete()
    await update.message.reply_text("__𝙿𝚕𝚎𝚊𝚜𝚎 𝙴𝚗𝚝𝚎𝚛 𝙽𝚎𝚠 𝙵𝚒𝚕𝚎𝙽𝚊𝚖𝚎...__", reply_to_message_id=update.message.reply_to_message.id, reply_markup=ForceReply(True))

@Client.on_message((filters.private | filters.group) & filters.reply)
async def refunc(client, message):
    reply_message = message.reply_to_message
    if (reply_message.reply_markup) and isinstance(reply_message.reply_markup, ForceReply):
        new_name = message.text
        await message.delete()
        msg = await client.get_messages(message.chat.id, reply_message.id)
        file = msg.reply_to_message
        media = getattr(file, file.media.value)
        if not "." in new_name:
            if "." in media.file_name:
                extn = media.file_name.rsplit('.', 1)[-1]
            else:
                extn = "mkv"
            new_name = new_name + "." + extn
        await reply_message.delete()

        button = [[InlineKeyboardButton(
            "📁 Dᴏᴄᴜᴍᴇɴᴛ", callback_data="upload_document")]]
        if file.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
            button.append([InlineKeyboardButton(
                "🎥 Vɪᴅᴇᴏ", callback_data="upload_video")])
        elif file.media == MessageMediaType.AUDIO:
            button.append([InlineKeyboardButton(
                "🎵 Aᴜᴅɪᴏ", callback_data="upload_audio")])
        await message.reply_text(
            text=f"<b>Sᴇʟᴇᴄᴛ Tʜᴇ Oᴜᴛᴩᴜᴛ Fɪʟᴇ Tyᴩᴇ</b>\n<b>• Fɪʟᴇ Nᴀᴍᴇ :-</b><code>{new_name}</code>",
            reply_to_message_id=file.id,
            reply_markup=InlineKeyboardMarkup(button)
        )


@Client.on_callback_query(filters.regex("upload"))
async def doc(bot, update):
    
    if not os.path.isdir("Metadata"):
        os.mkdir("Metadata")

    new_name = update.message.text
    new_filename = new_name.split(":-")[1].strip()
    file_path = f"Renames/{new_filename}"
    metadata_path = f"Metadata/{new_filename}"
    file = update.message.reply_to_message

    ms = await update.message.edit("⚠️__**Please wait...**__\n**Tʀyɪɴɢ Tᴏ Dᴏᴡɴʟᴏᴀᴅɪɴɢ....**")
    try:
        dl = await bot.download_media(message=file, file_name=file_path, progress=progress_for_pyrogram, progress_args=("\n⚠️__**Please wait...**__\n\n☃️ **Dᴏᴡɴʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ....**", ms, time.time()))
    except Exception as e:
        return await ms.edit(f"Download failed: {e}")

    duration = 0
    try:
        metadata = extractMetadata(createParser(file_path))
        if metadata.has("duration"):
            duration = metadata.get('duration').seconds
    except Exception as e:
        return await ms.edit(f"Metadata extraction failed: {e}")
        
    ph_path = None
    user_id = update.from_user.id
    media = getattr(file, file.media.value)
    c_caption = await db.get_caption(user_id)
    c_thumb = await db.get_thumbnail(user_id)

    if c_caption:
        try:
            caption = c_caption.format(filename=new_filename, filesize=humanbytes(media.file_size), duration=convert(duration))
        except Exception as e:
            return await ms.edit(text=f"Yᴏᴜʀ Cᴀᴩᴛɪᴏɴ Eʀʀᴏʀ Exᴄᴇᴩᴛ Kᴇʏᴡᴏʀᴅ Aʀɢᴜᴍᴇɴᴛ ●> ({e})")
    else:
        caption = f"**{new_filename}**"

    if (media.thumbs or c_thumb):
        if c_thumb:
            ph_path = await bot.download_media(c_thumb)
        else:
            ph_path = await bot.download_media(media.thumbs[0].file_id)
        Image.open(ph_path).convert("RGB").save(ph_path)
        img = Image.open(ph_path)
        img.resize((320, 320))
        img.save(ph_path, "JPEG")

    await ms.edit("__**Pʟᴇᴀsᴇ Wᴀɪᴛ...**__\n**Fᴇᴛᴄʜɪɴɢ Mᴇᴛᴀᴅᴀᴛᴀ....**")
    metadat = await db.get_metadata(user_id)
    
    if metadat:
        await ms.edit("I Fᴏᴜɴᴅ Yᴏᴜʀ Mᴇᴛᴀᴅᴀᴛᴀ\n\n__**Pʟᴇᴀsᴇ Wᴀɪᴛ...**__\n**Aᴅᴅɪɴɢ Mᴇᴛᴀᴅᴀᴛᴀ Tᴏ Fɪʟᴇ....**")
        cmd = f"""ffmpeg -i "{dl}" {metadat} "{metadata_path}" """

        process = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
            
        stdout, stderr = await process.communicate()
        er = stderr.decode()

        if er:
            return await ms.edit(f"FFmpeg error: {er}")

    # Validate the metadata file
    if os.path.exists(metadata_path):
        file_size = os.path.getsize(metadata_path)
        if file_size > 0:
            await ms.edit(f"File size: {humanbytes(file_size)}\nFile is valid. Proceeding to upload...")
        else:
            return await ms.edit("Error: Metadata file is empty or corrupted.")
    else:
        return await ms.edit("Error: Metadata file does not exist.")

    await ms.edit("Mᴇᴛᴀᴅᴀᴛᴀ ᴀᴅᴅᴇᴅ ᴛᴏ ᴛʜᴇ ғɪʟᴇ sᴜᴄᴄᴇssғᴜʟʟʏ ✅\n\n⚠️__**Please wait...**__\n**Tʀyɪɴɢ Tᴏ Uᴩʟᴏᴀᴅɪɴɢ....**")

    type = update.data.split("_")[1]

    try:
        # Attempt upload with retries
        for attempt in range(3):  # Retry 3 times
            try:
                print("Attempting to upload file...")
                if type == "document":
                    await bot.send_document(
                        update.from_user.id,
                        document=metadata_path,
                        thumb=ph_path,
                        caption=caption,
                        progress=progress_for_pyrogram,
                        progress_args=("⚠️__**Please wait...**__\n🌨️ **Upload Started....**", ms, time.time())
                    )
                elif type == "video":
                    await bot.send_video(
                        update.from_user.id,
                        video=metadata_path,
                        duration=duration,
                        thumb=ph_path,
                        caption=caption,
                        supports_streaming=True,
                        progress=progress_for_pyrogram,
                        progress_args=("⚠️__**Please wait...**__\n🌨️ **Upload Started....**", ms, time.time())
                    )
                elif type == "audio":
                    await bot.send_audio(
                        update.from_user.id,
                        audio=metadata_path,
                        duration=duration,
                        thumb=ph_path,
                        caption=caption,
                        progress=progress_for_pyrogram,
                        progress_args=("⚠️__**Please wait...**__\n🌨️ **Upload Started....**", ms, time.time())
                    )
                print("File uploaded successfully!")
                await ms.edit("File uploaded successfully!")
                break
            except Exception as e:
                print(f"Upload attempt {attempt + 1} failed with error: {e}")
                if attempt == 2:  # If it's the last attempt, show the error to the user
                    await ms.edit(f"Upload failed: {e}")
                    break
                await asyncio.sleep(5)  # Wait 5 seconds before retrying
    except asyncio.TimeoutError:
        print("Upload timed out.")
        await ms.edit("Upload timed out. Please try again.")
    except Exception as e:
        print(f"Upload failed with error: {e}")
        await ms.edit(f"Upload failed: {e}")
    finally:
        try:
            os.remove(dl)
            os.remove(metadata_path)
            os.remove(ph_path)
        except:
            pass
        
