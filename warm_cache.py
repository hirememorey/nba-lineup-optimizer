import logging
from pathlib import Path
import sys
import time

# Add project root to path to allow importing from src
sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.nba_stats.api.nba_stats_client import NBAStatsClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WarmCacheManager:
    """Manages warming the local API cache with representative data."""

    def __init__(self, season: str = "2024-25"):
        self.season = season
        self.client = NBAStatsClient()
        # Define a set of representative, league-wide endpoints to cache
        self.endpoints_to_warm = [
            {"method": "get_all_teams", "params": {"season": self.season}},
            {"method": "get_all_players", "params": {"season": self.season}},
            {"method": "get_league_player_advanced_stats", "params": {"season": self.season}},
            {"method": "get_league_hustle_stats", "params": {"season": self.season}},
            {"method": "get_league_player_shot_locations", "params": {"season": self.season}},
        ]

    def warm_cache(self) -> dict:
        """
        Iterates through the defined endpoints and calls them to populate the cache.
        """
        logger.info(f"Starting cache warming process for season {self.season}...")
        successful_requests = 0
        failed_requests = 0

        for endpoint in self.endpoints_to_warm:
            method_name = endpoint["method"]
            params = endpoint["params"]
            method_to_call = getattr(self.client, method_name, None)

            if method_to_call:
                try:
                    logger.info(f"Warming endpoint: {method_name} with params {params}...")
                    response = method_to_call(**params)
                    if response:
                        logger.info(f"Successfully cached {method_name}.")
                        successful_requests += 1
                    else:
                        logger.warning(f"Endpoint {method_name} returned no data.")
                        failed_requests += 1
                    # Respectful delay between API calls
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Failed to warm endpoint {method_name}: {e}")
                    failed_requests += 1
            else:
                logger.error(f"Method {method_name} not found in NBAStatsClient.")
                failed_requests += 1

        logger.info("Cache warming process complete.")
        return {
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "total_requests": len(self.endpoints_to_warm),
        }

def main():
    """Main function to run the cache warmer standalone."""
    # This allows the script to be run directly for debugging or manual cache warming
    manager = WarmCacheManager(season="2024-25")
    results = manager.warm_cache()
    print("\n--- Cache Warming Summary ---")
    print(f"Successful requests: {results['successful_requests']}")
    print(f"Failed requests: {results['failed_requests']}")
    print("-----------------------------")
    if results['failed_requests'] > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
