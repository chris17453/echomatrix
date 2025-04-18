# echomatrix/echomatrix/audioplayer.py

import os
import logging
import subprocess
from pydub import AudioSegment

logger = logging.getLogger('echomatrix_audioplayer')

def play_audio(audio_path):
    """
    Play an audio file using the system's audio player
    
    Args:
        audio_path (str): Path to the audio file
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found: {audio_path}")
        return False
    
    try:
        if audio_path.endswith('.mp3'):
            # Use play command from sox if available
            subprocess.run(['play', audio_path], check=True)
        elif audio_path.endswith('.wav'):
            # Use aplay for WAV files
            subprocess.run(['aplay', audio_path], check=True)
        else:
            logger.error(f"Unsupported audio format: {audio_path}")
            return False
        
        logger.info(f"Audio played successfully: {audio_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error playing audio: {e}")
        return False
    except FileNotFoundError:
        logger.error("Required audio player not found. Install sox or alsa-utils.")
        return False

def convert_mp3_to_wav(mp3_path, target_sample_rate=8000):
    """
    Convert an MP3 file to WAV format suitable for Asterisk
    
    Args:
        mp3_path (str): Path to the MP3 file
        target_sample_rate (int): Target sample rate for the WAV file
    
    Returns:
        str: Path to the converted WAV file, or None if conversion failed
    """
    if not os.path.exists(mp3_path):
        logger.error(f"MP3 file not found: {mp3_path}")
        return None
    
    try:
        # Get the WAV path by replacing the extension
        wav_path = os.path.splitext(mp3_path)[0] + '.wav'
        
        # Convert using pydub
        audio = AudioSegment.from_mp3(mp3_path)
        
        # Set to mono and target sample rate
        audio = audio.set_channels(1).set_frame_rate(target_sample_rate)
        
        # Export as PCM 16-bit WAV
        audio.export(wav_path, format='wav')
        
        logger.info(f"Converted MP3 to WAV: {wav_path}")
        return wav_path
    
    except Exception as e:
        logger.error(f"Error converting MP3 to WAV: {e}")
        return None