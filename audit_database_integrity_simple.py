#!/usr/bin/env python3
"""
Simplified Database Integrity Audit for Phase 2 Readiness

This script performs essential validation of database data quality.
"""

import sqlite3
from collections import Counter

def main():
    print("\n" + "🔍" * 40)
    print("SIMPLIFIED DATABASE INTEGRITY AUDIT")
    print("🔍" * 40)
    
    conn = sqlite3.connect('src/nba_stats/db/nba_stats.db')
    
    try:
        # Check 1: Possession counts per season
        print("\n📊 CHECK 1: Possession Counts")
        print("="*80)
        seasons = ['2018-19', '2020-21', '2021-22', '2022-23']
        for season in seasons:
            count = conn.execute("""
                SELECT COUNT(*) FROM Possessions p
                JOIN Games g ON p.game_id = g.game_id
                WHERE g.season = ?
            """, (season,)).fetchone()[0]
            print(f"  {season}: {count:,} possessions")
        
        # Check 2: Archetype table sizes
        print("\n📊 CHECK 2: Archetype Coverage")
        print("="*80)
        for season in ['2018-19', '2020-21', '2021-22', '2022-23']:
            table = f"PlayerArchetypeFeatures_{season.replace('-', '_')}"
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                
                # Check archetype distribution
                arch_dist = conn.execute(f"""
                    SELECT archetype_id, COUNT(*) as cnt FROM {table}
                    GROUP BY archetype_id ORDER BY archetype_id
                """).fetchall()
                
                print(f"\n  {season}:")
                print(f"    Total players: {count}")
                print(f"    Archetype distribution:")
                for arch_id, cnt in arch_dist:
                    pct = (cnt / count) * 100 if count > 0 else 0
                    print(f"      Arch {arch_id}: {cnt} ({pct:.1f}%)")
            except Exception as e:
                print(f"  {season}: Table {table} not found or error: {e}")
        
        # Check 3: DARKO coverage per season
        print("\n📊 CHECK 3: DARKO Coverage")
        print("="*80)
        for season in seasons:
            count = conn.execute("""
                SELECT COUNT(*) FROM PlayerSeasonSkill
                WHERE season = ?
            """, (season,)).fetchone()[0]
            print(f"  {season}: {count} players")
        
        # Check 4: Player overlap analysis
        print("\n📊 CHECK 4: Data Quality Sample Check")
        print("="*80)
        print("\n  Sampling 100 random possessions from 2018-19...")
        
        # Get sample possessions
        cursor = conn.execute("""
            SELECT p.game_id, p.event_num,
                   p.home_player_1_id, p.home_player_2_id, p.home_player_3_id, p.home_player_4_id, p.home_player_5_id,
                   p.away_player_1_id, p.away_player_2_id, p.away_player_3_id, p.away_player_4_id, p.away_player_5_id
            FROM Possessions p
            JOIN Games g ON p.game_id = g.game_id
            WHERE g.season = '2018-19'
            LIMIT 100
        """)
        
        rows = cursor.fetchall()
        total_checked = 0
        darko_covered = 0
        arch_covered = 0
        both_covered = 0
        
        for row in rows:
            game_id, event_num = row[0], row[1]
            players = [p for p in row[2:] if p is not None]
            
            if len(players) == 10:
                total_checked += 1
                
                # Check DARKO coverage
                placeholders = ','.join('?'*len(players))
                darko_count = conn.execute(f"""
                    SELECT COUNT(*) FROM PlayerSeasonSkill
                    WHERE player_id IN ({placeholders}) AND season = '2018-19'
                """, players).fetchone()[0]
                
                # Check archetype coverage
                arch_count = conn.execute(f"""
                    SELECT COUNT(*) FROM PlayerArchetypeFeatures_2018_19
                    WHERE player_id IN ({placeholders})
                """, players).fetchone()[0]
                
                if darko_count == 10:
                    darko_covered += 1
                if arch_count == 10:
                    arch_covered += 1
                if darko_count == 10 and arch_count == 10:
                    both_covered += 1
        
        if total_checked > 0:
            pct_darko = (darko_covered / total_checked) * 100
            pct_arch = (arch_covered / total_checked) * 100
            pct_both = (both_covered / total_checked) * 100
            print(f"\n  Results:")
            print(f"    Possessions with 10 players: {total_checked}")
            print(f"    Complete DARKO: {darko_covered} ({pct_darko:.1f}%)")
            print(f"    Complete Archetype: {arch_covered} ({pct_arch:.1f}%)")
            print(f"    Complete Both: {both_covered} ({pct_both:.1f}%)")
        
        # Check 5: Historical archetype CSV files
        print("\n📊 CHECK 5: Archetype CSV Files")
        print("="*80)
        import os
        csv_files = [
            'player_archetypes_k8_2018-19.csv',
            'player_archetypes_k8_2020-21.csv',
            'player_archetypes_k8_2021-22.csv',
            'player_archetypes_k8_2022_23.csv'
        ]
        for fname in csv_files:
            status = "✅" if os.path.exists(fname) else "❌"
            print(f"  {status} {fname}")
        
        print("\n✅ Audit complete!")
        
    except Exception as e:
        print(f"\n❌ Audit failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
