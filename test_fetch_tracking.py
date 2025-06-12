import logging
import time
from src.nba_stats.api.data_fetcher import NBAStatsFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fetch_tracking_test.log"),
        logging.StreamHandler()
    ]
)

# Configuration
DB_PATH = 'nba_data.db'  # Ensure this matches your database path
SEASON_TO_FETCH = "2023-24" # Season to fetch data for
PER_MODE_TO_FETCH = "PerGame" # "PerGame" or "Totals"

def run_test():
    logger = logging.getLogger(__name__)
    logger.info("Starting player tracking stats fetch test...")

    fetcher = NBAStatsFetcher(db_path=DB_PATH)

    try:
        logger.info(f"Fetching player tracking stats for season: {SEASON_TO_FETCH}, mode: {PER_MODE_TO_FETCH}")
        fetcher.fetch_player_tracking_stats(
            season=SEASON_TO_FETCH,
            per_mode=PER_MODE_TO_FETCH
        )
        logger.info("Player tracking stats fetch process initiated.")
        
        # The actual writing to DB happens in a separate thread.
        # We need to give it some time to complete.
        # In a real application, you might have a more robust way to check completion.
        logger.info("Waiting for DB writer thread to process queued items (approx 30 seconds)...")
        time.sleep(30) # Adjust this time based on expected data volume and processing speed
        
        logger.info("Assumed DB processing is complete.")
        logger.info("Test finished. Please check the database and 'fetch_tracking_test.log' for details.")

    except Exception as e:
        logger.error(f"An error occurred during the test: {e}", exc_info=True)

if __name__ == '__main__':
    run_test() 