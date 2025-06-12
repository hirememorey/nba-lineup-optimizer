"""Fetch and store player rebounding stats for a given season."""

import sqlite3
from .common_utils import get_db_connection, get_nba_stats_client, logger

def populate_player_rebounding_stats(season: str):
    """
    Fetches league-wide player rebounding stats and stores them in the database.
    """
    logger.info(f"Fetching rebounding stats for season: {season}")
    conn = get_db_connection()
    if conn is None:
        return

    try:
        client = get_nba_stats_client()
        rebounding_data = client.get_league_player_tracking_stats(
            season=season,
            pt_measure_type='Rebounding'
        )
        
        if not rebounding_data or 'resultSets' not in rebounding_data or not rebounding_data['resultSets']:
            logger.warning("No rebounding data returned from API.")
            return
            
        result_data = rebounding_data['resultSets'][0]
        headers = result_data.get('headers', [])
        rows = result_data.get('rowSet', [])
        
        if not headers or not rows:
            logger.info(f"No player rebounding data to process for season {season}.")
            return

        header_map = {
            'PLAYER_ID': 'player_id',
            'TEAM_ID': 'team_id',
            'OREB': 'rebounds_offensive',
            'DREB': 'rebounds_defensive',
            'REB': 'rebounds_total',
            'REB_CHANCES': 'rebound_chances_total',
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
            logger.warning("No valid rebounding stats records to insert.")
            return

        columns = stats_to_insert[0].keys()
        placeholders = ', '.join(['?'] * len(columns))
        sql = f"INSERT OR REPLACE INTO PlayerSeasonReboundingStats ({', '.join(columns)}) VALUES ({placeholders})"
        
        cursor = conn.cursor()
        cursor.executemany(sql, [tuple(d.values()) for d in stats_to_insert])
        conn.commit()
        logger.info(f"Successfully stored {cursor.rowcount} player rebounding stat records.")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    import argparse
    from ..config import settings
    
    parser = argparse.ArgumentParser(description="Populate player rebounding stats for a specific season.")
    parser.add_argument("--season", type=str, default=settings.SEASON_ID, help="The season to fetch data for (e.g., '2023-24').")
    args = parser.parse_args()
    
    populate_player_rebounding_stats(season=args.season) 