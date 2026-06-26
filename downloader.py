import yt_dlp


def download(url):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "%(title)s.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "quiet": False,
        "paths": {"home": "downloads/"},
    }
    with yt_dlp.YoutubeDL(ydl_opts) as video:
        info = video.extract_info(url, download=True)
        title = info["title"]
        print("Successfully downloaded")
        return f"downloads/{title}.mp3"
