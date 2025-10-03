#!/usr/bin/env python3
"""
Shot Metrics Fetcher for NBA Lineup Optimizer
Fetches shot data from NBA Stats API and converts to canonical metrics

This script fetches shot location data from the NBA Stats API and converts
the distance range data into the canonical metrics needed for player archetype
classification.
"""

import requests
import sqlite3
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import logging
import time
from typing import Dict, List, Optional, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('shot_metrics_fetcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ShotMetricsFetcher:
    def __init__(self, db_path="src/nba_stats/db/nba_stats.db"):
        self.db_path = db_path
        self.conn = None
        self.api_headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Origin': 'https://www.nba.com',
            'Pragma': 'no-cache',
            'Referer': 'https://www.nba.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }
        self.timeout = 30
        
    def connect_database(self):
        """Connect to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            logger.info(f"Connected to database: {self.db_path}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def fetch_shot_locations_data(self, season="2024-25") -> Optional[Dict]:
        """Fetch shot locations data from NBA Stats API."""
        logger.info(f"Fetching shot locations data for season {season}...")
        
        url = "https://stats.nba.com/stats/leaguedashplayershotlocations"
        params = {
            'College': '',
            'Conference': '',
            'Country': '',
            'DateFrom': '',
            'DateTo': '',
            'DistanceRange': '5ft Range',
            'Division': '',
            'DraftPick': '',
            'DraftYear': '',
            'GameScope': '',
            'GameSegment': '',
            'Height': '',
            'ISTRound': '',
            'LastNGames': '0',
            'Location': '',
            'MeasureType': 'Base',
            'Month': '0',
            'OpponentTeamID': '0',
            'Outcome': '',
            'PORound': '0',
            'PaceAdjust': 'N',
            'PerMode': 'PerGame',
            'Period': '0',
            'PlayerExperience': '',
            'PlayerPosition': '',
            'PlusMinus': 'N',
            'Rank': 'N',
            'Season': season,
            'SeasonSegment': '',
            'SeasonType': 'Regular Season',
            'ShotClockRange': '',
            'StarterBench': '',
            'TeamID': '0',
            'VsConference': '',
            'VsDivision': '',
            'Weight': ''
        }
        
        try:
            response = requests.get(url, params=params, headers=self.api_headers, timeout=self.timeout)
            
            if response.status_code != 200:
                logger.error(f"API request failed with status {response.status_code}: {response.text}")
                return None
            
            data = response.json()
            
            # Handle both dict and list formats for resultSets
            if isinstance(data.get('resultSets'), dict):
                result_set = data['resultSets']
            elif isinstance(data.get('resultSets'), list) and data['resultSets']:
                result_set = data['resultSets'][0]
            else:
                logger.error("Invalid resultSets format in API response")
                return None
            
            if 'rowSet' not in result_set:
                logger.error("Missing rowSet in API response")
                return None
            
            rows = result_set['rowSet']
            headers = result_set.get('headers', [])
            
            logger.info(f"Successfully fetched {len(rows)} players' shot data")
            return {
                'headers': headers,
                'rows': rows,
                'season': season
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    def convert_shot_data_to_metrics(self, shot_data: Dict) -> pd.DataFrame:
        """Convert shot location data to canonical metrics."""
        logger.info("Converting shot data to canonical metrics...")
        
        headers = shot_data['headers']
        rows = shot_data['rows']
        
        # Create DataFrame from API data
        # The headers structure has two objects:
        # 1. SHOT_CATEGORY with distance range names
        # 2. columns with the actual column names for the data
        column_names = []
        
        if isinstance(headers, list) and len(headers) >= 2:
            # Find the 'columns' header object which contains the actual column names
            for header in headers:
                if isinstance(header, dict) and header.get('name') == 'columns':
                    column_names = header.get('columnNames', [])
                    break
        
        # Fallback: create generic column names if we couldn't find the right structure
        if not column_names:
            column_names = [f'col_{i}' for i in range(len(rows[0]) if rows else 0)]
        
        # Handle duplicate column names by making them unique
        unique_columns = []
        for i, col in enumerate(column_names):
            if column_names.count(col) > 1:
                # Find how many times this column name has appeared before
                count = column_names[:i].count(col)
                unique_columns.append(f"{col}_{count}" if count > 0 else col)
            else:
                unique_columns.append(col)
        
        df = pd.DataFrame(rows, columns=unique_columns)
        
        # Debug: print column information
        logger.info(f"DataFrame created with {len(df.columns)} columns")
        logger.info(f"Column names: {list(df.columns)}")
        logger.info(f"First few rows shape: {df.shape}")
        
        # Map API columns to our canonical metrics
        # The API returns data in this format:
        # PLAYER_ID, PLAYER_NAME, TEAM_ID, TEAM_ABBREVIATION, AGE, NICKNAME,
        # FGM, FGA, FG_PCT (for each distance range)
        # Distance ranges: Less Than 5 ft, 5-9 ft, 10-14 ft, 15-19 ft, 20-24 ft, 25-29 ft, 30-34 ft, 35-39 ft, 40+ ft
        
        # Extract player info
        player_info = df[['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ID', 'TEAM_ABBREVIATION']].copy()
        
        # Debug: check data types
        logger.info(f"Player info columns: {list(player_info.columns)}")
        logger.info(f"Player info shape: {player_info.shape}")
        logger.info(f"Sample player data: {player_info.head(2)}")
        
        # Calculate shot distance metrics
        metrics = {}
        
        # The API returns data in this format:
        # Columns 0-5: PLAYER_ID, PLAYER_NAME, TEAM_ID, TEAM_ABBREVIATION, AGE, NICKNAME
        # Columns 6-32: FGM, FGA, FG_PCT for each of 9 distance ranges (3 columns each)
        # Distance ranges: Less Than 5 ft, 5-9 ft, 10-14 ft, 15-19 ft, 20-24 ft, 25-29 ft, 30-34 ft, 35-39 ft, 40+ ft
        
        # Calculate average shot distance
        # Initialize with zeros that match the DataFrame length
        total_fga = pd.Series([0.0] * len(df), index=df.index)
        weighted_distance = pd.Series([0.0] * len(df), index=df.index)
        
        # Distance midpoints for each range
        distances = [2.5, 7.0, 12.0, 17.0, 22.0, 27.0, 32.0, 37.0, 42.0]
        
        # Process each distance range (9 ranges total)
        for i in range(9):
            try:
                # Each range has 3 columns: FGM, FGA, FG_PCT
                # Starting from column 6, each range takes 3 columns
                fga_col_idx = 6 + (i * 3) + 1  # FGA is the second column in each group
                fgm_col_idx = 6 + (i * 3)      # FGM is the first column in each group
                
                logger.info(f"Processing range {i}: FGA col {fga_col_idx}, FGM col {fgm_col_idx}")
                
                if fga_col_idx < len(df.columns) and fgm_col_idx < len(df.columns):
                    fga_col = df.columns[fga_col_idx]
                    fgm_col = df.columns[fgm_col_idx]
                    
                    logger.info(f"  FGA column: {fga_col}, FGM column: {fgm_col}")
                    
                    # Get values and convert to numeric
                    logger.info(f"  FGA column data type: {type(df[fga_col])}")
                    logger.info(f"  FGA column sample: {df[fga_col].head()}")
                    logger.info(f"  FGA column dtype: {df[fga_col].dtype}")
                    
                    fga_values = pd.to_numeric(df[fga_col], errors='coerce').fillna(0)
                    fgm_values = pd.to_numeric(df[fgm_col], errors='coerce').fillna(0)
                    
                    logger.info(f"  FGA values shape: {fga_values.shape}, type: {type(fga_values)}")
                    logger.info(f"  FGM values shape: {fgm_values.shape}, type: {type(fgm_values)}")
                    
                    # Add to weighted average
                    total_fga += fga_values
                    weighted_distance += fga_values * distances[i]
                    
                    logger.info(f"  Updated total_fga shape: {total_fga.shape}")
                    logger.info(f"  Updated weighted_distance shape: {weighted_distance.shape}")
                else:
                    logger.warning(f"  Column indices out of range: {fga_col_idx}, {fgm_col_idx}")
            except Exception as e:
                logger.error(f"Error processing range {i}: {e}")
                raise
        
        # Calculate average shot distance (avoid division by zero)
        metrics['AVGDIST'] = (weighted_distance / (total_fga + 1e-6)).fillna(0)
        
        # Debug: check metrics calculation
        logger.info(f"Total FGA shape: {total_fga.shape if hasattr(total_fga, 'shape') else 'scalar'}")
        logger.info(f"Weighted distance shape: {weighted_distance.shape if hasattr(weighted_distance, 'shape') else 'scalar'}")
        logger.info(f"AVGDIST shape: {metrics['AVGDIST'].shape if hasattr(metrics['AVGDIST'], 'shape') else 'scalar'}")
        
        # Calculate shot distribution ratios with better handling of small denominators
        # Zone to 3-point range ratio (0-5 ft / 25-29 ft)
        zone_fga = pd.to_numeric(df[df.columns[7]], errors='coerce').fillna(0)  # Less Than 5 ft FGA
        three_fga = pd.to_numeric(df[df.columns[22]], errors='coerce').fillna(0)  # 25-29 ft FGA
        
        # Only calculate ratio if both values are meaningful (> 0.1)
        zone_three_ratio = pd.Series([0.0] * len(df), index=df.index)
        valid_mask = (zone_fga > 0.1) & (three_fga > 0.1)
        zone_three_ratio[valid_mask] = zone_fga[valid_mask] / three_fga[valid_mask]
        metrics['Zto3r'] = zone_three_ratio.clip(0, 10)  # Cap at 10 to prevent extreme values
        
        # Three to ten range ratio (5-9 ft / 15-19 ft)
        three_to_ten_fga = pd.to_numeric(df[df.columns[10]], errors='coerce').fillna(0)  # 5-9 ft FGA
        ten_to_sixteen_fga = pd.to_numeric(df[df.columns[19]], errors='coerce').fillna(0)  # 15-19 ft FGA
        
        three_ten_ratio = pd.Series([0.0] * len(df), index=df.index)
        valid_mask = (three_to_ten_fga > 0.1) & (ten_to_sixteen_fga > 0.1)
        three_ten_ratio[valid_mask] = three_to_ten_fga[valid_mask] / ten_to_sixteen_fga[valid_mask]
        metrics['THto10r'] = three_ten_ratio.clip(0, 10)
        
        # Ten to sixteen range ratio (15-19 ft / 25-29 ft)
        ten_to_sixteen_fga = pd.to_numeric(df[df.columns[19]], errors='coerce').fillna(0)  # 15-19 ft FGA
        sixteen_to_three_fga = pd.to_numeric(df[df.columns[22]], errors='coerce').fillna(0)  # 25-29 ft FGA
        
        ten_sixteen_ratio = pd.Series([0.0] * len(df), index=df.index)
        valid_mask = (ten_to_sixteen_fga > 0.1) & (sixteen_to_three_fga > 0.1)
        ten_sixteen_ratio[valid_mask] = ten_to_sixteen_fga[valid_mask] / sixteen_to_three_fga[valid_mask]
        metrics['TENto16r'] = ten_sixteen_ratio.clip(0, 10)
        
        # Sixteen to 3PT range ratio (25-29 ft / 30-34 ft)
        sixteen_to_three_fga = pd.to_numeric(df[df.columns[22]], errors='coerce').fillna(0)  # 25-29 ft FGA
        three_plus_fga = pd.to_numeric(df[df.columns[25]], errors='coerce').fillna(0)  # 30-34 ft FGA
        
        sixteen_three_ratio = pd.Series([0.0] * len(df), index=df.index)
        valid_mask = (sixteen_to_three_fga > 0.1) & (three_plus_fga > 0.1)
        sixteen_three_ratio[valid_mask] = sixteen_to_three_fga[valid_mask] / three_plus_fga[valid_mask]
        metrics['SIXTto3PTr'] = sixteen_three_ratio.clip(0, 10)
        
        # Combine player info with metrics
        result_df = player_info.copy()
        for metric_name, metric_values in metrics.items():
            result_df[metric_name] = metric_values
        
        logger.info(f"Converted shot data to {len(metrics)} canonical metrics")
        return result_df, total_fga
    
    def save_shot_metrics(self, metrics_df: pd.DataFrame, total_fga: pd.Series, season: str):
        """Save shot metrics to the database."""
        logger.info(f"Saving shot metrics for {len(metrics_df)} players...")
        
        try:
            # Create or update shot metrics table
            cursor = self.conn.cursor()
            
            # Clear existing data for this season
            cursor.execute("DELETE FROM PlayerShotMetrics WHERE season = ?", (season,))
            
            # Remove duplicates from metrics_df (keep first occurrence)
            metrics_df = metrics_df.drop_duplicates(subset=['PLAYER_ID'], keep='first')
            logger.info(f"Removed duplicates, processing {len(metrics_df)} unique players")
            
            # Insert new data
            for idx, row in metrics_df.iterrows():
                # Calculate total shots for this player
                player_total_shots = int(total_fga.iloc[idx])
                
                cursor.execute("""
                    INSERT OR REPLACE INTO PlayerShotMetrics 
                    (player_id, season, avgdist, zto3r, thto10r, tento16r, sixtto3ptr, total_shots)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(row['PLAYER_ID']),
                    season,
                    float(row['AVGDIST']),
                    float(row['Zto3r']),
                    float(row['THto10r']),
                    float(row['TENto16r']),
                    float(row['SIXTto3PTr']),
                    player_total_shots
                ))
            
            self.conn.commit()
            logger.info(f"Successfully saved shot metrics for {len(metrics_df)} players")
            
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            self.conn.rollback()
            raise
    
    def update_player_archetype_features(self, season: str):
        """Update PlayerArchetypeFeatures table with shot metrics."""
        logger.info("Updating PlayerArchetypeFeatures with shot metrics...")
        
        try:
            cursor = self.conn.cursor()
            
            # Get shot metrics for this season
            shot_metrics = pd.read_sql_query("""
                SELECT player_id, avgdist, zto3r, thto10r, tento16r, sixtto3ptr
                FROM PlayerShotMetrics 
                WHERE season = ?
            """, self.conn, params=(season,))
            
            if shot_metrics.empty:
                logger.warning("No shot metrics found for this season")
                return
            
            # Update PlayerArchetypeFeatures
            for _, row in shot_metrics.iterrows():
                cursor.execute("""
                    UPDATE PlayerArchetypeFeatures 
                    SET AVGDIST = ?, Zto3r = ?, THto10r = ?, TENto16r = ?, SIXTto3PTr = ?
                    WHERE player_id = ? AND season = ?
                """, (
                    float(row['avgdist']),
                    float(row['zto3r']),
                    float(row['thto10r']),
                    float(row['tento16r']),
                    float(row['sixtto3ptr']),
                    int(row['player_id']),
                    season
                ))
            
            self.conn.commit()
            logger.info(f"Updated PlayerArchetypeFeatures for {len(shot_metrics)} players")
            
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            self.conn.rollback()
            raise
    
    def run_fetch_and_update(self, season="2024-25"):
        """Main function to fetch shot data and update the database."""
        logger.info("Starting shot metrics fetch and update process...")
        
        if not self.connect_database():
            logger.error("Failed to connect to database")
            return False
        
        try:
            # Fetch shot data from API
            shot_data = self.fetch_shot_locations_data(season)
            if not shot_data:
                logger.error("Failed to fetch shot data from API")
                return False
            
            # Convert to canonical metrics
            metrics_df, total_fga = self.convert_shot_data_to_metrics(shot_data)
            if metrics_df.empty:
                logger.error("Failed to convert shot data to metrics")
                return False
            
            # Save shot metrics
            self.save_shot_metrics(metrics_df, total_fga, season)
            
            # Update PlayerArchetypeFeatures
            self.update_player_archetype_features(season)
            
            logger.info("Shot metrics fetch and update completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Process failed: {e}")
            return False
        finally:
            if self.conn:
                self.conn.close()

def main():
    """Main execution function."""
    fetcher = ShotMetricsFetcher()
    success = fetcher.run_fetch_and_update()
    
    if success:
        logger.info("Shot metrics fetcher completed successfully!")
    else:
        logger.error("Shot metrics fetcher failed!")
        exit(1)

if __name__ == "__main__":
    main()
