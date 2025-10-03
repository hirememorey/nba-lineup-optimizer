#!/usr/bin/env python3
"""
Analyze superclusters for qualitative validation (the "sniff test").

This script analyzes the results of lineup supercluster clustering and generates
human-readable reports to validate that the clusters make basketball sense.

This is the critical qualitative validation gate that must pass before proceeding
to Bayesian modeling.
"""

import sqlite3
import pandas as pd
import numpy as np
from collections import Counter
from pathlib import Path
import json

def load_archetype_lineups(conn):
    """Load archetype lineup data from possessions."""
    
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
    
    player_archetypes = pd.read_sql_query(query, conn)
    player_to_archetype = dict(zip(player_archetypes['player_id'], player_archetypes['archetype_name']))
    
    # Get possession data
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
            archetype_name = player_to_archetype.get(player_id, "Unknown")
            home_archetypes.append(archetype_name)
            
        for player_id in away_players:
            archetype_name = player_to_archetype.get(player_id, "Unknown")
            away_archetypes.append(archetype_name)
        
        # Create archetype lineup strings
        home_archetype_lineup = "_".join(sorted(home_archetypes))
        away_archetype_lineup = "_".join(sorted(away_archetypes))
        
        archetype_lineups.append({
            'game_id': row['game_id'],
            'event_num': row['event_num'],
            'home_archetype_lineup': home_archetype_lineup,
            'away_archetype_lineup': away_archetype_lineup,
            'offensive_team_id': row['offensive_team_id']
        })
    
    return pd.DataFrame(archetype_lineups)

def get_team_lineup_frequency(archetype_lineups):
    """Get the frequency of each archetype lineup by team."""
    
    # Get team information
    conn = sqlite3.connect("src/nba_stats/db/nba_stats.db")
    teams_query = "SELECT team_id, team_name FROM Teams"
    teams_df = pd.read_sql_query(teams_query, conn)
    team_id_to_name = dict(zip(teams_df['team_id'], teams_df['team_name']))
    conn.close()
    
    # Count lineup frequency by team
    team_lineups = {}
    
    for _, row in archetype_lineups.iterrows():
        team_id = row['offensive_team_id']
        team_name = team_id_to_name.get(team_id, f"Team_{team_id}")
        lineup = row['home_archetype_lineup'] if row['offensive_team_id'] == team_id else row['away_archetype_lineup']
        
        if team_name not in team_lineups:
            team_lineups[team_name] = Counter()
        
        team_lineups[team_name][lineup] += 1
    
    return team_lineups

