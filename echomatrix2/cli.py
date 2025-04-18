#!/usr/bin/env python3
# echomatrix/echomatrix/cli.py

import argparse
import sys
import logging

# Import CLI modules
from echomatrix.tts_cli import tts_main

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('echomatrix_cli')

def main():
    """
    Main CLI entrypoint for EchoMatrix
    """
    parser = argparse.ArgumentParser(
        description="EchoMatrix Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Create subparsers for different command types
    subparsers = parser.add_subparsers(dest='command', help="Command category")
    
    # TTS commands
    tts_parser = subparsers.add_parser('tts', help="Text-to-Speech functionality")
    tts_subparsers = tts_parser.add_subparsers(dest='tts_command', help="TTS command")
    
    # TTS Generate command
    generate_parser = tts_subparsers.add_parser('generate', help="Generate TTS audio")
    generate_parser.add_argument('--text', '-t', help="Text to convert to speech")
    generate_parser.add_argument('--file', '-f', help="File containing text to convert")
    generate_parser.add_argument('--model', '-m', default=None, help="TTS model/voice to use")
    generate_parser.add_argument('--play', '-p', action='store_true', help="Play audio after generation")
    
    # TTS List command
    list_parser = tts_subparsers.add_parser('list', help="List generated audio files")
    list_parser.add_argument('--filter', '-f', help="Filter by text content")
    list_parser.add_argument('--model', '-m', help="Filter by model/voice")
    
    # TTS Play command
    play_parser = tts_subparsers.add_parser('play', help="Play generated audio")
    play_parser.add_argument('--id', '-i', help="ID of audio file to play")
    play_parser.add_argument('--text', '-t', help="Text of audio file to play")
    play_parser.add_argument('--model', '-m', help="Filter by model/voice")
    
    # Other command categories can be added here, for example:
    # recordings_parser = subparsers.add_parser('recordings', help="Manage recordings")
    # ... add subcommands for recordings ...
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle command categories
    if args.command == 'tts':
        return tts_main(args)
    # elif args.command == 'recordings':
    #     return recordings_main(args)
    # Add other command categories as needed
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())