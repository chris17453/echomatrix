# echomatrix/tts_generator.py

import requests
from echomatrix import config

def generate_speech(text):
    url = "https://api.openai.com/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {config.OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "tts-1",
        "input": text,
        "voice": config.TTS_VOICE
    }
    response = requests.post(url, headers=headers, json=payload)
    with open(config.TEMP_MP3_PATH, "wb") as f:
        f.write(response.content)
    return config.TEMP_MP3_PATH
