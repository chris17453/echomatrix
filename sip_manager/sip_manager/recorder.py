import os
import time
import wave
import logging
import pjsua2 as pj

logger = logging.getLogger(__name__)

# Global dict to track recorders
audio_recorders = {}


class AudioRecorder:
    @staticmethod
    def start_recording(call, output_path, silence_timeout=None):
        """Start recording audio from a call"""
        try:
            # Create directory if needed
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            call_info = call.getInfo()
            call_id = call_info.callIdString
            
            logger.info(f"Setting up recording for call {call_id}")
            
            # Create recorder
            recorder = pj.AudioMediaRecorder()
            try:
                recorder.createRecorder(output_path)
            except Exception as e:
                logger.error(f"Failed to create recorder: {e}")
                return None
            
            # Store monitoring info
            recorder.output_path = output_path
            recorder.last_size = 0
            recorder.last_check_time = time.time()
            
            # Find the audio media
            audio_media = None
            for media_index, media in enumerate(call_info.media):
                if media.type == pj.PJMEDIA_TYPE_AUDIO and media.status == pj.PJSUA_CALL_MEDIA_ACTIVE:
                    try:
                        # Use call object to get audio media
                        audio_media = call.getAudioMedia(media_index)
                        logger.info(f"Found audio media at index {media_index}")
                        break
                    except Exception as e:
                        logger.error(f"Error getting audio media at index {media_index}: {e}")
            
            # Connect audio to recorder
            if audio_media:
                try:
                    audio_media.startTransmit(recorder)
                    logger.info("Successfully connected audio to recorder")
                    
                    # Store for tracking
                    audio_recorders[call_id] = recorder
                except Exception as e:
                    logger.error(f"Error connecting audio: {e}")
                    return None
            else:
                logger.error("No active audio media found")
                return None

            return recorder
        except Exception as e:
            logger.error(f"Error setting up recording: {e}")
            return None

            
    @staticmethod
    def stop_recording(call, recorder=None):
        """
        Stop recording the call
        """
        try:
            call_id = call.getInfo().callIdString
            
            # Get recorder if not provided
            if not recorder and call_id in audio_recorders:
                recorder = audio_recorders[call_id]
            
            if not recorder:
                logger.warning("No recorder found to stop")
                return False
                
            logger.info(f"Stopping recording for call {call_id}")
            
            # Disconnect audio media from recorder
            for mi in call.getInfo().media:
                if mi.type == pj.PJMEDIA_TYPE_AUDIO and mi.status == pj.PJSUA_CALL_MEDIA_ACTIVE:
                    try:
                        call_med = call.getMedia(mi.index)
                        aud_med = pj.AudioMedia.typecastFromMedia(call_med)
                        aud_med.stopTransmit(recorder)
                    except Exception as e:
                        logger.warning(f"Error disconnecting media: {e}")
            
            # Try different ways to close the recorder
            try:
                if hasattr(recorder, 'close'):
                    recorder.close()
                elif hasattr(pj.AudioMediaRecorder, 'close'):
                    pj.AudioMediaRecorder.close(recorder)
            except Exception as e:
                logger.warning(f"Error closing recorder: {e}")
            
            # Remove from tracking dict
            if call_id in audio_recorders:
                del audio_recorders[call_id]
                
            logger.info(f"Successfully stopped recording call {call_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return False    