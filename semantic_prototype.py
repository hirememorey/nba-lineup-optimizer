"""
Semantic Prototype for Possession-Level Modeling

This module implements the critical "Semantic Prototyping" step that validates
the analytical logic using synthetic data before attempting to use real data.

This addresses the key insight from the pre-mortem: we need fast feedback
on whether our model makes basketball sense before running the expensive
18-hour Bayesian training process.
"""

import sqlite3
import re
import pandas as pd

DB_PATH = "src/nba_stats/db/nba_stats.db"

def calculate_outcome(row):
    """
    Calculates the point value of a possession based on its description.

    Args:
        row (pd.Series): A row from the Possessions DataFrame.

    Returns:
        int: The number of points scored (0, 1, 2, or 3).
    """
    description = row["description"]
    if not isinstance(description, str):
        return 0

    # Turnovers or Missed Shots are 0 points
    if "Turnover" in description or "MISS" in description:
        return 0

    # Check for points scored using regex to find patterns like "(3 PTS)"
    match = re.search(r'\((\d+)\s+PTS\)', description)
    if match:
        return int(match.group(1))

    # Free throws (as a fallback, in case the PTS pattern isn't there)
    if "Free Throw" in description:
        if "makes" in description.lower():
            return 1
        else:
            # This covers missed free throws which might not have "MISS"
            return 0
            
    return 0


def get_archetypes(file_path="player_archetypes_k8_2022_23.csv"):
    """Loads player archetypes from a CSV file into a dictionary."""
    try:
        df = pd.read_csv(file_path)
        # Assuming columns are named 'player_id' and 'archetype_id'
        return pd.Series(df.archetype_id.values, index=df.player_id).to_dict()
    except FileNotFoundError:
        print(f"Error: Archetype file not found at {file_path}")
        return {}


def get_darko_ratings(db_path=DB_PATH):
    """Loads DARKO skill ratings from the database into a dictionary."""
    ratings = {}
    try:
        con = sqlite3.connect(db_path)
        query = "SELECT player_id, offensive_skill_rating, defensive_skill_rating FROM PlayerSkills WHERE skill_metric_source = 'DARKO'"
        df = pd.read_sql_query(query, con)
        con.close()
        for _, row in df.iterrows():
            ratings[row['player_id']] = {
                "o_darko": row['offensive_skill_rating'],
                "d_darko": row['defensive_skill_rating']
            }
        return ratings
    except sqlite3.Error as e:
        print(f"Database error while fetching DARKO ratings: {e}")
        return {}

def get_lineup_supercluster(archetype_lineup, supercluster_map):
    """Looks up the supercluster for a given archetype lineup."""
    # The key is a sorted tuple of archetype IDs to ensure order doesn't matter
    lineup_key = tuple(sorted(archetype_lineup))
    return supercluster_map.get(lineup_key, -1) # Return -1 if not found


def create_mock_supercluster_map():
    """Creates a mock mapping from archetype lineups to superclusters for prototyping."""
    # THIS IS A MOCK. The real mapping is complex and needs to be built.
    # For now, we'll create a few plausible fake mappings.
    mock_map = {
        tuple(sorted([1, 6, 5, 2, 3])): 0, # "Three-Point Symphony"
        tuple(sorted([4, 5, 0, 7, 1])): 1, # "Half-Court Individual Shot Creators"
        tuple(sorted([1, 1, 6, 5, 2])): 2, # "Slashing Offenses"
        tuple(sorted([0, 0, 0, 0, 0])): 3,
    }
    return mock_map


