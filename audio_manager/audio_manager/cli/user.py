# audio_manager/audio_manager/cli/user.py
"""
User Identity management commands for audio_manager CLI.
"""

import click
import logging
from ..audio_manager import AudioManager

logger = logging.getLogger(__name__)

# Pass AudioManager instance between commands
pass_audio_manager = click.make_pass_decorator(AudioManager)

@click.group(name='users')
def user_commands():
    """Manage user identities."""
    pass


@user_commands.command('register')
@click.option('--first-name', help='User\'s first name')
@click.option('--middle-name', help='User\'s middle name')
@click.option('--last-name', help='User\'s last name')
@click.option('--affiliation', help='User\'s organizational affiliation')
@click.option('--phone', help='User\'s phone number')
@click.option('--username', help='User\'s username')
@pass_audio_manager
def register_user_identity(audio_manager, first_name, middle_name, last_name, 
                         affiliation, phone, username):
    """Register a new user identity."""
    try:
        identity_id = audio_manager.register_user_identity(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            affiliation=affiliation,
            phone=phone,
            user_name=username
        )
        
        click.echo(f"User identity registered successfully with ID: {identity_id}")
        return identity_id
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return None


@user_commands.command('list')
@click.option('--name', help='Filter by name')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@pass_audio_manager
def list_user_identities(audio_manager, name, output_json):
    """List all user identities."""
    try:
        # Get all users and filter as needed
        if name:
            from ..db.user_identity import UserIdentityRecord
            users = UserIdentityRecord.find_by_name(audio_manager.db, name)
        else:
            from ..db.user_identity import UserIdentityRecord
            users = UserIdentityRecord.get_all(audio_manager.db)
        
        if not users:
            click.echo("No user identities found")
            return []
        
        if output_json:
            import json
            output = []
            for user in users:
                user_dict = {
                    'id': user.id,
                    'first_name': user.first_name,
                    'middle_name': user.middle_name,
                    'last_name': user.last_name,
                    'affiliation': user.affiliation,
                    'phone': user.phone,
                    'username': user.user_name
                }
                output.append(user_dict)
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(f"Found {len(users)} user identities:")
            for user in users:
                click.echo(f"ID: {user.id} | Name: {user.full_name} | " 
                      f"Username: {user.user_name}")
                if user.affiliation:
                    click.echo(f"  Affiliation: {user.affiliation}")
        
        return users
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return None