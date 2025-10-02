#!/usr/bin/env python3
"""
Comprehensive Data Sanity Check

This script performs a thorough analysis of all data to identify any issues
that could block the next phase of the project (player archetype analysis).
"""

import sqlite3
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_sanity_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ComprehensiveDataSanityChecker:
    """Comprehensive data sanity checker for NBA lineup optimizer."""
    
    def __init__(self, db_path: str = "src/nba_stats/db/nba_stats.db"):
        self.db_path = db_path
        self.results = {
            "critical_issues": [],
            "warnings": [],
            "data_summary": {},
            "analysis_readiness": True
        }
    
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """Run all sanity checks."""
        logger.info("Starting comprehensive data sanity check...")
        
        # Basic database checks
        self._check_database_connectivity()
        self._check_table_structure()
        self._check_data_completeness()
        self._check_data_quality()
        self._check_analysis_readiness()
        self._check_canonical_metrics()
        self._check_data_consistency()
        
        # Generate report
        self._generate_report()
        
        return self.results
    
    def _check_database_connectivity(self):
        """Check basic database connectivity and structure."""
        logger.info("Checking database connectivity...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if database exists and is accessible
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = [
                    'Players', 'Teams', 'PlayerSeasonRawStats', 
                    'PlayerSeasonAdvancedStats', 'PlayerSalaries'
                ]
                
                missing_tables = set(required_tables) - set(tables)
                if missing_tables:
                    self.results["critical_issues"].append(f"Missing required tables: {missing_tables}")
                    self.results["analysis_readiness"] = False
                else:
                    logger.info("✅ All required tables present")
                    
        except Exception as e:
            self.results["critical_issues"].append(f"Database connectivity failed: {str(e)}")
            self.results["analysis_readiness"] = False
    
    def _check_table_structure(self):
        """Check table structure and column completeness."""
        logger.info("Checking table structure...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check PlayerSeasonRawStats structure
                cursor = conn.execute("PRAGMA table_info(PlayerSeasonRawStats)")
                raw_stats_columns = [row[1] for row in cursor.fetchall()]
                
                # Check PlayerSeasonAdvancedStats structure
                cursor = conn.execute("PRAGMA table_info(PlayerSeasonAdvancedStats)")
                advanced_stats_columns = [row[1] for row in cursor.fetchall()]
                
                # Critical columns for analysis
                critical_raw_columns = [
                    'player_id', 'season', 'team_id', 'points', 'field_goals_made',
                    'field_goals_attempted', 'three_pointers_made', 'three_pointers_attempted',
                    'free_throws_made', 'free_throws_attempted', 'assists', 'total_rebounds',
                    'steals', 'blocks', 'turnovers', 'minutes_played'
                ]
                
                critical_advanced_columns = [
                    'player_id', 'season', 'team_id', 'offensive_rating', 'defensive_rating',
                    'net_rating', 'usage_percentage', 'true_shooting_percentage',
                    'effective_field_goal_percentage', 'assist_percentage', 'rebound_percentage'
                ]
                
                missing_raw = set(critical_raw_columns) - set(raw_stats_columns)
                missing_advanced = set(critical_advanced_columns) - set(advanced_stats_columns)
                
                if missing_raw:
                    self.results["critical_issues"].append(f"Missing critical columns in PlayerSeasonRawStats: {missing_raw}")
                    self.results["analysis_readiness"] = False
                
                if missing_advanced:
                    self.results["critical_issues"].append(f"Missing critical columns in PlayerSeasonAdvancedStats: {missing_advanced}")
                    self.results["analysis_readiness"] = False
                
                if not missing_raw and not missing_advanced:
                    logger.info("✅ All critical columns present")
                    
        except Exception as e:
            self.results["critical_issues"].append(f"Table structure check failed: {str(e)}")
            self.results["analysis_readiness"] = False
    
    def _check_data_completeness(self):
        """Check data completeness and coverage."""
        logger.info("Checking data completeness...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get row counts
                try:
                    # First check if table exists and has the right columns
                    cursor = conn.execute("PRAGMA table_info(PlayerSeasonRawStats)")
                    columns = [row[1] for row in cursor.fetchall()]
                    logger.info(f"PlayerSeasonRawStats columns: {columns}")
                    
                    # Test the query step by step
                    logger.info("Testing basic query...")
                    cursor = conn.execute("SELECT COUNT(*) FROM PlayerSeasonRawStats")
                    total_count = cursor.fetchone()[0]
                    logger.info(f"Total rows in PlayerSeasonRawStats: {total_count}")
                    
                    logger.info("Testing season filter...")
                    cursor = conn.execute("SELECT COUNT(*) FROM PlayerSeasonRawStats WHERE season = '2024-25'")
                    raw_stats_count = cursor.fetchone()[0]
                    logger.info(f"Rows with season '2024-25': {raw_stats_count}")
                except Exception as e:
                    logger.error(f"Error querying raw stats: {str(e)}")
                    raise e
                
                cursor = conn.execute("SELECT COUNT(*) FROM PlayerSeasonAdvancedStats WHERE season = '2024-25'")
                advanced_stats_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM Players")
                players_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM Teams")
                teams_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM PlayerSalaries WHERE season_id = '2024-25'")
                salaries_count = cursor.fetchone()[0]
                
                self.results["data_summary"] = {
                    "raw_stats_players": raw_stats_count,
                    "advanced_stats_players": advanced_stats_count,
                    "total_players": players_count,
                    "total_teams": teams_count,
                    "players_with_salaries": salaries_count
                }
                
                # Check for minimum data requirements
                if raw_stats_count < 100:
                    self.results["critical_issues"].append(f"Insufficient raw stats data: {raw_stats_count} players (minimum 100 required)")
                    self.results["analysis_readiness"] = False
                
                if advanced_stats_count < 100:
                    self.results["critical_issues"].append(f"Insufficient advanced stats data: {advanced_stats_count} players (minimum 100 required)")
                    self.results["analysis_readiness"] = False
                
                if players_count < 100:
                    self.results["critical_issues"].append(f"Insufficient player data: {players_count} players (minimum 100 required)")
                    self.results["analysis_readiness"] = False
                
                # Check data coverage ratios
                raw_coverage = (raw_stats_count / players_count * 100) if players_count > 0 else 0
                advanced_coverage = (advanced_stats_count / players_count * 100) if players_count > 0 else 0
                
                if raw_coverage < 50:
                    self.results["warnings"].append(f"Low raw stats coverage: {raw_coverage:.1f}% of players have raw stats")
                
                if advanced_coverage < 50:
                    self.results["warnings"].append(f"Low advanced stats coverage: {advanced_coverage:.1f}% of players have advanced stats")
                
                logger.info(f"✅ Data completeness check complete: {raw_stats_count} raw stats, {advanced_stats_count} advanced stats")
                
        except Exception as e:
            logger.error(f"Data completeness check failed: {str(e)}")
            self.results["critical_issues"].append(f"Data completeness check failed: {str(e)}")
            self.results["analysis_readiness"] = False
    
    def _check_data_quality(self):
        """Check data quality and logical consistency."""
        logger.info("Checking data quality...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check for logical inconsistencies in raw stats
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM PlayerSeasonRawStats 
                    WHERE field_goals_made > field_goals_attempted
                """)
                illogical_fg = cursor.fetchone()[0]
                
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM PlayerSeasonRawStats 
                    WHERE three_pointers_made > three_pointers_attempted
                """)
                illogical_3p = cursor.fetchone()[0]
                
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM PlayerSeasonRawStats 
                    WHERE free_throws_made > free_throws_attempted
                """)
                illogical_ft = cursor.fetchone()[0]
                
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM PlayerSeasonRawStats 
                    WHERE points < 0 OR assists < 0 OR total_rebounds < 0
                """)
                negative_stats = cursor.fetchone()[0]
                
                # Check for NULL values in critical columns
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM PlayerSeasonRawStats 
                    WHERE player_id IS NULL OR season IS NULL OR team_id IS NULL
                """)
                null_critical = cursor.fetchone()[0]
                
                if illogical_fg > 0:
                    self.results["critical_issues"].append(f"Illogical field goal data: {illogical_fg} records with FGM > FGA")
                    self.results["analysis_readiness"] = False
                
                if illogical_3p > 0:
                    self.results["critical_issues"].append(f"Illogical 3-point data: {illogical_3p} records with 3PM > 3PA")
                    self.results["analysis_readiness"] = False
                
                if illogical_ft > 0:
                    self.results["critical_issues"].append(f"Illogical free throw data: {illogical_ft} records with FTM > FTA")
                    self.results["analysis_readiness"] = False
                
                if negative_stats > 0:
                    self.results["critical_issues"].append(f"Negative statistics: {negative_stats} records with negative values")
                    self.results["analysis_readiness"] = False
                
                if null_critical > 0:
                    self.results["critical_issues"].append(f"NULL critical values: {null_critical} records with NULL player_id, season, or team_id")
                    self.results["analysis_readiness"] = False
                
                if all(x == 0 for x in [illogical_fg, illogical_3p, illogical_ft, negative_stats, null_critical]):
                    logger.info("✅ Data quality checks passed")
                
        except Exception as e:
            self.results["critical_issues"].append(f"Data quality check failed: {str(e)}")
            self.results["analysis_readiness"] = False
    
    def _check_analysis_readiness(self):
        """Check if data is ready for player archetype analysis."""
        logger.info("Checking analysis readiness...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if we have enough data for clustering
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM PlayerSeasonRawStats 
                    WHERE season = '2024-25' 
                    AND minutes_played > 10  -- Players with meaningful minutes
                """)
                meaningful_players = cursor.fetchone()[0]
                
                if meaningful_players < 50:
                    self.results["critical_issues"].append(f"Insufficient players for clustering: {meaningful_players} players with >10 minutes (minimum 50 required)")
                    self.results["analysis_readiness"] = False
                
                # Check for data diversity (different teams, positions)
                cursor = conn.execute("""
                    SELECT COUNT(DISTINCT team_id) FROM PlayerSeasonRawStats 
                    WHERE season = '2024-25' AND minutes_played > 10
                """)
                diverse_teams = cursor.fetchone()[0]
                
                if diverse_teams < 10:
                    self.results["warnings"].append(f"Low team diversity: only {diverse_teams} teams represented")
                
                # Check for statistical variance (needed for meaningful clustering)
                cursor = conn.execute("""
                    SELECT 
                        COUNT(DISTINCT points) as unique_points,
                        COUNT(DISTINCT assists) as unique_assists,
                        COUNT(DISTINCT total_rebounds) as unique_rebounds
                    FROM PlayerSeasonRawStats 
                    WHERE season = '2024-25' AND minutes_played > 10
                """)
                variance_data = cursor.fetchone()
                
                if variance_data[0] < 20:  # Less than 20 unique point values
                    self.results["warnings"].append("Low statistical variance in points - clustering may be less effective")
                
                if variance_data[1] < 15:  # Less than 15 unique assist values
                    self.results["warnings"].append("Low statistical variance in assists - clustering may be less effective")
                
                if variance_data[2] < 15:  # Less than 15 unique rebound values
                    self.results["warnings"].append("Low statistical variance in rebounds - clustering may be less effective")
                
                logger.info(f"✅ Analysis readiness check complete: {meaningful_players} meaningful players, {diverse_teams} teams")
                
        except Exception as e:
            self.results["critical_issues"].append(f"Analysis readiness check failed: {str(e)}")
            self.results["analysis_readiness"] = False
    
    def _check_canonical_metrics(self):
        """Check availability of canonical metrics from the source paper."""
        logger.info("Checking canonical metrics availability...")
        
        # Load canonical metrics from the project
        try:
            from canonical_metrics import CANONICAL_48_METRICS
            from definitive_metric_mapping import get_available_metrics, get_missing_metrics
            
            available_metrics = get_available_metrics()
            missing_metrics = get_missing_metrics()
            
            self.results["data_summary"]["canonical_metrics"] = {
                "total": len(CANONICAL_48_METRICS),
                "available": len(available_metrics),
                "missing": len(missing_metrics),
                "coverage_pct": (len(available_metrics) / len(CANONICAL_48_METRICS)) * 100
            }
            
            if len(missing_metrics) > 10:  # More than 10 missing metrics
                self.results["warnings"].append(f"Many canonical metrics missing: {len(missing_metrics)} out of {len(CANONICAL_48_METRICS)}")
            
            if len(available_metrics) < 30:  # Less than 30 available metrics
                self.results["critical_issues"].append(f"Insufficient canonical metrics: only {len(available_metrics)} available (minimum 30 required)")
                self.results["analysis_readiness"] = False
            
            logger.info(f"✅ Canonical metrics check: {len(available_metrics)}/{len(CANONICAL_48_METRICS)} available ({self.results['data_summary']['canonical_metrics']['coverage_pct']:.1f}%)")
            
        except ImportError as e:
            self.results["warnings"].append(f"Could not load canonical metrics: {str(e)}")
        except Exception as e:
            self.results["critical_issues"].append(f"Canonical metrics check failed: {str(e)}")
            self.results["analysis_readiness"] = False
    
    def _check_data_consistency(self):
        """Check data consistency across tables."""
        logger.info("Checking data consistency...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check for orphaned records
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM PlayerSeasonRawStats psr
                    LEFT JOIN Players p ON psr.player_id = p.player_id
                    WHERE p.player_id IS NULL
                """)
                orphaned_raw = cursor.fetchone()[0]
                
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM PlayerSeasonAdvancedStats pas
                    LEFT JOIN Players p ON pas.player_id = p.player_id
                    WHERE p.player_id IS NULL
                """)
                orphaned_advanced = cursor.fetchone()[0]
                
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM PlayerSeasonRawStats psr
                    LEFT JOIN Teams t ON psr.team_id = t.team_id
                    WHERE t.team_id IS NULL
                """)
                orphaned_teams_raw = cursor.fetchone()[0]
                
                if orphaned_raw > 0:
                    self.results["critical_issues"].append(f"Orphaned raw stats records: {orphaned_raw} records without corresponding players")
                    self.results["analysis_readiness"] = False
                
                if orphaned_advanced > 0:
                    self.results["critical_issues"].append(f"Orphaned advanced stats records: {orphaned_advanced} records without corresponding players")
                    self.results["analysis_readiness"] = False
                
                if orphaned_teams_raw > 0:
                    self.results["critical_issues"].append(f"Orphaned team references: {orphaned_teams_raw} raw stats records without corresponding teams")
                    self.results["analysis_readiness"] = False
                
                if orphaned_raw == 0 and orphaned_advanced == 0 and orphaned_teams_raw == 0:
                    logger.info("✅ No orphaned records found")
                
        except Exception as e:
            self.results["critical_issues"].append(f"Data consistency check failed: {str(e)}")
            self.results["analysis_readiness"] = False
    
    def _generate_report(self):
        """Generate comprehensive report."""
        report_path = Path("comprehensive_sanity_report.md")
        
        with open(report_path, "w") as f:
            f.write("# Comprehensive Data Sanity Check Report\n\n")
            f.write(f"**Database:** `{self.db_path}`\n")
            f.write(f"**Timestamp:** {pd.Timestamp.now().isoformat()}\n\n")
            
            # Summary
            f.write("## Executive Summary\n\n")
            if self.results["analysis_readiness"]:
                f.write("✅ **READY FOR NEXT PHASE** - All critical checks passed\n\n")
            else:
                f.write("❌ **NOT READY FOR NEXT PHASE** - Critical issues found\n\n")
            
            # Data summary
            f.write("## Data Summary\n\n")
            summary = self.results["data_summary"]
            for key, value in summary.items():
                f.write(f"- **{key.replace('_', ' ').title()}:** {value}\n")
            f.write("\n")
            
            # Critical issues
            if self.results["critical_issues"]:
                f.write("## Critical Issues (Blocking Next Phase)\n\n")
                for i, issue in enumerate(self.results["critical_issues"], 1):
                    f.write(f"{i}. {issue}\n")
                f.write("\n")
            else:
                f.write("## Critical Issues\n\n✅ No critical issues found\n\n")
            
            # Warnings
            if self.results["warnings"]:
                f.write("## Warnings (Non-blocking)\n\n")
                for i, warning in enumerate(self.results["warnings"], 1):
                    f.write(f"{i}. {warning}\n")
                f.write("\n")
            else:
                f.write("## Warnings\n\n✅ No warnings\n\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            if self.results["analysis_readiness"]:
                f.write("✅ **Proceed with player archetype analysis**\n")
                f.write("- Data quality is sufficient for clustering\n")
                f.write("- All critical metrics are available\n")
                f.write("- No blocking issues identified\n")
            else:
                f.write("❌ **Address critical issues before proceeding**\n")
                f.write("- Fix all critical issues listed above\n")
                f.write("- Re-run this sanity check\n")
                f.write("- Ensure data quality meets minimum requirements\n")
        
        logger.info(f"Comprehensive report generated: {report_path}")


def main():
    """Main entry point."""
    checker = ComprehensiveDataSanityChecker()
    results = checker.run_comprehensive_check()
    
    # Print summary
    print("\n" + "="*60)
    print("COMPREHENSIVE DATA SANITY CHECK SUMMARY")
    print("="*60)
    
    if results["analysis_readiness"]:
        print("✅ STATUS: READY FOR NEXT PHASE")
    else:
        print("❌ STATUS: NOT READY - CRITICAL ISSUES FOUND")
    
    print(f"\nCritical Issues: {len(results['critical_issues'])}")
    print(f"Warnings: {len(results['warnings'])}")
    
    if results["critical_issues"]:
        print("\n🚨 CRITICAL ISSUES:")
        for i, issue in enumerate(results["critical_issues"], 1):
            print(f"  {i}. {issue}")
    
    if results["warnings"]:
        print("\n⚠️  WARNINGS:")
        for i, warning in enumerate(results["warnings"], 1):
            print(f"  {i}. {warning}")
    
    print(f"\n📊 DATA SUMMARY:")
    for key, value in results["data_summary"].items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n📄 Full report: comprehensive_sanity_report.md")
    print("="*60)


if __name__ == "__main__":
    main()
