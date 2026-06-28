"""Export a cleaned MIDI file to a PDF score.

Two output styles are supported:
  - "notation": a classic music score (notes on a staff), rendered by music21
    through LilyPond.
  - "tabs": a guitar tablature (fret numbers on six strings). The MIDI is
    converted to LilyPond notation by ``lily_converter`` and rendered with a
    TabStaff.
"""

import os
import re
import subprocess

import music21
from music21 import instrument

from lily_converter import element_to_lily


def sanitize_filename(name):
    """Make a string safe to use as a filename (letters, digits, dashes)."""
    name = re.sub(r"[^\w\-]", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")


def export(midi_path, output_dir, mode="tabs"):
    """Export a cleaned MIDI file to a PDF and return the PDF path.

    Args:
        midi_path: Path to the cleaned MIDI file.
        output_dir: Directory where the final PDF is written.
        mode: "tabs" for guitar tablature, "notation" for a classic score.

    Returns:
        The path to the generated PDF, or None if rendering failed.
    """
    if mode == "tabs":
        return _export_tabs(midi_path, output_dir)
    return _export_notation(midi_path, output_dir)


def _export_notation(midi_path, output_dir):
    """Render a classic music score using music21's built-in LilyPond export."""
    output_base = _output_base_path(midi_path, output_dir)

    score = music21.converter.parse(midi_path)
    for part in score.parts:
        part.insert(0, instrument.Guitar())

    score.write("lily.pdf", fp=output_base)
    return f"{output_base}.pdf"


def _export_tabs(midi_path, output_dir):
    """Render a guitar tablature by generating a LilyPond TabStaff file."""
    output_base = _output_base_path(midi_path, output_dir)

    notes = _midi_to_lily_notes(midi_path)
    lily_source = _build_tab_template(notes)

    ly_path = f"{output_base}.ly"
    with open(ly_path, "w") as f:
        f.write(lily_source)

    result = subprocess.run(
        ["lilypond", "-o", output_base, ly_path],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"LilyPond error:\n{result.stderr}")
        return None

    return f"{output_base}.pdf"


def _midi_to_lily_notes(midi_path):
    """Convert every note/chord in a MIDI file to a LilyPond note string.

    The simple/full distinction is already handled upstream by the cleaner, so
    here we simply convert whatever notes are present.
    """
    score = music21.converter.parse(midi_path)
    flat = score.flatten()
    return " ".join(element_to_lily(element) for element in flat.notes)


def _build_tab_template(notes):
    """Wrap a sequence of LilyPond notes in a flat-tab TabStaff template.

    By default a TabStaff shows only fret numbers, with no rhythmic notation.
    We additionally hide stems, beams and the time signature, and disable
    automatic bar lines, to produce a clean, rhythm-free run of fret numbers.
    """
    return f"""\\version "2.24.0"
\\score {{
  \\new TabStaff {{
    \\override TabStaff.Stem.stencil = ##f
    \\override TabStaff.Flag.stencil = ##f
    \\override TabStaff.Beam.stencil = ##f
    \\omit TabStaff.TimeSignature
    \\cadenzaOn
    {notes}
  }}
  \\layout {{
    indent = 0
  }}
}}
"""


def _output_base_path(midi_path, output_dir):
    """Build the output path (without extension) for a given MIDI file."""
    raw_name = os.path.splitext(os.path.basename(midi_path))[0]
    filename = sanitize_filename(raw_name)
    return os.path.join(output_dir, filename)