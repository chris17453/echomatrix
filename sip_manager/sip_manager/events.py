import os
import logging
import threading
import time

logger = logging.getLogger(__name__)

class EventType:
    CALL_ANSWERED = "call_answered"
    CALL_DISCONNECTED = "call_disconnected"
    SILENCE_DETECTED = "silence_detected"
    SILENCE_ENDED = "silence_ended"
    SPEECH_DETECTED = "speech_detected"
    SPEECH_SEGMENT_COMPLETE = "speech_segment_complete"
    AUDIO_PLAYING = "audio_playing"
    AUDIO_ENDED = "audio_ended"
    RECORDING_STARTED = "recording_started"
    RECORDING_PAUSED = "recording_paused"
    RECORDING_RESUMED = "recording_resumed"
    RECORDING_STOPPED = "recording_stopped"
    AGENT_STARTED = "agent_started"
    AGENT_STOPPING = "agent_stopping"
    AGENT_STOPPED = "agent_stopped"
    ACCOUNT_REGISTERED = "account_registered"

    
class SipEventManager:
    """
    Central event manager for SIP events across the system.
    Uses observer pattern to notify listeners of events.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SipEventManager, cls).__new__(cls)
                cls._instance.listeners = {}
                cls._instance.initialize()
            return cls._instance

    def initialize(self):
        """Initialize the event manager"""
        for event_type in dir(EventType):
            if not event_type.startswith('_'):
                self.listeners[getattr(EventType, event_type)] = []
        logger.info("SIP Event Manager initialized")

    def add_listener(self, event_type, callback):
        """
        Add a listener for a specific event type
        
        Args:
            event_type: Type of event to listen for
            callback: Function to call when event occurs
        """
        if event_type in self.listeners:
            self.listeners[event_type].append(callback)
            logger.debug(f"Added listener for {event_type}")
        else:
            logger.warning(f"Unknown event type: {event_type}")

    def remove_listener(self, event_type, callback):
        """
        Remove a listener for a specific event type
        
        Args:
            event_type: Type of event to remove listener from
            callback: Function to remove
        """
        if event_type in self.listeners and callback in self.listeners[event_type]:
            self.listeners[event_type].remove(callback)
            logger.debug(f"Removed listener for {event_type}")

    def emit_event(self, event_type, **kwargs):
        """
        Emit an event to all registered listeners
        
        Args:
            event_type: Type of event to emit
            **kwargs: Data to pass to listeners
        """
        logger.info(f"EVENT EMITTED: {event_type} with {len(event_manager.listeners.get(event_type, []))} listeners")

        if event_type in self.listeners:
            # Create timestamp if not provided
            if 'timestamp' not in kwargs:
                kwargs['timestamp'] = time.time()
                
            event_data = kwargs
            
            for callback in self.listeners[event_type]:
                try:
                    callback(event_type, **event_data)
                except Exception as e:
                    logger.error(f"Error in event listener for {event_type}: {e}")
            
            logger.debug(f"Emitted {event_type} event with data: {event_data}")
        else:
            logger.warning(f"Attempted to emit unknown event type: {event_type}")

# Create singleton instance
event_manager = SipEventManager()

def register_listener(event_type, callback):
    """
    Register a listener for a specific event type
    
    Args:
        event_type: Type of event to listen for
        callback: Function to call when event occurs
    """
    event_manager.add_listener(event_type, callback)

def unregister_listener(event_type, callback):
    """
    Unregister a listener for a specific event type
    
    Args:
        event_type: Type of event to remove listener from
        callback: Function to remove
    """
    event_manager.remove_listener(event_type, callback)

def emit_event(event_type, **kwargs):
    """
    Emit an event to all registered listeners
    
    Args:
        event_type: Type of event to emit
        **kwargs: Data to pass to listeners
    """
    event_manager.emit_event(event_type, **kwargs)