import os
import sys
from pathlib import Path
import tempfile
import subprocess
import shutil
import logging
import uuid
import datetime  # Fixed: datetime is imported directly
from typing import Dict, Any, Optional, List

# Simplified path handling
parent_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)),"..", "config_manager"))
print(parent_dir)
sys.path.append(parent_dir)

from .config import default_config
from config_manager import Config
from .file_manager import FileManager
from .db import Database, AIIdentityRecord, UserIdentityRecord, FileRecord, RecordingRecord

logger = logging.getLogger(__name__)

class AudioManager:
    def __init__(self, config):
        # Access config via dot notation
        self.config = config

        self.db = Database(self.config.db_path)
        self.file_manager = FileManager()
        self.session_id = str(uuid.uuid4())

        self._ai_identity = None
        self._user_identity = None
        self.set_ai_identity(self.config.ai.id)
        self.set_user_identity(self.config.user.id)
    
    def set_ai_identity(self, ai_identity_id):
        """Set the session AI identity ID."""
        self.ai_identity_id = ai_identity_id
        self.get_current_ai_identity()
        logger.info(f"Set session AI identity to: {ai_identity_id}")
        
    def set_user_identity(self, user_identity_id):
        """Set the session user identity ID."""
        self.user_identity_id = user_identity_id
        self.get_current_user_identity()
        logger.info(f"Set session user identity to: {user_identity_id}")
        
    def get_current_ai_identity(self):
        """Get the current AI identity object for this session."""
        if not self.ai_identity_id:
            return None
            
        if not self._ai_identity:
            self._ai_identity = self.get_ai_identity(self.ai_identity_id)
            
        return self._ai_identity
        
    def get_current_user_identity(self):
        """Get the current user identity object for this session."""
        if not self.user_identity_id:
            return None
            
        if not self._user_identity:
            self._user_identity = self.get_user_identity(self.user_identity_id)
            
        return self._user_identity

    def generate_tts(self, text):
        """
        Generate text-to-speech audio using an AI identity's settings.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            str: Recording ID or None on failure
        """
        try:
            # Get the AI identity
            if not self.ai_identity_id:
                logger.error("AI identity ID NOT SET")
                return None

            # Fixed: using _ai_identity instead of ai_identity
            if not self._ai_identity:
                logger.error("AI identity RECORD NOT SET")
                return None
            
            logger.info(f"Using AI identity {self.ai_identity_id} with voice '{self._ai_identity.voice}' and model '{self._ai_identity.model}'")
            
            # Check if we already generated this text with this AI identity
            existing_recording = self.find_by_ai_text(text, self.ai_identity_id)
            if existing_recording:
                logger.info(f"Found existing TTS recording with ID: {existing_recording.id} for the same text and AI identity")
                return existing_recording.id

            loc = self.config.default_location

            if loc != 'local':  # Fixed: using string comparison
                # Get local storage path from config
                local_storage = self.config.locations.tmp
                destination_storage = self.config.locations[loc]  # Fixed variable name
            else:
                local_storage = self.config.locations.local
                destination_storage = self.config.locations.local  # Fixed variable name
                
            # Format similar to SQL Server timestamp: yyyymmdd_hhmmss
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{timestamp}_TTS.wav"


            recording = RecordingRecord(
                session_id=self.session_id,
                id=None,
                text=text,
                ai_generated=True,
                user_recorded=False,
                ai_identity_id=self.ai_identity_id,
                user_identity_id=None,
                location=loc,
                timestamp=timestamp
            )
            
            # Register the recording using the model's method
            recording_id = recording.register(self.db)
                    

            # Create full output path - fixed order of operations
            relative_path = self.file_manager.get_path_from_uuid(recording_id)
            output_dir = Path(os.path.join(local_storage.path, relative_path))
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / output_filename)
            db_path= str(os.path.join(relative_path , output_filename))
            # Generate the speech
            from .tts import generate_speech
            res = generate_speech(
                text=text, 
                voice=self._ai_identity.voice,  # Fixed: using _ai_identity
                model=self._ai_identity.model,  # Fixed: using _ai_identity
                output_path=output_path,
                config=self.config
            )
            
            if not res:
                logger.error("Failed to generate speech")
                return None
                
            # Update recording with file paths
            file_paths = {"wav": db_path}
        
            # Add files to the recording
            if file_paths:
                for file_type, file_path in file_paths.items():
                    recording.add_file(self.db, file_type, file_path)
                
            if loc != 'local':
                res = self.file_manager.push_file(output_path, local_storage, destination_storage)  
                if not res:
                    logger.error(f"Error pushing file to location: {destination_storage.name}")
                    raise Exception("Failed to push file to destination storage")
                os.unlink(output_path)  
            
            logger.info(f"Registered TTS recording with ID: {recording_id}")
            return recording_id
            
        except Exception as e:
            logger.error(f"Error generating TTS: {e}")
            return None

    def register_recording(self, 
                        session_id: Optional[str] = None,
                        rec_id: Optional[str] = None,
                        text: Optional[str] = None,
                        ai_generated: bool = False,
                        user_recorded: bool = False,
                        ai_identity_id: Optional[int] = None,
                        user_identity_id: Optional[int] = None,
                        location: str = "local",
                        timestamp: Optional[str] = None,
                        file_paths: Dict[str, str] = None
                        ) -> str:
        """
        Register a new recording with metadata and file paths.
        
        Args:
            session_id: Session identifier
            rec_id: Optional recording ID (UUID)
            text: Transcription text
            ai_generated: Whether the audio was generated by AI
            user_recorded: Whether the audio was recorded by a user
            ai_identity_id: ID of the AI identity used
            user_identity_id: ID of the user identity
            location: Storage location
            timestamp: Creation timestamp
            file_paths: Dictionary mapping file types to file paths
            
        Returns:
            str: The recording ID
        """
        # Create a recording record using the model class
        recording = RecordingRecord(
            session_id=session_id,
            id=rec_id,
            text=text,
            ai_generated=ai_generated,
            user_recorded=user_recorded,
            ai_identity_id=ai_identity_id,
            user_identity_id=user_identity_id,
            location=location,
            timestamp=timestamp
        )
        
        # Register the recording using the model's method
        recording_id = recording.register(self.db)
        
        # Add files to the recording
        if file_paths:
            for file_type, file_path in file_paths.items():
                print("ADDING FILE")
                recording.add_file(self.db, file_type, file_path)
            
        return recording_id
    
    def register_ai_identity(self, model: Optional[str] = None, voice: Optional[str] = None,
                            provider: Optional[str] = None, instruction: Optional[str] = None) -> int:
        """
        Register a new AI identity.
        
        Args:
            model: AI model identifier
            voice: AI voice identifier
            provider: AI provider name
            instruction: AI instruction or prompt
            
        Returns:
            int: The AI identity ID
        """
        ai_identity = AIIdentityRecord(
            model=model,
            voice=voice,
            provider=provider,
            instruction=instruction
        )
        return ai_identity.register(self.db)


    def transcribe(self, audio_data=None, audio_path=None, recording_id=None, register=False, user_recorded=True):
        """
        Transcribe audio using OpenAI's Whisper API.
        
        Args:
            audio_data: Raw audio data (bytes or numpy array)
            audio_path: Path to audio file
            recording_id: ID of existing recording to transcribe
            register: Whether to register the transcription in the database
            user_recorded: Whether this is a user recording (vs. external source)
            
        Returns:
            str or recording_id: Transcribed text, or recording ID if registered
        """
        try:
            from .transcriber import transcribe_audio
            audio_path=None        
          
            
            # If recording_id is provided, get  audio path
            if recording_id:
                recording = self.get_recording(recording_id)
                
                if not recording:
                    logger.error(f"Recording: {recording_id} not found..")
                    return None

                files=recording.get_files(self.db)
                if not files:
                    logger.error(f"No files for Recording: {recording_id}")
                    return None

                if files:
                    file=files[0]
                    local_storage = self.config.locations.local
                    audio_path = os.path.join(local_storage.path, file.path)
                    
                    # if the file is remote.. lets pull it down                
                    if recording.location!='local':
                        self.file_manager.pull_file(recording_id)



            transcription = transcribe_audio(
                audio_data=audio_data,
                audio_path=audio_path,
                config=self.config
            )

            # Transcribe the audio
            if not transcription:
                logger.error("Transcription failed")
                return None
            else:
                logger.info(f"Transcription completed: {transcription}")
                

            # Update existing recording
            if recording_id:
                self.update_recording(recording_id, {'text': transcription})
                logger.info(f"Updated recording {recording_id} with transcription")
                return recording_id
            
            return transcription
        except Exception as e:
            logger.error(f"Error in transcribe: {e}")
            return None


    def register_user_identity(self, 
                              first_name: Optional[str] = None, 
                              middle_name: Optional[str] = None, 
                              last_name: Optional[str] = None,
                              affiliation: Optional[str] = None, 
                              phone: Optional[str] = None, 
                              user_name: Optional[str] = None) -> int:
        """
        Register a new user identity.
        
        Args:
            first_name: User's first name
            middle_name: User's middle name
            last_name: User's last name
            affiliation: User's organizational affiliation
            phone: User's phone number
            user_name: User's username
            
        Returns:
            int: The user identity ID
        """
        user_identity = UserIdentityRecord(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            affiliation=affiliation,
            phone=phone,
            user_name=user_name
        )
        return user_identity.register(self.db)

    def get_ai_identity(self, ai_identity_id: int) -> Optional[AIIdentityRecord]:
        """
        Get an AI identity by its ID.
        
        Args:
            ai_identity_id: AI identity ID
            
        Returns:
            Optional[AIIdentityRecord]: The found AI identity or None
        """
        return AIIdentityRecord.get(self.db, ai_identity_id)

    def list_ai_identities(self) -> List[AIIdentityRecord]:
        """
        List all AI identities.
        
        Returns:
            List[AIIdentityRecord]: List of all AI identities
        """
        return AIIdentityRecord.get_all(self.db)
        
    def find_ai_identities_by_model(self, model: str) -> List[AIIdentityRecord]:
        """
        Find AI identities by model name.
        
        Args:
            model: The model name to search for
            
        Returns:
            List[AIIdentityRecord]: List of matching AI identities
        """
        return AIIdentityRecord.find_by_model(self.db, model)

    def update_ai_identity(self, ai_identity_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update an AI identity with new values.
        
        Args:
            ai_identity_id: AI identity ID
            updates: Dictionary of fields to update
            
        Returns:
            bool: Whether the update was successful
            
        Raises:
            ValueError: If AI identity not found
        """
        ai_identity = self.get_ai_identity(ai_identity_id)
        if not ai_identity:
            raise ValueError(f"AI identity {ai_identity_id} not found.")
            
        # Update AI identity fields
        for key, value in updates.items():
            if hasattr(ai_identity, key):
                setattr(ai_identity, key, value)
                
        return ai_identity.update(self.db)

    def delete_ai_identity(self, ai_identity_id: int) -> bool:
        """
        Delete an AI identity.
        
        Args:
            ai_identity_id: AI identity ID
            
        Returns:
            bool: Whether the deletion was successful
            
        Raises:
            ValueError: If AI identity not found
        """
        ai_identity = self.get_ai_identity(ai_identity_id)
        if not ai_identity:
            raise ValueError(f"AI identity {ai_identity_id} not found.")
            
        return ai_identity.delete(self.db)

    def find_by_ai_text(self, text: str, ai_entity_id: int) -> Optional[RecordingRecord]:
        """
        Find a recording by its text content and AI entity ID.
        
        Args:
            text: The text to search for
            ai_entity_id: AI entity ID to filter by
            
        Returns:
            Optional[RecordingRecord]: The found recording or None
        """
        return RecordingRecord.find_by_ai_text(self.db, text, ai_entity_id)

    def get_recording(self, rec_id: str) -> Optional[RecordingRecord]:
        """
        Get a recording by its ID.
        
        Args:
            rec_id: Recording ID
            
        Returns:
            Optional[RecordingRecord]: The found recording or None
        """
        return RecordingRecord.get(self.db, rec_id)

    def list_all(self) -> List[RecordingRecord]:
        """
        List all recordings.
        
        Returns:
            List[RecordingRecord]: List of all recordings
        """
        return RecordingRecord.get_all(self.db)
        
    def find_recordings_by_model(self, model: str) -> List[RecordingRecord]:
        """
        Find recordings by model name.
        
        Args:
            model: The model name to search for
            
        Returns:
            List[RecordingRecord]: List of matching recordings
        """
        return RecordingRecord.find_by_model(self.db, model)

    def find_recordings_by_location(self, location: str) -> List[RecordingRecord]:
        """
        Find recordings by storage location.
        
        Args:
            location: The location to search for
            
        Returns:
            List[RecordingRecord]: List of matching recordings
        """
        return RecordingRecord.find_by_location(self.db, location)
    
    def find_recordings_by_type(self, ai_generated: bool = None, user_recorded: bool = None) -> List[RecordingRecord]:
        """
        Find recordings by type.
        
        Args:
            ai_generated: Filter by AI-generated flag
            user_recorded: Filter by user-recorded flag
            
        Returns:
            List[RecordingRecord]: List of matching recordings
        """
        return RecordingRecord.find_by_type(self.db, ai_generated, user_recorded)

    def update_recording_location(self, recording_id: str, new_location: str) -> bool:
        """
        Update the location of a recording.
        
        Args:
            recording_id: Recording ID
            new_location: New location
            
        Returns:
            bool: Whether the update was successful
        """
        return RecordingRecord.update_location(self.db, recording_id, new_location)

    def push_recording(self, recording_id: str) -> None:
        """
        Push a recording to a remote destination.
        
        Args:
            recording_id: Recording ID
            
        Raises:
            ValueError: If recording not found or destination unknown
        """
        recording = self.get_recording(recording_id)
        if not recording:
            raise ValueError(f"Recording {recording_id} not found.")

        destination_config = self.config.locations.get(recording.location)
        
        if not destination_config:
            raise ValueError(f"Unknown location: {recording.location}")

        # local location
        local_config = self.config.locations.local
        if not local_config:
            raise ValueError(f"Unknown local location")

        # Get all files associated with this recording
        files = recording.get_files(self.db)
        
        # Push each file
        for file_record in files:
            self.file_manager.push_file(file_record.path, local_config, destination_config)
            
    def pull_recording(self, recording_id: str) -> None:
        """
        Pull a recording from its stored remote location to local storage.
        
        Args:
            recording_id: Recording ID
            
        Raises:
            ValueError: If recording not found or source location unknown
        """
        recording = self.get_recording(recording_id)
        if not recording:
            raise ValueError(f"Recording {recording_id} not found.")

        # Use the location stored in the recording
        source_name = recording.location
        if source_name == "local":
            logger.info(f"Recording {recording_id} is already local, no need to pull")
            return

        source_config = self.config.locations.get(source_name)
        if not source_config:
            raise ValueError(f"Unknown source location: {source_name}")

        # local location
        local_config = self.config.locations.local
        if not local_config:
            raise ValueError(f"Unknown local location")

        # Get all files associated with this recording
        files = recording.get_files(self.db)
        
        for file_record in files:
            # Create a local path with proper local prefix
            filename = Path(file_record.path).name
            
            # Pull the file from remote location
            self.file_manager.pull_file(file_record.path, source_config, local_config)
        
        logger.info(f"Successfully pulled recording {recording_id} to local storage")

    def get_file_by_type(self, recording_id: str, file_type: str) -> Optional[str]:
        """
        Get a file path of a specific type for a recording.
        
        Args:
            recording_id: Recording ID
            file_type: File type
            
        Returns:
            Optional[str]: Path to the file or None
            
        Raises:
            ValueError: If recording not found or file type not found
        """
        recording = self.get_recording(recording_id)
        if not recording:
            raise ValueError(f"Recording {recording_id} not found.")
            
        # Find the requested file type
        for file_record in recording.get_files(self.db):
            if file_record.file_type == file_type:
                # Pull the file if not local
                if not Path(file_record.path).exists():
                    local_config = self.config.locations.local
                    source_config = self.config.locations.get(recording.location)
                    if not source_config:
                        raise ValueError(f"Unknown source location: {recording.location}")
                    self.file_manager.pull_file(file_record.path, source_config, local_config)
                    return file_record.path
                else:
                    return file_record.path
                    
        raise ValueError(f"No {file_type} file found for recording {recording_id}")
        
    def delete_recording(self, recording_id: str) -> bool:
        """
        Delete a recording and all its associated files.
        
        Args:
            recording_id: Recording ID
            
        Returns:
            bool: Whether the deletion was successful
            
        Raises:
            ValueError: If recording not found
        """
        recording = self.get_recording(recording_id)
        if not recording:
            raise ValueError(f"Recording {recording_id} not found.")
            
        return recording.delete(self.db)
        
    def update_recording(self, recording_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a recording with new values.
        
        Args:
            recording_id: Recording ID
            updates: Dictionary of fields to update
            
        Returns:
            bool: Whether the update was successful
            
        Raises:
            ValueError: If recording not found
        """
        recording = self.get_recording(recording_id)
        if not recording:
            raise ValueError(f"Recording {recording_id} not found.")
            
        # Update recording fields
        for key, value in updates.items():
            if hasattr(recording, key):
                setattr(recording, key, value)
                
        return recording.update(self.db)

    def transcribe_segment(self, file_path, speech_segment):
        """
        Extract an audio segment and transcribe it.
        
        Args:
            file_path: Path to the PCM audio file
            speech_segment: Dictionary containing segment metadata with keys:
                - pcm_start_byte: Starting byte position in the file
                - pcm_end_byte: Ending byte position in the file
                - duration_ms: Optional duration in milliseconds
                - start_ms: Optional start time in milliseconds
                - end_ms: Optional end time in milliseconds
                
        Returns:
            str or None: Transcribed text, or None on failure
        """
        try:
            from .transcriber import transcribe_segment
            
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"Audio file not found: {file_path}")
                return None
                
            # Transcribe the segment
            transcription = transcribe_segment(
                file_path=file_path,
                speech_segment=speech_segment,
                config=self.config
            )
            
            if not transcription:
                logger.error("Segment transcription failed")
                return None
                
            logger.info(f"Segment transcription completed: {transcription}")
            return transcription
            
        except Exception as e:
            logger.error(f"Error in transcribe_segment: {e}")
            return None        

    def analyze_pcm_audio_level(self, file_path, sample_rate=8000, sample_width=2, sample_duration=1.0):
        """
        Analyze the audio level of a PCM file.
        
        Args:
            file_path: Path to the PCM audio file
            sample_rate: Sample rate in Hz (default: 8000)
            sample_width: Sample width in bytes (default: 2)
            sample_duration: Duration to analyze in seconds (default: 1.0)
                
        Returns:
            float: RMS audio level or 0 on failure
        """
        try:
            from .sound import analyze_pcm_audio_level
            
            # Verify file exists
            if not os.path.exists(file_path):
                logger.error(f"PCM file not found: {file_path}")
                return 0
                
            # Analyze the audio level
            result = analyze_pcm_audio_level(
                file_path=file_path,
                sample_rate=sample_rate,
                sample_width=sample_width,
                sample_duration=sample_duration
            )
            
            logger.info(f"Audio level analysis completed for {file_path}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in analyze_pcm_audio_level: {e}")
            return 0

    def extract_audio_segment(self, file_path, speech_segment, sample_rate=8000, sample_width=2):
        """
        Extract an audio segment from a PCM file based on segment metadata.
        
        Args:
            file_path: Path to the PCM audio file
            speech_segment: Dictionary containing segment metadata with keys:
                - pcm_start_byte: Starting byte position in the file
                - pcm_end_byte: Ending byte position in the file
            sample_rate: Sample rate of the audio (default: 8000 Hz)
            sample_width: Sample width in bytes (default: 2 bytes/sample)
                
        Returns:
            tuple: (audio_data, segment_info) or (None, None) on failure
                - audio_data: Binary data of the extracted segment
                - segment_info: Dictionary with metadata about the extracted segment
        """
        try:
            from .sound import extract_audio_segment
            
            # Verify file exists
            if not os.path.exists(file_path):
                logger.error(f"PCM file not found: {file_path}")
                return None, None
                
            # Extract the audio segment
            audio_data, segment_info = extract_audio_segment(
                file_path=file_path,
                speech_segment=speech_segment,
                sample_rate=sample_rate,
                sample_width=sample_width
            )
            
            if audio_data is None:
                logger.error(f"Failed to extract audio segment from {file_path}")
                return None, None
                
            logger.info(f"Audio segment extracted from {file_path}: {segment_info}")
            return audio_data, segment_info
            
        except Exception as e:
            logger.error(f"Error in extract_audio_segment: {e}")
            return None, None            