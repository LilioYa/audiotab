"""Convert music21 note objects into LilyPond notation strings.

A LilyPond note is written as: <name><octave><duration>
    Example: "cis'4"  ->  C# in octave 4, quarter note

This module only deals with pure data transformation. It has no knowledge of
MIDI files or the rest of the pipeline, which keeps it small, reusable, and
easy to test in isolation.
"""

from fractions import Fraction


# music21 step letters (C, D, E, ...) mapped to their LilyPond lowercase names.
_STEP_TO_LILY = {
    "C": "c",
    "D": "d",
    "E": "e",
    "F": "f",
    "G": "g",
    "A": "a",
    "B": "b",
}

# LilyPond uses octave 3 as its reference: a bare "c" is C3. Higher octaves add
# apostrophes, lower octaves add commas.
_LILY_REFERENCE_OCTAVE = 3

# Base note durations: quarterLength value -> LilyPond duration digit.
_BASE_DURATIONS = {
    Fraction(4): "1",      # whole note
    Fraction(2): "2",      # half note
    Fraction(1): "4",      # quarter note
    Fraction(1, 2): "8",   # eighth note
    Fraction(1, 4): "16",  # sixteenth note
    Fraction(1, 8): "32",  # thirty-second note
}

# Fallback duration when a value matches nothing (kept simple on purpose).
_DEFAULT_DURATION = "4"


def pitch_name_to_lily(name: str) -> str:
    """Convert a music21 pitch name to its LilyPond spelling.

    Examples:
        "E-" -> "ees"  (E flat)
        "G#" -> "gis"  (G sharp)
        "C"  -> "c"
    """
    step = name[0]
    accidentals = name[1:]

    lily = _STEP_TO_LILY[step]
    for accidental in accidentals:
        if accidental == "#":
            lily += "is"   # sharp
        elif accidental == "-":
            lily += "es"   # flat

    return lily


def octave_to_lily(octave: int) -> str:
    """Convert a music21 octave number to LilyPond octave marks.

    Octave 3 is the reference (no mark). Each octave above adds an apostrophe,
    each octave below adds a comma.
        4 -> "'"   5 -> "''"   2 -> ","
    """
    diff = octave - _LILY_REFERENCE_OCTAVE
    if diff > 0:
        return "'" * diff
    if diff < 0:
        return "," * abs(diff)
    return ""


def duration_to_lily(quarter_length: float) -> str:
    """Convert a music21 quarterLength to a LilyPond duration string.

    Handles plain durations (1.0 -> "4") and dotted ones (0.75 -> "8.").
    Falls back to a quarter note for anything that does not map cleanly.
    """
    ql = Fraction(quarter_length).limit_denominator(64)

    # Exact match with a base duration.
    if ql in _BASE_DURATIONS:
        return _BASE_DURATIONS[ql]

    # Dotted note: a dot adds half the base value (base * 3/2).
    for base_value, lily_digit in _BASE_DURATIONS.items():
        if ql == base_value * Fraction(3, 2):
            return lily_digit + "."

    return _DEFAULT_DURATION


def pitch_to_lily(pitch) -> str:
    """Convert a music21 Pitch to its LilyPond name + octave (no duration)."""
    return pitch_name_to_lily(pitch.name) + octave_to_lily(pitch.octave)


def note_to_lily(note) -> str:
    """Convert a single music21 Note to a complete LilyPond note."""
    return pitch_to_lily(note.pitch) + duration_to_lily(note.duration.quarterLength)


def chord_to_lily(chord) -> str:
    """Convert a music21 Chord to LilyPond chord syntax: <c' e' g'>4."""
    pitches = " ".join(pitch_to_lily(p) for p in chord.pitches)
    duration = duration_to_lily(chord.duration.quarterLength)
    return f"<{pitches}>{duration}"


def element_to_lily(element) -> str:
    """Convert a music21 Note or Chord to LilyPond, dispatching on its type."""
    if element.isChord:
        return chord_to_lily(element)
    return note_to_lily(element)