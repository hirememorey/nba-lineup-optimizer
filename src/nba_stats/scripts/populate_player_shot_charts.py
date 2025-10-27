"""
This script populates the PlayerShotChart table with granular shot data for each player.
"""
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from nba_stats.utils.common_utils import get_db_connection, get_nba_stats_client, logger
from nba_stats.config import settings

def _fetch_shot_chart_task(player_info: tuple, season: str) -> list:
    """Task to fetch shot chart data for a single player."""
    player_id, team_id = player_info
    client = get_nba_stats_client()
    logger.info(f"Fetching shot chart for Player ID: {player_id}, Team ID: {team_id}")
    
    try:
        shot_data = client.get_shot_chart_detail(
            player_id=player_id,
            team_id=team_id,
            season=season
        )
        if shot_data and 'resultSets' in shot_data and shot_data['resultSets']:
            rows = shot_data['resultSets'][0]['rowSet']
            headers = shot_data['resultSets'][0]['headers']
            return [dict(zip(headers, row)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching shot chart for player {player_id}: {e}", exc_info=True)
    
    return []

def _insert_shots_batch(conn: sqlite3.Connection, shots: list, season: str):
    """Inserts a batch of shot chart data into the database."""
    if not shots:
        return
        
    shots_to_insert = []
    for shot in shots:
        shots_to_insert.append((
            shot.get('PLAYER_ID'),
            shot.get('TEAM_ID'),
            shot.get('GAME_ID'),
            season,
            shot.get('ACTION_TYPE'),
            shot.get('EVENT_TYPE'),
            shot.get('SHOT_TYPE'),
            shot.get('SHOT_ZONE_BASIC'),
            shot.get('SHOT_ZONE_AREA'),
            shot.get('SHOT_ZONE_RANGE'),
            shot.get('SHOT_DISTANCE'),
            shot.get('LOC_X'),
            shot.get('LOC_Y'),
            shot.get('SHOT_MADE_FLAG')
        ))
    
    try:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT OR IGNORE INTO PlayerShotChart (
                player_id, team_id, game_id, season, action_type, event_type,
                shot_type, shot_zone_basic, shot_zone_area, shot_zone_range,
                shot_distance, loc_x, loc_y, shot_made_flag
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, shots_to_insert)
        conn.commit()
        logger.info(f"Successfully inserted/ignored {len(shots_to_insert)} shots.")
    except sqlite3.Error as e:
        logger.error(f"Database error during shot chart batch insertion: {e}")

def populate_player_shot_charts(season_to_load: str):
    """Fetches and stores shot chart data for all players in a season using parallel requests."""
    logger.info(f"Starting shot chart population for season {season_to_load}.")
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT player_id, team_id FROM PlayerSeasonRawStats WHERE season = ?", (season_to_load,))
        players = cursor.fetchall()
        logger.info(f"Found {len(players)} player-team combinations for season {season_to_load}.")

        with ThreadPoolExecutor(max_workers=settings.MAX_WORKERS) as executor:
            future_to_player = {
                executor.submit(_fetch_shot_chart_task, player, season_to_load): player 
                for player in players
            }
            
            for future in as_completed(future_to_player):
                shots = future.result()
                if shots:
                    _insert_shots_batch(conn, shots, season_to_load)
                
                # A small delay to be respectful to the API endpoint
                time.sleep(random.uniform(0.1, 0.3))

    except Exception as e:
        logger.error(f"An error occurred during shot chart population: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import argparse
    import random
    
    parser = argparse.ArgumentParser(description="Populate Player Shot Chart data for a given season.")
    parser.add_argument("--season", type=str, default=settings.SEASON_ID, help="The season to populate data for.")
    args = parser.parse_args()

    populate_player_shot_charts(season_to_load=args.season) 