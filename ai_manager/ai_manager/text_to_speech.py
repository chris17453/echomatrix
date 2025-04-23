"""
Text-to-Speech generator for audio_manager.
Provides TTS functionality using OpenAI's API.
"""

import logging
import os
from pathlib import Path
import uuid
import openai

from .openai import init_openai_client

logger = logging.getLogger(__name__)



def generate_speech(text, voice, model, output_path, client=None):
    """
    Generate speech using OpenAI's TTS API and save it as WAV file.
    
    Args:
        text: Text to convert to speech
        voice: Voice to use
        model: TTS model to use
        output_path: Path where to save WAV file
        config: Configuration object with openai settings
        
    Returns:
        str: True on success or None on failure
    """
    try:
        
        # Ensure output directory exists
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        if not client:
            logger.error("No OpenAI client available")
            return None

        # Generate speech using OpenAI API
        logger.info(f"Generating TTS for: '{text[:50]}...' using voice: {voice}, model: {model}")
        
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format="wav"
        )
        
        # Save WAV file
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        logger.info(f"Saved WAV file: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error generating speech: {e}")
        return None