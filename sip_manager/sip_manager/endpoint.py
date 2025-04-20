import logging
import time
import pjsua2 as pj
from .player import AudioPlayer
from .recorder import audio_recorders

logger = logging.getLogger(__name__)


class CustomEndpoint(pj.Endpoint):
    def __init__(self,silence_check_interval=100):
        super().__init__()
        self.silence_check_interval=silence_check_interval


    def onTimer(self, prm):
        self.utilTimerSchedule(self.silence_check_interval, None) 

        from .recorder import audio_recorders, AudioRecorder
        for call_id in list(audio_recorders.keys()):
            is_silent, duration = AudioRecorder.check_for_silence(call_id)
            if is_silent:
                logger.info(f"[onTimer] Silence detected on call {call_id} for {duration:.2f}s")
                # Optional: trigger stop, alert, etc.
        
        # Check for completed audio playback
        AudioPlayer.check_audio_players()