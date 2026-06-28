"""audiotab - turn a YouTube/TikTok link into guitar sheet music.

Pipeline:
    URL -> audio (yt-dlp) -> MIDI (Basic Pitch) -> cleaned MIDI (cleaner)
        -> PDF score or tablature (LilyPond)

Only the final PDF is kept. All intermediate files (audio, raw MIDI, cleaned
MIDI) are written to a temporary directory that is removed automatically when
the program exits.

Examples:
    python main.py "<url>"
    python main.py "<url>" --mode notation
    python main.py "<url>" --difficulty simple
    python main.py "<url>" --start 0 --end 35 --output ./scores
"""

import argparse
import os
import shutil
import sys
import tempfile

from downloader import download
from transcriber import transcribe
from cleaner import clean
from exporter import export


def parse_args():
    """Define and parse the command-line interface."""
    parser = argparse.ArgumentParser(
        prog="audiotab",
        description="Turn a YouTube/TikTok link into guitar sheet music.",
    )
    parser.add_argument(
        "url",
        help="Source URL (YouTube, TikTok, ...).",
    )
    parser.add_argument(
        "--mode",
        choices=["tabs", "notation"],
        default="tabs",
        help="Output style: 'tabs' for guitar tablature, "
             "'notation' for a classic score (default: tabs).",
    )
    parser.add_argument(
        "--difficulty",
        choices=["simple", "full"],
        default="full",
        help="'simple' reduces the music to a single melodic line, "
             "'full' keeps chords (default: full).",
    )
    parser.add_argument(
        "--start",
        type=float,
        default=None,
        help="Start time in seconds, to transcribe only a segment.",
    )
    parser.add_argument(
        "--end",
        type=float,
        default=None,
        help="End time in seconds, to transcribe only a segment.",
    )
    parser.add_argument(
        "--output",
        default="output",
        help="Directory where the final PDF is saved (default: ./output).",
    )
    return parser.parse_args()


def run(args, work_dir):
    """Run the full pipeline inside ``work_dir`` and return the PDF path.

    All intermediate files live in ``work_dir``; only the final PDF is copied
    to the user's output directory by the caller.
    """
    print("[1/4] Downloading audio...")
    audio_path = download(args.url, work_dir, start=args.start, end=args.end)

    print("[2/4] Transcribing to MIDI...")
    midi_path = transcribe(audio_path, work_dir)

    print("[3/4] Cleaning MIDI...")
    clean_midi_path = clean(midi_path, work_dir, difficulty=args.difficulty)

    print("[4/4] Rendering PDF...")
    pdf_path = export(clean_midi_path, work_dir, mode=args.mode)

    return pdf_path


def main():
    args = parse_args()
    os.makedirs(args.output, exist_ok=True)

    # Everything happens in a temporary directory that is wiped on exit, so the
    # only file that survives is the final PDF.
    with tempfile.TemporaryDirectory(prefix="audiotab_") as work_dir:
        pdf_path = run(args, work_dir)

        if pdf_path is None or not os.path.exists(pdf_path):
            print("\nFailed to produce a PDF. See the errors above.")
            sys.exit(1)

        final_path = os.path.join(args.output, os.path.basename(pdf_path))
        shutil.move(pdf_path, final_path)

    print(f"\nDone! Saved to {final_path}")


if __name__ == "__main__":
    main()