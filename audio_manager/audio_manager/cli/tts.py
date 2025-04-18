"""
TTS management commands for audio_manager CLI.
"""

import click
import logging
from ..audio_manager import AudioManager

logger = logging.getLogger(__name__)

# Pass AudioManager instance between commands
pass_audio_manager = click.make_pass_decorator(AudioManager)

@click.group(name='tts')
def tts_commands():
    """Generate and manage text-to-speech audio."""
    pass


@tts_commands.command('generate')
@click.argument('text', required=True)
@click.option('--ai-identity', type=int, help='AI identity ID to use for TTS (optional, uses default if not specified)')
@pass_audio_manager
def generate_tts(audio_manager, text, ai_identity):
    """Generate text-to-speech audio from TEXT using specified or default AI identity."""
    try:
        # If AI identity is specified, temporarily set it for this operation
        original_ai_identity = None
        if ai_identity:
            original_ai_identity = audio_manager.ai_identity_id
            audio_manager.set_ai_identity(ai_identity)
            click.echo(f"Using AI identity: {ai_identity}")
        
        # Generate TTS audio
        recording_id = audio_manager.generate_tts(text)
        
        if not recording_id:
            click.echo("Failed to generate TTS audio", err=True)
            return None
        
        # Restore original AI identity if needed
        if original_ai_identity:
            audio_manager.set_ai_identity(original_ai_identity)
        
        click.echo(f"TTS audio generated successfully with ID: {recording_id}")
        return recording_id
        
    except Exception as e:
        click.echo(f"Error generating TTS: {e}", err=True)
        return None
