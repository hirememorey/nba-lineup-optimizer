#!/usr/bin/env python3
"""
Validate archetype-lineup mappings and assess data density for clustering.

This script:
1. Creates archetype lineups from possession data
2. Validates that archetype lineups make basketball sense
3. Assesses data density for clustering feasibility
4. Provides detailed statistics for decision-making
"""

import sqlite3
import pandas as pd
import numpy as np
from collections import Counter
from pathlib import Path

def load_player_archetypes(conn):
    """Load player archetype mappings."""
    query = """
    SELECT 
        p.player_id,
        p.player_name,
        pa.archetype_id,
        a.archetype_name
    FROM Players p
    JOIN PlayerSeasonArchetypes pa ON p.player_id = pa.player_id
    JOIN Archetypes a ON pa.archetype_id = a.archetype_id
    WHERE pa.season = '2024-25'
    """
    
    return pd.read_sql_query(query, conn)

def create_archetype_lineups(conn, player_archetypes):
    """Create archetype lineups from possession data."""
    
    # Create player_id to archetype_id mapping
    player_to_archetype = dict(zip(player_archetypes['player_id'], player_archetypes['archetype_id']))
    
    # Get possession data with lineup information
    query = """
    SELECT 
        game_id,
        event_num,
        home_player_1_id, home_player_2_id, home_player_3_id, home_player_4_id, home_player_5_id,
        away_player_1_id, away_player_2_id, away_player_3_id, away_player_4_id, away_player_5_id,
        offensive_team_id
    FROM Possessions
    WHERE home_player_1_id IS NOT NULL 
    AND home_player_2_id IS NOT NULL 
    AND home_player_3_id IS NOT NULL 
    AND home_player_4_id IS NOT NULL 
    AND home_player_5_id IS NOT NULL
    AND away_player_1_id IS NOT NULL 
    AND away_player_2_id IS NOT NULL 
    AND away_player_3_id IS NOT NULL 
    AND away_player_4_id IS NOT NULL 
    AND away_player_5_id IS NOT NULL
    """
    
    possessions = pd.read_sql_query(query, conn)
    print(f"Loaded {len(possessions)} possessions with complete lineup data")
    
    # Create archetype lineups
    archetype_lineups = []
    
    for _, row in possessions.iterrows():
        # Home lineup
        home_players = [
            row['home_player_1_id'], row['home_player_2_id'], row['home_player_3_id'],
            row['home_player_4_id'], row['home_player_5_id']
        ]
        
        # Away lineup  
        away_players = [
            row['away_player_1_id'], row['away_player_2_id'], row['away_player_3_id'],
            row['away_player_4_id'], row['away_player_5_id']
        ]
        
        # Convert to archetype lineups
        home_archetypes = []
        away_archetypes = []
        
        for player_id in home_players:
            archetype_id = player_to_archetype.get(player_id, -1)  # -1 for unknown players
            home_archetypes.append(archetype_id)
            
        for player_id in away_players:
            archetype_id = player_to_archetype.get(player_id, -1)  # -1 for unknown players
            away_archetypes.append(archetype_id)
        
        # Create archetype lineup strings
        home_archetype_lineup = "_".join(map(str, sorted(home_archetypes)))
        away_archetype_lineup = "_".join(map(str, sorted(away_archetypes)))
        
        archetype_lineups.append({
            'game_id': row['game_id'],
            'event_num': row['event_num'],
            'home_archetype_lineup': home_archetype_lineup,
            'away_archetype_lineup': away_archetype_lineup,
            'offensive_team_id': row['offensive_team_id']
        })
    
    return pd.DataFrame(archetype_lineups)

