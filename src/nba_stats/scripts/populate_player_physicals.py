"""
This script populates missing physical attributes (height, weight) and draft year
for players by calling the CommonPlayerInfo endpoint.
"""

import sqlite3
import time
import random

# Ensure project root is on sys.path so that relative imports work
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from nba_stats.scripts.common_utils import get_db_connection, get_nba_stats_client, logger, settings

def _add_draft_year_column_if_not_exists(conn: sqlite3.Connection):
    """Adds the draft_year column to the Players table if it doesn't exist."""
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(Players)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'draft_year' not in columns:
            cursor.execute("ALTER TABLE Players ADD COLUMN draft_year TEXT")
            logger.info("Column 'draft_year' added to table 'Players'.")
    except sqlite3.Error as e:
        logger.error(f"DB error when adding 'draft_year' column: {e}")

def _update_player_physicals(conn: sqlite3.Connection, player_id: int, height: str, weight: str, draft_year: str):
    """Updates a player's height, weight, and draft year in the database."""
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Players SET height = ?, weight = ?, draft_year = ? WHERE player_id = ?",
            (height, weight, draft_year, player_id)
        )
    except sqlite3.Error as e:
        logger.error(f"DB error updating player {player_id}: {e}")

def populate_player_physicals(season: str):
    """
    Fetches and stores physical attributes for players with missing data for a specific season.
    """
    logger.info(f"Starting population of missing player physical attributes for season {season}.")
    conn = get_db_connection()
    if conn is None:
        return

    try:
        # Step 1: Add draft_year column if it doesn't exist
        _add_draft_year_column_if_not_exists(conn)

        cursor = conn.cursor()
        # Get players who are in the season stats but are missing height
        cursor.execute("""
            SELECT DISTINCT p.player_id
            FROM Players p
            JOIN PlayerSeasonRawStats rs ON p.player_id = rs.player_id
            WHERE
                rs.season = ? AND
                rs.minutes_played >= ?
        """, (season, settings.MIN_MINUTES_THRESHOLD))
        players_to_update = [row[0] for row in cursor.fetchall()]

        if not players_to_update:
            logger.info("No relevant players with missing height found. Exiting.")
            return

        logger.info(f"Found {len(players_to_update)} relevant players with missing physical attributes. Starting fetch.")
        
        client = get_nba_stats_client()
        updated_count = 0

        for player_id in players_to_update:
            logger.info(f"Fetching common info for player_id: {player_id}")
            player_info_raw = client.get_common_player_info(player_id)
            
            if player_info_raw and 'resultSets' in player_info_raw and len(player_info_raw['resultSets']) > 0:
                player_info_data = player_info_raw['resultSets'][0]
                headers = [h.upper() for h in player_info_data['headers']]
                
                if player_info_data['rowSet']:
                    row = player_info_data['rowSet'][0]
                    player_data = dict(zip(headers, row))
                    
                    height = player_data.get('HEIGHT')
                    weight = player_data.get('WEIGHT')
                    draft_year = player_data.get('DRAFT_YEAR')

                    if height:
                        _update_player_physicals(conn, player_id, height, weight, draft_year)
                        updated_count += 1
                        logger.info(f"Updated player {player_id} with height {height}, weight {weight}, and draft year {draft_year}.")

            # Sleep to avoid rate limiting
            time.sleep(random.uniform(settings.MIN_SLEEP, settings.MAX_SLEEP))
        
        conn.commit()
        logger.info(f"Finished processing. Updated physicals for {updated_count} players.")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    populate_player_physicals(season=settings.SEASON_ID) 