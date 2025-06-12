"""
This script populates the PlayerSeasonSkill table with data from a manually downloaded CSV file.
"""
import pandas as pd
import sqlite3
from pathlib import Path
from .common_utils import get_db_connection, logger

def populate_player_skill(season_to_load: str) -> None:
    """
    Populates the PlayerSeasonSkill table from a DARKO CSV file for a given season.
    """
    logger.info(f"Starting to populate PlayerSeasonSkill for season {season_to_load}.")
    conn = get_db_connection()
    if not conn:
        return

    try:
        csv_path = Path(f"data/darko_dpm_{season_to_load}.csv")
        if not csv_path.exists():
            logger.error(f"DARKO CSV file not found at {csv_path}. Cannot populate player skill ratings.")
            logger.warning("Please download the required file from https://apanalytics.shinyapps.io/DARKO/")
            return

        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} rows from {csv_path}.")

        # Prepare DataFrame for insertion
        df.rename(columns={'nba_id': 'player_id', 'Player': 'player_name', 'O-DPM': 'offensive_darko', 'D-DPM': 'defensive_darko', 'DPM': 'darko'}, inplace=True)
        df['season'] = season_to_load
        
        # Ensure player_id is a nullable integer type to handle non-numeric values
        df['player_id'] = pd.to_numeric(df['player_id'], errors='coerce')
        df.dropna(subset=['player_id'], inplace=True)
        df['player_id'] = df['player_id'].astype('Int64')

        # Filter for columns that exist in the database table
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(PlayerSeasonSkill)")
        db_columns = {col[1] for col in cursor.fetchall()}
        
        df_columns = [col for col in df.columns if col in db_columns]
        skill_df = df[df_columns]

        # Use executemany for efficient batch insertion
        placeholders = ', '.join(['?'] * len(df_columns))
        sql = f"INSERT OR REPLACE INTO PlayerSeasonSkill ({', '.join(df_columns)}) VALUES ({placeholders})"
        
        cursor.executemany(sql, skill_df.to_records(index=False).tolist())
        conn.commit()
        logger.info(f"Successfully populated PlayerSeasonSkill for {cursor.rowcount} players.")

    except Exception as e:
        logger.error(f"An error occurred during PlayerSeasonSkill population: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import argparse
    from ..config import settings
    
    parser = argparse.ArgumentParser(description="Populate PlayerSeasonSkill table from a CSV file.")
    parser.add_argument("--season", type=str, default=settings.SEASON_ID, help="The season to load data for.")
    args = parser.parse_args()
    
    populate_player_skill(season_to_load=args.season) 