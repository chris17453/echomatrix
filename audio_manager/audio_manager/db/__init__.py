"""
db module for audio manager

- Classes for managing audio recording data in the registry database.

This module provides classes that correspond to the tables in the registry database:
- AIIdentityRecord: Corresponds to the ai_identities table
- UserIdentityRecord: Corresponds to the user_identities table
- FileRecord: Corresponds to the recording_files table
- RecordingRecord: Corresponds to the recordings table

Each class provides methods for creating, retrieving, and managing records in a 
type-safe manner that directly corresponds to the database schema.
"""

from .database import Database
from .ai_identity import AIIdentityRecord
from .user_identity import UserIdentityRecord
from .file import FileRecord
from .record import RecordingRecord

__all__ = [
    'Database',
    'AIIdentityRecord',
    'UserIdentityRecord',
    'FileRecord',
    'RecordingRecord'
]