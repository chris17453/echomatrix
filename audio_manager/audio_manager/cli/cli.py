"""
Enhanced CLI for audio_manager package with improved usability.
Main entry point that imports and registers command groups.
"""

import os
import sys
import logging
import click
from pathlib import Path

parent_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)),"..","config_manager"))
sys.path.append(parent_dir)

from ..audio_manager import AudioManager
import config_manager

from . import ai
from . import user
from . import recording
from . import config
from . import tts 
from . import transcribe
from . import audio




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
    self.config_manager = config_manager.Config(config_path=config_path, default_config=default_config, env_prefix='AUDIO_MANAGER_')
        
    ctx.obj = AudioManager(config_path=config)

# Register command groups
cli.add_command(ai.ai_commands)
cli.add_command(user.user_commands)
cli.add_command(recording.recording_commands)
cli.add_command(config.config_commands)
cli.add_command(tts.tts_commands)  
cli.add_command(transcribe.transcribe_commands)  
cli.add_command(audio.audio_commands)

if __name__ == "__main__":
    cli()
