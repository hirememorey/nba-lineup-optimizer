"""Database initialization script."""

import logging
import sqlite3
from pathlib import Path

from ..config.settings import DB_FILE
from ..scripts.create_tables import create_all_tables


def init_database(db_path: str = DB_FILE) -> None:
    """Initialize the NBA stats database with all necessary tables.
    
    Args:
        db_path: Path to the SQLite database file
    """
    conn = None
    try:
        # Create database directory if it doesn't exist
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Enable WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode = WAL")
        
        # Create all tables
        create_all_tables(conn)
        
        logging.info("Database initialized successfully.")
        
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()