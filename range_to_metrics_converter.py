#!/usr/bin/env python3
"""
Range-to-Metrics Converter for NBA Shot Data

This module converts NBA shot location data from distance ranges into canonical metrics
that can be used for player archetype analysis. It handles the complex mapping from
the NBA Stats API's 9 distance ranges to meaningful basketball analytics metrics.

Author: AI Assistant
Date: 2025-10-03
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('range_converter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RangeToMetricsConverter:
    """
    Converts NBA shot location data from distance ranges to canonical metrics.
    
    The NBA Stats API provides shot data in 9 distance ranges:
    1. Less Than 5 ft (0-4.9 ft)
    2. 5-9 ft (5.0-9.9 ft) 
    3. 10-14 ft (10.0-14.9 ft)
    4. 15-19 ft (15.0-19.9 ft)
    5. 20-24 ft (20.0-24.9 ft)
    6. 25-29 ft (25.0-29.9 ft)
    7. 30-34 ft (30.0-34.9 ft)
    8. 35-39 ft (35.0-39.9 ft)
    9. 40+ ft (40.0+ ft)
    
    These are converted to canonical metrics:
    - AVGDIST: Average shot distance (weighted by attempts)
    - Zto3r: Zone to 3-point range ratio
    - THto10r: Three to ten range ratio  
    - TENto16r: Ten to sixteen range ratio
    - SIXTto3PTr: Sixteen to 3PT range ratio
    """
    
    def __init__(self):
        """Initialize the converter with distance range definitions."""
        # Distance ranges from NBA Stats API (in feet)
        self.distance_ranges = [
            (0, 4.9),    # Less Than 5 ft
            (5, 9.9),    # 5-9 ft
            (10, 14.9),  # 10-14 ft
            (15, 19.9),  # 15-19 ft
            (20, 24.9),  # 20-24 ft
            (25, 29.9),  # 25-29 ft
            (30, 34.9),  # 30-34 ft
            (35, 39.9),  # 35-39 ft
            (40, 50)     # 40+ ft (using 50 as upper bound)
        ]
        
        # Midpoints for weighted average calculations
        self.distance_midpoints = [2.5, 7.0, 12.0, 17.0, 22.0, 27.0, 32.0, 37.0, 42.0]
        
        # Range groupings for ratio calculations
        self.zone_range = 0      # Less Than 5 ft (index 0)
        self.three_to_ten_range = 1  # 5-9 ft (index 1)
        self.ten_to_sixteen_range = 3  # 15-19 ft (index 3)
        self.sixteen_to_three_range = 5  # 25-29 ft (index 5)
        self.three_plus_range = 6  # 30-34 ft (index 6)
        
        logger.info("RangeToMetricsConverter initialized with 9 distance ranges")
    
    def validate_input_data(self, df: pd.DataFrame) -> bool:
        """
        Validate that the input DataFrame has the expected structure.
        
        Args:
            df: DataFrame with shot data
            
        Returns:
            bool: True if valid, False otherwise
        """
        logger.info("Validating input data structure...")
        
        # Check if DataFrame is empty
        if df.empty:
            logger.error("Input DataFrame is empty")
            return False
        
        # Expected columns for shot data (FGM, FGA, FG_PCT for each range)
        expected_columns = ['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ID', 'TEAM_ABBREVIATION']
        
        # Check basic player info columns
        for col in expected_columns:
            if col not in df.columns:
                logger.error(f"Missing required column: {col}")
                return False
        
        # Check for shot data columns (should have FGM, FGA, FG_PCT for each range)
        shot_columns = [col for col in df.columns if any(prefix in col for prefix in ['FGM', 'FGA', 'FG_PCT'])]
        
        if len(shot_columns) < 27:  # 9 ranges * 3 columns each
            logger.error(f"Insufficient shot data columns. Found {len(shot_columns)}, expected at least 27")
            return False
        
        logger.info(f"Input validation passed. Found {len(df)} players with {len(shot_columns)} shot columns")
        return True
    
    def extract_shot_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Extract shot data columns from the input DataFrame.
        
        Args:
            df: Input DataFrame with shot data
            
        Returns:
            Tuple of (player_info_df, shot_columns)
        """
        logger.info("Extracting shot data from input DataFrame...")
        
        # Extract player information
        player_info = df[['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ID', 'TEAM_ABBREVIATION']].copy()
        
        # Find shot data columns
        shot_columns = []
        for i in range(9):  # 9 distance ranges
            # Look for FGM, FGA, FG_PCT columns for each range
            fgm_cols = [col for col in df.columns if col.startswith('FGM') and (col == 'FGM' or col.endswith(f'_{i}'))]
            fga_cols = [col for col in df.columns if col.startswith('FGA') and (col == 'FGA' or col.endswith(f'_{i}'))]
            fgpct_cols = [col for col in df.columns if col.startswith('FG_PCT') and (col == 'FG_PCT' or col.endswith(f'_{i}'))]
            
            # Add the first matching column for each type
            if fgm_cols:
                shot_columns.append(fgm_cols[0])
            if fga_cols:
                shot_columns.append(fga_cols[0])
            if fgpct_cols:
                shot_columns.append(fgpct_cols[0])
        
        logger.info(f"Extracted {len(shot_columns)} shot data columns")
        return player_info, shot_columns
    
    def calculate_average_shot_distance(self, df: pd.DataFrame, shot_columns: List[str]) -> pd.Series:
        """
        Calculate average shot distance weighted by field goal attempts.
        
        Args:
            df: DataFrame with shot data
            shot_columns: List of shot data column names
            
        Returns:
            Series with average shot distances
        """
        logger.info("Calculating average shot distance...")
        
        # Initialize arrays
        total_fga = pd.Series([0.0] * len(df), index=df.index)
        weighted_distance = pd.Series([0.0] * len(df), index=df.index)
        
        # Process each distance range
        for i in range(9):
            # Find FGA column for this range
            fga_col = None
            for col in shot_columns:
                if col.startswith('FGA') and (col == 'FGA' or col.endswith(f'_{i}')):
                    fga_col = col
                    break
            
            if fga_col is None:
                logger.warning(f"No FGA column found for range {i}")
                continue
            
            # Get FGA values and convert to numeric
            fga_values = pd.to_numeric(df[fga_col], errors='coerce').fillna(0)
            
            # Add to weighted average
            total_fga += fga_values
            weighted_distance += fga_values * self.distance_midpoints[i]
        
        # Calculate average distance (avoid division by zero)
        avg_distance = (weighted_distance / (total_fga + 1e-6)).fillna(0)
        
        logger.info(f"Calculated average shot distance for {len(avg_distance)} players")
        return avg_distance
    
    def calculate_shot_distribution_ratios(self, df: pd.DataFrame, shot_columns: List[str]) -> Dict[str, pd.Series]:
        """
        Calculate shot distribution ratios for different court areas.
        
        Args:
            df: DataFrame with shot data
            shot_columns: List of shot data column names
            
        Returns:
            Dictionary with ratio calculations
        """
        logger.info("Calculating shot distribution ratios...")
        
        ratios = {}
        
        # Helper function to get FGA for a specific range
        def get_fga_for_range(range_idx: int) -> pd.Series:
            for col in shot_columns:
                if col.startswith('FGA') and (col == 'FGA' or col.endswith(f'_{range_idx}')):
                    return pd.to_numeric(df[col], errors='coerce').fillna(0)
            return pd.Series([0.0] * len(df), index=df.index)
        
        # Zone to 3-point range ratio (0-5 ft / 25-29 ft)
        zone_fga = get_fga_for_range(self.zone_range)
        three_fga = get_fga_for_range(self.sixteen_to_three_range)
        ratios['Zto3r'] = (zone_fga / (three_fga + 1e-6)).fillna(0)
        
        # Three to ten range ratio (5-9 ft / 15-19 ft)
        three_to_ten_fga = get_fga_for_range(self.three_to_ten_range)
        ten_to_sixteen_fga = get_fga_for_range(self.ten_to_sixteen_range)
        ratios['THto10r'] = (three_to_ten_fga / (ten_to_sixteen_fga + 1e-6)).fillna(0)
        
        # Ten to sixteen range ratio (15-19 ft / 25-29 ft)
        ten_to_sixteen_fga = get_fga_for_range(self.ten_to_sixteen_range)
        sixteen_to_three_fga = get_fga_for_range(self.sixteen_to_three_range)
        ratios['TENto16r'] = (ten_to_sixteen_fga / (sixteen_to_three_fga + 1e-6)).fillna(0)
        
        # Sixteen to 3PT range ratio (25-29 ft / 30-34 ft)
        sixteen_to_three_fga = get_fga_for_range(self.sixteen_to_three_range)
        three_plus_fga = get_fga_for_range(self.three_plus_range)
        ratios['SIXTto3PTr'] = (sixteen_to_three_fga / (three_plus_fga + 1e-6)).fillna(0)
        
        logger.info(f"Calculated {len(ratios)} shot distribution ratios")
        return ratios
    
    def convert_to_canonical_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert shot data to canonical metrics.
        
        Args:
            df: DataFrame with shot data from NBA Stats API
            
        Returns:
            DataFrame with canonical metrics
        """
        logger.info("Starting conversion to canonical metrics...")
        
        # Validate input
        if not self.validate_input_data(df):
            raise ValueError("Input data validation failed")
        
        # Extract shot data
        player_info, shot_columns = self.extract_shot_data(df)
        
        # Calculate metrics
        metrics = {}
        
        # Average shot distance
        metrics['AVGDIST'] = self.calculate_average_shot_distance(df, shot_columns)
        
        # Shot distribution ratios
        ratios = self.calculate_shot_distribution_ratios(df, shot_columns)
        metrics.update(ratios)
        
        # Combine player info with metrics
        result_df = player_info.copy()
        for metric_name, metric_values in metrics.items():
            result_df[metric_name] = metric_values
        
        logger.info(f"Successfully converted {len(result_df)} players to {len(metrics)} canonical metrics")
        return result_df
    
    def get_conversion_summary(self, input_df: pd.DataFrame, output_df: pd.DataFrame) -> Dict:
        """
        Generate a summary of the conversion process.
        
        Args:
            input_df: Original input DataFrame
            output_df: Converted output DataFrame
            
        Returns:
            Dictionary with conversion summary
        """
        summary = {
            'input_players': len(input_df),
            'output_players': len(output_df),
            'metrics_calculated': len([col for col in output_df.columns if col not in ['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ID', 'TEAM_ABBREVIATION']]),
            'conversion_success_rate': len(output_df) / len(input_df) if len(input_df) > 0 else 0,
            'distance_ranges_processed': len(self.distance_ranges),
            'canonical_metrics': ['AVGDIST', 'Zto3r', 'THto10r', 'TENto16r', 'SIXTto3PTr']
        }
        
        # Add metric statistics
        for metric in summary['canonical_metrics']:
            if metric in output_df.columns:
                values = output_df[metric]
                summary[f'{metric}_stats'] = {
                    'mean': float(values.mean()),
                    'std': float(values.std()),
                    'min': float(values.min()),
                    'max': float(values.max()),
                    'non_zero_count': int((values != 0).sum())
                }
        
        return summary

def main():
    """Test the range-to-metrics converter."""
    logger.info("Testing RangeToMetricsConverter...")
    
    # Create sample data for testing
    sample_data = {
        'PLAYER_ID': [1, 2, 3],
        'PLAYER_NAME': ['Player A', 'Player B', 'Player C'],
        'TEAM_ID': [1, 2, 3],
        'TEAM_ABBREVIATION': ['LAL', 'GSW', 'BOS'],
        'FGM': [2.0, 1.5, 3.0],
        'FGA': [4.0, 3.0, 6.0],
        'FG_PCT': [0.5, 0.5, 0.5],
        'FGM_1': [1.0, 0.5, 2.0],
        'FGA_1': [2.0, 1.0, 4.0],
        'FG_PCT_1': [0.5, 0.5, 0.5],
        'FGM_2': [0.5, 1.0, 1.5],
        'FGA_2': [1.0, 2.0, 3.0],
        'FG_PCT_2': [0.5, 0.5, 0.5],
        'FGM_3': [1.0, 0.5, 2.0],
        'FGA_3': [2.0, 1.0, 4.0],
        'FG_PCT_3': [0.5, 0.5, 0.5],
        'FGM_4': [2.0, 1.5, 3.0],
        'FGA_4': [4.0, 3.0, 6.0],
        'FG_PCT_4': [0.5, 0.5, 0.5],
        'FGM_5': [1.5, 2.0, 2.5],
        'FGA_5': [3.0, 4.0, 5.0],
        'FG_PCT_5': [0.5, 0.5, 0.5],
        'FGM_6': [0.5, 1.0, 1.5],
        'FGA_6': [1.0, 2.0, 3.0],
        'FG_PCT_6': [0.5, 0.5, 0.5],
        'FGM_7': [0.0, 0.5, 1.0],
        'FGA_7': [0.0, 1.0, 2.0],
        'FG_PCT_7': [0.0, 0.5, 0.5],
        'FGM_8': [0.0, 0.0, 0.5],
        'FGA_8': [0.0, 0.0, 1.0],
        'FG_PCT_8': [0.0, 0.0, 0.5]
    }
    
    df = pd.DataFrame(sample_data)
    
    # Test the converter
    converter = RangeToMetricsConverter()
    result_df = converter.convert_to_canonical_metrics(df)
    
    # Generate summary
    summary = converter.get_conversion_summary(df, result_df)
    
    logger.info("Conversion test completed successfully!")
    logger.info(f"Summary: {json.dumps(summary, indent=2)}")
    
    print("\nSample output:")
    print(result_df.head())

if __name__ == "__main__":
    main()
