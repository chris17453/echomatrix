# echomatrix/echomatrix/system_checks.py

import os
import logging
import subprocess
import shutil
import sys

logger = logging.getLogger('echomatrix_system')

def check_dependencies():
    """
    Check that all system dependencies are installed
    
    Returns:
        bool: True if all dependencies are available, False otherwise
    """
    missing = []
    
    # Check for Python packages
    try:
        import pydub
        import aiohttp
        import websockets
        import yaml
        import soundfile
    except ImportError as e:
        missing.append(f"Python package: {str(e).split()[-1]}")
    
    # Check for system commands
    commands = ['sox', 'play', 'aplay', 'ffmpeg']
    for cmd in commands:
        if not shutil.which(cmd):
            missing.append(f"System command: {cmd}")
    
    # Report results
    if missing:
        logger.error("Missing dependencies:")
        for dep in missing:
            logger.error(f" - {dep}")
        
        logger.error("""
To install missing dependencies:

# For Python packages
pip install pydub aiohttp websockets pyyaml soundfile

# For system commands (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y sox alsa-utils ffmpeg

# For system commands (CentOS/RHEL)
sudo yum install -y sox alsa-utils ffmpeg
""")
        return False
    
    logger.info("All dependencies are available")
    return True

def create_required_directories(config):
    """
    Create any required directories that don't exist
    
    Args:
        config: Configuration object with folder paths
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create audio directory if it doesn't exist
        audio_dir = 'audio'
        if not os.path.exists(audio_dir):
            os.makedirs(audio_dir, exist_ok=True)
            logger.info(f"Created directory: {audio_dir}")
        
        # Create model directories
        os.makedirs(os.path.join(audio_dir, 'alloy'), exist_ok=True)
        os.makedirs(os.path.join(audio_dir, 'echo'), exist_ok=True)
        os.makedirs(os.path.join(audio_dir, 'nova'), exist_ok=True)
        os.makedirs(os.path.join(audio_dir, 'shimmer'), exist_ok=True)
        
        # Create recordings directory if specified and doesn't exist
        if hasattr(config, 'folders') and hasattr(config.folders, 'recordings'):
            if not os.path.exists(config.folders.recordings):
                os.makedirs(config.folders.recordings, exist_ok=True)
                logger.info(f"Created directory: {config.folders.recordings}")
        
        # Create temp directory if needed
        temp_dir = None
        if hasattr(config, 'temp_dir'):
            temp_dir = config.temp_dir
        elif hasattr(config, 'folders') and hasattr(config.folders, 'temp_dir'):
            temp_dir = config.folders.temp_dir
        
        if temp_dir and not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)
            logger.info(f"Created directory: {temp_dir}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error creating directories: {e}")
        return False

if __name__ == "__main__":
    # Set up logging when run directly
    logging.basicConfig(level=logging.INFO)
    
    # Run checks
    check_dependencies()