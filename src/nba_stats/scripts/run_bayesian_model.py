"""
This script implements the Bayesian regression model to evaluate lineup effectiveness.
"""

import pandas as pd
import numpy as np
from ..db.connection import get_db_connection
from ..config import settings
from ..api.client import NBAStatsClient
from ..utils.logger import logger
import cmdstanpy
import os
import random


def load_data():
    """
    Loads all necessary data from the database.
    - Possession data
    - Player skill ratings (DARKO)
    - Player archetypes
    - Lineup superclusters
    """
    logger.info("Loading data from the database.")
    conn = get_db_connection()
    if conn is None:
        logger.error("Could not connect to the database.")
        return None

    try:
        # Load possessions data
        possessions_df = pd.read_sql_query("SELECT * FROM Possessions", conn)
        logger.info(f"Loaded {len(possessions_df)} possessions.")

        # Load player skills
        player_skills_df = pd.read_sql_query("SELECT * FROM PlayerSeasonSkill", conn)
        logger.info(f"Loaded skill ratings for {len(player_skills_df)} player-seasons.")

        # Load player archetypes
        player_archetypes_df = pd.read_sql_query("SELECT * FROM PlayerSeasonArchetypes", conn)
        logger.info(f"Loaded archetypes for {len(player_archetypes_df)} player-seasons.")

        # Load lineup superclusters
        lineup_superclusters_df = pd.read_sql_query("SELECT * FROM ArchetypeLineups", conn)
        logger.info(f"Loaded {len(lineup_superclusters_df)} lineup supercluster assignments.")
        
        # Load supercluster definitions
        superclusters_df = pd.read_sql_query("SELECT * FROM LineupSuperclusters", conn)
        logger.info(f"Loaded {len(superclusters_df)} supercluster definitions.")


        return {
            "possessions": possessions_df,
            "player_skills": player_skills_df,
            "player_archetypes": player_archetypes_df,
            "lineup_superclusters": lineup_superclusters_df,
            "supercluster_definitions": superclusters_df
        }
    except Exception as e:
        logger.error(f"Error loading data: {e}", exc_info=True)
        return None
    finally:
        if conn:
            conn.close()


def _calculate_net_points(df):
    """
    Calculate the net points for each possession, accounting for transition points after turnovers.
    """
    df['points_scored'] = 0
    df['turnover'] = df['event_type'] == 5 # Event type 5 is a turnover

    # Simplified logic to find points scored
    for index, row in df.iterrows():
        if row['event_type'] == 1: # Shot made
            if '3PT' in str(row['home_description']) or '3PT' in str(row['visitor_description']):
                df.loc[index, 'points_scored'] = 3
            else:
                df.loc[index, 'points_scored'] = 2
        elif row['event_type'] == 3: # Free throw
            df.loc[index, 'points_scored'] = 1
    
    # Account for transition points
    net_points = df['points_scored'].copy()
    turnover_indices = df[df['turnover']].index
    for i in turnover_indices:
        # Look ahead within a small window of events for a score by the other team
        game_id = df.loc[i, 'game_id']
        current_period = df.loc[i, 'period']
        defensive_team_id = df.loc[i, 'defensive_team_id']
        
        future_events = df[(df.index > i) & (df.index < i + 10) & (df['game_id'] == game_id) & (df['period'] == current_period)]
        
        transition_score = future_events[
            (future_events['offensive_team_id'] == defensive_team_id) &
            (future_events['points_scored'] > 0)
        ]
        
        if not transition_score.empty:
            # Subtract the points scored in transition from the turnover "possession"
            net_points.loc[i] -= transition_score.iloc[0]['points_scored']

    return net_points


