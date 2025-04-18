import socket
import time
import wave
import logging
from echomatrix.config import config

logger = logging.getLogger("rtp_streamer")


def stream_wav_to_rtp(wav_path, target_ip, target_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    logger.info(f"Streaming {wav_path} to {target_ip}:{target_port} via RTP")

    try:
        with wave.open(wav_path, 'rb') as wf:
            assert wf.getframerate() == config.rtp.sample_rate
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2  # slin16

            frame_duration = 0.02  # 20ms
            frames_per_packet = int(config.rtp.sample_rate * frame_duration)

            while True:
                data = wf.readframes(frames_per_packet)
                if not data:
                    break
                sock.sendto(data, (target_ip, target_port))
                time.sleep(frame_duration)

        logger.info("Finished streaming audio")
    except Exception as e:
        logger.error(f"Error streaming RTP: {e}")
    finally:
        sock.close()


def receive_rtp_stream(output_path, listen_ip, listen_port, duration_sec):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((listen_ip, listen_port))
    sock.settimeout(2.0)

    logger.info(f"Listening for RTP on {listen_ip}:{listen_port}, saving to {output_path}")
    audio_data = bytearray()
    start_time = time.time()

    try:
        while time.time() - start_time < duration_sec:
            try:
                data, _ = sock.recvfrom(2048)
                audio_data.extend(data)
            except socket.timeout:
                continue
    finally:
        sock.close()

    # Save raw data to WAV
    with wave.open(output_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(config.rtp.sample_rate)
        wf.writeframes(audio_data)

    logger.info(f"Saved RTP stream to {output_path}")
    return output_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # Example usage:
    # stream_wav_to_rtp("/tmp/tts.wav", "10.90.0.72", 4000)
    # receive_rtp_stream("/tmp/input.wav", "0.0.0.0", 4000, 10)
