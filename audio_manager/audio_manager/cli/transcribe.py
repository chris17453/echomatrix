"""
Transcription commands for audio_manager CLI.
"""

import click
import logging
import os
from pathlib import Path
from ..audio_manager import AudioManager

logger = logging.getLogger(__name__)

# Pass AudioManager instance between commands
pass_audio_manager = click.make_pass_decorator(AudioManager)

@click.group(name='transcribe')
def transcribe_commands():
    """Transcribe audio files to text."""
    pass

@transcribe_commands.command('file')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--register', is_flag=True, help='Register transcription in database')
@click.option('--user-identity', type=int, help='Associate with user identity ID')
@pass_audio_manager
def transcribe_file(audio_manager, file_path, register, user_identity):
    """Transcribe an audio file to text."""
    try:
        file_path = os.path.abspath(file_path)
        click.echo(f"Transcribing file: {file_path}")
        
        # Set user identity if provided
        if user_identity:
            audio_manager.set_user_identity(user_identity)
        
        # Transcribe the audio file
        result = audio_manager.transcribe(
            audio_path=file_path,
            register=register
        )
        
        if not result:
            click.echo("Transcription failed", err=True)
            return None
            
        # If registered, the result is a recording ID
        if register:
            click.echo(f"Transcription registered with ID: {result}")
            # Get the text from the recording
            recording = audio_manager.get_recording(result)
            if recording:
                click.echo(f"Transcription result:\n{recording.text}")
        else:
            click.echo(f"Transcription result:\n{result}")
        
        return result
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return None

@transcribe_commands.command('recording')
@click.argument('recording_id')
@pass_audio_manager
def transcribe_recording(audio_manager, recording_id):
    """Transcribe an existing recording by ID."""
    try:
        click.echo(f"Transcribing recording: {recording_id}")
        
        # Transcribe the recording
        result = audio_manager.transcribe(recording_id=recording_id)
        
        if not result:
            click.echo("Transcription failed", err=True)
            return None
            
        # Get the updated text
        recording = audio_manager.get_recording(recording_id)
        if recording:
            click.echo(f"Transcription result:\n{recording.text}")
        
        return recording_id
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return None