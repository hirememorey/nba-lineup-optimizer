"""
Populate tracking stats for historical seasons (2018-19, 2020-21, 2021-22).

This script corrects the data quality issue where tracking stats have dummy
values by properly collecting them from the NBA API.
"""

import sqlite3
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.nba_stats.utils.common_utils import get_db_connection, logger
from src.nba_stats.scripts.populate_player_drive_stats import populate_player_drive_stats
from src.nba_stats.scripts.populate_player_tracking_touches_stats import populate_player_tracking_touches_stats
from src.nba_stats.scripts.populate_player_elbow_touch_stats import populate_player_elbow_touch_stats
from src.nba_stats.scripts.populate_player_paint_touch_stats import populate_player_paint_touch_stats
from src.nba_stats.scripts.populate_player_post_up_stats import populate_player_post_up_stats
from src.nba_stats.scripts.populate_player_catch_shoot_stats import populate_player_catch_shoot_stats
from src.nba_stats.scripts.populate_player_passing_stats import populate_player_passing_stats
from src.nba_stats.scripts.populate_player_pull_up_stats import populate_player_pull_up_stats
from src.nba_stats.scripts.populate_player_rebounding_stats import populate_player_rebounding_stats

HISTORICAL_SEASONS = ["2018-19", "2020-21", "2021-22"]

# Tracking stat populate functions (in order of dependency)
POPULATE_FUNCTIONS = [
    ("Drive Stats", populate_player_drive_stats),
    ("Tracking Touches Stats", populate_player_tracking_touches_stats),
    ("Elbow Touch Stats", populate_player_elbow_touch_stats),
    ("Paint Touch Stats", populate_player_paint_touch_stats),
    ("Post-Up Stats", populate_player_post_up_stats),
    ("Catch & Shoot Stats", populate_player_catch_shoot_stats),
    ("Passing Stats", populate_player_passing_stats),
    ("Pull-Up Stats", populate_player_pull_up_stats),
    ("Rebounding Stats", populate_player_rebounding_stats),
]


def clear_dummy_tracking_stats(season: str):
    """Clear dummy tracking stats data for a season."""
    logger.info(f"Clearing dummy tracking stats for {season}")
    conn = get_db_connection()
    
    if conn is None:
        return
    
    try:
        cursor = conn.cursor()
        
        # Delete all tracking stats for the season
        tables = [
            "PlayerSeasonDriveStats",
            "PlayerSeasonTrackingTouchesStats",
            "PlayerSeasonElbowTouchStats",
            "PlayerSeasonPaintTouchStats",
            "PlayerSeasonPostUpStats",
            "PlayerSeasonCatchAndShootStats",
            "PlayerSeasonPassingStats",
            "PlayerSeasonPullUpStats",
            "PlayerSeasonReboundingStats",
        ]
        
        for table in tables:
            try:
                cursor.execute(f"DELETE FROM {table} WHERE season = ?", (season,))
                deleted = cursor.rowcount
                if deleted > 0:
                    logger.info(f"  Deleted {deleted} dummy rows from {table}")
            except Exception as e:
                logger.warning(f"  Could not delete from {table}: {e}")
        
        conn.commit()
        logger.info(f"Cleared dummy tracking stats for {season}")
        
    finally:
        if conn:
            conn.close()


def populate_season_tracking_stats(season: str):
    """Populate all tracking stats for a specific season."""
    logger.info(f"\n{'=' * 80}")
    logger.info(f"POPULATING TRACKING STATS FOR {season}")
    logger.info(f"{'=' * 80}")
    
    # Clear dummy data first
    clear_dummy_tracking_stats(season)
    
    # Populate each tracking stat type
    for stat_name, populate_func in POPULATE_FUNCTIONS:
        logger.info(f"\nPopulating {stat_name} for {season}...")
        try:
            populate_func(season)
            logger.info(f"✅ {stat_name} populated successfully")
        except Exception as e:
            logger.error(f"❌ Failed to populate {stat_name}: {e}")
    
    logger.info(f"\n✅ Tracking stats collection complete for {season}")


def main():
    """Main function to populate tracking stats for all historical seasons."""
    logger.info("=" * 80)
    logger.info("POPULATING HISTORICAL TRACKING STATS")
    logger.info("Fixing dummy data by collecting real tracking stats from NBA API")
    logger.info("=" * 80)
    
    for season in HISTORICAL_SEASONS:
        populate_season_tracking_stats(season)
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ ALL HISTORICAL TRACKING STATS POPULATED")
    logger.info("Next steps:")
    logger.info("1. Re-run generate_archetype_features.py for each season")
    logger.info("2. Re-run assign_historical_archetypes_pooled.py")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

