# audio_manager/audio_manager/cli/recording.py
"""
Recording management commands for audio_manager CLI.
"""

import click
import logging
from ..audio_manager import AudioManager

logger = logging.getLogger(__name__)

# Pass AudioManager instance between commands
pass_audio_manager = click.make_pass_decorator(AudioManager)

@click.group(name='recording')
def recording_commands():
    """Manage audio recordings."""
    pass


@recording_commands.command('register')
@click.option('--text', help='Transcription text of the audio')
# Remove the model option
@click.option('--ai-generated', is_flag=True, help='Flag if audio was AI-generated')
@click.option('--user-recorded', is_flag=True, help='Flag if audio was user-recorded')
@click.option('--ai-identity-id', type=int, help='ID of the AI identity used')
@click.option('--user-identity-id', type=int, help='ID of the user identity')
@click.option('--location', default='local', help='Storage location')
@click.option('--audio-file', help='Path to the audio file')
@click.option('--transcript-file', help='Path to the transcript file')
@click.option('--metadata-file', help='Path to any additional metadata file')
@click.option('--session-id', help='Session identifier')
@pass_audio_manager
def register_recording(audio_manager, **kwargs):
    """Register a new audio recording with metadata."""
    try:
        file_paths = {}
        
        if kwargs['audio_file']:
            file_paths['audio'] = kwargs['audio_file']
        if kwargs['transcript_file']:
            file_paths['transcript'] = kwargs['transcript_file']
        if kwargs['metadata_file']:
            file_paths['metadata'] = kwargs['metadata_file']
        
        # Remove file options from kwargs before passing to register_recording
        for key in ['audio_file', 'transcript_file', 'metadata_file']:
            kwargs.pop(key, None)
        
        # If ai_identity_id is provided but model isn't, get the model from AI identity
        # This is no longer needed since model has been removed
        
        recording_id = audio_manager.register_recording(
            file_paths=file_paths,
            **kwargs
        )
        
        click.echo(f"Recording registered successfully with ID: {recording_id}")
        return recording_id
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return None
 
@recording_commands.command('list')
@click.option('--ai-generated', is_flag=True, help='Filter for AI-generated recordings')
@click.option('--user-recorded', is_flag=True, help='Filter for user-recorded recordings')
@click.option('--location', help='Filter by storage location')
@click.option('--show-files', is_flag=True, help='Show associated files')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@pass_audio_manager
def list_recordings(audio_manager, ai_generated, user_recorded, location, show_files, output_json):
    """List all recordings with optional filters."""
    try:
        recordings = audio_manager.list_all()
        # Apply filters if specified
        if ai_generated:
            recordings = [r for r in recordings if r.ai_generated]
        if user_recorded:
            recordings = [r for r in recordings if r.user_recorded]
        if location:
            recordings = [r for r in recordings if r.location == location]
        
        if not recordings:
            click.echo("No recordings found")
            return []
        
        if output_json:
            import json
            output = []
            for rec in recordings:
                rec_dict = {
                    'id': rec.id, 
                    'session_id': rec.session_id,
                    'location': rec.location,
                    'ai_generated': rec.ai_generated,
                    'user_recorded': rec.user_recorded,
                    'text': rec.text,
                    'timestamp': rec.timestamp,
                    'ai_identity_id': rec.ai_identity_id,
                    'user_identity_id': rec.user_identity_id
                }
                
                # Add files information if requested
                if show_files:
                    files = rec.get_files(audio_manager.db)
                    if files:
                        rec_dict['files'] = [
                            {'file_type': f.file_type, 'path': f.path} 
                            for f in files
                        ]
                
                output.append(rec_dict)
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(f"Found {len(recordings)} recordings:")
            for recording in recordings:
                type_info = []
                if recording.ai_generated:
                    type_info.append("AI-generated")
                if recording.user_recorded:
                    type_info.append("User-recorded")
                
                # Line 1: Main identifiers and type info
                click.echo(f"ID: {recording.id} | Location: {recording.location} | {', '.join(type_info)}")
                
                # Line 2: Session and timestamp information
                click.echo(f"  Session: {recording.session_id} | Timestamp: {recording.timestamp}")
                
                # Line 3: Identity information
                ai_id_info = f"AI ID: {recording.ai_identity_id}" if recording.ai_identity_id else "AI ID: None"
                user_id_info = f"User ID: {recording.user_identity_id}" if recording.user_identity_id else "User ID: None"
                click.echo(f"  {ai_id_info} | {user_id_info}")
                
                # Line 4: Text content (truncated if necessary)
                if recording.text:
                    if len(recording.text) > 50:
                        click.echo(f"  Text: {recording.text[:50]}...")
                    else:
                        click.echo(f"  Text: {recording.text}")
                
                # Add files if requested
                if show_files:
                    files = recording.get_files(audio_manager.db)
                    if files:
                        click.echo("  Files:")
                        for file in files:
                            click.echo(f"    - {file.file_type}: {file.path}")
                
                # Add separator between recordings for better readability
                click.echo("  " + "-" * 60)
        
        return recordings
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return None


