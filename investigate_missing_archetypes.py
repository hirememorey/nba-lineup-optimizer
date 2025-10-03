#!/usr/bin/env python3
"""
Investigate which players are missing archetype assignments.

This script identifies players who appear in possession data but don't have
archetype assignments, helping us understand the scope of the data quality problem.
"""

import sqlite3
import pandas as pd
from collections import Counter

def get_all_players_in_possessions(conn):
    """Get all unique player IDs that appear in possession data."""
    
    query = """
    SELECT DISTINCT player_id FROM (
        SELECT home_player_1_id as player_id FROM Possessions WHERE home_player_1_id IS NOT NULL
        UNION
        SELECT home_player_2_id as player_id FROM Possessions WHERE home_player_2_id IS NOT NULL
        UNION
        SELECT home_player_3_id as player_id FROM Possessions WHERE home_player_3_id IS NOT NULL
        UNION
        SELECT home_player_4_id as player_id FROM Possessions WHERE home_player_4_id IS NOT NULL
        UNION
        SELECT home_player_5_id as player_id FROM Possessions WHERE home_player_5_id IS NOT NULL
        UNION
        SELECT away_player_1_id as player_id FROM Possessions WHERE away_player_1_id IS NOT NULL
        UNION
        SELECT away_player_2_id as player_id FROM Possessions WHERE away_player_2_id IS NOT NULL
        UNION
        SELECT away_player_3_id as player_id FROM Possessions WHERE away_player_3_id IS NOT NULL
        UNION
        SELECT away_player_4_id as player_id FROM Possessions WHERE away_player_4_id IS NOT NULL
        UNION
        SELECT away_player_5_id as player_id FROM Possessions WHERE away_player_5_id IS NOT NULL
    ) WHERE player_id IS NOT NULL
    ORDER BY player_id
    """
    
    return pd.read_sql_query(query, conn)

def get_players_with_archetypes(conn):
    """Get all players who have archetype assignments."""
    
    query = """
    SELECT DISTINCT player_id 
    FROM PlayerSeasonArchetypes 
    WHERE season = '2024-25'
    ORDER BY player_id
    """
    
    return pd.read_sql_query(query, conn)

def get_player_minutes_played(conn):
    """Get minutes played for each player to prioritize missing players."""
    
    query = """
    SELECT 
        p.player_id,
        p.player_name,
        COALESCE(prs.minutes_played, 0) as minutes_played
    FROM Players p
    LEFT JOIN PlayerSeasonRawStats prs ON p.player_id = prs.player_id AND prs.season = '2024-25'
    ORDER BY COALESCE(prs.minutes_played, 0) DESC
    """
    
    return pd.read_sql_query(query, conn)

def main():
    """Investigate missing archetype assignments."""
    
    conn = sqlite3.connect("src/nba_stats/db/nba_stats.db")
    
    try:
        print("Analyzing player archetype coverage...")
        
        # Get all players in possession data
        all_players = get_all_players_in_possessions(conn)
        print(f"Total unique players in possession data: {len(all_players)}")
        
        # Get players with archetype assignments
        players_with_archetypes = get_players_with_archetypes(conn)
        print(f"Players with archetype assignments: {len(players_with_archetypes)}")
        
        # Find missing players
        all_player_ids = set(all_players['player_id'])
        archetype_player_ids = set(players_with_archetypes['player_id'])
        missing_player_ids = all_player_ids - archetype_player_ids
        
        print(f"Players missing archetype assignments: {len(missing_player_ids)}")
        print(f"Coverage: {len(archetype_player_ids) / len(all_player_ids) * 100:.1f}%")
        
        # Get player details for missing players
        player_minutes = get_player_minutes_played(conn)
        missing_players = player_minutes[player_minutes['player_id'].isin(missing_player_ids)]
        missing_players = missing_players.sort_values('minutes_played', ascending=False)
        
        print(f"\nTop 20 players missing archetype assignments (by minutes played):")
        print("=" * 80)
        for i, (_, row) in enumerate(missing_players.head(20).iterrows()):
            print(f"{i+1:2d}. {row['player_name']:30s} (ID: {row['player_id']:6d}) - {row['minutes_played']:6.1f} min")
        
        # Analyze the impact
        total_minutes_missing = missing_players['minutes_played'].sum()
        total_minutes_all = player_minutes['minutes_played'].sum()
        
        print(f"\nImpact Analysis:")
        print(f"  Total minutes by missing players: {total_minutes_missing:,.1f}")
        print(f"  Total minutes by all players: {total_minutes_all:,.1f}")
        print(f"  Percentage of minutes missing: {total_minutes_missing / total_minutes_all * 100:.1f}%")
        
        # Recommendations
        print(f"\n" + "="*60)
        print("RECOMMENDATIONS")
        print("="*60)
        
        if len(missing_player_ids) > 100:
            print("❌ CRITICAL: Too many players missing archetype assignments")
            print("   This indicates a fundamental data quality problem")
            print("   Consider:")
            print("   1. Re-running the archetype generation with more players")
            print("   2. Using a different player filtering criteria")
            print("   3. Implementing a fallback archetype assignment strategy")
        elif len(missing_player_ids) > 50:
            print("⚠️  WARNING: Significant number of players missing archetype assignments")
            print("   Consider manually mapping the top 50 missing players by minutes")
        else:
            print("✅ MANAGEABLE: Reasonable number of missing players")
            print("   Consider manually mapping the missing players")
        
        # Save missing players list for manual mapping
        missing_players.to_csv("missing_archetype_players.csv", index=False)
        print(f"\nSaved missing players list to: missing_archetype_players.csv")
        
    except Exception as e:
        print(f"Error during investigation: {e}")
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    main()
