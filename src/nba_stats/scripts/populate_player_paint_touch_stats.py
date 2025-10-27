"""
Fetches and stores player paint touch stats for a given season.
"""
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from nba_stats.utils.common_utils import get_db_connection, get_nba_stats_client, logger

def populate_player_paint_touch_stats(season_to_load: str):
    """
    Fetches and stores all player paint touch stats for a given season.
    """
    logger.info(f"Starting player paint touch stats population for season {season_to_load}.")
    client = get_nba_stats_client()
    conn = get_db_connection()

    if not conn:
        return

    try:
        paint_touch_data = client.get_league_player_tracking_stats(
            season=season_to_load,
            pt_measure_type='PaintTouch',
            per_mode='PerGame'
        )
        
        if not paint_touch_data or 'resultSets' not in paint_touch_data or not paint_touch_data['resultSets']:
            logger.warning("No paint touch data returned from API.")
            return
            
        result_data = paint_touch_data['resultSets'][0]
        headers = result_data.get('headers', [])
        rows = result_data.get('rowSet', [])
        
        if not rows or not headers:
            logger.info(f"No player paint touch data to process for season {season_to_load}.")
            return

        header_map = {
            'PLAYER_ID': 'player_id',
            'TEAM_ID': 'team_id',
            'GP': 'games_played',
            'MIN': 'minutes_played',
            'PAINT_TOUCHES': 'paint_touches',
            'PAINT_TOUCH_FGA': 'paint_touch_fga',
            'PAINT_TOUCH_FGM': 'paint_touch_fgm',
            'PAINT_TOUCH_FG_PCT': 'paint_touch_fg_pct',
            'PAINT_TOUCH_FTM': 'paint_touch_ftm',
            'PAINT_TOUCH_FTA': 'paint_touch_fta',
            'PAINT_TOUCH_FT_PCT': 'paint_touch_ft_pct',
            'PAINT_TOUCH_PASSES': 'paint_touch_passes',
            'PAINT_TOUCH_PASSES_PCT': 'paint_touch_pass_pct',
            'PAINT_TOUCH_AST': 'paint_touch_ast',
            'PAINT_TOUCH_AST_PCT': 'paint_touch_ast_pct',
            'PAINT_TOUCH_TOV': 'paint_touch_tov',
            'PAINT_TOUCH_TOV_PCT': 'paint_touch_tov_pct',
            'PAINT_TOUCH_FOULS': 'paint_touch_pf',
            'PAINT_TOUCH_FOULS_PCT': 'paint_touch_pf_pct',
            'PAINT_TOUCH_PTS': 'paint_touch_pts',
            'PAINT_TOUCH_PTS_PCT': 'paint_touch_pts_pct'
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
            query = f"INSERT OR REPLACE INTO PlayerSeasonPaintTouchStats ({columns}) VALUES ({placeholders})"
            
            cursor.executemany(query, stats_to_insert)
            conn.commit()
            logger.info(f"Successfully stored {cursor.rowcount} player paint touch stat records for {season_to_load}.")

    except sqlite3.Error as e:
        logger.error(f"Database error during paint touch stats insertion: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    # This is an example, the season will be passed by the orchestrator script
    current_season = "2024-25" 
    populate_player_paint_touch_stats(current_season) 