import os
import logging
import time
import sys
from .config import default_config
from .log import set_logging

# Simplified path handling
parent_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)),"config_manager"))
sys.path.append(parent_dir)
parent_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)),"sip_manager"))
sys.path.append(parent_dir)
parent_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)),"audio_manager"))
sys.path.append(parent_dir)

from config_manager import Config
import sip_manager

# Create log directory if it doesn't exist
log_dir = "/var/log/echomatrix"
os.makedirs(log_dir, exist_ok=True)

# Set up logging to file
log_file = os.path.join(log_dir, "full.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("Logging initialized")

# Call related events
def on_call_answered(event_type, **data):
    """Handler for call answered events"""
    call_id = data.get('call_id')
    logger.info(f"MAIN APP: Call answered: {call_id}")

def on_call_disconnected(event_type, **data):
    """Handler for call disconnected events"""
    call_id = data.get('call_id')
    duration = data.get('duration', 0)
    logger.info(f"MAIN APP: Call disconnected: {call_id}, duration: {duration:.2f}s")

# Silence detection events
def on_silence_detected(event_type, **data):
    """Handler for silence detected events"""
    call_id = data.get('call_id')
    duration = data.get('duration', 0)
    logger.info(f"MAIN APP: Silence detected on call {call_id} for {duration:.2f}s")

def on_silence_ended(event_type, **data):
    """Handler for silence ended events"""
    call_id = data.get('call_id')
    duration = data.get('duration', 0)
    logger.info(f"MAIN APP: Silence ended on call {call_id} after {duration:.2f}s")

# Speech segment events
def on_speech_detected(event_type, **data):
    """Handler for speech detected events"""
    call_id = data.get('call_id')
    start_ms = data.get('start_ms', 0)
    logger.info(f"MAIN APP: Speech detected on call {call_id} at {start_ms}ms")

def on_speech_segment_complete(event_type, **data):
    """Handler for speech segment complete events"""
    call_id = data.get('call_id')
    segment = data.get('segment', {})
    logger.info(f"MAIN APP: Speech segment completed on call {call_id}: {segment}")

# Audio playback events
def on_audio_playing(event_type, **data):
    """Handler for audio playing events"""
    call_id = data.get('call_id')
    file_path = data.get('file_path', '')
    duration = data.get('duration', 0)
    logger.info(f"MAIN APP: Audio playback started on call {call_id}: {file_path}, duration: {duration:.2f}s")

def on_audio_ended(event_type, **data):
    """Handler for audio ended events"""
    call_id = data.get('call_id')
    file_path = data.get('file_path', '')
    logger.info(f"MAIN APP: Audio playback ended on call {call_id}: {file_path}")

# Recording events
def on_recording_started(event_type, **data):
    """Handler for recording started events"""
    call_id = data.get('call_id')
    path = data.get('path', '')
    logger.info(f"MAIN APP: Recording started for call {call_id}: {path}")

def on_recording_paused(event_type, **data):
    """Handler for recording paused events"""
    call_id = data.get('call_id')
    logger.info(f"MAIN APP: Recording paused for call {call_id}")

def on_recording_resumed(event_type, **data):
    """Handler for recording resumed events"""
    call_id = data.get('call_id')
    logger.info(f"MAIN APP: Recording resumed for call {call_id}")

def on_recording_stopped(event_type, **data):
    """Handler for recording stopped events"""
    call_id = data.get('call_id')
    path = data.get('path', '')
    duration = data.get('duration', 0)
    logger.info(f"MAIN APP: Recording stopped for call {call_id}: {path}, duration: {duration:.2f}s")

# Agent events
def on_agent_started(event_type, **data):
    """Handler for agent started events"""
    agent_id = data.get('agent_id')
    logger.info(f"MAIN APP: Agent {agent_id} started successfully")

def on_agent_stopping(event_type, **data):
    """Handler for agent stopping events"""
    agent_id = data.get('agent_id')
    logger.info(f"MAIN APP: Agent {agent_id} is stopping")

def on_agent_stopped(event_type, **data):
    """Handler for agent stopped events"""
    agent_id = data.get('agent_id')
    logger.info(f"MAIN APP: Agent {agent_id} stopped")

# Account events
def on_account_registered(event_type, **data):
    """Handler for account registered events"""
    account_id = data.get('account_id')
    status = data.get('status', '')
    logger.info(f"MAIN APP: Account {account_id} registered with status: {status}")

# New segment events
def on_new_segment(event_type, **data):
    """Handler for new segment events"""
    call_id = data.get('call_id')
    segment_id = data.get('segment_id')
    logger.info(f"MAIN APP: New segment {segment_id} created for call {call_id}")

# Audio test events
def on_audio_test_completed(event_type, **data):
    """Handler for audio test completed events"""
    agent_id = data.g0et('agent_id')
    success = data.get('success', False)
    logger.info(f"MAIN APP: Audio test completed for agent {agent_id}, success: {success}")

if __name__ == "__main__":
    logger.info("Starting EchoMatrix")
    config_path = "config.yaml"
    
    try:
        # Load configuration
        config = Config(config_path=config_path, default_config=default_config, env_prefix='AUDIO_MANAGER_')
        
        set_logging(config.echomatrix.log_level)
        # Create the agent
        agent = sip_manager.create_agent(config.sip_manager, agent_id="emit_event")
        
        # Register event handlers for all event types
        # Call events
        agent.register_event(sip_manager.EventType.CALL_ANSWERED, on_call_answered)
        agent.register_event(sip_manager.EventType.CALL_DISCONNECTED, on_call_disconnected)
        
        # Silence events
        agent.register_event(sip_manager.EventType.SILENCE_DETECTED, on_silence_detected)
        agent.register_event(sip_manager.EventType.SILENCE_ENDED, on_silence_ended)
        
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
        agent.register_event(sip_manager.EventType.AGENT_STARTED, on_agent_started)
        agent.register_event(sip_manager.EventType.AGENT_STOPPING, on_agent_stopping)
        agent.register_event(sip_manager.EventType.AGENT_STOPPED, on_agent_stopped)
        
        # Account events
        agent.register_event(sip_manager.EventType.ACCOUNT_REGISTERED, on_account_registered)
        
        # Other events
        agent.register_event(sip_manager.EventType.NEW_SEGMENT, on_new_segment)
        
        # Start the agent
        logger.info("Starting SIP agent...")
        success = agent.start_nonblocking()
        
        if not success:
            logger.error("Failed to start agent")
            sys.exit(1)
        
        logger.info("Agent started. Running for 60 seconds...")
        
        # Keep the program running for a while
        runtime = 60  # seconds
        start_time = time.time()
        try:
            while time.time() - start_time < runtime:
                # Do other work here while the agent runs
                time.sleep(1)
                
                # Print status every 10 seconds
                elapsed = time.time() - start_time
                if elapsed % 10 < 1:
                    logger.info(f"Agent running for {int(elapsed)}s")
                    
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        
        # Stop the agent
        agent.stop()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)