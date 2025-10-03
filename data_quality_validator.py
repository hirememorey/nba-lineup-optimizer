#!/usr/bin/env python3
"""
Data Quality Validator for NBA Player Archetype Features

This module validates the quality and completeness of player archetype features
data, ensuring that the data meets the standards required for reliable clustering
and analysis.

Author: AI Assistant
Date: 2025-10-03
"""

import pandas as pd
import numpy as np
import sqlite3
import logging
from typing import Dict, List, Tuple, Optional, Any
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_quality_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataQualityValidator:
    """
    Validates data quality for NBA player archetype features.
    
    This validator checks for:
    - Data completeness (missing values)
    - Data consistency (outliers, impossible values)
    - Data accuracy (within expected ranges)
    - Data freshness (recent updates)
    - Data integrity (foreign key relationships)
    """
    
    def __init__(self, db_path: str = "src/nba_stats/db/nba_stats.db"):
        """Initialize the validator with database connection."""
        self.db_path = db_path
        self.conn = None
        
        # Define expected data quality thresholds
        self.thresholds = {
            'min_completeness': 0.8,  # 80% of data must be present
            'max_outlier_ratio': 0.05,  # 5% of data can be outliers
            'min_players_per_season': 100,  # Minimum players per season
            'max_age_days': 7,  # Data should be less than 7 days old
            'min_shot_attempts': 10,  # Minimum shot attempts for valid metrics
            'max_shot_percentage': 1.0,  # Shot percentage can't exceed 100%
            'min_shot_percentage': 0.0,  # Shot percentage can't be negative
        }
        
        # Define expected ranges for different metrics
        self.metric_ranges = {
            'AVGDIST': (0, 50),  # Average shot distance in feet
            'Zto3r': (0, 10),    # Zone to 3-point ratio
            'THto10r': (0, 10),  # Three to ten range ratio
            'TENto16r': (0, 10), # Ten to sixteen range ratio
            'SIXTto3PTr': (0, 10), # Sixteen to 3PT range ratio
            'FTPCT': (0, 1),     # Free throw percentage
            'FG3PCT': (0, 1),    # 3-point percentage
            'FGPCT': (0, 1),     # Field goal percentage
        }
        
        logger.info("DataQualityValidator initialized")
    
    def connect_database(self) -> bool:
        """Connect to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            logger.info(f"Connected to database: {self.db_path}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def validate_data_completeness(self, season: str = "2024-25") -> Dict[str, Any]:
        """
        Validate data completeness for a given season.
        
        Args:
            season: Season to validate
            
        Returns:
            Dictionary with completeness validation results
        """
        logger.info(f"Validating data completeness for season {season}...")
        
        if not self.conn:
            raise ValueError("Database not connected")
        
        # Get all columns in PlayerArchetypeFeatures table
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(PlayerArchetypeFeatures)")
        columns_info = cursor.fetchall()
        
        # Get data for the season
        df = pd.read_sql_query("""
            SELECT * FROM PlayerArchetypeFeatures 
            WHERE season = ?
        """, self.conn, params=(season,))
        
        if df.empty:
            return {
                'status': 'FAILED',
                'error': 'No data found for season',
                'completeness_score': 0.0
            }
        
        # Calculate completeness for each column
        completeness_results = {}
        total_players = len(df)
        
        for col_info in columns_info:
            col_name = col_info[1]
            if col_name in ['player_id', 'season']:  # Skip key columns
                continue
                
            non_null_count = df[col_name].notna().sum()
            completeness = non_null_count / total_players
            completeness_results[col_name] = {
                'completeness': completeness,
                'missing_count': total_players - non_null_count,
                'total_count': total_players,
                'status': 'PASS' if completeness >= self.thresholds['min_completeness'] else 'FAIL'
            }
        
        # Calculate overall completeness score
        completeness_scores = [result['completeness'] for result in completeness_results.values()]
        overall_completeness = np.mean(completeness_scores)
        
        # Count failed columns
        failed_columns = [col for col, result in completeness_results.items() 
                         if result['status'] == 'FAIL']
        
        result = {
            'status': 'PASS' if len(failed_columns) == 0 else 'FAIL',
            'overall_completeness': overall_completeness,
            'total_players': total_players,
            'failed_columns': failed_columns,
            'column_details': completeness_results
        }
        
        logger.info(f"Completeness validation: {result['status']} "
                   f"(score: {overall_completeness:.3f}, failed: {len(failed_columns)})")
        
        return result
    
    def validate_data_consistency(self, season: str = "2024-25") -> Dict[str, Any]:
        """
        Validate data consistency and detect outliers.
        
        Args:
            season: Season to validate
            
        Returns:
            Dictionary with consistency validation results
        """
        logger.info(f"Validating data consistency for season {season}...")
        
        if not self.conn:
            raise ValueError("Database not connected")
        
        # Get data for the season
        df = pd.read_sql_query("""
            SELECT * FROM PlayerArchetypeFeatures 
            WHERE season = ?
        """, self.conn, params=(season,))
        
        if df.empty:
            return {
                'status': 'FAILED',
                'error': 'No data found for season'
            }
        
        consistency_results = {}
        outlier_columns = []
        
        # Check each metric for outliers and impossible values
        for metric, (min_val, max_val) in self.metric_ranges.items():
            if metric not in df.columns:
                continue
                
            values = pd.to_numeric(df[metric], errors='coerce')
            valid_values = values.dropna()
            
            if len(valid_values) == 0:
                consistency_results[metric] = {
                    'status': 'FAIL',
                    'error': 'No valid numeric values',
                    'outlier_count': 0,
                    'outlier_ratio': 0.0
                }
                outlier_columns.append(metric)
                continue
            
            # Check for values outside expected range
            out_of_range = ((valid_values < min_val) | (valid_values > max_val)).sum()
            outlier_ratio = out_of_range / len(valid_values)
            
            # Check for statistical outliers using IQR method
            Q1 = valid_values.quantile(0.25)
            Q3 = valid_values.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            statistical_outliers = ((valid_values < lower_bound) | (valid_values > upper_bound)).sum()
            statistical_outlier_ratio = statistical_outliers / len(valid_values)
            
            total_outlier_ratio = max(outlier_ratio, statistical_outlier_ratio)
            
            consistency_results[metric] = {
                'status': 'PASS' if total_outlier_ratio <= self.thresholds['max_outlier_ratio'] else 'FAIL',
                'outlier_count': int(out_of_range + statistical_outliers),
                'outlier_ratio': total_outlier_ratio,
                'range_violations': int(out_of_range),
                'statistical_outliers': int(statistical_outliers),
                'mean': float(valid_values.mean()),
                'std': float(valid_values.std()),
                'min': float(valid_values.min()),
                'max': float(valid_values.max())
            }
            
            if consistency_results[metric]['status'] == 'FAIL':
                outlier_columns.append(metric)
        
        result = {
            'status': 'PASS' if len(outlier_columns) == 0 else 'FAIL',
            'outlier_columns': outlier_columns,
            'metric_details': consistency_results
        }
        
        logger.info(f"Consistency validation: {result['status']} "
                   f"(outlier columns: {len(outlier_columns)})")
        
        return result
    
    def validate_data_freshness(self, season: str = "2024-25") -> Dict[str, Any]:
        """
        Validate data freshness (how recent the data is).
        
        Args:
            season: Season to validate
            
        Returns:
            Dictionary with freshness validation results
        """
        logger.info(f"Validating data freshness for season {season}...")
        
        if not self.conn:
            raise ValueError("Database not connected")
        
        # Check if there's an updated_at column
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(PlayerArchetypeFeatures)")
        columns_info = cursor.fetchall()
        
        has_updated_at = any(col[1] == 'updated_at' for col in columns_info)
        
        if not has_updated_at:
            return {
                'status': 'WARNING',
                'message': 'No updated_at column found, cannot validate freshness'
            }
        
        # Get the most recent update time
        cursor.execute("""
            SELECT MAX(updated_at) as last_update
            FROM PlayerArchetypeFeatures 
            WHERE season = ?
        """, (season,))
        
        result = cursor.fetchone()
        if not result or not result[0]:
            return {
                'status': 'FAIL',
                'error': 'No update timestamp found'
            }
        
        last_update = datetime.fromisoformat(result[0].replace('Z', '+00:00'))
        days_since_update = (datetime.now() - last_update.replace(tzinfo=None)).days
        
        status = 'PASS' if days_since_update <= self.thresholds['max_age_days'] else 'FAIL'
        
        result = {
            'status': status,
            'last_update': result[0],
            'days_since_update': days_since_update,
            'max_allowed_days': self.thresholds['max_age_days']
        }
        
        logger.info(f"Freshness validation: {status} "
                   f"(last update: {days_since_update} days ago)")
        
        return result
    
    def validate_data_integrity(self, season: str = "2024-25") -> Dict[str, Any]:
        """
        Validate data integrity (foreign key relationships, referential integrity).
        
        Args:
            season: Season to validate
            
        Returns:
            Dictionary with integrity validation results
        """
        logger.info(f"Validating data integrity for season {season}...")
        
        if not self.conn:
            raise ValueError("Database not connected")
        
        integrity_results = {}
        
        # Check if all players in PlayerArchetypeFeatures exist in Players table
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as orphaned_players
            FROM PlayerArchetypeFeatures paf
            LEFT JOIN Players p ON paf.player_id = p.player_id
            WHERE paf.season = ? AND p.player_id IS NULL
        """, (season,))
        
        orphaned_players = cursor.fetchone()[0]
        
        integrity_results['orphaned_players'] = {
            'count': orphaned_players,
            'status': 'PASS' if orphaned_players == 0 else 'FAIL'
        }
        
        # Check for duplicate player-season combinations
        cursor.execute("""
            SELECT player_id, COUNT(*) as count
            FROM PlayerArchetypeFeatures
            WHERE season = ?
            GROUP BY player_id
            HAVING COUNT(*) > 1
        """, (season,))
        
        duplicates = cursor.fetchall()
        
        integrity_results['duplicates'] = {
            'count': len(duplicates),
            'status': 'PASS' if len(duplicates) == 0 else 'FAIL',
            'duplicate_players': [row[0] for row in duplicates]
        }
        
        # Check for negative shot attempts (if available)
        shot_columns = ['FGA', 'FG3A', 'FTA']
        for col in shot_columns:
            if col in [col_info[1] for col_info in cursor.execute("PRAGMA table_info(PlayerArchetypeFeatures)").fetchall()]:
                cursor.execute(f"""
                    SELECT COUNT(*) as negative_count
                    FROM PlayerArchetypeFeatures
                    WHERE season = ? AND {col} < 0
                """, (season,))
                
                negative_count = cursor.fetchone()[0]
                integrity_results[f'{col}_negative'] = {
                    'count': negative_count,
                    'status': 'PASS' if negative_count == 0 else 'FAIL'
                }
        
        # Overall integrity status
        failed_checks = [check for check, result in integrity_results.items() 
                        if result['status'] == 'FAIL']
        
        result = {
            'status': 'PASS' if len(failed_checks) == 0 else 'FAIL',
            'failed_checks': failed_checks,
            'check_details': integrity_results
        }
        
        logger.info(f"Integrity validation: {result['status']} "
                   f"(failed checks: {len(failed_checks)})")
        
        return result
    
    def run_comprehensive_validation(self, season: str = "2024-25") -> Dict[str, Any]:
        """
        Run all validation checks and return comprehensive results.
        
        Args:
            season: Season to validate
            
        Returns:
            Dictionary with comprehensive validation results
        """
        logger.info(f"Running comprehensive data quality validation for season {season}...")
        
        if not self.connect_database():
            return {
                'status': 'FAILED',
                'error': 'Database connection failed'
            }
        
        try:
            # Run all validation checks
            completeness = self.validate_data_completeness(season)
            consistency = self.validate_data_consistency(season)
            freshness = self.validate_data_freshness(season)
            integrity = self.validate_data_integrity(season)
            
            # Determine overall status
            check_statuses = [
                completeness.get('status', 'FAIL'),
                consistency.get('status', 'FAIL'),
                freshness.get('status', 'FAIL'),
                integrity.get('status', 'FAIL')
            ]
            
            overall_status = 'PASS' if all(status == 'PASS' for status in check_statuses) else 'FAIL'
            
            # Calculate overall quality score
            quality_score = 0.0
            if completeness.get('status') == 'PASS':
                quality_score += 0.3
            if consistency.get('status') == 'PASS':
                quality_score += 0.3
            if freshness.get('status') == 'PASS':
                quality_score += 0.2
            if integrity.get('status') == 'PASS':
                quality_score += 0.2
            
            result = {
                'overall_status': overall_status,
                'quality_score': quality_score,
                'season': season,
                'validation_timestamp': datetime.now().isoformat(),
                'checks': {
                    'completeness': completeness,
                    'consistency': consistency,
                    'freshness': freshness,
                    'integrity': integrity
                }
            }
            
            logger.info(f"Comprehensive validation completed: {overall_status} "
                       f"(quality score: {quality_score:.3f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Validation failed with error: {e}")
            return {
                'status': 'FAILED',
                'error': str(e)
            }
        finally:
            if self.conn:
                self.conn.close()

def main():
    """Test the data quality validator."""
    logger.info("Testing DataQualityValidator...")
    
    validator = DataQualityValidator()
    results = validator.run_comprehensive_validation("2024-25")
    
    print("\nValidation Results:")
    print(json.dumps(results, indent=2, default=str))

if __name__ == "__main__":
    main()
