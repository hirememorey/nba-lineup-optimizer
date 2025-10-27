#!/usr/bin/env python3
"""
Train Multi-Season Supercluster Model for Semantic Stability

This script trains a K-Means model on pooled historical lineup features (2018-19, 2020-21, 2021-22)
to create a semantically stable supercluster definition that can be consistently applied
across all seasons, avoiding the data drift issue identified in the pre-mortem.

This completes Phase 0: Create a semantically stable supercluster model.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import RobustScaler
from sklearn.cluster import KMeans
import joblib
import json
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def train_multi_season_superclusters(
    features_path="historical_lineup_features/historical_lineup_features.csv",
    output_dir="trained_models",
    scaler_path="trained_models/multi_season_robust_scaler.joblib",
    kmeans_path="trained_models/multi_season_kmeans_model.joblib",
    num_clusters=6,
    random_state=42
):
    """
    Train K-Means model on pooled historical lineup features.

    Args:
        features_path: Path to the historical lineup features CSV
        output_dir: Directory to save trained models
        scaler_path: Path to save the trained RobustScaler
        kmeans_path: Path to save the trained KMeans model
        num_clusters: Number of superclusters (k value)
        random_state: Random state for reproducibility
    """
    logging.info("="*80)
    logging.info("TRAINING MULTI-SEASON SUPERCLUSTER MODEL")
    logging.info("="*80)

    # Load historical lineup features
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Historical features not found at {features_path}")

    df = pd.read_csv(features_path)
    logging.info(f"Loaded {len(df)} historical lineup features")

    # Select clustering features (same as original approach)
    clustering_features = [
        'w_pct', 'plus_minus', 'off_rating', 'pace',
        'ast_pct', 'ast_to',
        'pct_fga_2pt', 'pct_fga_3pt',
        'pct_pts_2pt', 'pct_pts_2pt_mr', 'pct_pts_3pt',
        'pct_pts_ft', 'pct_pts_off_tov', 'pct_pts_paint'
    ]

    available_features = [f for f in clustering_features if f in df.columns]
    logging.info(f"Using {len(available_features)} features for clustering: {available_features}")

    if len(available_features) < len(clustering_features):
        missing = [f for f in clustering_features if f not in df.columns]
        logging.warning(f"Missing features: {missing}")

    # Extract feature matrix
    X = df[available_features].values

    # Handle any missing values
    if np.any(np.isnan(X)):
        logging.warning("Found NaN values in features, filling with 0")
        X = np.nan_to_num(X, nan=0.0)

    logging.info(f"Feature matrix shape: {X.shape}")

    # Apply RobustScaler (same as original approach)
    logging.info("Applying RobustScaler to handle outliers...")
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X)

    # Save the scaler
    os.makedirs(output_dir, exist_ok=True)
    joblib.dump(scaler, scaler_path)
    logging.info(f"RobustScaler saved to {scaler_path}")

    # Train K-Means model
    logging.info(f"Training K-Means model with k={num_clusters}...")
    kmeans = KMeans(
        n_clusters=num_clusters,
        random_state=random_state,
        n_init=10,
        max_iter=300
    )

    # Fit the model
    clusters = kmeans.fit_predict(X_scaled)

    # Save the trained model
    joblib.dump(kmeans, kmeans_path)
    logging.info(f"K-Means model saved to {kmeans_path}")

    # Add cluster assignments to dataframe
    df_with_clusters = df.copy()
    df_with_clusters['supercluster_id'] = clusters

    # Analyze cluster distribution
    cluster_counts = df_with_clusters['supercluster_id'].value_counts().sort_index()
    logging.info(f"\nCluster distribution:")
    for cluster_id in range(num_clusters):
        count = cluster_counts.get(cluster_id, 0)
        pct = (count / len(df_with_clusters)) * 100
        logging.info(f"  Supercluster {cluster_id}: {count} lineups ({pct:.1f}%)")

    # Analyze cluster characteristics
    logging.info(f"\nCluster characteristics (mean values):")
    cluster_means = df_with_clusters.groupby('supercluster_id')[available_features].mean()

    for cluster_id in range(num_clusters):
        logging.info(f"\nSupercluster {cluster_id} (n={cluster_counts.get(cluster_id, 0)}):")
        means = cluster_means.loc[cluster_id]
        for feature in available_features:
            logging.info(f"  {feature}: {means[feature]:.3f}")

    # Save enhanced features with clusters
    cluster_features_path = "historical_lineup_features/historical_lineup_features_with_clusters.csv"
    df_with_clusters.to_csv(cluster_features_path, index=False)
    logging.info(f"Features with cluster assignments saved to {cluster_features_path}")

    # Create supercluster assignment map (similar to existing approach)
    logging.info(f"\nCreating supercluster assignment map...")

    # Group by archetype lineup and take the most common supercluster
    lineup_to_cluster = {}
    for lineup_key, group in df_with_clusters.groupby('archetype_lineup'):
        most_common_cluster = group['supercluster_id'].mode().iloc[0]
        lineup_to_cluster[lineup_key] = int(most_common_cluster)

    # Save assignment map
    assignment_map = {
        'description': 'Multi-season supercluster assignments trained on pooled historical data (2018-19, 2020-21, 2021-22)',
        'num_superclusters': num_clusters,
        'num_lineup_combinations': len(lineup_to_cluster),
        'training_seasons': ['2018-19', '2020-21', '2021-22'],
        'features_used': available_features,
        'lineup_assignments': lineup_to_cluster
    }

    assignment_map_path = "historical_lineup_features/multi_season_supercluster_assignments.json"
    with open(assignment_map_path, 'w') as f:
        json.dump(assignment_map, f, indent=2)

    logging.info(f"Assignment map saved to {assignment_map_path}")

    # Validation: Check that we have good separation between clusters
    logging.info(f"\nValidating cluster separation...")

    # Calculate silhouette score as a measure of cluster quality
    from sklearn.metrics import silhouette_score
    if len(df_with_clusters) > num_clusters:
        silhouette_avg = silhouette_score(X_scaled, clusters)
        logging.info(f"Silhouette Score: {silhouette_avg:.3f}")
        logging.info("(Higher values indicate better cluster separation)")

    return {
        'num_lineups': len(df_with_clusters),
        'num_clusters': num_clusters,
        'silhouette_score': silhouette_avg if len(df_with_clusters) > num_clusters else None,
        'cluster_distribution': cluster_counts.to_dict(),
        'features_used': available_features,
        'scaler_path': scaler_path,
        'kmeans_path': kmeans_path,
        'assignment_map_path': assignment_map_path
    }

def main():
    """Main execution function."""
    try:
        results = train_multi_season_superclusters()

        logging.info("\n" + "="*80)
        logging.info("✅ MULTI-SEASON SUPERCLUSTER MODEL TRAINING COMPLETE")
        logging.info("="*80)

        logging.info(f"Training Results:")
        logging.info(f"  - Lineups processed: {results['num_lineups']:,}")
        logging.info(f"  - Superclusters created: {results['num_clusters']}")
        logging.info(f"  - Features used: {len(results['features_used'])}")
        if results['silhouette_score'] is not None:
            logging.info(f"  - Cluster quality (silhouette): {results['silhouette_score']:.3f}")

        logging.info(f"\nModel files saved:")
        logging.info(f"  - RobustScaler: {results['scaler_path']}")
        logging.info(f"  - K-Means model: {results['kmeans_path']}")
        logging.info(f"  - Assignment map: {results['assignment_map_path']}")

        logging.info(f"\n📋 Next Steps:")
        logging.info(f"  1. Update matchup-specific data prep to use this new model")
        logging.info(f"  2. Retrain Bayesian model with matchup-specific parameters")
        logging.info(f"  3. Validate improved predictive performance")

        logging.info(f"\n🎯 Phase 0 Complete: Semantically stable supercluster model ready!")

    except Exception as e:
        logging.error(f"Training failed: {e}")
        raise

if __name__ == '__main__':
    main()
