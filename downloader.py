"""Download audio from a URL (YouTube, TikTok, ...) using yt-dlp.

The audio is extracted to an MP3 file inside the directory passed by the
caller. A time range can be requested to download only a segment of the source,
which is useful to skip intros or grab a single riff.
"""

import os

import yt_dlp
from yt_dlp.utils import download_range_func


def download(url, output_dir, start=None, end=None):
    """Download the audio track of ``url`` as an MP3 and return its path.

    Args:
        url: Source URL (YouTube, TikTok, and anything else yt-dlp supports).
        output_dir: Directory where the MP3 is written.
        start: Optional start time in seconds for a partial download.
        end: Optional end time in seconds for a partial download.

    Returns:
        The path to the downloaded MP3 file.
    """
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
        "quiet": True,
        "no_warnings": True,
        "paths": {"home": output_dir},
        "noplaylist": True,
        # Replace spaces and special characters in filenames so that titles
        # containing slashes or non-ASCII characters do not break the path.
        "restrictfilenames": True,
    }

    # Restrict the download to a single time range when both bounds are given.
    if start is not None and end is not None:
        ydl_opts["download_ranges"] = download_range_func(None, [(start, end)])
        ydl_opts["force_keyframes_at_cuts"] = True

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # prepare_filename gives the real on-disk name (with restrictfilenames
        # already applied); we swap the extension because the post-processor
        # converts the container to MP3.
        downloaded_path = ydl.prepare_filename(info)
        mp3_path = os.path.splitext(downloaded_path)[0] + ".mp3"

    return mp3_path