def analyze_supercluster(supercluster_id, lineup_assignments, team_lineups):
    """Analyze a single supercluster and generate a report."""
    
    # Get lineups in this supercluster
    cluster_lineups = [lineup for lineup, cluster in lineup_assignments.items() if cluster == supercluster_id]
    
    if not cluster_lineups:
        return None
    
    # Count archetype frequency in this cluster
    archetype_counts = Counter()
    for lineup in cluster_lineups:
        archetypes = lineup.split('_')
        archetype_counts.update(archetypes)
    
    # Get teams that use these lineups most frequently
    team_usage = {}
    for team_name, lineup_freqs in team_lineups.items():
        team_cluster_usage = sum(lineup_freqs.get(lineup, 0) for lineup in cluster_lineups)
        if team_cluster_usage > 0:
            team_usage[team_name] = team_cluster_usage
    
    # Sort teams by usage
    top_teams = sorted(team_usage.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Generate report
    report = {
        'supercluster_id': supercluster_id,
        'num_lineups': len(cluster_lineups),
        'lineups': cluster_lineups,
        'archetype_distribution': dict(archetype_counts),
        'top_teams': top_teams,
        'total_usage': sum(team_usage.values())
    }
    
    return report

def generate_supercluster_report(supercluster_assignments_file):
    """Generate a comprehensive supercluster analysis report."""
    
    # Load supercluster assignments
    if not Path(supercluster_assignments_file).exists():
        print(f"Error: Supercluster assignments file not found: {supercluster_assignments_file}")
        return False
    
    with open(supercluster_assignments_file, 'r') as f:
        assignments_data = json.load(f)
    
    lineup_assignments = assignments_data['lineup_assignments']
    
    # Load archetype lineup data
    conn = sqlite3.connect("src/nba_stats/db/nba_stats.db")
    archetype_lineups = load_archetype_lineups(conn)
    team_lineups = get_team_lineup_frequency(archetype_lineups)
    conn.close()
    
    # Analyze each supercluster
    superclusters = {}
    unique_clusters = set(lineup_assignments.values())
    
    for cluster_id in unique_clusters:
        report = analyze_supercluster(cluster_id, lineup_assignments, team_lineups)
        if report:
            superclusters[cluster_id] = report
    
    # Generate markdown report
    report_content = generate_markdown_report(superclusters)
    
    # Save report
    report_file = "supercluster_analysis_report.md"
    with open(report_file, 'w') as f:
        f.write(report_content)
    
    print(f"✅ Generated supercluster analysis report: {report_file}")
    
    # Print summary for quick validation
    print("\n" + "="*60)
    print("SUPERCLUSTER SUMMARY")
    print("="*60)
    
    for cluster_id in sorted(superclusters.keys()):
        report = superclusters[cluster_id]
        print(f"\nSupercluster {cluster_id}:")
        print(f"  Lineups: {report['num_lineups']}")
        print(f"  Total Usage: {report['total_usage']:,}")
        print(f"  Top Teams: {', '.join([team for team, _ in report['top_teams'][:3]])}")
        print(f"  Archetype Distribution: {report['archetype_distribution']}")
    
    return True

def generate_markdown_report(superclusters):
    """Generate a markdown report for the superclusters."""
    
    content = "# Supercluster Analysis Report\n\n"
    content += "Generated for qualitative validation of lineup superclusters.\n\n"
    content += "## Summary\n\n"
    content += f"Total superclusters: {len(superclusters)}\n"
    content += f"Total unique lineups: {sum(r['num_lineups'] for r in superclusters.values())}\n\n"
    
    for cluster_id in sorted(superclusters.keys()):
        report = superclusters[cluster_id]
        
        content += f"## Supercluster {cluster_id}\n\n"
        content += f"**Lineups in cluster:** {report['num_lineups']}\n"
        content += f"**Total usage:** {report['total_usage']:,} possessions\n\n"
        
        content += "### Lineup Compositions\n"
        for lineup in sorted(report['lineups']):
            archetypes = lineup.split('_')
            content += f"- {lineup}: {', '.join(archetypes)}\n"
        content += "\n"
        
        content += "### Archetype Distribution\n"
        for archetype, count in sorted(report['archetype_distribution'].items()):
            percentage = count / sum(report['archetype_distribution'].values()) * 100
            content += f"- {archetype}: {count} ({percentage:.1f}%)\n"
        content += "\n"
        
        content += "### Top Teams Using This Style\n"
        for i, (team, usage) in enumerate(report['top_teams'][:5], 1):
            content += f"{i}. {team}: {usage:,} possessions\n"
        content += "\n"
        
        content += "---\n\n"
    
    return content

def main():
    """Main function to analyze superclusters."""
    
    # For now, create a mock supercluster assignment for testing
    # In the real implementation, this would come from the clustering results
    mock_assignments = {
        "lineup_assignments": {
            "Big Men_Primary Ball Handlers_Role Players_Role Players_Role Players": 0,
            "Big Men_Primary Ball Handlers_Primary Ball Handlers_Role Players_Role Players": 1,
            "Primary Ball Handlers_Primary Ball Handlers_Role Players_Role Players_Role Players": 2,
            "Primary Ball Handlers_Role Players_Role Players_Role Players_Role Players": 2,
            "Big Men_Big Men_Primary Ball Handlers_Role Players_Role Players": 0,
            "Big Men_Primary Ball Handlers_Primary Ball Handlers_Primary Ball Handlers_Role Players": 1,
            "Big Men_Role Players_Role Players_Role Players_Role Players": 0,
            "Big Men_Big Men_Primary Ball Handlers_Primary Ball Handlers_Role Players": 0,
            "Primary Ball Handlers_Primary Ball Handlers_Primary Ball Handlers_Role Players_Role Players": 1,
            "Role Players_Role Players_Role Players_Role Players_Role Players": 2,
            "Big Men_Big Men_Big Men_Primary Ball Handlers_Role Players": 0,
            "Big Men_Big Men_Primary Ball Handlers_Primary Ball Handlers_Primary Ball Handlers": 1,
            "Primary Ball Handlers_Primary Ball Handlers_Primary Ball Handlers_Primary Ball Handlers_Role Players": 1,
            "Big Men_Big Men_Role Players_Role Players_Role Players": 0,
            "Primary Ball Handlers_Primary Ball Handlers_Primary Ball Handlers_Primary Ball Handlers_Primary Ball Handlers": 1,
            "Big Men_Big Men_Big Men_Role Players_Role Players": 0,
            "Big Men_Big Men_Big Men_Big Men_Role Players": 0
        }
    }
    
    # Save mock assignments for testing
    with open("mock_supercluster_assignments.json", 'w') as f:
        json.dump(mock_assignments, f, indent=2)
    
    # Generate report
    success = generate_supercluster_report("mock_supercluster_assignments.json")
    
    if success:
        print("\n✅ Supercluster analysis complete")
        print("Review the generated report to validate that clusters make basketball sense")
        print("This is the critical 'sniff test' that must pass before Bayesian modeling")
    
    return success

if __name__ == "__main__":
    main()
