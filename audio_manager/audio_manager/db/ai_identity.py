import logging
import sqlite3
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

class AIIdentityRecord:
    """
    Class for AI identity information matching the identities table.
    """
    def __init__(self, id: Optional[int] = None, model: Optional[str] = None, 
                 voice: Optional[str] = None, provider: Optional[str] = None,
                 instruction: Optional[str] = None):
        self.id = id
        self.model = model
        self.voice = voice
        self.provider = provider
        self.instruction = instruction
    
    def register(self, db):
        """Register this AI identity in the database."""
        if self.id is not None:
            logger.warning(f"AI identity already has ID {self.id}, not registering again")
            return self.id
        
        try:
            cursor = db.conn.cursor()
            cursor.execute('''
                INSERT INTO ai_identities (model, voice, provider, instruction)
                VALUES (?, ?, ?, ?)
            ''', (self.model, self.voice, self.provider, self.instruction))
            db.conn.commit()
            
            self.id = cursor.lastrowid
            logger.info(f"Registered AI identity with ID: {self.id}")
            return self.id
        except sqlite3.Error as e:
            logger.error(f"Error registering AI identity: {e}")
            raise
    
    def update(self, db):
        """Update this AI identity in the database."""
        if self.id is None:
            raise ValueError("Cannot update AI identity without ID")
        
        try:
            cursor = db.conn.cursor()
            cursor.execute('''
                UPDATE ai_identities 
                SET model = ?, voice = ?, provider = ?, instruction = ?
                WHERE id = ?
            ''', (self.model, self.voice, self.provider, self.instruction, self.id))
            db.conn.commit()
            
            affected_rows = cursor.rowcount
            logger.info(f"Updated AI identity with ID: {self.id}, rows affected: {affected_rows}")
            return affected_rows > 0
        except sqlite3.Error as e:
            logger.error(f"Error updating AI identity {self.id}: {e}")
            raise
    
    def delete(self, db):
        """Delete this AI identity from the database."""
        if self.id is None:
            raise ValueError("Cannot delete AI identity without ID")
        
        try:
            cursor = db.conn.cursor()
            cursor.execute('DELETE FROM ai_identities WHERE id = ?', (self.id,))
            db.conn.commit()
            
            affected_rows = cursor.rowcount
            logger.info(f"Deleted AI identity with ID: {self.id}, rows affected: {affected_rows}")
            return affected_rows > 0
        except sqlite3.Error as e:
            logger.error(f"Error deleting AI identity {self.id}: {e}")
            raise
        
    @classmethod
    def get(cls, db, id: int):
        """Retrieve an AI identity from the database by ID."""
        try:
            cursor = db.conn.cursor()
            cursor.execute('SELECT id, model, voice, provider, instruction FROM ai_identities WHERE id = ?', (id,))
            record = cursor.fetchone()
            
            if not record:
                logger.warning(f"AI identity {id} not found")
                return None
                
            return cls(id=record[0], model=record[1], voice=record[2], 
                       provider=record[3], instruction=record[4])
            
        except sqlite3.Error as e:
            logger.error(f"Error retrieving AI identity {id}: {e}")
            raise
    
    @classmethod
    def get_all(cls, db) -> List['AIIdentityRecord']:
        """Retrieve all AI identities from the database."""
        try:
            cursor = db.conn.cursor()
            cursor.execute('SELECT id, model, voice, provider, instruction FROM ai_identities')
            records = cursor.fetchall()
            
            return [cls(id=record[0], model=record[1], voice=record[2],
                        provider=record[3], instruction=record[4]) 
                   for record in records]
            
        except sqlite3.Error as e:
            logger.error(f"Error retrieving all AI identities: {e}")
            raise
    
    @classmethod
    def find_by_model(cls, db, model_name: str) -> List['AIIdentityRecord']:
        """Find AI identities by model name."""
        try:
            cursor = db.conn.cursor()
            cursor.execute('SELECT id, model, voice, provider, instruction FROM ai_identities WHERE model LIKE ?', (f'%{model_name}%',))
            records = cursor.fetchall()
            
            return [cls(id=record[0], model=record[1], voice=record[2],
                        provider=record[3], instruction=record[4])
                   for record in records]
        except sqlite3.Error as e:
            logger.error(f"Error finding AI identities by model {model_name}: {e}")
            raise

    @classmethod
    def find_by_all_fields(cls, db, model: Optional[str] = None,
                           voice: Optional[str] = None,
                           provider: Optional[str] = None,
                           instruction: Optional[str] = None) -> List['AIIdentityRecord']:
        """Find AI identities by exact match on any combination of fields."""
        try:
            query = 'SELECT id, model, voice, provider, instruction FROM ai_identities WHERE 1=1'
            params = []

            if model is not None:
                query += ' AND model = ?'
                params.append(model)
            if voice is not None:
                query += ' AND voice = ?'
                params.append(voice)
            if provider is not None:
                query += ' AND provider = ?'
                params.append(provider)
            if instruction is not None:
                query += ' AND instruction = ?'
                params.append(instruction)

            cursor = db.conn.cursor()
            cursor.execute(query, tuple(params))
            records = cursor.fetchall()

            return [cls(id=record[0], model=record[1], voice=record[2],
                        provider=record[3], instruction=record[4])
                    for record in records]
        except sqlite3.Error as e:
            logger.error("Error finding AI identities by fields: %s", e)
            raise
