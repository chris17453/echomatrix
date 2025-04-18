import logging
import sqlite3
import uuid
from datetime import datetime
from typing import Optional, List, Tuple
from .ai_identity import AIIdentityRecord
from .user_identity import UserIdentityRecord
from .file import FileRecord

logger = logging.getLogger(__name__)

class RecordingRecord:
    def __init__(
        self,
        session_id: Optional[str] = None,
        id: Optional[str] = None,
        text: Optional[str] = None,
        ai_generated: bool = False,
        user_recorded: bool = False,
        ai_identity_id: Optional[int] = None,
        user_identity_id: Optional[int] = None,
        location: str = "local",
        timestamp: Optional[str] = None
    ):
        self.session_id = session_id
        self.id = id if id is not None else str(uuid.uuid4())
        self.text = text
        self.ai_generated = ai_generated
        self.user_recorded = user_recorded
        self.ai_identity_id = ai_identity_id
        self.user_identity_id = user_identity_id
        self.location = location
        self.timestamp = timestamp if timestamp else datetime.now().isoformat()

        self._ai_identity = None
        self._user_identity = None
        self._files = None

    def register(self, db):
        try:
            cursor = db.conn.cursor()
            cursor.execute('SELECT id FROM recordings WHERE id = ?', (self.id,))
            existing = cursor.fetchone()
            if existing:
                logger.warning(f"Recording with ID {self.id} already exists in database")
                return self.id


            cursor.execute('''
                INSERT INTO recordings (
                    id, text, ai_generated, user_recorded,
                    ai_identity_id, user_identity_id, location, timestamp, session_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.id, self.text,
                1 if self.ai_generated else 0,
                1 if self.user_recorded else 0,
                self.ai_identity_id,
                self.user_identity_id,
                self.location,
                self.timestamp,
                self.session_id
            ))
            db.conn.commit()
            logger.info(f"Registered recording with ID: {self.id}")
            return self.id
        except sqlite3.Error as e:
            logger.error(f"Error registering recording: {e}")
            raise

    def update(self, db):
        if not self.id:
            raise ValueError("Cannot update recording without ID")
        try:
            cursor = db.conn.cursor()
            cursor.execute('''
                UPDATE recordings
                SET text = ?,  ai_generated = ?, user_recorded = ?,
                    ai_identity_id = ?, user_identity_id = ?, location = ?, session_id = ?
                WHERE id = ?
            ''', (
                self.text, 
                1 if self.ai_generated else 0,
                1 if self.user_recorded else 0,
                self.ai_identity_id,
                self.user_identity_id,
                self.location,
                self.session_id,
                self.id
            ))
            db.conn.commit()
            affected_rows = cursor.rowcount
            logger.info(f"Updated recording with ID: {self.id}, rows affected: {affected_rows}")
            return affected_rows > 0
        except sqlite3.Error as e:
            logger.error(f"Error updating recording {self.id}: {e}")
            raise

    def delete(self, db):
        if not self.id:
            raise ValueError("Cannot delete recording without ID")
        try:
            FileRecord.delete_by_recording(db, self.id)
            cursor = db.conn.cursor()
            cursor.execute('DELETE FROM recordings WHERE id = ?', (self.id,))
            db.conn.commit()
            affected_rows = cursor.rowcount
            logger.info(f"Deleted recording with ID: {self.id}, rows affected: {affected_rows}")
            return affected_rows > 0
        except sqlite3.Error as e:
            logger.error(f"Error deleting recording {self.id}: {e}")
            raise

    def add_file(self, db, file_type: str, path: str):
        if not self.id:
            raise ValueError("Recording must be registered before adding files")
        file_record = FileRecord(recording_id=self.id, file_type=file_type, path=path)
        file_record.register(db)
        self._files = None
        return file_record

    def get_files(self, db) -> List[FileRecord]:
        if self._files is not None:
            return self._files
        if not self.id:
            return []
        self._files = FileRecord.get_by_recording(db, self.id)
        return self._files

    def get_ai_identity(self, db) -> Optional[AIIdentityRecord]:
        if self._ai_identity:
            return self._ai_identity
        if not self.ai_identity_id:
            return None
        self._ai_identity = AIIdentityRecord.get(db, self.ai_identity_id)
        return self._ai_identity

    def get_user_identity(self, db) -> Optional[UserIdentityRecord]:
        if self._user_identity:
            return self._user_identity
        if not self.user_identity_id:
            return None
        self._user_identity = UserIdentityRecord.get(db, self.user_identity_id)
        return self._user_identity

    @classmethod
    def get(cls, db, recording_id: str):
        try:
            cursor = db.conn.cursor()
            cursor.execute('''
                SELECT id, text, ai_generated, user_recorded,
                       ai_identity_id, user_identity_id, location, timestamp, session_id
                FROM recordings WHERE id = ?
            ''', (recording_id,))
            record = cursor.fetchone()
            if not record:
                logger.warning(f"Recording {recording_id} not found")
                return None
            return cls(
                id=record[0], text=record[1], 
                ai_generated=bool(record[2]), user_recorded=bool(record[3]),
                ai_identity_id=record[4], user_identity_id=record[5],
                location=record[6], timestamp=record[7], session_id=record[8]
            )
        except sqlite3.Error as e:
            logger.error(f"Error retrieving recording {recording_id}: {e}")
            raise

    @classmethod
    def get_all(cls, db) -> List['RecordingRecord']:
        try:
            cursor = db.conn.cursor()
            cursor.execute('''
                SELECT id, text, ai_generated, user_recorded,
                       ai_identity_id, user_identity_id, location, timestamp, session_id
                FROM recordings
            ''')
            records = cursor.fetchall()
            return [
                cls(
                    id=r[0], text=r[1], 
                    ai_generated=bool(r[2]), user_recorded=bool(r[3]),
                    ai_identity_id=r[4], user_identity_id=r[5],
                    location=r[6], timestamp=r[7], session_id=r[8]
                ) for r in records
            ]
        except sqlite3.Error as e:
            logger.error("Error retrieving all recordings: {e}")
            raise

    @classmethod

    def find_by_ai_text(cls, db, text: str, ai_entity_id: int) -> Optional['RecordingRecord']:
        try:
            cursor = db.conn.cursor()
            query = '''
                SELECT id, text, ai_generated, user_recorded,
                    ai_identity_id, user_identity_id, location, timestamp, session_id
                FROM recordings 
                WHERE text COLLATE NOCASE = ? AND ai_identity_id = ?
            '''
            cursor.execute(query, (text, ai_entity_id))
            record = cursor.fetchone()
            if not record:
                return None
            return cls(
                id=record[0], text=record[1], 
                ai_generated=bool(record[2]), user_recorded=bool(record[3]),
                ai_identity_id=record[4], user_identity_id=record[5],
                location=record[6], timestamp=record[7], session_id=record[8]
            )
        except sqlite3.Error as e:
            logger.error(f"Error finding recording by text and entity ID: {e}")
            raise

    @classmethod
    def find_by_location(cls, db, location: str) -> List['RecordingRecord']:
        try:
            cursor = db.conn.cursor()
            cursor.execute('''
                SELECT id, text, ai_generated, user_recorded,
                       ai_identity_id, user_identity_id, location, timestamp, session_id
                FROM recordings WHERE location = ?
            ''', (location,))
            records = cursor.fetchall()
            return [
                cls(
                    id=r[0], text=r[1], 
                    ai_generated=bool(r[2]), user_recorded=bool(r[3]),
                    ai_identity_id=r[4], user_identity_id=r[5],
                    location=r[6], timestamp=r[7], session_id=r[8]
                ) for r in records
            ]
        except sqlite3.Error as e:
            logger.error(f"Error finding recordings by location {location}: {e}")
            raise

    @classmethod
    def find_by_type(cls, db, is_ai_generated: bool = None, is_user_recorded: bool = None) -> List['RecordingRecord']:
        try:
            query = '''
                SELECT id, text,  ai_generated, user_recorded,
                       ai_identity_id, user_identity_id, location, timestamp, session_id
                FROM recordings WHERE 1=1
            '''
            params = []
            if is_ai_generated is not None:
                query += ' AND ai_generated = ?'
                params.append(1 if is_ai_generated else 0)
            if is_user_recorded is not None:
                query += ' AND user_recorded = ?'
                params.append(1 if is_user_recorded else 0)
            cursor = db.conn.cursor()
            cursor.execute(query, tuple(params))
            records = cursor.fetchall()
            return [
                cls(
                    id=r[0], text=r[1], 
                    ai_generated=bool(r[2]), user_recorded=bool(r[3]),
                    ai_identity_id=r[4], user_identity_id=r[5],
                    location=r[6], timestamp=r[7], session_id=r[8]
                ) for r in records
            ]
        except sqlite3.Error as e:
            logger.error(f"Error finding recordings by type: {e}")
            raise

    @classmethod
    def find_by_session(cls, db, session_id: str) -> List['RecordingRecord']:
        try:
            cursor = db.conn.cursor()
            cursor.execute('''
                SELECT id, text,  ai_generated, user_recorded,
                       ai_identity_id, user_identity_id, location, timestamp, session_id
                FROM recordings WHERE session_id = ?
            ''', (session_id,))
            records = cursor.fetchall()
            return [
                cls(
                    id=r[0], text=r[1], 
                    ai_generated=bool(r[2]), user_recorded=bool(r[3]),
                    ai_identity_id=r[4], user_identity_id=r[5],
                    location=r[6], timestamp=r[7], session_id=r[8]
                ) for r in records
            ]
        except sqlite3.Error as e:
            logger.error(f"Error finding recordings by session: {e}")
            raise

    @classmethod
    def update_location(cls, db, recording_id: str, new_location: str) -> bool:
        try:
            cursor = db.conn.cursor()
            cursor.execute('''
                UPDATE recordings
                SET location = ?
                WHERE id = ?
            ''', (new_location, recording_id))
            db.conn.commit()
            affected_rows = cursor.rowcount
            logger.info(f"Updated location for recording {recording_id} to {new_location}, rows affected: {affected_rows}")
            return affected_rows > 0
        except sqlite3.Error as e:
            logger.error(f"Error updating location for recording {recording_id}: {e}")
            raise