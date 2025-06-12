"""
Database connection and management module.
"""
import sqlite3
import pandas as pd
import logging
from typing import Optional, List, Dict, Any
from src.nba_stats.config.settings import DB_PATH

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DatabaseConnection:
    def __init__(self, db_path: str = DB_PATH):
        """Initialize database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._connection = sqlite3.connect(db_path)
        self._connection.row_factory = sqlite3.Row
        self._cursor = self._connection.cursor()
        
        # Enable WAL mode for better concurrency
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=NORMAL")
        
        logging.info("Database connection established successfully.")
    
    def execute(self, query: str, params: Optional[tuple] = None) -> None:
        """Execute a SQL query with optional parameters."""
        try:
            if params:
                self._cursor.execute(query, params)
            else:
                self._cursor.execute(query)
        except sqlite3.Error as e:
            logging.error(f"Database error: {str(e)}")
            raise
    
    def executemany(self, query: str, params: List[tuple]) -> None:
        """Execute a SQL query with multiple parameter sets."""
        try:
            self._cursor.executemany(query, params)
        except sqlite3.Error as e:
            logging.error(f"Database error: {str(e)}")
            raise
            
    def fetchall(self) -> List[Dict[str, Any]]:
        """Fetch all results from the last query."""
        return [dict(row) for row in self._cursor.fetchall()]
        
    def fetchone(self) -> Optional[Dict[str, Any]]:
        """Fetch one result from the last query."""
        row = self._cursor.fetchone()
        return dict(row) if row else None
        
    def commit(self) -> None:
        """Commit the current transaction."""
        self._connection.commit()
        
    def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            logging.info("Database connection closed successfully.")

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        logging.info(f"Successfully connected to the database at {DB_PATH}.")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Failed to connect to the database: {str(e)}")
        raise 