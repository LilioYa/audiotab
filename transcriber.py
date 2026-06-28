"""Transcribe an audio file into a MIDI file using Spotify's Basic Pitch.

Basic Pitch is an open-source neural model that performs automatic music
transcription: it listens to an audio file and predicts the notes being played,
producing a MIDI file. The output is raw and noisy; cleaning happens later in
the pipeline (see ``cleaner.py``).
"""

import os

from basic_pitch.inference import predict


def transcribe(audio_path, output_dir):
    """Transcribe ``audio_path`` to a MIDI file and return its path.

    Args:
        audio_path: Path to the input audio file (MP3, WAV, ...).
        output_dir: Directory where the MIDI file is written.

    Returns:
        The path to the generated MIDI file.
    """
    _model_output, midi_data, _note_events = predict(audio_path)

    filename = os.path.splitext(os.path.basename(audio_path))[0]
    midi_path = os.path.join(output_dir, f"{filename}.mid")
    midi_data.write(midi_path)

    return midi_path