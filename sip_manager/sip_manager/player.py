import os
import time
import wave
import logging
import pjsua2 as pj
from .events import emit_event, EventType

logger = logging.getLogger(__name__)

# Global dict to track players
audio_players = {}


class AudioPlayer:
    @staticmethod
    def play_wav_to_call(account, wav_file_path, call=None):
        """
        Play a WAV file through a specific SIP call or the first active call.
        
        Args:
            account: The SIP account with active calls
            wav_file_path: Path to the WAV file to play
            call: Specific call to play audio to (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(wav_file_path):
                logger.error(f"WAV file not found: {wav_file_path}")
                return False
            # Use provided call or check for active calls
            if call:
                selected_call = call
            elif account.calls:
                selected_call = account.calls[0]
            else:
                logger.warning("No active calls to play audio to")
                return False
                
            # Get call info
            call_id = selected_call.getInfo().callIdString
            
            # Get call info to confirm we're connected
            call_info = selected_call.getInfo()
            
            if call_info.state != pj.PJSIP_INV_STATE_CONFIRMED:
                logger.warning("Call is not in confirmed state")
                return False
                
            # Clean up any existing player for this call
            if call_id in audio_players:
                try:
                    logger.info(f"Stopping previous audio player for call {call_id}")
                    player = audio_players[call_id]
                    player.stop()
                    # Emit audio ended event
                    emit_event(EventType.AUDIO_ENDED, call_id=call_id)
                    del audio_players[call_id]
                except Exception as e:
                    logger.warning(f"Error cleaning up previous player: {e}")
            
            # Create player
            player = pj.AudioMediaPlayer()
            
            # Get file duration using wave module
            with wave.open(wav_file_path, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / float(rate)
                logger.info(f"WAV duration: {duration} seconds")
            
            # Initialize player with the WAV file
            player.createPlayer(wav_file_path, pj.PJMEDIA_FILE_NO_LOOP)
            
            # Store in global dict to prevent garbage collection
            audio_players[call_id] = player
            # Add file path and duration to player for reference
            player.file_path = wav_file_path
            player.duration = duration
            
            # Get the call media
            for mi in call_info.media:
                logger.info(f"Media {mi.index}: type={mi.type}, status={mi.status}")
                if mi.type == pj.PJMEDIA_TYPE_AUDIO and mi.status == pj.PJSUA_CALL_MEDIA_ACTIVE:
                    # Get the audio media from the call
                    call_med = selected_call.getMedia(mi.index)
                    aud_med = pj.AudioMedia.typecastFromMedia(call_med)
                    
                    # Connect the player to the call audio
                    player.startTransmit(aud_med)
                    
                    logger.info(f"Started playing {wav_file_path} to call {call_id}")
                    
                    # Emit audio playing event
                    emit_event(EventType.AUDIO_PLAYING, 
                              call_id=call_id,
                              file_path=wav_file_path,
                              duration=duration)
                    
                    # Schedule a timer to emit audio ended event when playback completes
                    # Since we don't have direct callbacks from PJSUA for playback completion,
                    # we can check the status in the endpoint timer
                    
                    return True
                    
            logger.warning("No active audio media found in call")
            return False
            
        except Exception as e:
            logger.error(f"Error playing WAV file: {e}")
            return False
            
    @staticmethod
    def check_audio_players():
        """
        Check if any audio players have finished playback.
        This should be called periodically from the SIP agent's timer.
        """
        try:
            current_time = time.time()
            for call_id in list(audio_players.keys()):
                try:
                    player = audio_players[call_id]
                    # Check if the player has finished
                    if hasattr(player, 'start_time') and hasattr(player, 'duration'):
                        elapsed = current_time - player.start_time
                        if elapsed >= player.duration:
                            # Playback finished
                            logger.info(f"Audio playback finished for call {call_id}")
                            # Emit audio ended event
                            emit_event(EventType.AUDIO_ENDED, 
                                      call_id=call_id,
                                      file_path=player.file_path,
                                      duration=player.duration)
                            # Cleanup
                            player.stop()
                            del audio_players[call_id]
                except Exception as e:
                    logger.error(f"Error checking audio player for call {call_id}: {e}")
        except Exception as e:
            logger.error(f"Error in check_audio_players: {e}")