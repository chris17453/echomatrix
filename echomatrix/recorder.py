# echomatrix/recorder.py

import subprocess
import tempfile
import numpy as np
import soundfile as sf
from echomatrix import config

def record_audio(duration=5):
    temp_path = config.TEMP_AUDIO_PATH
    subprocess.run([
        "arecord", "-f", "S16_LE", "-r", str(config.SAMPLE_RATE),
        "-d", str(duration), "-t", "raw", temp_path
    ])
    audio, _ = sf.read(temp_path, samplerate=config.SAMPLE_RATE, dtype='int16', channels=1)
    return audio
