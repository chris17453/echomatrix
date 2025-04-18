import os
import logging

logger = logging.getLogger('echomatrix_utils')

def cleanup_temp_file(path):
    """Safely delete a temporary file"""
    if not path:
        return
        
    try:
        if os.path.exists(path):
            logger.debug(f"Deleting temporary file: {path}")
            os.remove(path)
    except Exception as e:
        logger.error(f"Failed to delete temp file {path}: {e}")

def get_asterisk_sound_path():
    """Get path to Asterisk sounds directory"""
    # This path may need to be adjusted based on your Asterisk configuration
    return "/var/lib/asterisk/sounds"

def prepare_path_for_asterisk(full_path):
    """
    Strip path and extension for Asterisk commands
    
    Asterisk commands like STREAM FILE expect just the filename 
    without extension and often relative to sounds directory
    """
    if not full_path:
        return None
        
    # Get just the filename without path or extension
    filename = os.path.basename(full_path)
    basename, _ = os.path.splitext(filename)
    
    return basename