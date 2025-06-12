"""Script to populate the PlayerSeasonHustleStats table with league-wide hustle stats."""

import sqlite3
from .common_utils import get_db_connection, get_nba_stats_client, logger

def _insert_hustle_stats(conn: sqlite3.Connection, season: str, stats_data: dict):
    """Inserts a single player's hustle stats for a season."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO PlayerSeasonHustleStats (
                player_id, season, team_id,
                contested_shots, deflections, loose_balls_recovered, charges_drawn,
                screen_assists, box_outs
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            stats_data.get('PLAYER_ID'),
            season,
            stats_data.get('TEAM_ID'),
            stats_data.get('CONTESTED_SHOTS'),
            stats_data.get('DEFLECTIONS'),
            stats_data.get('LOOSE_BALLS_RECOVERED'),
            stats_data.get('CHARGES_DRAWN'),
            stats_data.get('SCREEN_ASSISTS'),
            stats_data.get('BOX_OUTS')
        ))
    except sqlite3.Error as e:
        logger.error(f"DB error for player {stats_data.get('PLAYER_ID')} hustle stats: {e}")

def populate_player_hustle_stats(season_to_load: str):
    """Fetches and stores league-wide hustle stats for a given season."""
    logger.info(f"Starting league hustle stats fetch for season {season_to_load}")
    conn = get_db_connection()
    if conn is None:
        return

    try:
        client = get_nba_stats_client()
        hustle_stats_response = client.get_league_hustle_stats(season=season_to_load)

        if not hustle_stats_response or "resultSets" not in hustle_stats_response:
            logger.warning(f"Failed to fetch or parse league hustle stats for {season_to_load}.")
            return

        result_sets = hustle_stats_response["resultSets"]
        if not result_sets:
            logger.warning("No resultSets found in hustle stats API response.")
            return

        hustle_data = result_sets[0]
        headers = hustle_data.get("headers")
        row_set = hustle_data.get("rowSet")

        if not headers or not row_set:
            logger.warning("No data found in hustle stats resultSet.")
            return

        processed_count = 0
        for row in row_set:
            stats_data = dict(zip(headers, row))
            if stats_data.get('PLAYER_ID'):
                _insert_hustle_stats(conn, season_to_load, stats_data)
                processed_count += 1
        
        conn.commit()
        logger.info(f"Finished processing. Stored hustle stats for {processed_count} players.")

    except Exception as e:
        logger.error(f"An unexpected error occurred in hustle stats population: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import argparse
    from ..config import settings
    parser = argparse.ArgumentParser(description="Populate player hustle stats for a specific NBA season.")
    parser.add_argument("--season", type=str, default=settings.SEASON_ID, help="The season to populate stats for, e.g., '2024-25'.")
    args = parser.parse_args()

    populate_player_hustle_stats(season_to_load=args.season) 