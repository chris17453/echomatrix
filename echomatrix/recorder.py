# echomatrix/recorder.py

import subprocess
import tempfile
import numpy as np
import soundfile as sf
from echomatrix.config import config

def record_audio(duration=5):
    temp_path = config.generate_temp_audio_path()
    subprocess.run([
        "arecord", "-f", "S16_LE", "-r", str(config.sample_rate),
        "-d", str(duration), "-t", "raw", temp_path
    ])
    audio, _ = sf.read(temp_path, samplerate=config.sample_rate, dtype='int16', channels=1)
    return audio, temp_path
