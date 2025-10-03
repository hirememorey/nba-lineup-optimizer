#!/usr/bin/env python3
"""
Create Stratified Data Sample for Bayesian Model Prototype

This script creates a stratified sample of possessions that ensures all possible
matchup combinations (offensive supercluster vs defensive supercluster) are 
represented in the sample. This is critical for the Bayesian model to have
data to estimate every parameter.

Author: AI Assistant
Date: October 3, 2025
"""

import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StratifiedSampleCreator:
    """Creates stratified samples of possession data for Bayesian modeling."""
    
    def __init__(self, db_path: str = "src/nba_stats/db/nba_stats.db"):
        self.db_path = db_path
        self.conn = None
        
    def connect_database(self) -> bool:
        """Connect to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            logger.info(f"Connected to database: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def load_possession_data(self) -> pd.DataFrame:
        """Load possession data with lineup and archetype information."""
        logger.info("Loading possession data...")
        
        query = """
        SELECT 
            p.game_id,
            p.event_num,
            p.home_player_1_id, p.home_player_2_id, p.home_player_3_id, 
            p.home_player_4_id, p.home_player_5_id,
            p.away_player_1_id, p.away_player_2_id, p.away_player_3_id, 
            p.away_player_4_id, p.away_player_5_id,
            p.offensive_team_id,
            p.defensive_team_id,
            -- Add outcome data if available
            p.score,
            p.score_margin
        FROM Possessions p
        WHERE p.home_player_1_id IS NOT NULL 
        AND p.home_player_2_id IS NOT NULL 
        AND p.home_player_3_id IS NOT NULL 
        AND p.home_player_4_id IS NOT NULL 
        AND p.home_player_5_id IS NOT NULL
        AND p.away_player_1_id IS NOT NULL 
        AND p.away_player_2_id IS NOT NULL 
        AND p.away_player_3_id IS NOT NULL 
        AND p.away_player_4_id IS NOT NULL 
        AND p.away_player_5_id IS NOT NULL
        """
        
        possessions = pd.read_sql_query(query, self.conn)
        logger.info(f"Loaded {len(possessions)} possessions with complete lineup data")
        
        return possessions
    
    def load_player_archetypes(self) -> Dict[int, int]:
        """Load player archetype mappings."""
        logger.info("Loading player archetype mappings...")
        
        query = """
        SELECT 
            pa.player_id,
            pa.archetype_id
        FROM PlayerSeasonArchetypes pa
        WHERE pa.season = '2024-25'
        """
        
        archetype_df = pd.read_sql_query(query, self.conn)
        player_to_archetype = dict(zip(archetype_df['player_id'], archetype_df['archetype_id']))
        
        logger.info(f"Loaded archetype mappings for {len(player_to_archetype)} players")
        return player_to_archetype
    
    def load_lineup_superclusters(self) -> Dict[str, int]:
        """Load lineup supercluster mappings from JSON file."""
        logger.info("Loading lineup supercluster mappings from JSON file...")
        
        import json
        
        try:
            with open('lineup_supercluster_results/supercluster_assignments.json', 'r') as f:
                data = json.load(f)
                lineup_to_supercluster = data['lineup_assignments']
            
            logger.info(f"Loaded supercluster mappings for {len(lineup_to_supercluster)} lineups")
            return lineup_to_supercluster
        except Exception as e:
            logger.error(f"Failed to load supercluster mappings from JSON: {e}")
            return {}
    
    def create_archetype_lineup_id(self, player_ids: List[int], player_to_archetype: Dict[int, int]) -> str:
        """Create archetype lineup ID from player IDs."""
        archetypes = []
        missing_players = []
        for player_id in player_ids:
            if player_id in player_to_archetype:
                archetypes.append(player_to_archetype[player_id])
            else:
                missing_players.append(player_id)
        
        if missing_players:
            # Log first few missing players for debugging
            if len(missing_players) <= 5:
                logger.debug(f"Missing archetype assignments for players: {missing_players}")
            return None
        
        # Sort archetypes to create consistent lineup ID
        return '_'.join(map(str, sorted(archetypes)))
    
    def load_player_team_mappings(self) -> Dict[int, int]:
        """Load player to team ID mappings."""
        logger.info("Loading player team mappings...")
        
        query = """
        SELECT 
            p.player_id,
            p.team_id
        FROM Players p
        """
        
        team_df = pd.read_sql_query(query, self.conn)
        player_to_team = dict(zip(team_df['player_id'], team_df['team_id']))
        
        logger.info(f"Loaded team mappings for {len(player_to_team)} players")
        return player_to_team

    def add_lineup_metadata(self, possessions: pd.DataFrame, 
                           player_to_archetype: Dict[int, int],
                           lineup_to_supercluster: Dict[str, int],
                           player_to_team: Dict[int, int]) -> pd.DataFrame:
        """Add archetype and supercluster information to possessions."""
        logger.info("Adding lineup metadata to possessions...")
        
        # Create lineup columns
        possessions['home_archetype_lineup'] = None
        possessions['away_archetype_lineup'] = None
        possessions['offensive_supercluster'] = None
        possessions['defensive_supercluster'] = None
        
        valid_possessions = []
        processed_count = 0
        missing_archetype_count = 0
        missing_supercluster_count = 0
        team_mismatch_count = 0
        
        for idx, row in possessions.iterrows():
            processed_count += 1
            if processed_count % 100000 == 0:
                logger.info(f"Processed {processed_count} possessions...")
            # Get home lineup player IDs
            home_lineup = [
                row['home_player_1_id'], row['home_player_2_id'], row['home_player_3_id'],
                row['home_player_4_id'], row['home_player_5_id']
            ]
            
            # Get away lineup player IDs  
            away_lineup = [
                row['away_player_1_id'], row['away_player_2_id'], row['away_player_3_id'],
                row['away_player_4_id'], row['away_player_5_id']
            ]
            
            # Create archetype lineup IDs
            home_archetype_lineup = self.create_archetype_lineup_id(home_lineup, player_to_archetype)
            away_archetype_lineup = self.create_archetype_lineup_id(away_lineup, player_to_archetype)
            
            if home_archetype_lineup is None or away_archetype_lineup is None:
                missing_archetype_count += 1
                continue
                
            # Get supercluster assignments
            home_supercluster = lineup_to_supercluster.get(home_archetype_lineup)
            away_supercluster = lineup_to_supercluster.get(away_archetype_lineup)
            
            if home_supercluster is None or away_supercluster is None:
                missing_supercluster_count += 1
                continue
            
            # Determine offensive and defensive superclusters
            # Get team IDs for home and away lineups
            home_team_id = player_to_team.get(home_lineup[0])  # All players in lineup should have same team
            away_team_id = player_to_team.get(away_lineup[0])
            
            if home_team_id is None or away_team_id is None:
                continue
            
            # Determine which lineup is on offense
            if row['offensive_team_id'] == home_team_id:
                offensive_supercluster = home_supercluster
                defensive_supercluster = away_supercluster
            elif row['offensive_team_id'] == away_team_id:
                offensive_supercluster = away_supercluster
                defensive_supercluster = home_supercluster
            else:
                # Skip if offensive_team_id doesn't match either lineup
                team_mismatch_count += 1
                continue
            
            # Update the row
            row['home_archetype_lineup'] = home_archetype_lineup
            row['away_archetype_lineup'] = away_archetype_lineup
            row['offensive_supercluster'] = offensive_supercluster
            row['defensive_supercluster'] = defensive_supercluster
            
            valid_possessions.append(row)
        
        result_df = pd.DataFrame(valid_possessions)
        logger.info(f"Added metadata to {len(result_df)} possessions")
        logger.info(f"Debug stats: processed={processed_count}, missing_archetype={missing_archetype_count}, missing_supercluster={missing_supercluster_count}, team_mismatch={team_mismatch_count}")
        
        return result_df
    
    def create_stratified_sample(self, possessions: pd.DataFrame, 
                                target_size: int = 10000) -> pd.DataFrame:
        """Create stratified sample ensuring all matchup combinations are represented."""
        logger.info(f"Creating stratified sample of {target_size} possessions...")
        
        # Count possessions by matchup
        matchup_counts = possessions.groupby(['offensive_supercluster', 'defensive_supercluster']).size()
        logger.info(f"Found {len(matchup_counts)} unique matchups")
        
        # Calculate minimum samples per matchup to ensure representation
        min_samples_per_matchup = max(1, target_size // (len(matchup_counts) * 2))
        logger.info(f"Targeting {min_samples_per_matchup} samples per matchup")
        
        sampled_possessions = []
        
        for (off_super, def_super), count in matchup_counts.items():
            # Get possessions for this matchup
            matchup_possessions = possessions[
                (possessions['offensive_supercluster'] == off_super) & 
                (possessions['defensive_supercluster'] == def_super)
            ]
            
            # Sample from this matchup
            n_samples = min(min_samples_per_matchup, len(matchup_possessions))
            if n_samples > 0:
                sampled = matchup_possessions.sample(n=n_samples, random_state=42)
                sampled_possessions.append(sampled)
                logger.info(f"Sampled {n_samples} possessions for matchup ({off_super}, {def_super})")
        
        # Combine all samples
        if sampled_possessions:
            result = pd.concat(sampled_possessions, ignore_index=True)
            logger.info(f"Created stratified sample with {len(result)} possessions")
            
            # Verify all matchups are represented
            final_matchups = result.groupby(['offensive_supercluster', 'defensive_supercluster']).size()
            logger.info(f"Final sample covers {len(final_matchups)} unique matchups")
            
            return result
        else:
            logger.error("No valid possessions found for sampling")
            return pd.DataFrame()
    
    def save_sample(self, sample_df: pd.DataFrame, output_path: str = "stratified_sample_10k.csv"):
        """Save the stratified sample to CSV."""
        logger.info(f"Saving stratified sample to {output_path}")
        sample_df.to_csv(output_path, index=False)
        logger.info(f"Sample saved with {len(sample_df)} possessions")
        
        # Save summary statistics
        summary_path = output_path.replace('.csv', '_summary.txt')
        with open(summary_path, 'w') as f:
            f.write(f"Stratified Sample Summary\n")
            f.write(f"========================\n\n")
            f.write(f"Total possessions: {len(sample_df)}\n")
            f.write(f"Unique matchups: {len(sample_df.groupby(['offensive_supercluster', 'defensive_supercluster']))}\n")
            f.write(f"Archetype distribution:\n")
            f.write(f"  Big Men: {len(sample_df[sample_df['home_archetype_lineup'].str.contains('0')])}\n")
            f.write(f"  Primary Ball Handlers: {len(sample_df[sample_df['home_archetype_lineup'].str.contains('1')])}\n")
            f.write(f"  Role Players: {len(sample_df[sample_df['home_archetype_lineup'].str.contains('2')])}\n")
        
        logger.info(f"Summary saved to {summary_path}")
    
    def run(self, target_size: int = 10000):
        """Run the complete stratified sampling process."""
        logger.info("Starting stratified sample creation...")
        
        if not self.connect_database():
            return False
        
        try:
            # Load data
            possessions = self.load_possession_data()
            player_to_archetype = self.load_player_archetypes()
            lineup_to_supercluster = self.load_lineup_superclusters()
            player_to_team = self.load_player_team_mappings()
            
            # Add metadata
            possessions_with_metadata = self.add_lineup_metadata(
                possessions, player_to_archetype, lineup_to_supercluster, player_to_team
            )
            
            if len(possessions_with_metadata) == 0:
                logger.error("No possessions with valid metadata found")
                return False
            
            # Create stratified sample
            sample = self.create_stratified_sample(possessions_with_metadata, target_size)
            
            if len(sample) == 0:
                logger.error("Failed to create stratified sample")
                return False
            
            # Save sample
            self.save_sample(sample)
            
            logger.info("Stratified sample creation completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error during stratified sample creation: {e}")
            return False
        finally:
            if self.conn:
                self.conn.close()

def main():
    """Main function."""
    creator = StratifiedSampleCreator()
    success = creator.run(target_size=10000)
    
    if success:
        print("✅ Stratified sample created successfully!")
    else:
        print("❌ Failed to create stratified sample")
        exit(1)

if __name__ == "__main__":
    main()