def prepare_model_input(data):
    """
    Prepares the data for the Stan model.
    Constructs the feature vectors as described in Formula (2.5).
    """
    logger.info("Preparing model input.")
    
    possessions_df = data['possessions'].copy()
    player_archetypes_df = data['player_archetypes']
    player_skills_df = data['player_skills']
    lineup_superclusters_df = data['lineup_superclusters']

    # Convert season to string to ensure consistent merge keys
    possessions_df['season'] = possessions_df['season'].astype(str)
    player_archetypes_df['season'] = player_archetypes_df['season'].astype(str)
    player_skills_df['season'] = player_skills_df['season'].astype(str)
    
    # Create a unique season identifier for each possession based on game_id
    possessions_df['season'] = possessions_df['game_id'].str[:4].apply(lambda x: f"{x}-{str(int(x[2:])+1).zfill(2)}")


    # Merge archetypes and skills onto possessions for each of the 10 players
    for i in range(1, 6):
        # Home players
        possessions_df = pd.merge(possessions_df, player_archetypes_df, 
                                  left_on=[f'home_player_{i}_id', 'season'], 
                                  right_on=['player_id', 'season'], 
                                  how='left', suffixes=('', f'_home_{i}_arch'))
        possessions_df = pd.merge(possessions_df, player_skills_df, 
                                  left_on=[f'home_player_{i}_id', 'season'], 
                                  right_on=['player_id', 'season'], 
                                  how='left', suffixes=('', f'_home_{i}_skill'))
        # Away players
        possessions_df = pd.merge(possessions_df, player_archetypes_df, 
                                  left_on=[f'away_player_{i}_id', 'season'], 
                                  right_on=['player_id', 'season'], 
                                  how='left', suffixes=('', f'_away_{i}_arch'))
        possessions_df = pd.merge(possessions_df, player_skills_df, 
                                  left_on=[f'away_player_{i}_id', 'season'], 
                                  right_on=['player_id', 'season'], 
                                  how='left', suffixes=('', f'_away_{i}_skill'))
    
    # Fill missing archetypes/skills with a default value (e.g., 0 or a specific category)
    # This is important for robustness
    for col in possessions_df.columns:
        if 'archetype_id' in col:
            possessions_df[col].fillna(0, inplace=True) # Assuming 0 is a safe default
        if 'darko' in col:
            possessions_df[col].fillna(0.0, inplace=True)

    # Determine offensive and defensive lineups
    possessions_df['offensive_lineup_archetypes'] = possessions_df.apply(
        lambda row: tuple(sorted([row[f'archetype_id_home_{i}'] for i in range(1, 6)])) if row['offensive_team_id'] == row['home_team_id'] else tuple(sorted([row[f'archetype_id_away_{i}'] for i in range(1, 6)])),
        axis=1
    )
    possessions_df['defensive_lineup_archetypes'] = possessions_df.apply(
        lambda row: tuple(sorted([row[f'archetype_id_away_{i}'] for i in range(1, 6)])) if row['offensive_team_id'] == row['home_team_id'] else tuple(sorted([row[f'archetype_id_home_{i}'] for i in range(1, 6)])),
        axis=1
    )

    # Map lineups to superclusters
    lineup_superclusters_df['archetype_lineup_id'] = lineup_superclusters_df['archetype_lineup_id'].apply(lambda x: tuple(sorted(map(int, x.split('-')))))
    
    possessions_df['offensive_supercluster_id'] = possessions_df['offensive_lineup_archetypes'].map(lineup_superclusters_df.set_index('archetype_lineup_id')['supercluster_id'])
    possessions_df['defensive_supercluster_id'] = possessions_df['defensive_lineup_archetypes'].map(lineup_superclusters_df.set_index('archetype_lineup_id')['supercluster_id'])

    # Construct Z_off and Z_def
    num_archetypes = int(player_archetypes_df['archetype_id'].nunique())
    Z_off = np.zeros((len(possessions_df), num_archetypes))
    Z_def = np.zeros((len(possessions_df), num_archetypes))

    for index, row in possessions_df.iterrows():
        for i in range(1, 6):
            if row['offensive_team_id'] == row['home_team_id']:
                off_archetype_col = f'archetype_id'
                off_skill_col = f'offensive_darko_home_{i}_skill'
                def_archetype_col = f'archetype_id_away_{i}_arch'
                def_skill_col = f'defensive_darko_away_{i}_skill'
            else:
                off_archetype_col = f'archetype_id_away_{i}_arch'
                off_skill_col = f'offensive_darko_away_{i}_skill'
                def_archetype_col = f'archetype_id'
                def_skill_col = f'defensive_darko_home_{i}_skill'

            off_archetype = int(row[off_archetype_col])
            off_skill = row[off_skill_col]
            def_archetype = int(row[def_archetype_col])
            def_skill = row[def_skill_col]
            
            if off_archetype > 0:
                Z_off[index, off_archetype - 1] += off_skill
            if def_archetype > 0:
                Z_def[index, def_archetype - 1] += def_skill

    # Define the outcome variable y using net points
    possessions_df['net_points'] = _calculate_net_points(possessions_df)
    y = possessions_df['net_points'].values

    # Create matchup indices
    possessions_df.dropna(subset=['offensive_supercluster_id', 'defensive_supercluster_id'], inplace=True)
    matchup_map = {tuple(x): i+1 for i, x in enumerate(possessions_df[['offensive_supercluster_id', 'defensive_supercluster_id']].drop_duplicates().to_numpy())}
    possessions_df['matchup_index'] = possessions_df.set_index(['offensive_supercluster_id', 'defensive_supercluster_id']).index.map(matchup_map)
    matchup_indices = possessions_df['matchup_index'].values.astype(int)

    # Filter out rows where matchup_index is NaN before creating Z_off and Z_def
    valid_indices = ~possessions_df['matchup_index'].isna()
    possessions_df = possessions_df[valid_indices]
    Z_off = Z_off[valid_indices]
    Z_def = Z_def[valid_indices]
    y = y[valid_indices]
    matchup_indices = matchup_indices[valid_indices]

    return Z_off, Z_def, y, matchup_indices, possessions_df, len(matchup_map)


