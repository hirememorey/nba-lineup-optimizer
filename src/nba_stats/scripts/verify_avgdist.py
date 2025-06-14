import pandas as pd
from pathlib import Path
import sys

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from nba_stats.db.connection import get_db_connection
from nba_stats.scripts.common_utils import logger

def verify_avgdist(season):
    """Queries the PlayerSeasonRawStats table to verify AVGDIST data."""
    with get_db_connection() as conn:
        logger.info(f"Checking PlayerSeasonRawStats for AVGDIST in season {season}...")
        try:
            df = pd.read_sql_query(f"SELECT player_id, avg_shot_distance FROM PlayerSeasonRawStats WHERE season = '{season}'", conn)
            if df.empty:
                logger.info("No data found for the season in PlayerSeasonRawStats.")
            else:
                logger.info(f"Found {len(df)} rows in PlayerSeasonRawStats for season {season}.")
                non_zero_avgdist = (df['avg_shot_distance'] > 0).any()
                if non_zero_avgdist:
                    logger.info("Verification successful: Found non-zero AVGDIST data.")
                    logger.info("Sum of avg_shot_distance: " + str(df['avg_shot_distance'].sum()))
                else:
                    logger.warning("Verification failed: All AVGDIST values are zero or null.")
                    print(df['avg_shot_distance'].describe())
        except Exception as e:
            logger.error(f"An error occurred during verification: {e}")

def main():
    """Main function to run the script."""
    from nba_stats.config import settings
    import argparse

    parser = argparse.ArgumentParser(description="Verify AVGDIST data in the PlayerSeasonRawStats table.")
    parser.add_argument(
        "--season", 
        type=str, 
        default=settings.SEASON_ID,
        help=f"The season to verify data for (e.g., '{settings.SEASON_ID}')."
    )
    args = parser.parse_args()
    verify_avgdist(args.season)

if __name__ == "__main__":
    main() 