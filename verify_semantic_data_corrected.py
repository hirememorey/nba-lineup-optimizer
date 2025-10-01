#!/usr/bin/env python3
"""
Corrected Semantic Data Verification Tool

This script validates that the NBA API is returning semantically correct data
using the correct data fetcher approach instead of the raw API client.
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.nba_stats.api.data_fetcher import create_data_fetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('semantic_data_verification_corrected.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CorrectedSemanticDataVerifier:
    """
    Verifies that NBA API data is semantically correct using the data fetcher.
    """
    
    def __init__(self, season: str = "2024-25"):
        """Initialize the semantic data verifier."""
        self.season = season
        self.fetcher = create_data_fetcher()
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
        logger.info("Starting corrected semantic data verification...")
        logger.info(f"Verifying season: {self.season}")
        logger.info("=" * 60)
        
        # Check 1: Data fetcher availability
        self._check_data_fetcher_availability()
        
        # Check 2: Critical metrics availability
        self._check_critical_metrics_availability()
        
        # Check 3: Data completeness for key metrics
        self._check_data_completeness()
        
        # Check 4: Data consistency and reasonableness
        self._check_data_consistency()
        
        # Calculate overall success
        success_rate = (self.results["checks_passed"] / self.results["total_checks"] * 100) if self.results["total_checks"] > 0 else 0
        self.results["success_rate"] = success_rate
        self.results["verification_end_time"] = time.time()
        self.results["duration"] = self.results["verification_end_time"] - self.results["verification_start_time"]
        
        # Generate final report
        self._generate_verification_report()
        
        logger.info("=" * 60)
        logger.info(f"Corrected semantic verification completed in {self.results['duration']:.2f} seconds")
        logger.info(f"Checks passed: {self.results['checks_passed']}/{self.results['total_checks']} ({success_rate:.1f}%)")
        
        if self.results["critical_failures"]:
            logger.error(f"Critical failures: {len(self.results['critical_failures'])}")
            for failure in self.results["critical_failures"]:
                logger.error(f"  - {failure}")
        else:
            logger.info("✅ All critical checks passed!")
        
        return self.results
    
    def _run_check(self, name: str, check_func, critical: bool = True) -> bool:
        """Run a single check and record the result."""
        self.results["total_checks"] += 1
        start_time = time.time()
        
        try:
            result = check_func()
            duration = time.time() - start_time
            
            if result:
                self.results["checks_passed"] += 1
                self.results["check_results"].append({
                    "name": name,
                    "status": "PASS",
                    "duration": duration,
                    "critical": critical
                })
                logger.info(f"✓ {name}: PASSED ({duration:.2f}s)")
                return True
            else:
                self.results["checks_failed"] += 1
                self.results["check_results"].append({
                    "name": name,
                    "status": "FAIL",
                    "duration": duration,
                    "critical": critical
                })
                if critical:
                    self.results["critical_failures"].append(name)
                else:
                    self.results["warnings"].append(name)
                logger.error(f"✗ {name}: FAILED ({duration:.2f}s)")
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.results["checks_failed"] += 1
            self.results["check_results"].append({
                "name": name,
                "status": "ERROR",
                "duration": duration,
                "critical": critical,
                "error": str(e)
            })
            if critical:
                self.results["critical_failures"].append(f"{name}: {str(e)}")
            else:
                self.results["warnings"].append(f"{name}: {str(e)}")
            logger.error(f"✗ {name}: ERROR - {str(e)} ({duration:.2f}s)")
            return False
    
    def _check_data_fetcher_availability(self) -> None:
        """Check that the data fetcher is working correctly."""
        logger.info("Check 1: Data Fetcher Availability")
        
        # Test basic functionality
        self._run_check(
            name="Data fetcher initialization",
            check_func=lambda: self.fetcher is not None,
            critical=True
        )
        
        # Test getting available metrics
        self._run_check(
            name="Available metrics retrieval",
            check_func=lambda: len(self.fetcher.get_available_metrics()) > 0,
            critical=True
        )
    
    def _check_critical_metrics_availability(self) -> None:
        """Check that critical metrics are available."""
        logger.info("Check 2: Critical Metrics Availability")
        
        critical_metrics = ["FTPCT", "TSPCT", "THPAr", "FTr", "TRBPCT"]
        
        for metric in critical_metrics:
            self._run_check(
                name=f"Critical metric: {metric}",
                check_func=lambda m=metric: self._validate_metric_availability(m),
                critical=True
            )
    
    def _check_data_completeness(self) -> None:
        """Check that data is complete for key metrics."""
        logger.info("Check 3: Data Completeness")
        
        # Test with a few key metrics
        test_metrics = ["FTPCT", "TSPCT", "THPAr"]
        
        for metric in test_metrics:
            self._run_check(
                name=f"{metric} data completeness",
                check_func=lambda m=metric: self._validate_metric_completeness(m),
                critical=True
            )
    
    def _check_data_consistency(self) -> None:
        """Check that data values are consistent and reasonable."""
        logger.info("Check 4: Data Consistency")
        
        # Test percentage metrics are in valid range
        percentage_metrics = ["FTPCT", "TSPCT"]
        
        for metric in percentage_metrics:
            self._run_check(
                name=f"{metric} value consistency",
                check_func=lambda m=metric: self._validate_percentage_metric(m),
                critical=True
            )
    
    def _validate_metric_availability(self, metric: str) -> bool:
        """Validate that a metric is available."""
        try:
            data = self.fetcher.fetch_metric_data(metric, self.season)
            return data is not None and len(data) > 0
        except Exception as e:
            logger.error(f"Error validating {metric}: {e}")
            return False
    
    def _validate_metric_completeness(self, metric: str) -> bool:
        """Validate that a metric has sufficient data."""
        try:
            data = self.fetcher.fetch_metric_data(metric, self.season)
            if not data:
                return False
            
            # Check for reasonable number of players
            player_count = len(data)
            if player_count < 100:  # Expect at least 100 players
                logger.warning(f"Only {player_count} players found for {metric}")
                return False
            
            # Check for null/missing values
            null_count = sum(1 for value in data.values() if value is None)
            null_percentage = (null_count / player_count) * 100
            
            if null_percentage > 50:  # More than 50% null values
                logger.warning(f"{null_percentage:.1f}% null values for {metric}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating completeness for {metric}: {e}")
            return False
    
    def _validate_percentage_metric(self, metric: str) -> bool:
        """Validate that percentage metrics are in valid range (0-1)."""
        try:
            data = self.fetcher.fetch_metric_data(metric, self.season)
            if not data:
                return False
            
            invalid_count = 0
            for player_id, value in data.items():
                if value is not None:
                    try:
                        float_val = float(value)
                        if not (0 <= float_val <= 1):
                            invalid_count += 1
                    except (ValueError, TypeError):
                        invalid_count += 1
            
            invalid_percentage = (invalid_count / len(data)) * 100
            if invalid_percentage > 10:  # More than 10% invalid values
                logger.warning(f"{invalid_percentage:.1f}% invalid values for {metric}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating percentage metric {metric}: {e}")
            return False
    
    def _generate_verification_report(self) -> None:
        """Generate a detailed verification report."""
        report = {
            "verification_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "season": self.season,
            "summary": {
                "total_checks": self.results["total_checks"],
                "checks_passed": self.results["checks_passed"],
                "checks_failed": self.results["checks_failed"],
                "success_rate": self.results["success_rate"],
                "critical_failures": len(self.results["critical_failures"]),
                "warnings": len(self.results["warnings"])
            },
            "check_details": self.results["check_results"],
            "critical_failures": self.results["critical_failures"],
            "warnings": self.results["warnings"]
        }
        
        # Save report to file
        report_file = f"semantic_data_verification_corrected_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Verification report saved to {report_file}")

def main():
    """Main function to run the corrected semantic verification."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Corrected Semantic Data Verification")
    parser.add_argument("--season", default="2024-25", help="Season to verify (default: 2024-25)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    verifier = CorrectedSemanticDataVerifier(args.season)
    results = verifier.run_verification()
    
    if results["critical_failures"]:
        print(f"\n❌ VERIFICATION FAILED: {len(results['critical_failures'])} critical failures")
        sys.exit(1)
    else:
        print(f"\n✅ VERIFICATION PASSED: {results['success_rate']:.1f}% success rate")
        sys.exit(0)

if __name__ == "__main__":
    main()
