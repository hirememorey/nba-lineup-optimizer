"""Main script for NBA stats application."""

import logging
import sys
from typing import List
from .api.fetcher import NBAStatsFetcher
from .models.player import Player
from .db.connection import DatabaseConnection
from .config.settings import SEASON_ID
from .db.init_db import init_database

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('nba_stats.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def save_players_to_db(players: List[Player], db: DatabaseConnection) -> None:
    """Save player data to the database.
    
    Args:
        players: List of Player objects to save
        db: Database connection
    """
    if not players:
        logging.warning("No players to save to database")
        return
    
    try:
        # Prepare the SQL query
        query = """
            INSERT OR REPLACE INTO PlayerSeasonRawStats (
                player_id,
                season,
                team_id,
                minutes_played,
                field_goal_percentage,
                three_point_percentage,
                free_throw_percentage,
                total_rebounds,
                assists,
                steals,
                blocks,
                points,
                plus_minus
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Prepare the data
        data = [
            (
                player.player_id,
                player.season_id,
                player.team_id,
                player.minutes_played,
                player.field_goal_percentage,
                player.three_point_percentage,
                player.free_throw_percentage,
                player.rebounds,
                player.assists,
                player.steals,
                player.blocks,
                player.points,
                player.plus_minus
            )
            for player in players
        ]
        
        # Execute the query
        db.execute_many(query, data)
        logging.info(f"Successfully saved {len(players)} players to database")
        
    except Exception as e:
        logging.error(f"Error saving players to database: {e}")
        raise

def main():
    """Main entry point for the application."""
    try:
        # Setup logging
        setup_logging()
        logging.info("Starting NBA stats data collection")
        
        # Initialize database
        init_database()
        
        # Initialize components
        fetcher = NBAStatsFetcher()
        db = DatabaseConnection()
        
        # Fetch player data
        logging.info(f"Fetching player data for season {SEASON_ID}")
        players = fetcher.fetch_all_players(SEASON_ID)
        
        if not players:
            logging.error("No player data was fetched")
            sys.exit(1)
        
        # Save data to database
        logging.info("Saving player data to database")
        save_players_to_db(players, db)
        
        logging.info("Data collection completed successfully")
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        sys.exit(1)
        
    finally:
        # Cleanup
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    main() 