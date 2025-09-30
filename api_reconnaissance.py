"""
API Reconnaissance Tool

This tool performs comprehensive forensics on the NBA Stats API to inventory
all available columns from all relevant endpoints. It tests multiple parameter
combinations and player types to discover schema variations.
"""

import json
import time
import random
from typing import Dict, List, Set, Tuple
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from canonical_metrics import CANONICAL_48_METRICS
from metric_to_script_mapping import METRIC_TO_SCRIPT_MAPPING, get_all_api_endpoints
from src.nba_stats.scripts.common_utils import get_nba_stats_client, logger

# Test players representing different archetypes and usage patterns
TEST_PLAYERS = [
    {"id": 2544, "name": "LeBron James", "type": "star_veteran"},
    {"id": 201935, "name": "James Harden", "type": "star_veteran"}, 
    {"id": 201142, "name": "Kevin Durant", "type": "star_veteran"},
    {"id": 1629029, "name": "Ja Morant", "type": "star_young"},
    {"id": 203999, "name": "Nikola Jokic", "type": "star_big"},
    {"id": 1628368, "name": "Jayson Tatum", "type": "star_wing"},
    {"id": 1629027, "name": "Deandre Ayton", "type": "role_big"},
    {"id": 203954, "name": "Jabari Parker", "type": "role_wing"},
    {"id": 1627742, "name": "Domantas Sabonis", "type": "role_big"},
    {"id": 1628991, "name": "Luka Doncic", "type": "star_young"},
    {"id": 1629028, "name": "Trae Young", "type": "star_young"},
    {"id": 1627759, "name": "Jaylen Brown", "type": "star_wing"},
    {"id": 1628369, "name": "Lonzo Ball", "type": "role_guard"},
    {"id": 203507, "name": "Giannis Antetokounmpo", "type": "star_big"},
    {"id": 201566, "name": "Russell Westbrook", "type": "star_veteran"}
]

# Parameter combinations to test for each endpoint
PARAMETER_COMBINATIONS = {
    "leaguedashplayerstats": [
        {"MeasureType": "Base", "PerMode": "PerGame", "SeasonType": "Regular Season"},
        {"MeasureType": "Advanced", "PerMode": "PerGame", "SeasonType": "Regular Season"},
        {"MeasureType": "Base", "PerMode": "Per100Possessions", "SeasonType": "Regular Season"},
        {"MeasureType": "Advanced", "PerMode": "Per100Possessions", "SeasonType": "Regular Season"},
    ],
    "leaguedashptstats": [
        {"PtMeasureType": "Drives", "PerMode": "PerGame"},
        {"PtMeasureType": "CatchShoot", "PerMode": "PerGame"},
        {"PtMeasureType": "PullUpShot", "PerMode": "PerGame"},
        {"PtMeasureType": "PostTouch", "PerMode": "PerGame"},
        {"PtMeasureType": "PaintTouch", "PerMode": "PerGame"},
        {"PtMeasureType": "ElbowTouch", "PerMode": "PerGame"},
        {"PtMeasureType": "Possessions", "PerMode": "PerGame"},
        {"PtMeasureType": "Passing", "PerMode": "PerGame"},
    ],
    "leaguedashplayershotlocations": [
        {"MeasureType": "Base", "PerMode": "PerGame"},
        {"MeasureType": "Base", "PerMode": "Per100Possessions"},
    ],
    "leaguedashplayerhustlestats": [
        {"PerMode": "PerGame"},
        {"PerMode": "Per100Possessions"},
    ],
    "commonplayerinfo": [
        {}  # No additional parameters
    ]
}

