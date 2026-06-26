from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH
import os


def transcrib(audio_path):
    model_output, midi_data, note_events = predict(audio_path)
    filename = os.path.splitext(os.path.basename(audio_path))[0]
    midi_path = f"midi_output/{filename}.mid"
    midi_data.write(midi_path)
    return midi_path