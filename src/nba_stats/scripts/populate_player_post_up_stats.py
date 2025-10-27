"""
Fetches and stores player post-up stats for a given season.
"""
import sqlite3
import logging
from pathlib import Path
import sys

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from nba_stats.utils.common_utils import get_db_connection, get_nba_stats_client, logger

def populate_player_post_up_stats(season_to_load: str):
    """
    Fetches and stores all player post-up stats for a given season.
    """
    logger.info(f"Starting player post-up stats population for season {season_to_load}.")
    client = get_nba_stats_client()
    conn = get_db_connection()

    if not conn:
        return

    try:
        post_up_data = client.get_league_player_tracking_stats(
            season=season_to_load,
            pt_measure_type='PostTouch',
            per_mode='PerGame'
        )
        
        if not post_up_data or 'resultSets' not in post_up_data or not post_up_data['resultSets']:
            logger.warning("No post-up data returned from API.")
            return
            
        result_data = post_up_data['resultSets'][0]
        headers = result_data.get('headers', [])
        rows = result_data.get('rowSet', [])
        
        if not rows or not headers:
            logger.info(f"No player post-up data to process for season {season_to_load}.")
            return

        header_map = {
            'PLAYER_ID': 'player_id',
            'TEAM_ID': 'team_id',
            'GP': 'games_played',
            'MIN': 'minutes_played',
            'POST_TOUCHES': 'possessions',
            'POST_TOUCH_PTS': 'points',
            'POST_TOUCH_FGM': 'fgm',
            'POST_TOUCH_FGA': 'fga',
            'POST_TOUCH_FG_PCT': 'fg_pct',
            'POST_TOUCH_FT_PCT': 'ft_frequency_pct',
            'POST_TOUCH_TOV_PCT': 'tov_frequency_pct',
            'POST_TOUCH_FOULS_PCT': 'sf_frequency_pct',
            'POST_TOUCH_PASSES_PCT': 'pass_frequency_pct',
            'POST_TOUCH_AST': 'assists',
            'POST_TOUCH_AST_PCT': 'assist_pct',
            'POST_TOUCH_PTS_PCT': 'points_per_possession'
        }
        
        db_headers = [header_map[h] for h in headers if h in header_map]
        if 'TOUCHES' in headers and 'POST_TOUCHES' in headers:
            db_headers.append('frequency_pct')
        db_headers.append('season')

        stats_to_insert = []
        for row in rows:
            row_dict = dict(zip(headers, row))
            db_record = {header_map[k]: v for k, v in row_dict.items() if k in header_map}
            
            total_touches = row_dict.get('TOUCHES', 0)
            post_touches = row_dict.get('POST_TOUCHES', 0)
            db_record['frequency_pct'] = post_touches / total_touches if total_touches > 0 else 0
            
            db_record['season'] = season_to_load
            stats_to_insert.append(tuple(db_record.get(h) for h in db_headers))
            
        if stats_to_insert:
            cursor = conn.cursor()
            columns = ", ".join(db_headers)
            placeholders = ", ".join(['?'] * len(db_headers))
            query = f"INSERT OR REPLACE INTO PlayerSeasonPostUpStats ({columns}) VALUES ({placeholders})"
            
            cursor.executemany(query, stats_to_insert)
            conn.commit()
            logger.info(f"Successfully stored {cursor.rowcount} player post-up stat records for {season_to_load}.")

    except sqlite3.Error as e:
        logger.error(f"Database error during post-up stats insertion: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    import argparse
    from src.nba_stats.config import settings

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    parser = argparse.ArgumentParser(description="Populate player post-up stats for a given season.")
    parser.add_argument(
        "--season",
        type=str,
        default=settings.SEASON_ID,
        help=f"The season to populate stats for (e.g., '{settings.SEASON_ID}')."
    )
    args = parser.parse_args()

    populate_player_post_up_stats(args.season) 