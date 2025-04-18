import os
import uuid
import logging
import tempfile
import soundfile as sf
from echomatrix.config import config, client

logger = logging.getLogger('echomatrix_transcriber')

def transcribe(audio_data, audio_path=None):
    """
    Transcribe audio using OpenAI Whisper API
    
    Args:
        audio_data: Can be either raw binary data or numpy array
        audio_path: Optional existing file path that contains audio
        
    Returns:
        The transcribed text
    """
    logger.debug(f"Transcribing audio, data type: {type(audio_data)}")
    
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
            logger.debug("Creating temporary file for transcription")
            with tempfile.NamedTemporaryFile(suffix=".wav", dir=config.temp_dir, delete=False) as f:
                temp_path = f.name
                
                # If audio_data is binary, write directly
                if isinstance(audio_data, bytes):
                    f.write(audio_data)
                # Otherwise assume it's a numpy array
                else:
                    sf.write(f.name, audio_data, config.sample_rate, format='WAV')
                
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
        return "Transcription error"