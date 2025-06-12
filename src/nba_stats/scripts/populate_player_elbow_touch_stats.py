"""
Fetches and stores player elbow touch stats for a given season.
"""
import sqlite3
from .common_utils import get_db_connection, get_nba_stats_client, logger

def populate_player_elbow_touch_stats(season_to_load: str):
    """
    Fetches and stores all player elbow touch stats for a given season.
    """
    logger.info(f"Starting player elbow touch stats population for season {season_to_load}.")
    client = get_nba_stats_client()
    conn = get_db_connection()

    if not conn:
        return

    try:
        elbow_touch_data = client.get_league_player_tracking_stats(
            season=season_to_load,
            pt_measure_type='ElbowTouch',
            per_mode='PerGame'
        )
        
        if not elbow_touch_data or 'resultSets' not in elbow_touch_data or not elbow_touch_data['resultSets']:
            logger.warning("No elbow touch data returned from API.")
            return
            
        result_data = elbow_touch_data['resultSets'][0]
        headers = result_data.get('headers', [])
        rows = result_data.get('rowSet', [])
        
        if not rows or not headers:
            logger.info(f"No player elbow touch data to process for season {season_to_load}.")
            return

        header_map = {
            'PLAYER_ID': 'player_id',
            'TEAM_ID': 'team_id',
            'GP': 'games_played',
            'MIN': 'minutes_played',
            'ELBOW_TOUCHES': 'elbow_touches',
            'ELBOW_TOUCH_FGA': 'elbow_touch_fga',
            'ELBOW_TOUCH_FGM': 'elbow_touch_fgm',
            'ELBOW_TOUCH_FG_PCT': 'elbow_touch_fg_pct',
            'ELBOW_TOUCH_FTM': 'elbow_touch_ftm',
            'ELBOW_TOUCH_FTA': 'elbow_touch_fta',
            'ELBOW_TOUCH_FT_PCT': 'elbow_touch_ft_pct',
            'ELBOW_TOUCH_PASSES': 'elbow_touch_passes',
            'ELBOW_TOUCH_PASSES_PCT': 'elbow_touch_pass_pct',
            'ELBOW_TOUCH_AST': 'elbow_touch_ast',
            'ELBOW_TOUCH_AST_PCT': 'elbow_touch_ast_pct',
            'ELBOW_TOUCH_TOV': 'elbow_touch_tov',
            'ELBOW_TOUCH_TOV_PCT': 'elbow_touch_tov_pct',
            'ELBOW_TOUCH_FOULS': 'elbow_touch_pf',
            'ELBOW_TOUCH_FOULS_PCT': 'elbow_touch_pf_pct',
            'ELBOW_TOUCH_PTS': 'elbow_touch_pts',
            'ELBOW_TOUCH_PTS_PCT': 'elbow_touch_pts_pct'
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
            query = f"INSERT OR REPLACE INTO PlayerSeasonElbowTouchStats ({columns}) VALUES ({placeholders})"
            
            cursor.executemany(query, stats_to_insert)
            conn.commit()
            logger.info(f"Successfully stored {cursor.rowcount} player elbow touch stat records for {season_to_load}.")

    except sqlite3.Error as e:
        logger.error(f"Database error during elbow touch stats insertion: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    # This is an example, the season will be passed by the orchestrator script
    current_season = "2023-24" 
    populate_player_elbow_touch_stats(current_season) 