# echomatrix/audio_player.py

import subprocess
from echomatrix import config

def play_audio(mp3_path):
    subprocess.run(["mpg123", mp3_path])
