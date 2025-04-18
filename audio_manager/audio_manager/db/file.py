import logging
import sqlite3
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

class FileRecord:
    """
    Class for file information matching the recording_files table.
    """
    def __init__(self, id: Optional[int] = None, recording_id: Optional[str] = None,
                 file_type: Optional[str] = None, path: Optional[str] = None):
        self.id = id
        self.recording_id = recording_id
        self.file_type = file_type
        self.path = path
    
    def register(self, db):
        """Register this file in the database."""
        if self.id is not None:
            logger.warning(f"File record already has ID {self.id}, not registering again")
            return self.id
            
        if not self.recording_id:
            raise ValueError("Recording ID is required to register a file")
            
        if not self.file_type:
            raise ValueError("File type is required to register a file")
            
        if not self.path:
            raise ValueError("File path is required to register a file")
        
        try:
            cursor = db.conn.cursor()
            cursor.execute('''
                INSERT INTO recording_files (recording_id, file_type, path)
                VALUES (?, ?, ?)
            ''', (self.recording_id, self.file_type, str(self.path)))
            db.conn.commit()
            
            self.id = cursor.lastrowid
            logger.info(f"Registered file record with ID: {self.id}")
            return self.id
            
        except sqlite3.Error as e:
            logger.error(f"Error registering file record: {e}")
            raise
    
    def update(self, db):
        """Update this file record in the database."""
        if self.id is None:
            raise ValueError("Cannot update file record without ID")
            
        try:
            cursor = db.conn.cursor()
            cursor.execute('''
                UPDATE recording_files
                SET recording_id = ?, file_type = ?, path = ?
                WHERE id = ?
            ''', (self.recording_id, self.file_type, str(self.path), self.id))
            db.conn.commit()
            
            affected_rows = cursor.rowcount
            logger.info(f"Updated file record with ID: {self.id}, rows affected: {affected_rows}")
            return affected_rows > 0
        except sqlite3.Error as e:
            logger.error(f"Error updating file record {self.id}: {e}")
            raise
    
    def delete(self, db):
        """Delete this file record from the database."""
        if self.id is None:
            raise ValueError("Cannot delete file record without ID")
            
        try:
            cursor = db.conn.cursor()
            cursor.execute('DELETE FROM recording_files WHERE id = ?', (self.id,))
            db.conn.commit()
            
            affected_rows = cursor.rowcount
            logger.info(f"Deleted file record with ID: {self.id}, rows affected: {affected_rows}")
            return affected_rows > 0
        except sqlite3.Error as e:
            logger.error(f"Error deleting file record {self.id}: {e}")
            raise
    
    @classmethod
    def get(cls, db, file_id: int):
        """Retrieve a file record from the database by ID."""
        try:
            cursor = db.conn.cursor()
            cursor.execute('SELECT id, recording_id, file_type, path FROM recording_files WHERE id = ?', (file_id,))
            record = cursor.fetchone()
            
            if not record:
                logger.warning(f"File record {file_id} not found")
                return None
                
            return cls(
                id=record[0],
                recording_id=record[1],
                file_type=record[2],
                path=record[3]
            )
            
        except sqlite3.Error as e:
            logger.error(f"Error retrieving file record {file_id}: {e}")
            raise
    
    @classmethod
    def get_by_recording(cls, db, recording_id: str) -> List['FileRecord']:
        """Retrieve all file records associated with a recording."""
        try:
            cursor = db.conn.cursor()
            cursor.execute('SELECT id, recording_id, file_type, path FROM recording_files WHERE recording_id = ?', (recording_id,))
            records = cursor.fetchall()
            
            if not records:
                logger.info(f"No file records found for recording {recording_id}")
                return []
                
            return [cls(
                id=record[0],
                recording_id=record[1],
                file_type=record[2],
                path=record[3]
            ) for record in records]
            
        except sqlite3.Error as e:
            logger.error(f"Error retrieving file records for recording {recording_id}: {e}")
            raise
    
    @classmethod
    def get_by_type(cls, db, recording_id: str, file_type: str) -> Optional['FileRecord']:
        """Get a file of a specific type for a recording."""
        try:
            cursor = db.conn.cursor()
            cursor.execute('''
                SELECT id, recording_id, file_type, path 
                FROM recording_files 
                WHERE recording_id = ? AND file_type = ?
            ''', (recording_id, file_type))
            record = cursor.fetchone()
            
            if not record:
                logger.info(f"No {file_type} file found for recording {recording_id}")
                return None
                
            return cls(
                id=record[0],
                recording_id=record[1],
                file_type=record[2],
                path=record[3]
            )
        except sqlite3.Error as e:
            logger.error(f"Error retrieving {file_type} file for recording {recording_id}: {e}")
            raise
    
    @classmethod
    def delete_by_recording(cls, db, recording_id: str) -> int:
        """Delete all files associated with a recording."""
        try:
            cursor = db.conn.cursor()
            cursor.execute('DELETE FROM recording_files WHERE recording_id = ?', (recording_id,))
            db.conn.commit()
            
            affected_rows = cursor.rowcount
            logger.info(f"Deleted {affected_rows} file records for recording {recording_id}")
            return affected_rows
        except sqlite3.Error as e:
            logger.error(f"Error deleting file records for recording {recording_id}: {e}")
            raise