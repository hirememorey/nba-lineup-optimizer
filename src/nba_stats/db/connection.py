"""Database connection management for NBA stats application."""

import sqlite3
import logging
from typing import Optional
from datetime import datetime
from ..config.settings import DB_PATH

def register_datetime_adapters():
    """Register adapters for datetime objects to be stored as ISO 8601 strings."""
    def adapt_datetime(ts):
        return ts.isoformat()
    
    def convert_timestamp(val):
        """Convert ISO 8601 string to datetime object."""
        return datetime.fromisoformat(val.decode('utf-8'))

    sqlite3.register_adapter(datetime, adapt_datetime)
    sqlite3.register_converter("timestamp", convert_timestamp)

class DatabaseConnection:
    """Manages database connections and provides common database operations."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initializes the database connection.
        
        Args:
            db_path: Path to the database file. Defaults to path from settings.
        """
        self.db_path = db_path or DB_PATH
        self.connection = None
        self.cursor = None
        
    def connect(self) -> sqlite3.Connection:
        """Establish a connection to the database.
        
        Returns:
            sqlite3.Connection: The database connection
            
        Raises:
            sqlite3.Error: If connection cannot be established
        """
        if self.connection is None:
            try:
                self.connection = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
                self.connection.row_factory = sqlite3.Row
                register_datetime_adapters()
                logging.info("Database connection established successfully.")
            except sqlite3.Error as e:
                logging.error(f"Database connection error: {e}")
                raise
        return self.connection
    
    def close(self) -> None:
        """Close the database connection if it exists."""
        if self.connection is not None:
            try:
                self.connection.close()
                self.connection = None
                logging.info("Database connection closed successfully.")
            except sqlite3.Error as e:
                logging.error(f"Error closing database connection: {e}")
    
    def execute(self, query: str, params: tuple = None) -> sqlite3.Cursor:
        """Execute a SQL query.
        
        Args:
            query: SQL query to execute
            params: Parameters for the query
            
        Returns:
            sqlite3.Cursor: The cursor with the query results
            
        Raises:
            sqlite3.Error: If query execution fails
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor
        except sqlite3.Error as e:
            logging.error(f"Database error executing query: {e}")
            raise
    
    def execute_many(self, query: str, params_list: list) -> None:
        """Execute a SQL query multiple times with different parameters.
        
        Args:
            query: SQL query to execute
            params_list: List of parameter tuples
            
        Raises:
            sqlite3.Error: If query execution fails
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Database error executing many queries: {e}")
            raise
    
    def fetch_all(self, query: str, params: tuple = None) -> list:
        """Execute a query and fetch all results.
        
        Args:
            query: SQL query to execute
            params: Parameters for the query
            
        Returns:
            list: List of results
            
        Raises:
            sqlite3.Error: If query execution fails
        """
        cursor = self.execute(query, params)
        return cursor.fetchall()
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[tuple]:
        """Execute a query and fetch one result.
        
        Args:
            query: SQL query to execute
            params: Parameters for the query
            
        Returns:
            Optional[tuple]: Single result or None if no results
            
        Raises:
            sqlite3.Error: If query execution fails
        """
        cursor = self.execute(query, params)
        return cursor.fetchone()
    
    def __enter__(self):
        """Context manager entry."""
        return self.connect()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

def get_db_connection() -> Optional[sqlite3.Connection]:
    """
    Provides a direct database connection.
    This is a helper function to avoid changing all call sites that expect
    a direct connection object rather than a manager class.
    """
    try:
        register_datetime_adapters()
        conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logging.error(f"Failed to get database connection: {e}")
        return None 