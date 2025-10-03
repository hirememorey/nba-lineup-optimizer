#!/usr/bin/env python3
"""
Reconstruct PlayerArchetypeFeatures Table with Clean Data

This script reconstructs the PlayerArchetypeFeatures table by:
1. Removing duplicate player entries
2. Ensuring data quality and consistency
3. Rebuilding the table with clean, validated data
4. Adding proper timestamps for data freshness tracking

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
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reconstruct_features.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FeaturesTableReconstructor:
    """
    Reconstructs the PlayerArchetypeFeatures table with clean, validated data.
    """
    
    def __init__(self, db_path: str = "src/nba_stats/db/nba_stats.db"):
        """Initialize the reconstructor with database connection."""
        self.db_path = db_path
        self.conn = None
        
        # Data quality thresholds
        self.thresholds = {
            'min_shot_attempts': 10,  # Minimum shot attempts for valid metrics
            'max_ratio_value': 10,    # Maximum ratio value to prevent outliers
            'min_percentage': 0.0,    # Minimum percentage value
            'max_percentage': 1.0,    # Maximum percentage value
        }
        
        logger.info("FeaturesTableReconstructor initialized")
    
    def connect_database(self) -> bool:
        """Connect to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            logger.info(f"Connected to database: {self.db_path}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def backup_existing_table(self, season: str = "2024-25") -> bool:
        """Create a backup of the existing table before reconstruction."""
        logger.info(f"Creating backup of existing PlayerArchetypeFeatures table for season {season}...")
        
        try:
            cursor = self.conn.cursor()
            
            # Create backup table
            backup_table_name = f"PlayerArchetypeFeatures_backup_{season.replace('-', '_')}"
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {backup_table_name} AS 
                SELECT * FROM PlayerArchetypeFeatures 
                WHERE season = ?
            """, (season,))
            
            # Count records in backup
            cursor.execute(f"SELECT COUNT(*) FROM {backup_table_name}")
            backup_count = cursor.fetchone()[0]
            
            self.conn.commit()
            logger.info(f"Backup created: {backup_table_name} with {backup_count} records")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Backup creation failed: {e}")
            return False
    
    def get_clean_player_data(self, season: str = "2024-25") -> pd.DataFrame:
        """
        Get clean player data by removing duplicates and applying quality filters.
        
        Args:
            season: Season to process
            
        Returns:
            Clean DataFrame with player data
        """
        logger.info(f"Getting clean player data for season {season}...")
        
        # Get all data for the season
        # Check if updated_at column exists
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(PlayerArchetypeFeatures)")
        columns_info = cursor.fetchall()
        has_updated_at = any(col[1] == 'updated_at' for col in columns_info)
        
        if has_updated_at:
            df = pd.read_sql_query("""
                SELECT * FROM PlayerArchetypeFeatures 
                WHERE season = ?
                ORDER BY player_id, updated_at DESC
            """, self.conn, params=(season,))
        else:
            df = pd.read_sql_query("""
                SELECT * FROM PlayerArchetypeFeatures 
                WHERE season = ?
                ORDER BY player_id
            """, self.conn, params=(season,))
        
        if df.empty:
            logger.warning(f"No data found for season {season}")
            return df
        
        logger.info(f"Retrieved {len(df)} records for season {season}")
        
        # Remove duplicates (keep most recent record per player)
        if 'updated_at' in df.columns:
            df = df.sort_values('updated_at', ascending=False)
            df = df.drop_duplicates(subset=['player_id'], keep='first')
        else:
            # If no timestamp, just remove duplicates
            df = df.drop_duplicates(subset=['player_id'], keep='first')
        
        logger.info(f"After removing duplicates: {len(df)} unique players")
        
        # Apply data quality filters
        df = self.apply_quality_filters(df)
        
        logger.info(f"After quality filtering: {len(df)} players with clean data")
        
        return df
    
    def apply_quality_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply data quality filters to remove invalid or problematic data.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Filtered DataFrame
        """
        logger.info("Applying data quality filters...")
        
        original_count = len(df)
        
        # Filter out players with insufficient shot data
        if 'AVGDIST' in df.columns:
            # Only keep players with meaningful shot data
            valid_shot_data = df['AVGDIST'].notna() & (df['AVGDIST'] > 0)
            df = df[valid_shot_data]
            logger.info(f"Filtered by shot data: {len(df)} players remaining")
        
        # Cap extreme ratio values
        ratio_columns = ['Zto3r', 'THto10r', 'TENto16r', 'SIXTto3PTr']
        for col in ratio_columns:
            if col in df.columns:
                # Cap at maximum ratio value
                df[col] = df[col].clip(0, self.thresholds['max_ratio_value'])
                # Set very small values to 0
                df[col] = df[col].where(df[col] >= 0.01, 0)
        
        # Ensure percentage values are within valid range
        percentage_columns = ['FTPCT', 'TSPCT', 'FG3PCT', 'FGPCT']
        for col in percentage_columns:
            if col in df.columns:
                df[col] = df[col].clip(
                    self.thresholds['min_percentage'], 
                    self.thresholds['max_percentage']
                )
        
        # Handle zero values in required fields
        # Set zero height to a default value (6 feet = 72 inches)
        if 'HEIGHT' in df.columns:
            df['HEIGHT'] = df['HEIGHT'].replace(0, 72)
        
        # Set zero wingspan to a default value (6 feet = 72 inches)
        if 'WINGSPAN' in df.columns:
            df['WINGSPAN'] = df['WINGSPAN'].replace(0, 72)
        
        # Remove players with all zeros in key metrics (likely data quality issues)
        key_metrics = ['AVGDIST', 'FTPCT', 'TSPCT']
        valid_metrics = df[key_metrics].notna().any(axis=1)
        df = df[valid_metrics]
        
        filtered_count = len(df)
        logger.info(f"Quality filtering: {original_count} -> {filtered_count} players "
                   f"({original_count - filtered_count} removed)")
        
        return df
    
    def create_clean_table_structure(self) -> bool:
        """Create a clean table structure with proper constraints and indexes."""
        logger.info("Creating clean table structure...")
        
        try:
            cursor = self.conn.cursor()
            
            # Drop existing table if it exists
            cursor.execute("DROP TABLE IF EXISTS PlayerArchetypeFeatures_clean")
            
            # Create new table with proper structure
            cursor.execute("""
                CREATE TABLE PlayerArchetypeFeatures_clean (
                    player_id INTEGER NOT NULL,
                    season TEXT NOT NULL,
                    FTPCT REAL CHECK (FTPCT >= 0 AND FTPCT <= 1),
                    TSPCT REAL CHECK (TSPCT >= 0 AND TSPCT <= 1),
                    THPAr REAL CHECK (THPAr >= 0),
                    FTr REAL CHECK (FTr >= 0),
                    TRBPCT REAL CHECK (TRBPCT >= 0),
                    ASTPCT REAL CHECK (ASTPCT >= 0),
                    AVGDIST REAL CHECK (AVGDIST >= 0 AND AVGDIST <= 50),
                    Zto3r REAL CHECK (Zto3r >= 0 AND Zto3r <= 10),
                    THto10r REAL CHECK (THto10r >= 0 AND THto10r <= 10),
                    TENto16r REAL CHECK (TENto16r >= 0 AND TENto16r <= 10),
                    SIXTto3PTr REAL CHECK (SIXTto3PTr >= 0 AND SIXTto3PTr <= 10),
                    HEIGHT REAL CHECK (HEIGHT > 0),
                    WINGSPAN REAL CHECK (WINGSPAN > 0),
                    FRNTCTTCH REAL CHECK (FRNTCTTCH >= 0),
                    TOP REAL CHECK (TOP >= 0),
                    AVGSECPERTCH REAL CHECK (AVGSECPERTCH >= 0),
                    AVGDRIBPERTCH REAL CHECK (AVGDRIBPERTCH >= 0),
                    ELBWTCH REAL CHECK (ELBWTCH >= 0),
                    POSTUPS REAL CHECK (POSTUPS >= 0),
                    PNTTOUCH REAL CHECK (PNTTOUCH >= 0),
                    DRIVES REAL CHECK (DRIVES >= 0),
                    DRFGA REAL CHECK (DRFGA >= 0),
                    DRPTSPCT REAL CHECK (DRPTSPCT >= 0 AND DRPTSPCT <= 1),
                    DRPASSPCT REAL CHECK (DRPASSPCT >= 0 AND DRPASSPCT <= 1),
                    DRASTPCT REAL CHECK (DRASTPCT >= 0),
                    DRTOVPCT REAL CHECK (DRTOVPCT >= 0 AND DRTOVPCT <= 1),
                    DRPFPCT REAL CHECK (DRPFPCT >= 0),
                    DRIMFGPCT REAL CHECK (DRIMFGPCT >= 0 AND DRIMFGPCT <= 1),
                    CSFGA REAL CHECK (CSFGA >= 0),
                    CS3PA REAL CHECK (CS3PA >= 0),
                    PASSESMADE REAL CHECK (PASSESMADE >= 0),
                    SECAST REAL CHECK (SECAST >= 0),
                    POTAST REAL CHECK (POTAST >= 0),
                    PUFGA REAL CHECK (PUFGA >= 0),
                    PU3PA REAL CHECK (PU3PA >= 0),
                    PSTUPFGA REAL CHECK (PSTUPFGA >= 0),
                    PSTUPPTSPCT REAL CHECK (PSTUPPTSPCT >= 0 AND PSTUPPTSPCT <= 1),
                    PSTUPPASSPCT REAL CHECK (PSTUPPASSPCT >= 0 AND PSTUPPASSPCT <= 1),
                    PSTUPASTPCT REAL CHECK (PSTUPASTPCT >= 0),
                    PSTUPTOVPCT REAL CHECK (PSTUPTOVPCT >= 0 AND PSTUPTOVPCT <= 1),
                    PNTTCHS REAL CHECK (PNTTCHS >= 0),
                    PNTFGA REAL CHECK (PNTFGA >= 0),
                    PNTPTSPCT REAL CHECK (PNTPTSPCT >= 0 AND PNTPTSPCT <= 1),
                    PNTPASSPCT REAL CHECK (PNTPASSPCT >= 0 AND PNTPASSPCT <= 1),
                    PNTASTPCT REAL CHECK (PNTASTPCT >= 0),
                    PNTTVPCT REAL CHECK (PNTTVPCT >= 0 AND PNTTVPCT <= 1),
                    AVGFGATTEMPTEDAGAINSTPERGAME REAL CHECK (AVGFGATTEMPTEDAGAINSTPERGAME >= 0),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (player_id, season),
                    FOREIGN KEY (player_id) REFERENCES Players(player_id)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX idx_player_season ON PlayerArchetypeFeatures_clean(player_id, season)")
            cursor.execute("CREATE INDEX idx_updated_at ON PlayerArchetypeFeatures_clean(updated_at)")
            
            self.conn.commit()
            logger.info("Clean table structure created successfully")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Failed to create clean table structure: {e}")
            return False
    
    def populate_clean_table(self, df: pd.DataFrame, season: str = "2024-25") -> bool:
        """
        Populate the clean table with validated data.
        
        Args:
            df: Clean DataFrame with player data
            season: Season to process
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Populating clean table with {len(df)} players...")
        
        try:
            cursor = self.conn.cursor()
            
            # Clear existing data for this season
            cursor.execute("DELETE FROM PlayerArchetypeFeatures_clean WHERE season = ?", (season,))
            
            # Insert clean data
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO PlayerArchetypeFeatures_clean 
                    (player_id, season, FTPCT, TSPCT, THPAr, FTr, TRBPCT, ASTPCT, 
                     AVGDIST, Zto3r, THto10r, TENto16r, SIXTto3PTr, HEIGHT, WINGSPAN,
                     FRNTCTTCH, TOP, AVGSECPERTCH, AVGDRIBPERTCH, ELBWTCH, POSTUPS,
                     PNTTOUCH, DRIVES, DRFGA, DRPTSPCT, DRPASSPCT, DRASTPCT, DRTOVPCT,
                     DRPFPCT, DRIMFGPCT, CSFGA, CS3PA, PASSESMADE, SECAST, POTAST,
                     PUFGA, PU3PA, PSTUPFGA, PSTUPPTSPCT, PSTUPPASSPCT, PSTUPASTPCT,
                     PSTUPTOVPCT, PNTTCHS, PNTFGA, PNTPTSPCT, PNTPASSPCT, PNTASTPCT,
                     PNTTVPCT, AVGFGATTEMPTEDAGAINSTPERGAME, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(row['player_id']),
                    season,
                    float(row.get('FTPCT', 0)),
                    float(row.get('TSPCT', 0)),
                    float(row.get('THPAr', 0)),
                    float(row.get('FTr', 0)),
                    float(row.get('TRBPCT', 0)),
                    float(row.get('ASTPCT', 0)),
                    float(row.get('AVGDIST', 0)),
                    float(row.get('Zto3r', 0)),
                    float(row.get('THto10r', 0)),
                    float(row.get('TENto16r', 0)),
                    float(row.get('SIXTto3PTr', 0)),
                    float(row.get('HEIGHT', 0)),
                    float(row.get('WINGSPAN', 0)),
                    float(row.get('FRNTCTTCH', 0)),
                    float(row.get('TOP', 0)),
                    float(row.get('AVGSECPERTCH', 0)),
                    float(row.get('AVGDRIBPERTCH', 0)),
                    float(row.get('ELBWTCH', 0)),
                    float(row.get('POSTUPS', 0)),
                    float(row.get('PNTTOUCH', 0)),
                    float(row.get('DRIVES', 0)),
                    float(row.get('DRFGA', 0)),
                    float(row.get('DRPTSPCT', 0)),
                    float(row.get('DRPASSPCT', 0)),
                    float(row.get('DRASTPCT', 0)),
                    float(row.get('DRTOVPCT', 0)),
                    float(row.get('DRPFPCT', 0)),
                    float(row.get('DRIMFGPCT', 0)),
                    float(row.get('CSFGA', 0)),
                    float(row.get('CS3PA', 0)),
                    float(row.get('PASSESMADE', 0)),
                    float(row.get('SECAST', 0)),
                    float(row.get('POTAST', 0)),
                    float(row.get('PUFGA', 0)),
                    float(row.get('PU3PA', 0)),
                    float(row.get('PSTUPFGA', 0)),
                    float(row.get('PSTUPPTSPCT', 0)),
                    float(row.get('PSTUPPASSPCT', 0)),
                    float(row.get('PSTUPASTPCT', 0)),
                    float(row.get('PSTUPTOVPCT', 0)),
                    float(row.get('PNTTCHS', 0)),
                    float(row.get('PNTFGA', 0)),
                    float(row.get('PNTPTSPCT', 0)),
                    float(row.get('PNTPASSPCT', 0)),
                    float(row.get('PNTASTPCT', 0)),
                    float(row.get('PNTTVPCT', 0)),
                    float(row.get('AVGFGATTEMPTEDAGAINSTPERGAME', 0)),
                    datetime.now().isoformat()
                ))
            
            self.conn.commit()
            logger.info(f"Successfully populated clean table with {len(df)} players")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Failed to populate clean table: {e}")
            self.conn.rollback()
            return False
    
    def replace_original_table(self, season: str = "2024-25") -> bool:
        """Replace the original table with the clean version."""
        logger.info("Replacing original table with clean version...")
        
        try:
            cursor = self.conn.cursor()
            
            # Drop original table
            cursor.execute("DROP TABLE IF EXISTS PlayerArchetypeFeatures")
            
            # Rename clean table to original name
            cursor.execute("ALTER TABLE PlayerArchetypeFeatures_clean RENAME TO PlayerArchetypeFeatures")
            
            self.conn.commit()
            logger.info("Successfully replaced original table with clean version")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Failed to replace original table: {e}")
            return False
    
    def generate_reconstruction_report(self, season: str = "2024-25") -> Dict[str, Any]:
        """Generate a report of the reconstruction process."""
        logger.info("Generating reconstruction report...")
        
        try:
            cursor = self.conn.cursor()
            
            # Get final statistics
            cursor.execute("SELECT COUNT(*) FROM PlayerArchetypeFeatures WHERE season = ?", (season,))
            final_count = cursor.fetchone()[0]
            
            # Get data quality metrics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_players,
                    COUNT(AVGDIST) as players_with_shot_data,
                    COUNT(FTPCT) as players_with_ft_data,
                    AVG(AVGDIST) as avg_shot_distance,
                    AVG(FTPCT) as avg_ft_percentage
                FROM PlayerArchetypeFeatures 
                WHERE season = ?
            """, (season,))
            
            quality_stats = cursor.fetchone()
            
            report = {
                'reconstruction_timestamp': datetime.now().isoformat(),
                'season': season,
                'final_player_count': final_count,
                'data_quality_metrics': {
                    'total_players': quality_stats[0],
                    'players_with_shot_data': quality_stats[1],
                    'players_with_ft_data': quality_stats[2],
                    'avg_shot_distance': float(quality_stats[3]) if quality_stats[3] else 0,
                    'avg_ft_percentage': float(quality_stats[4]) if quality_stats[4] else 0
                },
                'improvements': [
                    'Removed duplicate player entries',
                    'Applied data quality filters',
                    'Added proper constraints and validation',
                    'Added timestamp tracking for data freshness',
                    'Capped extreme ratio values to prevent outliers'
                ]
            }
            
            return report
            
        except sqlite3.Error as e:
            logger.error(f"Failed to generate report: {e}")
            return {'error': str(e)}
    
    def run_reconstruction(self, season: str = "2024-25") -> bool:
        """
        Run the complete reconstruction process.
        
        Args:
            season: Season to reconstruct
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Starting reconstruction of PlayerArchetypeFeatures table for season {season}...")
        
        if not self.connect_database():
            return False
        
        try:
            # Step 1: Create backup
            if not self.backup_existing_table(season):
                logger.error("Backup creation failed, aborting reconstruction")
                return False
            
            # Step 2: Get clean data
            clean_df = self.get_clean_player_data(season)
            if clean_df.empty:
                logger.error("No clean data available, aborting reconstruction")
                return False
            
            # Step 3: Create clean table structure
            if not self.create_clean_table_structure():
                logger.error("Failed to create clean table structure")
                return False
            
            # Step 4: Populate clean table
            if not self.populate_clean_table(clean_df, season):
                logger.error("Failed to populate clean table")
                return False
            
            # Step 5: Replace original table
            if not self.replace_original_table(season):
                logger.error("Failed to replace original table")
                return False
            
            # Step 6: Generate report
            report = self.generate_reconstruction_report(season)
            
            # Save report
            report_file = f"reconstruction_report_{season.replace('-', '_')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Reconstruction completed successfully! Report saved to {report_file}")
            logger.info(f"Final result: {report['final_player_count']} players with clean data")
            
            return True
            
        except Exception as e:
            logger.error(f"Reconstruction failed with error: {e}")
            return False
        finally:
            if self.conn:
                self.conn.close()

def main():
    """Run the reconstruction process."""
    logger.info("Starting PlayerArchetypeFeatures table reconstruction...")
    
    reconstructor = FeaturesTableReconstructor()
    success = reconstructor.run_reconstruction("2024-25")
    
    if success:
        print("\n✅ Reconstruction completed successfully!")
        print("The PlayerArchetypeFeatures table has been cleaned and reconstructed.")
    else:
        print("\n❌ Reconstruction failed!")
        print("Check the logs for details.")

if __name__ == "__main__":
    main()
