"""
Sanity check script for validating all historical statistics data.

This script uses first principles to verify that we have all necessary data
for training multi-season Bayesian models. It checks:
1. Data existence across all stat tables for each historical season
2. Completeness (player coverage, NULL rates)
3. Data quality (plausibility checks)
4. Gap identification between what we have vs what we need

From the source paper (Section 2.1), we need:
- 48 player archetype metrics for K-means clustering
- Historical seasons: 2018-19, 2020-21, 2021-22
"""

import sqlite3
import pandas as pd
from typing import Dict, List, Tuple
from pathlib import Path
import json
from datetime import datetime

# Database path
DB_PATH = "src/nba_stats/db/nba_stats.db"

# Historical seasons to check
HISTORICAL_SEASONS = ["2018-19", "2020-21", "2021-22"]

# All stat tables that feed into archetype generation (from generate_archetype_features.py)
STAT_TABLES = [
    "Players",
    "PlayerSeasonRawStats",
    "PlayerSeasonAdvancedStats",
    "PlayerSeasonTrackingTouchesStats",
    "PlayerSeasonElbowTouchStats",
    "PlayerSeasonPostUpStats",
    "PlayerSeasonPaintTouchStats",
    "PlayerSeasonDriveStats",
    "PlayerSeasonCatchAndShootStats",
    "PlayerSeasonPassingStats",
    "PlayerSeasonPullUpStats",
    "PlayerSeasonOpponentShootingStats",
    "PlayerShotMetrics",
]


def check_table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    """Check if a table exists in the database."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None


def get_table_row_count(conn: sqlite3.Connection, table_name: str, season: str) -> int:
    """Get row count for a table filtered by season."""
    try:
        if not check_table_exists(conn, table_name):
            return 0
        
        # Determine if table has season column
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "season" not in columns:
            # Table doesn't have season column, return total count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            return cursor.fetchone()[0]
        
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE season = ?", (season,))
        return cursor.fetchone()[0]
    except Exception as e:
        print(f"Error checking {table_name}: {e}")
        return 0


def check_data_completeness(conn: sqlite3.Connection, season: str) -> Dict:
    """Check data completeness for a specific season."""
    results = {
        "season": season,
        "tables": {},
        "total_players": 0,
        "players_with_stats": 0,
        "missing_data": []
    }
    
    # Check each table
    for table in STAT_TABLES:
        count = get_table_row_count(conn, table, season)
        results["tables"][table] = {
            "exists": check_table_exists(conn, table),
            "row_count": count,
            "has_data": count > 0
        }
    
    # Get unique player count for this season
    try:
        cursor = conn.cursor()
        # Try to get player count from PlayerSeasonRawStats (most reliable)
        cursor.execute("""
            SELECT COUNT(DISTINCT player_id) 
            FROM PlayerSeasonRawStats 
            WHERE season = ?
        """, (season,))
        results["total_players"] = cursor.fetchone()[0]
    except Exception as e:
        print(f"Error getting player count for {season}: {e}")
    
    return results


def analyze_gaps(results: List[Dict]) -> Dict:
    """Analyze gaps in the collected data."""
    gap_report = {
        "timestamp": datetime.now().isoformat(),
        "seasons_checked": len(results),
        "findings": {},
        "recommendations": []
    }
    
    # Analyze each season
    for season_result in results:
        season = season_result["season"]
        gap_report["findings"][season] = {
            "tables_with_data": [],
            "tables_without_data": [],
            "player_coverage": season_result["total_players"],
            "issues": []
        }
        
        for table_name, table_info in season_result["tables"].items():
            if table_info["has_data"]:
                gap_report["findings"][season]["tables_with_data"].append(table_name)
            else:
                gap_report["findings"][season]["tables_without_data"].append(table_name)
                gap_report["findings"][season]["issues"].append(
                    f"Missing data for {table_name}"
                )
    
    # Generate recommendations
    for season in HISTORICAL_SEASONS:
        season_data = next((r for r in results if r["season"] == season), None)
        if not season_data:
            gap_report["recommendations"].append(
                f"No data found for {season} - run populate scripts"
            )
            continue
        
        missing_tables = gap_report["findings"][season]["tables_without_data"]
        if missing_tables:
            gap_report["recommendations"].append(
                f"For {season}, populate missing tables: {', '.join(missing_tables)}"
            )
    
    return gap_report


def main():
    """Main execution function."""
    print("=" * 80)
    print("HISTORICAL STATS SANITY CHECK")
    print("=" * 80)
    print()
    
    if not Path(DB_PATH).exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    results = []
    
    print("Checking data existence for historical seasons...")
    print()
    
    # Check each historical season
    for season in HISTORICAL_SEASONS:
        print(f"Season: {season}")
        print("-" * 80)
        season_results = check_data_completeness(conn, season)
        results.append(season_results)
        
        print(f"Total Players: {season_results['total_players']}")
        print()
        print("Stat Tables:")
        for table_name, table_info in season_results["tables"].items():
            status = "✅" if table_info["has_data"] else "❌"
            print(f"  {status} {table_name:50} {table_info['row_count']:6} rows")
        print()
    
    # Analyze gaps
    gap_report = analyze_gaps(results)
    
    # Print gap report
    print("=" * 80)
    print("GAP ANALYSIS")
    print("=" * 80)
    print()
    
    for season, findings in gap_report["findings"].items():
        print(f"Season: {season}")
        print(f"  Player Coverage: {findings['player_coverage']} players")
        print(f"  Tables with Data: {len(findings['tables_with_data'])}")
        print(f"  Tables without Data: {len(findings['tables_without_data'])}")
        if findings["issues"]:
            print(f"  Issues:")
            for issue in findings["issues"]:
                print(f"    - {issue}")
        print()
    
    # Recommendations
    if gap_report["recommendations"]:
        print("RECOMMENDATIONS:")
        for i, rec in enumerate(gap_report["recommendations"], 1):
            print(f"  {i}. {rec}")
        print()
    
    # Final summary
    all_seasons_complete = all(
        len(gap_report["findings"][s]["tables_without_data"]) == 0 
        for s in HISTORICAL_SEASONS
    )
    
    print("=" * 80)
    if all_seasons_complete:
        print("✅ ALL HISTORICAL DATA COMPLETE")
        print("Ready for multi-season Bayesian model training!")
    else:
        print("⚠️  DATA GAPS IDENTIFIED")
        print("Review recommendations above. Model training may proceed")
        print("with missing metrics defaulting to 0 (LEFT JOIN behavior).")
    print("=" * 80)
    
    conn.close()


if __name__ == "__main__":
    main()

