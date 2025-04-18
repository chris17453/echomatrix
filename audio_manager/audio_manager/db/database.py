import os
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class Database:
    """
    Database handler for the audio manager application.
    Manages connections and provides methods for database operations.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to the SQLite database file. If None, error
        """
        if db_path is None:
            raise ValueError("Database path cannot be None")
        
        # Convert string path to Path object
        path_obj = Path(db_path)
        
        # Create parent directories if they don't exist
        if not path_obj.parent.exists():
            path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        self.db_path = str(path_obj)
        self.conn = None
        self._connect()
        self._initialize_tables()
        
    def _connect(self):
        """Establish a connection to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            # Enable foreign key constraints
            self.conn.execute("PRAGMA foreign_keys = ON")
            # Configure connection to return rows as dictionaries
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connected to database at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def _initialize_tables(self):
        """Create the necessary tables if they don't exist."""
        try:
            cursor = self.conn.cursor()
            
            # Create AI identities table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_identities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT,
                    voice TEXT,
                    provider TEXT,
                    instruction TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
      
            
            # Create user identities table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_identities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT,
                    middle_name TEXT,
                    last_name TEXT,
                    affiliation TEXT,
                    phone TEXT,
                    user_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create recordings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recordings (
                    session_id TEXT,
                    id TEXT PRIMARY KEY,
                    text TEXT,
                    ai_generated BOOLEAN DEFAULT 0,
                    user_recorded BOOLEAN DEFAULT 0,
                    ai_identity_id INTEGER,
                    user_identity_id INTEGER,
                    location TEXT DEFAULT 'local',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ai_identity_id) REFERENCES ai_identities (id),
                    FOREIGN KEY (user_identity_id) REFERENCES user_identities (id)
                )
            ''')
            
            # Create recording files table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recording_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recording_id TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    path TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (recording_id) REFERENCES recordings (id) ON DELETE CASCADE
                )
            ''')
            
            self.conn.commit()
            logger.info("Database tables initialized")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database tables: {e}")
            raise
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
