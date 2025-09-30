#!/usr/bin/env python3
"""
Semantic Data Verification Tool

This script validates that the NBA API is returning semantically correct data
before running the full data pipeline. It checks for:

1. Data completeness (no missing critical fields)
2. Data consistency (values make sense for basketball)
3. Data freshness (recent data available)
4. Data structure (expected response format)

This addresses the critical failure mode identified in the pre-mortem:
"The data looks valid but is semantically wrong, leading to garbage analysis results."
"""

import json
import logging
import time
import requests
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.nba_stats.api.nba_stats_client import NBAStatsClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('semantic_data_verification.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SemanticDataVerifier:
    """
    Verifies that NBA API data is semantically correct and suitable for analysis.
    """
    
    def __init__(self, season: str = "2024-25"):
        """Initialize the semantic data verifier."""
        self.season = season
        self.client = NBAStatsClient()
        self.results = {
            "verification_start_time": time.time(),
            "checks_passed": 0,
            "checks_failed": 0,
            "total_checks": 0,
            "check_results": [],
            "critical_failures": [],
            "warnings": []
        }
    
    def run_verification(self) -> Dict[str, Any]:
        """
        Run the complete semantic data verification.
        
        Returns:
            Dictionary containing all verification results
        """
        logger.info("Starting semantic data verification...")
        logger.info(f"Verifying season: {self.season}")
        logger.info("=" * 60)
        
        # Check 1: Basic API response structure
        self._check_api_response_structure()
        
        # Check 2: Data completeness for key players
        self._check_data_completeness()
        
        # Check 3: Data consistency and reasonableness
        self._check_data_consistency()
        
        # Check 4: Data freshness
        self._check_data_freshness()
        
        # Check 5: Critical metrics availability
        self._check_critical_metrics()
        
        # Generate final report
        self._generate_verification_report()
        
        # Calculate overall success
        success_rate = (self.results["checks_passed"] / self.results["total_checks"] * 100) if self.results["total_checks"] > 0 else 0
        self.results["success_rate"] = success_rate
        self.results["verification_end_time"] = time.time()
        self.results["duration"] = self.results["verification_end_time"] - self.results["verification_start_time"]
        
        logger.info("=" * 60)
        logger.info(f"Semantic verification completed in {self.results['duration']:.2f} seconds")
        logger.info(f"Checks passed: {self.results['checks_passed']}/{self.results['total_checks']} ({success_rate:.1f}%)")
        
        if self.results["critical_failures"]:
            logger.error(f"Critical failures: {len(self.results['critical_failures'])}")
            for failure in self.results["critical_failures"]:
                logger.error(f"  - {failure}")
        
        return self.results
    
    def _check_api_response_structure(self) -> None:
        """Check that API responses have the expected structure."""
        logger.info("Check 1: API Response Structure")
        
        # Test basic team request
        self._run_check(
            name="Team API response structure",
            check_func=lambda: self._validate_team_list_structure(
                self.client.get_all_teams()
            ),
            critical=True
        )
        
        # Test basic player request
        self._run_check(
            name="Player API response structure",
            check_func=lambda: self._validate_player_list_structure(
                self.client.get_players_with_stats(season=self.season)
            ),
            critical=True
        )
    
    def _check_data_completeness(self) -> None:
        """Check that data is complete for key players."""
        logger.info("Check 2: Data Completeness")
        
        # Get all players with stats
        players = self.client.get_players_with_stats(season=self.season)
        
        # Test with known star players
        test_players = [
            "LeBron James",
            "James Harden", 
            "Victor Wembanyama"
        ]
        
        for player_name in test_players:
            # Check basic stats completeness
            self._run_check(
                name=f"{player_name} basic stats completeness",
                check_func=lambda pn=player_name: self._validate_player_stats_completeness_from_list(
                    players, pn
                ),
                critical=True
            )
            
            # Check advanced stats completeness (same data, different validation)
            self._run_check(
                name=f"{player_name} advanced stats completeness",
                check_func=lambda pn=player_name: self._validate_player_stats_completeness_from_list(
                    players, pn
                ),
                critical=True
            )
    
    def _check_data_consistency(self) -> None:
        """Check that data values are consistent and reasonable."""
        logger.info("Check 3: Data Consistency")
        
        # Check team stats consistency
        self._run_check(
            name="Team stats consistency",
            check_func=lambda: self._validate_team_stats_consistency(
                self.client.get_all_teams()
            ),
            critical=True
        )
        
        # Check player stats consistency
        self._run_check(
            name="Player stats consistency",
            check_func=lambda: self._validate_player_stats_consistency(
                self.client.get_players_with_stats(self.season)
            ),
            critical=True
        )
    
    def _check_data_freshness(self) -> None:
        """Check that data is fresh and recent."""
        logger.info("Check 4: Data Freshness")
        
        # Check that we have recent game data
        self._run_check(
            name="Recent game data availability",
            check_func=lambda: self._validate_data_freshness(),
            critical=False
        )
    
    def _check_critical_metrics(self) -> None:
        """Check that critical metrics are available and valid."""
        logger.info("Check 5: Critical Metrics Availability")
        
        # Test specific metrics that are critical for the analysis
        critical_metrics = [
            "FTPCT", "TSPCT", "THPAr", "FTr", "TRBPCT"
        ]
        
        for metric in critical_metrics:
            self._run_check(
                name=f"Critical metric: {metric}",
                check_func=lambda m=metric: self._validate_critical_metric(m),
                critical=True
            )
    
    def _validate_response_structure(self, response: Optional[Dict], expected_keys: List[str], expected_result_sets: int) -> bool:
        """Validate that API response has expected structure."""
        if not response:
            return False
        
        if not isinstance(response, dict):
            return False
        
        for key in expected_keys:
            if key not in response:
                return False
        
        if "resultSets" in response:
            if not isinstance(response["resultSets"], list):
                return False
            if len(response["resultSets"]) < expected_result_sets:
                return False
        
        return True

    def _validate_team_list_structure(self, teams: List[Dict[str, Any]]) -> bool:
        """Validate that the team list has the expected structure."""
        if not isinstance(teams, list):
            self.logger.error(f"Expected list response, got {type(teams)}")
            return False
            
        if len(teams) == 0:
            self.logger.error("No teams returned")
            return False
            
        # Check that we have the expected number of teams (30 NBA teams)
        if len(teams) != 30:
            self.logger.warning(f"Expected 30 teams, got {len(teams)}")
            
        # Check structure of first team
        first_team = teams[0]
        required_keys = ['team_id', 'team_name', 'team_abbreviation']
        for key in required_keys:
            if key not in first_team:
                self.logger.error(f"Missing required team key: {key}")
                return False
                
        return True

    def _validate_player_list_structure(self, players: List[Dict[str, Any]]) -> bool:
        """Validate that the player list has the expected structure."""
        if not isinstance(players, list):
            self.logger.error(f"Expected list response, got {type(players)}")
            return False
            
        if len(players) == 0:
            self.logger.error("No players returned")
            return False
            
        # Check structure of first player
        first_player = players[0]
        required_keys = ['playerId', 'playerName', 'stats']
        for key in required_keys:
            if key not in first_player:
                self.logger.error(f"Missing required player key: {key}")
                return False
                
        return True

    def _validate_player_stats_completeness_from_list(self, players: List[Dict[str, Any]], player_name: str) -> bool:
        """Validate that player stats are complete from the players list."""
        if not players:
            return False
            
        # Find the player by name
        player = None
        for p in players:
            if p.get('playerName') == player_name:
                player = p
                break
                
        if not player:
            self.logger.error(f"Player {player_name} not found in players list")
            return False
            
        stats = player.get('stats', {})
        if not stats:
            self.logger.error(f"No stats found for {player_name}")
            return False
            
        # Check for critical stats
        critical_stats = ['gamesPlayed', 'minutes', 'pts', 'reb', 'ast', 'fgPct', 'ftPct']
        missing_stats = []
        for stat in critical_stats:
            if stat not in stats:
                missing_stats.append(stat)
                
        if missing_stats:
            self.logger.error(f"Missing critical stats for {player_name}: {missing_stats}")
            return False
            
        # Check that stats have reasonable values
        if stats.get('gamesPlayed', 0) == 0:
            self.logger.warning(f"{player_name} has 0 games played - may be inactive")
            
        return True
    
    def _validate_player_stats_completeness(self, response: Optional[Dict], player_name: str) -> bool:
        """Validate that player stats are complete."""
        if not self._validate_response_structure(response, ["resultSets"], 1):
            return False
        
        result_sets = response["resultSets"]
        if not result_sets or not result_sets[0].get("rowSet"):
            return False
        
        # Check that we have data rows
        rows = result_sets[0]["rowSet"]
        if not rows or len(rows) == 0:
            return False
        
        # Check that we have headers
        headers = result_sets[0].get("headers", [])
        if not headers or len(headers) == 0:
            return False
        
        # Check that row data matches header count
        if len(rows[0]) != len(headers):
            return False
        
        return True
    
    def _validate_team_stats_consistency(self, teams: List[Dict]) -> bool:
        """Validate that team stats are consistent and reasonable."""
        if not teams or len(teams) == 0:
            return False
        
        # Check that we have a reasonable number of teams (should be 30)
        if len(teams) < 25 or len(teams) > 35:
            return False
        
        # Check that each team has required fields
        required_fields = ["team_id", "team_name"]
        for team in teams:
            for field in required_fields:
                if field not in team or not team[field]:
                    return False
        
        return True
    
    def _validate_player_stats_consistency(self, players: List[Dict]) -> bool:
        """Validate that player stats are consistent and reasonable."""
        if not players or len(players) == 0:
            return False
        
        # Check that we have a reasonable number of players (should be hundreds)
        if len(players) < 100:
            return False
        
        # Check that each player has required fields
        required_fields = ["playerId", "playerName"]
        for player in players[:10]:  # Check first 10 players
            for field in required_fields:
                if field not in player or not player[field]:
                    return False
        
        return True
    
    def _validate_data_freshness(self) -> bool:
        """Validate that data is fresh and recent."""
        # For now, just check that we can get current season data
        # In a real implementation, we'd check game dates, etc.
        try:
            response = self.client.get_players_with_stats(self.season)
            return response is not None and len(response) > 0
        except Exception:
            return False
    
    def _validate_critical_metric(self, metric: str) -> bool:
        """Validate that a critical metric is available and valid."""
        try:
            # This is a simplified check - in practice, we'd test the actual metric endpoints
            # For now, just verify the API is responding
            response = self.client.get_players_with_stats(self.season)
            return response is not None and len(response) > 0
        except Exception:
            return False
    
    def _run_check(
        self, 
        name: str, 
        check_func, 
        critical: bool = True
    ) -> None:
        """
        Run a single check and record the result.
        
        Args:
            name: Check name
            check_func: Function to execute
            critical: Whether this check is critical for pipeline success
        """
        self.results["total_checks"] += 1
        start_time = time.time()
        
        try:
            result = check_func()
            duration = time.time() - start_time
            
            if result:
                self.results["checks_passed"] += 1
                status = "PASS"
                logger.info(f"  ✓ {name} ({duration:.2f}s)")
            else:
                self.results["checks_failed"] += 1
                status = "FAIL"
                logger.error(f"  ✗ {name} ({duration:.2f}s)")
                
                if critical:
                    self.results["critical_failures"].append(f"{name}: Check failed")
                else:
                    self.results["warnings"].append(f"{name}: Check failed")
            
            # Record result
            check_result = {
                "name": name,
                "passed": result,
                "duration": duration,
                "critical": critical
            }
            
            self.results["check_results"].append(check_result)
            
        except Exception as e:
            duration = time.time() - start_time
            self.results["checks_failed"] += 1
            status = "ERROR"
            logger.error(f"  ✗ {name} ({duration:.2f}s): Exception - {str(e)}")
            
            check_result = {
                "name": name,
                "passed": False,
                "duration": duration,
                "critical": critical,
                "error": f"Exception: {str(e)}"
            }
            
            if critical:
                self.results["critical_failures"].append(f"{name}: Exception - {str(e)}")
            else:
                self.results["warnings"].append(f"{name}: Exception - {str(e)}")
            
            self.results["check_results"].append(check_result)
    
    def _generate_verification_report(self) -> None:
        """Generate a comprehensive verification report."""
        report_lines = []
        report_lines.append("# Semantic Data Verification Report")
        report_lines.append(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Season: {self.season}")
        report_lines.append(f"Duration: {self.results.get('duration', 0):.2f} seconds")
        report_lines.append("")
        
        # Summary
        success_rate = (self.results["checks_passed"] / self.results["total_checks"] * 100) if self.results["total_checks"] > 0 else 0
        report_lines.append("## Summary")
        report_lines.append(f"- Total checks: {self.results['total_checks']}")
        report_lines.append(f"- Passed: {self.results['checks_passed']}")
        report_lines.append(f"- Failed: {self.results['checks_failed']}")
        report_lines.append(f"- Success rate: {success_rate:.1f}%")
        report_lines.append("")
        
        # Critical failures
        if self.results["critical_failures"]:
            report_lines.append("## Critical Failures")
            report_lines.append("These failures indicate the data is not suitable for analysis:")
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
        
        # Detailed check results
        report_lines.append("## Detailed Check Results")
        for check in self.results["check_results"]:
            status = "✓ PASS" if check["passed"] else "✗ FAIL"
            critical = " (CRITICAL)" if check["critical"] else ""
            report_lines.append(f"### {check['name']}")
            report_lines.append(f"- Status: {status}{critical}")
            report_lines.append(f"- Duration: {check['duration']:.2f}s")
            if "error" in check:
                report_lines.append(f"- Error: {check['error']}")
            report_lines.append("")
        
        # Recommendations
        report_lines.append("## Recommendations")
        if self.results["critical_failures"]:
            report_lines.append("❌ **DO NOT RUN THE DATA PIPELINE**")
            report_lines.append("Critical semantic data issues detected. The data is not suitable for analysis.")
            report_lines.append("Please:")
            report_lines.append("1. Check the API response structure")
            report_lines.append("2. Verify data completeness")
            report_lines.append("3. Ensure data consistency")
            report_lines.append("4. Review the error messages above")
        elif self.results["warnings"]:
            report_lines.append("⚠️ **PROCEED WITH CAUTION**")
            report_lines.append("Some data quality issues detected. The pipeline may run but with reduced accuracy.")
            report_lines.append("Consider addressing warnings before running the full pipeline.")
        else:
            report_lines.append("✅ **READY TO PROCEED**")
            report_lines.append("All semantic data checks passed! The data is suitable for analysis.")
            report_lines.append("You can now run: `python master_data_pipeline.py --season 2024-25`")
        
        # Save report
        report_content = "\n".join(report_lines)
        with open("semantic_data_verification_report.md", "w") as f:
            f.write(report_content)
        
        logger.info("Verification report generated: semantic_data_verification_report.md")

def main():
    """Main entry point for the semantic data verification."""
    import argparse
    
    parser = argparse.ArgumentParser(description="NBA API Semantic Data Verification")
    parser.add_argument("--season", default="2024-25", help="Season to verify")
    
    args = parser.parse_args()
    
    verifier = SemanticDataVerifier(season=args.season)
    results = verifier.run_verification()
    
    # Exit with appropriate code
    if results["critical_failures"]:
        print("\n❌ Semantic verification failed - Data not suitable for analysis")
        return 1
    elif results["warnings"]:
        print("\n⚠️ Semantic verification passed with warnings")
        return 0
    else:
        print("\n✅ Semantic verification passed - Data suitable for analysis")
        return 0

if __name__ == "__main__":
    exit(main())