def validate_archetype_lineups(archetype_lineups, player_archetypes):
    """Validate that archetype lineups make basketball sense."""
    
    print("\n" + "="*60)
    print("ARCHETYPE LINEUP VALIDATION")
    print("="*60)
    
    # Get archetype names for interpretation
    archetype_names = dict(zip(player_archetypes['archetype_id'], player_archetypes['archetype_name']))
    archetype_names[-1] = "Unknown"
    
    # Analyze home lineups
    home_lineups = archetype_lineups['home_archetype_lineup'].value_counts()
    away_lineups = archetype_lineups['away_archetype_lineup'].value_counts()
    
    print(f"\nTotal unique home archetype lineups: {len(home_lineups)}")
    print(f"Total unique away archetype lineups: {len(away_lineups)}")
    
    # Check for unknown players
    unknown_home = archetype_lineups['home_archetype_lineup'].str.contains('-1').sum()
    unknown_away = archetype_lineups['away_archetype_lineup'].str.contains('-1').sum()
    total_possessions = len(archetype_lineups)
    
    print(f"\nPossessions with unknown players:")
    print(f"  Home lineups: {unknown_home} ({unknown_home/total_possessions*100:.1f}%)")
    print(f"  Away lineups: {unknown_away} ({unknown_away/total_possessions*100:.1f}%)")
    print(f"  Total: {unknown_home + unknown_away} ({(unknown_home + unknown_away)/total_possessions*100:.1f}%)")
    
    # Validation gate: require at least 80% of possessions to have valid archetype assignments
    valid_possessions = total_possessions - unknown_home - unknown_away
    valid_percentage = valid_possessions / total_possessions * 100
    
    print(f"\nVALIDATION GATE: {valid_percentage:.1f}% of possessions have valid archetype assignments")
    
    if valid_percentage < 80:
        print("❌ FAILED: Less than 80% of possessions have valid archetype assignments")
        print("   This indicates a serious data quality problem that must be resolved before clustering")
        return False
    else:
        print("✅ PASSED: Sufficient valid archetype assignments for clustering")
    
    # Show examples of valid archetype lineups
    print(f"\nTop 10 most common home archetype lineups:")
    for i, (lineup, count) in enumerate(home_lineups.head(10).items()):
        archetype_list = [archetype_names[int(x)] for x in lineup.split('_')]
        print(f"  {i+1:2d}. {lineup:15s} ({count:5d} times) - {archetype_list}")
    
    return True

def assess_data_density(archetype_lineups):
    """Assess data density for clustering feasibility."""
    
    print("\n" + "="*60)
    print("DATA DENSITY ASSESSMENT")
    print("="*60)
    
    # Get all unique archetype lineups
    all_lineups = pd.concat([
        archetype_lineups['home_archetype_lineup'],
        archetype_lineups['away_archetype_lineup']
    ]).value_counts()
    
    print(f"Total unique archetype lineups: {len(all_lineups)}")
    print(f"Total lineup occurrences: {all_lineups.sum()}")
    
    # Calculate distribution statistics
    lineup_counts = all_lineups.values
    print(f"\nLineup frequency distribution:")
    print(f"  Most common lineup: {all_lineups.iloc[0]} occurrences")
    print(f"  Least common lineup: {all_lineups.iloc[-1]} occurrences")
    print(f"  Median occurrences: {np.median(lineup_counts):.1f}")
    print(f"  Mean occurrences: {np.mean(lineup_counts):.1f}")
    
    # Assess clustering feasibility for different k values
    print(f"\nClustering feasibility assessment:")
    
    for k in [3, 4, 5, 6, 7, 8, 9, 10]:
        min_lineups_per_cluster = len(all_lineups) // k
        print(f"  k={k}: {min_lineups_per_cluster} lineups per cluster (minimum)")
        
        if min_lineups_per_cluster < 10:
            print(f"    ⚠️  WARNING: Insufficient data density for k={k}")
        elif min_lineups_per_cluster < 15:
            print(f"    ⚠️  CAUTION: Low data density for k={k}")
        else:
            print(f"    ✅ Good data density for k={k}")
    
    # Recommendation
    recommended_k = max([k for k in [3, 4, 5, 6, 7, 8, 9, 10] if len(all_lineups) // k >= 15])
    print(f"\nRECOMMENDATION: Use k={recommended_k} for clustering")
    print(f"  This provides {len(all_lineups) // recommended_k} lineups per cluster on average")
    
    return recommended_k

def main():
    """Main validation process."""
    
    db_path = "src/nba_stats/db/nba_stats.db"
    
    if not Path(db_path).exists():
        print(f"Error: Database file not found: {db_path}")
        return False
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    try:
        print("Loading player archetype data...")
        player_archetypes = load_player_archetypes(conn)
        print(f"Loaded {len(player_archetypes)} players with archetype assignments")
        
        print("\nCreating archetype lineups from possession data...")
        archetype_lineups = create_archetype_lineups(conn, player_archetypes)
        
        # Validate archetype lineups
        validation_passed = validate_archetype_lineups(archetype_lineups, player_archetypes)
        
        if not validation_passed:
            print("\n❌ VALIDATION FAILED: Cannot proceed with clustering")
            return False
        
        # Assess data density
        recommended_k = assess_data_density(archetype_lineups)
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print("✅ Archetype lineup validation: PASSED")
        print(f"✅ Recommended clustering k-value: {recommended_k}")
        print("✅ Ready to proceed with clustering implementation")
        
        return True
        
    except Exception as e:
        print(f"Error during validation: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
