#!/usr/bin/env python3
"""
Inventory ALL Archetype Combinations from 2022-23 Season

This script creates a complete inventory of archetype combinations that actually
appear in 2022-23 NBA games. This ensures our supercluster mapping will have
100% coverage and no possessions get filtered out.

Methodology:
1. Load 2022-23 archetype assignments
2. Query ALL possessions from 2022-23 season (not a sample)
3. Extract archetype combinations for each lineup
4. Create comprehensive inventory with frequencies
5. Validate coverage meets requirements for supercluster generation
"""

import pandas as pd
import sqlite3
import json
import logging
from collections import Counter, defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_2022_23_archetypes():
    """Load archetype assignments for 2022-23 season."""
    csv_path = "player_archetypes_k8_2022_23.csv"
    try:
        df = pd.read_csv(csv_path)
        # Create mapping: player_id -> archetype_id (keeping 1-8 range for keys)
        archetypes = {row['player_id']: row['archetype_id'] for _, row in df.iterrows()}
        logging.info(f"Loaded {len(archetypes)} archetype assignments for 2022-23")
        return archetypes
    except Exception as e:
        logging.error(f"Failed to load archetypes: {e}")
        return {}

def extract_archetype_combinations_from_possessions(archetypes, season="2022-23"):
    """
    Extract ALL unique archetype combinations from the complete 2022-23 season.

    Returns:
        dict: {
            'combinations': set of (offensive_tuple, defensive_tuple),
            'frequency': Counter of combination frequencies,
            'lineups_only': set of unique lineup keys (for supercluster generation)
        }
    """
    db_path = "src/nba_stats/db/nba_stats.db"
    conn = sqlite3.connect(db_path)

    combinations = set()
    lineup_combinations = set()
    frequency = Counter()

    try:
        # Query ALL possessions from 2022-23 season (no LIMIT)
        cursor = conn.execute("""
            SELECT p.home_player_1_id, p.home_player_2_id, p.home_player_3_id,
                   p.home_player_4_id, p.home_player_5_id,
                   p.away_player_1_id, p.away_player_2_id, p.away_player_3_id,
                   p.away_player_4_id, p.away_player_5_id,
                   p.offensive_team_id, p.player1_team_id
            FROM Possessions p
            JOIN Games g ON p.game_id = g.game_id
            WHERE g.season = ?
        """, (season,))

        processed = 0
        valid_combinations = 0

        for row in cursor:
            processed += 1
            if processed % 50000 == 0:
                logging.info(f"Processed {processed} possessions...")

            # Extract players
            home_players = [row[i] for i in range(5)]
            away_players = [row[i] for i in range(5, 10)]
            offensive_team = row[10]
            player1_team = row[11]

            # Skip if any player IDs are missing
            if any(pd.isna(p) for p in home_players + away_players):
                continue

            # Convert to archetypes
            home_archetypes = []
            away_archetypes = []

            for player in home_players:
                if player in archetypes:
                    home_archetypes.append(archetypes[player])

            for player in away_players:
                if player in archetypes:
                    away_archetypes.append(archetypes[player])

            # Only process if both lineups have all 5 archetypes
            if len(home_archetypes) == 5 and len(away_archetypes) == 5:
                # Determine which is offense/defense
                if player1_team == offensive_team:
                    off_arch = home_archetypes
                    def_arch = away_archetypes
                else:
                    off_arch = away_archetypes
                    def_arch = home_archetypes

                # Create sorted tuples for deduplication
                off_tuple = tuple(sorted(off_arch))
                def_tuple = tuple(sorted(def_arch))
                combination = (off_tuple, def_tuple)

                # Add to sets and counters
                combinations.add(combination)
                lineup_combinations.add(off_tuple)
                lineup_combinations.add(def_tuple)

                # Track frequency of this specific combination
                frequency[combination] += 1
                valid_combinations += 1

        logging.info(f"Completed processing {processed} possessions")
        logging.info(f"Found {valid_combinations} valid archetype combinations")
        logging.info(f"Found {len(combinations)} unique archetype combination pairs")
        logging.info(f"Found {len(lineup_combinations)} unique lineup combinations")

    finally:
        conn.close()

    return {
        'combinations': combinations,
        'frequency': frequency,
        'lineups_only': lineup_combinations,
        'total_possessions': processed,
        'valid_combinations': valid_combinations
    }

