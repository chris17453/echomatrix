"""
Enhanced CLI for audio_manager package with improved usability.
Main entry point that imports and registers command groups.
"""

import os
import sys
import logging
import click
from pathlib import Path

from ..audio_manager import AudioManager
from . import ai
from . import user
from . import recording
from . import config
from . import tts 
from . import transcribe


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pass context between command groups
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('--config', help='Path to configuration file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.version_option(version='0.1.0', prog_name='audio_manager')
@click.pass_context
def cli(ctx, config, verbose):
    """Audio Manager CLI - Enterprise Audio Recording Management System.
    
    Manage audio recordings, identities, and storage with a robust and user-friendly interface.
    """
    # Configure logging based on verbosity
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize AudioManager with config
    ctx.obj = AudioManager(config_path=config)

# Register command groups
cli.add_command(ai.ai_commands)
cli.add_command(user.user_commands)
cli.add_command(recording.recording_commands)
cli.add_command(config.config_commands)
cli.add_command(tts.tts_commands)  
cli.add_command(transcribe.transcribe_commands)  


if __name__ == "__main__":
    cli()
