import logging
import time
import pjsua2 as pj

logger = logging.getLogger(__name__)

from .recorder import audio_recorders

class CustomEndpoint(pj.Endpoint):
    def __init__(self):
        super().__init__()

    def onTimer(self, prm):
        self.utilTimerSchedule(100, None) 

        from .recorder import audio_recorders, AudioRecorder
        for call_id in list(audio_recorders.keys()):
            is_silent, duration = AudioRecorder.check_for_silence(call_id)
            if is_silent:
                logger.info(f"[onTimer] Silence detected on call {call_id} for {duration:.2f}s")
                # Optional: trigger stop, alert, etc.
