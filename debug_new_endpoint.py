#!/usr/bin/env python3
"""
Reconnaissance script to analyze the leaguedashplayerstats endpoint schema compatibility.

This script validates whether the bulk endpoint provides all necessary columns
to populate the PlayerSeasonAdvancedStats table, addressing the architectural
flaw identified in the post-mortem.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from nba_stats.api.nba_stats_client import NBAStatsClient
from nba_stats.scripts.common_utils import get_db_connection, logger
import sqlite3

def get_database_schema():
    """Get the schema of PlayerSeasonAdvancedStats table from the database."""
    conn = get_db_connection()
    if not conn:
        logger.error("Could not connect to database")
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(PlayerSeasonAdvancedStats)")
        columns = cursor.fetchall()
        return [col[1] for col in columns]  # col[1] is the column name
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return []
    finally:
        conn.close()

def test_leaguedashplayerstats_endpoint():
    """Test the leaguedashplayerstats endpoint and analyze its schema."""
    client = NBAStatsClient()
    
    # Test with 2024-25 season using correct parameters from NBA.com
    season = "2024-25"
    logger.info(f"Testing leaguedashplayerstats endpoint for season {season}")
    
    # Test both Base and Advanced measure types with correct parameters
    for measure_type in ["Base", "Advanced"]:
        logger.info(f"\n=== Testing {measure_type} Measure Type ===")
        
        try:
            if measure_type == "Base":
                # Use the correct parameters that match NBA.com's actual requests
                response = client.get_players_with_stats(season)
            else:
                response = client.get_league_player_advanced_stats(season)
            
            if not response:
                logger.error(f"No response for {measure_type} measure type")
                continue
                
            # Extract headers from the response
            if 'resultSets' in response and response['resultSets']:
                result_set = response['resultSets'][0]
                headers = result_set.get('headers', [])
                row_count = len(result_set.get('rowSet', []))
                
                logger.info(f"API Response - {measure_type}:")
                logger.info(f"  - Number of players: {row_count}")
                logger.info(f"  - Number of columns: {len(headers)}")
                logger.info(f"  - Headers: {headers}")
                
                # Check for key columns we need
                key_columns = ['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ID', 'GP', 'MIN']
                missing_key_columns = [col for col in key_columns if col not in headers]
                
                if missing_key_columns:
                    logger.warning(f"Missing key columns in {measure_type}: {missing_key_columns}")
                else:
                    logger.info(f"All key columns present in {measure_type}")
                
                # Check for games played data quality
                if 'GP' in headers:
                    gp_index = headers.index('GP')
                    games_played_values = []
                    for row in result_set.get('rowSet', [])[:10]:  # Check first 10 players
                        if gp_index < len(row):
                            games_played_values.append(row[gp_index])
                    
                    logger.info(f"Sample games played values: {games_played_values}")
                    if games_played_values:
                        max_gp = max(games_played_values)
                        logger.info(f"Maximum games played in sample: {max_gp}")
                        
                        if max_gp < 82:
                            logger.warning(f"WARNING: Maximum games played ({max_gp}) is less than 82!")
                        else:
                            logger.info("Games played data looks reasonable")
                
            else:
                logger.error(f"Invalid response structure for {measure_type}")
                
        except Exception as e:
            logger.error(f"Error testing {measure_type} measure type: {e}")

def test_per_player_endpoint_with_correct_params():
    """Test the per-player endpoint using the exact parameters from NBA.com cURL."""
    client = NBAStatsClient()
    
    # Test with LeBron James (ID: 2544) using correct parameters
    test_player_id = 2544
    season = "2024-25"
    
    logger.info(f"\n=== Testing Per-Player Endpoint with Correct Parameters ===")
    logger.info(f"Testing with Player ID: {test_player_id}, Season: {season}")
    
    try:
        # Use the exact parameters from the cURL request
        base_stats = client.get_player_stats(
            player_id=test_player_id, 
            season=season, 
            per_mode="PerGame",  # This was the key difference!
            measure_type="Base"
        )
        
        advanced_stats = client.get_player_stats(
            player_id=test_player_id, 
            season=season, 
            per_mode="PerGame",
            measure_type="Advanced"
        )
        
        if not base_stats or not advanced_stats:
            logger.error("Failed to fetch per-player data with correct parameters")
            return False
            
        # Extract and analyze the data
        def extract_data(response):
            if not response or 'resultSets' not in response:
                return {}
            for result_set in response.get('resultSets', []):
                if result_set.get('name') == 'OverallPlayerDashboard' and result_set.get('rowSet'):
                    headers = [h.upper() for h in result_set['headers']]
                    row = result_set['rowSet'][0]
                    return dict(zip(headers, row))
            return {}
        
        base_data = extract_data(base_stats)
        advanced_data = extract_data(advanced_stats)
        
        if not base_data or not advanced_data:
            logger.error("Could not extract data from per-player endpoint")
            return False
            
        logger.info(f"Per-player endpoint data:")
        logger.info(f"  - Base columns: {len(base_data)}")
        logger.info(f"  - Advanced columns: {len(advanced_data)}")
        logger.info(f"  - Sample base columns: {list(base_data.keys())[:10]}")
        logger.info(f"  - Sample advanced columns: {list(advanced_data.keys())[:10]}")
        
        # Check games played
        if 'GP' in base_data:
            gp_value = base_data['GP']
            logger.info(f"  - Games played: {gp_value}")
            if gp_value < 82:
                logger.warning(f"WARNING: Games played ({gp_value}) is less than 82!")
            else:
                logger.info("Games played data looks reasonable")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing per-player endpoint: {e}")
        return False

def compare_schemas():
    """Compare API response schema with database table schema."""
    logger.info("\n=== Schema Comparison ===")
    
    # Get database schema
    db_columns = get_database_schema()
    if not db_columns:
        logger.error("Could not retrieve database schema")
        return
    
    logger.info(f"Database columns ({len(db_columns)}): {db_columns}")
    
    # Test the Advanced endpoint (most relevant for PlayerSeasonAdvancedStats)
    client = NBAStatsClient()
    response = client.get_league_player_advanced_stats("2024-25")
    
    if not response or 'resultSets' not in response:
        logger.error("Could not retrieve API response")
        return
    
    api_headers = response['resultSets'][0].get('headers', [])
    logger.info(f"API columns ({len(api_headers)}): {api_headers}")
    
    # Find matches and mismatches
    db_set = set(db_columns)
    api_set = set(api_headers)
    
    matches = db_set.intersection(api_set)
    db_only = db_set - api_set
    api_only = api_set - db_set
    
    logger.info(f"\nSchema Analysis:")
    logger.info(f"  - Matching columns: {len(matches)}")
    logger.info(f"  - Database-only columns: {len(db_only)}")
    logger.info(f"  - API-only columns: {len(api_only)}")
    
    if matches:
        logger.info(f"  - Matches: {sorted(matches)}")
    
    if db_only:
        logger.warning(f"  - Missing from API: {sorted(db_only)}")
    
    if api_only:
        logger.info(f"  - Extra in API: {sorted(api_only)}")
    
    # Check for critical missing columns
    critical_columns = ['player_id', 'season', 'team_id', 'games_played', 'minutes_played']
    critical_missing = [col for col in critical_columns if col not in api_headers]
    
    if critical_missing:
        logger.error(f"CRITICAL: Missing essential columns: {critical_missing}")
        return False
    else:
        logger.info("All critical columns are present in API response")
        return True

def main():
    """Main function to run the reconnaissance."""
    logger.info("Starting reconnaissance of NBA API endpoints with correct parameters")
    
    # Test the per-player endpoint with correct parameters first
    per_player_success = test_per_player_endpoint_with_correct_params()
    
    # Test the bulk endpoint
    test_leaguedashplayerstats_endpoint()
    
    # Compare schemas
    schema_compatible = compare_schemas()
    
    logger.info(f"\n=== Reconnaissance Summary ===")
    logger.info(f"Per-player endpoint (corrected): {'✅ WORKING' if per_player_success else '❌ FAILED'}")
    logger.info(f"Bulk endpoint: {'✅ WORKING' if schema_compatible else '❌ FAILED'}")
    
    if schema_compatible and per_player_success:
        logger.info("✅ BOTH ENDPOINTS WORKING: Can proceed with data integrity fixes")
        logger.info("   The issue was incorrect API parameters, not endpoint failures.")
    elif per_player_success and not schema_compatible:
        logger.warning("⚠️  MIXED RESULTS: Per-player works, bulk has issues")
        logger.warning("   Consider using per-player endpoint for now.")
    else:
        logger.error("❌ CRITICAL ISSUES: Both endpoints have problems")
        logger.error("   Need to investigate API access and parameters further.")
    
    return schema_compatible and per_player_success

if __name__ == "__main__":
    main()
