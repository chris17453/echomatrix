import os
import json
import logging
from .call import calls, Call
from .config import config
from .config import engine_instance
from datetime import datetime

logger = logging.getLogger(__name__)

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

def on_account_registered(event_type, **data):
    """Handler for account registered events"""
    account_id = data.get('account_id')
    status = data.get('status', '')
    logger.info(f"MAIN APP: Account {account_id} registered with status: {status}")

# Recording events
def on_recording_started(event_type, **data):
    """Handler for recording started events"""
    call_id = data.get('call_id')
    path = data.get('path', '')
    logger.info(f"MAIN APP: Recording started for call {call_id}: {path}")

    call = Call.get_or_create_call(calls, call_id)
    call.add_event(data)


def on_recording_paused(event_type, **data):
    """Handler for recording paused events"""
    call_id = data.get('call_id')
    logger.info(f"MAIN APP: Recording paused for call {call_id}")

    call = Call.get_or_create_call(calls, call_id)
    call.add_event(data)

def on_recording_resumed(event_type, **data):
    """Handler for recording resumed events"""
    call_id = data.get('call_id')
    logger.info(f"MAIN APP: Recording resumed for call {call_id}")

    call = Call.get_or_create_call(calls, call_id)
    call.add_event(data)

def on_recording_stopped(event_type, **data):
    """Handler for recording stopped events"""
    call_id = data.get('call_id')
    path = data.get('path', '')
    duration = data.get('duration', 0)
    logger.info(f"MAIN APP: Recording stopped for call {call_id}: {path}, duration: {duration:.2f}s")

    call = Call.get_or_create_call(calls, call_id)
    call.add_event(data)


# Call related events
def on_call_answered(event_type, **data):
    """Handler for call answered events"""
    call_id = data.get('call_id')
    logger.info(f"MAIN APP: Call answered: {call_id} {call_info.remoteUri}")
    call_info = data.get('call_iinfo')

     # Get or create call
    call = Call.get_or_create_call(calls, call_id)
    call.add_event(data)

    

def on_call_disconnected(event_type, **data):
    """Handler for call disconnected events"""
    call_id = data.get('call_id')
    duration = data.get('duration', 0)
    logger.info(f"MAIN APP: Call disconnected: {call_id}, duration: {duration:.2f}s")

    # Get the call object
    call = Call.get_by_id(calls, call_id)
    if not call:
        logger.warning(f"Call not found for ID: {call_id}")
        return
    
    # Complete the call data
    call.end_call()
    call.add_event(data)
    
    # Create directory for call logs if it doesn't exist
    call_log_dir = "/var/log/echomatrix/calls"
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{call_log_dir}/call_{call_id}_{timestamp}.yaml"
    
    call.save(filename)
    

# Silence detection events
def on_silence_detected(event_type, **data):
    """Handler for silence detected events"""
    call_id = data.get('call_id')
    duration = data.get('duration', 0)
    logger.info(f"MAIN APP: Silence detected on call {call_id} for {duration:.2f}s")

    call = Call.get_or_create_call(calls, call_id)
    call.add_event(data)

def on_silence_ended(event_type, **data):
    """Handler for silence ended events"""
    call_id = data.get('call_id')
    duration = data.get('duration', 0)
    logger.info(f"MAIN APP: Silence ended on call {call_id} after {duration:.2f}s")

    call = Call.get_or_create_call(calls, call_id)
    call.add_event(data)

# Speech segment events
def on_speech_detected(event_type, **data):
    """Handler for speech detected events"""
    call_id = data.get('call_id')
    start_ms = data.get('start_ms', 0)
    logger.info(f"MAIN APP: Speech detected on call {call_id} at {start_ms}ms")

    call = Call.get_or_create_call(calls, call_id)
    call.add_event(data)

def on_speech_segment_complete(event_type, **data):
    """Handler for speech segment complete events"""
    call_id = data.get('call_id')
    segment = data.get('segment', {})
    
    logger.info(f"MAIN APP: Speech segment completed on call {call_id}: {segment}")

    call = Call.get_or_create_call(calls, call_id)
    call.add_event(data)

    # Transcribe the segment
    engine=engine_instance.get("instance")
    audio_path = segment.get("audio_path")

    if audio_path:
        transcript = engine.audio_manager.transcribe_segment(audio_path, segment)
        if transcript:
            call.add_chat_message("user", transcript)
            logger.info(f"Transcript: {transcript} created for call {call_id}")
        else:
            logger.warning(f"Segment:  Transcript failed for call {call_id}")
    else:
        logger.warning(f"Segment: No audiopath for for call {call_id}")



# Audio playback events
def on_audio_playing(event_type, **data):
    """Handler for audio playing events"""
    call_id = data.get('call_id')
    file_path = data.get('file_path', '')
    duration = data.get('duration', 0)
    logger.info(f"MAIN APP: Audio playback started on call {call_id}: {file_path}, duration: {duration:.2f}s")

    call = Call.get_or_create_call(calls, call_id)
    call.add_event(data)

def on_audio_ended(event_type, **data):
    """Handler for audio ended events"""
    call_id = data.get('call_id')
    file_path = data.get('file_path', '')
    logger.info(f"MAIN APP: Audio playback ended on call {call_id}: {file_path}")

    call = Call.get_or_create_call(calls, call_id)
    call.add_event(data)

