# echomatrix/echomatrix/agi_handler.py

import sys
from echomatrix.recorder import record_audio
from echomatrix.transcriber import transcribe
from echomatrix.ivr_logic import handle_input
from echomatrix.tts_generator import generate_speech
from echomatrix.audioplayer import play_audio
from echomatrix.utils import cleanup_temp_file

def main():
    sys.stdin.readline()  # Consume AGI env vars

    try:
        pcm_data, temp_input_path = record_audio()
        transcript = transcribe(pcm_data, temp_input_path)
        response = handle_input(transcript)
        mp3_path = generate_speech(response)
        play_audio(mp3_path)
    finally:
        cleanup_temp_file(temp_input_path)
        cleanup_temp_file(mp3_path)

if __name__ == "__main__":
    main()
