import os
import logging
import time
import sys
from .config import default_config, engine_instance
from .log import set_logging
from .event_handlers import *
from .call import calls

# Simplified path handling
parent_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)),"config_manager"))
sys.path.append(parent_dir)
parent_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)),"sip_manager"))
sys.path.append(parent_dir)
parent_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)),"audio_manager"))
sys.path.append(parent_dir)
parent_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)),"ai_manager"))
sys.path.append(parent_dir)

from  config_manager  import Config
from  audio_manager import AudioManager
from  ai_manager import AIManager
import sip_manager

logger = logging.getLogger(__name__)


class engine:

    def __init__(self,config_path):
        try:
            global config,audio_manager
            # Load configuration
            self.config= Config(config_path=config_path, default_config=default_config, env_prefix='AUDIO_MANAGER_')
            self.audio_manager=AudioManager(self.config.audio_manager)
            self.ai_manager=AIManager(self.config.ai_manager)
            
            set_logging(self.config.echomatrix.log_level)
            
            # Create the agent
            agent = sip_manager.create_agent(self.config.sip_manager, agent_id="emit_event")
            
            self.agent=agent
            engine_instance["instance"] = self
            
            # Register event handlers for all event types
            # Call events
            agent.register_event(sip_manager.EventType.CALL_ANSWERED, on_call_answered)
            agent.register_event(sip_manager.EventType.CALL_DISCONNECTED, on_call_disconnected)
            
            # Silence events
            #agent.register_event(sip_manager.EventType.SILENCE_DETECTED, on_silence_detected)
            #agent.register_event(sip_manager.EventType.SILENCE_ENDED, on_silence_ended)
            
            # Speech events
            agent.register_event(sip_manager.EventType.SPEECH_DETECTED, on_speech_detected)
            agent.register_event(sip_manager.EventType.SPEECH_SEGMENT_COMPLETE, on_speech_segment_complete)
            
            # Audio playback events
            agent.register_event(sip_manager.EventType.AUDIO_PLAYING, on_audio_playing)
            agent.register_event(sip_manager.EventType.AUDIO_ENDED, on_audio_ended)
            
            # Recording events
            agent.register_event(sip_manager.EventType.RECORDING_STARTED, on_recording_started)
            agent.register_event(sip_manager.EventType.RECORDING_PAUSED, on_recording_paused)
            agent.register_event(sip_manager.EventType.RECORDING_RESUMED, on_recording_resumed)
            agent.register_event(sip_manager.EventType.RECORDING_STOPPED, on_recording_stopped)
            
            # Agent lifecycle events
            # agent.register_event(sip_manager.EventType.AGENT_STARTED, on_agent_started)
            # agent.register_event(sip_manager.EventType.AGENT_STOPPING, on_agent_stopping)
            # agent.register_event(sip_manager.EventType.AGENT_STOPPED, on_agent_stopped)
            
            # Account events
            agent.register_event(sip_manager.EventType.ACCOUNT_REGISTERED, on_account_registered)
            
            
            # Start the agent
            logger.info("Starting SIP agent...")
            success = agent.start_nonblocking()
            
            if not success:
                logger.error("Failed to start agent")
                sys.exit(1)
            
            start_time = time.time()
            try:
                while 1:
                    self.process_calls()
                    time.sleep(.01)
                    
                        
            except KeyboardInterrupt:
                logger.info("Interrupted by user")
            
            # Stop the agent
            agent.stop()
            
        except Exception as e:
            logger.error(f"Error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            sys.exit(1)

    def process_calls(self):
        """
        Process all active calls and handle any new unprocessed transcriptions
        This should be called periodically from your main loop
        """
        
        for call in calls:
            # Check if there are unprocessed transcriptions to handle
            if not call.processed:
                try:
                    old_transcript = []
                    new_transcript= []
                    for msg in call.chat:
                       # if msg['processed']:
                       #     old_transcript .append( f"{msg['role']} : {msg['text']} ")
                       # else:
                       if not msg['processed']:
                            new_transcript .append( f"{msg['role']} : {msg['text']} ")
                       msg['processed']=True
                    # ok now we have what we WERE talkinmg about
                    # and what we ARe talking about...
                    messages=old_transcript+new_transcript
                    result=self.ai_manager.chat("generic",{'text':"\n".join(messages)})
                    logger.info(f"processing result: {result}")

                    call.add_chat_message(role="system",text=result,processed=True)
                    path=self.ai_manager.generate_speech(result)
                    logger.info(f"Engine:_PLAY_WAV {path},{call.id}")
                    self.agent.play_wav_to_call(path,call.id)

                    call.update_processed_state()    
                except Exception as e:
                    logger.error(f"Error processing call segment: {e}")
