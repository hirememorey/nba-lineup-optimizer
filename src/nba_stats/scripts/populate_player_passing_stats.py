"""Fetch and store player passing stats for a given season."""

import sqlite3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from nba_stats.utils.common_utils import get_db_connection, get_nba_stats_client, logger

def populate_player_passing_stats(season: str):
    """
    Fetches league-wide player passing stats and stores them in the database.
    """
    logger.info(f"Fetching passing stats for season: {season}")
    conn = get_db_connection()
    if conn is None:
        return

    try:
        client = get_nba_stats_client()
        passing_data = client.get_league_player_tracking_stats(
            season=season,
            pt_measure_type='Passing'
        )
        
        if not passing_data or 'resultSets' not in passing_data or not passing_data['resultSets']:
            logger.warning("No passing data returned from API.")
            return
            
        result_data = passing_data['resultSets'][0]
        headers = result_data.get('headers', [])
        rows = result_data.get('rowSet', [])
        
        if not headers or not rows:
            logger.info(f"No player passing data to process for season {season}.")
            return

        header_map = {
            'PLAYER_ID': 'player_id',
            'TEAM_ID': 'team_id',
            'PASSES_MADE': 'passes_made',
            'PASSES_RECEIVED': 'passes_received',
            'AST': 'assists',
            'FT_AST': 'free_throw_assists',
            'SECONDARY_AST': 'secondary_assists',
            'POTENTIAL_AST': 'potential_assists',
            'AST_POINTS_CREATED': 'assist_points_created'
        }

        stats_to_insert = []
        for row in rows:
            record = dict(zip(headers, row))
            db_record = {
                db_col: record.get(api_key) 
                for api_key, db_col in header_map.items()
            }
            db_record['season'] = season
            if db_record.get('player_id'):
                stats_to_insert.append(db_record)

        if not stats_to_insert:
            logger.warning("No valid passing stats records to insert.")
            return

        columns = stats_to_insert[0].keys()
        placeholders = ', '.join(['?'] * len(columns))
        sql = f"INSERT OR REPLACE INTO PlayerSeasonPassingStats ({', '.join(columns)}) VALUES ({placeholders})"
        
        cursor = conn.cursor()
        cursor.executemany(sql, [tuple(d.values()) for d in stats_to_insert])
        conn.commit()
        logger.info(f"Successfully stored {cursor.rowcount} player passing stat records.")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    import argparse
    from ..config import settings
    
    parser = argparse.ArgumentParser(description="Populate player passing stats for a specific season.")
    parser.add_argument("--season", type=str, default=settings.SEASON_ID, help="The season to fetch data for (e.g., '2023-24').")
    args = parser.parse_args()
    
    populate_player_passing_stats(season=args.season) 