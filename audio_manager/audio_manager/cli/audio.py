"""
Audio analysis commands for audio_manager CLI.
"""

import click
import logging
import os
import json
from pathlib import Path
from ..audio_manager import AudioManager

logger = logging.getLogger(__name__)

# Pass AudioManager instance between commands
pass_audio_manager = click.make_pass_decorator(AudioManager)

@click.group(name='audio')
def audio_commands():
    """Audio file analysis and manipulation commands."""
    pass

@audio_commands.command('analyze')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--sample-rate', type=int, default=8000, help='Sample rate in Hz (default: 8000)')
@click.option('--sample-width', type=int, default=2, help='Sample width in bytes (default: 2)')
@click.option('--sample-duration', type=float, default=1.0, help='Duration to analyze in seconds (default: 1.0)')
@pass_audio_manager
def analyze_audio_level(audio_manager, file_path, sample_rate, sample_width, sample_duration):
    """Analyze audio level of a PCM file."""
    try:
        file_path = os.path.abspath(file_path)
        click.echo(f"Analyzing audio level for file: {file_path}")
        
        # Analyze the audio level
        result = audio_manager.analyze_pcm_audio_level(
            file_path=file_path,
            sample_rate=sample_rate,
            sample_width=sample_width,
            sample_duration=sample_duration
        )
        
        click.echo(f"Audio level (RMS): {result}")
        return result
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return None

@audio_commands.command('extract')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--start-byte', type=int, required=True, help='Starting byte position in the file')
@click.option('--end-byte', type=int, required=True, help='Ending byte position in the file')
@click.option('--start-ms', type=int, help='Start time in milliseconds')
@click.option('--end-ms', type=int, help='End time in milliseconds')
@click.option('--duration-ms', type=int, help='Duration in milliseconds')
@click.option('--sample-rate', type=int, default=8000, help='Sample rate in Hz (default: 8000)')
@click.option('--sample-width', type=int, default=2, help='Sample width in bytes (default: 2)')
@click.option('--output', type=click.Path(), help='Output file path for the extracted segment')
@pass_audio_manager
def extract_audio_segment_cli(audio_manager, file_path, start_byte, end_byte, start_ms, end_ms, 
                           duration_ms, sample_rate, sample_width, output):
    """Extract an audio segment from a PCM file."""
    try:
        file_path = os.path.abspath(file_path)
        click.echo(f"Extracting audio segment from file: {file_path}")
        
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
            
        # Extract the audio segment
        audio_data, segment_info = audio_manager.extract_audio_segment(
            file_path=file_path,
            speech_segment=speech_segment,
            sample_rate=sample_rate,
            sample_width=sample_width
        )
        
        if audio_data is None:
            click.echo("Extraction failed", err=True)
            return None
            
        # Output the segment information
        click.echo(f"Segment information: {json.dumps(segment_info, indent=2)}")
        
        # Save the extracted segment if output path is provided
        if output:
            output_path = os.path.abspath(output)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            click.echo(f"Extracted segment saved to: {output_path}")
        
        return audio_data, segment_info
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return None