# audio_manager/audio_manager/cli/identity.py
"""
AI Identity management commands for audio_manager CLI.
"""

import click
import logging
from ..audio_manager import AudioManager

logger = logging.getLogger(__name__)

# Pass AudioManager instance between commands
pass_audio_manager = click.make_pass_decorator(AudioManager)

@click.group(name='ai')
def ai_commands():
    """Manage AI identities."""
    pass


@ai_commands.command('register')
@click.option('--model', required=True, help='AI model identifier')
@click.option('--voice', help='AI voice identifier')
@click.option('--provider', help='AI provider name')
@click.option('--instruction', help='AI instruction or prompt')
@pass_audio_manager
def register_ai_identity(audio_manager, model, voice, provider, instruction):
    """Register a new AI identity."""
    try:
        identity_id = audio_manager.register_ai_identity(
            model=model,
            voice=voice,
            provider=provider,
            instruction=instruction
        )
        
        click.echo(f"AI identity registered successfully with ID: {identity_id}")
        return identity_id
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return None


@ai_commands.command('list')
@click.option('--model', help='Filter by AI model')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@pass_audio_manager
def list_ai_identities(audio_manager, model, output_json):
    """List all AI identities."""
    try:
        if model:
            ai_identities = audio_manager.find_ai_identities_by_model(model)
        else:
            ai_identities = audio_manager.list_ai_identities()
        
        if not ai_identities:
            click.echo("No AI identities found")
            return []
        
        if output_json:
            import json
            output = []
            for identity in ai_identities:
                ai_dict = {
                    'id': identity.id,
                    'model': identity.model,
                    'voice': identity.voice,
                    'provider': identity.provider,
                    'instruction': identity.instruction
                }
                output.append(ai_dict)
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(f"Found {len(ai_identities)} AI identities:")
            for identity in ai_identities:
                click.echo(f"ID: {identity.id} | Model: {identity.model} | " 
                      f"Voice: {identity.voice} | Provider: {identity.provider}")
                
                # Show instruction if available and not too long
                if identity.instruction:
                    instruction = identity.instruction
                    if len(instruction) > 50:
                        instruction = instruction[:50] + "..."
                    click.echo(f"  Instruction: {instruction}")
        
        return ai_identities
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return None


@ai_commands.command('update')
@click.argument('identity_id', type=int)
@click.option('--model', help='AI model identifier')
@click.option('--voice', help='AI voice identifier')
@click.option('--provider', help='AI provider name')
@click.option('--instruction', help='AI instruction or prompt')
@pass_audio_manager
def update_ai_identity(audio_manager, identity_id, model, voice, provider, instruction):
    """Update an existing AI identity."""
    try:
        ai_identity = audio_manager.get_ai_identity(identity_id)
        if not ai_identity:
            click.echo(f"AI identity with ID {identity_id} not found", err=True)
            return False
        
        updates = {}
        if model:
            updates['model'] = model
        if voice:
            updates['voice'] = voice
        if provider:
            updates['provider'] = provider
        if instruction:
            updates['instruction'] = instruction
        
        if not updates:
            click.echo("No updates provided")
            return False
        
        success = audio_manager.update_ai_identity(identity_id, updates)
        if success:
            click.echo(f"AI identity {identity_id} updated successfully")
        else:
            click.echo(f"Failed to update AI identity {identity_id}", err=True)
        
        return success
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return False


@ai_commands.command('delete')
@click.argument('identity_id', type=int)
@click.option('--force', is_flag=True, help='Force deletion without confirmation')
@pass_audio_manager
def delete_ai_identity(audio_manager, identity_id, force):
    """Delete an AI identity."""
    try:
        ai_identity = audio_manager.get_ai_identity(identity_id)
        if not ai_identity:
            click.echo(f"AI identity with ID {identity_id} not found", err=True)
            return False
        
        if not force and not click.confirm(f"Are you sure you want to delete AI identity {identity_id}?"):
            click.echo("Operation cancelled")
            return False
        
        success = audio_manager.delete_ai_identity(identity_id)
        if success:
            click.echo(f"AI identity {identity_id} deleted successfully")
        else:
            click.echo(f"Failed to delete AI identity {identity_id}", err=True)
        
        return success
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return False