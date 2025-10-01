"""
Populate Player Anthropometric Data from NBA Draft Combine.

This script fetches wingspan and other physical measurements from the NBA Draft Combine
API and populates the PlayerAnthroStats table. The data is highly sparse, only available
for players who attended the draft combine.

The script is designed to be:
- Idempotent: Can be run multiple times safely
- Resilient: Handles API failures gracefully
- Dependency-aware: Checks for required upstream data
"""

import sys
import sqlite3
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from nba_stats.api.nba_stats_client import NBAStatsClient, UpstreamDataMissingError
from nba_stats.api.response_models import DraftCombineAnthroResponse
from nba_stats.scripts.common_utils import get_db_connection, logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _assert_upstream_dependencies(conn: sqlite3.Connection, season: str) -> None:
    """
    Assert that required upstream data exists before processing.
    
    Args:
        conn: Database connection
        season: Season being processed
        
    Raises:
        UpstreamDataMissingError: If required upstream data is missing
    """
    cursor = conn.cursor()
    
    # Check that Players table has been populated
    cursor.execute("SELECT COUNT(*) FROM Players")
    player_count = cursor.fetchone()[0]
    
    if player_count < 400:  # Reasonable threshold for NBA players
        raise UpstreamDataMissingError(
            f"Fatal: Cannot populate player anthropometric data. "
            f"The 'Players' table has only {player_count} records, which is below the minimum threshold of 400. "
            f"Please ensure the core player population script runs first in the population_config.json."
        )
    
    logger.info(f"✓ Upstream dependency check passed: {player_count} players found in database")


def _get_available_seasons() -> List[str]:
    """
    Get list of seasons with available draft combine data.
    
    Returns:
        List of season strings in YYYY-YY format
    """
    # Generate seasons from 2000 to current year
    current_year = datetime.now().year
    seasons = []
    
    for year in range(2000, current_year + 1):
        season = f"{year}-{str(year + 1)[-2:]}"
        seasons.append(season)
    
    return seasons


def _process_season_data(client: NBAStatsClient, conn: sqlite3.Connection, season: str) -> Dict[str, int]:
    """
    Process anthropometric data for a single season.
    
    Args:
        client: NBA Stats API client
        conn: Database connection
        season: Season to process
        
    Returns:
        Dictionary with processing statistics
    """
    cursor = conn.cursor()
    
    try:
        logger.info(f"Fetching anthropometric data for season: {season}")
        
        # Fetch data from API
        response = client.get_draft_combine_anthro(season)
        
        if not response or 'resultSets' not in response:
            logger.warning(f"No data available for season {season}")
            return {'processed': 0, 'skipped': 0, 'errors': 0}
        
        result_set = response['resultSets'][0]
        rows = result_set.get('rowSet', [])
        
        if not rows:
            logger.warning(f"Empty data for season {season}")
            return {'processed': 0, 'skipped': 0, 'errors': 0}
        
        processed = 0
        skipped = 0
        errors = 0
        
        for row in rows:
            try:
                # Extract data from row (based on API structure)
                player_id = row[1]  # PLAYER_ID
                wingspan = row[11] if len(row) > 11 and row[11] is not None else None
                height_wo_shoes = row[6] if len(row) > 6 and row[6] is not None else None
                height_w_shoes = row[8] if len(row) > 8 and row[8] is not None else None
                weight = row[10] if len(row) > 10 and row[10] is not None else None
                standing_reach = row[13] if len(row) > 13 and row[13] is not None else None
                body_fat_pct = row[15] if len(row) > 15 and row[15] is not None else None
                hand_length = row[16] if len(row) > 16 and row[16] is not None else None
                hand_width = row[17] if len(row) > 17 and row[17] is not None else None
                
                # Check if player exists in our database
                cursor.execute("SELECT player_id FROM Players WHERE player_id = ?", (player_id,))
                if not cursor.fetchone():
                    logger.debug(f"Player {player_id} not found in Players table, skipping")
                    skipped += 1
                    continue
                
                # Insert or update anthropometric data
                cursor.execute("""
                    INSERT OR REPLACE INTO PlayerAnthroStats (
                        player_id, wingspan_inches, height_wo_shoes_inches, height_w_shoes_inches,
                        weight_pounds, standing_reach_inches, body_fat_pct, hand_length_inches,
                        hand_width_inches, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    player_id, wingspan, height_wo_shoes, height_w_shoes,
                    weight, standing_reach, body_fat_pct, hand_length,
                    hand_width, datetime.now().isoformat()
                ))
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Error processing player data for season {season}: {e}")
                errors += 1
                continue
        
        conn.commit()
        logger.info(f"Season {season}: {processed} processed, {skipped} skipped, {errors} errors")
        
        return {'processed': processed, 'skipped': skipped, 'errors': errors}
        
    except Exception as e:
        logger.error(f"Error processing season {season}: {e}")
        return {'processed': 0, 'skipped': 0, 'errors': 1}


def populate_player_anthro(season_to_load: Optional[str] = None) -> None:
    """
    Main function to populate player anthropometric data.
    
    Args:
        season_to_load: Optional specific season to load. If None, loads all available seasons.
    """
    logger.info("Starting player anthropometric data population")
    
    # Get database connection
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to get database connection")
        return
    
    try:
        # Pre-run dependency check
        _assert_upstream_dependencies(conn, season_to_load or "all")
        
        # Initialize API client
        client = NBAStatsClient()
        
        # Determine which seasons to process
        if season_to_load:
            seasons_to_process = [season_to_load]
        else:
            seasons_to_process = _get_available_seasons()
        
        logger.info(f"Processing {len(seasons_to_process)} seasons")
        
        # Process each season
        total_stats = {'processed': 0, 'skipped': 0, 'errors': 0}
        
        for season in seasons_to_process:
            try:
                stats = _process_season_data(client, conn, season)
                for key in total_stats:
                    total_stats[key] += stats[key]
            except Exception as e:
                logger.error(f"Failed to process season {season}: {e}")
                total_stats['errors'] += 1
        
        # Final summary
        logger.info("=== ANTHROPOMETRIC DATA POPULATION COMPLETE ===")
        logger.info(f"Total processed: {total_stats['processed']}")
        logger.info(f"Total skipped: {total_stats['skipped']}")
        logger.info(f"Total errors: {total_stats['errors']}")
        
        # Verify final state
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM PlayerAnthroStats")
        final_count = cursor.fetchone()[0]
        logger.info(f"Total anthropometric records in database: {final_count}")
        
    except UpstreamDataMissingError as e:
        logger.error(f"Dependency check failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during population: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Populate player anthropometric data")
    parser.add_argument("--season", type=str, help="Specific season to load (e.g., '2024-25')")
    args = parser.parse_args()
    
    populate_player_anthro(season_to_load=args.season)
