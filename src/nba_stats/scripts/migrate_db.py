"""
Script for handling database schema migrations.
"""
import sqlite3
import logging
from typing import Dict
from .common_utils import get_db_connection, logger

def get_existing_columns(conn: sqlite3.Connection, table_name: str) -> set:
    """Gets the set of existing column names for a table."""
    cursor = conn.cursor()
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        return {row[1] for row in cursor.fetchall()}
    except sqlite3.OperationalError:
        logger.warning(f"Table '{table_name}' does not exist. It may be created by the schema script.")
        return set()

def migrate_table(conn: sqlite3.Connection, table_name: str, required_columns: Dict[str, str]):
    """
    Adds any missing columns to a specific table.
    """
    existing_columns = get_existing_columns(conn, table_name)
    if not existing_columns: # Table doesn't exist, will be created later
        return

    cursor = conn.cursor()
    added_any_columns = False
    for col_name, col_type in required_columns.items():
        if col_name not in existing_columns:
            logger.info(f"Adding column '{col_name}' to '{table_name}' table...")
            try:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")
                added_any_columns = True
            except sqlite3.OperationalError as e:
                logger.error(f"Could not add column '{col_name}' to '{table_name}': {e}")
    
    if added_any_columns:
        logger.info(f"Schema migration for '{table_name}' completed successfully.")
    else:
        logger.info(f"No new columns needed for '{table_name}'. Schema is up-to-date.")


def run_migrations(conn: sqlite3.Connection):
    """
    Runs all pending schema migrations.
    """
    teams_columns = {
        "abbreviation": "TEXT"
    }
    migrate_table(conn, "Teams", teams_columns)

    players_columns = {
        "wingspan": "REAL"
    }
    migrate_table(conn, "Players", players_columns)
    
    # Add future migrations here, for example:
    # stats_columns = {
    #     "new_stat": "REAL"
    # }
    # migrate_table(conn, "PlayerSeasonRawStats", stats_columns)

    migrate_salaries_and_skills(conn)

    conn.commit()
    logger.info("All database migrations checked.")


def migrate_salaries_and_skills(conn: sqlite3.Connection):
    """
    Handles the specific migration for PlayerSalaries and PlayerSkills tables.
    This follows a rename-and-recreate pattern to be safe and idempotent.
    """
    cursor = conn.cursor()

    # --- Migrate PlayerSalaries Table ---
    required_salaries_cols = {'player_salary_id', 'player_id', 'season_id', 'salary'}
    try:
        cursor.execute("PRAGMA table_info(PlayerSalaries)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        if required_salaries_cols.issubset(existing_columns):
            logger.info("PlayerSalaries table is already up-to-date.")
        else:
            logger.info("Outdated 'PlayerSalaries' schema found. Archiving and recreating.")
            cursor.execute("ALTER TABLE PlayerSalaries RENAME TO PlayerSalaries_old")
            create_player_salaries_table(cursor)
            logger.info("Archived old 'PlayerSalaries' table to 'PlayerSalaries_old'.")

    except sqlite3.OperationalError:
        logger.info("'PlayerSalaries' table not found. Creating new table.")
        create_player_salaries_table(cursor)

    # --- Migrate PlayerSkills Table ---
    required_skills_cols = {
        'player_skill_id', 'player_id', 'season_id', 
        'offensive_skill_rating', 'defensive_skill_rating', 'skill_metric_source'
    }
    try:
        cursor.execute("PRAGMA table_info(PlayerSkills)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        if required_skills_cols.issubset(existing_columns):
            logger.info("PlayerSkills table is already up-to-date.")
        else:
            logger.info("Outdated 'PlayerSkills' schema found. Archiving and recreating.")
            cursor.execute("ALTER TABLE PlayerSkills RENAME TO PlayerSkills_old")
            create_player_skills_table(cursor)
            logger.info("Archived old 'PlayerSkills' table to 'PlayerSkills_old'.")

    except sqlite3.OperationalError:
        logger.info("'PlayerSkills' table not found. Creating new table.")
        create_player_skills_table(cursor)


def create_player_salaries_table(cursor: sqlite3.Cursor):
    """Creates the new PlayerSalaries table."""
    cursor.execute("""
    CREATE TABLE PlayerSalaries (
        player_salary_id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        season_id TEXT NOT NULL,
        salary REAL,
        FOREIGN KEY (player_id) REFERENCES Players(player_id)
    );
    """)
    logger.info("Successfully created new 'PlayerSalaries' table.")


def create_player_skills_table(cursor: sqlite3.Cursor):
    """Creates the new PlayerSkills table."""
    cursor.execute("""
    CREATE TABLE PlayerSkills (
        player_skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        season_id TEXT NOT NULL,
        offensive_skill_rating REAL,
        defensive_skill_rating REAL,
        skill_metric_source TEXT NOT NULL,
        FOREIGN KEY (player_id) REFERENCES Players(player_id)
    );
    """)
    logger.info("Successfully created new 'PlayerSkills' table.")

 
def main():
    """Main function to connect to DB and run migrations."""
    conn = get_db_connection()
    if conn is not None:
        try:
            run_migrations(conn)
        except sqlite3.Error as e:
            logger.error(f"Database error during migration: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    main() 