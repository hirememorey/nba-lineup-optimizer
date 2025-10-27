"""
Populate Player Shot Metrics from existing shot chart data.

This script calculates the 5 derivable shot metrics (AVGDIST, Zto3r, THto10r, TENto16r, SIXTto3PTr)
from the existing PlayerShotChart table and stores them in a dedicated PlayerShotMetrics table.

The script is designed to be:
- Idempotent: Can be run multiple times safely
- Resilient: Handles missing data gracefully
- Dependency-aware: Checks for required upstream data
- Performance-optimized: Uses efficient SQL queries
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

from nba_stats.utils.common_utils import get_db_connection, logger
from nba_stats.api.nba_stats_client import UpstreamDataMissingError

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
    
    # Check that PlayerShotChart table has been populated
    cursor.execute("SELECT COUNT(*) FROM PlayerShotChart WHERE season = ?", (season,))
    shot_count = cursor.fetchone()[0]
    
    if shot_count < 1000:  # Reasonable threshold for shot data
        raise UpstreamDataMissingError(
            f"Fatal: Cannot populate shot metrics. "
            f"The 'PlayerShotChart' table has only {shot_count} shots for season {season}, "
            f"which is below the minimum threshold of 1000. "
            f"Please ensure the shot chart population script runs first."
        )
    
    logger.info(f"✓ Upstream dependency check passed: {shot_count} shots found for season {season}")


def _create_shot_metrics_table(conn: sqlite3.Connection) -> None:
    """
    Create the PlayerShotMetrics table if it doesn't exist.
    
    Args:
        conn: Database connection
    """
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PlayerShotMetrics (
            player_id INTEGER,
            season TEXT,
            avgdist REAL,
            zto3r REAL,
            thto10r REAL,
            tento16r REAL,
            sixtto3ptr REAL,
            total_shots INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (player_id, season),
            FOREIGN KEY (player_id) REFERENCES Players(player_id)
        )
    """)
    conn.commit()
    logger.info("✓ PlayerShotMetrics table ensured")


def _calculate_shot_metrics_for_player(conn: sqlite3.Connection, player_id: int, season: str) -> Optional[Dict[str, Any]]:
    """
    Calculate shot metrics for a single player from their shot chart data.
    
    Args:
        conn: Database connection
        player_id: Player ID
        season: Season
        
    Returns:
        Dictionary with calculated metrics or None if no data
    """
    cursor = conn.cursor()
    
    # Get all shots for this player in this season
    cursor.execute("""
        SELECT shot_distance, shot_zone_range, shot_made_flag
        FROM PlayerShotChart 
        WHERE player_id = ? AND season = ?
    """, (player_id, season))
    
    shots = cursor.fetchall()
    
    if not shots:
        return None
    
    # Calculate metrics
    total_shots = len(shots)
    
    # 1. AVGDIST - Average shot distance
    distances = [shot[0] for shot in shots if shot[0] is not None]
    avgdist = sum(distances) / len(distances) if distances else 0.0
    
    # 2-5. Zone-based metrics
    zone_counts = {
        'Less than 8 ft.': 0,
        '8-16 ft.': 0,
        '16-24 ft.': 0,
        '24+ ft.': 0
    }
    
    for shot in shots:
        zone = shot[1]  # shot_zone_range
        if zone in zone_counts:
            zone_counts[zone] += 1
    
    # Calculate ratios
    zto3r = zone_counts['Less than 8 ft.'] / total_shots
    thto10r = zone_counts['8-16 ft.'] / total_shots
    tento16r = zone_counts['16-24 ft.'] / total_shots
    sixtto3ptr = zone_counts['24+ ft.'] / total_shots
    
    return {
        'player_id': player_id,
        'season': season,
        'avgdist': round(avgdist, 2),
        'zto3r': round(zto3r, 4),
        'thto10r': round(thto10r, 4),
        'tento16r': round(tento16r, 4),
        'sixtto3ptr': round(sixtto3ptr, 4),
        'total_shots': total_shots
    }


