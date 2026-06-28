import os
import re
import subprocess
import music21
from music21 import instrument
from lily_converter import element_to_lily


def sanitize_filename(name):
    name = re.sub(r"[^\w\-]", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")


def export_music_theorie(midi_path, output_dir="pdf_output"):
    os.makedirs(output_dir, exist_ok=True)

    raw_name = os.path.splitext(os.path.basename(midi_path))[0]
    filename = sanitize_filename(raw_name)
    output_base = os.path.join(output_dir, filename)

    score = music21.converter.parse(midi_path)
    for part in score.parts:
        part.insert(0, instrument.Guitar())

    score.write("lily.pdf", fp=output_base)

    return f"{output_base}.pdf"


def midi_to_lily_notes(midi_path):
    """
    Parcourt le MIDI et convertit chaque element (note ou accord)
    en notation LilyPond. Le mode simple/full est deja gere en amont
    par le cleaner, donc ici on convertit tel quel.
    Retourne une string avec tous les elements separes par des espaces.
    """
    score = music21.converter.parse(midi_path)
    flat = score.flatten()

    return " ".join(element_to_lily(element) for element in flat.notes)


def export_tabs(midi_path, output_dir="pdf_output"):
    os.makedirs(output_dir, exist_ok=True)

    raw_name = os.path.splitext(os.path.basename(midi_path))[0]
    filename = sanitize_filename(raw_name)
    output_base = os.path.join(output_dir, filename)

    notes = midi_to_lily_notes(midi_path)

    # Template LilyPond avec TabStaff pour generer les tablatures
    lily_template = f"""\\version "2.24.0"
\\score {{
  \\new TabStaff {{
    \\tabFullNotation
    {notes}
  }}
}}
"""

    ly_path = f"{output_base}.ly"
    with open(ly_path, "w") as f:
        f.write(lily_template)

    result = subprocess.run(
        ["lilypond", "-o", output_base, ly_path],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Erreur LilyPond:\n{result.stderr}")
        return None

    print(f"Tabs PDF generated : {output_base}.pdf")
    return f"{output_base}.pdf"


def export(midi_path, output_dir="pdf_output", mode="tabs"):
    return export_tabs(midi_path, output_dir) if mode == "tabs" else export_music_theorie(midi_path, output_dir)