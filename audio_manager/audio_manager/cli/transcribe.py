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

@transcribe_commands.command('segment')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--start-byte', type=int, required=True, help='Starting byte position in the file')
@click.option('--end-byte', type=int, required=True, help='Ending byte position in the file')
@click.option('--start-ms', type=int, help='Start time in milliseconds')
@click.option('--end-ms', type=int, help='End time in milliseconds')
@click.option('--duration-ms', type=int, help='Duration in milliseconds')
@pass_audio_manager
def transcribe_segment_cli(audio_manager, file_path, start_byte, end_byte, start_ms, end_ms, duration_ms):
    """Transcribe a specific segment of an audio file."""
    try:
        file_path = os.path.abspath(file_path)
        click.echo(f"Transcribing segment from file: {file_path}")
        
        # Create speech segment dictionary
        speech_segment = {
            'pcm_start_byte': start_byte,
            'pcm_end_byte': end_byte
        }
        
        if start_ms is not None:
            speech_segment['start_ms'] = start_ms
        if end_ms is not None:
            speech_segment['end_ms'] = end_ms
        if duration_ms is not None:
            speech_segment['duration_ms'] = duration_ms
            
        # Transcribe the segment
        result = audio_manager.transcribe_segment(
            file_path=file_path,
            speech_segment=speech_segment
        )
        
        if not result:
            click.echo("Segment transcription failed", err=True)
            return None
            
        click.echo(f"Segment transcription result:\n{result}")
        return result
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return None        