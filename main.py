from downloader import download
from transcriber import transcrib
from exporter import export

file_path = download("https://vm.tiktok.com/ZNRToTLEk/")
midi_file_path = transcrib(file_path)
export(midi_file_path)