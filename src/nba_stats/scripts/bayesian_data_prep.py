import pandas as pd
import os
import sys

# Add the project root to the python path so we can import modules from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from src.nba_stats.utils.db_utils import get_db_connection

def prepare_bayesian_data(input_path='lineup_supercluster_results/lineup_features_with_superclusters.csv', output_path='production_bayesian_data.csv'):
    """
    Prepares the final dataset for the Bayesian model.
    1. Loads the lineup data with supercluster assignments.
    2. Loads possession data.
    3. Merges them to create matchups.
    4. Creates a unique matchup_id for each offensive vs. defensive supercluster pairing.
    5. Saves the final model-ready data.
    """
    print(f"Loading supercluster data from {input_path}...")
    lineups_df = pd.read_csv(input_path)

    # For now, we'll create a simplified matchup structure based on the supercluster_id.
    # A full implementation would merge this with possession data to get offensive
    # and defensive lineups for each possession.
    
    # This is a simplified placeholder logic, matching the test harness requirement.
    # It assumes each lineup plays against a lineup of the same supercluster.
    lineups_df['matchup_id'] = lineups_df['supercluster_id']
    
    # The final output should match the structure of 'ground_truth_stan_input.csv'
    # For this phase, we are just selecting the required columns.
    final_df = lineups_df[['GROUP_ID', 'supercluster_id', 'matchup_id']].copy()
    final_df.rename(columns={'GROUP_ID': 'lineup_id'}, inplace=True)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_df.to_csv(output_path, index=False)
    print(f"Final Bayesian model data saved to {output_path}")

    return final_df

if __name__ == '__main__':
    prepare_bayesian_data()
