# echomatrix/transcriber.py

import openai
import soundfile as sf
import tempfile

from echomatrix import config

openai.api_key = config.OPENAI_API_KEY

def transcribe(pcm_data):
    with tempfile.NamedTemporaryFile(suffix=".flac", delete=False) as f:
        sf.write(f.name, pcm_data, config.SAMPLE_RATE, format='FLAC')
        with open(f.name, "rb") as audio_file:
            transcript = openai.Audio.transcribe(
                model=config.WHISPER_MODEL,
                file=audio_file
            )
    return transcript["text"]
