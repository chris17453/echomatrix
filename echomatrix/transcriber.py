import os
import openai
import soundfile as sf
import tempfile
from echomatrix.config import config

def transcribe(pcm_data, temp_path=None):

    if not temp_path:
        temp_path = os.path.join(config.temp_dir, f"transcribe_{uuid.uuid4().hex}.flac")

    with tempfile.NamedTemporaryFile(suffix=".flac", dir=config.temp_dir, delete=False) as f:
        sf.write(f.name, pcm_data, config.sample_rate, format='FLAC')
        with open(f.name, "rb") as audio_file:
            transcript = openai.Audio.transcribe(
                model=config.whisper_model,
                file=audio_file
            )
    return transcript["text"]
