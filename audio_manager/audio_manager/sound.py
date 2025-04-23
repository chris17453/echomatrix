import os
import logging
import numpy as np

import numpy as np


logger = logging.getLogger(__name__)

def analyze_pcm_audio_level(file_path, sample_rate=8000, sample_width=2, sample_duration=1.0):
    try:
        if not os.path.exists(file_path):
            logger.warning(f"PCM file does not exist: {file_path}")
            return 0

        if sample_width not in (1, 2, 4):
            logger.warning(f"Unsupported sample width: {sample_width}")
            return 0

        dtype_map = {1: np.uint8, 2: np.int16, 4: np.int32}
        dtype = dtype_map[sample_width]

        bytes_per_sample = sample_width
        frame_count = int(sample_rate * sample_duration)
        byte_count = frame_count * bytes_per_sample

        file_size = os.path.getsize(file_path)
        if file_size < byte_count:
            logger.info(f"File too small ({file_size} bytes), adjusting window to fit")
            byte_count = file_size

        if byte_count == 0:
            logger.info("File is empty")
            return 0

        with open(file_path, 'rb') as f:
            f.seek(-byte_count, os.SEEK_END)
            raw = f.read(byte_count)

        data = np.frombuffer(raw, dtype=dtype)

        if sample_width == 1:
            data = data - 128  # convert unsigned to signed center

        if len(data) == 0:
            return 0

        rms = np.sqrt(np.mean(data.astype(np.float32) ** 2))
        return rms

    except Exception as e:
        logger.error(f"Error analyzing PCM: {e}")
        return 0


def extract_audio_segment(file_path, speech_segment, sample_rate=8000, sample_width=2):
    """
    Extract an audio segment from a PCM file based on segment metadata.
    
    Args:
        file_path: Path to the PCM audio file
        speech_segment: Dictionary containing segment metadata with keys:
            - pcm_start_byte: Starting byte position in the file
            - pcm_end_byte: Ending byte position in the file
        sample_rate: Sample rate of the audio (default: 8000 Hz)
        sample_width: Sample width in bytes (default: 2 bytes/sample)
        
    Returns:
        audio_data: Binary data of the extracted segment
        segment_info: Dictionary with metadata about the extracted segment
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"PCM file does not exist: {file_path}")
            return None, None
            
        # Calculate exact byte positions
        start_byte = speech_segment.get('pcm_start_byte', 0)
        end_byte = speech_segment.get('pcm_end_byte', 0)
        
        if start_byte >= end_byte:
            logger.error(f"Invalid byte positions: start {start_byte} >= end {end_byte}")
            return None, None
            
        # Calculate duration in milliseconds and seconds
        duration_ms = speech_segment.get('duration_ms', end_byte - start_byte)
        duration_sec = duration_ms / 1000.0
        
        # Open file and extract the requested segment
        with open(file_path, 'rb') as f:
            file_size = os.path.getsize(file_path)
            
            # Validate byte positions against file size
            if end_byte > file_size:
                logger.warning(f"End byte {end_byte} exceeds file size {file_size}, adjusting")
                end_byte = file_size
                
            if start_byte >= file_size:
                logger.error(f"Start byte {start_byte} exceeds file size {file_size}")
                return None, None
                
            # Seek to the start position and read the segment
            f.seek(start_byte)
            segment_bytes = f.read(end_byte - start_byte)
            
        # Create segment info for reference
        segment_info = {
            'start_ms': speech_segment.get('start_ms', 0),
            'end_ms': speech_segment.get('end_ms', 0),
            'duration_ms': duration_ms,
            'duration_sec': duration_sec,
            'sample_rate': sample_rate,
            'sample_width': sample_width,
            'bytes_read': len(segment_bytes)
        }
        
        logger.debug(f"Extracted audio segment: {segment_info}")
        return segment_bytes, segment_info
            
    except Exception as e:
        logger.error(f"Error extracting audio segment: {e}")
        return None, None

