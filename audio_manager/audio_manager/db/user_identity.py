import logging
import sqlite3
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

class UserIdentityRecord:
    """
    Class for user identity information matching the user_identities table.
    """
    def __init__(self, id: Optional[int] = None, first_name: Optional[str] = None,
                 middle_name: Optional[str] = None, last_name: Optional[str] = None,
                 affiliation: Optional[str] = None, phone: Optional[str] = None,
                 user_name: Optional[str] = None):
        self.id = id
        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name = last_name
        self.affiliation = affiliation
        self.phone = phone
        self.user_name = user_name
    
    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.middle_name:
            parts.append(self.middle_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts)
    
    def register(self, db):
        """Register this user identity in the database."""
        if self.id is not None:
            logger.warning(f"User identity already has ID {self.id}, not registering again")
            return self.id
        
        try:
            cursor = db.conn.cursor()
            cursor.execute('''
                INSERT INTO user_identities (first_name, middle_name, last_name, 
                                          affiliation, phone, user_name)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.first_name, self.middle_name, self.last_name, 
                 self.affiliation, self.phone, self.user_name))
            db.conn.commit()
            
            self.id = cursor.lastrowid
            logger.info(f"Registered user identity with ID: {self.id}")
            return self.id
        except sqlite3.Error as e:
            logger.error(f"Error registering user identity: {e}")
            raise
    
    def update(self, db):
        """Update this user identity in the database."""
        if self.id is None:
            raise ValueError("Cannot update user identity without ID")
        
        try:
            cursor = db.conn.cursor()
            cursor.execute('''
                UPDATE user_identities 
                SET first_name = ?, middle_name = ?, last_name = ?, 
                    affiliation = ?, phone = ?, user_name = ?
                WHERE id = ?
            ''', (self.first_name, self.middle_name, self.last_name,
                 self.affiliation, self.phone, self.user_name, self.id))
            db.conn.commit()
            
            affected_rows = cursor.rowcount
            logger.info(f"Updated user identity with ID: {self.id}, rows affected: {affected_rows}")
            return affected_rows > 0
        except sqlite3.Error as e:
            logger.error(f"Error updating user identity {self.id}: {e}")
            raise
    
    def delete(self, db):
        """Delete this user identity from the database."""
        if self.id is None:
            raise ValueError("Cannot delete user identity without ID")
        
        try:
            cursor = db.conn.cursor()
            cursor.execute('DELETE FROM user_identities WHERE id = ?', (self.id,))
            db.conn.commit()
            
            affected_rows = cursor.rowcount
            logger.info(f"Deleted user identity with ID: {self.id}, rows affected: {affected_rows}")
            return affected_rows > 0
        except sqlite3.Error as e:
            logger.error(f"Error deleting user identity {self.id}: {e}")
            raise
        
    @classmethod
    def get(cls, db, user_id: int):
        """Retrieve a user identity from the database by ID."""
        try:
            cursor = db.conn.cursor()
            cursor.execute('''SELECT id, first_name, middle_name, last_name, 
                           affiliation, phone, user_name 
                           FROM user_identities WHERE id = ?''', (user_id,))
            record = cursor.fetchone()
            
            if not record:
                logger.warning(f"User identity {user_id} not found")
                return None
                
            return cls(
                id=record[0], 
                first_name=record[1], 
                middle_name=record[2],
                last_name=record[3],
                affiliation=record[4],
                phone=record[5],
                user_name=record[6]
            )
            
        except sqlite3.Error as e:
            logger.error(f"Error retrieving user identity {user_id}: {e}")
            raise
    
    @classmethod
    def get_all(cls, db) -> List['UserIdentityRecord']:
        """Retrieve all user identities from the database."""
        try:
            cursor = db.conn.cursor()
            cursor.execute('''SELECT id, first_name, middle_name, last_name, 
                           affiliation, phone, user_name FROM user_identities''')
            records = cursor.fetchall()
            
            return [cls(
                id=record[0], 
                first_name=record[1], 
                middle_name=record[2],
                last_name=record[3],
                affiliation=record[4],
                phone=record[5],
                user_name=record[6]
            ) for record in records]
            
        except sqlite3.Error as e:
            logger.error(f"Error retrieving all user identities: {e}")
            raise
    
    @classmethod
    def find_by_name(cls, db, name: str) -> List['UserIdentityRecord']:
        """Find user identities by name."""
        try:
            cursor = db.conn.cursor()
            search_term = f'%{name}%'
            cursor.execute('''
                SELECT id, first_name, middle_name, last_name, affiliation, phone, user_name 
                FROM user_identities 
                WHERE first_name LIKE ? OR middle_name LIKE ? OR last_name LIKE ?
            ''', (search_term, search_term, search_term))
            records = cursor.fetchall()
            
            return [cls(
                id=record[0], 
                first_name=record[1], 
                middle_name=record[2],
                last_name=record[3],
                affiliation=record[4],
                phone=record[5],
                user_name=record[6]
            ) for record in records]
        except sqlite3.Error as e:
            logger.error(f"Error finding user identities by name {name}: {e}")
            raise
    
    @classmethod
    def find_by_username(cls, db, username: str) -> Optional['UserIdentityRecord']:
        """Find a user identity by username."""
        try:
            cursor = db.conn.cursor()
            cursor.execute('''
                SELECT id, first_name, middle_name, last_name, affiliation, phone, user_name 
                FROM user_identities 
                WHERE user_name = ?
            ''', (username,))
            record = cursor.fetchone()
            
            if not record:
                return None
                
            return cls(
                id=record[0], 
                first_name=record[1], 
                middle_name=record[2],
                last_name=record[3],
                affiliation=record[4],
                phone=record[5],
                user_name=record[6]
            )
        except sqlite3.Error as e:
            logger.error(f"Error finding user identity by username {username}: {e}")
            raise