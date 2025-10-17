#!/usr/bin/env python3
"""
Populate DARKO data into the NBA Lineup Optimizer database - Fixed version.

This script processes the DARKO data from nbarapm.com and populates the PlayerSeasonSkill table
with offensive and defensive skill ratings for historical seasons.

Usage:
    python populate_darko_data_fixed.py [--season SEASON] [--all-seasons]
"""

import json
import sqlite3
import argparse
import sys
from pathlib import Path

def connect_to_database():
    """Connect to the NBA stats database."""
    db_path = "src/nba_stats/db/nba_stats.db"
    if not Path(db_path).exists():
        print(f"❌ Database not found at {db_path}")
        print("Please run the data pipeline first: python master_data_pipeline.py --season 2022-23")
        sys.exit(1)
    
    return sqlite3.connect(db_path)

def load_darko_data():
    """Load DARKO data from JSON file."""
    darko_file = "darko_data.json"
    if not Path(darko_file).exists():
        print(f"❌ DARKO data file not found: {darko_file}")
        print("Please download the DARKO data first using the curl command provided.")
        sys.exit(1)
    
    with open(darko_file, 'r') as f:
        return json.load(f)

def get_player_mapping(cursor):
    """Get mapping of NBA IDs to our internal player IDs."""
    # First try to get from PlayerSeasonSkill table which has player_name
    cursor.execute("""
        SELECT DISTINCT ps.player_id, ps.player_name
        FROM PlayerSeasonSkill ps
        WHERE ps.player_name IS NOT NULL
    """)
    name_mapping = {name.lower(): player_id for player_id, name in cursor.fetchall()}
    
    # Also get from Players table
    cursor.execute("""
        SELECT player_id, player_name 
        FROM Players 
        WHERE player_name IS NOT NULL
    """)
    for player_id, name in cursor.fetchall():
        if name.lower() not in name_mapping:
            name_mapping[name.lower()] = player_id
    
    return name_mapping

def get_darko_season(season):
    """Convert season string to DARKO season number."""
    if season == "2018-19":
        return 2019
    elif season == "2019-20":
        return 2020
    elif season == "2020-21":
        return 2021
    elif season == "2021-22":
        return 2022
    elif season == "2022-23":
        return 2023
    elif season == "2023-24":
        return 2024
    elif season == "2024-25":
        return 2025
    else:
        # Generic mapping for other seasons
        return int(season.split('-')[1])

