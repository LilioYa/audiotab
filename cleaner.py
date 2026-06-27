import music21

GUITAR_MIN_MIDI = 40
GUITAR_MAX_MIDI = 88

MIN_DURATION = 0.125


def clean(midi_path, mode="full"):
    score = music21.converter.parse(midi_path)
    flat = score.flatten()
    for chord in flat.notes:
        if chord.duration.quarterLength < MIN_DURATION:
            flat.remove(chord)
            continue

        chord.pitches = tuple(
            p for p in chord.pitches if GUITAR_MIN_MIDI <= p.midi <= GUITAR_MAX_MIDI
        )

        if len(chord.pitches) == 0 :
            flat.remove(chord)

    if mode == "simple" :
        flat = simplify(flat)

    output_path = midi_path.replace(".mid", "_clean.mid") 
    flat.write("midi", fp=output_path)
    return output_path


def simplify(flat):
    for chord in flat.notes:
        temp = chord.pitches
        chord.pitches = (max(temp, key=lambda p: p.midi),)
    return flat
