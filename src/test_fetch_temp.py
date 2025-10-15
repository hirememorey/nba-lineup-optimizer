import os
import sys

from nba_stats.api.nba_stats_client import NBAStatsClient
from nba_stats.utils.common_utils import CommonUtils

def test_api_fetch(season, measure_type):
    """
    Performs a minimal, isolated API call to fetch lineup stats
    and prints the raw response.
    """
    utils = CommonUtils()
    client = NBAStatsClient(utils)
    
    print(f"--- Testing API fetch for Season: {season}, MeasureType: {measure_type} ---")
    
    try:
        # Use a known valid team ID for the test, e.g., Lakers
        team_id = '1610612747' 
        
        response = client.get_lineup_stats(
            season=season,
            team_id=team_id,
            measure_type=measure_type
        )
        
        if response:
            print("--- RAW API RESPONSE ---")
            # Print the entire response to see its structure
            import json
            print(json.dumps(response, indent=2))
            
            # Check for key parts of the response
            if 'resultSets' in response and response['resultSets']:
                result_sets = response['resultSets']
                if isinstance(result_sets, list) and result_sets:
                    headers = result_sets[0].get('headers')
                    row_set = result_sets[0].get('rowSet')
                    print(f"\n--- VALIDATION ---")
                    print(f"Successfully found 'resultSets'.")
                    print(f"Number of rows returned: {len(row_set) if row_set else 0}")
                    print(f"Headers: {headers}")
                else:
                    print("\n--- VALIDATION FAILED ---")
                    print("'resultSets' is not a non-empty list.")
            else:
                print("\n--- VALIDATION FAILED ---")
                print("'resultSets' key not found or is empty in the response.")
        else:
            print("--- API call returned an empty response. ---")
            
    except Exception as e:
        print(f"\n--- An error occurred during the API call ---")
        print(e)

if __name__ == "__main__":
    # We are testing one of the data types that was failing in the profiling
    test_api_fetch(season='2022-23', measure_type='Advanced')
