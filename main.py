import argparse
from downloader import download
from transcriber import transcrib
from cleaner import clean
from exporter import export


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio from a URL to sheet music")
    parser.add_argument("url", help="YouTube or TikTok URL")
    parser.add_argument("--difficulty", choices=["simple", "full"], default="full", help="Difficulty transcription mode")
    parser.add_argument("--mode", choices=["music_theorie", "tabs"], default="tabs", help="Type of the output sheet")
    args = parser.parse_args()

    print(f"Downloading audio...")
    file_path = download(args.url)

    print(f"Transcribing to MIDI...")
    midi_path = transcrib(file_path)

    print(f"Cleaning MIDI...")
    clean_midi_path = clean(midi_path, difficulty=args.difficulty)

    print(f"Exporting to PDF...")
    pdf_path = export(clean_midi_path, mode=args.mode)

    print(f"Done ! PDF saved at {pdf_path}")


if __name__ == "__main__":
    main()