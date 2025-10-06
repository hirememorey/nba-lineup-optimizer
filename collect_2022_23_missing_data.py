#!/usr/bin/env python3
"""
Collect missing 2022-23 data: DARKO ratings and salary data.
"""

import requests
import pandas as pd
import sqlite3
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MissingDataCollector:
    """Collect missing 2022-23 DARKO and salary data."""
    
    def __init__(self):
        self.db_path = "src/nba_stats/db/nba_stats.db"
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
    def collect_darko_2022_23(self) -> bool:
        """
        Collect 2022-23 DARKO ratings.
        Note: This is a placeholder - DARKO data needs to be manually downloaded.
        """
        logger.info("Collecting 2022-23 DARKO data...")
        
        # DARKO data is not publicly available via API
        # It needs to be manually downloaded from https://apanalytics.shinyapps.io/DARKO/
        # For now, we'll create a placeholder structure
        
        darko_file = self.data_dir / "darko_dpm_2022-23.csv"
        
        if darko_file.exists():
            logger.info(f"✅ DARKO 2022-23 data already exists: {darko_file}")
            return True
        
        logger.warning("❌ DARKO 2022-23 data not found!")
        logger.warning("Please manually download DARKO 2022-23 data from:")
        logger.warning("https://apanalytics.shinyapps.io/DARKO/")
        logger.warning("Save as: data/darko_dpm_2022-23.csv")
        
        return False
    
    def collect_salary_2022_23(self) -> bool:
        """
        Collect 2022-23 salary data.
        Note: This is a placeholder - salary data needs to be manually collected.
        """
        logger.info("Collecting 2022-23 salary data...")
        
        salary_file = self.data_dir / "player_salaries_2022-23.csv"
        
        if salary_file.exists():
            logger.info(f"✅ Salary 2022-23 data already exists: {salary_file}")
            return True
        
        logger.warning("❌ Salary 2022-23 data not found!")
        logger.warning("Please manually collect 2022-23 salary data from:")
        logger.warning("- HoopsHype: https://hoopshype.com/salaries/")
        logger.warning("- Spotrac: https://www.spotrac.com/nba/rankings/")
        logger.warning("Save as: data/player_salaries_2022-23.csv")
        
        return False
    
    def create_placeholder_data(self) -> None:
        """Create placeholder data structure for missing 2022-23 data."""
        logger.info("Creating placeholder data structure...")
        
        # Get player list from our 2022-23 archetype data
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT player_id FROM PlayerArchetypeFeatures_2022_23")
        player_ids = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"Found {len(player_ids)} players in 2022-23 archetype data")
        
        # Create placeholder DARKO data
        darko_placeholder = []
        for player_id in player_ids:
            darko_placeholder.append({
                'nba_id': player_id,
                'Player': f'Player_{player_id}',  # Placeholder name
                'O-DPM': 0.0,  # Placeholder offensive rating
                'D-DPM': 0.0,  # Placeholder defensive rating
                'DPM': 0.0     # Placeholder overall rating
            })
        
        darko_df = pd.DataFrame(darko_placeholder)
        darko_file = self.data_dir / "darko_dpm_2022-23_placeholder.csv"
        darko_df.to_csv(darko_file, index=False)
        logger.info(f"Created placeholder DARKO data: {darko_file}")
        
        # Create placeholder salary data
        salary_placeholder = []
        for player_id in player_ids:
            salary_placeholder.append({
                'Player': f'Player_{player_id}',  # Placeholder name
                'Salary': 1000000  # Placeholder salary ($1M)
            })
        
        salary_df = pd.DataFrame(salary_placeholder)
        salary_file = self.data_dir / "player_salaries_2022-23_placeholder.csv"
        salary_df.to_csv(salary_file, index=False)
        logger.info(f"Created placeholder salary data: {salary_file}")
        
        conn.close()
    
    def populate_darko_2022_23(self) -> bool:
        """Populate DARKO 2022-23 data into the database."""
        logger.info("Populating DARKO 2022-23 data...")
        
        darko_file = self.data_dir / "darko_dpm_2022-23.csv"
        if not darko_file.exists():
            logger.error(f"DARKO 2022-23 file not found: {darko_file}")
            return False
        
        try:
            # Load DARKO data
            darko_df = pd.read_csv(darko_file)
            logger.info(f"Loaded {len(darko_df)} DARKO records")
            
            # Select and rename columns
            darko_df = darko_df[['nba_id', 'Player', 'O-DPM', 'D-DPM']].rename(columns={
                'nba_id': 'player_id',
                'Player': 'player_name',
                'O-DPM': 'offensive_skill_rating',
                'D-DPM': 'defensive_skill_rating'
            })
            
            # Add season and source
            darko_df['season_id'] = '2022-23'
            darko_df['skill_metric_source'] = 'DARKO'
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            
            # Insert into PlayerSkills table
            skill_data = darko_df[['player_id', 'season_id', 'offensive_skill_rating', 'defensive_skill_rating', 'skill_metric_source']]
            skill_data.to_sql('PlayerSkills', conn, if_exists='append', index=False)
            
            logger.info(f"✅ Inserted {len(skill_data)} DARKO records for 2022-23")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error populating DARKO 2022-23 data: {e}")
            return False
    
    def populate_salary_2022_23(self) -> bool:
        """Populate salary 2022-23 data into the database."""
        logger.info("Populating salary 2022-23 data...")
        
        salary_file = self.data_dir / "player_salaries_2022-23.csv"
        if not salary_file.exists():
            logger.error(f"Salary 2022-23 file not found: {salary_file}")
            return False
        
        try:
            # Load salary data
            salary_df = pd.read_csv(salary_file)
            logger.info(f"Loaded {len(salary_df)} salary records")
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get player name to ID mapping
            cursor.execute("SELECT player_id, player_name FROM Players")
            player_map = {name: player_id for player_id, name in cursor.fetchall()}
            
            # Match salary data to player IDs
            matched_count = 0
            for _, row in salary_df.iterrows():
                player_name = row['Player']
                salary = row['Salary']
                
                # Try to find matching player
                player_id = None
                for db_name, db_id in player_map.items():
                    if player_name.lower() in db_name.lower() or db_name.lower() in player_name.lower():
                        player_id = db_id
                        break
                
                if player_id:
                    # Insert salary data
                    cursor.execute("""
                        INSERT OR REPLACE INTO PlayerSalaries (player_id, season_id, salary)
                        VALUES (?, ?, ?)
                    """, (player_id, '2022-23', salary))
                    matched_count += 1
            
            conn.commit()
            logger.info(f"✅ Inserted {matched_count} salary records for 2022-23")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error populating salary 2022-23 data: {e}")
            return False
    
    def validate_missing_data(self) -> None:
        """Validate that we have the required 2022-23 data."""
        logger.info("Validating 2022-23 data completeness...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check DARKO data
        cursor.execute("SELECT COUNT(*) FROM PlayerSkills WHERE season_id = '2022-23'")
        darko_count = cursor.fetchone()[0]
        logger.info(f"DARKO 2022-23 records: {darko_count}")
        
        # Check salary data
        cursor.execute("SELECT COUNT(*) FROM PlayerSalaries WHERE season_id = '2022-23'")
        salary_count = cursor.fetchone()[0]
        logger.info(f"Salary 2022-23 records: {salary_count}")
        
        # Check archetype data
        cursor.execute("SELECT COUNT(*) FROM PlayerArchetypeFeatures_2022_23")
        archetype_count = cursor.fetchone()[0]
        logger.info(f"Archetype 2022-23 records: {archetype_count}")
        
        conn.close()
        
        if darko_count > 0 and salary_count > 0 and archetype_count > 0:
            logger.info("✅ All required 2022-23 data is available!")
            return True
        else:
            logger.warning("❌ Missing required 2022-23 data!")
            logger.warning("Need: DARKO ratings, salary data, and archetype features")
            return False

def main():
    """Main function to collect missing 2022-23 data."""
    collector = MissingDataCollector()
    
    logger.info("=== Collecting Missing 2022-23 Data ===")
    
    # Check if we already have the data
    if collector.validate_missing_data():
        logger.info("✅ All 2022-23 data is already available!")
        return
    
    # Try to collect DARKO data
    darko_success = collector.collect_darko_2022_23()
    
    # Try to collect salary data
    salary_success = collector.collect_salary_2022_23()
    
    if not darko_success or not salary_success:
        logger.warning("Creating placeholder data structure...")
        collector.create_placeholder_data()
        logger.warning("Please manually collect the real data and replace the placeholder files!")
        return
    
    # Populate the data if we have it
    if darko_success:
        collector.populate_darko_2022_23()
    
    if salary_success:
        collector.populate_salary_2022_23()
    
    # Final validation
    collector.validate_missing_data()

if __name__ == "__main__":
    main()
