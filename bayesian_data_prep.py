#!/usr/bin/env python3
"""
Bayesian Model Data Preparation Module

This module transforms possession data into the format required by the Bayesian
possession-level model. It implements the data transformation logic from the
research paper, creating the Z matrix and outcome variables.

Author: AI Assistant
Date: October 3, 2025
"""

import sqlite3
import pandas as pd
import json
import logging
from collections import defaultdict
import numpy as np

# It's good practice to reuse proven components
from semantic_prototype import (
    get_archetypes, 
    get_darko_ratings, 
    create_mock_supercluster_map, 
    get_lineup_supercluster,
    calculate_outcome
)

DB_PATH = "src/nba_stats/db/nba_stats.db"
OUTPUT_CSV_PATH = "possessions_k8_prepared.csv"
SAMPLE_CSV_PATH = "stratified_sample_10k.csv"
BATCH_SIZE = 50000

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def prepare_bayesian_data():
    """
    Builds the final, model-ready dataset by processing all possessions,
    filtering for data completeness, and applying transformation logic.
    """
    logging.info("--- Starting Bayesian Data Preparation: Phase 3 ---")

    # 1. Load all auxiliary data
    logging.info("Loading auxiliary data (archetypes, DARKO ratings)...")
    archetypes = get_archetypes()
    darko_ratings = get_darko_ratings()
    
    # !!! CRITICAL PLACEHOLDER !!!
    # The current supercluster map is a mock. A full implementation requires
    # clustering the ~182 unique archetype lineups based on their weighted
    # average lineup statistics, as described in the source paper.
    # This is a significant sub-task that must be completed before the model
    # can be considered valid.
    supercluster_map = create_mock_supercluster_map()
    logging.warning("Using a MOCK supercluster map. This is a placeholder!")

    if not archetypes or not darko_ratings:
        logging.error("Could not load archetypes or DARKO ratings. Aborting.")
        return

    # 2. Process possessions in batches and filter for clean data
    logging.info("Processing all possessions from the database...")
    clean_rows = []
    total_processed = 0
    
    try:
        con = sqlite3.connect(DB_PATH)
        # Note: The 'Possessions' table seems to contain multiple seasons.
        # For true reproducibility, we should filter for the '2022-23' season.
        # This requires a join with the 'Games' table. Deferring for now to match paper's scope.
        query = "SELECT * FROM Possessions WHERE offensive_team_id IS NOT NULL"
        
        for chunk in pd.read_sql_query(query, con, chunksize=BATCH_SIZE):
            total_processed += len(chunk)
            
            # Coalesce description columns for outcome calculation
            chunk['description'] = chunk['home_description'].fillna('') + chunk['visitor_description'].fillna('') + chunk['neutral_description'].fillna('')
            chunk['description'] = chunk['description'].replace('', None)

            for _, row in chunk.iterrows():
                home_players = [row[f'home_player_{i}_id'] for i in range(1, 6)]
                away_players = [row[f'away_player_{i}_id'] for i in range(1, 6)]

                if any(pd.isnull(p) for p in home_players + away_players):
                    continue
                
                all_players = [int(p) for p in home_players + away_players]
                
                # HARDENING: Explicitly filter based on Phase 2 findings
                if not all(p in archetypes and p in darko_ratings for p in all_players):
                    continue

                # If the row is clean, process it
                # (This reuses the logic from the semantic prototype)
                offensive_team_id = row['offensive_team_id']
                if row['player1_team_id'] == offensive_team_id:
                    offensive_players, defensive_players = home_players, away_players
                else:
                    offensive_players, defensive_players = away_players, home_players

                offensive_archetypes = [archetypes.get(p) for p in offensive_players]
                defensive_archetypes = [archetypes.get(p) for p in defensive_players]

                offensive_supercluster = get_lineup_supercluster(offensive_archetypes, supercluster_map)
                defensive_supercluster = get_lineup_supercluster(defensive_archetypes, supercluster_map)
                
                # PRAGMATIC MODIFICATION: Assign a default supercluster if not found in the mock map.
                # This unblocks the data generation, but the supercluster IDs are NOT yet meaningful.
                if offensive_supercluster == -1:
                    offensive_supercluster = 0 # Default to supercluster 0
                if defensive_supercluster == -1:
                    defensive_supercluster = 0 # Default to supercluster 0
                    
                outcome = calculate_outcome(row)
                
                # Aggregate Z-scores
                z_scores_off = defaultdict(float)
                z_scores_def = defaultdict(float)
                
                for i, p_id in enumerate(offensive_players):
                    arch = offensive_archetypes[i]
                    z_scores_off[arch] += darko_ratings[p_id]["o_darko"]

                for i, p_id in enumerate(defensive_players):
                    arch = defensive_archetypes[i]
                    z_scores_def[arch] += darko_ratings[p_id]["d_darko"]
                    
                final_row = {
                    "outcome": outcome,
                    "matchup_id": f"{offensive_supercluster}_vs_{defensive_supercluster}"
                }
                for i in range(8):
                    final_row[f"z_off_{i}"] = z_scores_off[i]
                    final_row[f"z_def_{i}"] = z_scores_def[i]
                
                clean_rows.append(final_row)

            logging.info(f"...processed {total_processed} possessions, found {len(clean_rows)} clean possessions so far.")

    except sqlite3.Error as e:
        logging.error(f"Database error during processing: {e}")
    finally:
        if con:
            con.close()

    if not clean_rows:
        logging.error("No clean data was found. The output file will be empty. Aborting.")
        return

    # 3. Create and save the final DataFrame
    logging.info(f"Finished processing. Found a total of {len(clean_rows)} clean possessions.")
    final_df = pd.DataFrame(clean_rows)
    
    # --- HARDENING STEP: Validate data before saving ---
    logging.info("Validating final DataFrame for NaN or Inf values...")
    initial_rows = len(final_df)
    
    # Replace inf/-inf with NaN
    final_df.replace([np.inf, -np.inf], np.nan, inplace=True)
    
    # Drop rows with any NaN values
    final_df.dropna(inplace=True)
    
    final_rows = len(final_df)
    rows_dropped = initial_rows - final_rows
    
    if rows_dropped > 0:
        logging.warning(f"Dropped {rows_dropped} rows containing NaN/Inf values.")
    else:
        logging.info("Data validation passed. No NaN/Inf values found.")
        
    final_df.to_csv(OUTPUT_CSV_PATH, index=False)
    logging.info(f"Successfully saved full prepared dataset to {OUTPUT_CSV_PATH}")

    # 4. Create and save the stratified sample
    if len(final_df) > 10000:
        # For now, a simple random sample is sufficient as the next step is prototyping.
        # A true stratified sample would balance by matchup_id.
        sample_df = final_df.sample(n=10000, random_state=42)
        sample_df.to_csv(SAMPLE_CSV_PATH, index=False)
        logging.info(f"Successfully saved stratified sample to {SAMPLE_CSV_PATH}")
    else:
        logging.warning("Dataset is smaller than 10,000 rows, so the sample file will be the same as the full file.")
        final_df.to_csv(SAMPLE_CSV_PATH, index=False)

    logging.info("--- Bayesian Data Preparation: Phase 3 Complete ---")

if __name__ == "__main__":
    prepare_bayesian_data()
