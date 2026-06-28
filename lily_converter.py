from fractions import Fraction

_STEP_TO_LILY = {
    "C": "c",
    "D": "d",
    "E": "e",
    "F": "f",
    "G": "g",
    "A": "a",
    "B": "b",
}

def pitch_name_to_lily(name: str) -> str:
    step = name[0]
    accidentals = name[1:]

    lily = _STEP_TO_LILY[step]

    for acc in accidentals:
        if acc == "#":
            lily += "is"
        elif acc == "-":
            lily += "es"

    return lily


def octave_to_lily(octave: int) -> str:
    diff = octave - 3
    if diff > 0:
        return "'" * diff
    elif diff < 0:
        return "," * abs(diff)
    return ""


def duration_to_lily(quarter_length: float) -> str:
    ql = Fraction(quarter_length).limit_denominator(64)

    base_durations = {
        Fraction(4): "1",
        Fraction(2): "2",
        Fraction(1): "4",
        Fraction(1, 2): "8",
        Fraction(1, 4): "16",
        Fraction(1, 8): "32",
    }

    if ql in base_durations:
        return base_durations[ql]

    for frac, lily in base_durations.items():
        if ql == frac * Fraction(3, 2):
            return lily + "."

    return "4"


def pitch_to_lily(pitch) -> str:
    return pitch_name_to_lily(pitch.name) + octave_to_lily(pitch.octave)


def note_to_lily(note) -> str:
    return pitch_to_lily(note.pitch) + duration_to_lily(note.duration.quarterLength)


def chord_to_lily(chord) -> str:
    pitches = " ".join(pitch_to_lily(p) for p in chord.pitches)
    duration = duration_to_lily(chord.duration.quarterLength)
    return f"<{pitches}>{duration}"


def element_to_lily(element) -> str:
    if element.isChord:
        return chord_to_lily(element)
    return note_to_lily(element)
