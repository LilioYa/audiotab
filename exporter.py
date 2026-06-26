import os
import re
import music21
from music21 import instrument


def sanitize_filename(name):
    name = re.sub(r"[^\w\-]", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")


def export(midi_path, output_dir="pdf_output"):
    os.makedirs(output_dir, exist_ok=True)

    raw_name = os.path.splitext(os.path.basename(midi_path))[0]
    filename = sanitize_filename(raw_name)
    output_base = os.path.join(output_dir, filename)

    score = music21.converter.parse(midi_path)
    for part in score.parts:
        part.insert(0, instrument.Guitar())

    score.write("lily.pdf", fp=output_base)
    print(f"PDF généré : {output_base}.pdf")

    return f"{output_base}.pdf"