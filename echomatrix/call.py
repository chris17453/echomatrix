import os
import yaml
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


calls = []

class Call:
    def __init__(self, call_id: Optional[str] = None):
        """
        Initialize a new Call object to track a conversation
        
        Args:
            call_id: Optional ID for the call, generates UUID if not provided
        """
        self.id = call_id or str(uuid.uuid4())
        self.start_time = datetime.now()
        self.end_time = None
        self.duration_sec = 0
        self.processed = None
        self.chat = []  # List of text messages/transcripts
        self.unprocessed  =[]
        self.actions = []  # Actions taken during call
        self.input_audio = None  # Full input audio path or data
        self.outgoing_audio = []  # List of outgoing audio segments
        self.metadata = {}  # Additional call metadata
        self.events= []

    def add_speech_segment(self, segment: Dict[str, Any]) -> None:
        """Add a speech segment to unprocessed list"""
        self.unprocessed.append(segment)

    def add_event(self, event: Dict[str, Any]) -> None:
        """Add an event to the events list"""
        self.events.append(event)
        
    def add_chat_message(self, role: str, text: str,processed: bool = None) -> None:
        """Add a chat message to the conversation history"""
        
        if processed:
            processed_time=datetime.now()
        else :
            processed_time=None

        self.chat.append({
            "processed_time": None,
            "processed": processed_time,
            "role": role,
            "text": text,
            "timestamp": datetime.now()
        })
        if not processed:
            self.processed=None
        
    def add_action(self, action_type: str, details: Dict[str, Any]) -> None:
        """Record an action taken during the call"""
        self.actions.append({
            "type": action_type,
            "details": details,
            "timestamp": datetime.now()
        })
    
    def add_outgoing_audio(self, audio_data: bytes, metadata: Dict[str, Any]) -> None:
        """Add outgoing audio data with metadata"""
        self.outgoing_audio.append({
            "audio": audio_data,
            "metadata": metadata,
            "timestamp": datetime.now()
        })
    
    def end_call(self) -> None:
        """Mark the call as ended and calculate duration"""
        self.end_time = datetime.now()
        self.duration_sec = (self.end_time - self.start_time).total_seconds()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert call data to dictionary for serialization"""
        return {
            "id": self.id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_sec": self.duration_sec,
            "chat": self.chat,
            "actions": self.actions,
            "unprocessed_count": len(self.unprocessed),
            "outgoing_audio_count": len(self.outgoing_audio),
            "metadata": self.metadata
        }

    @staticmethod
    def get_by_id(calls_list: List["Call"], call_id: str) -> Optional["Call"]:
        """
        Find a call by its ID in a list of calls
        
        Args:
            calls_list: List of Call objects to search
            call_id: ID of the call to find
            
        Returns:
            Call object if found, None otherwise
        """
        for call in calls_list:
            if call.id == call_id:
                return call
        return None

    @classmethod
    def get_or_create_call(cls, calls_list: List["Call"], call_id: str) -> "Call":
        """
        Get a call by ID or create a new one if it doesn't exist
        
        Args:
            calls_list: List of Call objects
            call_id: ID of the call to find or create
            
        Returns:
            Existing or newly created Call object
        """
        # Try to find existing call
        call = cls.get_by_id(calls_list, call_id)
        
        # Create new call if not found
        if not call:
            logger.info(f"Creating new call with ID: {call_id}")
            call = cls(call_id=call_id)
            calls_list.append(call)
        
        return call

    def save(self, file_path: Optional[str] = None) -> str:
            """
            Save call data to a YAML file
            
            Args:
                file_path: Optional file path to save to. If not provided, 
                        uses call ID with yaml extension in current directory
            
            Returns:
                Path where file was saved
            """
            # Default filename based on call ID if not provided
            if not file_path:
                file_path = f"{self.id}.yaml"
            
            # Convert call data to dictionary
            data = self.to_dict()
            
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
                
                # Write YAML file
                with open(file_path, 'w') as yaml_file:
                    yaml.dump(data, yaml_file, default_flow_style=False, sort_keys=False)
                
                logger.info(f"Call data saved to {file_path}")
                return file_path
            except Exception as e:
                logger.error(f"Failed to save call data: {e}")
                raise

    def update_processed_state(self) -> bool:
        """
        Check if all chat messages are processed and update the Call's processed state
        
        Returns:
            bool: True if all messages are processed, False otherwise
        """
        # Only proceed if there are chat messages
        if not self.chat:
            return False
            
        # Check if all messages are processed
        all_processed = all(msg.get("processed") is not None for msg in self.chat)
        
        # Update the Call's processed state
        if all_processed:
            self.processed = True
        else:
            self.processed = None
            
        return all_processed