"""Common utility functions for NBA stats scripts."""

import logging
import sqlite3
from datetime import datetime
from ..api.nba_stats_client import NBAStatsClient # Adjusted import path
from ..config import settings
from typing import Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("nba_stats.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DB_PATH = "src/nba_stats/db/nba_stats.db" # Define DB_PATH relative to workspace root

def adapt_datetime(dt):
    """Adapt datetime to SQLite format."""
    return dt.isoformat()

def convert_datetime(val):
    """Convert SQLite value to datetime."""
    try:
        return datetime.fromisoformat(val.decode())
    except (AttributeError, ValueError):
        return None

def get_db_connection():
    """Establish and return a database connection."""
    sqlite3.register_adapter(datetime, adapt_datetime)
    sqlite3.register_converter("TIMESTAMP", convert_datetime)
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    logger.info(f"Using database at {DB_PATH}")
    return conn

def get_nba_stats_client():
    """Return an instance of the NBAStatsClient."""
    return NBAStatsClient()

def add_column_if_not_exists(conn, table_name, column_name, column_def):
    """
    Adds a column to a table if it doesn't already exist.
    """
    cursor = conn.cursor()
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        if column_name not in columns:
            logger.info(f"Adding column '{column_name}' to table '{table_name}'...")
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")
            conn.commit()
            logger.info("Column added successfully.")
        else:
            logger.debug(f"Column '{column_name}' already exists in table '{table_name}'.")
    except sqlite3.Error as e:
        logger.error(f"Error adding column '{column_name}' to '{table_name}': {e}")

def migrate_table(conn: sqlite3.Connection, table_name: str, schema: Dict[str, str]):
    """
    Adds any missing columns to a table based on a provided schema.
    """
    logger.info(f"Checking for schema updates for table '{table_name}'...")
    try:
        for column_name, column_def in schema.items():
            add_column_if_not_exists(conn, table_name, column_name, column_def)
        logger.info(f"No new columns needed for '{table_name}'. Schema is up-to-date.")
    except Exception as e:
        logger.error(f"Error migrating table {table_name}: {e}", exc_info=True) 