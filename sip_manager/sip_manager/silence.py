# Add these imports at the top of audio.py
import logging 
import threading
import numpy as np
import audioop
import struct
import time
from .recorder import audio_recorders

logger = logging.getLogger(__name__)

# Global dict to track silence detectors
silence_detectors = {}

class SilenceDetector:
    def __init__(self, call, recorder, silence_timeout=5.0, sample_interval=0.1, 
                 rms_threshold=500, callback=None):
        """
        Monitor audio levels and detect silence
        
        Args:
            call: The call to monitor
            recorder: The recorder object
            silence_timeout: How long silence must persist before triggering (seconds)
            sample_interval: How often to check audio levels (seconds)
            rms_threshold: RMS threshold below which is considered silence
            callback: Function to call when silence is detected
        """
        self.call = call
        self.recorder = recorder
        self.silence_timeout = silence_timeout
        self.sample_interval = sample_interval
        self.rms_threshold = rms_threshold
        self.callback = callback
        self.is_running = False
        self.silence_start_time = None
        self.thread = None
        
    def start(self):
        """Start silence detection in a background thread"""
        self.is_running = True
        self.thread = threading.Thread(target=self._monitor_silence)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Started silence detection (threshold: {self.silence_timeout}s)")
        
    def stop(self):
        """Stop silence detection"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        logger.info("Stopped silence detection")
        
    def _monitor_silence(self):
        """Background thread that monitors audio levels"""
        try:
            while self.is_running:
                # Get audio level from the recorder
                # This is a simplification - in a real implementation,
                # you'd need to access the recorder's buffer or use PJSUA callbacks
                # to get actual audio levels
                
                # For now, we'll use a placeholder check that will need to be 
                # replaced with actual audio level detection
                is_silent = self._check_for_silence()
                
                if is_silent:
                    # Start tracking silence if not already
                    if self.silence_start_time is None:
                        self.silence_start_time = time.time()
                        logger.debug("Silence started")
                    
                    # Check if silence duration exceeds threshold
                    silence_duration = time.time() - self.silence_start_time
                    if silence_duration >= self.silence_timeout:
                        logger.info(f"Silence detected for {silence_duration:.1f}s")
                        if self.callback:
                            self.callback(self.call, silence_duration)
                        # Stop after triggering callback
                        self.is_running = False
                        break
                else:
                    # Reset silence tracking if audio detected
                    if self.silence_start_time is not None:
                        logger.debug("Silence ended")
                        self.silence_start_time = None
                
                # Sleep before next check
                time.sleep(self.sample_interval)
                
        except Exception as e:
            logger.error(f"Error in silence detection: {e}")
            self.is_running = False
    
    def _check_for_silence(self):
        """
        Check if current audio is silence by using file size changes
        """
        try:
            # Get call ID
            call_id = self.call.getInfo().callIdString
            
            # Check if recorder exists and is active
            if call_id in audio_recorders:
                # For PJSUA2, we can't easily get audio levels directly
                # Instead, check if the recorder's output file is growing
                output_path = getattr(self.recorder, 'output_path', None)
                if output_path and os.path.exists(output_path):
                    current_size = os.path.getsize(output_path)
                    
                    # Store previous size if not set
                    if not hasattr(self, 'previous_size'):
                        self.previous_size = current_size
                        return False
                    
                    # If file size hasn't changed, we might have silence
                    size_change = current_size - self.previous_size
                    self.previous_size = current_size
                    
                    logger.debug(f"File size change: {size_change} bytes")
                    return size_change < 1000  # Threshold for "silence" (small file size change)
            
            # Default to non-silence if we can't determine
            return False
            
        except Exception as e:
            logger.error(f"Error checking audio levels: {e}")
            return False
            """
            Check if current audio is silence by measuring RMS level
            """
            try:
                # Get audio level from PJSUA recorder via a callback
                # This requires adding a port to capture audio levels
                if hasattr(self.recorder, 'port') and self.recorder.port:
                    # Get audio frame from port
                    frame = self.recorder.port.get_frame()
                    if frame and len(frame) > 0:
                        # Calculate RMS
                        rms = audioop.rms(frame, 2)  # Assuming 16-bit audio
                        logger.debug(f"Audio RMS level: {rms}")
                        return rms < self.rms_threshold
                
                # If we can't get direct audio levels, return false
                # to avoid false silence detection
                return False
                
            except Exception as e:
                logger.error(f"Error checking audio levels: {e}")
                return False