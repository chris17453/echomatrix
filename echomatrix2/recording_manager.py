#!/usr/bin/env python3
# echomatrix/echomatrix/recording_manager.py

import os
import sys
import datetime
import glob
import argparse
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('recording_manager')

def list_recordings(directory="/var/lib/asterisk/recordings", days=None):
    """
    List all recordings in the specified directory
    
    Args:
        directory: Directory containing recordings
        days: Only show recordings from the last X days
    """
    if not os.path.exists(directory):
        logger.error(f"Directory does not exist: {directory}")
        return []
    
    recordings = []
    wav_files = glob.glob(os.path.join(directory, "*.wav"))
    
    cutoff_time = None
    if days:
        cutoff_time = datetime.datetime.now() - datetime.timedelta(days=days)
    
    for wav_file in sorted(wav_files, key=os.path.getmtime, reverse=True):
        try:
            file_time = datetime.datetime.fromtimestamp(os.path.getmtime(wav_file))
            
            # Skip files older than cutoff
            if cutoff_time and file_time < cutoff_time:
                continue
                
            file_size = os.path.getsize(wav_file)
            basename = os.path.basename(wav_file)
            
            # Get metadata if available
            metadata = {}
            meta_file = f"{wav_file}.txt"
            if os.path.exists(meta_file):
                with open(meta_file, 'r') as f:
                    for line in f:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip()
            
            recording = {
                'filename': basename,
                'path': wav_file,
                'size': file_size,
                'timestamp': file_time.strftime("%Y-%m-%d %H:%M:%S"),
                'metadata': metadata
            }
            
            recordings.append(recording)
            
        except Exception as e:
            logger.error(f"Error processing file {wav_file}: {e}")
    
    return recordings

def cleanup_old_recordings(directory="/var/lib/asterisk/recordings", days=30):
    """
    Delete recordings older than the specified number of days
    
    Args:
        directory: Directory containing recordings
        days: Delete recordings older than this many days
    """
    if not os.path.exists(directory):
        logger.error(f"Directory does not exist: {directory}")
        return
    
    cutoff_time = datetime.datetime.now() - datetime.timedelta(days=days)
    
    wav_files = glob.glob(os.path.join(directory, "*.wav"))
    
    for wav_file in wav_files:
        try:
            file_time = datetime.datetime.fromtimestamp(os.path.getmtime(wav_file))
            
            if file_time < cutoff_time:
                logger.info(f"Deleting old recording: {wav_file}")
                os.remove(wav_file)
                
                # Also delete metadata file if it exists
                meta_file = f"{wav_file}.txt"
                if os.path.exists(meta_file):
                    os.remove(meta_file)
                    logger.info(f"Deleted metadata file: {meta_file}")
        except Exception as e:
            logger.error(f"Error deleting file {wav_file}: {e}")
    
    logger.info(f"Cleanup complete. Deleted recordings older than {days} days.")

def print_recording_info(recordings):
    """
    Print formatted information about recordings
    """
    if not recordings:
        print("No recordings found.")
        return
    
    print(f"Found {len(recordings)} recordings:")
    print("-" * 80)
    
    for i, rec in enumerate(recordings, 1):
        print(f"{i}. {rec['filename']} ({rec['size']} bytes)")
        print(f"   Recorded: {rec['timestamp']}")
        
        if rec['metadata']:
            print("   Metadata:")
            for key, value in rec['metadata'].items():
                print(f"     {key}: {value}")
        
        print("-" * 80)

def main():
    parser = argparse.ArgumentParser(description="Manage Asterisk recordings")
    parser.add_argument('--dir', default="/var/lib/asterisk/recordings",
                       help="Directory containing recordings")
    
    subparsers = parser.add_subparsers(dest='command', help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser('list', help="List recordings")
    list_parser.add_argument('--days', type=int, help="Only show recordings from last X days")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help="Delete old recordings")
    cleanup_parser.add_argument('--days', type=int, default=30,
                              help="Delete recordings older than X days")
    
    args = parser.parse_args()
    
    if args.command == 'list':
        recordings = list_recordings(args.dir, args.days)
        print_recording_info(recordings)
    elif args.command == 'cleanup':
        cleanup_old_recordings(args.dir, args.days)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()