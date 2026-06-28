"""Clean the raw MIDI produced by Basic Pitch.

On guitar audio, Basic Pitch returns a "messy" transcription:
  - polyphony that overlaps in time (several notes at the same instant)
  - the harmonics of each note (octave, fifth) detected as separate notes
  - a single sustained note chopped into several fragments
  - very short, spurious note changes

The "simple" mode applies a robust monophonic reduction that turns this mess
into a single, playable melodic line. The strategy was tuned by objectively
comparing several approaches on real data:

  1. flatten chords and notes into timed events
  2. sample time on a regular grid (one note per instant -> no more overlap)
  3. fold octaves into a reference register (pitch folding -> removes the
     octave jumps caused by harmonics)
  4. smooth the sequence with a median filter (removes isolated stray notes)
  5. merge consecutive identical samples into sustained notes
"""

import os

import music21


# Standard guitar range (EADGBE tuning): E2 (MIDI 40) -> E6 (MIDI 88).
GUITAR_MIN_MIDI = 40
GUITAR_MAX_MIDI = 88

# Minimum duration of a raw note (in quarterLength). 0.125 = sixteenth note.
MIN_DURATION = 0.125

# Time-sampling step for the monophonic reduction (in quarterLength).
# 0.25 = sixteenth note: fine enough for rhythm, wide enough to smooth.
GRID = 0.25

# Median filter window size (in number of samples).
# 3 = fix a single isolated note surrounded by two different ones.
SMOOTH_WINDOW = 3


def in_guitar_range(midi):
    """Return True if a MIDI pitch falls within the playable guitar range."""
    return GUITAR_MIN_MIDI <= midi <= GUITAR_MAX_MIDI


def clean(midi_path, output_dir, difficulty="full"):
    """Clean a raw Basic Pitch MIDI file and write the result to disk.

    In "simple" mode, applies the monophonic reduction (a single melodic line).
    In "full" mode, only performs light filtering that keeps chords. In both
    cases the rhythm is quantized to a sixteenth-note grid.

    Args:
        midi_path: Path to the raw MIDI file.
        output_dir: Directory where the cleaned MIDI file is written.
        difficulty: "simple" or "full".

    Returns:
        The path to the cleaned MIDI file.
    """
    score = music21.converter.parse(midi_path)
    flat = score.flatten()

    if difficulty == "simple":
        flat = monophonic_reduction(flat)
    else:
        flat = filter_full(flat)

    flat.quantize((4,), True, True, True)

    filename = os.path.splitext(os.path.basename(midi_path))[0]
    output_path = os.path.join(output_dir, f"{filename}_clean.mid")
    flat.write("midi", fp=output_path)
    return output_path


def filter_full(flat):
    """Light cleanup for full mode.

    Removes micro-notes and anything outside the guitar range, but keeps chords
    intact.
    """
    for element in list(flat.notes):
        if element.duration.quarterLength < MIN_DURATION:
            flat.remove(element)
            continue

        if element.isChord:
            element.pitches = tuple(
                p for p in element.pitches if in_guitar_range(p.midi)
            )
            if len(element.pitches) == 0:
                flat.remove(element)
        else:
            if not in_guitar_range(element.pitch.midi):
                flat.remove(element)
    return flat


def extract_notes(flat):
    """Flatten a stream into a list of (start, end, midi) events.

    Chords are split into their constituent notes. Micro-notes and pitches
    outside the guitar range are discarded.
    """
    events = []
    for element in flat.notes:
        if element.duration.quarterLength < MIN_DURATION:
            continue

        start = float(element.offset)
        end = start + float(element.duration.quarterLength)

        if element.isChord:
            for p in element.pitches:
                if in_guitar_range(p.midi):
                    events.append((start, end, p.midi))
        else:
            if in_guitar_range(element.pitch.midi):
                events.append((start, end, element.pitch.midi))
    return events


def median_smooth(values, window=SMOOTH_WINDOW):
    """Smooth a sequence of pitches with a median filter.

    An isolated value that differs from its neighbours is pulled toward the
    median of its window, which removes one-off detection artifacts.
    """
    if len(values) < window:
        return values

    half = window // 2
    smoothed = list(values)
    for i in range(half, len(values) - half):
        neighborhood = values[i - half: i + half + 1]
        smoothed[i] = sorted(neighborhood)[len(neighborhood) // 2]
    return smoothed


def monophonic_reduction(flat):
    """Turn a messy polyphonic transcription into a single melodic line.

    See the module docstring for the five-step strategy.
    """
    events = extract_notes(flat)
    if not events:
        return flat

    # Reference octave: anchored on the lowest note of the piece.
    min_midi = min(midi for (_, _, midi) in events)
    ref_low = min_midi
    ref_high = min_midi + 12

    def fold(midi):
        """Fold a pitch into the reference octave [ref_low, ref_high)."""
        while midi >= ref_high:
            midi -= 12
        while midi < ref_low:
            midi += 12
        return midi

    total_end = max(end for (_, end, _) in events)

    # Time sampling: at each step, keep the lowest active (folded) pitch.
    times = []
    pitches = []
    t = 0.0
    while t < total_end:
        active = [midi for (start, end, midi) in events if start <= t < end]
        if active:
            times.append(t)
            pitches.append(min(fold(m) for m in active))
        t += GRID

    if not pitches:
        return flat

    # Median smoothing to remove isolated stray notes.
    pitches = median_smooth(pitches)

    # Merge consecutive samples of the same pitch into sustained notes.
    merged = [[times[0], times[0] + GRID, pitches[0]]]
    for i in range(1, len(times)):
        last = merged[-1]
        same_pitch = pitches[i] == last[2]
        adjacent = abs(times[i] - last[1]) < GRID * 1.5
        if same_pitch and adjacent:
            last[1] = times[i] + GRID
        else:
            merged.append([times[i], times[i] + GRID, pitches[i]])

    # Rebuild a clean monophonic stream.
    new_stream = music21.stream.Stream()
    for start, end, midi in merged:
        note = music21.note.Note()
        note.pitch.midi = midi
        note.duration.quarterLength = max(end - start, MIN_DURATION)
        new_stream.insert(start, note)

    return new_stream