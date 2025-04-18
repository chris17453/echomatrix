"""
Text-to-Speech generator for audio_manager.
Provides TTS functionality using OpenAI's API.
"""

import logging
import os
from pathlib import Path
import uuid
from openai import OpenAI

logger = logging.getLogger(__name__)

def init_openai_client(config):
    """
    Initialize the OpenAI client using configuration.
    
    Args:
        config: Configuration object with openai settings
        
    Returns:
        OpenAI: Initialized OpenAI client or None on failure
    """
    try:
        # Access configuration using dot notation
        client = OpenAI(
            api_key=config.openai.api_key,
            organization=config.openai.organization_id
        )
        return client
    except Exception as e:
        logger.error(f"Error initializing OpenAI client: {e}")
        return None

def generate_speech(text, voice, model, output_path, config=None):
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
        # Initialize OpenAI client
        client = init_openai_client(config)
        if not client:
            logger.error("Failed to initialize OpenAI client")
            return None
        
        # Ensure output directory exists
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
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
        return True
        
    except Exception as e:
        logger.error(f"Error generating speech: {e}")
        return None