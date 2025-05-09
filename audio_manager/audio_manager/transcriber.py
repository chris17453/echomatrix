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
from openai import OpenAI
from .sound import extract_audio_segment

logger = logging.getLogger(__name__)

def transcribe_audio(audio_data=None, audio_path=None, config=None):
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

  
    # Get OpenAI client
    client = OpenAI(
        api_key=config.openai.api_key,
        organization=config.openai.organization_id
    )

    if audio_data is None and (not audio_path or not os.path.exists(audio_path)):
        logger.error("No valid audio data or path provided")
        return None
    
    # Use provided client or initialize a new one
    if not client and config:
        try:
            client = OpenAI(
                api_key=config.openai.api_key,
                organization=config.openai.organization_id
            )
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {e}")
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

def transcribe_segment(file_path, speech_segment, config=None):
    """
    Extract an audio segment and transcribe it using OpenAI
    """
    # Extract the audio segment
    audio_data, segment_info = extract_audio_segment(
        file_path, 
        speech_segment,
        sample_rate=getattr(config, 'sample_rate', 8000),
        sample_width=getattr(config, 'sample_width', 2)
    )
    
    if audio_data is None:
        logger.error("Failed to extract audio segment")
        return None
    
    # Convert raw PCM to WAV with proper headers
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        temp_path = temp_wav.name
        
        # Create a proper WAV file with headers
        with wave.open(temp_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(getattr(config, 'sample_width', 2))
            wav_file.setframerate(getattr(config, 'sample_rate', 8000))
            wav_file.writeframes(audio_data)
    
    try:
        # Send the WAV file for transcription
        result = transcribe_audio(
            audio_path=temp_path,
            config=config
        )
        return result
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)  