#!/usr/bin/env python3
"""
Generate lineup superclusters using the validated 3-archetype system.

This script implements the final lineup supercluster generation with:
1. Proper data density assessment (k=3 based on 17 unique lineups)
2. Qualitative validation framework (sniff test)
3. Basketball-meaningful supercluster names
"""

import sqlite3
import pandas as pd
import numpy as np
import json
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from collections import Counter
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LineupSuperclusterGenerator:
    """Generate lineup superclusters with proper validation."""
    
    def __init__(self, db_path: str = "src/nba_stats/db/nba_stats.db"):
        """Initialize the generator."""
        self.db_path = db_path
        self.conn = None
        
    def connect_database(self):
        """Connect to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def load_archetype_lineups(self):
        """Load archetype lineup data from possessions."""
        
        # Get player archetype mappings
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
        
        player_archetypes = pd.read_sql_query(query, self.conn)
        player_to_archetype = dict(zip(player_archetypes['player_id'], player_archetypes['archetype_id']))
        
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
        
        possessions = pd.read_sql_query(query, self.conn)
        logger.info(f"Loaded {len(possessions)} possessions with complete lineup data")
        
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
                archetype_id = player_to_archetype.get(player_id, -1)
                home_archetypes.append(archetype_id)
                
            for player_id in away_players:
                archetype_id = player_to_archetype.get(player_id, -1)
                away_archetypes.append(archetype_id)
            
            # Create archetype lineup strings (sorted for consistency)
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
    
    def create_lineup_features(self, archetype_lineups):
        """Create features for each unique archetype lineup."""
        
        # Get all unique lineups
        all_lineups = pd.concat([
            archetype_lineups['home_archetype_lineup'],
            archetype_lineups['away_archetype_lineup']
        ]).value_counts()
        
        logger.info(f"Found {len(all_lineups)} unique archetype lineups")
        
        # Create features for each lineup
        lineup_features = []
        
        for lineup, frequency in all_lineups.items():
            # Parse archetype lineup
            archetypes = [int(x) for x in lineup.split('_')]
            
            # Count archetype frequency
            archetype_counts = Counter(archetypes)
            big_men_count = archetype_counts.get(0, 0)
            ball_handlers_count = archetype_counts.get(1, 0)
            role_players_count = archetype_counts.get(2, 0)
            
            # Calculate features
            features = {
                'lineup_id': lineup,
                'frequency': frequency,
                'big_men_count': big_men_count,
                'ball_handlers_count': ball_handlers_count,
                'role_players_count': role_players_count,
                'big_men_ratio': big_men_count / 5.0,
                'ball_handlers_ratio': ball_handlers_count / 5.0,
                'role_players_ratio': role_players_count / 5.0,
                'dominance_score': max(big_men_count, ball_handlers_count, role_players_count) / 5.0,
                'balance_score': 1.0 - (np.var([big_men_count, ball_handlers_count, role_players_count]) / 4.0)
            }
            
            lineup_features.append(features)
        
        return pd.DataFrame(lineup_features)
    
    def find_optimal_k(self, features_df):
        """Find the optimal number of clusters based on data density."""
        
        n_lineups = len(features_df)
        
        # Data density constraints
        max_k_by_density = n_lineups // 5  # At least 5 lineups per cluster
        
        # Test k values from 2 to min(6, max_k_by_density)
        max_k = min(6, max_k_by_density)
        
        if max_k < 2:
            logger.warning("Insufficient data for clustering")
            return 2
        
        logger.info(f"Testing k values from 2 to {max_k}")
        
        # Prepare features for clustering
        feature_columns = ['big_men_ratio', 'ball_handlers_ratio', 'role_players_ratio', 
                          'dominance_score', 'balance_score']
        X = features_df[feature_columns].values
        
        # Test different k values
        results = []
        
        for k in range(2, max_k + 1):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X)
            
            # Calculate metrics
            silhouette = silhouette_score(X, cluster_labels)
            calinski_harabasz = calinski_harabasz_score(X, cluster_labels)
            davies_bouldin = davies_bouldin_score(X, cluster_labels)
            
            results.append({
                'k': k,
                'silhouette': silhouette,
                'calinski_harabasz': calinski_harabasz,
                'davies_bouldin': davies_bouldin,
                'inertia': kmeans.inertia_
            })
            
            logger.info(f"k={k}: silhouette={silhouette:.3f}, calinski_harabasz={calinski_harabasz:.1f}")
        
        # Choose optimal k (prefer higher k if metrics are similar)
        best_k = max(results, key=lambda x: x['silhouette'])['k']
        
        logger.info(f"Selected k={best_k} as optimal")
        return best_k
    
    def generate_superclusters(self, features_df, k):
        """Generate superclusters using K-means."""
        
        # Prepare features
        feature_columns = ['big_men_ratio', 'ball_handlers_ratio', 'role_players_ratio', 
                          'dominance_score', 'balance_score']
        X = features_df[feature_columns].values
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Perform clustering
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X_scaled)
        
        # Add cluster assignments to features
        features_df['supercluster_id'] = cluster_labels
        
        # Calculate cluster metrics
        silhouette = silhouette_score(X_scaled, cluster_labels)
        calinski_harabasz = calinski_harabasz_score(X_scaled, cluster_labels)
        davies_bouldin = davies_bouldin_score(X_scaled, cluster_labels)
        
        logger.info(f"Clustering completed:")
        logger.info(f"  Silhouette Score: {silhouette:.3f}")
        logger.info(f"  Calinski-Harabasz Score: {calinski_harabasz:.1f}")
        logger.info(f"  Davies-Bouldin Index: {davies_bouldin:.3f}")
        
        return features_df, kmeans, scaler
    
    def generate_qualitative_validation(self, features_df, archetype_lineups):
        """Generate qualitative validation report for superclusters."""
        
        # Get team information
        teams_query = "SELECT team_id, team_name FROM Teams"
        teams_df = pd.read_sql_query(teams_query, self.conn)
        team_id_to_name = dict(zip(teams_df['team_id'], teams_df['team_name']))
        
        # Count lineup frequency by team
        team_lineups = {}
        
        for _, row in archetype_lineups.iterrows():
            team_id = row['offensive_team_id']
            team_name = team_id_to_name.get(team_id, f"Team_{team_id}")
            lineup = row['home_archetype_lineup'] if row['offensive_team_id'] == team_id else row['away_archetype_lineup']
            
            if team_name not in team_lineups:
                team_lineups[team_name] = Counter()
            
            team_lineups[team_name][lineup] += 1
        
        # Generate report for each supercluster
        supercluster_reports = {}
        
        for cluster_id in sorted(features_df['supercluster_id'].unique()):
            cluster_id = int(cluster_id)  # Convert to Python int
            cluster_lineups = features_df[features_df['supercluster_id'] == cluster_id]
            
            logger.info(f"Processing cluster {cluster_id} with {len(cluster_lineups)} lineups")
            
            # Get lineup IDs in this cluster
            lineup_ids = cluster_lineups['lineup_id'].tolist()
            
            try:
                # Count archetype frequency
                archetype_counts = Counter()
                for lineup_id in lineup_ids:
                    archetypes = [int(x) for x in lineup_id.split('_')]
                    archetype_counts.update(archetypes)
                
                # Get teams using these lineups
                team_usage = {}
                for team_name, lineup_freqs in team_lineups.items():
                    team_cluster_usage = sum(lineup_freqs.get(lineup, 0) for lineup in lineup_ids)
                    if team_cluster_usage > 0:
                        team_usage[team_name] = team_cluster_usage
                
                # Sort teams by usage
                top_teams = sorted(team_usage.items(), key=lambda x: x[1], reverse=True)[:5]
                
                # Generate descriptive name
                if cluster_lineups['big_men_ratio'].mean() > 0.4:
                    cluster_name = "Big Man Heavy"
                elif cluster_lineups['ball_handlers_ratio'].mean() > 0.4:
                    cluster_name = "Ball Handler Heavy"
                else:
                    cluster_name = "Role Player Heavy"
                    
            except Exception as e:
                logger.error(f"Error processing cluster {cluster_id}: {e}")
                logger.error(f"Lineup IDs: {lineup_ids}")
                logger.error(f"Cluster lineups columns: {cluster_lineups.columns.tolist()}")
                raise
            
            supercluster_reports[cluster_id] = {
                'cluster_name': cluster_name,
                'num_lineups': int(len(cluster_lineups)),
                'lineup_ids': lineup_ids,
                'archetype_distribution': {str(k): int(v) for k, v in dict(archetype_counts).items()},
                'top_teams': [(team, int(usage)) for team, usage in top_teams],
                'total_usage': int(sum(team_usage.values()))
            }
        
        return supercluster_reports
    
    def save_results(self, features_df, kmeans, scaler, supercluster_reports):
        """Save clustering results and models."""
        
        # Create output directory
        output_dir = Path("lineup_supercluster_results")
        output_dir.mkdir(exist_ok=True)
        
        try:
            # Save lineup assignments (convert numpy types to Python types)
            lineup_assignments = dict(zip(features_df['lineup_id'], features_df['supercluster_id'].astype(int)))
            
            results = {
                'lineup_assignments': lineup_assignments,
                'supercluster_reports': supercluster_reports,
                'clustering_metrics': {
                    'k': int(len(supercluster_reports)),
                    'silhouette_score': float(silhouette_score(
                        scaler.transform(features_df[['big_men_ratio', 'ball_handlers_ratio', 'role_players_ratio', 
                                                    'dominance_score', 'balance_score']].values),
                        features_df['supercluster_id']
                    ))
                }
            }
        except Exception as e:
            logger.error(f"Error creating results dictionary: {e}")
            logger.error(f"Features_df columns: {features_df.columns.tolist()}")
            logger.error(f"Features_df dtypes: {features_df.dtypes}")
            raise
        
        # Save JSON results
        with open(output_dir / "supercluster_assignments.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save CSV results
        features_df.to_csv(output_dir / "lineup_supercluster_features.csv", index=False)
        
        # Save models
        import joblib
        joblib.dump(kmeans, output_dir / "supercluster_kmeans.pkl")
        joblib.dump(scaler, output_dir / "supercluster_scaler.pkl")
        
        # Generate markdown report
        self.generate_markdown_report(supercluster_reports, output_dir)
        
        logger.info(f"Results saved to {output_dir}")
        
        return output_dir
    
    def generate_markdown_report(self, supercluster_reports, output_dir):
        """Generate a markdown report for the superclusters."""
        
        content = "# Lineup Supercluster Analysis Report\n\n"
        content += "Generated for qualitative validation of lineup superclusters.\n\n"
        content += "## Summary\n\n"
        content += f"Total superclusters: {len(supercluster_reports)}\n"
        content += f"Total unique lineups: {sum(r['num_lineups'] for r in supercluster_reports.values())}\n\n"
        
        for cluster_id in sorted(supercluster_reports.keys()):
            report = supercluster_reports[cluster_id]
            
            content += f"## Supercluster {cluster_id}: {report['cluster_name']}\n\n"
            content += f"**Lineups in cluster:** {report['num_lineups']}\n"
            content += f"**Total usage:** {report['total_usage']:,} possessions\n\n"
            
            content += "### Lineup Compositions\n"
            for lineup_id in sorted(report['lineup_ids']):
                archetypes = [int(x) for x in lineup_id.split('_')]
                archetype_names = ['Big Men', 'Primary Ball Handlers', 'Role Players']
                archetype_list = [archetype_names[x] for x in archetypes]
                content += f"- {lineup_id}: {', '.join(archetype_list)}\n"
            content += "\n"
            
            content += "### Archetype Distribution\n"
            total_archetypes = sum(report['archetype_distribution'].values())
            for archetype_id, count in sorted(report['archetype_distribution'].items()):
                archetype_name = ['Big Men', 'Primary Ball Handlers', 'Role Players'][archetype_id]
                percentage = count / total_archetypes * 100
                content += f"- {archetype_name}: {count} ({percentage:.1f}%)\n"
            content += "\n"
            
            content += "### Top Teams Using This Style\n"
            for i, (team, usage) in enumerate(report['top_teams'], 1):
                content += f"{i}. {team}: {usage:,} possessions\n"
            content += "\n"
            
            content += "---\n\n"
        
        # Save report
        with open(output_dir / "supercluster_analysis_report.md", 'w') as f:
            f.write(content)
    
    def run(self):
        """Run the complete supercluster generation process."""
        
        if not self.connect_database():
            return False
        
        try:
            # Load archetype lineup data
            logger.info("Loading archetype lineup data...")
            archetype_lineups = self.load_archetype_lineups()
            
            # Create lineup features
            logger.info("Creating lineup features...")
            features_df = self.create_lineup_features(archetype_lineups)
            
            # Find optimal k
            logger.info("Finding optimal number of clusters...")
            optimal_k = self.find_optimal_k(features_df)
            
            # Generate superclusters
            logger.info(f"Generating {optimal_k} superclusters...")
            features_df, kmeans, scaler = self.generate_superclusters(features_df, optimal_k)
            
            # Generate qualitative validation
            logger.info("Generating qualitative validation...")
            supercluster_reports = self.generate_qualitative_validation(features_df, archetype_lineups)
            
            # Save results
            logger.info("Saving results...")
            output_dir = self.save_results(features_df, kmeans, scaler, supercluster_reports)
            
            # Print summary
            print("\n" + "="*60)
            print("SUPERCLUSTER GENERATION COMPLETE")
            print("="*60)
            
            for cluster_id in sorted(supercluster_reports.keys()):
                report = supercluster_reports[cluster_id]
                print(f"\nSupercluster {cluster_id}: {report['cluster_name']}")
                print(f"  Lineups: {report['num_lineups']}")
                print(f"  Total Usage: {report['total_usage']:,}")
                print(f"  Top Teams: {', '.join([team for team, _ in report['top_teams'][:3]])}")
            
            print(f"\n✅ Results saved to: {output_dir}")
            print("✅ Review the markdown report to validate superclusters make basketball sense")
            print("✅ This is the critical 'sniff test' that must pass before Bayesian modeling")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during supercluster generation: {e}")
            return False
        finally:
            if self.conn:
                self.conn.close()

def main():
    """Main function to generate lineup superclusters."""
    
    generator = LineupSuperclusterGenerator()
    success = generator.run()
    
    if success:
        print("\n🎉 Lineup supercluster generation completed successfully!")
        print("Next step: Review the qualitative validation report")
        print("If the superclusters make basketball sense, proceed to Bayesian modeling")
    else:
        print("\n❌ Lineup supercluster generation failed")
        print("Check the logs for error details")
    
    return success

if __name__ == "__main__":
    main()
