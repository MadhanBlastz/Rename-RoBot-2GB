from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from helper.utils import progress_for_pyrogram, convert, humanbytes, add_prefix_suffix
from helper.database import jishubotz
from mutagen.mp4 import MP4, MP4Cover
from mutagen.mp3 import EasyMP3
from mutagen.id3 import ID3, COMM
from asyncio import sleep
import os, time, random, asyncio


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

        button = [[InlineKeyboardButton("📁 Document", callback_data = "upload_document")]]
        if file.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
            button.append([InlineKeyboardButton("🎥 Video", callback_data = "upload_video")])
        elif file.media == MessageMediaType.AUDIO:
            button.append([InlineKeyboardButton("🎵 Audio", callback_data = "upload_audio")])
        await message.reply(
            text=f"**Select The Output File Type**\n\n**File Name :-** `{new_name}`",
            reply_to_message_id=file.id,
            reply_markup=InlineKeyboardMarkup(button)
        )


@Client.on_callback_query(filters.regex("upload"))
async def doc(bot, update):    
    # Creating Directory for Metadata
    if not os.path.isdir("Metadata"):
        os.mkdir("Metadata")
        
    # Extracting necessary information    
    prefix = await jishubotz.get_prefix(update.message.chat.id)
    suffix = await jishubotz.get_suffix(update.message.chat.id)
    new_name = update.message.text
    new_filename_ = new_name.split(":-")[1]

    try:
        new_filename = add_prefix_suffix(new_filename_, prefix, suffix)
    except Exception as e:
        return await update.message.edit(f"Something Went Wrong Can't Set Prefix Or Suffix 🥺 \n\n**Contact My Creator :** @CallAdminRobot\n\n**Error :** `{e}`")
    
    file_path = f"downloads/{update.from_user.id}/{new_filename}"
    file = update.message.reply_to_message

    ms = await update.message.edit("`Trying To Download`")    
    try:
        path = await bot.download_media(message=file, file_name=file_path, progress=progress_for_pyrogram, progress_args=("`Download Started....`", ms, time.time()))                    
    except Exception as e:
        return await ms.edit(f"Download failed: {e}")
     
    # Adding metadata without FFmpeg
    try:
        if file.media == MessageMediaType.AUDIO:
            audio = EasyMP3(path)
            audio['title'] = new_filename
            audio['artist'] = '@AniMovieRulz'
            audio.save()
        elif file.media == MessageMediaType.VIDEO:
            video = MP4(path)
            video["\xa9nam"] = new_filename
            video["\xa9cmt"] = '@AniMovieRulz'
            video.save()

        await ms.edit("**Metadata Added To The File Successfully ✅**\n\n`Trying To Download`")
    except Exception as e:
        await ms.edit(f"Metadata addition failed: {e}\n\nProceeding with renaming only.")
        pass

    # Proceed with the upload...
    await ms.edit("`Trying To Upload`")
    try:
        if update.data == "upload_document":
            await bot.send_document(
                update.message.chat.id,
                document=path,
                caption=new_filename,
                progress=progress_for_pyrogram,
                progress_args=("`Upload Started....`", ms, time.time())
            )
        elif update.data == "upload_video":
            await bot.send_video(
                update.message.chat.id,
                video=path,
                caption=new_filename,
                progress=progress_for_pyrogram,
                progress_args=("`Upload Started....`", ms, time.time())
            )
        elif update.data == "upload_audio":
            await bot.send_audio(
                update.message.chat.id,
                audio=path,
                caption=new_filename,
                progress=progress_for_pyrogram,
                progress_args=("`Upload Started....`", ms, time.time())
            )

    except Exception as e:          
        os.remove(path)
        return await ms.edit(f"**Error :** `{e}`")

    await ms.delete() 
    os.remove(path)

# Credit: @JishuBotz | @JishuDeveloper 
# Edited by @Rename_iBot 
