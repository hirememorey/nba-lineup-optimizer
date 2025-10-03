"""
Fetches and stores player pull-up stats for a given season.
"""
import sqlite3
from .common_utils import get_db_connection, get_nba_stats_client, logger

def populate_player_pull_up_stats(season_to_load: str):
    """
    Fetches and stores all player pull-up stats for a given season.
    """
    logger.info(f"Starting player pull-up stats population for season {season_to_load}.")
    client = get_nba_stats_client()
    conn = get_db_connection()

    if not conn:
        return

    try:
        pull_up_data = client.get_league_player_tracking_stats(
            season=season_to_load,
            pt_measure_type='PullUpShot',
            per_mode='PerGame'
        )
        
        if not pull_up_data or 'resultSets' not in pull_up_data or not pull_up_data['resultSets']:
            logger.warning("No pull-up data returned from API.")
            return
            
        result_data = pull_up_data['resultSets'][0]
        headers = result_data.get('headers', [])
        rows = result_data.get('rowSet', [])
        
        if not rows or not headers:
            logger.info(f"No player pull-up data to process for season {season_to_load}.")
            return

        header_map = {
            'PLAYER_ID': 'player_id',
            'TEAM_ID': 'team_id',
            'GP': 'games_played',
            'W': 'wins',
            'L': 'losses',
            'MIN': 'minutes_played',
            'PULL_UP_FGM': 'pull_up_fgm',
            'PULL_UP_FGA': 'pull_up_fga',
            'PULL_UP_FG_PCT': 'pull_up_fg_pct',
            'PULL_UP_FG3M': 'pull_up_3pm',
            'PULL_UP_FG3A': 'pull_up_3pa',
            'PULL_UP_FG3_PCT': 'pull_up_3p_pct',
            'PULL_UP_EFG_PCT': 'pull_up_efg_pct',
            'PULL_UP_PTS': 'pull_up_pts',
        }
        
        db_headers = [header_map[h] for h in headers if h in header_map]
        db_headers.append('season')

        stats_to_insert = []
        for row in rows:
            row_dict = dict(zip(headers, row))
            db_record = {header_map[k]: v for k, v in row_dict.items() if k in header_map}
            db_record['season'] = season_to_load
            stats_to_insert.append(tuple(db_record.get(h) for h in db_headers))
            
        if stats_to_insert:
            cursor = conn.cursor()
            columns = ", ".join(db_headers)
            placeholders = ", ".join(['?'] * len(db_headers))
            query = f"INSERT OR REPLACE INTO PlayerSeasonPullUpStats ({columns}) VALUES ({placeholders})"
            
            cursor.executemany(query, stats_to_insert)
            conn.commit()
            logger.info(f"Successfully stored {cursor.rowcount} player pull-up stat records for {season_to_load}.")

    except sqlite3.Error as e:
        logger.error(f"Database error during pull-up stats insertion: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    current_season = "2024-25" # Updated to current season
    populate_player_pull_up_stats(current_season) 