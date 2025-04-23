"""
Transcription module for audio_manager.
Provides audio transcription functionality using OpenAI's Whisper API.
"""

import os
import logging
import wave
import tempfile
from pathlib import Path
import soundfile as sf
import openai

logger = logging.getLogger(__name__)

def transcribe_audio(audio_data=None, audio_path=None, client=None):
    """
    Transcribe audio using OpenAI Whisper API
    
    Args:
        audio_data: Can be either raw binary data or numpy array
        audio_path: Optional existing file path that contains audio
        config: Configuration object with openai settings
        client: Optional pre-initialized OpenAI client
        
    Returns:
        The transcribed text or None on failure
    """
    logger.debug(f"Transcribing audio, data type: {type(audio_data) if audio_data else 'None'}, path: {audio_path}")

  
    if audio_data is None and (not audio_path or not os.path.exists(audio_path)):
        logger.error("No valid audio data or path provided")
        return None
    
    if not client:
        logger.error("No OpenAI client available")
        return None
    
    try:
        # If audio_path is provided and file exists, use it directly
        if audio_path and os.path.exists(audio_path):
            logger.debug(f"Using existing audio file: {audio_path}")
            with open(audio_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model=config.openai.whisper_model,
                    file=audio_file
                )
        # Otherwise, create a temporary file
        else:
            temp_dir = getattr(config, "temp_dir", "/tmp")
            sample_rate = getattr(config, "sample_rate", 44100)
            
            logger.debug(f"Creating temporary file for transcription in {temp_dir}")
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
                
                # If audio_data is binary, write directly
                if isinstance(audio_data, bytes):
                    f.write(audio_data)
                # Otherwise assume it's a numpy array
                else:
                    sf.write(f.name, audio_data, sample_rate, format='WAV')
                
            try:
                logger.debug(f"Opening temp file for transcription: {temp_path}")
                with open(temp_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model=config.openai.whisper_model,
                        file=audio_file
                    )
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        logger.info(f"Transcription result: {transcript.text}")
        return transcript.text
    
    except Exception as e:
        logger.error(f"Error in transcription: {e}")
        return None
