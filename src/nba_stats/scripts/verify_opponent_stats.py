import sqlite3
import pandas as pd
from pathlib import Path
import sys

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from nba_stats.db.connection import get_db_connection
from nba_stats.scripts.common_utils import logger

def verify_data(season):
    """Queries the PlayerSeasonOpponentShootingStats table to verify data insertion."""
    with get_db_connection() as conn:
        logger.info(f"Checking PlayerSeasonOpponentShootingStats for season {season}...")
        try:
            df = pd.read_sql_query(f"SELECT * FROM PlayerSeasonOpponentShootingStats WHERE season = '{season}'", conn)
            if df.empty:
                logger.info("No data found for the season in PlayerSeasonOpponentShootingStats.")
            else:
                logger.info(f"Found {len(df)} rows in PlayerSeasonOpponentShootingStats for season {season}.")
                logger.info("First 5 rows:")
                print(df.head())
                # Check if the relevant columns have non-zero values
                fga_cols = [
                    'opp_fga_lt_5ft',
                    'opp_fga_5_9ft',
                    'opp_fga_10_14ft',
                    'opp_fga_15_19ft',
                    'opp_fga_20_24ft',
                    'opp_fga_25_29ft'
                ]
                # check that the fga_cols exist before trying to sum them
                existing_fga_cols = [col for col in fga_cols if col in df.columns]
                if not existing_fga_cols:
                    logger.warning("None of the FGA columns were found in the dataframe.")
                    return
                    
                logger.info("Checking sums of FGA columns:")
                print(df[existing_fga_cols].sum())
                
                non_zero_fga_sum = (df[existing_fga_cols].sum() > 0).any()
                if non_zero_fga_sum:
                    logger.info("Verification successful: Found non-zero opponent FGA data.")
                else:
                    logger.warning("Verification failed: All opponent FGA columns are zero.")


        except Exception as e:
            logger.error(f"An error occurred during verification: {e}")

def main():
    """Main function to run the script."""
    from nba_stats.config import settings
    import argparse

    parser = argparse.ArgumentParser(description="Verify data in the PlayerSeasonOpponentShootingStats table.")
    parser.add_argument(
        "--season", 
        type=str, 
        default=settings.SEASON_ID,
        help=f"The season to verify data for (e.g., '{settings.SEASON_ID}')."
    )
    args = parser.parse_args()
    verify_data(args.season)


if __name__ == "__main__":
    main() 