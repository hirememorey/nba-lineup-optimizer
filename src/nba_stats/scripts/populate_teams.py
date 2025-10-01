"""
Script to populate the Teams table with all active NBA teams.
"""
import sqlite3
from common_utils import get_db_connection, get_nba_stats_client, logger

def populate_teams_data():
    """
    Fetches all NBA teams from the API and stores them in the Teams table.
    This function is designed to be called by the main orchestration script.
    """
    logger.info("Starting team population process...")
    conn = get_db_connection()
    if conn is None:
        logger.error("Could not establish database connection. Aborting team population.")
        return

    try:
        # The nba_api `teams.get_teams()` call does not require a client instance.
        # It's a static method call that fetches a list of all teams.
        from nba_api.stats.static import teams
        teams_list = teams.get_teams()
        
        if not teams_list:
            logger.warning("No teams data was returned from the API.")
            return

        teams_to_insert = [
            (
                team['id'],
                team['full_name'],
                team['abbreviation'],
                team['nickname'],
                team['city'],
                team.get('conference', 'N/A'),  # Add conference and division with defaults
                team.get('division', 'N/A')
            ) for team in teams_list
        ]

        cursor = conn.cursor()
        cursor.executemany(
            "INSERT OR REPLACE INTO Teams (team_id, team_name, team_abbreviation, team_code, team_city, team_conference, team_division) VALUES (?, ?, ?, ?, ?, ?, ?)",
            teams_to_insert
        )
        conn.commit()
        
        logger.info(f"Team population process finished. Inserted or replaced {cursor.rowcount} teams.")

    except sqlite3.Error as e:
        logger.error(f"A database error occurred during team population: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred during team population: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Allows for direct execution of this script for testing or standalone use.
    logger.info("Running populate_teams.py as a standalone script.")
    populate_teams_data() 