def analyze_combination_coverage(inventory):
    """Analyze the coverage and distribution of archetype combinations."""

    combinations = inventory['combinations']
    frequency = inventory['frequency']
    lineups_only = inventory['lineups_only']

    # Analyze lineup diversity
    lineup_counts = Counter()
    for lineup in lineups_only:
        lineup_counts[len(set(lineup))] += 1  # Count unique archetypes in lineup

    logging.info("\n=== ARCHETYPE COMBINATION ANALYSIS ===")
    logging.info(f"Total unique lineup combinations: {len(lineups_only)}")
    logging.info(f"Total unique matchup combinations: {len(combinations)}")
    logging.info(f"Total valid possession combinations: {inventory['valid_combinations']}")

    logging.info("\nLineup diversity (unique archetypes per lineup):")
    for unique_count in sorted(lineup_counts.keys()):
        logging.info(f"  {unique_count} unique archetypes: {lineup_counts[unique_count]} lineups")

    # Analyze frequency distribution
    freq_values = list(frequency.values())
    logging.info("\nCombination frequency statistics:")
    logging.info(f"  Most frequent combination: {max(freq_values)} possessions")
    logging.info(f"  Least frequent combination: {min(freq_values)} possessions")
    logging.info(f"  Average frequency: {sum(freq_values) / len(freq_values):.2f} possessions")

    # Count combinations by frequency thresholds
    thresholds = [1, 10, 100, 1000]
    for threshold in thresholds:
        count = sum(1 for freq in freq_values if freq >= threshold)
        logging.info(f"  Combinations with ≥{threshold} possessions: {count}")

    return {
        'lineup_diversity': lineup_counts,
        'frequency_stats': {
            'max': max(freq_values),
            'min': min(freq_values),
            'mean': sum(freq_values) / len(freq_values),
            'median': sorted(freq_values)[len(freq_values)//2]
        }
    }

def validate_coverage_requirements(inventory):
    """Validate that we have sufficient coverage for supercluster generation."""

    lineups_only = inventory['lineups_only']
    total_combinations = len(inventory['combinations'])
    valid_possessions = inventory['valid_combinations']

    # Minimum requirements for successful supercluster generation
    min_lineups = 150  # Original paper had 182
    min_matchups = 5000  # Should cover most common scenarios
    min_possession_coverage = 500000  # Should be close to original paper's 574K

    logging.info("\n=== COVERAGE VALIDATION ===")

    checks = [
        ("Unique lineup combinations", len(lineups_only), min_lineups),
        ("Unique matchup combinations", total_combinations, min_matchups),
        ("Valid possession combinations", valid_possessions, min_possession_coverage)
    ]

    all_passed = True
    for name, actual, minimum in checks:
        passed = actual >= minimum
        status = "✅ PASS" if passed else "❌ FAIL"
        logging.info(f"{status} {name}: {actual:,} (minimum: {minimum:,})")
        if not passed:
            all_passed = False

    return all_passed

def save_inventory_results(inventory, analysis, validation_passed):
    """Save the complete inventory and analysis results."""

    # First, save just the lineup combinations (this is what we need for superclusters)
    lineup_output = '2022_23_lineup_combinations.json'
    lineup_data = {
        'lineups': sorted([list(lineup) for lineup in inventory['lineups_only']]),
        'count': len(inventory['lineups_only']),
        'description': 'Unique archetype lineup combinations from 2022-23 season'
    }

    with open(lineup_output, 'w') as f:
        json.dump(lineup_data, f, indent=2)

    logging.info(f"Saved lineup combinations for supercluster generation to {lineup_output}")

    # Try to save full inventory, but don't fail if JSON serialization issues
    try:
        # Convert all data to basic Python types for JSON serialization
        def convert_for_json(obj):
            if isinstance(obj, (int, float)):
                return obj
            elif isinstance(obj, dict):
                return {k: convert_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_for_json(item) for item in obj]
            else:
                return str(obj)

        output_data = {
            'metadata': {
                'season': '2022-23',
                'description': 'Complete inventory of archetype combinations from 2022-23 season',
                'validation_passed': bool(validation_passed),
                'generated_at': str(pd.Timestamp.now())
            },
            'inventory': {
                'total_possessions_processed': int(inventory['total_possessions']),
                'valid_combinations': int(inventory['valid_combinations']),
                'unique_lineup_combinations': len(inventory['lineups_only']),
                'unique_matchup_combinations': len(inventory['combinations'])
            },
            'analysis': convert_for_json(analysis),
            'lineup_combinations': sorted([list(lineup) for lineup in inventory['lineups_only']]),
            'top_combinations': [{'combination': list(k), 'frequency': int(v)} for k, v in inventory['frequency'].most_common(20)]
        }

        output_path = '2022_23_archetype_inventory.json'
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        logging.info(f"Saved complete inventory to {output_path}")

    except Exception as e:
        logging.warning(f"Could not save full inventory due to JSON serialization: {e}")
        logging.info("But lineup combinations were saved successfully for supercluster generation")
        output_path = lineup_output

    return output_path

def main():
    logging.info("="*80)
    logging.info("INVENTORYING 2022-23 ARCHETYPE COMBINATIONS")
    logging.info("="*80)

    # Load 2022-23 archetypes
    archetypes = load_2022_23_archetypes()
    if not archetypes:
        logging.error("Failed to load archetypes. Aborting.")
        return

    # Extract ALL combinations from complete season
    logging.info("\nExtracting archetype combinations from ALL 2022-23 possessions...")
    inventory = extract_archetype_combinations_from_possessions(archetypes)

    # Analyze coverage and diversity
    analysis = analyze_combination_coverage(inventory)

    # Validate coverage requirements
    validation_passed = validate_coverage_requirements(inventory)

    # Save results
    output_path = save_inventory_results(inventory, analysis, validation_passed)

    # Summary
    logging.info("\n" + "="*80)
    logging.info("INVENTORY COMPLETE")
    logging.info("="*80)

    status = "✅ SUCCESS" if validation_passed else "⚠️  WARNING"
    logging.info(f"Status: {status}")

    logging.info("\nKey Results:")
    logging.info(f"  - Processed {inventory['total_possessions']:,} possessions")
    logging.info(f"  - Found {len(inventory['lineups_only'])} unique lineup combinations")
    logging.info(f"  - Found {len(inventory['combinations'])} unique matchup combinations")
    logging.info(f"  - Coverage validation: {'PASSED' if validation_passed else 'FAILED'}")

    if validation_passed:
        logging.info("\n🎉 Ready for supercluster generation!")
        logging.info("Next step: Run supercluster generation with complete lineup coverage")
    else:
        logging.warning("\n⚠️  Coverage may be insufficient for robust supercluster generation")
        logging.warning("Consider expanding archetype coverage or using alternative approach")

if __name__ == '__main__':
    main()