def run_bayesian_model():
    """
    Main function to run the Bayesian model.
    """
    logger.info("Starting Bayesian model script.")
    
    # 1. Load data
    data = load_data()
    if not data:
        return

    # 2. Prepare model input
    Z_off, Z_def, y, matchup_indices, _, num_matchups = prepare_model_input(data)

    # 3. Define and train the Stan model
    stan_file = os.path.join(os.path.dirname(__file__), '..', 'models', 'bayesian_model.stan')
    try:
        model = cmdstanpy.CmdStanModel(stan_file=stan_file)
    except Exception as e:
        logger.error(f"Failed to compile Stan model: {e}", exc_info=True)
        return

    stan_data = {
        'N': len(y),
        'K': Z_off.shape[1],
        'M': num_matchups,
        'Z_off': Z_off,
        'Z_def': Z_def,
        'y': y,
        'matchup_indices': matchup_indices
    }

    try:
        logger.info("Starting MCMC sampling.")
        fit = model.sample(data=stan_data, chains=1, iter_sampling=1000, iter_warmup=500, seed=123)
        logger.info("MCMC sampling completed.")
        logger.info(fit.summary())
    except Exception as e:
        logger.error(f"Error during MCMC sampling: {e}", exc_info=True)
        return

    # 4. Evaluate lineups and players
    # This is a placeholder for where the full evaluation logic would go.
    # It would require loading all player data, defining opponent teams, etc.
    
    # posterior_samples = fit.stan_variables()
    
    # core_lakers = [2544, 1629029, 1628366] # LeBron, AD, Reaves
    # available_players = [...] # Would be a list of player IDs
    # playoff_teams = [...] # List of team IDs
    
    # best_fit_for_lakers, value = recommend_player(core_lakers, available_players, playoff_teams, posterior_samples, all_player_data)
    # logger.info(f"Recommendation for Lakers: Player ID {best_fit_for_lakers} with value {value}")


def evaluate_lineup(lineup_player_ids, opponent_lineup_ids, posterior_samples, all_player_data):
    """
    Evaluates a given lineup against a specific opponent lineup.
    """
    # This is a placeholder for the complex logic of mapping players to archetypes/skills
    # and then using the posterior samples to calculate E[y(l1, l2)]
    # This will require careful handling of the posterior distributions of beta coefficients.
    
    # For now, returns a random value.
    return random.uniform(-5, 5)

def calculate_lineup_value(lineup_player_ids, opponent_team_ids, posterior_samples, all_player_data):
    """
    Calculates the value of a lineup against a set of representative opponents.
    """
    total_value = 0
    
    # In a real implementation, we would get the primary lineups for each opponent team
    # For now, we'll just use a placeholder opponent lineup
    placeholder_opponent_lineup = [201939, 201942, 202695, 203954, 1629027] # Example: Warriors lineup

    for _ in opponent_team_ids:
        # v(l1, l2) = E[y(l1, l2)] - E[y(l2, l1)]
        value_off = evaluate_lineup(lineup_player_ids, placeholder_opponent_lineup, posterior_samples, all_player_data)
        value_def = evaluate_lineup(placeholder_opponent_lineup, lineup_player_ids, posterior_samples, all_player_data)
        total_value += (value_off - value_def)
        
    return total_value / len(opponent_team_ids)

def recommend_player(core_player_ids, available_player_ids, opponent_team_ids, posterior_samples, all_player_data):
    """
    Recommends the best available player to complete a lineup.
    """
    best_player = None
    max_value = -float('inf')

    for player_id in available_player_ids:
        if player_id not in core_player_ids:
            current_lineup = core_player_ids + [player_id]
            value = calculate_lineup_value(current_lineup, opponent_team_ids, posterior_samples, all_player_data)
            
            if value > max_value:
                max_value = value
                best_player = player_id
                
    return best_player, max_value

if __name__ == '__main__':
    run_bayesian_model() 