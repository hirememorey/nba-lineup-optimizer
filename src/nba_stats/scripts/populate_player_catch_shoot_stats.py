"""
Fetches and stores player catch & shoot stats for a given season.
"""
import sqlite3
from .common_utils import get_db_connection, get_nba_stats_client, logger

def populate_player_catch_shoot_stats(season_to_load: str):
    """
    Fetches and stores all player catch & shoot stats for a given season.
    """
    logger.info(f"Starting player catch & shoot stats population for season {season_to_load}.")
    client = get_nba_stats_client()
    conn = get_db_connection()

    if not conn:
        return

    try:
        catch_shoot_data = client.get_league_player_tracking_stats(
            season=season_to_load,
            pt_measure_type='CatchShoot',
            per_mode='PerGame'
        )
        
        if not catch_shoot_data or 'resultSets' not in catch_shoot_data or not catch_shoot_data['resultSets']:
            logger.warning("No catch & shoot data returned from API.")
            return
            
        result_data = catch_shoot_data['resultSets'][0]
        headers = result_data.get('headers', [])
        rows = result_data.get('rowSet', [])
        
        if not rows or not headers:
            logger.info(f"No player catch & shoot data to process for season {season_to_load}.")
            return

        # Map API headers to DB columns (snake_case)
        header_map = {
            'PLAYER_ID': 'player_id',
            'TEAM_ID': 'team_id',
            'GP': 'games_played',
            'W': 'wins',
            'L': 'losses',
            'MIN': 'minutes_played',
            'CATCH_SHOOT_FGM': 'catch_shoot_fgm',
            'CATCH_SHOOT_FGA': 'catch_shoot_fga',
            'CATCH_SHOOT_FG_PCT': 'catch_shoot_fg_pct',
            'CATCH_SHOOT_FG3M': 'catch_shoot_3pm',
            'CATCH_SHOOT_FG3A': 'catch_shoot_3pa',
            'CATCH_SHOOT_FG3_PCT': 'catch_shoot_3p_pct',
            'CATCH_SHOOT_EFG_PCT': 'catch_shoot_efg_pct',
            'CATCH_SHOOT_PTS': 'catch_shoot_pts',
        }
        
        # Filter and rename headers for DB insertion
        db_headers = [header_map[h] for h in headers if h in header_map]
        db_headers.append('season')

        stats_to_insert = []
        for row in rows:
            row_dict = dict(zip(headers, row))
            
            # Build record for DB insertion
            db_record = {header_map[k]: v for k, v in row_dict.items() if k in header_map}
            db_record['season'] = season_to_load
            stats_to_insert.append(tuple(db_record.get(h) for h in db_headers))
            
        if stats_to_insert:
            cursor = conn.cursor()
            columns = ", ".join(db_headers)
            placeholders = ", ".join(['?'] * len(db_headers))
            query = f"INSERT OR REPLACE INTO PlayerSeasonCatchAndShootStats ({columns}) VALUES ({placeholders})"
            
            cursor.executemany(query, stats_to_insert)
            conn.commit()
            logger.info(f"Successfully stored {cursor.rowcount} player catch & shoot stat records for {season_to_load}.")

    except sqlite3.Error as e:
        logger.error(f"Database error during catch & shoot stats insertion: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    current_season = "2023-24" # Example season
    populate_player_catch_shoot_stats(current_season) 