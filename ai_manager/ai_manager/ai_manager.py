import logging
import os
from pathlib import Path

from .chat import chat
from .openai import init_openai_client
from .prompts import get_prompts
from .text_to_speech import generate_speech
from .transcribe import transcribe_audio

class AIManager:
    """
    Wrapper class for AI Manager functionality.
    Initializes OpenAI client and provides access to all functions.
    """
    
    def __init__(self, config):
        """
        Initialize the AI Manager with configuration.
        
        Args:
            config: Configuration object with OpenAI settings
        """
        self.config = config
        self.client = init_openai_client(config)
        self.prompts = get_prompts(config)
        self.logger = logging.getLogger(__name__)
        
        if not self.client:
            self.logger.error("Failed to initialize OpenAI client")
            
    def chat(self, prompt_name, data={}, model=None):
        """
        Generate chat completion.
        
        Args:
            prompt_name: Name of the prompt to use
            data: Dictionary of data to format the prompt with
            model: OpenAI model to use (defaults to config value)
            
        Returns:
            Generated text or None on failure
        """
        if not model:
            model = self.config.openai.chat_model
            
        return chat(
            prompt_name=prompt_name,
            data=data,
            model=model,
            client=self.client,
            prompts=self.prompts
        )
    
    def generate_speech(self, text, voice=None, model=None, output_path=None):
        """
        Generate speech from text.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (defaults to config value)
            model: TTS model to use (defaults to config value)
            output_path: Path where to save WAV file (optional)
            
        Returns:
            True on success or None on failure
        """
        if not voice:
            voice = self.config.openai.tts_voice
            
        if not model:
            model = self.config.openai.tts_model
            
        if not output_path:
            # Generate a default output path if none provided
            output_dir = Path(self.config.output_dir) / "speech"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"speech_{os.urandom(4).hex()}.wav"
            
        return generate_speech(
            text=text,
            voice=voice,
            model=model,
            output_path=str(output_path),
            client=self.client
        )
    
    def transcribe_audio(self, audio_data=None, audio_path=None):
        """
        Transcribe audio using Whisper API.
        
        Args:
            audio_data: Raw binary data or numpy array
            audio_path: Path to audio file
            
        Returns:
            Transcribed text or None on failure
        """
        return transcribe_audio(
            audio_data=audio_data,
            audio_path=audio_path,
            client=self.client
        )
        
    def get_prompts(self):
        """
        Get available prompts.
        
        Returns:
            Dictionary of prompts
        """
        return self.prompts