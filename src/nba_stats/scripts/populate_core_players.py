"""Script to populate the Players table with core player information."""

import sqlite3
from datetime import datetime

from .common_utils import get_db_connection, get_nba_stats_client, logger
from pydantic import ValidationError
from ..models.player import Player

def _insert_player(conn: sqlite3.Connection, player: Player) -> None:
    """Insert or update a single player in the Players table."""
    try:
        cursor = conn.cursor()
        name_parts = player.player_name.split(maxsplit=1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        cursor.execute("""
            INSERT INTO Players (
                player_id, player_name, first_name, last_name, team_id, position,
                height, weight, birth_date, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(player_id) DO UPDATE SET
                team_id=excluded.team_id,
                position=excluded.position,
                updated_at=excluded.updated_at,
                height=CASE WHEN excluded.height IS NOT NULL THEN excluded.height ELSE Players.height END,
                weight=CASE WHEN excluded.weight IS NOT NULL THEN excluded.weight ELSE Players.weight END
        """, (
            player.player_id,
            player.player_name,
            first_name,
            last_name,
            player.team_id,
            player.position,
            player.height,
            player.weight,
            player.birth_date,
            datetime.now()
        ))
    except sqlite3.Error as e:
        # Log error but don't re-raise, to allow the main loop to continue
        logger.error(f"Database error inserting player {player.player_name}: {e}")

def populate_all_players_data(season_to_load: str) -> None:
    """
    Fetches all players for a given season, validates their data,
    and stores them in the database.
    """
    logger.info(f"Starting core player population process for season: {season_to_load}")
    conn = get_db_connection()
    if conn is None:
        logger.error("Could not get database connection. Aborting player population.")
        return

    client = get_nba_stats_client()
    
    try:
        all_players_raw = client.get_all_players(season=season_to_load)
        if not all_players_raw or 'resultSets' not in all_players_raw or not all_players_raw['resultSets']:
            logger.warning("No player data found in the API response.")
            return

        player_data = all_players_raw['resultSets'][0]
        headers = [header.upper() for header in player_data['headers']]
        player_rows = player_data['rowSet']
        
        players_processed_count = 0
        for player_row in player_rows:
            player_data_dict = dict(zip(headers, player_row))
            
            try:
                # Add season_id to the dictionary for validation with the Pydantic model
                player_data_dict['season_id'] = season_to_load
                
                player = Player.model_validate(player_data_dict)
                
                # Insert player into the database
                _insert_player(conn, player)
                players_processed_count += 1
            
            except ValidationError as e:
                player_id = player_data_dict.get('PERSON_ID', 'N/A')
                logger.warning(f"Skipping player_id {player_id} due to validation error: {e}")

        conn.commit()
        logger.info(f"Successfully processed and committed {players_processed_count} players for season {season_to_load}.")

    except Exception as e:
        logger.error(f"An unexpected error occurred during player population: {e}", exc_info=True)
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import argparse
    from ..config import settings
    
    parser = argparse.ArgumentParser(description="Populate the Players table for a specific season.")
    parser.add_argument("--season", type=str, default=settings.SEASON_ID, help="The season to fetch player data for (e.g., '2023-24').")
    args = parser.parse_args()

    populate_all_players_data(season_to_load=args.season) 