import os
import re
import time

# ID regex to differentiate between numeric IDs and usernames
id_pattern = re.compile(r'^-?\d+$')

class Config(object):
    # Pyrogram client config
    API_ID = int(os.getenv("API_ID", "22451708"))
    API_HASH = os.getenv("API_HASH", "288f749fcef814c1ec90b66936158c68")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")

    # Mongo DB
    DB_NAME = os.getenv("DB_NAME", "rename")
    DB_URL = os.getenv("DB_URL", "mongodb://localhost:27017")

    # Optional port (for webhook deployment)
    PORT = int(os.getenv("PORT", "8080"))

    # Internal uptime tracker
    BOT_UPTIME = time.time()

    # Optional start image
    START_PIC = os.getenv(
        "START_PIC",
        "https://i.ibb.co/6ckYMvTM/photo-2025-08-03-07-50-57-7534270173679714320.jpg"
    )

    # Admin list from env
    ADMIN = [
        int(x) if id_pattern.match(x) else x
        for x in os.getenv('ADMIN', '6975428639').split()
    ]

    # Channel settings
    FORCE_SUB_CHANNELS = os.getenv(
        "FORCE_SUB_CHANNELS", "Mortals_Log_Channel"
    ).split(',')
    LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", "-1002887783820"))  # Admin logs
    DUMP_CHANNEL = int(os.getenv("DUMP_CHANNEL", "-1002887783820"))  # Renamed files storage

    # Owner ID
    BOT_OWNER = int(os.getenv("BOT_OWNER", "6975428639"))

    # Optional webhook toggle
    WEBHOOK = bool(os.getenv("WEBHOOK", "True").lower() in ["true", "1", "yes"])


class Txt(object):
    START_TXT = """<b>ʜᴇʏ {} ✨

» I am an advanced Auto Rename Bot ⚙  
— Auto file renaming, thumbnails, sequence support & NSFW filter 🚫</b>"""

    FILE_NAME_TXT = """<b><u>📂 Rename Format Setup:</u></b>

<b>Available placeholders:</b>
➲ filename — base name of the original file  
➲ ext — file extension (.mp4, .pdf, etc.)  
➲ title — custom/set series title  
➲ season — season number  
➲ episode — episode number  
➲ chapter — chapter number (for PDFs/manga)  
➲ quality — video/audio quality  
➲ language — language tag  
➲ resolution — resolution (e.g., 1080p)  
➲ year — release year  
➲ custom — any user-defined label/tag  

<b>Example:</b>  
/format {title} [S{season}E{episode}] [{quality}]{ext}"""

    ABOUT_TXT = """<b>🤖 Bot:</b> AutoRename  
<b>👨‍💻 Dev:</b> <a href="https://t.me/Aaru_2075">Aaru</a>  
<b>🗃 DB:</b> MongoDB  
<b>💻 Host:</b> VPS  
<b>📢 Channel:</b> <a href="https://t.me/Manga_Campus">Manga Campus</a>"""

    THUMBNAIL_TXT = """<b><u>🖼 Custom Thumbnail:</u></b>
Send any photo to set thumbnail.  
/viewthumb — preview  
/delthumb — delete"""

    CAPTION_TXT = """<b><u>📌 Custom Caption:</u></b>
Supported placeholders:
/set_caption 🎬 {filename} | {filesize} | ⏱ {duration}"""

    PROGRESS_BAR = """\n
<b>Progress:</b> {0}%  
<b>Size:</b> {1} of {2}  
<b>Speed:</b> {3}/s  
<b>ETA:</b> {4}"""

    DONATE_TXT = """💖 Donate via:  
UPI: <code>Rai2075@fam</code>"""

    PREMIUM_TXT = """<b>💎 Premium Benefits:</b>
• Unlimited renaming  
• Priority queue"""

    PREPLANS_TXT = """<b>📊 Plans:</b>
• ₹150 – Month  
• ₹5 – Day"""

    HELP_TXT = """<b>🆘 Help:</b>
Send a file, bot renames using your /format.  
NSFW → strike system."""

    SEND_METADATA = """🔧 Metadata:
/metadata on/off"""

    SOURCE_TXT = """💻 Open Source – Built with Pyrogram & MongoDB"""

    META_TXT = """**Editing Metadata**
/settitle  
/setseason  
/setepisode  
..."""

    SEQUENCE_TXT = """<b>📦 Sequence Manager:</b>
/startsequence  
/showsequence  
/endsequence  
/cancelsequence"""
    
