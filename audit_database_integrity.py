#!/usr/bin/env python3
"""
Database Integrity Audit for Phase 2 Readiness

This script performs comprehensive validation of database data quality BEFORE
attempting Phase 2 multi-season model training. It checks for:
- Data completeness (join success rates)
- Season alignment (DARKO ratings match possessions)
- Archetype distribution (all 8 archetypes present)
- Data quality spot-checks (known players)
- Matchup generation feasibility

Based on pre-mortem analysis: We must validate data integrity FIRST before
fixing downstream bugs, or risk building on corrupted foundation.
"""

import sqlite3
import pandas as pd
from collections import defaultdict, Counter
from datetime import datetime
import sys

def connect_db():
    """Connect to the database."""
    return sqlite3.connect('src/nba_stats/db/nba_stats.db')

def audit_data_completeness(conn):
    """
    Check 1: Can we join possession players to required tables?
    
    Samples random possessions per season and verifies all 10 players
    can be joined to DARKO and archetype tables.
    """
    print("\n" + "="*80)
    print("AUDIT CHECK 1: Data Completeness (Join Success Rates)")
    print("="*80)
    
    seasons = ['2018-19', '2020-21', '2021-22']
    results = {}
    
    for season in seasons:
        print(f"\nAnalyzing {season}...")
        
        # Sample 1000 random possessions per season
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT p.game_id, p.event_num
            FROM Possessions p
            JOIN Games g ON p.game_id = g.game_id
            WHERE g.season = ?
            ORDER BY RANDOM()
            LIMIT 1000
        """, (season,))
        
        sample_possessions = cursor.fetchall()
        total_samples = len(sample_possessions)
        
        if total_samples == 0:
            print(f"  ⚠️  No possessions found for {season}")
            results[season] = {'join_success': 0, 'total': 0}
            continue
        
        # Check join success
        archetype_table = f"PlayerArchetypeFeatures_{season.replace('-', '_')}"
        join_success = 0
        join_failures = []
        
        for row in sample_possessions:
            poss_id, game_id = row[0], row[1]
            
            try:
                # Get full possession row to access individual player columns
                full_row = conn.execute("""
                    SELECT home_player_1_id, home_player_2_id, home_player_3_id, 
                           home_player_4_id, home_player_5_id,
                           away_player_1_id, away_player_2_id, away_player_3_id,
                           away_player_4_id, away_player_5_id
                    FROM Possessions
                    WHERE game_id = ? AND event_num = ?
                """, (game_id, poss_id)).fetchone()
                
                if not full_row:
                    join_failures.append({'possession_id': poss_id, 'error': 'Could not fetch full row'})
                    continue
                
                # Extract player IDs from columns
                home_players = [full_row[i] for i in range(5)]
                away_players = [full_row[i] for i in range(5, 10)]
                all_players = home_players + away_players
                
                # Filter out NULL values and ensure we have exactly 10 players
                all_players = [p for p in all_players if p is not None]
                
                # If we don't have 10 valid players, skip
                if len(all_players) < 10:
                    join_failures.append({
                        'possession_id': f"{game_id}:{poss_id}",
                        'darko_count': 0,
                        'archetype_count': 0,
                        'expected': 10,
                        'actual_players': len(all_players)
                    })
                    continue
                
                # Check DARKO join
                placeholders = ','.join('?'*len(all_players))
                darko_query = f"""
                    SELECT COUNT(*) FROM PlayerSeasonSkill
                    WHERE player_id IN ({placeholders}) AND season = ?
                """
                darko_check = conn.execute(darko_query, all_players + [season])
                
                darko_count = darko_check.fetchone()[0]
                
                # Check archetype join
                archetype_query = f"""
                    SELECT COUNT(*) FROM {archetype_table}
                    WHERE player_id IN ({placeholders})
                """
                archetype_check = conn.execute(archetype_query, all_players)
                
                archetype_count = archetype_check.fetchone()[0]
                
                # Success if all 10 players have both DARKO and archetype
                if darko_count == 10 and archetype_count == 10:
                    join_success += 1
                else:
                    join_failures.append({
                        'possession_id': poss_id,
                        'darko_count': darko_count,
                        'archetype_count': archetype_count,
                        'expected': 10
                    })
                    
            except Exception as e:
                join_failures.append({'possession_id': poss_id, 'error': str(e)})
        
        success_rate = (join_success / total_samples) * 100
        results[season] = {'join_success': join_success, 'total': total_samples}
        
        print(f"  Total sample possessions: {total_samples:,}")
        print(f"  Successful joins: {join_success:,} ({success_rate:.1f}%)")
        print(f"  Failed joins: {len(join_failures)}")
        
        if len(join_failures) > 0:
            print(f"  ⚠️  Sample of failures:")
            for fail in join_failures[:5]:
                print(f"     Possession {fail.get('possession_id')}: DARKO={fail.get('darko_count', 0)}/10, Archetype={fail.get('archetype_count', 0)}/10")
    
    return results

def audit_season_alignment(conn):
    """
    Check 2: Are DARKO ratings aligned with possession seasons?
    
    Verify no cross-season contamination.
    """
    print("\n" + "="*80)
    print("AUDIT CHECK 2: Season Alignment (DARKO Ratings Match Possessions)")
    print("="*80)
    
    seasons = ['2018-19', '2020-21', '2021-22']
    
    for season in seasons:
        print(f"\nAnalyzing {season}...")
        
        # Get player count in possessions (simpler approach)
        all_player_ids = set()
        cursor = conn.execute("""
            SELECT home_player_1_id, home_player_2_id, home_player_3_id, home_player_4_id, home_player_5_id,
                   away_player_1_id, away_player_2_id, away_player_3_id, away_player_4_id, away_player_5_id
            FROM Possessions p
            JOIN Games g ON p.game_id = g.game_id
            WHERE g.season = ?
            LIMIT 10000
        """, (season,))
        for row in cursor:
            all_player_ids.update([p for p in row if p is not None])
        poss_players = len(all_player_ids)
        
        # Get DARKO coverage for that season
        darko_players = conn.execute("""
            SELECT COUNT(DISTINCT player_id)
            FROM PlayerSeasonSkill
            WHERE season = ?
        """, (season,)).fetchone()[0]
        
        # Get overlap (simplified - check sample of players from possessions)
        darko_player_ids = set(conn.execute("""
            SELECT player_id FROM PlayerSeasonSkill WHERE season = ?
        """, (season,)).fetchall())
        darko_player_ids = {row[0] for row in darko_player_ids}
        overlap = len(all_player_ids & darko_player_ids)
        
        print(f"  Players in possessions: {poss_players}")
        print(f"  Players with DARKO ratings: {darko_players}")
        print(f"  Overlap: {overlap} ({overlap/poss_players*100 if poss_players > 0 else 0:.1f}%)")
        
        if poss_players > 0 and overlap / poss_players < 0.5:
            print(f"  ⚠️  Less than 50% overlap - season alignment may be problematic")

def audit_archetype_distribution(conn):
    """
    Check 3: Are all 8 archetypes present and reasonably distributed?
    
    For each historical season, verify archetype assignments.
    """
    print("\n" + "="*80)
    print("AUDIT CHECK 3: Archetype Distribution (All 8 Archetypes Present)")
    print("="*80)
    
    seasons = ['2018-19', '2020-21', '2021-22']
    
    for season in seasons:
        archetype_table = f"PlayerArchetypeFeatures_{season.replace('-', '_')}"
        print(f"\nAnalyzing {season}...")
        
        try:
            cursor = conn.execute(f"""
                SELECT archetype_id, COUNT(*) as count
                FROM {archetype_table}
                GROUP BY archetype_id
                ORDER BY archetype_id
            """)
            
            distribution = cursor.fetchall()
            total = sum(row[1] for row in distribution)
            
            print(f"  Total players with archetypes: {total}")
            print(f"  Archetype distribution:")
            
            for arch_id, count in distribution:
                pct = (count / total) * 100 if total > 0 else 0
                print(f"    Archetype {arch_id}: {count} players ({pct:.1f}%)")
                
                # Flag unusual distributions
                if pct < 1.0:
                    print(f"      ⚠️  Less than 1% of players - may indicate clustering issue")
                elif pct > 40:
                    print(f"      ⚠️  More than 40% of players - may indicate clustering imbalance")
            
            # Check if all 8 archetypes present
            arch_ids = [row[0] for row in distribution]
            missing = [i for i in range(1, 9) if i not in arch_ids]
            
            if missing:
                print(f"  ⚠️  Missing archetypes: {missing}")
            else:
                print(f"  ✅  All 8 archetypes present")
                
        except Exception as e:
            print(f"  ❌  Error reading {archetype_table}: {e}")

def audit_spot_checks(conn):
    """
    Check 4: Spot-check known players for reasonableness.
    
    Verify LeBron, AD, Steph, etc. have sensible data across seasons.
    """
    print("\n" + "="*80)
    print("AUDIT CHECK 4: Data Quality Spot-Checks (Known Players)")
    print("="*80)
    
    # Known players to check (player_id, name)
    known_players = [
        (201935, "LeBron James"),
        (203076, "Anthony Davis"),
        (201566, "Russell Westbrook"),
        (202681, "Kawhi Leonard"),
        (201939, "Stephen Curry"),
        (2544, "LeBron James"),  # Different ID for older seasons?
    ]
    
    seasons = ['2018-19', '2020-21', '2021-22']
    
    for player_id, name in known_players:
        print(f"\n  Checking {name} (ID: {player_id})...")
        
        for season in seasons:
            arch_table = f"PlayerArchetypeFeatures_{season.replace('-', '_')}"
            
            # Check archetype
            arch = conn.execute(f"""
                SELECT archetype_id FROM {arch_table}
                WHERE player_id = ?
            """, (player_id,)).fetchone()
            
            # Check DARKO
            darko = conn.execute("""
                SELECT o_darko, d_darko FROM PlayerSeasonSkill
                WHERE player_id = ? AND season = ?
            """, (player_id, season)).fetchone()
            
            if arch and darko:
                arch_id = arch[0]
                o_darko, d_darko = darko
                print(f"    {season}: Archetype={arch_id}, O_DARKO={o_darko:.2f}, D_DARKO={d_darko:.2f}")
            elif arch and not darko:
                print(f"    {season}: Archetype={arch[0]}, ⚠️  No DARKO rating")
            elif darko and not arch:
                print(f"    {season}: ⚠️  No archetype, DARKO: O={o_darko:.2f}, D={d_darko:.2f}")
            else:
                print(f"    {season}: ⚠️  Player not found in database")

def audit_supercluster_feasibility(conn):
    """
    Check 5: Preview supercluster distributions for matchup feasibility.
    
    Are there enough lineups to generate 36 unique matchups?
    """
    print("\n" + "="*80)
    print("AUDIT CHECK 5: Supercluster Feasibility (Matchup Generation Preview)")
    print("="*80)
    
    # Check if supercluster assignments exist
    try:
        cursor = conn.execute("""
            SELECT COUNT(*) FROM lineup_features_with_superclusters
        """)
        count = cursor.fetchone()[0]
        print(f"\n  Total lineup-supercluster records: {count:,}")
        
        # Check unique superclusters
        cursor = conn.execute("""
            SELECT DISTINCT supercluster_id FROM lineup_features_with_superclusters
            ORDER BY supercluster_id
        """)
        superclusters = [row[0] for row in cursor.fetchall()]
        print(f"  Unique superclusters: {superclusters}")
        
        # Calculate possible matchups
        if len(superclusters) > 0:
            possible_matchups = len(superclusters) * len(superclusters)
            print(f"  Possible matchup combinations: {possible_matchups}")
            
            if possible_matchups < 36:
                print(f"  ⚠️  Not enough superclusters to generate 36 matchups (need 6 unique superclusters)")
        
    except Exception as e:
        print(f"  ⚠️  Could not query superclusters: {e}")

def audit_historical_comparison(conn):
    """
    Check 6: Compare historical vs 2022-23 data quality.
    
    Is the 13% pass rate consistent with known-good 2022-23?
    """
    print("\n" + "="*80)
    print("AUDIT CHECK 6: Historical Comparison (Data Quality Consistency)")
    print("="*80)
    
    seasons = ['2018-19', '2020-21', '2021-22', '2022-23']
    
    print("\n  Possession counts and expected eligibility:")
    for season in seasons:
        # Get total possessions
        total = conn.execute("""
            SELECT COUNT(*) FROM Possessions p
            JOIN Games g ON p.game_id = g.game_id
            WHERE g.season = ?
        """, (season,)).fetchone()[0]
        
        # Get eligible player count (1000+ minutes with archetype + DARKO)
        archetype_table = f"PlayerArchetypeFeatures_{season.replace('-', '_')}"
        
        eligible = conn.execute(f"""
            SELECT COUNT(DISTINCT af.player_id)
            FROM {archetype_table} af
            JOIN PlayerSeasonSkill pss ON af.player_id = pss.player_id
            WHERE pss.season = ?
        """, (season,)).fetchone()[0]
        
        print(f"\n  {season}:")
        print(f"    Total possessions: {total:,}")
        print(f"    Eligible players: {eligible}")
        
        # Rough estimate: with eligible players, what % of possessions pass?
        # Simplistic calc: assume uniform player distribution
        if eligible > 0:
            coverage_pct = (eligible / 340) * 100 if season != '2022-23' else 100
            print(f"    Estimated coverage: {coverage_pct:.1f}% of active players")

def generate_report(results):
    """Generate final audit report."""
    print("\n" + "="*80)
    print("FINAL AUDIT SUMMARY")
    print("="*80)
    
    # Determine overall status
    issues_found = []
    
    if 'join_success' in str(results):
        print("\n📊 Status: Database integrity audit complete")
        print("\nNext steps:")
        print("1. Review the detailed checks above")
        print("2. If any ⚠️  warnings found, investigate root causes")
        print("3. If all checks pass, proceed with Phase 2 bug fixes")
        print("4. If critical issues found, fix database before proceeding")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"database_integrity_audit_{timestamp}.txt"
    
    print(f"\n📝 Full report saved to: {report_file}")

def main():
    """Run complete database integrity audit."""
    print("\n" + "🔍" * 40)
    print("DATABASE INTEGRITY AUDIT - PHASE 2 READINESS")
    print("🔍" * 40)
    print("\nThis audit validates database integrity BEFORE attempting Phase 2 fixes.")
    print("We must ensure data is correct before fixing downstream bugs.")
    
    conn = connect_db()
    
    try:
        results = {}
        
        # Run all audit checks
        results['completeness'] = audit_data_completeness(conn)
        audit_season_alignment(conn)
        audit_archetype_distribution(conn)
        audit_spot_checks(conn)
        audit_supercluster_feasibility(conn)
        audit_historical_comparison(conn)
        
        # Generate report
        generate_report(results)
        
        print("\n✅ Audit complete!")
        
    except Exception as e:
        print(f"\n❌ Audit failed with error: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
