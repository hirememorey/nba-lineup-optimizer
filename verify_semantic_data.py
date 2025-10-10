#!/usr/bin/env python3
"""
Semantic Data Verification Tool

This script validates that the NBA API is returning semantically correct data
before running the full data pipeline. It checks for:

1. Data completeness (no missing critical fields)
2. Data consistency (values make sense for basketball)
3. Data freshness (recent data available)
4. Data structure (expected response format)

This addresses the critical failure mode identified in the pre-mortem:
"The data looks valid but is semantically wrong, leading to garbage analysis results."
"""

import sqlite3
import pandas as pd
import json
from collections import defaultdict
import itertools

# Reuse functions from the prototype
from semantic_prototype import get_archetypes, get_darko_ratings, create_mock_supercluster_map, get_lineup_supercluster

DB_PATH = "src/nba_stats/db/nba_stats.db"
BATCH_SIZE = 50000

def verify_data_at_scale():
    """
    Applies the prototype's logic to the full dataset to find all data issues.
    """
    print("--- Running Full-Scale Data Verification: Phase 2 ---")
    
    # Load auxiliary data once
    print("Loading auxiliary data...")
    archetypes = get_archetypes()
    darko_ratings = get_darko_ratings()
    supercluster_map = create_mock_supercluster_map()
    
    if not archetypes or not darko_ratings:
        print("Could not load auxiliary data. Aborting.")
        return

    # --- Data Sanity Check ---
    print("Starting data sanity check over the full dataset...")
    sanity_issues = {
        "total_possessions_processed": 0,
        "possessions_with_incomplete_lineups": 0,
        "possessions_missing_archetypes": 0,
        "possessions_missing_darko": 0,
        "players_missing_archetype": defaultdict(int),
        "players_missing_darko": defaultdict(int),
    }
    
    clean_possessions_data = []

    con = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM Possessions WHERE offensive_team_id IS NOT NULL"
    
    for chunk in pd.read_sql_query(query, con, chunksize=BATCH_SIZE):
        sanity_issues["total_possessions_processed"] += len(chunk)
        
        for _, row in chunk.iterrows():
            home_players = [row[f'home_player_{i}_id'] for i in range(1, 6)]
            away_players = [row[f'away_player_{i}_id'] for i in range(1, 6)]
            
            # Check for null player IDs, indicating an incomplete lineup
            if any(pd.isnull(p) for p in home_players + away_players):
                sanity_issues["possessions_with_incomplete_lineups"] += 1
                continue
            
            all_players = [int(p) for p in home_players + away_players]
            
            missing_archetype_players = [p for p in all_players if p not in archetypes]
            missing_darko_players = [p for p in all_players if p not in darko_ratings]

            is_clean = True
            if missing_archetype_players:
                sanity_issues["possessions_missing_archetypes"] += 1
                for p_id in missing_archetype_players:
                    sanity_issues["players_missing_archetype"][p_id] += 1
                is_clean = False
                
            if missing_darko_players:
                sanity_issues["possessions_missing_darko"] += 1
                for p_id in missing_darko_players:
                    sanity_issues["players_missing_darko"][p_id] += 1
                is_clean = False
            
            if is_clean:
                clean_possessions_data.append(row)

        print(f"  ...processed {sanity_issues['total_possessions_processed']} possessions")

    con.close()
    
    # Save the sanity report
    # Convert defaultdicts to regular dicts for JSON serialization
    sanity_issues["players_missing_archetype"] = dict(sanity_issues["players_missing_archetype"])
    sanity_issues["players_missing_darko"] = dict(sanity_issues["players_missing_darko"])
    
    with open("data_sanity_check.json", "w") as f:
        json.dump(sanity_issues, f, indent=2)
    print(f"\nData sanity check complete. Report saved to data_sanity_check.json")

    # --- Statistical Profiling on Clean Data ---
    print("\nStarting statistical profile on clean data...")
    clean_df = pd.DataFrame(clean_possessions_data)
    
    if len(clean_df) == 0:
        print("No clean possessions found. Cannot generate statistical profile.")
        return
        
    matchup_frequencies = defaultdict(int)
    
    for _, row in clean_df.iterrows():
        home_players = [int(row[f'home_player_{i}_id']) for i in range(1, 6)]
        away_players = [int(row[f'away_player_{i}_id']) for i in range(1, 6)]

        home_archetypes = [archetypes.get(p_id) for p_id in home_players]
        away_archetypes = [archetypes.get(p_id) for p_id in away_players]

        home_supercluster = get_lineup_supercluster(home_archetypes, supercluster_map)
        away_supercluster = get_lineup_supercluster(away_archetypes, supercluster_map)
        
        # Determine offensive and defensive superclusters
        offensive_team_id = row['offensive_team_id']
        if row['player1_team_id'] == offensive_team_id:
             offensive_sc = home_supercluster
             defensive_sc = away_supercluster
        else:
             offensive_sc = away_supercluster
             defensive_sc = home_supercluster
             
        if offensive_sc != -1 and defensive_sc != -1:
            matchup_frequencies[f"{offensive_sc}_vs_{defensive_sc}"] += 1
            
    # Save the statistical profile
    statistical_profile = {
        "total_clean_possessions": len(clean_df),
        "matchup_frequencies": dict(sorted(matchup_frequencies.items(), key=lambda item: item[1], reverse=True)),
        "total_unique_matchups_found": len(matchup_frequencies),
    }

    with open("statistical_profile.json", "w") as f:
        json.dump(statistical_profile, f, indent=2)
    print("Statistical profile complete. Report saved to statistical_profile.json")
    
    print("\nPhase 2 completed. Review reports to inform the next steps.")

if __name__ == "__main__":
    verify_data_at_scale()
