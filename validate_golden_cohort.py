#!/usr/bin/env python3
"""
Golden Cohort Validation Script

This script performs deep, surgical checks on a predefined "Golden Cohort" of players
to validate cross-table consistency and data integrity. This addresses the pre-mortem
risk of subtle data corruption that could poison downstream analysis.

The Golden Cohort includes players representing known edge cases:
- A superstar (LeBron James)
- A rookie (Victor Wembanyama) 
- A player who was traded mid-season (James Harden)
- An international player (Luka Dončić)
- A journeyman role-player (Danny Green)
"""

import sqlite3
import logging
import json
from typing import Dict, List, Tuple, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('golden_cohort_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Golden Cohort Definition
GOLDEN_COHORT = {
    2544: "LeBron James (Superstar)",
    1630173: "Victor Wembanyama (Rookie)", 
    201935: "James Harden (Traded Mid-Season)",
    201142: "Luka Dončić (International)",
    201980: "Danny Green (Journeyman Role-Player)"
}

# Critical tables to check for consistency
CRITICAL_TABLES = [
    "PlayerSeasonRawStats",
    "PlayerSeasonAdvancedStats", 
    "PlayerSeasonDriveStats",
    "PlayerSeasonPostUpStats",
    "PlayerSeasonCatchAndShootStats",
    "PlayerSeasonPassingStats",
    "PlayerSeasonHustleStats",
    "PlayerSeasonReboundingStats",
    "PlayerSeasonShootingRangeStats",
    "PlayerSeasonShootingZoneStats",
    "PlayerSeasonTrackingTouchesStats",
    "PlayerSeasonElbowTouchStats",
    "PlayerSeasonPaintTouchStats",
    "PlayerSeasonOpponentShootingStats"
]

class GoldenCohortValidator:
    def __init__(self, db_path: str = "src/nba_stats/db/nba_stats.db"):
        self.db_path = db_path
        self.results = {
            "validation_timestamp": datetime.now().isoformat(),
            "cohort_players": GOLDEN_COHORT,
            "checks_performed": [],
            "overall_status": "PENDING",
            "critical_failures": [],
            "warnings": [],
            "summary": {}
        }
    
    def validate_cohort(self) -> Dict[str, Any]:
        """Run all validation checks on the Golden Cohort."""
        logger.info("Starting Golden Cohort Validation...")
        logger.info(f"Validating {len(GOLDEN_COHORT)} players across {len(CRITICAL_TABLES)} tables")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Check 1: Player Existence
                self._check_player_existence(conn)
                
                # Check 2: Season Consistency
                self._check_season_consistency(conn)
                
                # Check 3: Data Completeness
                self._check_data_completeness(conn)
                
                # Check 4: Value Reasonableness
                self._check_value_reasonableness(conn)
                
                # Check 5: Cross-Table Consistency
                self._check_cross_table_consistency(conn)
                
                # Generate summary
                self._generate_summary()
                
        except Exception as e:
            logger.error(f"Critical error during validation: {e}")
            self.results["critical_failures"].append(f"Database connection error: {str(e)}")
            self.results["overall_status"] = "FAILED"
        
        return self.results
    
    def _check_player_existence(self, conn: sqlite3.Connection):
        """Verify all Golden Cohort players exist in the database."""
        logger.info("Check 1: Verifying player existence...")
        
        check_result = {
            "check_name": "Player Existence",
            "status": "PASS",
            "details": {}
        }
        
        for player_id, player_name in GOLDEN_COHORT.items():
            cursor = conn.execute("SELECT player_id, player_name FROM Players WHERE player_id = ?", (player_id,))
            row = cursor.fetchone()
            
            if row:
                check_result["details"][str(player_id)] = {
                    "status": "EXISTS",
                    "name": row["player_name"],
                    "expected": player_name
                }
                logger.info(f"✓ {player_name} (ID: {player_id}) exists in database")
            else:
                check_result["status"] = "FAIL"
                check_result["details"][str(player_id)] = {
                    "status": "MISSING",
                    "expected": player_name
                }
                self.results["critical_failures"].append(f"Player {player_name} (ID: {player_id}) not found in database")
                logger.error(f"✗ {player_name} (ID: {player_id}) missing from database")
        
        self.results["checks_performed"].append(check_result)
    
    def _check_season_consistency(self, conn: sqlite3.Connection):
        """Verify season consistency across all tables for each player."""
        logger.info("Check 2: Verifying season consistency...")
        
        check_result = {
            "check_name": "Season Consistency",
            "status": "PASS", 
            "details": {}
        }
        
        for player_id, player_name in GOLDEN_COHORT.items():
            player_seasons = {}
            
            # Check each critical table for this player
            for table in CRITICAL_TABLES:
                try:
                    cursor = conn.execute(f"SELECT DISTINCT season FROM {table} WHERE player_id = ?", (player_id,))
                    seasons = [row["season"] for row in cursor.fetchall()]
                    player_seasons[table] = seasons
                except sqlite3.OperationalError:
                    # Table doesn't exist or has no season column
                    player_seasons[table] = []
            
            # Check for consistency
            all_seasons = []
            for seasons in player_seasons.values():
                all_seasons.extend(seasons)
            
            unique_seasons = list(set(all_seasons))
            
            if len(unique_seasons) <= 1:
                check_result["details"][str(player_id)] = {
                    "status": "CONSISTENT",
                    "seasons": unique_seasons,
                    "table_breakdown": player_seasons
                }
                logger.info(f"✓ {player_name}: Season consistency verified ({unique_seasons})")
            else:
                check_result["status"] = "FAIL"
                check_result["details"][str(player_id)] = {
                    "status": "INCONSISTENT",
                    "seasons": unique_seasons,
                    "table_breakdown": player_seasons
                }
                self.results["critical_failures"].append(
                    f"Player {player_name} has inconsistent seasons across tables: {unique_seasons}"
                )
                logger.error(f"✗ {player_name}: Season inconsistency detected ({unique_seasons})")
        
        self.results["checks_performed"].append(check_result)
    
    def _check_data_completeness(self, conn: sqlite3.Connection):
        """Check data completeness for each player across critical tables."""
        logger.info("Check 3: Verifying data completeness...")
        
        check_result = {
            "check_name": "Data Completeness",
            "status": "PASS",
            "details": {}
        }
        
        for player_id, player_name in GOLDEN_COHORT.items():
            table_coverage = {}
            
            for table in CRITICAL_TABLES:
                try:
                    cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table} WHERE player_id = ?", (player_id,))
                    count = cursor.fetchone()["count"]
                    table_coverage[table] = count > 0
                except sqlite3.OperationalError:
                    table_coverage[table] = False
            
            coverage_pct = (sum(table_coverage.values()) / len(CRITICAL_TABLES)) * 100
            
            if coverage_pct >= 80:  # Allow some missing data
                check_result["details"][str(player_id)] = {
                    "status": "ADEQUATE",
                    "coverage_percentage": coverage_pct,
                    "table_breakdown": table_coverage
                }
                logger.info(f"✓ {player_name}: {coverage_pct:.1f}% table coverage")
            else:
                check_result["status"] = "FAIL"
                check_result["details"][str(player_id)] = {
                    "status": "INADEQUATE", 
                    "coverage_percentage": coverage_pct,
                    "table_breakdown": table_coverage
                }
                self.results["critical_failures"].append(
                    f"Player {player_name} has inadequate data coverage: {coverage_pct:.1f}%"
                )
                logger.error(f"✗ {player_name}: Inadequate coverage ({coverage_pct:.1f}%)")
        
        self.results["checks_performed"].append(check_result)
    
    def _check_value_reasonableness(self, conn: sqlite3.Connection):
        """Check that key statistical values are within reasonable ranges."""
        logger.info("Check 4: Verifying value reasonableness...")
        
        check_result = {
            "check_name": "Value Reasonableness",
            "status": "PASS",
            "details": {}
        }
        
        # Define reasonable ranges for key metrics
        reasonable_ranges = {
            "FTPCT": (0.0, 1.0),  # Free throw percentage
            "TSPCT": (0.0, 1.0),  # True shooting percentage
            "THPAr": (0.0, 1.0),  # Three-point attempt rate
            "FTr": (0.0, 1.0),    # Free throw rate
            "TRBPCT": (0.0, 0.5), # Total rebound percentage
            "ASTPCT": (0.0, 0.5), # Assist percentage
        }
        
        for player_id, player_name in GOLDEN_COHORT.items():
            player_issues = []
            
            # Check basic stats
            try:
                cursor = conn.execute("""
                    SELECT FTPCT, TSPCT, THPAr, FTr, TRBPCT, ASTPCT 
                    FROM PlayerSeasonRawStats 
                    WHERE player_id = ? AND season = '2024-25'
                """, (player_id,))
                row = cursor.fetchone()
                
                if row:
                    for metric, (min_val, max_val) in reasonable_ranges.items():
                        value = row[metric]
                        if value is not None and (value < min_val or value > max_val):
                            player_issues.append(f"{metric}: {value} (expected {min_val}-{max_val})")
                
            except sqlite3.OperationalError:
                player_issues.append("Could not access PlayerSeasonRawStats table")
            
            if player_issues:
                check_result["status"] = "FAIL"
                check_result["details"][str(player_id)] = {
                    "status": "UNREASONABLE",
                    "issues": player_issues
                }
                self.results["warnings"].append(f"Player {player_name} has unreasonable values: {player_issues}")
                logger.warning(f"⚠ {player_name}: Unreasonable values detected: {player_issues}")
            else:
                check_result["details"][str(player_id)] = {
                    "status": "REASONABLE",
                    "issues": []
                }
                logger.info(f"✓ {player_name}: All values within reasonable ranges")
        
        self.results["checks_performed"].append(check_result)
    
    def _check_cross_table_consistency(self, conn: sqlite3.Connection):
        """Check for consistency between related tables."""
        logger.info("Check 5: Verifying cross-table consistency...")
        
        check_result = {
            "check_name": "Cross-Table Consistency",
            "status": "PASS",
            "details": {}
        }
        
        for player_id, player_name in GOLDEN_COHORT.items():
            consistency_issues = []
            
            # Check that if a player has data in one table, they have data in related tables
            try:
                # Check basic vs advanced stats consistency
                basic_cursor = conn.execute("""
                    SELECT COUNT(*) as count FROM PlayerSeasonRawStats 
                    WHERE player_id = ? AND season = '2024-25'
                """, (player_id,))
                basic_count = basic_cursor.fetchone()["count"]
                
                advanced_cursor = conn.execute("""
                    SELECT COUNT(*) as count FROM PlayerSeasonAdvancedStats 
                    WHERE player_id = ? AND season = '2024-25'
                """, (player_id,))
                advanced_count = advanced_cursor.fetchone()["count"]
                
                if basic_count > 0 and advanced_count == 0:
                    consistency_issues.append("Has basic stats but missing advanced stats")
                elif basic_count == 0 and advanced_count > 0:
                    consistency_issues.append("Has advanced stats but missing basic stats")
                
            except sqlite3.OperationalError as e:
                consistency_issues.append(f"Could not check basic/advanced consistency: {e}")
            
            if consistency_issues:
                check_result["status"] = "FAIL"
                check_result["details"][str(player_id)] = {
                    "status": "INCONSISTENT",
                    "issues": consistency_issues
                }
                self.results["warnings"].append(f"Player {player_name} has cross-table inconsistencies: {consistency_issues}")
                logger.warning(f"⚠ {player_name}: Cross-table inconsistencies: {consistency_issues}")
            else:
                check_result["details"][str(player_id)] = {
                    "status": "CONSISTENT",
                    "issues": []
                }
                logger.info(f"✓ {player_name}: Cross-table consistency verified")
        
        self.results["checks_performed"].append(check_result)
    
    def _generate_summary(self):
        """Generate overall summary of validation results."""
        total_checks = len(self.results["checks_performed"])
        failed_checks = sum(1 for check in self.results["checks_performed"] if check["status"] == "FAIL")
        
        if failed_checks == 0 and len(self.results["critical_failures"]) == 0:
            self.results["overall_status"] = "PASS"
        elif len(self.results["critical_failures"]) > 0:
            self.results["overall_status"] = "CRITICAL_FAILURE"
        else:
            self.results["overall_status"] = "WARNING"
        
        self.results["summary"] = {
            "total_checks": total_checks,
            "passed_checks": total_checks - failed_checks,
            "failed_checks": failed_checks,
            "critical_failures": len(self.results["critical_failures"]),
            "warnings": len(self.results["warnings"]),
            "cohort_size": len(GOLDEN_COHORT),
            "tables_checked": len(CRITICAL_TABLES)
        }
        
        logger.info(f"Validation Summary: {total_checks - failed_checks}/{total_checks} checks passed")
        logger.info(f"Critical failures: {len(self.results['critical_failures'])}")
        logger.info(f"Warnings: {len(self.results['warnings'])}")
    
    def save_results(self, filename: str = "golden_cohort_validation_results.json"):
        """Save validation results to JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Results saved to {filename}")

def main():
    """Main execution function."""
    validator = GoldenCohortValidator()
    results = validator.validate_cohort()
    validator.save_results()
    
    # Print final status
    if results["overall_status"] == "PASS":
        print("✅ GOLDEN COHORT VALIDATION PASSED")
        print("All critical data integrity checks passed. The dataset is ready for analysis.")
    elif results["overall_status"] == "WARNING":
        print("⚠️  GOLDEN COHORT VALIDATION PASSED WITH WARNINGS")
        print("Data integrity verified but some warnings detected. Review the log for details.")
    else:
        print("❌ GOLDEN COHORT VALIDATION FAILED")
        print("Critical data integrity issues detected. Review the log and fix issues before proceeding.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
