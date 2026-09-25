import asyncio
import os
import tempfile
from pathlib import Path
import yt_dlp

async def download_media(url: str, audio_only: bool = False):
    folder = Path(tempfile.mkdtemp(prefix="tgdl_"))
    output = str(folder / "%(title).80s.%(ext)s")
    options = {
        "outtmpl": output,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
    }
    if audio_only:
        options.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    else:
        options["format"] = "best[ext=mp4]/best"

    def run():
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])
        files = list(folder.glob("*"))
        return files[0] if files else None

    return await asyncio.to_thread(run)
