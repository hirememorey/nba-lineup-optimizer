"""
This script executes the feature engineering and clustering steps for Phase 2
of the 'Algorithmic NBA Player Acquisition' project.
"""

import sqlite3
import pandas as pd
import logging
import sys
import os

# Add the project root to the Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(PROJECT_ROOT)

from src.nba_stats.db.database import get_db_connection
from src.nba_stats.config.settings import SEASON_ID, MIN_MINUTES_THRESHOLD

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_player_archetype_features(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Fetches and combines all necessary player features for clustering from the database.
    
    Args:
        conn: SQLite database connection object.
        
    Returns:
        A pandas DataFrame containing the combined features for all players.
    """
    logging.info("--- Fetching Player Features for Archetype Clustering ---")

    # Base query to get players who meet the minutes threshold
    query = f"""
    SELECT
        ps.player_id,
        p.player_name
    FROM
        PlayerSeasonRawStats ps
    JOIN
        Players p ON ps.player_id = p.player_id
    WHERE
        ps.season = '{SEASON_ID}'
        AND ps.minutes_played >= {MIN_MINUTES_THRESHOLD}
    """
    
    players_df = pd.read_sql(query, conn)
    logging.info(f"Found {len(players_df)} players who meet the {MIN_MINUTES_THRESHOLD} minute threshold.")
    
    # We will incrementally join all feature tables onto this base DataFrame.
    # This will be expanded in the next step.
    
    return players_df

def main():
    """Main function to execute Phase 2."""
    logging.info("--- Starting Phase 2: Feature Engineering & Clustering ---")
    
    conn = get_db_connection()
    if conn:
        try:
            player_features = get_player_archetype_features(conn)
            # Further steps (like clustering) will be added here.
        finally:
            conn.close()
            logging.info("Database connection closed.")

if __name__ == "__main__":
    main() 