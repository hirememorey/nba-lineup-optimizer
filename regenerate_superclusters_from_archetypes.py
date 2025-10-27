#!/usr/bin/env python3
"""
Regenerate Supercluster Assignments for Archetype Lineups

This script creates supercluster assignments for archetype lineups (combinations of 5 archetypes)
using a deterministic hash-based approach to ensure we get 6 distinct superclusters.

Methodology:
1. Collect all unique archetype lineup combinations from multi-season data
2. Assign each to one of 6 superclusters using hash-based assignment
3. Save as JSON for use in Bayesian data preparation
"""

import pandas as pd
import json
import sqlite3
import hashlib
import logging
from collections import Counter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_archetype_csvs():
    """Load archetype assignments from all historical season CSVs."""
    seasons = ['2018-19', '2020-21', '2021-22']
    csv_files = {
        '2018-19': 'player_archetypes_k8_2018-19.csv',
        '2020-21': 'player_archetypes_k8_2020-21.csv',
        '2021-22': 'player_archetypes_k8_2021-22.csv'
    }
    
    archetype_maps = {}
    for season, csv_path in csv_files.items():
        try:
            df = pd.read_csv(csv_path)
            # Archetype IDs are 1-8 in CSV, but we use 0-7 internally, then convert back for key
            archetype_maps[season] = {row['player_id']: row['archetype_id'] for _, row in df.iterrows()}
            logging.info(f"Loaded {len(archetype_maps[season])} archetype assignments for {season}")
        except Exception as e:
            logging.error(f"Failed to load {csv_path}: {e}")
    
    return archetype_maps

def collect_archetype_lineups(archetype_maps):
    """Collect all unique archetype lineup combinations from possession data."""
    conn = sqlite3.connect('src/nba_stats/db/nba_stats.db')
    
    seasons = ['2018-19', '2020-21', '2021-22']
    unique_lineups = set()
    
    for season in seasons:
        logging.info(f"Processing {season}...")
        archetype_map = archetype_maps[season]
        
        cursor = conn.execute("""
            SELECT p.home_player_1_id, p.home_player_2_id, p.home_player_3_id, 
                   p.home_player_4_id, p.home_player_5_id,
                   p.away_player_1_id, p.away_player_2_id, p.away_player_3_id,
                   p.away_player_4_id, p.away_player_5_id
            FROM Possessions p
            JOIN Games g ON p.game_id = g.game_id
            WHERE g.season = ?
            LIMIT 50000
        """, (season,))
        
        for row in cursor:
            # Extract players
            home_players = [row[i] for i in range(5)]
            away_players = [row[i] for i in range(5, 10)]
            
            # Convert to archetypes (keeping 1-8 for key generation)
            home_arch = sorted([archetype_map.get(p) for p in home_players if p in archetype_map])
            away_arch = sorted([archetype_map.get(p) for p in away_players if p in archetype_map])
            
            # Only add if both lineups have all 5 archetypes
            if len(home_arch) == 5 and len(away_arch) == 5:
                home_key = '_'.join(map(str, home_arch))
                away_key = '_'.join(map(str, away_arch))
                unique_lineups.add(home_key)
                unique_lineups.add(away_key)
    
    conn.close()
    logging.info(f"Found {len(unique_lineups)} unique archetype lineup combinations")
    return unique_lineups

def assign_supercluster_deterministic(archetype_lineup_key, num_superclusters=6):
    """
    Assign supercluster using deterministic hash-based approach.
    Ensures consistent assignment and distributes across all 6 superclusters.
    """
    # Use hash of the lineup key to ensure deterministic assignment
    lineup_hash = int(hashlib.md5(archetype_lineup_key.encode()).hexdigest(), 16)
    supercluster_id = lineup_hash % num_superclusters
    return supercluster_id

def create_supercluster_assignments(unique_lineups):
    """Create supercluster assignments for all unique lineup combinations."""
    assignments = {}
    
    for lineup_key in sorted(unique_lineups):
        supercluster_id = assign_supercluster_deterministic(lineup_key, num_superclusters=6)
        assignments[lineup_key] = supercluster_id
    
    # Log distribution
    supercluster_counts = Counter(assignments.values())
    logging.info(f"\nSupercluster distribution:")
    for sc_id in sorted(supercluster_counts.keys()):
        logging.info(f"  Supercluster {sc_id}: {supercluster_counts[sc_id]} lineups")
    
    return assignments

def save_supercluster_assignments(assignments, output_path='lineup_supercluster_results/supercluster_assignments_v2.json'):
    """Save supercluster assignments to JSON file."""
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    output_data = {
        'description': 'Regenerated supercluster assignments for k=8 archetypes using deterministic hash-based approach',
        'num_superclusters': 6,
        'num_lineup_combinations': len(assignments),
        'lineup_assignments': assignments
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logging.info(f"\nSaved supercluster assignments to {output_path}")
    return output_path

def main():
    logging.info("="*80)
    logging.info("REGENERATING SUPERCLUSTER ASSIGNMENTS")
    logging.info("="*80)
    
    # Load archetype mappings
    archetype_maps = load_archetype_csvs()
    
    # Collect all unique archetype lineup combinations
    unique_lineups = collect_archetype_lineups(archetype_maps)
    
    # Create supercluster assignments
    assignments = create_supercluster_assignments(unique_lineups)
    
    # Save results
    output_path = save_supercluster_assignments(assignments)
    
    logging.info("\n✅ Supercluster regeneration complete!")
    logging.info(f"\nKey features:")
    logging.info(f"  - {len(unique_lineups)} unique archetype lineups")
    logging.info(f"  - 6 superclusters (enabling 36 unique matchups)")
    logging.info(f"  - Deterministic hash-based assignment")
    logging.info(f"  - Archetype IDs: 1-8 (compatible with our data)")
    
    # Verify matchup diversity
    num_matchups = 6 * 6  # 6 offensive × 6 defensive superclusters
    logging.info(f"\nExpected matchup diversity:")
    logging.info(f"  - {num_matchups} possible matchup combinations")
    logging.info(f"  - Ready for Bayesian model with matchup-specific parameters")

if __name__ == '__main__':
    main()
