import os
import re
import time
import shutil
import asyncio
import logging
from datetime import datetime
from PIL import Image
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from plugins.antinsfw import check_anti_nsfw
from helper.utils import progress_for_pyrogram, humanbytes
from helper.database import Element_Network
from config import Config

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
renaming_operations = {}

# Regex for extracting season/episode
SEASON_EPISODE_PATTERNS = [
    (re.compile(r"S(\d{1,2})E(\d{1,2})", re.IGNORECASE), ('season', 'episode')),
    (re.compile(r"S(\d+)[\s._-]*EP?(\d+)", re.IGNORECASE), ('season', 'episode')),
    (re.compile(r"Season\s*(\d+)\s*Episode\s*(\d+)", re.IGNORECASE), ('season', 'episode')),
    (re.compile(r"[Ss](\d+)[^\w]?[Ee](\d+)"), ('season', 'episode')),
    (re.compile(r"EP(?:isode)?[\s_-]?(\d+)", re.IGNORECASE), (None, 'episode')),
]

QUALITY_PATTERNS = [
    re.compile(r"(?:2160|4k)"),
    re.compile(r"(1080|720|480|360)p", re.IGNORECASE),
    re.compile(r"\b(HDRip|HDTV|BluRay|WEBRip)\b", re.IGNORECASE)
]

def extract_season_episode(text):
    for pattern, (s_group, e_group) in SEASON_EPISODE_PATTERNS:
        match = pattern.search(text)
        if match:
            groups = match.groups()
            season = groups[int(s_group == 'episode') * 0] if s_group else ''
            episode = groups[int(e_group == 'episode')] if e_group else ''
            return season.zfill(2), episode.zfill(2)
    return "01", "01"

def extract_quality(text):
    for pattern in QUALITY_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return "HQ"

def get_duration(file_path):
    try:
        metadata = extractMetadata(createParser(file_path))
        if metadata and metadata.has("duration"):
            return metadata.get("duration")
    except Exception:
        pass
    return "00:00:00"

async def process_thumb(client, thumb_id, path):
    if thumb_id:
        thumb_path = await client.download_media(thumb_id)
        if os.path.exists(thumb_path):
            try:
                with Image.open(thumb_path) as img:
                    img.convert("RGB").resize((320, 320)).save(thumb_path, "JPEG")
                return thumb_path
            except Exception as e:
                logger.warning(f"Thumb processing failed: {e}")
                os.remove(thumb_path)
    return None

@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def file_rename_handler(client: Client, message: Message):
    user_id = message.from_user.id
    media = message.document or message.video or message.audio
    file_name = media.file_name or "file"
    file_size = media.file_size or 0
    duration = getattr(media, 'duration', 0)
    ext = os.path.splitext(file_name)[1]

    # Block NSFW
    if await check_anti_nsfw(file_name, message):
        return

    # Prevent duplicates
    if media.file_id in renaming_operations:
        return await message.reply("⏳ File is already being processed.")
    renaming_operations[media.file_id] = time.time()

    try:
        # Check Premium access
        is_premium = await Element_Network.check_premium(user_id)
        if not is_premium:
            return await message.reply_text(
                "🚫 This is a premium feature.\nContact @Shadow_Blank to get access.")

        # Get rename template
        template = await Element_Network.get_format_template(user_id)
        if not template:
            return await message.reply_text("❗ No rename format found. Use /format to set one.")

        # Get user metadata
        metadata = await Element_Network.get_metadata(user_id)
        season, episode = extract_season_episode(file_name)
        quality = extract_quality(file_name)

        placeholders = {
            "filename": os.path.splitext(file_name)[0],
            "ext": ext,
            "title": metadata.get("title", ""),
            "season": metadata.get("season", season),
            "episode": metadata.get("episode", episode),
            "chapter": metadata.get("chapter", ""),
            "quality": metadata.get("quality", quality),
            "language": metadata.get("language", ""),
            "resolution": metadata.get("resolution", ""),
            "year": metadata.get("year", ""),
            "custom": metadata.get("custom", "")
        }

        try:
            final_name = template.format(**placeholders).strip()
        except KeyError as ke:
            return await message.reply_text(f"❌ Unknown placeholder: {ke}")
        new_filename = final_name + ext

        downloads_dir = f"downloads/{user_id}"
        os.makedirs(downloads_dir, exist_ok=True)
        download_path = os.path.join(downloads_dir, new_filename)

        # Download file
        status = await message.reply_text("📥 Downloading your file...")
        await client.download_media(
            message, download_path,
            progress=progress_for_pyrogram,
            progress_args=("📥 Downloading...", status, time.time())
        )

        # Add metadata (if FFmpeg available)
        processed_path = download_path
        try:
            meta_output = os.path.join(downloads_dir, f"meta_{new_filename}")
            await add_metadata(download_path, meta_output, user_id)
            processed_path = meta_output
        except Exception as e:
            logger.warning(f"Metadata skipped: {e}")

        # Get caption and thumbnail
        caption_tpl = await Element_Network.get_caption(user_id)
        duration_fm = str(get_duration(processed_path)) if media.mime_type.startswith("video") else ""
        caption = caption_tpl.format(
            filename=new_filename,
            filesize=humanbytes(file_size),
            duration=duration_fm
        ) if caption_tpl else f"`{new_filename}`"

        thumb_id = await Element_Network.get_thumbnail(user_id)
        thumb_path = await process_thumb(client, thumb_id, downloads_dir)

        # Upload format
        media_type = metadata.get("media_type", "document").lower()
        await status.edit("📤 Uploading...")
        if media_type == "video":
            await client.send_video(
                message.chat.id,
                video=processed_path,
                caption=caption,
                thumb=thumb_path,
                progress=progress_for_pyrogram,
                progress_args=("📤 Uploading...", status, time.time())
            )
        elif media_type == "audio":
            await client.send_audio(
                message.chat.id,
                audio=processed_path,
                caption=caption,
                thumb=thumb_path,
                progress=progress_for_pyrogram,
                progress_args=("📤 Uploading...", status, time.time())
            )
        else:
            await client.send_document(
                message.chat.id,
                document=processed_path,
                caption=caption,
                thumb=thumb_path,
                force_document=True,
                progress=progress_for_pyrogram,
                progress_args=("📤 Uploading...", status, time.time())
            )

        await status.delete()

    except Exception as e:
        logger.error(f"Error in file_rename_handler: {e}")
        await message.reply_text(f"❌ Error: {str(e)}")
    finally:
        renaming_operations.pop(media.file_id, None)
        await cleanup_files(download_path, thumb_path)


