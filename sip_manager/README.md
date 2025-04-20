# SIP Event System

This module adds a complete event system to your SIP manager, allowing you to track and respond to various call events including:

- Call answering and disconnection
- Silence detection
- Speech segment detection
- Audio playback status
- Recording status changes

## Overview

The event system uses the Observer pattern to allow different parts of your code to subscribe to events without tight coupling. The central `SipEventManager` handles event registration and dispatching.

## Event Types

The following event types are available:

- `CALL_ANSWERED`: Triggered when a call is connected
- `CALL_DISCONNECTED`: Triggered when a call ends
- `SILENCE_DETECTED`: Triggered when silence is detected for the configured duration
- `SILENCE_ENDED`: Triggered when silence ends and speech resumes
- `NEW_SEGMENT`: Triggered when a new speech segment is detected after silence
- `AUDIO_PLAYING`: Triggered when audio playback starts
- `AUDIO_ENDED`: Triggered when audio playback completes
- `RECORDING_STARTED`: Triggered when call recording begins
- `RECORDING_PAUSED`: Triggered when recording is paused
- `RECORDING_RESUMED`: Triggered when recording is resumed
- `RECORDING_STOPPED`: Triggered when recording ends

## Event Data

Each event includes relevant data such as:

- `call_id`: The unique ID of the call
- `remote_uri`: The SIP URI of the remote party (caller ID)
- `output_path`: Path to the recording file (for recording events)
- `duration`: Duration in seconds (for silence events)
- `audio_file`: Path to the audio file (for playback events)
- `segment`: Speech segment details (for NEW_SEGMENT events)

## Usage

### Registering Event Listeners

```python
from sip_manager.sip_events import EventType, register_listener

# Define your event handler
def on_call_answered(event_type, **event_data):
    print(f"Call answered: {event_data['call_id']} from {event_data['remote_uri']}")

# Register the handler
register_listener(EventType.CALL_ANSWERED, on_call_answered)
```

### Handling Multiple Events with One Function

```python
def on_recording_events(event_type, **event_data):
    action = event_type.split("_")[1]  # started, paused, resumed, stopped
    print(f"Recording {action} for call {event_data['call_id']} to {event_data['output_path']}")

# Register for multiple events
register_listener(EventType.RECORDING_STARTED, on_recording_events)
register_listener(EventType.RECORDING_PAUSED, on_recording_events)
register_listener(EventType.RECORDING_RESUMED, on_recording_events)
register_listener(EventType.RECORDING_STOPPED, on_recording_events)
```

### Unregistering Listeners

```python
from sip_manager.sip_events import unregister_listener

unregister_listener(EventType.CALL_ANSWERED, on_call_answered)
```

### Manually Emitting Events (if needed)

```python
from sip_manager.sip_events import emit_event, EventType

emit_event(EventType.NEW_SEGMENT, 
           call_id="12345",
           remote_uri="sip:user@example.com",
           output_path="/path/to/recording.wav",
           segment={
               'start_ms': 1000,
               'end_ms': 3000,
               'duration_ms': 2000
           })
```

## Configuration

The event system uses several configuration parameters from your existing configuration:

- `silence_threshold`: RMS level below which audio is considered silence
- `silence_duration`: Duration in milliseconds before silence is reported
- `silence_check_interval`: How often to check for silence (ms)







import sip_manager

# Create the agent
agent = sip_manager.create_agent(config_path='config.yaml')

# Register an event handler
def on_call_answered(event_type, **data):
    call_id = data.get('call_id')
    print(f"Call answered: {call_id}")

agent.register_event(sip_manager.EventType.CALL_ANSWERED, on_call_answered)

# Start the agent non-blocking
agent.start_nonblocking()

# Do other work
print("Agent is running in the background")
time.sleep(10)

# Check if still running
if agent.is_running():
    print("Agent is still running")

# Stop the agent when done
agent.stop()



Make sure these are set in your configuration.