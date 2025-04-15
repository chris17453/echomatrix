# echomatrix/tts_generator.py

import requests
from echomatrix import config

def generate_speech(text):
    url = "https://api.openai.com/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {config.openai_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "tts-1",
        "input": text,
        "voice": config.tts_voice
    }
    response = requests.post(url, headers=headers, json=payload)
    
    mp3_path = config.generate_temp_mp3_path()
    with open(mp3_path, "wb") as f:
        f.write(response.content)
    return mp3_path