def fetch_endpoint_columns(client, endpoint: str, params: Dict, season: str = "2024-25") -> Set[str]:
    """
    Fetch columns from a specific endpoint with given parameters.
    Returns a set of column names found in the response.
    """
    try:
        logger.info(f"Testing {endpoint} with params: {params}")
        
        # Add season to all requests
        request_params = {"Season": season, **params}
        
        # Make the API call based on endpoint type
        if endpoint == "leaguedashplayerstats":
            # Use the correct method name and parameter structure
            if request_params.get("MeasureType") == "Base":
                response = client.get_players_with_stats(season=season)
            else:  # Advanced
                response = client.get_league_player_advanced_stats(season=season, season_type=request_params.get("SeasonType", "Regular Season"))
        elif endpoint == "leaguedashptstats":
            # Use the correct method name and parameter structure
            pt_measure_type = request_params.get("PtMeasureType", "Drives")
            response = client.get_league_player_tracking_stats(season=season, pt_measure_type=pt_measure_type)
        elif endpoint == "leaguedashplayershotlocations":
            # Use the correct method name and parameter structure
            response = client.get_league_player_shot_locations(season=season)
        elif endpoint == "leaguedashplayerhustlestats":
            # Use the correct method name and parameter structure
            response = client.get_league_hustle_stats(season=season)
        elif endpoint == "commonplayerinfo":
            # For commonplayerinfo, we need to test with a specific player
            response = client.get_common_player_info(player_id=2544)  # LeBron James
        else:
            logger.warning(f"Unknown endpoint: {endpoint}")
            return set()
        
        if not response or 'resultSets' not in response:
            logger.warning(f"No resultSets in response for {endpoint}")
            return set()
            
        # Extract columns from all result sets
        columns = set()
        for result_set in response['resultSets']:
            if 'headers' in result_set and result_set['headers']:
                columns.update(result_set['headers'])
        
        logger.info(f"Found {len(columns)} columns for {endpoint}")
        return columns
        
    except Exception as e:
        logger.error(f"Error fetching {endpoint} with params {params}: {e}")
        return set()

def test_player_specific_endpoints(client, season: str = "2024-25") -> Dict[str, Set[str]]:
    """
    Test endpoints that require specific player IDs to discover player-specific columns.
    """
    player_columns = {}
    
    for player in TEST_PLAYERS[:3]:  # Test with first 3 players to avoid rate limiting
        try:
            logger.info(f"Testing player-specific endpoints for {player['name']}")
            
            # Test commonplayerinfo for this specific player
            response = client.get_common_player_info(player_id=player['id'])
            if response and 'resultSets' in response:
                columns = set()
                for result_set in response['resultSets']:
                    if 'headers' in result_set and result_set['headers']:
                        columns.update(result_set['headers'])
                player_columns[f"commonplayerinfo_player_{player['id']}"] = columns
                
        except Exception as e:
            logger.error(f"Error testing player {player['name']}: {e}")
            
        # Add delay to avoid rate limiting
        time.sleep(1)
    
    return player_columns

