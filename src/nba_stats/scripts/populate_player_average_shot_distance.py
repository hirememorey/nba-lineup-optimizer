"""Script to populate player average shot distance."""

import sqlite3
import time
import random
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

from .common_utils import get_db_connection, get_nba_stats_client, logger

def get_players_for_season(conn: sqlite3.Connection, season: str) -> List[Tuple[int, int]]:
    """
    Fetches player_id and team_id for all players who have a record in PlayerSeasonRawStats for the given season.
    This ensures we only process players who have basic stats populated for that season.
    """
    cursor = conn.cursor()
    try:
        # Joining with Players table to get the most recent team_id for the player
        # Note: A player can play for multiple teams. We'll use the team_id from the Players table as a default.
        # The shot chart API requires a team_id.
        cursor.execute("""
            SELECT psr.player_id, p.team_id
            FROM PlayerSeasonRawStats psr
            JOIN Players p ON psr.player_id = p.player_id
            WHERE psr.season = ?
        """, (season,))
        players = cursor.fetchall()
        logger.info(f"Fetched {len(players)} players for season {season} to calculate avg shot distance.")
        return players
    except sqlite3.Error as e:
        logger.error(f"Database error fetching players for season {season}: {e}")
        return []

def calculate_and_update_avg_shot_distance(
    conn: sqlite3.Connection,
    client,
    player_id: int,
    team_id: int,
    season: str,
) -> None:
    """
    Fetches shot chart data for a player, calculates the average shot distance,
    and updates the PlayerSeasonRawStats table.
    """
    try:
        logger.info(f"Fetching shot chart details for Player ID: {player_id}, Season: {season}")
        shot_chart_data = client.get_shot_chart_detail(
            player_id=player_id,
            team_id=team_id,
            season=season,
        )
        print(shot_chart_data)

        if not shot_chart_data or "resultSets" not in shot_chart_data:
            logger.warning(f"No shot chart data returned for Player ID: {player_id}, Season: {season}")
            return

        result_sets = shot_chart_data["resultSets"]
        if not result_sets or not isinstance(result_sets, list) or len(result_sets) == 0:
            logger.warning(f"No resultSets found for Player ID: {player_id}, Season: {season}")
            return
        
        shot_details = result_sets[0]
        headers = shot_details.get("headers")
        row_set = shot_details.get("rowSet")

        if not row_set:
            logger.info(f"No shots found for Player ID: {player_id}, Season: {season}. Avg shot distance will be NULL.")
            avg_distance = None
        else:
            try:
                shot_distance_index = headers.index("SHOT_DISTANCE")
                shot_distances = [row[shot_distance_index] for row in row_set]
                
                if not shot_distances:
                    avg_distance = None
                else:
                    avg_distance = sum(shot_distances) / len(shot_distances)
                
                logger.info(f"Calculated avg shot distance for Player ID {player_id}: {avg_distance:.2f} ft")
            except (ValueError, IndexError) as e:
                logger.error(f"Could not find 'SHOT_DISTANCE' in headers for Player {player_id}: {e}")
                return
            except ZeroDivisionError:
                logger.warning(f"Zero division error for player {player_id}, setting avg_distance to None.")
                avg_distance = None


        cursor = conn.cursor()
        cursor.execute("""
            UPDATE PlayerSeasonRawStats
            SET avg_shot_distance = ?, updated_at = ?
            WHERE player_id = ? AND season = ?
        """, (avg_distance, datetime.now(), player_id, season))
        conn.commit()

        if cursor.rowcount == 0:
            logger.warning(f"No row found in PlayerSeasonRawStats for Player ID {player_id} and Season {season} to update.")
        else:
            logger.debug(f"Successfully updated avg_shot_distance for Player ID {player_id}, Season {season}")

    except Exception as e:
        logger.error(f"An unexpected error occurred for player {player_id}: {e}", exc_info=True)


def fetch_and_store_player_avg_shot_distance(season: str, conn: Optional[sqlite3.Connection] = None, client: Optional[Any] = None):
    """Orchestrates fetching and storing average shot distance for all players in a season."""
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True

    if client is None:
        client = get_nba_stats_client()

    if conn is None:
        logger.error("Could not establish database connection. Aborting.")
        return

    try:
        players_to_process = get_players_for_season(conn, season)
        
        for i, (player_id, team_id) in enumerate(players_to_process):
            calculate_and_update_avg_shot_distance(conn, client, player_id, team_id, season)
            
            # Add a delay to be respectful to the API
            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i+1}/{len(players_to_process)} players. Pausing briefly...")
                time.sleep(random.uniform(5, 10))
            else:
                time.sleep(random.uniform(1, 2))

        logger.info(f"Finished processing average shot distance for {len(players_to_process)} players for season {season}.")

    finally:
        if close_conn:
            conn.close()


def main(season_to_load: str):
    logger.info(f"Starting player average shot distance population for season: {season_to_load}")
    fetch_and_store_player_avg_shot_distance(season=season_to_load)
    logger.info("Player average shot distance population finished.")


if __name__ == "__main__":
    from ..config import settings
    import argparse

    parser = argparse.ArgumentParser(description="Populate player average shot distance for a specific NBA season.")
    parser.add_argument("--season", type=str, default=settings.SEASON_ID, help="The season to populate stats for, e.g., '2023-24'.")
    args = parser.parse_args()

    main(season_to_load=args.season) 