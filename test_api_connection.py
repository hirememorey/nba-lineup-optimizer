import logging
import json
from src.nba_stats.api.nba_stats_client import NBAStatsClient

# Configure basic logging to see the client's output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_schedule_fetch():
    """
    Isolates the API call to fetch the league schedule to diagnose
    the hanging issue.
    """
    target_season = "2024-25"
    logging.info(f"Attempting to fetch schedule for season: {target_season}")

    try:
        client = NBAStatsClient()
        schedule_data = client.get_schedule(season=target_season)

        if schedule_data:
            logging.info(f"Successfully fetched schedule data. Found {len(schedule_data)} game entries.")
            # Print the first game as a sample
            print("\n--- Sample Game Data ---")
            print(json.dumps(schedule_data[0], indent=2))
            print("------------------------\n")
        else:
            logging.warning("API call succeeded but returned no data.")

    except Exception as e:
        logging.error(f"An exception occurred during the API call: {e}", exc_info=True)

if __name__ == "__main__":
    test_schedule_fetch()
