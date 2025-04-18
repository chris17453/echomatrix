import os
import time
import threading
import logging
import pjsua2 as pj

from .player import audio_players  
from .recorder import AudioRecorder, audio_recorders
from .silence import SilenceDetector, silence_detectors


logger = logging.getLogger(__name__)

# Extend Call class to handle call state events
class Call(pj.Call):
    def __init__(self, acc, call_id=pj.PJSUA_INVALID_ID,config=None):
        pj.Call.__init__(self, acc, call_id)
        self.config=config
        self.acc = acc
        
    def onCallState(self, prm):
        ci = self.getInfo()
        logger.info(f"Call state: {ci.stateText}")
        
        if ci.state == pj.PJSIP_INV_STATE_CONFIRMED:
            # This state is triggered when the call is established
            # Get the WAV file from config
            wav_file =self.config.wav
            self.on_pickup(wav_file)
            self.start_recording()

        
        # If call is disconnected, clean up
        elif ci.state == pj.PJSIP_INV_STATE_DISCONNECTED:
            logger.info("Call disconnected")
            # Clean up any audio players for this call
            call_id = ci.callIdString
            if call_id in audio_players:
                try:
                    del audio_players[call_id]
                    logger.info(f"Cleaned up audio player for call {call_id}")
                except Exception as e:
                    logger.warning(f"Error cleaning up audio player: {e}")
                        
            if self in self.acc.calls:
                self.acc.calls.remove(self)


    def onCallMediaState(self, prm):
        # Connect audio when media is active
        logger.info("Call media state changed")
        ci = self.getInfo()

        



    def on_pickup(self, wav_file=None):
        """
        Triggered when a call is picked up/answered.
        """
        logger.info("Call picked up - preparing welcome audio")
        
        # Apply welcome delay if configured
        delay = self.config.welcome_delay
        if delay and delay > 0:
            logger.info(f"Waiting {delay}s delay before playing greeting")
            time.sleep(delay)
        
        # Play greeting - this will block until complete
        logger.info("Playing greeting to call")
        result = self.acc.play_wav_to_call(wav_file, self)
        
        


    # In the Call class, add these methods
    def start_recording(self, output_path=None, silence_timeout=None):
        """
        Start recording the call
        
        Args:
            output_path: Path to save the recording (None for auto-generated)
            silence_timeout: Duration of silence (seconds) before stopping (None for continuous)
                
        Returns:
            bool: Success or failure
        """
        try:
            # Generate output path if not provided
            if not output_path:
                call_id = self.getInfo().callIdString
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                output_dir = self.config.recording_dir if hasattr(self.config, 'recording_dir') else "recordings"
                
                # Create directory if it doesn't exist
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    
                output_path = os.path.join(output_dir, f"{timestamp}_{call_id}.wav")
                
            # Use silence_timeout from config if not specified
            if silence_timeout is None and hasattr(self.config, 'silence'):
                silence_timeout = self.config.silence
                
            # Default to 5 seconds if not specified anywhere
            if silence_timeout is None:
                silence_timeout = 5.0
                
            logger.info(f"Starting recording with silence timeout: {silence_timeout}s")
                
            # Start recording
            recorder = AudioRecorder.start_recording(self, output_path)
            
            if not recorder:
                logger.error("Failed to start recording")
                return False
                
            # Save recorder reference
            call_id = self.getInfo().callIdString
            audio_recorders[call_id] = recorder
            
            # Start silence detection if timeout specified
            #if silence_timeout and silence_timeout > 0:
            #//    self.start_silence_detection(recorder, silence_timeout)
                
            return True
            
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            return False
            
    def stop_recording(self):
        """
        Stop recording the call
        
        Returns:
            bool: Success or failure
        """
        try:
            call_id = self.getInfo().callIdString
            
            # Stop silence detection if active
            if call_id in silence_detectors:
                silence_detector = silence_detectors[call_id]
                silence_detector.stop()
                del silence_detectors[call_id]
                
            # Stop recording if active
            if call_id in audio_recorders:
                recorder = audio_recorders[call_id]
                success = AudioRecorder.stop_recording(self, recorder)
                del audio_recorders[call_id]
                return success
            else:
                logger.warning("No active recording to stop")
                return False
                
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return False
            
    def start_silence_detection(self, recorder, silence_timeout):
        """
        Start detecting silence on the call
        
        Args:
            recorder: The recorder to monitor
            silence_timeout: Duration of silence (seconds) before triggering
                
        Returns:
            bool: Success or failure
        """
        try:
            call_id = self.getInfo().callIdString
            
            # Stop existing silence detector if any
            if call_id in silence_detectors:
                silence_detectors[call_id].stop()
                
            # Create and start a new silence detector
            detector = SilenceDetector(
                self, 
                recorder, 
                silence_timeout=silence_timeout,
                callback=self.on_silence_detected
            )
            detector.start()
            
            # Save reference
            silence_detectors[call_id] = detector
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting silence detection: {e}")
            return False
            
    def on_silence_detected(self, call, duration):
        """
        Callback when silence is detected
        
        Args:
            call: The call where silence was detected
            duration: Duration of silence detected
        """
        logger.info(f"Silence detected for {duration:.1f}s")
        
        # Stop recording
        self.stop_recording()
        
        # Run custom handler if configured
        if hasattr(self.config, 'on_silence_handler'):
            try:
                handler = self.config.on_silence_handler
                if callable(handler):
                    handler(self, duration)
            except Exception as e:
                logger.error(f"Error in silence handler: {e}")        