def run_comprehensive_reconnaissance(season: str = "2024-25") -> Dict:
    """
    Run comprehensive API reconnaissance to discover all available columns.
    """
    logger.info("Starting comprehensive API reconnaissance...")
    
    client = get_nba_stats_client()
    if not client:
        logger.error("Failed to get NBA Stats client")
        return {}
    
    # Get all unique endpoints from our mapping
    endpoints = get_all_api_endpoints()
    logger.info(f"Testing {len(endpoints)} unique endpoints")
    
    # Results storage
    api_column_map = {}
    endpoint_coverage = {}
    
    # Test each endpoint with all parameter combinations
    for endpoint in endpoints:
        logger.info(f"Testing endpoint: {endpoint}")
        endpoint_columns = set()
        
        if endpoint in PARAMETER_COMBINATIONS:
            for params in PARAMETER_COMBINATIONS[endpoint]:
                columns = fetch_endpoint_columns(client, endpoint, params, season)
                endpoint_columns.update(columns)
                
                # Store parameter-specific results
                param_key = f"{endpoint}_{json.dumps(params, sort_keys=True)}"
                api_column_map[param_key] = list(columns)
                
                # Add delay to avoid rate limiting
                time.sleep(0.5)
        else:
            # Test with default parameters
            columns = fetch_endpoint_columns(client, endpoint, {}, season)
            endpoint_columns.update(columns)
            api_column_map[endpoint] = list(endpoint_columns)
        
        endpoint_coverage[endpoint] = list(endpoint_columns)
        logger.info(f"Total columns found for {endpoint}: {len(endpoint_columns)}")
    
    # Test player-specific endpoints
    logger.info("Testing player-specific endpoints...")
    player_columns = test_player_specific_endpoints(client, season)
    api_column_map.update(player_columns)
    
    # Generate summary statistics
    all_columns = set()
    for columns in endpoint_coverage.values():
        all_columns.update(columns)
    
    summary = {
        "total_endpoints_tested": len(endpoints),
        "total_unique_columns": len(all_columns),
        "endpoint_coverage": {endpoint: len(columns) for endpoint, columns in endpoint_coverage.items()},
        "season_tested": season,
        "test_players_used": len(TEST_PLAYERS)
    }
    
    logger.info(f"Reconnaissance complete. Found {len(all_columns)} unique columns across {len(endpoints)} endpoints")
    
    return {
        "api_column_map": api_column_map,
        "endpoint_coverage": endpoint_coverage,
        "summary": summary
    }

def save_reconnaissance_results(results: Dict, output_file: str = "api_reconnaissance_results.json"):
    """Save reconnaissance results to JSON file."""
    try:
        # Convert sets to lists for JSON serialization
        def convert_sets_to_lists(obj):
            if isinstance(obj, set):
                return list(obj)
            elif isinstance(obj, dict):
                return {key: convert_sets_to_lists(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_sets_to_lists(item) for item in obj]
            else:
                return obj
        
        serializable_results = convert_sets_to_lists(results)
        
        with open(output_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        logger.info(f"Results saved to {output_file}")
    except Exception as e:
        logger.error(f"Error saving results: {e}")

def generate_column_inventory_report(results: Dict) -> str:
    """Generate a human-readable report of all discovered columns."""
    report_lines = []
    report_lines.append("# NBA Stats API Column Inventory Report")
    report_lines.append(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # Summary
    summary = results.get("summary", {})
    report_lines.append("## Summary")
    report_lines.append(f"- Total endpoints tested: {summary.get('total_endpoints_tested', 0)}")
    report_lines.append(f"- Total unique columns found: {summary.get('total_unique_columns', 0)}")
    report_lines.append(f"- Season tested: {summary.get('season_tested', 'Unknown')}")
    report_lines.append("")
    
    # Endpoint coverage
    report_lines.append("## Endpoint Coverage")
    endpoint_coverage = results.get("endpoint_coverage", {})
    for endpoint, column_count in endpoint_coverage.items():
        report_lines.append(f"- {endpoint}: {column_count} columns")
    report_lines.append("")
    
    # Detailed column listings
    report_lines.append("## Detailed Column Listings")
    api_column_map = results.get("api_column_map", {})
    
    for endpoint_key, columns in api_column_map.items():
        report_lines.append(f"### {endpoint_key}")
        if columns:
            for column in sorted(columns):
                report_lines.append(f"- {column}")
        else:
            report_lines.append("- No columns found")
        report_lines.append("")
    
    return "\n".join(report_lines)

if __name__ == "__main__":
    # Run the reconnaissance
    results = run_comprehensive_reconnaissance()
    
    # Save results
    save_reconnaissance_results(results)
    
    # Generate and save report
    report = generate_column_inventory_report(results)
    with open("api_column_inventory_report.md", "w") as f:
        f.write(report)
    
    print("API reconnaissance complete!")
    print(f"Results saved to: api_reconnaissance_results.json")
    print(f"Report saved to: api_column_inventory_report.md")