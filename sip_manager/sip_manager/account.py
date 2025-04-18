import os
import logging
import pjsua2 as pj
import time
from .call import Call
from .player import AudioPlayer

logger = logging.getLogger(__name__)

# Extend Account class to handle callbacks
class Account(pj.Account):
    def __init__(self,config):
        pj.Account.__init__(self)
        self.calls = []
        self.config=config
        
    def onIncomingCall(self, prm):
        logger.info(f"Incoming call received with ID: {prm.callId}")
        call = Call(self, prm.callId,self.config)
        self.calls.append(call)
        
        try:
            call_info = call.getInfo()
            logger.info(f"Call from: {call_info.remoteUri}")
            
            # Answer directly - don't wait
            call_prm = pj.CallOpParam(True)
            call_prm.opt.audioCount = 1
            call_prm.opt.videoCount = 0
            call_prm.opt.flag |= pj.PJSUA_CALL_INCLUDE_DISABLED_MEDIA
            call_prm.statusCode = 200  # OK
            call.answer(call_prm)
            logger.info("Call answered with 200 OK")
        except Exception as e:
            logger.error(f"Error in onIncomingCall: {e}")
        
    def play_wav_to_call(self, wav_file_path, call=None):
        """
        Play a WAV file to a specific call or the first active call
        
        Args:
            wav_file_path: Path to the WAV file
            call: Specific call object to play to (optional)
            
        Returns:
            bool: Success or failure
        """
        return AudioPlayer.play_wav_to_call(self, wav_file_path, call)          