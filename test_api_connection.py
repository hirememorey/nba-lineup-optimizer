#!/usr/bin/env python3
"""
API Connection Smoke Test

This script performs a comprehensive smoke test of the NBA API to verify
that all critical endpoints are working before running the full data pipeline.
It tests the exact same client and methods that the main pipeline uses.

This is the "isolate with curl first" principle in action - we test the API
in isolation before debugging any application logic.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.nba_stats.api.nba_stats_client import NBAStatsClient
from src.nba_stats.api.data_fetcher import create_data_fetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_smoke_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class APISmokeTester:
    """
    Performs comprehensive smoke tests on the NBA API.
    """
    
    def __init__(self, season: str = "2024-25"):
        """Initialize the smoke tester."""
        self.season = season
        self.client = NBAStatsClient()
        self.fetcher = create_data_fetcher()
        self.results = {
            "test_start_time": time.time(),
            "tests_passed": 0,
            "tests_failed": 0,
            "total_tests": 0,
            "test_results": [],
            "critical_failures": [],
            "warnings": []
        }
    
    def run_smoke_test(self) -> Dict[str, Any]:
        """
        Run the complete smoke test suite.
        
        Returns:
            Dictionary containing all test results
        """
        logger.info("Starting NBA API smoke test...")
        logger.info(f"Testing season: {self.season}")
        logger.info("=" * 60)
        
        # Test 1: Basic API connectivity
        self._test_basic_connectivity()
        
        # Test 2: League-wide endpoints
        self._test_league_endpoints()
        
        # Test 3: Player-specific endpoints
        self._test_player_endpoints()
        
        # Test 4: Data fetcher integration
        self._test_data_fetcher()
        
        # Test 5: Rate limiting and error handling
        self._test_rate_limiting()
        
        # Generate final report
        self._generate_test_report()
        
        # Calculate overall success
        success_rate = (self.results["tests_passed"] / self.results["total_tests"] * 100) if self.results["total_tests"] > 0 else 0
        self.results["success_rate"] = success_rate
        self.results["test_end_time"] = time.time()
        self.results["duration"] = self.results["test_end_time"] - self.results["test_start_time"]
        
        logger.info("=" * 60)
        logger.info(f"Smoke test completed in {self.results['duration']:.2f} seconds")
        logger.info(f"Tests passed: {self.results['tests_passed']}/{self.results['total_tests']} ({success_rate:.1f}%)")
        
        if self.results["critical_failures"]:
            logger.error(f"Critical failures: {len(self.results['critical_failures'])}")
            for failure in self.results["critical_failures"]:
                logger.error(f"  - {failure}")
        
        return self.results
    
    def _test_basic_connectivity(self) -> None:
        """Test basic API connectivity and authentication."""
        logger.info("Test 1: Basic API Connectivity")
        
        # Test 1.1: Simple team request
        self._run_test(
            name="Basic team request",
            test_func=lambda: self.client.get_all_teams(),
            critical=True,
            expected_keys=["resultSets"]
        )
        
        # Test 1.2: Simple player request
        self._run_test(
            name="Basic player request",
            test_func=lambda: self.client.get_players_with_stats(season=self.season),
            critical=True,
            expected_keys=["resultSets"]
        )
    
    def _test_league_endpoints(self) -> None:
        """Test league-wide statistical endpoints."""
        logger.info("Test 2: League-wide Endpoints")
        
        # Test 2.1: League player stats (Base)
        self._run_test(
            name="League player stats (Base)",
            test_func=lambda: self.client.get_players_with_stats(season=self.season),
            critical=True,
            expected_keys=["resultSets"]
        )
        
        # Test 2.2: League player stats (Advanced)
        self._run_test(
            name="League player stats (Advanced)",
            test_func=lambda: self.client.get_league_player_advanced_stats(season=self.season),
            critical=True,
            expected_keys=["resultSets"]
        )
        
        # Test 2.3: League hustle stats
        self._run_test(
            name="League hustle stats",
            test_func=lambda: self.client.get_league_hustle_stats(season=self.season),
            critical=False,
            expected_keys=["resultSets"]
        )
        
        # Test 2.4: League shot locations
        self._run_test(
            name="League shot locations",
            test_func=lambda: self.client.get_league_player_shot_locations(season=self.season),
            critical=False,
            expected_keys=["resultSets"]
        )
        
        # Test 2.5: League tracking stats (Drives)
        self._run_test(
            name="League tracking stats (Drives)",
            test_func=lambda: self.client.get_league_player_tracking_stats(
                season=self.season, 
                pt_measure_type="Drives"
            ),
            critical=False,
            expected_keys=["resultSets"]
        )
    
    def _test_player_endpoints(self) -> None:
        """Test player-specific endpoints with representative players."""
        logger.info("Test 3: Player-specific Endpoints")
        
        # Representative players for testing
        test_players = [
            (2544, "LeBron James", "superstar"),
            (201935, "James Harden", "veteran"),
            (1630173, "Victor Wembanyama", "rookie")
        ]
        
        for player_id, player_name, player_type in test_players:
            logger.info(f"  Testing {player_name} ({player_type})...")
            
            # Test 3.1: Player basic stats
            self._run_test(
                name=f"{player_name} basic stats",
                test_func=lambda pid=player_id: self.client.get_player_stats(
                    player_id=pid, 
                    season=self.season,
                    measure_type="Base"
                ),
                critical=True,
                expected_keys=["resultSets"]
            )
            
            # Test 3.2: Player advanced stats
            self._run_test(
                name=f"{player_name} advanced stats",
                test_func=lambda pid=player_id: self.client.get_player_advanced_stats(
                    player_id=pid,
                    season=self.season
                ),
                critical=True,
                expected_keys=["resultSets"]
            )
            
            # Test 3.3: Player info
            self._run_test(
                name=f"{player_name} player info",
                test_func=lambda pid=player_id: self.client.get_common_player_info(player_id=pid),
                critical=False,
                expected_keys=["resultSets"]
            )
            
            # Add delay between players
            time.sleep(1)
    
    def _test_data_fetcher(self) -> None:
        """Test the data fetcher integration."""
        logger.info("Test 4: Data Fetcher Integration")
        
        # Test 4.1: Available metrics count
        available_metrics = self.fetcher.get_available_metrics()
        self._run_test(
            name="Available metrics count",
            test_func=lambda: len(available_metrics),
            critical=True,
            expected_min=30,  # Should have at least 30 available metrics
            is_value_test=True
        )
        
        # Test 4.2: Missing metrics count
        missing_metrics = self.fetcher.get_missing_metrics()
        self._run_test(
            name="Missing metrics count",
            test_func=lambda: len(missing_metrics),
            critical=False,
            expected_max=10,  # Should have at most 10 missing metrics
            is_value_test=True
        )
        
        # Test 4.3: Fetch specific metrics
        test_metrics = ["FTPCT", "TSPCT", "THPAr", "FTr", "TRBPCT"]
        for metric in test_metrics:
            self._run_test(
                name=f"Fetch metric: {metric}",
                test_func=lambda m=metric: self.fetcher.fetch_metric_data(m, self.season),
                critical=True,
                expected_keys=[],
                is_data_test=True
            )
            time.sleep(0.5)  # Rate limiting
    
    def _test_rate_limiting(self) -> None:
        """Test rate limiting and error handling."""
        logger.info("Test 5: Rate Limiting and Error Handling")
        
        # Test 5.1: Rapid requests (should not fail)
        logger.info("  Testing rapid requests...")
        rapid_success = 0
        rapid_total = 5
        
        for i in range(rapid_total):
            try:
                response = self.client.get_players_with_stats(season=self.season)
                if response and 'resultSets' in response:
                    rapid_success += 1
                time.sleep(0.1)  # Very short delay
            except Exception as e:
                logger.warning(f"    Rapid request {i+1} failed: {e}")
        
        success_rate = (rapid_success / rapid_total) * 100
        self._run_test(
            name="Rapid requests success rate",
            test_func=lambda: success_rate,
            critical=False,
            expected_min=80.0,  # At least 80% should succeed
            is_value_test=True
        )
        
        # Test 5.2: Invalid player ID (should handle gracefully)
        self._run_test(
            name="Invalid player ID handling",
            test_func=lambda: self.client.get_player_stats(
                player_id=999999,  # Non-existent player
                season=self.season
            ),
            critical=False,
            expected_keys=["resultSets"],
            should_fail=True
        )
    
    def _run_test(
        self, 
        name: str, 
        test_func, 
        critical: bool = True, 
        expected_keys: List[str] = None,
        expected_min: float = None,
        expected_max: float = None,
        is_value_test: bool = False,
        is_data_test: bool = False,
        should_fail: bool = False
    ) -> None:
        """
        Run a single test and record the result.
        
        Args:
            name: Test name
            test_func: Function to execute
            critical: Whether this test is critical for pipeline success
            expected_keys: Keys that should be present in the response
            expected_min: Minimum expected value (for numeric tests)
            expected_max: Maximum expected value (for numeric tests)
            is_value_test: Whether this is testing a numeric value
            is_data_test: Whether this is testing data presence
            should_fail: Whether this test is expected to fail
        """
        self.results["total_tests"] += 1
        start_time = time.time()
        
        try:
            result = test_func()
            duration = time.time() - start_time
            
            # Determine if test passed
            passed = False
            error_msg = None
            
            if should_fail:
                # Test is expected to fail
                if result is None or (isinstance(result, dict) and not result.get('resultSets')):
                    passed = True
                else:
                    error_msg = "Expected test to fail but it succeeded"
            elif is_value_test:
                # Testing a numeric value
                if expected_min is not None and result < expected_min:
                    error_msg = f"Value {result} below minimum {expected_min}"
                elif expected_max is not None and result > expected_max:
                    error_msg = f"Value {result} above maximum {expected_max}"
                else:
                    passed = True
            elif is_data_test:
                # Testing data presence
                if result and len(result) > 0:
                    passed = True
                else:
                    error_msg = "No data returned"
            else:
                # Testing response structure
                if result and isinstance(result, dict):
                    if expected_keys:
                        missing_keys = [key for key in expected_keys if key not in result]
                        if missing_keys:
                            error_msg = f"Missing keys: {missing_keys}"
                        else:
                            passed = True
                    else:
                        passed = True
                else:
                    error_msg = "Invalid response format"
            
            # Record result
            test_result = {
                "name": name,
                "passed": passed,
                "duration": duration,
                "critical": critical,
                "error": error_msg,
                "result_type": "value" if is_value_test else "data" if is_data_test else "response"
            }
            
            if passed:
                self.results["tests_passed"] += 1
                status = "PASS"
                logger.info(f"  ✓ {name} ({duration:.2f}s)")
            else:
                self.results["tests_failed"] += 1
                status = "FAIL"
                logger.error(f"  ✗ {name} ({duration:.2f}s): {error_msg}")
                
                if critical:
                    self.results["critical_failures"].append(f"{name}: {error_msg}")
                else:
                    self.results["warnings"].append(f"{name}: {error_msg}")
            
            self.results["test_results"].append(test_result)
            
        except Exception as e:
            duration = time.time() - start_time
            self.results["tests_failed"] += 1
            status = "ERROR"
            logger.error(f"  ✗ {name} ({duration:.2f}s): Exception - {str(e)}")
            
            test_result = {
                "name": name,
                "passed": False,
                "duration": duration,
                "critical": critical,
                "error": f"Exception: {str(e)}",
                "result_type": "exception"
            }
            
            if critical:
                self.results["critical_failures"].append(f"{name}: Exception - {str(e)}")
            else:
                self.results["warnings"].append(f"{name}: Exception - {str(e)}")
            
            self.results["test_results"].append(test_result)
    
    def _generate_test_report(self) -> None:
        """Generate a comprehensive test report."""
        report_lines = []
        report_lines.append("# NBA API Smoke Test Report")
        report_lines.append(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Season: {self.season}")
        report_lines.append(f"Duration: {self.results['duration']:.2f} seconds")
        report_lines.append("")
        
        # Summary
        success_rate = (self.results["tests_passed"] / self.results["total_tests"] * 100) if self.results["total_tests"] > 0 else 0
        report_lines.append("## Summary")
        report_lines.append(f"- Total tests: {self.results['total_tests']}")
        report_lines.append(f"- Passed: {self.results['tests_passed']}")
        report_lines.append(f"- Failed: {self.results['tests_failed']}")
        report_lines.append(f"- Success rate: {success_rate:.1f}%")
        report_lines.append("")
        
        # Critical failures
        if self.results["critical_failures"]:
            report_lines.append("## Critical Failures")
            report_lines.append("These failures will prevent the data pipeline from running successfully:")
            for failure in self.results["critical_failures"]:
                report_lines.append(f"- {failure}")
            report_lines.append("")
        
        # Warnings
        if self.results["warnings"]:
            report_lines.append("## Warnings")
            report_lines.append("These issues may cause problems but won't prevent the pipeline from running:")
            for warning in self.results["warnings"]:
                report_lines.append(f"- {warning}")
            report_lines.append("")
        
        # Detailed test results
        report_lines.append("## Detailed Test Results")
        for test in self.results["test_results"]:
            status = "✓ PASS" if test["passed"] else "✗ FAIL"
            critical = " (CRITICAL)" if test["critical"] else ""
            report_lines.append(f"### {test['name']}")
            report_lines.append(f"- Status: {status}{critical}")
            report_lines.append(f"- Duration: {test['duration']:.2f}s")
            if test["error"]:
                report_lines.append(f"- Error: {test['error']}")
            report_lines.append("")
        
        # Recommendations
        report_lines.append("## Recommendations")
        if self.results["critical_failures"]:
            report_lines.append("❌ **DO NOT RUN THE DATA PIPELINE**")
            report_lines.append("Critical failures detected. Please:")
            report_lines.append("1. Check your internet connection")
            report_lines.append("2. Verify the NBA API is accessible")
            report_lines.append("3. Check if the season parameter is correct")
            report_lines.append("4. Review the error messages above")
        elif self.results["warnings"]:
            report_lines.append("⚠️ **PROCEED WITH CAUTION**")
            report_lines.append("Some non-critical issues detected. The pipeline may run but with reduced functionality.")
            report_lines.append("Consider addressing warnings before running the full pipeline.")
        else:
            report_lines.append("✅ **READY TO PROCEED**")
            report_lines.append("All tests passed! The data pipeline should run successfully.")
            report_lines.append("You can now run: `python master_data_pipeline.py --season 2024-25`")
        
        # Save report
        report_content = "\n".join(report_lines)
        with open("api_smoke_test_report.md", "w") as f:
            f.write(report_content)
        
        logger.info("Test report generated: api_smoke_test_report.md")

def main():
    """Main entry point for the smoke test."""
    import argparse
    
    parser = argparse.ArgumentParser(description="NBA API Smoke Test")
    parser.add_argument("--season", default="2024-25", help="Season to test")
    parser.add_argument("--quick", action="store_true", help="Run quick test (fewer endpoints)")
    
    args = parser.parse_args()
    
    tester = APISmokeTester(season=args.season)
    results = tester.run_smoke_test()
    
    # Exit with appropriate code
    if results["critical_failures"]:
        print("\n❌ Smoke test failed - Critical issues detected")
        return 1
    elif results["warnings"]:
        print("\n⚠️ Smoke test passed with warnings")
        return 0
    else:
        print("\n✅ Smoke test passed - Ready to proceed")
        return 0

if __name__ == "__main__":
    exit(main())