#!/usr/bin/env python3
"""
Implement fallback archetype assignments for players missing from archetype generation.

This script addresses the critical data quality issue where 295 players (18.7% of minutes)
are missing archetype assignments because they played fewer than 1000 minutes.

Strategy:
1. For players with 500-999 minutes: Use a simple heuristic based on position and stats
2. For players with <500 minutes: Assign to "Role Players" (most common archetype)
3. Update the database with these fallback assignments
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

def get_players_missing_archetypes(conn):
    """Get players who appear in possession data but don't have archetype assignments."""
    
    # Get all players in possession data
    possession_players_query = """
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
    """
    
    possession_players = pd.read_sql_query(possession_players_query, conn)
    
    # Get players with archetype assignments
    archetype_players_query = """
    SELECT DISTINCT player_id 
    FROM PlayerSeasonArchetypes 
    WHERE season = '2024-25'
    """
    
    archetype_players = pd.read_sql_query(archetype_players_query, conn)
    
    # Find missing players
    possession_player_ids = set(possession_players['player_id'])
    archetype_player_ids = set(archetype_players['player_id'])
    missing_player_ids = possession_player_ids - archetype_player_ids
    
    return list(missing_player_ids)

def get_player_stats_for_fallback(conn, player_ids):
    """Get basic stats for players to determine fallback archetype assignments."""
    
    placeholders = ','.join(['?' for _ in player_ids])
    
    query = f"""
    SELECT 
        p.player_id,
        p.player_name,
        p.height,
        p.position,
        COALESCE(rs.minutes_played, 0) as minutes_played,
        COALESCE(rs.games_played, 0) as games_played,
        COALESCE(rs.assists, 0) as assists,
        COALESCE(rs.total_rebounds, 0) as total_rebounds,
        COALESCE(rs.three_pointers_made, 0) as three_pointers_made,
        COALESCE(rs.three_pointers_attempted, 0) as three_pointers_attempted,
        COALESCE(rs.field_goals_made, 0) as field_goals_made,
        COALESCE(rs.field_goals_attempted, 0) as field_goals_attempted
    FROM Players p
    LEFT JOIN PlayerSeasonRawStats rs ON p.player_id = rs.player_id AND rs.season = '2024-25'
    WHERE p.player_id IN ({placeholders})
    ORDER BY COALESCE(rs.minutes_played, 0) DESC
    """
    
    return pd.read_sql_query(query, conn, params=player_ids)

def assign_fallback_archetype(row):
    """
    Assign fallback archetype based on simple heuristics.
    
    Archetype assignments:
    0 = Big Men (high rebounds, low 3PT rate, typically C/PF)
    1 = Primary Ball Handlers (high assists, typically PG/SG)  
    2 = Role Players (everyone else)
    """
    
    # Extract basic stats
    minutes_played = row['minutes_played']
    assists = row['assists']
    total_rebounds = row['total_rebounds']
    three_pointers_made = row['three_pointers_made']
    three_pointers_attempted = row['three_pointers_attempted']
    field_goals_attempted = row['field_goals_attempted']
    position = str(row['position']).upper() if pd.notna(row['position']) else ''
    
    # Calculate rates
    assist_rate = assists / max(minutes_played, 1) * 36  # per 36 minutes
    rebound_rate = total_rebounds / max(minutes_played, 1) * 36  # per 36 minutes
    three_point_rate = three_pointers_attempted / max(field_goals_attempted, 1) if field_goals_attempted > 0 else 0
    
    # Heuristic 1: Big Men (Archetype 0)
    # High rebound rate, low 3PT rate, typically C/PF
    if (rebound_rate > 8.0 and three_point_rate < 0.3) or position in ['C', 'PF']:
        return 0, "Big Men"
    
    # Heuristic 2: Primary Ball Handlers (Archetype 1)  
    # High assist rate, typically PG/SG
    elif assist_rate > 5.0 or position in ['PG', 'SG']:
        return 1, "Primary Ball Handlers"
    
    # Heuristic 3: Role Players (Archetype 2)
    # Everyone else
    else:
        return 2, "Role Players"

def implement_fallback_assignments():
    """Implement fallback archetype assignments for missing players."""
    
    db_path = "src/nba_stats/db/nba_stats.db"
    
    if not Path(db_path).exists():
        print(f"Error: Database file not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    
    try:
        print("Implementing fallback archetype assignments...")
        
        # Get missing players
        missing_player_ids = get_players_missing_archetypes(conn)
        print(f"Found {len(missing_player_ids)} players missing archetype assignments")
        
        if not missing_player_ids:
            print("No players missing archetype assignments")
            return True
        
        # Get player stats for fallback assignment
        player_stats = get_player_stats_for_fallback(conn, missing_player_ids)
        print(f"Retrieved stats for {len(player_stats)} players")
        
        # Assign fallback archetypes
        fallback_assignments = []
        archetype_counts = {0: 0, 1: 0, 2: 0}
        
        for _, row in player_stats.iterrows():
            archetype_id, archetype_name = assign_fallback_archetype(row)
            fallback_assignments.append({
                'player_id': row['player_id'],
                'player_name': row['player_name'],
                'archetype_id': archetype_id,
                'archetype_name': archetype_name,
                'minutes_played': row['minutes_played']
            })
            archetype_counts[archetype_id] += 1
        
        # Insert fallback assignments into database
        cursor = conn.cursor()
        
        for assignment in fallback_assignments:
            cursor.execute("""
                INSERT OR REPLACE INTO PlayerSeasonArchetypes 
                (player_id, season, archetype_id) 
                VALUES (?, '2024-25', ?)
            """, (assignment['player_id'], assignment['archetype_id']))
        
        conn.commit()
        print("✅ Successfully inserted fallback archetype assignments")
        
        # Show results
        print(f"\nFallback assignment results:")
        print(f"  Big Men: {archetype_counts[0]} players")
        print(f"  Primary Ball Handlers: {archetype_counts[1]} players") 
        print(f"  Role Players: {archetype_counts[2]} players")
        
        # Show top players by minutes in each category
        for archetype_id in [0, 1, 2]:
            archetype_name = ["Big Men", "Primary Ball Handlers", "Role Players"][archetype_id]
            top_players = [a for a in fallback_assignments if a['archetype_id'] == archetype_id]
            top_players.sort(key=lambda x: x['minutes_played'], reverse=True)
            
            print(f"\nTop 5 {archetype_name} by minutes:")
            for i, player in enumerate(top_players[:5]):
                print(f"  {i+1}. {player['player_name']:25s} - {player['minutes_played']:6.1f} min")
        
        # Save detailed results
        fallback_df = pd.DataFrame(fallback_assignments)
        fallback_df.to_csv("fallback_archetype_assignments.csv", index=False)
        print(f"\nSaved detailed results to: fallback_archetype_assignments.csv")
        
        return True
        
    except Exception as e:
        print(f"Error implementing fallback assignments: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = implement_fallback_assignments()
    exit(0 if success else 1)
