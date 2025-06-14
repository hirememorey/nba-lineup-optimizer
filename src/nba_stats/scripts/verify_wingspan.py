"""Script to verify wingspan data in the Players table."""

import pandas as pd
from pathlib import Path
import sys

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from nba_stats.db.connection import get_db_connection
from nba_stats.scripts.common_utils import logger

def verify_wingspan(season):
    """
    Queries the Players table for players active in a given season
    and verifies their WINGSPAN data.
    """
    with get_db_connection() as conn:
        logger.info(f"Checking Players table for WINGSPAN for players active in season {season}...")
        try:
            # Join Players with PlayerSeasonRawStats to get players active in the specified season
            query = f"""
                SELECT
                    p.player_id,
                    p.player_name,
                    p.wingspan
                FROM Players p
                JOIN PlayerSeasonRawStats psrs ON p.player_id = psrs.player_id
                WHERE psrs.season = '{season}'
            """
            df = pd.read_sql_query(query, conn)
            
            if df.empty:
                logger.info("No active players found for the season in PlayerSeasonRawStats.")
                return

            logger.info(f"Found {len(df)} active players for season {season}.")
            
            # Check for null or zero wingspans
            missing_wingspan_df = df[df['wingspan'].isnull() | (df['wingspan'] == 0)]
            num_missing = len(missing_wingspan_df)

            if num_missing == 0:
                logger.info("Verification successful: All active players have a wingspan value.")
            else:
                logger.warning(f"Verification found {num_missing} active players with a missing or zero wingspan.")
                # Log a few examples
                logger.info("Examples of players with missing wingspan:")
                logger.info(missing_wingspan_df.head())

        except Exception as e:
            logger.error(f"An error occurred during verification: {e}", exc_info=True)

def main():
    """Main function to run the script."""
    from nba_stats.config import settings
    import argparse

    parser = argparse.ArgumentParser(description="Verify WINGSPAN data in the Players table for active players in a season.")
    parser.add_argument(
        "--season", 
        type=str, 
        default=settings.SEASON_ID,
        help=f"The season to verify data for (e.g., '{settings.SEASON_ID}')."
    )
    args = parser.parse_args()
    verify_wingspan(args.season)

if __name__ == "__main__":
    main() 