import os
import time
import logging
import pjsua2 as pj
from .account import Account
from .recorder import audio_recorders
from .endpoint import CustomEndpoint


logger = logging.getLogger(__name__)

class SipAgent:
    def __init__(self, config=None):
        # Create endpoint
        self.ep = CustomEndpoint()
        self.account = None
        self.is_running = False
        self.config = config
        
        # Initialize logging
        ep_cfg = pj.EpConfig()
        ep_cfg.logConfig.level = self.config.log_level  # More verbose logging
        
        # Configure media with NAT settings
        ep_cfg.medConfig.noVad = self.config.noVad

        ep_cfg.medConfig.ecTailLen = self.config.ecTailLen

        ep_cfg.medConfig.clockRate = self.config.clockRate
        ep_cfg.medConfig.sndClockRate = self.config.sndClockRate

        ep_cfg.medConfig.quality = self.config.quality
        ep_cfg.medConfig.ptime = self.config.ptime
        ep_cfg.medConfig.channelCount = self.config.channelCount
        ep_cfg.medConfig.ec_options = self.config.ec_options
        ep_cfg.medConfig.txDropPct = self.config.txDropPct
        
        # Create a StringVector for STUN servers
        stun_servers = pj.StringVector(["stun.l.google.com:19302"])
        ep_cfg.uaConfig.stunServer = stun_servers
        
        # Set NAT keep-alive interval (in seconds)
        ep_cfg.uaConfig.natKeepAliveInterval = 30

        # Configure media config for NAT handling
        ep_cfg.medConfig.enableIce = True  # Enable ICE
        ep_cfg.medConfig.enableRtcp = True  # Enable RTCP
        ep_cfg.medConfig.enableSrtp = pj.PJMEDIA_SRTP_OPTIONAL  # Optional SRTP


        # Enable ICE for NAT traversal
#        ep_cfg.uaConfig.natTypeInSdp = self.config.natTypInSdp
        ep_cfg.uaConfig.natTypeInSdp = 4

        # Create endpoint
        self.ep.libCreate()
        self.ep.libInit(ep_cfg)
        
        
        # Create transport with public IP
        transport_cfg = pj.TransportConfig()
        transport_cfg.port = self.config.public_port
        
        transport_cfg.publicAddress = self.config.public_ip
        transport_cfg.boundAddress = "0.0.0.0"  # Bind to all interfaces

        logger.info(f"Using public IP: {self.config.public_ip}")
        
        self.transport = self.ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, transport_cfg)
        
        # Start the endpoint
        self.ep.libStart()
        
        # Set NULL device
        self.ep.audDevManager().setNullDev()
        
        # Set codec priorities
        self.ep.codecSetPriority("PCMU/8000", 255)
        self.ep.codecSetPriority("PCMA/8000", 254)
        
        logger.info("SIP endpoint started with NULL audio device")

        # Instance variable
        pj.Endpoint.instance()
            
    def register_account(self):
        # Create an account configuration
        acc_cfg = pj.AccountConfig()
        acc_cfg.idUri = f"sip:{self.config.username}@{self.config.domain}"
        
        # Account NAT settings
        acc_cfg.natConfig.iceEnabled = True

        # Use the outbound proxy from config
        if hasattr(self.config, 'outbound_proxy'):
            proxy = f"sip:{self.config.outbound_proxy}"
            acc_cfg.sipConfig.proxies.append(proxy)
            logger.info(f"Using outbound proxy: {proxy}")
        
        # Set registrar from config or use domain
        if hasattr(self.config, 'contact'):
            contact = self.config.contact
            if contact.startswith('sip:'):
                parts = contact.split('@')
                if len(parts) > 1:
                    registrar = f"sip:{parts[1].split(':')[0]}"
                    acc_cfg.regConfig.registrarUri = registrar
                    logger.info(f"Using registrar: {registrar}")
        else:
            acc_cfg.regConfig.registrarUri = f"sip:{self.config.domain}"
        
        # For a headless server that only receives calls, you can disable registration
        acc_cfg.regConfig.registerOnAdd = self.config.register
    
        # Add authentication credentials
        cred = pj.AuthCredInfo("digest", "*", self.config.username, 0, self.config.password)
        acc_cfg.sipConfig.authCreds.append(cred)
        
        # Create the account
        self.account = Account(self.config)
        self.account.create(acc_cfg)
        logger.info(f"SIP account created: {acc_cfg.idUri}")

    def start(self):
        self.is_running = True
        logger.info("SIP agent started and ready to receive calls")
        
        try:
            # Main loop to keep the application running
            self.ep.utilTimerSchedule(500, None)

            while self.is_running:
                # Handle events with 100ms timeout
                self.ep.libHandleEvents(100)

                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt detected")
        finally:
            self.stop()

    def stop(self):
        # Cleanup
        self.is_running = False
        try:
            if self.account:
                # Try different methods that might exist
                try:
                    self.account.shutdown()
                except AttributeError:
                    try:
                        self.account.destroy()
                    except AttributeError:
                        # Just log the issue
                        logger.warning("Could not properly shut down account")
                        
            if self.ep:
                self.ep.libDestroy()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            
        logger.info("SIP agent stopped")
    
    def play_wav_to_call(self, wav_file_path):
        """
        Play a WAV file to the current active call
        
        Args:
            wav_file_path: Path to the WAV file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.account and self.account.calls:
            return self.account.play_wav_to_call(wav_file_path)
        else:
            logger.warning("No active account or calls to play audio to")
            return False
                    

    def test_audio_routing(self):
        """Test if audio is properly routed in the endpoint"""
        try:
            # Log audio devices
            logger.info("Testing audio routing")
            
            # Get audio device manager
            adm = self.ep.audDevManager()
            
            # Check sound devices
            dev_info = adm.getDevInfo()
            logger.info(f"Sound devices: input={dev_info.inputCount}, output={dev_info.outputCount}")
            
            # Test if null device is active
            try:
                cap_dev = adm.getCaptureDevMedia()
                play_dev = adm.getPlaybackDevMedia()
                logger.info("Successfully got capture and playback devices")
            except Exception as e:
                logger.error(f"Failed to get media devices: {e}")
                
            # Check codecs
            codecs = []
            try:
                for i in range(128):  # arbitrary limit
                    try:
                        codec_info = self.ep.codecEnum(i)
                        codecs.append(codec_info.codecId)
                    except:
                        break
                logger.info(f"Available codecs: {', '.join(codecs)}")
            except Exception as e:
                logger.error(f"Error enumerating codecs: {e}")
                
            return True
        except Exception as e:
            logger.error(f"Error testing audio: {e}")
            return False                