@recording_commands.command('find')
@click.option('--id', 'recording_id', help='Recording ID to search for')
@click.option('--text', help='Text content to search for')
@click.option('--ai-identity', type=int, help='Optional AI identity ID to filter by when searching by text')
@click.option('--show-files', is_flag=True, help='Show associated files')
@pass_audio_manager
def find_recording(audio_manager, recording_id, text, ai_identity, show_files):
    """Find a recording by ID or text content."""
    try:
        if recording_id:
            recording = audio_manager.get_recording(recording_id)
            if not recording:
                click.echo(f"No recording found with ID: {recording_id}", err=True)
                return None
        elif text:
            if ai_identity:
                recording = audio_manager.find_by_text_and_entity(text, ai_identity)
                if not recording:
                    click.echo(f"No recording found with the specified text and AI identity", err=True)
                    return None
            else:
                recording = audio_manager.find_by_text(text)
                if not recording:
                    click.echo(f"No recording found with the specified text", err=True)
                    return None
        else:
            click.echo("Error: Either --id or --text must be provided", err=True)
            return None
        
        # Display recording information
        click.echo(f"Recording ID: {recording.id}")
        click.echo(f"Text: {recording.text}")
        # Remove model display
        click.echo(f"AI Generated: {recording.ai_generated}")
        click.echo(f"User Recorded: {recording.user_recorded}")
        click.echo(f"Location: {recording.location}")
        click.echo(f"Timestamp: {recording.timestamp}")
        
        # Display associated files if requested
        if show_files:
            files = recording.get_files(audio_manager.db)
            if files:
                click.echo("\nAssociated Files:")
                for file in files:
                    click.echo(f"  - {file.file_type}: {file.path}")
        
        return recording
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return None

@recording_commands.command('find-by-ai-text')
@click.option('--text', required=True, help='Text content to search for')
@click.option('--ai-identity-id', required=True, type=int, help='AI identity ID to filter by')
@click.option('--show-files', is_flag=True, help='Show associated files')
@pass_audio_manager
def find_by_ai_text(audio_manager, text, ai_identity_id, show_files):
    """Find a recording by text content and AI identity ID."""
    try:
        recording = audio_manager.find_by_ai_text(text, ai_identity_id)
        if not recording:
            click.echo(f"No recording found with text: '{text}' and AI identity ID: {ai_identity_id}", err=True)
            return None
        
        # Display recording information
        click.echo(f"Recording ID: {recording.id}")
        click.echo(f"Text: {recording.text}")
        click.echo(f"AI Generated: {recording.ai_generated}")
        click.echo(f"User Recorded: {recording.user_recorded}")
        click.echo(f"AI Identity ID: {recording.ai_identity_id}")
        click.echo(f"User Identity ID: {recording.user_identity_id}")
        click.echo(f"Location: {recording.location}")
        click.echo(f"Timestamp: {recording.timestamp}")
        
        # Display associated files if requested
        if show_files:
            files = recording.get_files(audio_manager.db)
            if files:
                click.echo("\nAssociated Files:")
                for file in files:
                    click.echo(f"  - {file.file_type}: {file.path}")
        
        return recording
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return None


@recording_commands.command('push')
@click.argument('recording_id')
@click.option('--destination', help='Destination location name (from config)')
@pass_audio_manager
def push_recording(audio_manager, recording_id, destination):
    """Push a recording to a remote destination."""
    try:
        recording = audio_manager.get_recording(recording_id)
        if not recording:
            click.echo(f"No recording found with ID: {recording_id}", err=True)
            return False
        
        # Verify local location exists in config
        if 'local' not in audio_manager.config.locations:
            click.echo("Error: 'local' location is required in configuration for push operations", err=True)
            return False
            
        # Verify local path exists
        local_config = audio_manager.config.locations.local
        if not local_config.get('path'):
            click.echo("Error: 'path' is required in local configuration for push operations", err=True)
            return False
        
        # If destination specified, update the recording location
        if destination:
            # Check if destination exists in config
            if destination not in audio_manager.config.locations:
                click.echo(f"Destination {destination} not found in configuration", err=True)
                return False
            
            # Update recording location in database
            audio_manager.update_recording(recording_id, {'location': destination})
            recording.location = destination
        
        audio_manager.push_recording(recording_id)
        click.echo(f"Recording {recording_id} pushed successfully to {recording.location}")
        return True
        
    except Exception as e:
        click.echo(f"Error pushing recording: {e}", err=True)
        return False


@recording_commands.command('pull')
@click.argument('recording_id')
@pass_audio_manager
def pull_recording(audio_manager, recording_id):
    """Pull a recording from its remote location to local storage."""
    try:
        recording = audio_manager.get_recording(recording_id)
        if not recording:
            click.echo(f"No recording found with ID: {recording_id}", err=True)
            return False
        
        # Verify local location exists in config
        if 'local' not in audio_manager.config.locations:
            click.echo("Error: 'local' location is required in configuration for pull operations", err=True)
            return False
            
        # Verify local path exists
        local_config = audio_manager.config.locations.local
        if not local_config.get('path'):
            click.echo("Error: 'path' is required in local configuration for pull operations", err=True)
            return False
        
        if recording.location == 'local':
            click.echo(f"Recording {recording_id} is already in local storage")
            return True
        
        audio_manager.pull_recording(recording_id)
        click.echo(f"Recording {recording_id} pulled successfully from {recording.location}")
        return True
        
    except Exception as e:
        click.echo(f"Error pulling recording: {e}", err=True)
        return False


@recording_commands.command('delete')
@click.argument('recording_id')
@click.option('--force', is_flag=True, help='Force deletion without confirmation')
@pass_audio_manager
def delete_recording(audio_manager, recording_id, force):
    """Delete a recording and its associated files."""
    try:
        recording = audio_manager.get_recording(recording_id)
        if not recording:
            click.echo(f"No recording found with ID: {recording_id}", err=True)
            return False
        
        if not force and not click.confirm(f"Are you sure you want to delete recording {recording_id}?"):
            click.echo("Operation cancelled")
            return False
        
        success = audio_manager.delete_recording(recording_id)
        if success:
            click.echo(f"Recording {recording_id} deleted successfully")
        else:
            click.echo(f"Failed to delete recording {recording_id}", err=True)
        
        return success
    except Exception as e:
        click.echo(f"Error deleting recording: {e}", err=True)
        return False