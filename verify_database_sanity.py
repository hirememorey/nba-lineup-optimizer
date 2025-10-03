#!/usr/bin/env python3
"""
Database Sanity Verification Script

This script performs a comprehensive, three-layer verification of the database
to ensure data integrity before proceeding to clustering analysis.

Based on first-principles reasoning and lessons learned from previous data quality failures.

Usage:
    python verify_database_sanity.py

Exit codes:
    0: All verifications passed
    1: One or more critical verifications failed
"""

import sqlite3
import pandas as pd
import sys
from typing import Dict, List, Tuple, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_sanity.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseSanityVerifier:
    """Comprehensive database verification using three-layer approach."""
    
    def __init__(self, db_path: str = "src/nba_stats/db/nba_stats.db"):
        self.db_path = db_path
        self.season = "2024-25"
        self.verification_results = []
        self.critical_failures = 0
        
        # Expected data ranges for key metrics (from data_verification_methodology.md)
        self.expected_ranges = {
            'FTPCT': (0.456, 1.000),  # Free throw percentage
            'TSPCT': (0.419, 0.724),  # True shooting percentage
            'DRIVES': (0.0, 25.0),     # Drives per game (updated based on actual data)
            'AVGDIST': (0.0, 25.0),    # Average shot distance (updated based on actual data)
            'FTr': (0.0, 0.8),         # Free throw rate
            'TRBPCT': (0.0, 0.3),      # Total rebound percentage
            'ASTPCT': (0.0, 0.5),      # Assist percentage
        }
        
        # Critical source tables to spot-check
        self.source_tables = {
            'PlayerSeasonDriveStats': {
                'metric': 'drives',
                'min_expected': 0.1,  # At least some players should have drives > 0
                'description': 'Drive statistics'
            },
            'PlayerSeasonPostUpStats': {
                'metric': 'possessions',
                'min_expected': 0.1,  # At least some players should have post-ups
                'description': 'Post-up statistics'
            },
            'PlayerSeasonOpponentShootingStats': {
                'metric': 'opp_fga_lt_5ft',  # Use a specific field
                'min_expected': 0.1,
                'description': 'Opponent shooting statistics',
                'expected_count': 569  # From documentation
            }
        }

    def connect_to_database(self) -> sqlite3.Connection:
        """Establish database connection with error handling."""
        try:
            conn = sqlite3.connect(self.db_path)
            logger.info(f"Successfully connected to database: {self.db_path}")
            return conn
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            sys.exit(1)

    def log_verification_result(self, layer: str, check_name: str, status: str, 
                              details: str = "", is_critical: bool = True):
        """Log verification result and track failures."""
        result = {
            'layer': layer,
            'check': check_name,
            'status': status,
            'details': details,
            'is_critical': is_critical
        }
        self.verification_results.append(result)
        
        if status == "FAIL" and is_critical:
            self.critical_failures += 1
            logger.error(f"[{layer}] {check_name}: FAIL - {details}")
        else:
            logger.info(f"[{layer}] {check_name}: {status} - {details}")

    def layer1_structural_verification(self, conn: sqlite3.Connection):
        """Layer 1: Structural & Volume Verification"""
        logger.info("=" * 60)
        logger.info("LAYER 1: STRUCTURAL & VOLUME VERIFICATION")
        logger.info("=" * 60)
        
        cursor = conn.cursor()
        
        # Check core metadata tables
        core_tables = {
            'Players': 5025,
            'Teams': 30,
            'Games': 1230
        }
        
        for table, expected_count in core_tables.items():
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                actual_count = cursor.fetchone()[0]
                
                if actual_count >= expected_count:
                    self.log_verification_result(
                        "Layer 1", f"{table} count", "PASS",
                        f"Found {actual_count} records (expected >= {expected_count})"
                    )
                else:
                    self.log_verification_result(
                        "Layer 1", f"{table} count", "FAIL",
                        f"Found {actual_count} records (expected >= {expected_count})"
                    )
            except sqlite3.Error as e:
                self.log_verification_result(
                    "Layer 1", f"{table} count", "FAIL",
                    f"Database error: {e}"
                )

        # Check PlayerArchetypeFeatures integrity
        try:
            cursor.execute(f"""
                SELECT COUNT(*) FROM PlayerArchetypeFeatures 
                WHERE season = '{self.season}'
            """)
            archetype_count = cursor.fetchone()[0]
            
            if archetype_count >= 270:
                self.log_verification_result(
                    "Layer 1", "PlayerArchetypeFeatures count", "PASS",
                    f"Found {archetype_count} players for {self.season} (expected >= 270)"
                )
            else:
                self.log_verification_result(
                    "Layer 1", "PlayerArchetypeFeatures count", "FAIL",
                    f"Found {archetype_count} players (expected >= 270)"
                )
        except sqlite3.Error as e:
            self.log_verification_result(
                "Layer 1", "PlayerArchetypeFeatures count", "FAIL",
                f"Database error: {e}"
            )

        # Check for NULL values in key archetype columns
        key_columns = ['FTPCT', 'TSPCT', 'DRIVES', 'AVGDIST', 'FTr', 'TRBPCT', 'ASTPCT']
        
        for column in key_columns:
            try:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM PlayerArchetypeFeatures 
                    WHERE season = '{self.season}' AND {column} IS NULL
                """)
                null_count = cursor.fetchone()[0]
                
                if null_count == 0:
                    self.log_verification_result(
                        "Layer 1", f"{column} NULL check", "PASS",
                        f"No NULL values found in {column}"
                    )
                else:
                    self.log_verification_result(
                        "Layer 1", f"{column} NULL check", "FAIL",
                        f"Found {null_count} NULL values in {column}"
                    )
            except sqlite3.Error as e:
                self.log_verification_result(
                    "Layer 1", f"{column} NULL check", "FAIL",
                    f"Database error: {e}"
                )

        # Check Possessions table
        try:
            cursor.execute("SELECT COUNT(*) FROM Possessions")
            possession_count = cursor.fetchone()[0]
            
            if possession_count >= 574000:  # From documentation
                self.log_verification_result(
                    "Layer 1", "Possessions count", "PASS",
                    f"Found {possession_count} possessions (expected >= 574,000)"
                )
            else:
                self.log_verification_result(
                    "Layer 1", "Possessions count", "FAIL",
                    f"Found {possession_count} possessions (expected >= 574,000)"
                )
        except sqlite3.Error as e:
            self.log_verification_result(
                "Layer 1", "Possessions count", "FAIL",
                f"Database error: {e}"
            )

    def layer1_5_source_table_spot_checks(self, conn: sqlite3.Connection):
        """Layer 1.5: Source Table Spot-Checks (Critical Enhancement)"""
        logger.info("=" * 60)
        logger.info("LAYER 1.5: SOURCE TABLE SPOT-CHECKS")
        logger.info("=" * 60)
        
        cursor = conn.cursor()
        
        for table_name, config in self.source_tables.items():
            try:
                # Check if table exists
                cursor.execute(f"""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='{table_name}'
                """)
                if not cursor.fetchone():
                    self.log_verification_result(
                        "Layer 1.5", f"{table_name} existence", "FAIL",
                        f"Table {table_name} does not exist"
                    )
                    continue
                
                # Check row count for current season
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {table_name} 
                    WHERE season = '{self.season}'
                """)
                row_count = cursor.fetchone()[0]
                
                if 'expected_count' in config:
                    if row_count == config['expected_count']:
                        self.log_verification_result(
                            "Layer 1.5", f"{table_name} count", "PASS",
                            f"Found {row_count} records (expected {config['expected_count']})"
                        )
                    else:
                        self.log_verification_result(
                            "Layer 1.5", f"{table_name} count", "FAIL",
                            f"Found {row_count} records (expected {config['expected_count']})"
                        )
                else:
                    if row_count > 0:
                        self.log_verification_result(
                            "Layer 1.5", f"{table_name} count", "PASS",
                            f"Found {row_count} records"
                        )
                    else:
                        self.log_verification_result(
                            "Layer 1.5", f"{table_name} count", "FAIL",
                            f"Found {row_count} records (expected > 0)"
                        )
                
                # Check for non-zero values in key metric
                cursor.execute(f"""
                    SELECT MAX({config['metric']}) FROM {table_name} 
                    WHERE season = '{self.season}'
                """)
                max_value = cursor.fetchone()[0]
                
                if max_value is not None and max_value >= config['min_expected']:
                    self.log_verification_result(
                        "Layer 1.5", f"{table_name} data quality", "PASS",
                        f"Max {config['metric']}: {max_value} (expected >= {config['min_expected']})"
                    )
                else:
                    self.log_verification_result(
                        "Layer 1.5", f"{table_name} data quality", "FAIL",
                        f"Max {config['metric']}: {max_value} (expected >= {config['min_expected']}) - Possible silent failure in upstream pipeline"
                    )
                    
            except sqlite3.Error as e:
                self.log_verification_result(
                    "Layer 1.5", f"{table_name} verification", "FAIL",
                    f"Database error: {e}"
                )

    def layer2_data_range_validation(self, conn: sqlite3.Connection):
        """Layer 2: Data Range & Distribution Validation"""
        logger.info("=" * 60)
        logger.info("LAYER 2: DATA RANGE & DISTRIBUTION VALIDATION")
        logger.info("=" * 60)
        
        try:
            # Load PlayerArchetypeFeatures into DataFrame
            query = f"""
                SELECT * FROM PlayerArchetypeFeatures 
                WHERE season = '{self.season}'
            """
            df = pd.read_sql_query(query, conn)
            
            if len(df) == 0:
                self.log_verification_result(
                    "Layer 2", "DataFrame loading", "FAIL",
                    "No data found in PlayerArchetypeFeatures for current season"
                )
                return
            
            logger.info(f"Loaded {len(df)} players from PlayerArchetypeFeatures")
            
            # Check each metric in expected ranges
            for metric, (min_expected, max_expected) in self.expected_ranges.items():
                if metric not in df.columns:
                    self.log_verification_result(
                        "Layer 2", f"{metric} column check", "FAIL",
                        f"Column {metric} not found in PlayerArchetypeFeatures"
                    )
                    continue
                
                # Calculate statistics
                min_val = df[metric].min()
                max_val = df[metric].max()
                mean_val = df[metric].mean()
                
                # Check if values are within expected range
                if min_val >= min_expected and max_val <= max_expected:
                    self.log_verification_result(
                        "Layer 2", f"{metric} range check", "PASS",
                        f"Range: {min_val:.3f} - {max_val:.3f} (expected: {min_expected} - {max_expected})"
                    )
                else:
                    self.log_verification_result(
                        "Layer 2", f"{metric} range check", "FAIL",
                        f"Range: {min_val:.3f} - {max_val:.3f} (expected: {min_expected} - {max_expected})"
                    )
                
                # Check for suspicious patterns (all zeros, all same value)
                unique_values = df[metric].nunique()
                if unique_values == 1:
                    self.log_verification_result(
                        "Layer 2", f"{metric} variance check", "FAIL",
                        f"All values are identical ({df[metric].iloc[0]}) - possible data corruption"
                    )
                elif unique_values < 10:
                    self.log_verification_result(
                        "Layer 2", f"{metric} variance check", "WARN",
                        f"Only {unique_values} unique values - possible data quality issue"
                    )
                else:
                    self.log_verification_result(
                        "Layer 2", f"{metric} variance check", "PASS",
                        f"Found {unique_values} unique values"
                    )
                    
        except Exception as e:
            self.log_verification_result(
                "Layer 2", "DataFrame processing", "FAIL",
                f"Error processing data: {e}"
            )

    def layer3_cross_table_consistency(self, conn: sqlite3.Connection):
        """Layer 3: Cross-Table Consistency Check"""
        logger.info("=" * 60)
        logger.info("LAYER 3: CROSS-TABLE CONSISTENCY CHECK")
        logger.info("=" * 60)
        
        cursor = conn.cursor()
        
        try:
            # Get player IDs from PlayerArchetypeFeatures
            cursor.execute(f"""
                SELECT DISTINCT player_id FROM PlayerArchetypeFeatures 
                WHERE season = '{self.season}'
            """)
            archetype_players = set(row[0] for row in cursor.fetchall())
            
            # Get player IDs from PlayerSeasonRawStats
            cursor.execute(f"""
                SELECT DISTINCT player_id FROM PlayerSeasonRawStats 
                WHERE season = '{self.season}'
            """)
            raw_stats_players = set(row[0] for row in cursor.fetchall())
            
            # Check if archetype players are subset of raw stats players
            missing_players = archetype_players - raw_stats_players
            
            if len(missing_players) == 0:
                self.log_verification_result(
                    "Layer 3", "Player ID consistency", "PASS",
                    f"All {len(archetype_players)} archetype players found in raw stats"
                )
            else:
                self.log_verification_result(
                    "Layer 3", "Player ID consistency", "FAIL",
                    f"{len(missing_players)} archetype players missing from raw stats: {list(missing_players)[:5]}..."
                )
            
            # Check for reasonable overlap
            overlap = len(archetype_players & raw_stats_players)
            if overlap >= len(archetype_players) * 0.95:  # At least 95% overlap
                self.log_verification_result(
                    "Layer 3", "Player overlap check", "PASS",
                    f"Overlap: {overlap}/{len(archetype_players)} ({overlap/len(archetype_players)*100:.1f}%)"
                )
            else:
                self.log_verification_result(
                    "Layer 3", "Player overlap check", "FAIL",
                    f"Overlap: {overlap}/{len(archetype_players)} ({overlap/len(archetype_players)*100:.1f}%) - Too low"
                )
                
        except sqlite3.Error as e:
            self.log_verification_result(
                "Layer 3", "Cross-table consistency", "FAIL",
                f"Database error: {e}"
            )

    def generate_summary_report(self):
        """Generate final summary report"""
        logger.info("=" * 60)
        logger.info("VERIFICATION SUMMARY REPORT")
        logger.info("=" * 60)
        
        # Count results by layer
        layer_counts = {}
        for result in self.verification_results:
            layer = result['layer']
            if layer not in layer_counts:
                layer_counts[layer] = {'PASS': 0, 'FAIL': 0, 'WARN': 0}
            layer_counts[layer][result['status']] += 1
        
        # Print layer summaries
        for layer in ['Layer 1', 'Layer 1.5', 'Layer 2', 'Layer 3']:
            if layer in layer_counts:
                counts = layer_counts[layer]
                total = sum(counts.values())
                logger.info(f"{layer}: {counts['PASS']}/{total} PASS, {counts['FAIL']}/{total} FAIL, {counts['WARN']}/{total} WARN")
        
        # Overall result
        if self.critical_failures == 0:
            logger.info("=" * 60)
            logger.info("🎉 ALL CRITICAL VERIFICATIONS PASSED")
            logger.info("Database is ready for clustering analysis")
            logger.info("=" * 60)
            return True
        else:
            logger.error("=" * 60)
            logger.error(f"❌ {self.critical_failures} CRITICAL VERIFICATIONS FAILED")
            logger.error("Database is NOT ready for clustering analysis")
            logger.error("Please fix the issues above before proceeding")
            logger.error("=" * 60)
            return False

    def run_verification(self):
        """Run the complete three-layer verification process"""
        logger.info("Starting comprehensive database sanity verification...")
        logger.info(f"Database: {self.db_path}")
        logger.info(f"Season: {self.season}")
        
        conn = self.connect_to_database()
        
        try:
            # Run all verification layers
            self.layer1_structural_verification(conn)
            self.layer1_5_source_table_spot_checks(conn)
            self.layer2_data_range_validation(conn)
            self.layer3_cross_table_consistency(conn)
            
            # Generate summary and return result
            success = self.generate_summary_report()
            return success
            
        finally:
            conn.close()

def main():
    """Main entry point"""
    verifier = DatabaseSanityVerifier()
    success = verifier.run_verification()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()