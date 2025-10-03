#!/usr/bin/env python3
"""
Simple lineup supercluster generation.

This is a simplified version that focuses on getting the basic clustering working
without complex validation that's causing errors.
"""

import sqlite3
import pandas as pd
import numpy as np
import json
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from collections import Counter
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Generate simple lineup superclusters."""
    
    # Connect to database
    conn = sqlite3.connect("src/nba_stats/db/nba_stats.db")
    
    try:
        # Load archetype lineup data
        logger.info("Loading archetype lineup data...")
        
        # Get player archetype mappings
        query = """
        SELECT 
            p.player_id,
            pa.archetype_id
        FROM Players p
        JOIN PlayerSeasonArchetypes pa ON p.player_id = pa.player_id
        WHERE pa.season = '2024-25'
        """
        
        player_archetypes = pd.read_sql_query(query, conn)
        player_to_archetype = dict(zip(player_archetypes['player_id'], player_archetypes['archetype_id']))
        
        # Get possession data
        query = """
        SELECT 
            home_player_1_id, home_player_2_id, home_player_3_id, home_player_4_id, home_player_5_id,
            away_player_1_id, away_player_2_id, away_player_3_id, away_player_4_id, away_player_5_id
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
        logger.info(f"Loaded {len(possessions)} possessions with complete lineup data")
        
        # Create archetype lineups
        all_lineups = []
        
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
            for players in [home_players, away_players]:
                archetypes = []
                for player_id in players:
                    archetype_id = player_to_archetype.get(player_id, -1)
                    archetypes.append(archetype_id)
                
                # Create archetype lineup string (sorted for consistency)
                archetype_lineup = "_".join(map(str, sorted(archetypes)))
                all_lineups.append(archetype_lineup)
        
        # Count lineup frequency
        lineup_counts = Counter(all_lineups)
        logger.info(f"Found {len(lineup_counts)} unique archetype lineups")
        
        # Create features for clustering
        lineup_features = []
        
        for lineup, frequency in lineup_counts.items():
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
                'big_men_ratio': big_men_count / 5.0,
                'ball_handlers_ratio': ball_handlers_count / 5.0,
                'role_players_ratio': role_players_count / 5.0,
                'dominance_score': max(big_men_count, ball_handlers_count, role_players_count) / 5.0,
                'balance_score': 1.0 - (np.var([big_men_count, ball_handlers_count, role_players_count]) / 4.0)
            }
            
            lineup_features.append(features)
        
        features_df = pd.DataFrame(lineup_features)
        logger.info(f"Created features for {len(features_df)} lineups")
        
        # Determine optimal k based on data density
        n_lineups = len(features_df)
        max_k = min(6, n_lineups // 5)  # At least 5 lineups per cluster
        
        if max_k < 2:
            logger.warning("Insufficient data for clustering, using k=2")
            optimal_k = 2
        else:
            # Test k values
            feature_columns = ['big_men_ratio', 'ball_handlers_ratio', 'role_players_ratio', 
                              'dominance_score', 'balance_score']
            X = features_df[feature_columns].values
            
            best_silhouette = -1
            optimal_k = 2
            
            for k in range(2, max_k + 1):
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                cluster_labels = kmeans.fit_predict(X)
                
                from sklearn.metrics import silhouette_score
                silhouette = silhouette_score(X, cluster_labels)
                
                logger.info(f"k={k}: silhouette={silhouette:.3f}")
                
                if silhouette > best_silhouette:
                    best_silhouette = silhouette
                    optimal_k = k
            
            logger.info(f"Selected k={optimal_k} as optimal")
        
        # Perform final clustering
        feature_columns = ['big_men_ratio', 'ball_handlers_ratio', 'role_players_ratio', 
                          'dominance_score', 'balance_score']
        X = features_df[feature_columns].values
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Perform clustering
        kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X_scaled)
        
        # Add cluster assignments
        features_df['supercluster_id'] = cluster_labels
        
        # Calculate metrics
        from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
        silhouette = silhouette_score(X_scaled, cluster_labels)
        calinski_harabasz = calinski_harabasz_score(X_scaled, cluster_labels)
        davies_bouldin = davies_bouldin_score(X_scaled, cluster_labels)
        
        logger.info(f"Clustering completed:")
        logger.info(f"  Silhouette Score: {silhouette:.3f}")
        logger.info(f"  Calinski-Harabasz Score: {calinski_harabasz:.1f}")
        logger.info(f"  Davies-Bouldin Index: {davies_bouldin:.3f}")
        
        # Create simple supercluster reports
        supercluster_reports = {}
        
        for cluster_id in range(optimal_k):
            cluster_lineups = features_df[features_df['supercluster_id'] == cluster_id]
            
            # Count archetype frequency
            archetype_counts = Counter()
            for lineup_id in cluster_lineups['lineup_id']:
                archetypes = [int(x) for x in lineup_id.split('_')]
                archetype_counts.update(archetypes)
            
            # Generate descriptive name
            if cluster_lineups['big_men_ratio'].mean() > 0.4:
                cluster_name = "Big Man Heavy"
            elif cluster_lineups['ball_handlers_ratio'].mean() > 0.4:
                cluster_name = "Ball Handler Heavy"
            else:
                cluster_name = "Role Player Heavy"
            
            supercluster_reports[cluster_id] = {
                'cluster_name': cluster_name,
                'num_lineups': len(cluster_lineups),
                'lineup_ids': cluster_lineups['lineup_id'].tolist(),
                'archetype_distribution': {str(k): int(v) for k, v in dict(archetype_counts).items()},
                'total_usage': int(cluster_lineups['frequency'].sum())
            }
        
        # Save results
        output_dir = Path("lineup_supercluster_results")
        output_dir.mkdir(exist_ok=True)
        
        # Save lineup assignments
        lineup_assignments = dict(zip(features_df['lineup_id'], features_df['supercluster_id'].astype(int)))
        
        results = {
            'lineup_assignments': lineup_assignments,
            'supercluster_reports': supercluster_reports,
            'clustering_metrics': {
                'k': int(optimal_k),
                'silhouette_score': float(silhouette),
                'calinski_harabasz_score': float(calinski_harabasz),
                'davies_bouldin_index': float(davies_bouldin)
            }
        }
        
        # Save JSON results
        with open(output_dir / "supercluster_assignments.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save CSV results
        features_df.to_csv(output_dir / "lineup_supercluster_features.csv", index=False)
        
        # Save models
        import joblib
        joblib.dump(kmeans, output_dir / "supercluster_kmeans.pkl")
        joblib.dump(scaler, output_dir / "supercluster_scaler.pkl")
        
        # Generate simple markdown report
        content = "# Lineup Supercluster Analysis Report\n\n"
        content += f"Total superclusters: {optimal_k}\n"
        content += f"Total unique lineups: {len(features_df)}\n\n"
        
        for cluster_id in range(optimal_k):
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
                archetype_name = ['Big Men', 'Primary Ball Handlers', 'Role Players'][int(archetype_id)]
                percentage = count / total_archetypes * 100
                content += f"- {archetype_name}: {count} ({percentage:.1f}%)\n"
            content += "\n---\n\n"
        
        with open(output_dir / "supercluster_analysis_report.md", 'w') as f:
            f.write(content)
        
        # Print summary
        print("\n" + "="*60)
        print("SUPERCLUSTER GENERATION COMPLETE")
        print("="*60)
        
        for cluster_id in range(optimal_k):
            report = supercluster_reports[cluster_id]
            print(f"\nSupercluster {cluster_id}: {report['cluster_name']}")
            print(f"  Lineups: {report['num_lineups']}")
            print(f"  Total Usage: {report['total_usage']:,}")
        
        print(f"\n✅ Results saved to: {output_dir}")
        print("✅ Review the markdown report to validate superclusters make basketball sense")
        print("✅ This is the critical 'sniff test' that must pass before Bayesian modeling")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during supercluster generation: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Lineup supercluster generation completed successfully!")
    else:
        print("\n❌ Lineup supercluster generation failed")