def populate_darko_data(season=None, all_seasons=False):
    """Populate DARKO data into the database."""
    
    print("🏀 NBA Lineup Optimizer - DARKO Data Population (Fixed)")
    print("=" * 60)
    
    # Connect to database
    print("📊 Connecting to database...")
    conn = connect_to_database()
    cursor = conn.cursor()
    
    # Load DARKO data
    print("📥 Loading DARKO data...")
    darko_data = load_darko_data()
    print(f"   Loaded {len(darko_data)} total records")
    
    # Get player mapping
    print("🔍 Building player mapping...")
    player_mapping = get_player_mapping(cursor)
    print(f"   Found {len(player_mapping)} players with names")
    
    # Filter data by season
    if all_seasons:
        filtered_data = darko_data
        print(f"📅 Processing all seasons...")
    elif season:
        darko_season = get_darko_season(season)
        filtered_data = [record for record in darko_data if record.get('season') == darko_season]
        print(f"📅 Processing season {season} (DARKO season {darko_season})...")
    else:
        # Default to 2022-23 for Phase 1
        filtered_data = [record for record in darko_data if record.get('season') == 2023]
        print(f"📅 Processing 2022-23 season (default for Phase 1)...")
    
    print(f"   Found {len(filtered_data)} records for target season(s)")
    
    # Process records
    inserted_count = 0
    skipped_count = 0
    error_count = 0
    
    print("💾 Inserting DARKO data...")
    
    for record in filtered_data:
        try:
            player_name = record.get('player_name')
            if not player_name or player_name.lower() not in player_mapping:
                skipped_count += 1
                continue
            
            player_id = player_mapping[player_name.lower()]
            # Map DARKO season to our season format
            darko_season = record.get('season')
            if darko_season == 2019:
                season = "2018-19"
            elif darko_season == 2020:
                season = "2019-20"
            elif darko_season == 2021:
                season = "2020-21"
            elif darko_season == 2022:
                season = "2021-22"
            elif darko_season == 2023:
                season = "2022-23"
            elif darko_season == 2024:
                season = "2023-24"
            elif darko_season == 2025:
                season = "2024-25"
            else:
                # Generic mapping for other seasons
                season = f"20{str(darko_season)[-2:]}-{str(darko_season + 1)[-2:]}"
            
            # Extract skill ratings
            offensive_darko = record.get('o_dpm')
            defensive_darko = record.get('d_dpm')
            darko = record.get('dpm')
            
            if offensive_darko is None or defensive_darko is None or darko is None:
                skipped_count += 1
                continue
            
            # Insert or update record in PlayerSeasonSkill table
            cursor.execute("""
                INSERT OR REPLACE INTO PlayerSeasonSkill 
                (player_id, season, player_name, team_abbreviation, offensive_darko, defensive_darko, darko)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (player_id, season, player_name, record.get('team_name'), 
                  offensive_darko, defensive_darko, darko))
            
            inserted_count += 1
            
            if inserted_count % 100 == 0:
                print(f"   Processed {inserted_count} records...")
                
        except Exception as e:
            print(f"   ⚠️  Error processing record for player {player_name}: {e}")
            error_count += 1
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("\n✅ DARKO Data Population Complete!")
    print(f"   📊 Records inserted/updated: {inserted_count}")
    print(f"   ⏭️  Records skipped: {skipped_count}")
    print(f"   ❌ Errors: {error_count}")
    
    if inserted_count > 0:
        print(f"\n🎉 Successfully populated DARKO data for {inserted_count} players!")
        print("   This should unblock Phase 1 of the project.")
    else:
        print("\n⚠️  No records were inserted. Check the data and player mapping.")

def verify_data(cursor, season="2022-23"):
    """Verify the populated data."""
    print(f"\n🔍 Verifying DARKO data for {season}...")
    
    cursor.execute("""
        SELECT COUNT(*) 
        FROM PlayerSeasonSkill 
        WHERE season = ? AND offensive_darko IS NOT NULL
    """, (season,))
    
    count = cursor.fetchone()[0]
    print(f"   DARKO records for {season}: {count}")
    
    if count > 0:
        cursor.execute("""
            SELECT player_name, offensive_darko, defensive_darko, darko
            FROM PlayerSeasonSkill 
            WHERE season = ? AND offensive_darko IS NOT NULL
            ORDER BY offensive_darko DESC
            LIMIT 5
        """, (season,))
        
        print(f"   Top 5 offensive players:")
        for name, off_skill, def_skill, total_skill in cursor.fetchall():
            print(f"     {name}: Off={off_skill:.2f}, Def={def_skill:.2f}, Total={total_skill:.2f}")

def main():
    parser = argparse.ArgumentParser(description='Populate DARKO data into NBA Lineup Optimizer database (Fixed)')
    parser.add_argument('--season', help='Season to process (e.g., 2018-19, 2019-20, 2020-21, 2021-22, 2022-23, 2023-24, 2024-25)')
    parser.add_argument('--all-seasons', action='store_true', help='Process all available seasons')
    parser.add_argument('--verify', action='store_true', help='Verify the data after insertion')
    
    args = parser.parse_args()
    
    # Populate data
    populate_darko_data(season=args.season, all_seasons=args.all_seasons)
    
    # Verify data if requested
    if args.verify or not args.all_seasons:
        conn = connect_to_database()
        cursor = conn.cursor()
        verify_data(cursor, args.season or "2022-23")
        conn.close()

if __name__ == "__main__":
    main()
