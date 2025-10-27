"""Script to populate the PlayerSeasonDriveStats table."""

import sqlite3
import time
import random
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure project root is on sys.path so that relative imports work
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Local imports (after path fix)
from nba_stats.utils.common_utils import get_db_connection, get_nba_stats_client, logger
from nba_stats.config import settings

def _insert_drive_stats(conn: sqlite3.Connection, player_id: int, season: str, stats: Dict):
    """Inserts drive stats for a single player-season."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO PlayerSeasonDriveStats (
                player_id, season, team_id,
                drives, drive_fgm, drive_fga, drive_fg_pct, drive_pts,
                drive_passes, drive_ast, drive_tov
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            player_id, season, stats.get('TEAM_ID'),
            stats.get('DRIVES'), stats.get('DRIVE_FGM'), stats.get('DRIVE_FGA'),
            stats.get('DRIVE_FG_PCT'), stats.get('DRIVE_PTS'), stats.get('DRIVE_PASSES'),
            stats.get('DRIVE_AST'), stats.get('DRIVE_TOV')
        ))
    except sqlite3.Error as e:
        logger.error(f"DB error for player {player_id} drive stats: {e}")

def _fetch_drive_stats_task(player_info: Tuple[int, str], season: str) -> Dict:
    """Task to fetch drive stats for a single player."""
    player_id, player_name = player_info
    client = get_nba_stats_client()
    
    logger.info(f"Fetching drive stats for {player_name} (ID: {player_id})")
    
    try:
        time.sleep(random.uniform(settings.MIN_SLEEP, settings.MAX_SLEEP))
        drive_stats = client.get_player_drive_stats(player_id, season)
        
        if drive_stats and drive_stats.get('resultSets'):
            for result_set in drive_stats['resultSets']:
                if result_set.get('rowSet'):
                    headers = result_set['headers']
                    row = result_set['rowSet'][0]
                    # The API returns all stats with the same key prefix
                    return dict(zip(headers, row))
        return {}
    except Exception as e:
        logger.error(f"Exception in thread for player {player_id} drive stats: {e}")
        return {}

def populate_player_drive_stats(season_to_load: str):
    """Fetches and stores drive stats for all players using parallel requests."""
    logger.info(f"Starting player drive stats fetch for season {season_to_load}.")
    conn = get_db_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()
        # Only fetch players who were active during the target season
        cursor.execute("""
            SELECT DISTINCT p.player_id, p.player_name
            FROM Players p
            INNER JOIN PlayerSeasonRawStats rs ON p.player_id = rs.player_id
            WHERE rs.season = ? AND rs.minutes_played >= 100
        """, (season_to_load,))
        players_to_process = cursor.fetchall()

        if not players_to_process:
            logger.warning("No players in DB to fetch drive stats for.")
            return

        with ThreadPoolExecutor(max_workers=settings.MAX_WORKERS) as executor:
            future_to_player = {
                executor.submit(_fetch_drive_stats_task, player, season_to_load): player 
                for player in players_to_process
            }
            
            processed_count = 0
            for future in as_completed(future_to_player):
                stats = future.result()
                player_id = future_to_player[future][0]
                if stats:
                    _insert_drive_stats(conn, player_id, season_to_load, stats)
                    processed_count += 1
            
            conn.commit()
            logger.info(f"Finished processing. Stored drive stats for {processed_count} players.")

    except Exception as e:
        logger.error(f"An unexpected error occurred in drive stats population: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Populate player drive stats for a specific NBA season.")
    parser.add_argument("--season", type=str, default=settings.SEASON_ID, help="The season to populate stats for, e.g., '2024-25'.")
    args = parser.parse_args()

    populate_player_drive_stats(season_to_load=args.season) 