"""
This script fixes the data type of the player_id column in all tables
where it exists, casting it to INTEGER. This is necessary to repair
data inserted by older scripts that may have stored player_id as TEXT.
"""

import sqlite3
from .common_utils import get_db_connection, logger

def get_tables_with_player_id(conn: sqlite3.Connection) -> list[str]:
    """
    Scans the database and returns a list of all tables containing a
    'player_id' column.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    tables_with_player_id = []
    for table in tables:
        cursor.execute(f"PRAGMA table_info('{table}')")
        columns = [row[1] for row in cursor.fetchall()]
        if 'player_id' in columns:
            tables_with_player_id.append(table)
            
    logger.info(f"Found {len(tables_with_player_id)} tables with 'player_id' column: {tables_with_player_id}")
    return tables_with_player_id

def fix_player_id_column(conn: sqlite3.Connection, table_name: str):
    """
    Updates the player_id column in a given table, casting all values to INTEGER.
    """
    logger.info(f"Attempting to fix 'player_id' column in table: '{table_name}'...")
    cursor = conn.cursor()
    try:
        # This command will attempt to cast the player_id to an integer.
        # SQLite will perform the cast. If a value cannot be cast (e.g., non-numeric text),
        # it may result in 0 or remain as text depending on the context, but
        # for player IDs from the NBA API, this should be safe.
        cursor.execute(f"UPDATE {table_name} SET player_id = CAST(player_id AS INTEGER)")
        
        # We can also check for rows that failed to cast if necessary, but this is a good first step.
        logger.info(f"Successfully executed player_id fix for table '{table_name}'. Affected rows: {cursor.rowcount}")

    except sqlite3.Error as e:
        logger.error(f"Failed to fix player_id in table '{table_name}': {e}", exc_info=True)
        raise # Re-raise the exception to trigger a transaction rollback

def main():
    """Main function to run the data fixing script."""
    logger.info("Starting player_id data type fix process...")
    conn = get_db_connection()
    if not conn:
        logger.error("Could not get database connection. Aborting.")
        return

    tables_to_fix = get_tables_with_player_id(conn)
    
    if not tables_to_fix:
        logger.info("No tables with a 'player_id' column found. Nothing to do.")
        conn.close()
        return

    try:
        # Start a transaction
        conn.execute('BEGIN')

        for table in tables_to_fix:
            fix_player_id_column(conn, table)
        
        # Commit the transaction
        conn.commit()
        logger.info("All tables successfully fixed and transaction committed.")

    except Exception as e:
        logger.error(f"An error occurred during the fix process. Rolling back transaction. Error: {e}")
        conn.rollback()
    
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    main() 