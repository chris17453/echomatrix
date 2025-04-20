import os
import time
import logging
import pjsua2 as pj

from .player import audio_players  
from .recorder import AudioRecorder, audio_recorders

logger = logging.getLogger(__name__)

# Extend Call class to handle call state events
class Call(pj.Call):
    def __init__(self, acc, call_id=pj.PJSUA_INVALID_ID, config=None):
        pj.Call.__init__(self, acc, call_id)
        self.config = config
        self.acc = acc
        self.current_recording_path = None
        self.silence_detection_active = False
        
    def onCallState(self, prm):
        ci = self.getInfo()
        call_id = ci.callIdString
        logger.info(f"Call state: {ci.stateText}")
        
        if ci.state == pj.PJSIP_INV_STATE_CONFIRMED:
            # This state is triggered when the call is established
            
            # Get the WAV file from config
            wav_file = self.config.welcome_message
            self.on_pickup(wav_file)
            
            # Start recording immediately
            self.start_recording(call_id)
        
        # If call is disconnected, clean up
        elif ci.state == pj.PJSIP_INV_STATE_DISCONNECTED:
            logger.info("Call disconnected")
            # Clean up devices
            if call_id in audio_players:
                try:
                    if call_id in audio_players:
                        del audio_players[call_id]
                        logger.info(f"Cleaned up audio player for call {call_id}")
                except Exception as e:
                    logger.warning(f"Error cleaning up audio player: {e}")
                try:
                    if call_id in audio_recorders:
                        del audio_recorders[call_id]
                        logger.info(f"Cleaned up recorder for call {call_id}")
                except Exception as e:
                    logger.warning(f"Error cleaning up recorder: {e}")

            if self in self.acc.calls:
                self.acc.calls.remove(self)

    def onCallMediaState(self, prm):
        """Called when media state changes"""
        try:
            logger.info("Call media state changed")
            ci = self.getInfo()

            # Check if the call is active
            if ci.state != pj.PJSIP_INV_STATE_CONFIRMED:
                return
        except Exception as e:
            logger.warning(f"Error onMediaState: {e}")
        
    
    def on_pickup(self, wav_file=None):
        """
        Triggered when a call is picked up/answered.
        """
        logger.info("Call picked up - preparing welcome audio")
        
        # Apply welcome delay if configured
        delay = self.config.welcome_delay
        if delay and delay > 0:
            logger.info(f"Waiting {delay}s delay before playing greeting")
            time.sleep(delay/1000)
        
        # Play greeting - this will block until complete
        logger.info("Playing greeting to call")
        result = self.acc.play_wav_to_call(wav_file, self)
        
      #  time.sleep(self.config.welcome_message_length/1000)
        logger.info(f"Done with greeting ")
    
    def start_recording(self, call_id=None):
        """
        Start recording the call
        
        Args:
                
        Returns:
            bool: Success or failure
        """
        try:
            logger.info(f"In Recording")
            if not call_id:
                call_id = self.getInfo().callIdString

            # Generate output path
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            output_dir = self.config.recording_dir if hasattr(self.config, 'recording_dir') else "recordings"
            
            try:
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"Created directory: {output_dir}")
            except Exception as e:
                logger.error(f"Failed to create directory {output_dir}: {e}")
                return None

            # it needs to always be PCM
            if self.config.audio_format=='pcm':
                ext='pcm'
            else:
                ext='wav'

            output_path = os.path.join(output_dir, f"{timestamp}_{call_id}.{ext}")
            self.current_recording_path = output_path
                
            # Start recording
            recorder = AudioRecorder.start_recording(self, output_path, self.config)
            
            if not recorder:
                logger.error("Failed to start recording")
                return False
                
            # Save recorder reference
            audio_recorders[call_id] = recorder
            logger.info(f"Started recording to {output_path}")
                
            return True
            
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            return False
            
    def stop_recording(self):
        """
        Stop recording the call and return the path to the recording
        
        Returns:
            str: Path to the recording file or None if failed
        """
        try:
            call_id = self.getInfo().callIdString
            recording_path = None
            
            # Get the recording path before stopping
            if call_id in audio_recorders:
                recorder = audio_recorders[call_id]
                if hasattr(recorder, 'output_path'):
                    recording_path = recorder.output_path
                
                # Stop recording
                success = AudioRecorder.stop_recording(self, recorder)
                del audio_recorders[call_id]
                
                if success:
                    logger.info(f"Stopped recording to {recording_path}")
                    return recording_path
                else:
                    logger.warning("Failed to stop recording properly")
                    return None
            else:
                logger.warning("No active recording to stop")
                return None
                
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return None
                    
    def process_audio(self, audio_path):
        """Process recorded audio file"""
        logger.info(f"Processing audio file: {audio_path}")
        # Add your transcription code here
        # For example:
        # transcription = self.transcribe_audio(audio_path)
        # logger.info(f"Transcription: {transcription}")
