"""Script to populate PlayerSeasonTrackingTouchesStats with various player tracking touch-based data."""

import sqlite3
import time
import random
from typing import Dict, List, Any
from .common_utils import get_db_connection, get_nba_stats_client, logger, settings

PT_MEASURE_TYPES = ["Possessions", "ElbowTouch", "PaintTouch", "PostTouch"]

def _fetch_tracking_data_for_type(client, season: str, measure_type: str) -> List[Dict]:
    """Fetches player tracking data for a single measure type."""
    logger.info(f"Fetching {measure_type} data for {season} season.")
    try:
        response = client.get_league_player_tracking_stats(season=season, pt_measure_type=measure_type)
        if response and response.get("resultSets"):
            data = response["resultSets"][0]
            headers = data.get("headers")
            rows = data.get("rowSet")
            if headers and rows:
                return [dict(zip(headers, row)) for row in rows]
    except Exception as e:
        logger.error(f"Failed to fetch {measure_type} data: {e}", exc_info=True)
    return []

def _aggregate_all_touch_stats(client, season: str) -> Dict[int, Dict]:
    """Fetches and aggregates all touch-related stats for all players."""
    aggregated_data = {}

    for measure_type in PT_MEASURE_TYPES:
        data_rows = _fetch_tracking_data_for_type(client, season, measure_type)
        for row in data_rows:
            player_id = row.get("PLAYER_ID")
            if not player_id:
                continue
            
            if player_id not in aggregated_data:
                aggregated_data[player_id] = {'player_id': player_id}
            
            # Merge the new data into the aggregated record
            aggregated_data[player_id].update(row)
        
        time.sleep(random.uniform(settings.MIN_SLEEP, settings.MAX_SLEEP))

    return aggregated_data

def _insert_touch_stats_batch(conn: sqlite3.Connection, season: str, all_player_stats: Dict[int, Dict]):
    """Inserts the aggregated touch stats into the database in a single transaction."""
    cursor = conn.cursor()
    cursor.execute("SELECT player_id FROM Players")
    db_player_ids = {row[0] for row in cursor.fetchall()}

    stats_to_insert = []
    
    header_map = {
        'TEAM_ID': 'team_id',
        'TOUCHES': 'touches',
        'FRONT_CT_TOUCHES': 'front_ct_touches',
        'TIME_OF_POSS': 'time_of_poss',
        'AVG_SEC_PER_TOUCH': 'avg_sec_per_touch',
        'AVG_DRIB_PER_TOUCH': 'avg_drib_per_touch',
        'ELBOW_TOUCHES': 'elbow_touches',
        'POST_TOUCHES': 'post_touches',
        'PAINT_TOUCHES': 'paint_touches'
    }

    for player_id, stats in all_player_stats.items():
        if player_id in db_player_ids:
            db_record = {
                'player_id': player_id,
                'season': season,
                'team_id': stats.get('TEAM_ID')
            }
            for api_key, db_col in header_map.items():
                if api_key != 'TEAM_ID':
                    db_record[db_col] = stats.get(api_key)
            
            stats_to_insert.append(db_record)

    if not stats_to_insert:
        logger.warning("No valid tracking touch stats to insert.")
        return

    columns = stats_to_insert[0].keys()
    placeholders = ', '.join(['?'] * len(columns))
    sql = f"INSERT OR REPLACE INTO PlayerSeasonTrackingTouchesStats ({', '.join(columns)}) VALUES ({placeholders})"
    
    try:
        cursor.executemany(sql, [tuple(d.values()) for d in stats_to_insert])
        conn.commit()
        logger.info(f"Successfully stored {cursor.rowcount} player tracking touch stat records.")
    except sqlite3.Error as e:
        logger.error(f"Database error during touch stats batch insertion: {e}")

def populate_player_tracking_touches_stats(season: str):
    """Fetches, aggregates, and stores all player tracking touches stats for a season."""
    logger.info(f"Starting player tracking touches stats population for season: {season}")
    conn = get_db_connection()
    if conn is None:
        return

    try:
        client = get_nba_stats_client()
        aggregated_stats = _aggregate_all_touch_stats(client, season)
        if aggregated_stats:
            _insert_touch_stats_batch(conn, season, aggregated_stats)
    except Exception as e:
        logger.error(f"An unexpected error occurred during the main process: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Populate player tracking touches stats for a specific NBA season.")
    parser.add_argument("--season", type=str, default=settings.SEASON_ID, help="The season to populate stats for (e.g., '2024-25').")
    args = parser.parse_args()
    
    populate_player_tracking_touches_stats(season=args.season) 