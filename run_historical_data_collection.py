#!/usr/bin/env python3
"""
Historical Data Collection Script for NBA Lineup Optimizer

This script collects historical player data for 2018-19, 2020-21, and 2021-22 seasons
to enable the evolution from an explanatory model to a predictive model.

Based on the post-mortem insights and first-principles approach.
"""

import sys
import os
import sqlite3
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nba_stats.api.nba_stats_client import NBAStatsClient
from nba_stats.models.player import Player

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("historical_data_collection.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HistoricalDataCollector:
    """Main class for collecting historical NBA data."""
    
    def __init__(self, db_path: str = "src/nba_stats/db/nba_stats.db"):
        self.db_path = db_path
        self.client = NBAStatsClient()
        self.seasons = ["2018-19", "2020-21", "2021-22"]
        
    def get_db_connection(self):
        """Get database connection."""
        if not Path(self.db_path).exists():
            logger.error(f"Database not found at {self.db_path}")
            return None
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    
    def check_existing_data(self, season: str) -> Dict[str, int]:
        """Check what data already exists for a season."""
        conn = self.get_db_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # Check games data
            cursor.execute("SELECT COUNT(*) FROM Games WHERE season = ?", (season,))
            games_count = cursor.fetchone()[0]
            
            # Check players data (approximate by checking for star players)
            cursor.execute("""
                SELECT COUNT(*) FROM Players 
                WHERE player_id IN (2544, 201939, 201142, 201935, 203999)
            """)
            players_count = cursor.fetchone()[0]
            
            # Check player season stats
            cursor.execute("SELECT COUNT(*) FROM PlayerSeasonRawStats WHERE season = ?", (season,))
            stats_count = cursor.fetchone()[0]
            
            # Check DARKO data
            cursor.execute("SELECT COUNT(*) FROM PlayerSeasonSkill WHERE season = ?", (season,))
            darko_count = cursor.fetchone()[0]
            
            return {
                'games': games_count,
                'players': players_count,
                'stats': stats_count,
                'darko': darko_count
            }
            
        except Exception as e:
            logger.error(f"Error checking existing data for {season}: {e}")
            return {}
        finally:
            conn.close()
    
    def populate_games(self, season: str) -> bool:
        """Populate games data for a season."""
        logger.info(f"Populating games data for {season}")
        
        try:
            # Use the existing populate_games.py script
            import subprocess
            result = subprocess.run([
                sys.executable, "populate_games.py", "--season", season
            ], capture_output=True, text=True, cwd=Path(__file__).parent)
            
            if result.returncode == 0:
                logger.info(f"✅ Games data populated for {season}")
                return True
            else:
                logger.error(f"❌ Failed to populate games for {season}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error populating games for {season}: {e}")
            return False
    
    def populate_players(self, season: str) -> bool:
        """Populate core players data for a season."""
        logger.info(f"Populating players data for {season}")
        
        conn = self.get_db_connection()
        if not conn:
            return False
        
        try:
            # Fetch players from API
            all_players_raw = self.client.get_all_players(season=season)
            
            if not all_players_raw or 'resultSets' not in all_players_raw or not all_players_raw['resultSets']:
                logger.warning(f"No player data found for {season}")
                return False
            
            player_data = all_players_raw['resultSets'][0]
            headers = [header.upper() for header in player_data['headers']]
            player_rows = player_data['rowSet']
            
            logger.info(f"Found {len(player_rows)} players for {season}")
            
            cursor = conn.cursor()
            players_processed = 0
            
            for player_row in player_rows:
                try:
                    player_data_dict = dict(zip(headers, player_row))
                    player_data_dict['season_id'] = season
                    
                    player = Player.model_validate(player_data_dict)
                    
                    # Insert player
                    name_parts = player.player_name.split(maxsplit=1)
                    first_name = name_parts[0]
                    last_name = name_parts[1] if len(name_parts) > 1 else ''
                    
                    cursor.execute("""
                        INSERT OR IGNORE INTO Players (
                            player_id, player_name, first_name, last_name, team_id, position,
                            height, weight, birth_date, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        datetime.now().isoformat()
                    ))
                    
                    players_processed += 1
                    
                    if players_processed % 100 == 0:
                        logger.info(f"Processed {players_processed} players...")
                        
                except Exception as e:
                    logger.warning(f"Error processing player: {e}")
                    continue
            
            conn.commit()
            logger.info(f"✅ Processed {players_processed} players for {season}")
            return True
            
        except Exception as e:
            logger.error(f"Error populating players for {season}: {e}")
            return False
        finally:
            conn.close()
    
    def populate_player_stats(self, season: str) -> bool:
        """Populate player season stats for a season."""
        logger.info(f"Populating player stats for {season}")
        
        # For now, we'll create a simple implementation
        # In a full implementation, this would use the existing populate_player_season_stats.py
        logger.warning(f"Player stats population for {season} not yet implemented")
        logger.warning("This requires refactoring the existing populate_player_season_stats.py script")
        return False
    
    def populate_darko_data(self, season: str) -> bool:
        """Populate DARKO data for a season."""
        logger.info(f"Populating DARKO data for {season}")
        
        try:
            # Use the fixed populate_darko_data_fixed.py script
            import subprocess
            result = subprocess.run([
                sys.executable, "populate_darko_data_fixed.py", "--season", season
            ], capture_output=True, text=True, cwd=Path(__file__).parent)
            
            if result.returncode == 0:
                logger.info(f"✅ DARKO data populated for {season}")
                return True
            else:
                logger.error(f"❌ Failed to populate DARKO for {season}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error populating DARKO for {season}: {e}")
            return False
    
    def collect_season_data(self, season: str, force: bool = False) -> bool:
        """Collect all data for a single season."""
        logger.info(f"Starting data collection for {season}")
        
        # Check existing data
        existing_data = self.check_existing_data(season)
        logger.info(f"Existing data for {season}: {existing_data}")
        
        success = True
        
        # Populate games data
        if existing_data.get('games', 0) == 0 or force:
            if not self.populate_games(season):
                success = False
        else:
            logger.info(f"Games data already exists for {season}, skipping")
        
        # Populate players data
        if existing_data.get('players', 0) == 0 or force:
            if not self.populate_players(season):
                success = False
        else:
            logger.info(f"Players data already exists for {season}, skipping")
        
        # Populate player stats (not yet implemented)
        if existing_data.get('stats', 0) == 0 or force:
            if not self.populate_player_stats(season):
                logger.warning(f"Player stats collection failed for {season}")
                success = False
        else:
            logger.info(f"Player stats already exist for {season}, skipping")
        
        # Populate DARKO data
        if existing_data.get('darko', 0) == 0 or force:
            if not self.populate_darko_data(season):
                success = False
        else:
            logger.info(f"DARKO data already exists for {season}, skipping")
        
        # Final verification
        final_data = self.check_existing_data(season)
        logger.info(f"Final data for {season}: {final_data}")
        
        return success
    
    def collect_all_historical_data(self, force: bool = False) -> bool:
        """Collect data for all historical seasons."""
        logger.info("Starting historical data collection for all seasons")
        
        overall_success = True
        
        for season in self.seasons:
            logger.info(f"\n{'='*50}")
            logger.info(f"Processing season: {season}")
            logger.info(f"{'='*50}")
            
            if not self.collect_season_data(season, force):
                logger.error(f"Failed to collect data for {season}")
                overall_success = False
            else:
                logger.info(f"✅ Successfully collected data for {season}")
        
        logger.info(f"\n{'='*50}")
        logger.info("Historical data collection complete")
        logger.info(f"{'='*50}")
        
        if overall_success:
            logger.info("✅ All seasons processed successfully!")
        else:
            logger.warning("⚠️ Some seasons had issues. Check the logs for details.")
        
        return overall_success

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Collect historical NBA data for predictive modeling")
    parser.add_argument("--season", help="Specific season to process (e.g., 2018-19)")
    parser.add_argument("--force", action="store_true", help="Force re-collection even if data exists")
    parser.add_argument("--check-only", action="store_true", help="Only check existing data, don't collect")
    
    args = parser.parse_args()
    
    collector = HistoricalDataCollector()
    
    if args.check_only:
        # Just check what data exists
        logger.info("Checking existing data...")
        for season in collector.seasons:
            data = collector.check_existing_data(season)
            logger.info(f"{season}: {data}")
        return
    
    if args.season:
        # Process specific season
        if args.season not in collector.seasons:
            logger.error(f"Invalid season: {args.season}. Valid seasons: {collector.seasons}")
            sys.exit(1)
        
        success = collector.collect_season_data(args.season, args.force)
        if not success:
            sys.exit(1)
    else:
        # Process all seasons
        success = collector.collect_all_historical_data(args.force)
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()
