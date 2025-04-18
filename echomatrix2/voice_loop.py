import logging
import uuid
import os
import threading
import time
from echomatrix.config import config
from echomatrix.rtp_streamer import stream_wav_to_rtp, receive_rtp_stream
from echomatrix.transcriber import transcribe
from echomatrix.gpt_processor import get_gpt_response
from echomatrix.tts_generator import generate_speech

logger = logging.getLogger("voice_loop")


def listen_for_input(rx_ip, rx_port, session_id, silence_timeout=3, max_silence=10):
    logger.info("Listening for caller input with silence detection")
    received_audio = os.path.join(config.temp_dir, f"recv_{session_id}.wav")
    receive_rtp_stream(received_audio, rx_ip, rx_port, duration_sec=max_silence)
    return received_audio


def voice_session():
    tx_ip = config.sip.outbound_proxy
    tx_port = config.rtp.tx_port
    rx_ip = config.sip.local_ip
    rx_port = config.rtp.rx_port

    logger.info("Voice session started")

    greeting = "Hello. What can I help you with today?"
    greeting_wav = generate_speech(greeting)
    stream_wav_to_rtp(greeting_wav, tx_ip, tx_port)

    while True:
        session_id = str(uuid.uuid4())
        audio_path = listen_for_input(rx_ip, rx_port, session_id)
        
        transcript = transcribe(None, audio_path)
        logger.info(f"Caller said: {transcript}")

        if not transcript or transcript.strip().lower() in ["", "exit", "goodbye"]:
            logger.info("Caller silent or ended conversation.")
            farewell = generate_speech("Goodbye.")
            stream_wav_to_rtp(farewell, tx_ip, tx_port)
            break

        response_text = get_gpt_response(transcript)
        logger.info(f"GPT response: {response_text}")

        response_wav = generate_speech(response_text)
        stream_wav_to_rtp(response_wav, tx_ip, tx_port)


def handle_call():
    thread = threading.Thread(target=voice_session, daemon=True)
    thread.start()
