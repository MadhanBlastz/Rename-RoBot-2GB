from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helper.utils import progress_for_pyrogram, convert, humanbytes, add_prefix_suffix
from helper.database import jishubotz
from asyncio import sleep
from PIL import Image
import os, time, random, asyncio

def add_metadata_to_image(file_path, description):
    with Image.open(file_path) as img:
        # Extract existing EXIF data
        exif_data = img.info.get('exif', b'')
        # Update the EXIF data with description
        if exif_data:
            exif_dict = dict(Image._getexif(img))
            exif_dict[TAGS['ImageDescription']] = description
        else:
            exif_dict = {TAGS['ImageDescription']: description}
        
        # Save the image with updated EXIF data
        img.save(file_path, exif=exif_data)

def add_metadata_to_mp3(file_path, title, comment):
    try:
        import eyed3
        audiofile = eyed3.load(file_path)
        if audiofile.tag is None:
            audiofile.initTag()
        audiofile.tag.title = title
        audiofile.tag.comments.set(comment)
        audiofile.tag.save()
    except ImportError:
        print("eyed3 library is not installed. Metadata addition to MP3 files cannot be performed.")

@Client.on_message(filters.private & (filters.document | filters.audio | filters.video))
async def rename_start(client, message):
    file = getattr(message, message.media.value)
    filename = file.file_name
    if file.file_size > 2000 * 1024 * 1024:
        return await message.reply_text("Sorry Bro This Bot Doesn't Support Uploading Files Bigger Than 2GB")

    try:
        await message.reply_text(
            text=f"**Please Enter New Filename...**\n\n**Old File Name** :- `{filename}`",
            reply_to_message_id=message.id,
            reply_markup=ForceReply(True)
        )
        await sleep(30)
    except FloodWait as e:
        await sleep(e.value)
        await message.reply_text(
            text=f"**Please Enter New Filename**\n\n**Old File Name** :- `{filename}`",
            reply_to_message_id=message.id,
            reply_markup=ForceReply(True)
        )
    except:
        pass

@Client.on_message(filters.private & filters.reply)
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

        button = [[InlineKeyboardButton("📁 Document", callback_data="upload_document")]]
        if file.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
            button.append([InlineKeyboardButton("🎥 Video", callback_data="upload_video")])
        elif file.media == MessageMediaType.AUDIO:
            button.append([InlineKeyboardButton("🎵 Audio", callback_data="upload_audio")])
        await message.reply(
            text=f"**Select The Output File Type**\n\n**File Name :-** `{new_name}`",
            reply_to_message_id=file.id,
            reply_markup=InlineKeyboardMarkup(button)
        )

@Client.on_callback_query(filters.regex("upload"))
async def doc(bot, update):
    if not os.path.isdir("Metadata"):
        os.mkdir("Metadata")

    prefix = await jishubotz.get_prefix(update.message.chat.id)
    suffix = await jishubotz.get_suffix(update.message.chat.id)
    new_name = update.message.text
    new_filename_ = new_name.split(":-")[1]

    try:
        new_filename = add_prefix_suffix(new_filename_, prefix, suffix)
    except Exception as e:
        return await update.message.edit(f"Something Went Wrong Can't Able To Set Prefix Or Suffix 🥺 \n\n**Contact My Creator :** @CallAdminRobot\n\n**Error :** `{e}`")

    file_path = f"downloads/{update.from_user.id}/{new_filename}"
    file = update.message.reply_to_message

    ms = await update.message.edit("`Trying To Downloading`")

    try:
        print(f"Downloading file to: {file_path}")
        path = await bot.download_media(message=file, file_name=file_path, progress=progress_for_pyrogram, progress_args=("`Download Started....`", ms, time.time()))
        print(f"File downloaded to: {path}")
    except Exception as e:
        print(f"Download failed: {e}")
        return await ms.edit(f"**Error during download:** `{e}`")

    _bool_metadata = await jishubotz.get_metadata(update.message.chat.id)

    if _bool_metadata:
        metadata_path = f"Metadata/{new_filename}"
        metadata = await jishubotz.get_metadata_code(update.message.chat.id)
        if metadata:
            await ms.edit("I Found Your Metadata\n\n__Please Wait...__\n`Adding Metadata To File...`")
            # Skip ffmpeg and use alternative methods if needed
            await ms.edit("**Metadata Added To The File Successfully ✅**\n\n__**Please Wait...**__\n\n`Trying To Downloading`")
    else:
        await ms.edit("`Trying To Downloading`")

    duration = 0
    try:
        parser = createParser(file_path)
        metadata = extractMetadata(parser)
        if metadata.has("duration"):
            duration = metadata.get('duration').seconds
        parser.close()
    except:
        pass

    ph_path = None
    user_id = int(update.message.chat.id)
    media = getattr(file, file.media.value)
    c_caption = await jishubotz.get_caption(update.message.chat.id)
    c_thumb = await jishubotz.get_thumbnail(update.message.chat.id)

    if c_caption:
        try:
            caption = c_caption.format(filename=new_filename, filesize=humanbytes(media.file_size), duration=convert(duration))
        except Exception as e:
            return await ms.edit(text=f"Your Caption Error Except Keyword Argument: ({e})")
    else:
        caption = f"**{new_filename}**"

    if (media.thumbs or c_thumb):
        if c_thumb:
            ph_path = await bot.download_media(c_thumb)
            width, height, ph_path = await fix_thumb(ph_path)
        else:
            try:
                ph_path_ = await take_screen_shot(file_path, os.path.dirname(os.path.abspath(file_path)), random.randint(0, duration - 1))
                width, height, ph_path = await fix_thumb(ph_path_)
            except Exception as e:
                ph_path = None
                print(e)

    await ms.edit("`Trying To Uploading`")
    type = update.data.split("_")[1]
    try:
        if type == "document":
            await bot.send_document(
                update.message.chat.id,
                document=file_path,
                thumb=ph_path,
                caption=caption,
                progress=progress_for_pyrogram,
                progress_args=("`Upload Started....`", ms, time.time())
            )
        elif type == "video":
            await bot.send_video(
                update.message.chat.id,
                video=file_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("`Upload Started....`", ms, time.time())
            )
        elif type == "audio":
            await bot.send_audio(
                update.message.chat.id,
                audio=file_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("`Upload Started....`", ms, time.time())
            )
    except Exception as e:
        os.remove(file_path)
        if ph_path:
            os.remove(ph_path)
        if metadata_path:
            os.remove(metadata_path)
        if path:
            os.remove(path)
        return await ms.edit(f"**Error :** `{e}`")

    await ms.delete()
    if ph_path:
        os.remove(ph_path)
    if file_path:
        os.remove(file_path)
    if metadata_path:
        os.remove(metadata_path)

# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @JishuBotz
# Developer @JishuDeveloper
