import yaml
import os
import uuid

_config_path = os.path.join(os.path.dirname(__file__), "config.yaml")

with open(_config_path, "r") as f:
    _raw_config = yaml.safe_load(f)

class Config:
    openai_api_key = _raw_config["openai_api_key"]
    whisper_model = _raw_config["whisper_model"]
    gpt_model = _raw_config["gpt_model"]
    tts_voice = _raw_config["tts_voice"]
    sample_rate = _raw_config["sample_rate"]
    temp_dir = _raw_config.get("temp_dir", "/tmp")

    @classmethod
    def generate_temp_audio_path(cls):
        return os.path.join(cls.temp_dir, f"ivr_input_{uuid.uuid4().hex}.wav")

    @classmethod
    def generate_temp_mp3_path(cls):
        return os.path.join(cls.temp_dir, f"ivr_response_{uuid.uuid4().hex}.mp3")

config = Config()
