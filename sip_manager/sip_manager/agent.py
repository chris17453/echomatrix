import os
import time
import logging
import pjsua2 as pj
import queue
from .events import emit_event, EventType
from .account import Account
from .recorder import audio_recorders
from .endpoint import CustomEndpoint

logger = logging.getLogger(__name__)

class SipAgent:
    def __init__(self, config=None):
        self.account = None
        self.running = False
        self.config = config
        self.audio_command_queue = queue.Queue()
            
        # Create endpoint
        self.ep = CustomEndpoint(self.config.silence_check_interval)

        # Initialize logging
        ep_cfg = pj.EpConfig()
        ep_cfg.logConfig.level = self.config.log_level

        # Media configuration
        ep_cfg.medConfig.noVad = self.config.no_vad
        ep_cfg.medConfig.clockRate = self.config.clock_rate
        ep_cfg.medConfig.sndClockRate = self.config.snd_clock_rate
        ep_cfg.medConfig.quality = self.config.quality
        ep_cfg.medConfig.ptime = self.config.ptime
        ep_cfg.medConfig.channelCount = self.config.channel_count
        ep_cfg.medConfig.txDropPct = self.config.tx_drop_pct
        ep_cfg.medConfig.ecTailLen = self.config.ec_tail_len
        ep_cfg.medConfig.ec_options = self.config.ec_options
        ep_cfg.medConfig.ecEnabled = self.config.echo_cancelation
        

        # Threading
        ep_cfg.uaConfig.mainThreadOnly = self.config.main_thread_only
        ep_cfg.uaConfig.threadCnt = self.config.thread_count

        # NAT and STUN
        stun_servers = pj.StringVector( [ self.config.stun_server ] )
        ep_cfg.uaConfig.stunServer = stun_servers
        ep_cfg.uaConfig.natKeepAliveInterval = self.config.nat_keep_alive_interval
        ep_cfg.uaConfig.natTypeInSdp = self.config.nat_type_in_sdp

        # Enable media features
        ep_cfg.medConfig.enableIce = True
        ep_cfg.medConfig.enableRtcp = True
        ep_cfg.medConfig.enableSrtp = pj.PJMEDIA_SRTP_OPTIONAL


        # Init endpoint
        self.ep.libCreate()
        self.ep.libInit(ep_cfg)
        
        
        # Transport configuration
        transport_cfg = pj.TransportConfig()
        transport_cfg.port = self.config.public_port
        transport_cfg.publicAddress = self.config.public_ip
        transport_cfg.boundAddress = self.config.bound_address

        logger.info(f"Using public IP: {self.config.public_ip}")

        self.transport = self.ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, transport_cfg)

        self.ep.libStart()
        self.ep.audDevManager().setNullDev()

        # Set codec priorities
        self.ep.codecSetPriority(self.config.pcmu_codec, self.config.pcmu_priority)
        self.ep.codecSetPriority(self.config.pcma_codec, self.config.pcma_priority)

        logger.info("SIP endpoint started with NULL audio device")

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

        emit_event(EventType.ACCOUNT_REGISTERED, account_uri=acc_cfg.idUri,registrar=acc_cfg.regConfig.registrarUri)

        logger.info(f"SIP account created: {acc_cfg.idUri}")

    def start(self):
        self.running = True
        logger.info("SIP agent started and ready to receive calls")
        
        try:
            # Main loop to keep the application running
            self.ep.utilTimerSchedule(self.config.welcome_message_length, None)

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
    
    def play_wav_to_call(self, wav_file_path,call_id=None):
        """
        Play a WAV file to the current active call
        
        Args:
            wav_file_path: Path to the WAV file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.account and self.account.calls:
            return self.account.play_wav_to_call(wav_file_path,call_id)
            
        else:
            logger.warning("No active account or calls to play audio to")
            return False
                    
    def process_audio_queue(self):
        """Process any pending audio playback commands"""
        try:
            # Only try to get a command if the queue isn't empty
            if not self.audio_command_queue.empty():
                cmd = self.audio_command_queue.get_nowait()
                if cmd.get('type') == 'play_wav':
                    file_path = cmd.get('file_path')
                    call_id = cmd.get('call_id')
                    logger.info(f"Processing audio command to play {file_path} on call {call_id}")
                    if self.account and file_path and call_id:
                        success = self.account.play_wav_to_call(file_path, call_id)
                        logger.info(f"Audio command processed successfully: {success}")
                        # Mark the task as done
                        self.audio_command_queue.task_done()
                        return success
                # Mark the task as done even if we couldn't process it
                self.audio_command_queue.task_done()
        except queue.Empty:
            # Queue was empty - this is normal, not an error
            pass
        except Exception as e:
            logger.error(f"Error processing audio queue: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return False