def process_single_possession(possession_row, archetypes, darko_ratings, supercluster_map):
    """
    Processes a single possession row to create a model-ready data vector.
    """
    # 1. Get player IDs for the possession
    home_players = [possession_row[f'home_player_{i}_id'] for i in range(1, 6)]
    away_players = [possession_row[f'away_player_{i}_id'] for i in range(1, 6)]

    offensive_team_id = possession_row['offensive_team_id']
    
    # Determine which lineup is on offense
    if possession_row['player1_team_id'] == offensive_team_id:
        offensive_players = home_players
        defensive_players = away_players
    else:
        offensive_players = away_players
        defensive_players = home_players

    # 2. Look up archetypes
    offensive_archetypes = [archetypes.get(p_id, -1) for p_id in offensive_players]
    defensive_archetypes = [archetypes.get(p_id, -1) for p_id in defensive_players]

    # 3. Look up superclusters
    offensive_supercluster = get_lineup_supercluster(offensive_archetypes, supercluster_map)
    defensive_supercluster = get_lineup_supercluster(defensive_archetypes, supercluster_map)

    # 4. Look up DARKO ratings
    offensive_skills = [darko_ratings.get(p_id, {"o_darko": 0, "d_darko": 0}) for p_id in offensive_players]
    defensive_skills = [darko_ratings.get(p_id, {"o_darko": 0, "d_darko": 0}) for p_id in defensive_players]

    # 5. Calculate Z-scores (aggregated skill by archetype)
    z_scores = {"off": {i: 0 for i in range(8)}, "def": {i: 0 for i in range(8)}}
    for i, archetype_id in enumerate(offensive_archetypes):
        if archetype_id != -1:
            z_scores["off"][archetype_id] += offensive_skills[i]["o_darko"]
    
    for i, archetype_id in enumerate(defensive_archetypes):
        if archetype_id != -1:
            z_scores["def"][archetype_id] += defensive_skills[i]["d_darko"]
            
    # 6. Assemble the final data point
    model_input = {
        "possession_id": possession_row['game_id'] + "_" + str(possession_row['event_num']),
        "outcome": calculate_outcome(possession_row),
        "offensive_supercluster": offensive_supercluster,
        "defensive_supercluster": defensive_supercluster,
        "z_scores_off": z_scores["off"],
        "z_scores_def": z_scores["def"],
        "raw_offensive_archetypes": offensive_archetypes,
        "raw_defensive_archetypes": defensive_archetypes,
    }

    return model_input


def main():
    """
    Main function to run the semantic prototype.
    """
    print("--- Running Semantic Prototype: Phase 1 ---")
    
    # --- Phase 1.1: Outcome Calculation ---
    try:
        con = sqlite3.connect(DB_PATH)
        # Fetch a sample of 100 possessions to analyze
        query = "SELECT * FROM Possessions WHERE offensive_team_id IS NOT NULL LIMIT 100"
        df = pd.read_sql_query(query, con)
        con.close()
        print(f"Successfully connected to {DB_PATH} and fetched {len(df)} possessions.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return
    except Exception as e:
        print(f"An error occurred: {e}")
        return

    # Coalesce description columns for outcome calculation
    df['description'] = df['home_description'].fillna('') + df['visitor_description'].fillna('') + df['neutral_description'].fillna('')
    df['description'] = df['description'].replace('', None)
    df["calculated_outcome"] = df.apply(calculate_outcome, axis=1)
    print("Phase 1.1 (Outcome Calculation) completed.")
    
    # --- Phase 1.2: Construct a Single Perfect Model Input ---
    print("\n--- Running Semantic Prototype: Phase 1.2 ---")
    print("Loading auxiliary data (archetypes, DARKO ratings)...")
    archetypes = get_archetypes()
    darko_ratings = get_darko_ratings()
    supercluster_map = create_mock_supercluster_map()
    
    if not archetypes or not darko_ratings:
        print("Could not load auxiliary data. Aborting.")
        return
        
    print("Processing a single possession to create a model-ready input...")
    
    # Find a possession where we have data for all players to ensure a good example
    sample_row = None
    for _, row in df.iterrows():
         home_players = [row[f'home_player_{i}_id'] for i in range(1, 6)]
         away_players = [row[f'away_player_{i}_id'] for i in range(1, 6)]
         all_players = home_players + away_players
         if all(p in archetypes and p in darko_ratings for p in all_players):
             sample_row = row
             break
    
    if sample_row is None:
        print("\nCould not find a single possession in the sample with complete data for all 10 players.")
        print("This is a potential issue for the main pipeline. For now, using the first row as a fallback.")
        sample_row = df.iloc[0]

    # Process the single possession
    model_ready_vector = process_single_possession(sample_row, archetypes, darko_ratings, supercluster_map)

    print("\n--- A Single, Perfect, Model-Ready Data Point ---")
    import json
    print(json.dumps(model_ready_vector, indent=2))
    
    print("\nPhase 1.2 (Single Model Input) completed.")
    print("The prototype successfully generated a complete data vector for one possession.")
    print("Next step is Phase 2: Full-Scale Data Verification and Profiling.")


if __name__ == "__main__":
    main()