def _process_season_metrics(conn: sqlite3.Connection, season: str) -> Dict[str, int]:
    """
    Process shot metrics for all players in a season.
    
    Args:
        conn: Database connection
        season: Season to process
        
    Returns:
        Dictionary with processing statistics
    """
    cursor = conn.cursor()
    
    # Get all players who have shot data for this season
    cursor.execute("""
        SELECT DISTINCT player_id 
        FROM PlayerShotChart 
        WHERE season = ?
        ORDER BY player_id
    """, (season,))
    
    player_ids = [row[0] for row in cursor.fetchall()]
    logger.info(f"Processing shot metrics for {len(player_ids)} players in season {season}")
    
    processed = 0
    skipped = 0
    errors = 0
    
    for player_id in player_ids:
        try:
            metrics = _calculate_shot_metrics_for_player(conn, player_id, season)
            
            if metrics:
                # Insert or update the metrics
                cursor.execute("""
                    INSERT OR REPLACE INTO PlayerShotMetrics (
                        player_id, season, avgdist, zto3r, thto10r, tento16r, sixtto3ptr, total_shots, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics['player_id'],
                    metrics['season'],
                    metrics['avgdist'],
                    metrics['zto3r'],
                    metrics['thto10r'],
                    metrics['tento16r'],
                    metrics['sixtto3ptr'],
                    metrics['total_shots'],
                    datetime.now().isoformat()
                ))
                
                processed += 1
                
                if processed % 50 == 0:
                    logger.info(f"Processed {processed}/{len(player_ids)} players...")
            else:
                skipped += 1
                
        except Exception as e:
            logger.error(f"Error processing player {player_id} for season {season}: {e}")
            errors += 1
            continue
    
    conn.commit()
    logger.info(f"Season {season}: {processed} processed, {skipped} skipped, {errors} errors")
    
    return {'processed': processed, 'skipped': skipped, 'errors': errors}


def populate_player_shot_metrics(season_to_load: Optional[str] = None) -> None:
    """
    Main function to populate player shot metrics.
    
    Args:
        season_to_load: Optional specific season to load. If None, loads all available seasons.
    """
    logger.info("Starting player shot metrics population")
    
    # Get database connection
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to get database connection")
        return
    
    try:
        # Create the metrics table
        _create_shot_metrics_table(conn)
        
        # Determine which seasons to process
        if season_to_load:
            seasons_to_process = [season_to_load]
        else:
            # Get all seasons with shot data
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT season FROM PlayerShotChart ORDER BY season")
            seasons_to_process = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"Processing {len(seasons_to_process)} seasons")
        
        # Process each season
        total_stats = {'processed': 0, 'skipped': 0, 'errors': 0}
        
        for season in seasons_to_process:
            try:
                # Pre-run dependency check for this season
                _assert_upstream_dependencies(conn, season)
                
                # Process the season
                stats = _process_season_metrics(conn, season)
                for key in total_stats:
                    total_stats[key] += stats[key]
                    
            except UpstreamDataMissingError as e:
                logger.error(f"Dependency check failed for season {season}: {e}")
                total_stats['errors'] += 1
            except Exception as e:
                logger.error(f"Failed to process season {season}: {e}")
                total_stats['errors'] += 1
        
        # Final summary
        logger.info("=== SHOT METRICS POPULATION COMPLETE ===")
        logger.info(f"Total processed: {total_stats['processed']}")
        logger.info(f"Total skipped: {total_stats['skipped']}")
        logger.info(f"Total errors: {total_stats['errors']}")
        
        # Verify final state
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM PlayerShotMetrics")
        final_count = cursor.fetchone()[0]
        logger.info(f"Total shot metrics records in database: {final_count}")
        
    except Exception as e:
        logger.error(f"Unexpected error during population: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Populate player shot metrics")
    parser.add_argument("--season", type=str, help="Specific season to load (e.g., '2024-25')")
    args = parser.parse_args()
    
    populate_player_shot_metrics(season_to_load=args.season)
