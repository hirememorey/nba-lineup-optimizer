#!/usr/bin/env python3
"""
Test Resumability Script

This script tests the resumability feature of populate_possessions.py
by running it for a short time, stopping it, and then resuming it.
"""

import time
import signal
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.nba_stats.scripts.populate_possessions import populate_possessions
from src.nba_stats.scripts.common_utils import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('resumability_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ResumabilityTester:
    """
    Tests the resumability feature of the possessions population script.
    """
    
    def __init__(self, season: str = "2024-25"):
        """Initialize the tester."""
        self.season = season
        self.interrupted = False
        self.test_results = {
            "initial_run": False,
            "resume_run": False,
            "data_consistency": False,
            "games_processed_initial": 0,
            "games_processed_resume": 0,
            "total_games_processed": 0
        }
    
    def test_resumability(self) -> bool:
        """
        Test the resumability feature by running, interrupting, and resuming.
        
        Returns:
            True if resumability works correctly, False otherwise
        """
        logger.info("Starting resumability test...")
        
        # Step 1: Check initial state
        initial_count = self._get_processed_games_count()
        logger.info(f"Initial processed games count: {initial_count}")
        
        # Step 2: Run for a short time then interrupt
        logger.info("Running initial population (will be interrupted after 30 seconds)...")
        self._run_with_timeout(30)  # Run for 30 seconds
        
        # Step 3: Check intermediate state
        intermediate_count = self._get_processed_games_count()
        self.test_results["games_processed_initial"] = intermediate_count - initial_count
        logger.info(f"Games processed in initial run: {self.test_results['games_processed_initial']}")
        
        if self.test_results["games_processed_initial"] > 0:
            self.test_results["initial_run"] = True
            logger.info("✓ Initial run processed some games")
        else:
            logger.warning("✗ Initial run did not process any games")
            return False
        
        # Step 4: Resume the process
        logger.info("Resuming population...")
        self._run_with_timeout(60)  # Run for 60 seconds
        
        # Step 5: Check final state
        final_count = self._get_processed_games_count()
        self.test_results["games_processed_resume"] = final_count - intermediate_count
        self.test_results["total_games_processed"] = final_count - initial_count
        logger.info(f"Games processed in resume run: {self.test_results['games_processed_resume']}")
        logger.info(f"Total games processed: {self.test_results['total_games_processed']}")
        
        if self.test_results["games_processed_resume"] > 0:
            self.test_results["resume_run"] = True
            logger.info("✓ Resume run processed additional games")
        else:
            logger.warning("✗ Resume run did not process any additional games")
        
        # Step 6: Verify data consistency
        self.test_results["data_consistency"] = self._verify_data_consistency()
        
        # Generate report
        self._generate_test_report()
        
        return (self.test_results["initial_run"] and 
                self.test_results["resume_run"] and 
                self.test_results["data_consistency"])
    
    def _run_with_timeout(self, timeout_seconds: int) -> None:
        """Run the population script with a timeout."""
        def timeout_handler(signum, frame):
            logger.info(f"Timeout reached ({timeout_seconds}s), stopping population...")
            self.interrupted = True
            raise KeyboardInterrupt("Timeout reached")
        
        # Set up signal handler for timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        
        try:
            populate_possessions(self.season)
            signal.alarm(0)  # Cancel the alarm
        except KeyboardInterrupt:
            signal.alarm(0)  # Cancel the alarm
            logger.info("Population interrupted (expected)")
        except Exception as e:
            signal.alarm(0)  # Cancel the alarm
            logger.error(f"Error during population: {e}")
            raise
    
    def _get_processed_games_count(self) -> int:
        """Get the count of processed games from the database."""
        conn = get_db_connection()
        if not conn:
            return 0
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT game_id) FROM Possessions")
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            logger.error(f"Error getting processed games count: {e}")
            return 0
        finally:
            conn.close()
    
    def _verify_data_consistency(self) -> bool:
        """Verify that the data in the database is consistent."""
        conn = get_db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Check for duplicate events
            cursor.execute("""
                SELECT game_id, event_num, COUNT(*) as count
                FROM Possessions 
                GROUP BY game_id, event_num 
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()
            
            if duplicates:
                logger.error(f"Found {len(duplicates)} duplicate events")
                return False
            
            # Check for missing required fields
            cursor.execute("""
                SELECT COUNT(*) FROM Possessions 
                WHERE game_id IS NULL OR event_num IS NULL
            """)
            missing_required = cursor.fetchone()[0]
            
            if missing_required > 0:
                logger.error(f"Found {missing_required} records with missing required fields")
                return False
            
            # Check for reasonable data ranges
            cursor.execute("""
                SELECT COUNT(*) FROM Possessions 
                WHERE period < 1 OR period > 4
            """)
            invalid_periods = cursor.fetchone()[0]
            
            if invalid_periods > 0:
                logger.error(f"Found {invalid_periods} records with invalid periods")
                return False
            
            logger.info("✓ Data consistency checks passed")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying data consistency: {e}")
            return False
        finally:
            conn.close()
    
    def _generate_test_report(self) -> None:
        """Generate a test report."""
        report_lines = []
        report_lines.append("# Resumability Test Report")
        report_lines.append(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Season: {self.season}")
        report_lines.append("")
        
        # Test results
        report_lines.append("## Test Results")
        report_lines.append(f"- Initial run successful: {'✓' if self.test_results['initial_run'] else '✗'}")
        report_lines.append(f"- Resume run successful: {'✓' if self.test_results['resume_run'] else '✗'}")
        report_lines.append(f"- Data consistency: {'✓' if self.test_results['data_consistency'] else '✗'}")
        report_lines.append("")
        
        # Processing statistics
        report_lines.append("## Processing Statistics")
        report_lines.append(f"- Games processed in initial run: {self.test_results['games_processed_initial']}")
        report_lines.append(f"- Games processed in resume run: {self.test_results['games_processed_resume']}")
        report_lines.append(f"- Total games processed: {self.test_results['total_games_processed']}")
        report_lines.append("")
        
        # Overall result
        overall_success = (self.test_results["initial_run"] and 
                          self.test_results["resume_run"] and 
                          self.test_results["data_consistency"])
        
        report_lines.append("## Overall Result")
        if overall_success:
            report_lines.append("✅ **RESUMABILITY TEST PASSED**")
            report_lines.append("The populate_possessions.py script correctly handles resumability.")
        else:
            report_lines.append("❌ **RESUMABILITY TEST FAILED**")
            report_lines.append("The populate_possessions.py script has issues with resumability.")
        
        # Save report
        report_content = "\n".join(report_lines)
        with open("resumability_test_report.md", "w") as f:
            f.write(report_content)
        
        logger.info("Test report generated: resumability_test_report.md")

def main():
    """Main entry point for the resumability test."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Resumability of populate_possessions.py")
    parser.add_argument("--season", default="2024-25", help="Season to test")
    parser.add_argument("--quick", action="store_true", help="Run quick test (shorter timeouts)")
    
    args = parser.parse_args()
    
    tester = ResumabilityTester(season=args.season)
    
    try:
        success = tester.test_resumability()
        
        if success:
            print("\n✅ Resumability test passed!")
            return 0
        else:
            print("\n❌ Resumability test failed!")
            return 1
            
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        print(f"\n❌ Test failed with exception: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
