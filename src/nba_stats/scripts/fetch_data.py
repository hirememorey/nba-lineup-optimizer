"""Script to fetch NBA stats data."""

import logging
import os
from pathlib import Path

from nba_stats.api.data_fetcher import NBAStatsFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Main function to run the NBA stats data fetcher."""
    try:
        # Get the directory containing this script
        script_dir = Path(__file__).parent.parent.parent.parent
        
        # Construct path to database
        db_path = script_dir / "nba_lineup_data.db"
        
        logging.info(f"Using database at: {db_path}")
        
        # Initialize fetcher
        fetcher = NBAStatsFetcher(str(db_path))
        
        # Fetch data for both Base and Advanced stats
        for measure_type in ["Base", "Advanced"]:
            logging.info(f"Fetching {measure_type} stats")
            fetcher.fetch_all_data(measure_type=measure_type, limit=100)
            
        logging.info("Data fetch completed successfully")
        
    except Exception as e:
        logging.error(f"Error during data fetch: {e}")
        raise

if __name__ == "__main__":
    main() 