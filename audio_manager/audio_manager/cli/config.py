# audio_manager/audio_manager/cli/config.py
"""
Configuration management commands for audio_manager CLI.
"""

import click
import logging
from ..audio_manager import AudioManager

logger = logging.getLogger(__name__)

# Pass AudioManager instance between commands
pass_audio_manager = click.make_pass_decorator(AudioManager)

@click.group(name='config')
def config_commands():
    """View or update configuration."""
    pass


@config_commands.command('show')
@pass_audio_manager
def show_config(audio_manager):
    """Show current configuration."""
    try:
        click.echo("Current Configuration:")
        click.echo(f"Database Path: {audio_manager.config.db_path}")
        click.echo("Locations:")
        
        for location, config in audio_manager.config:
            click.echo(f"  - {location}: {config}")
        
        return audio_manager.config
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return None


@config_commands.command('update')
@click.option('--config-path', required=True, help='Path to new configuration file')
@pass_audio_manager
def update_config(audio_manager, config_path):
    """Update configuration from a file."""
    try:
        # Reinitialize with new config
        audio_manager.config_manager = audio_manager.config_manager.__class__(config_path)
        audio_manager.config = audio_manager.config_manager.get()
        click.echo(f"Configuration updated from {config_path}")
        
        return audio_manager.config
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return None