#!/usr/bin/env python3
"""
Phase 1: API Reconnaissance Script

This script isolates and characterizes the NBA API behavior to de-risk external dependencies
before implementing the full comparison script. Based on the post-mortem insights, this
script tests the happy path, sad path, and scope verification.

Key principles:
1. Isolate & Characterize the API before relying on it
2. Test the most dangerous failure mode (silent timeout) first
3. Verify that bulk endpoints can provide both Base and Advanced scopes
"""

import sys
import time
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from nba_stats.api.nba_stats_client import NBAStatsClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_happy_path():
    """
    Test Case A: Verify happy path with active player (LeBron James)
    This confirms basic connectivity and data shapes for both endpoints.
    """
    logger.info("=== Test Case A: Happy Path ===")
    
    client = NBAStatsClient()
    season = "2024-25"
    
    # LeBron James player ID (known active player)
    lebron_id = 2544
    
    try:
        # Test old per-player endpoint (Base)
        logger.info("Testing old per-player endpoint (Base)...")
        start_time = time.time()
        old_base_response = client.get_player_stats(lebron_id, season, "PerGame", "Base")
        old_base_time = time.time() - start_time
        
        if old_base_response and 'resultSets' in old_base_response:
            logger.info(f"✅ Old Base endpoint: SUCCESS ({old_base_time:.2f}s)")
            logger.info(f"   Response structure: {len(old_base_response['resultSets'])} result sets")
        else:
            logger.error("❌ Old Base endpoint: FAILED")
            return False
            
        # Test old per-player endpoint (Advanced)
        logger.info("Testing old per-player endpoint (Advanced)...")
        start_time = time.time()
        old_advanced_response = client.get_player_advanced_stats(lebron_id, season)
        old_advanced_time = time.time() - start_time
        
        if old_advanced_response and 'resultSets' in old_advanced_response:
            logger.info(f"✅ Old Advanced endpoint: SUCCESS ({old_advanced_time:.2f}s)")
            logger.info(f"   Response structure: {len(old_advanced_response['resultSets'])} result sets")
        else:
            logger.error("❌ Old Advanced endpoint: FAILED")
            return False
            
        # Test new bulk endpoint
        logger.info("Testing new bulk endpoint...")
        start_time = time.time()
        new_bulk_response = client.get_league_player_advanced_stats(season)
        new_bulk_time = time.time() - start_time
        
        if new_bulk_response and 'resultSets' in new_bulk_response:
            result_set = new_bulk_response['resultSets'][0]
            player_count = len(result_set.get('rowSet', []))
            logger.info(f"✅ New bulk endpoint: SUCCESS ({new_bulk_time:.2f}s)")
            logger.info(f"   Players returned: {player_count}")
            logger.info(f"   Headers: {len(result_set.get('headers', []))}")
        else:
            logger.error("❌ New bulk endpoint: FAILED")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Happy path test failed with exception: {e}")
        return False

def test_sad_path():
    """
    Test Case B: Verify sad path with retired player (Michael Jordan) to confirm silent timeout
    This is the most critical test - it reveals the API's most dangerous quirk.
    """
    logger.info("=== Test Case B: Sad Path (Silent Timeout Test) ===")
    
    client = NBAStatsClient()
    season = "2024-25"
    
    # Michael Jordan player ID (long-retired player)
    jordan_id = 893
    
    try:
        # Test old per-player endpoint with retired player
        logger.info("Testing old per-player endpoint with retired player (Michael Jordan)...")
        logger.info("This should either error quickly or timeout - we're testing the failure mode")
        
        start_time = time.time()
        old_response = client.get_player_stats(jordan_id, season, "PerGame", "Base")
        old_time = time.time() - start_time
        
        if old_response is None:
            logger.info(f"✅ Old endpoint with retired player: Expected failure ({old_time:.2f}s)")
        elif old_time > 30:  # If it took more than 30 seconds, it likely hung
            logger.warning(f"⚠️  Old endpoint with retired player: Silent timeout detected ({old_time:.2f}s)")
        else:
            logger.info(f"ℹ️  Old endpoint with retired player: Unexpected success ({old_time:.2f}s)")
            
        # Test new bulk endpoint (should work fine)
        logger.info("Testing new bulk endpoint (should work regardless of individual player)...")
        start_time = time.time()
        new_response = client.get_league_player_advanced_stats(season)
        new_time = time.time() - start_time
        
        if new_response and 'resultSets' in new_response:
            logger.info(f"✅ New bulk endpoint: SUCCESS ({new_time:.2f}s)")
            logger.info("   (Bulk endpoint should work even if individual players are problematic)")
        else:
            logger.error("❌ New bulk endpoint: FAILED")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Sad path test failed with exception: {e}")
        return False

def test_scope_verification():
    """
    Test Case C: Verify if bulk endpoint can provide both Base and Advanced scopes
    The old process required two calls. We need to confirm the new endpoint can provide both.
    """
    logger.info("=== Test Case C: Scope Verification ===")
    
    client = NBAStatsClient()
    season = "2024-25"
    
    try:
        # Test bulk endpoint with Base measure type
        logger.info("Testing bulk endpoint with Base measure type...")
        start_time = time.time()
        base_response = client.get_players_with_stats(season)
        base_time = time.time() - start_time
        
        if base_response:
            logger.info(f"✅ Bulk Base: SUCCESS ({base_time:.2f}s)")
            logger.info(f"   Players returned: {len(base_response)}")
        else:
            logger.error("❌ Bulk Base: FAILED")
            return False
            
        # Test bulk endpoint with Advanced measure type
        logger.info("Testing bulk endpoint with Advanced measure type...")
        start_time = time.time()
        advanced_response = client.get_league_player_advanced_stats(season)
        advanced_time = time.time() - start_time
        
        if advanced_response and 'resultSets' in advanced_response:
            result_set = advanced_response['resultSets'][0]
            player_count = len(result_set.get('rowSet', []))
            headers = result_set.get('headers', [])
            logger.info(f"✅ Bulk Advanced: SUCCESS ({advanced_time:.2f}s)")
            logger.info(f"   Players returned: {player_count}")
            logger.info(f"   Headers count: {len(headers)}")
            
            # Check for key advanced stats columns
            key_advanced_columns = ['PIE', 'USG_PCT', 'PACE', 'PACE_PER40', 'POSS', 'PIE']
            found_advanced = [col for col in key_advanced_columns if col in headers]
            logger.info(f"   Key advanced columns found: {found_advanced}")
            
        else:
            logger.error("❌ Bulk Advanced: FAILED")
            return False
            
        # Verify we can get both scopes
        logger.info("✅ Scope verification: Both Base and Advanced scopes available via bulk endpoints")
        return True
        
    except Exception as e:
        logger.error(f"❌ Scope verification failed with exception: {e}")
        return False

def main():
    """Main function to run all reconnaissance tests."""
    logger.info("Starting API Reconnaissance - Phase 1")
    logger.info("=" * 60)
    
    results = {
        'happy_path': False,
        'sad_path': False,
        'scope_verification': False
    }
    
    # Run all test cases
    results['happy_path'] = test_happy_path()
    results['sad_path'] = test_sad_path()
    results['scope_verification'] = test_scope_verification()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("RECONNAISSANCE SUMMARY")
    logger.info("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n🎉 ALL TESTS PASSED - API is ready for full comparison script")
        logger.info("   Proceeding to Phase 2: Comprehensive Audit Script")
    else:
        logger.error("\n⚠️  SOME TESTS FAILED - Address issues before proceeding")
        logger.error("   Do not proceed to Phase 2 until all tests pass")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
