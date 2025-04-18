import logging
import pjsua2 as pj
import time
import sys
import threading
from echomatrix.config import config

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Extend Account class to handle callbacks
class Account(pj.Account):
    def __init__(self):
        pj.Account.__init__(self)
        self.calls = []
    
        # Callback for incoming calls
    def onIncomingCall(self, prm):
        logger.info(f"Incoming call received with ID: {prm.callId}")
        call = Call(self, prm.callId)
        self.calls.append(call)
        
        # Get call info to log more details
        try:
            call_info = call.getInfo()
            logger.info(f"Call from: {call_info.remoteUri}")
        except Exception as e:
            logger.error(f"Error getting call info: {e}")
        
        # Auto-answer the call after ringing for a moment
        call_prm = pj.CallOpParam()
        call_prm.statusCode = 180  # Ringing
        call.answer(call_prm)
        
        # Wait briefly then answer
        time.sleep(1)
        call_prm.statusCode = 200  # OK
        call.answer(call_prm)
        logger.info("Call answered")

# Extend Call class to handle call state events
class Call(pj.Call):
    def __init__(self, acc, call_id=pj.PJSUA_INVALID_ID):
        pj.Call.__init__(self, acc, call_id)
        self.acc = acc
        
    def onCallState(self, prm):
        ci = self.getInfo()
        logger.info(f"Call state: {ci.stateText}")
        
        # If call is disconnected, clean up
        if ci.state == pj.PJSIP_INV_STATE_DISCONNECTED:
            logger.info("Call disconnected")
            if self in self.acc.calls:
                self.acc.calls.remove(self)
    
    def onCallMediaState(self, prm):
        # Connect audio when media is active
        logger.info("Call media state changed")
        ci = self.getInfo()
        
        # Loop through media
        for mi in ci.media:
            if mi.type == pj.PJMEDIA_TYPE_AUDIO and mi.status == pj.PJSUA_CALL_MEDIA_ACTIVE:
                # Get the call media
                call_med = self.getMedia(mi.index)
                # Convert to audio media
                aud_med = pj.AudioMedia.typecastFromMedia(call_med)
                
                # Connect audio device to call audio
                ep = pj.Endpoint.instance()
                ep.audDevManager().getCaptureDevMedia().startTransmit(aud_med)
                aud_med.startTransmit(ep.audDevManager().getPlaybackDevMedia())
                
                logger.info("Media connected")


class SipAgent:
    def __init__(self, username, password, domain, port=5060):
        # Create endpoint
        self.ep = pj.Endpoint()
        self.username = username
        self.password = password
        self.domain = domain
        self.port = port
        self.account = None
        self.is_running = False
        
        # Initialize logging
        ep_cfg = pj.EpConfig()
        ep_cfg.logConfig.level = 4  # Set to 5 for more verbose logging
        
        # Configure media
        ep_cfg.medConfig.portRange = 1000  # Lower bound of UDP port range
        ep_cfg.medConfig.maxPortRange = 60000  # Upper bound of UDP port range
        
        # Create endpoint
        self.ep.libCreate()
        self.ep.libInit(ep_cfg)
        
        # Create UDP transport for SIP signaling on standard port 5060
        transport_cfg = pj.TransportConfig()
        transport_cfg.port = port
        self.transport = self.ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, transport_cfg)
        
        # Start the endpoint
        self.ep.libStart()
        logger.info("SIP endpoint started")
        
        # Create instance variable for endpoint
        pj.Endpoint.instance()
        
    def register_account(self):
        # Create an account configuration
        acc_cfg = pj.AccountConfig()
        acc_cfg.idUri = f"sip:{self.username}@{self.domain}"
        acc_cfg.regConfig.registrarUri = f"sip:{self.domain}"
        
        # Add authentication credentials
        cred = pj.AuthCredInfo("digest", "*", self.username, 0, self.password)
        acc_cfg.sipConfig.authCreds.append(cred)
        
        # Create the account
        self.account = Account()
        self.account.create(acc_cfg)
        logger.info(f"SIP account created: {acc_cfg.idUri}")
    
    def start(self):
        self.is_running = True
        logger.info("SIP agent started and ready to receive calls")
        
        try:
            # Main loop to keep the application running
            while self.is_running:
                self.ep.libHandleEvents(100)  # Handle events with 100ms timeout
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt detected")
        finally:
            self.stop()
            
    def stop(self):
        # Cleanup
        self.is_running = False
        if self.account:
            self.account.delete()
        if self.ep:
            self.ep.libDestroy()
        logger.info("SIP agent stopped")


if __name__ == "__main__":
        
    logger.info(f"Starting EchoMatrix")
    # Replace with your Twilio SIP credentials and your server's IP address
    USERNAME = config.sip.username
    PASSWORD = config.sip.password
    PORT = config.sip.local_port
    DOMAIN = config.sip.domain
    
    try:
        # Create and start SIP agent
        agent = SipAgent(USERNAME, PASSWORD, DOMAIN, PORT)
        agent.register_account()
        agent.start()
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

