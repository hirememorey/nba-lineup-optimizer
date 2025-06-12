"""Script to populate the NBA games table for a given season."""

import logging
from datetime import datetime
from .common_utils import get_db_connection, get_nba_stats_client, logger
import sqlite3

def populate_games_for_season(season: str) -> None:
    """
    Populates the Games table with all games from the specified season.
    
    Args:
        season: The season to fetch games for (e.g., "2024-25").
    """
    logger.info(f"Starting game population for season {season}")
    conn = get_db_connection()
    if not conn:
        logger.error("Could not get database connection. Aborting game population.")
        return
        
    try:
        client = get_nba_stats_client()
        schedule_data = client.get_schedule(season)
        
        if not schedule_data:
            logger.warning(f"No schedule data returned for season {season}.")
            return

        games_to_insert = []
        for game in schedule_data:
            game_id = game.get('gameId')
            # The API returns two entries per game, one for each team. We only need one.
            if game_id and not any(g[0] == game_id for g in games_to_insert):
                games_to_insert.append((
                    game_id,
                    datetime.strptime(game['gameDate'], '%Y-%m-%d').strftime('%Y-%m-%d'),
                    season,
                    'Regular Season',  # Assuming regular season, as API doesn't specify
                    game.get('home_team_id'),  # Assuming client provides this
                    game.get('away_team_id')   # Assuming client provides this
                ))
        
        cursor = conn.cursor()
        for game_data in games_to_insert:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO Games (
                        game_id, game_date, season, season_type, home_team_id, away_team_id,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, game_data)
            except sqlite3.IntegrityError as e:
                logger.warning(f"Could not insert game {game_data[0]} (likely already exists): {e}")
            except sqlite3.Error as e:
                logger.error(f"Database error inserting game {game_data[0]}: {e}")

        conn.commit()
        logger.info(f"Successfully inserted or ignored {len(games_to_insert)} games for season {season}")
        
    except Exception as e:
        logger.error(f"An unexpected error occurred during game population for season {season}: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import argparse
    from ..config import settings
    parser = argparse.ArgumentParser(description="Populate the Games table for a specific NBA season.")
    parser.add_argument("--season", type=str, default=settings.SEASON_ID, help="The season to populate games for (e.g., '2024-25').")
    args = parser.parse_args()
    
    populate_games_for_season(season=args.season) 