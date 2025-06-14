import pandas as pd
from pathlib import Path
import sys

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from nba_stats.db.connection import get_db_connection
from nba_stats.scripts.common_utils import logger

def verify_features(season):
    """Queries the PlayerArchetypeFeatures table to verify data."""
    with get_db_connection() as conn:
        logger.info(f"Checking PlayerArchetypeFeatures for season {season}...")
        try:
            df = pd.read_sql_query(f"SELECT AVGDIST, AVGFGATTEMPTEDAGAINSTPERGAME FROM PlayerArchetypeFeatures WHERE season = '{season}'", conn)
            if df.empty:
                logger.info("No data found for the season in PlayerArchetypeFeatures.")
            else:
                logger.info(f"Found {len(df)} rows in PlayerArchetypeFeatures for season {season}.")
                
                avgdist_ok = (df['AVGDIST'] > 0).any()
                avgfg_ok = (df['AVGFGATTEMPTEDAGAINSTPERGAME'] > 0).any()

                if avgdist_ok and avgfg_ok:
                    logger.info("Verification successful: Found non-zero data for both AVGDIST and AVGFGATTEMPTEDAGAINSTPERGAME.")
                    logger.info(f"AVGDIST sum: {df['AVGDIST'].sum()}")
                    logger.info(f"AVGFGATTEMPTEDAGAINSTPERGAME sum: {df['AVGFGATTEMPTEDAGAINSTPERGAME'].sum()}")
                else:
                    if not avgdist_ok:
                        logger.warning("Verification failed: All AVGDIST values are zero or null.")
                    if not avgfg_ok:
                        logger.warning("Verification failed: All AVGFGATTEMPTEDAGAINSTPERGAME values are zero or null.")

        except Exception as e:
            logger.error(f"An error occurred during verification: {e}")

def main():
    """Main function to run the script."""
    from nba_stats.config import settings
    import argparse

    parser = argparse.ArgumentParser(description="Verify data in the PlayerArchetypeFeatures table.")
    parser.add_argument(
        "--season", 
        type=str, 
        default=settings.SEASON_ID,
        help=f"The season to verify data for (e.g., '{settings.SEASON_ID}')."
    )
    args = parser.parse_args()
    verify_features(args.season)

if __name__ == "__main__":
    main() 