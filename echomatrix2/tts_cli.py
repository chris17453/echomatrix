#!/usr/bin/env python3
# echomatrix/echomatrix/tts_cli.py

import logging
import os
import sys
import yaml
from echomatrix.tts_generator import generate_speech, list_generated_audio, find_audio_by_text

# Set up logging
logger = logging.getLogger('tts_cli')

def generate_command(args):
    """Handle the generate command"""
    if args.file:
        # Read text from file
        try:
            with open(args.file, 'r') as f:
                text = f.read().strip()
        except Exception as e:
            logger.error(f"Error reading file {args.file}: {e}")
            return 1
    else:
        # Use text from command line
        text = args.text
    
    if not text:
        logger.error("No text provided for TTS generation")
        return 1
    
    # Generate speech
    speech_path = generate_speech(text, args.model)
    
    if speech_path:
        print(f"Generated audio: {speech_path}")
        
        # If playback requested
        if args.play:
            try:
                import subprocess
                subprocess.run(["play", speech_path])
            except Exception as e:
                logger.error(f"Error playing audio: {e}")
        
        return 0
    else:
        logger.error("Failed to generate speech")
        return 1

def list_command(args):
    """Handle the list command"""
    registry = list_generated_audio()
    
    if not registry:
        print("No generated audio files found")
        return 0
    
    print(f"Found {len(registry)} generated audio files:")
    print("-" * 80)
    
    for file_id, file_info in registry.items():
        # Apply text filter if specified
        if args.filter and args.filter.lower() not in file_info.get('text', '').lower():
            continue
            
        # Apply model filter if specified
        if args.model and args.model != file_info.get('model'):
            continue
        
        print(f"ID: {file_id}")
        print(f"Model: {file_info.get('model')}")
        print(f"Path: {file_info.get('path')}")
        print(f"Created: {file_info.get('timestamp')}")
        print(f"Text: {file_info.get('text')}")
        print("-" * 80)
    
    return 0

def play_command(args):
    """Handle the play command"""
    # If ID is provided, play that specific file
    registry = list_generated_audio()
    
    if args.id:
        if args.id not in registry:
            logger.error(f"Audio file with ID {args.id} not found")
            return 1
        
        file_path = registry[args.id].get('path')
        
    # Otherwise, find by text
    elif args.text:
        matches = find_audio_by_text(args.text, args.model)
        
        if not matches:
            logger.error(f"No audio files found matching text: {args.text}")
            return 1
        
        # Use the first match
        file_path = matches[0].get('path')
    else:
        logger.error("Either --id or --text must be provided")
        return 1
    
    # Play the audio
    try:
        import subprocess
        print(f"Playing: {file_path}")
        subprocess.run(["play", file_path])
        return 0
    except Exception as e:
        logger.error(f"Error playing audio: {e}")
        return 1

def tts_main(args):
    """
    Main handler for TTS commands
    This function is called from the main CLI
    """
    if args.tts_command == 'generate':
        return generate_command(args)
    elif args.tts_command == 'list':
        return list_command(args)
    elif args.tts_command == 'play':
        return play_command(args)
    else:
        logger.error("No TTS subcommand specified")
        return 1

# For standalone execution
if __name__ == "__main__":
    print("This module is intended to be called from the main CLI.")
    print("Please use 'echomatrix tts' instead.")
    sys.exit(1)