#!/usr/bin/env python3
"""
Bayesian Model Data Preparation Module

This module transforms possession data into the format required by the Bayesian
possession-level model. It implements the data transformation logic from the
research paper, creating the Z matrix and outcome variables.

Author: AI Assistant
Date: October 3, 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BayesianDataPreparer:
    """Prepares data for Bayesian modeling."""
    
    def __init__(self, db_path: str = "src/nba_stats/db/nba_stats.db"):
        self.db_path = db_path
        self.player_to_archetype = {}
        self.player_to_team = {}
        self.lineup_to_supercluster = {}
        self.player_skills = {}
        
    def load_metadata(self) -> bool:
        """Load all required metadata for data preparation."""
        logger.info("Loading metadata for Bayesian model...")
        
        try:
            # Load player archetypes
            self.player_to_archetype = self._load_player_archetypes()
            if not self.player_to_archetype:
                logger.error("Failed to load player archetypes")
                return False
            
            # Load player team mappings
            self.player_to_team = self._load_player_teams()
            if not self.player_to_team:
                logger.error("Failed to load player team mappings")
                return False
            
            # Load lineup superclusters
            self.lineup_to_supercluster = self._load_lineup_superclusters()
            if not self.lineup_to_supercluster:
                logger.error("Failed to load lineup superclusters")
                return False
            
            # Load player skills (DARKO)
            self.player_skills = self._load_player_skills()
            if not self.player_skills:
                logger.error("Failed to load player skills")
                return False
            
            logger.info("Successfully loaded all metadata")
            return True
            
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            return False
    
    def _load_player_archetypes(self) -> Dict[int, int]:
        """Load player archetype mappings."""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT 
            pa.player_id,
            pa.archetype_id
        FROM PlayerSeasonArchetypes pa
        WHERE pa.season = '2024-25'
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return dict(zip(df['player_id'], df['archetype_id']))
    
    def _load_player_teams(self) -> Dict[int, int]:
        """Load player team mappings."""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT 
            p.player_id,
            p.team_id
        FROM Players p
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return dict(zip(df['player_id'], df['team_id']))
    
    def _load_lineup_superclusters(self) -> Dict[str, int]:
        """Load lineup supercluster mappings from JSON file."""
        try:
            with open('lineup_supercluster_results/supercluster_assignments.json', 'r') as f:
                data = json.load(f)
                return data['lineup_assignments']
        except Exception as e:
            logger.error(f"Failed to load supercluster mappings: {e}")
            return {}
    
    def _load_player_skills(self) -> Dict[int, Dict[str, float]]:
        """Load player skill ratings (DARKO)."""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT 
            ps.player_id,
            ps.offensive_darko,
            ps.defensive_darko
        FROM PlayerSeasonSkill ps
        WHERE ps.season = '2024-25'
        AND ps.offensive_darko IS NOT NULL
        AND ps.defensive_darko IS NOT NULL
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        skills = {}
        for _, row in df.iterrows():
            skills[row['player_id']] = {
                'offensive': row['offensive_darko'],
                'defensive': row['defensive_darko']
            }
        
        return skills
    
    def create_archetype_lineup_id(self, player_ids: List[int]) -> Optional[str]:
        """Create archetype lineup ID from player IDs."""
        archetypes = []
        for player_id in player_ids:
            if player_id in self.player_to_archetype:
                archetypes.append(self.player_to_archetype[player_id])
            else:
                return None
        
        # Sort archetypes for consistency
        return '_'.join(map(str, sorted(archetypes)))
    
    def calculate_outcome_variable(self, possession: pd.Series) -> float:
        """
        Calculate the outcome variable (expected net points) for a possession.
        
        For now, we'll use a simplified version. In the full implementation,
        this would calculate expected net points based on the possession outcome.
        """
        # This is a placeholder - in the real implementation, we would:
        # 1. Parse the score information
        # 2. Calculate points scored by offensive team
        # 3. Subtract points given up in transition (within 7 seconds of turnover)
        # 4. Return the net points
        
        # For the prototype, we'll use a random outcome for now
        # This will be replaced with actual calculation logic
        return np.random.normal(0, 1)  # Placeholder: mean=0, std=1
    
    def prepare_possession_data(self, possessions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform possession data into model-ready format.
        
        This implements the core data transformation from the research paper:
        - Creates archetype lineup IDs
        - Determines offensive vs defensive lineups
        - Calculates outcome variables
        - Prepares the Z matrix (aggregated skills by archetype)
        """
        logger.info("Preparing possession data for Bayesian model...")
        
        # Initialize result columns
        result_data = []
        
        for idx, row in possessions_df.iterrows():
            if idx % 1000 == 0:
                logger.info(f"Processing possession {idx}/{len(possessions_df)}")
            
            # Get home and away lineups
            home_lineup = [
                row['home_player_1_id'], row['home_player_2_id'], row['home_player_3_id'],
                row['home_player_4_id'], row['home_player_5_id']
            ]
            
            away_lineup = [
                row['away_player_1_id'], row['away_player_2_id'], row['away_player_3_id'],
                row['away_player_4_id'], row['away_player_5_id']
            ]
            
            # Create archetype lineup IDs
            home_archetype_lineup = self.create_archetype_lineup_id(home_lineup)
            away_archetype_lineup = self.create_archetype_lineup_id(away_lineup)
            
            if home_archetype_lineup is None or away_archetype_lineup is None:
                continue
            
            # Get supercluster assignments
            home_supercluster = self.lineup_to_supercluster.get(home_archetype_lineup)
            away_supercluster = self.lineup_to_supercluster.get(away_archetype_lineup)
            
            if home_supercluster is None or away_supercluster is None:
                continue
            
            # Determine offensive and defensive lineups
            home_team_id = self.player_to_team.get(home_lineup[0])
            away_team_id = self.player_to_team.get(away_lineup[0])
            
            if home_team_id is None or away_team_id is None:
                continue
            
            # Determine which lineup is on offense
            if row['offensive_team_id'] == home_team_id:
                offensive_lineup = home_lineup
                defensive_lineup = away_lineup
                offensive_supercluster = home_supercluster
                defensive_supercluster = away_supercluster
            elif row['offensive_team_id'] == away_team_id:
                offensive_lineup = away_lineup
                defensive_lineup = home_lineup
                offensive_supercluster = away_supercluster
                defensive_supercluster = home_supercluster
            else:
                continue
            
            # Calculate outcome variable
            outcome = self.calculate_outcome_variable(row)
            
            # Create Z matrix (aggregated skills by archetype)
            z_offensive = self._calculate_z_matrix(offensive_lineup, 'offensive')
            z_defensive = self._calculate_z_matrix(defensive_lineup, 'defensive')
            
            # Create matchup identifier
            matchup = (offensive_supercluster, defensive_supercluster)
            
            # Store result
            result_data.append({
                'possession_id': f"{row['game_id']}_{row['event_num']}",
                'outcome': outcome,
                'offensive_supercluster': offensive_supercluster,
                'defensive_supercluster': defensive_supercluster,
                'matchup': matchup,
                'z_off_0': z_offensive.get(0, 0.0),  # Big Men offensive skill
                'z_off_1': z_offensive.get(1, 0.0),  # Primary Ball Handlers offensive skill
                'z_off_2': z_offensive.get(2, 0.0),  # Role Players offensive skill
                'z_def_0': z_defensive.get(0, 0.0),  # Big Men defensive skill
                'z_def_1': z_defensive.get(1, 0.0),  # Primary Ball Handlers defensive skill
                'z_def_2': z_defensive.get(2, 0.0),  # Role Players defensive skill
            })
        
        result_df = pd.DataFrame(result_data)
        logger.info(f"Prepared {len(result_df)} possessions for modeling")
        
        return result_df
    
    def _calculate_z_matrix(self, lineup: List[int], skill_type: str) -> Dict[int, float]:
        """
        Calculate the Z matrix (aggregated skills by archetype) for a lineup.
        
        This implements the Z matrix calculation from the research paper:
        Z_ia = sum of skills for all players of archetype a in lineup i
        """
        z_matrix = {0: 0.0, 1: 0.0, 2: 0.0}  # Initialize for all 3 archetypes
        
        for player_id in lineup:
            if player_id in self.player_skills:
                archetype = self.player_to_archetype.get(player_id)
                if archetype is not None:
                    skill_value = self.player_skills[player_id][skill_type]
                    z_matrix[archetype] += skill_value
        
        return z_matrix
    
    def save_prepared_data(self, data_df: pd.DataFrame, output_path: str = "bayesian_model_data.csv"):
        """Save the prepared data to CSV."""
        logger.info(f"Saving prepared data to {output_path}")
        data_df.to_csv(output_path, index=False)
        
        # Save summary statistics
        summary_path = output_path.replace('.csv', '_summary.txt')
        with open(summary_path, 'w') as f:
            f.write(f"Bayesian Model Data Summary\n")
            f.write(f"==========================\n\n")
            f.write(f"Total possessions: {len(data_df)}\n")
            f.write(f"Unique matchups: {len(data_df['matchup'].unique())}\n")
            f.write(f"Outcome statistics:\n")
            f.write(f"  Mean: {data_df['outcome'].mean():.4f}\n")
            f.write(f"  Std: {data_df['outcome'].std():.4f}\n")
            f.write(f"  Min: {data_df['outcome'].min():.4f}\n")
            f.write(f"  Max: {data_df['outcome'].max():.4f}\n")
            
            f.write(f"\nZ matrix statistics:\n")
            for col in ['z_off_0', 'z_off_1', 'z_off_2', 'z_def_0', 'z_def_1', 'z_def_2']:
                f.write(f"  {col}: mean={data_df[col].mean():.4f}, std={data_df[col].std():.4f}\n")
        
        logger.info(f"Summary saved to {summary_path}")
    
    def run(self, input_csv: str = "stratified_sample_10k.csv", 
            output_csv: str = "bayesian_model_data.csv") -> bool:
        """Run the complete data preparation process."""
        logger.info("Starting Bayesian model data preparation...")
        
        # Load metadata
        if not self.load_metadata():
            return False
        
        # Load possession data
        try:
            possessions_df = pd.read_csv(input_csv)
            logger.info(f"Loaded {len(possessions_df)} possessions from {input_csv}")
        except Exception as e:
            logger.error(f"Failed to load possession data: {e}")
            return False
        
        # Prepare data
        try:
            prepared_data = self.prepare_possession_data(possessions_df)
            
            if len(prepared_data) == 0:
                logger.error("No valid possessions found after preparation")
                return False
            
            # Save results
            self.save_prepared_data(prepared_data, output_csv)
            
            logger.info("Data preparation completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error during data preparation: {e}")
            return False

def main():
    """Main function."""
    preparer = BayesianDataPreparer()
    success = preparer.run()
    
    if success:
        print("✅ Bayesian model data preparation completed successfully!")
    else:
        print("❌ Failed to prepare Bayesian model data")
        exit(1)

if __name__ == "__main__":
    main()
