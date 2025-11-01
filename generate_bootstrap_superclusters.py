#!/usr/bin/env python3
"""
Generate Bootstrap Superclusters from Complete 2022-23 Archetype Combinations

This script creates superclusters using the complete set of 347 unique lineup combinations
discovered from the 2022-23 season, ensuring 100% coverage and no filtering losses.

Methodology:
1. Load all 347 unique archetype lineup combinations from inventory
2. Create feature vectors for each lineup based on archetype composition
3. Perform k-means clustering (k=6) to create superclusters
4. Validate coverage and save mapping for Bayesian model use

This follows the original paper's approach of clustering lineups by playing style,
but uses archetype composition as features since we don't have their exact metrics.
"""

import json
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from collections import Counter, defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_lineup_combinations(lineups_path='2022_23_lineups.txt'):
    """Load the complete set of lineup combinations from text file."""
    try:
        lineups = []
        with open(lineups_path, 'r') as f:
            for line in f:
                if line.strip():
                    # Parse comma-separated archetype IDs
                    archetype_ids = [int(x.strip()) for x in line.strip().split(',')]
                    lineups.append(tuple(archetype_ids))
        logging.info(f"Loaded {len(lineups)} unique lineup combinations from {lineups_path}")
        return lineups
    except Exception as e:
        logging.error(f"Failed to load lineup combinations: {e}")
        return []

def create_lineup_features(lineups):
    """
    Create feature vectors for each lineup based on archetype composition.

    Since we don't have the original paper's weighted metrics (WFGMPercUAST, etc.),
    we use archetype composition features that capture lineup "style":
    - Archetype frequencies (how many of each archetype)
    - Archetype diversity (number of unique archetypes)
    - Archetype balance (distribution across positions)
    """
    features = []

    for lineup in lineups:
        # Count frequency of each archetype (1-8)
        archetype_counts = Counter(lineup)

        # Create feature vector
        feature_vector = []

        # Archetype frequencies (8 features)
        for archetype_id in range(1, 9):  # 1-8
            feature_vector.append(archetype_counts.get(archetype_id, 0))

        # Diversity score (1 feature: number of unique archetypes)
        unique_archetypes = len(set(lineup))
        feature_vector.append(unique_archetypes)

        # Balance score (1 feature: standard deviation of archetype counts)
        counts = [archetype_counts.get(i, 0) for i in range(1, 9)]
        balance_score = np.std(counts) if counts else 0
        feature_vector.append(balance_score)

        # Archetype concentration (1 feature: max frequency / total players)
        max_count = max(counts) if counts else 0
        concentration = max_count / 5.0  # 5 players total
        feature_vector.append(concentration)

        features.append(feature_vector)

    # Convert to numpy array
    feature_matrix = np.array(features)

    logging.info(f"Created feature matrix: {feature_matrix.shape[0]} lineups × {feature_matrix.shape[1]} features")

    # Log feature statistics
    feature_names = [f'archetype_{i}' for i in range(1, 9)] + ['diversity', 'balance', 'concentration']
    for i, name in enumerate(feature_names):
        values = feature_matrix[:, i]
        logging.info(".3f")

    return feature_matrix, feature_names

def perform_clustering(feature_matrix, n_clusters=6, random_state=42):
    """
    Perform k-means clustering to create superclusters.

    Uses k=6 as per the original paper's methodology.
    """
    logging.info(f"Performing k-means clustering with k={n_clusters}...")

    # Standardize features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(feature_matrix)

    # Perform clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    cluster_labels = kmeans.fit_predict(scaled_features)

    # Analyze cluster sizes
    cluster_sizes = Counter(cluster_labels)
    logging.info(f"Supercluster sizes:")
    for cluster_id in sorted(cluster_sizes.keys()):
        logging.info(f"  Supercluster {cluster_id}: {cluster_sizes[cluster_id]} lineups")

    # Calculate silhouette score (cluster quality)
    from sklearn.metrics import silhouette_score
    silhouette_avg = silhouette_score(scaled_features, cluster_labels)
    logging.info(f"Silhouette Score: {silhouette_avg:.3f} (higher is better)")

    return cluster_labels, kmeans, scaler

def create_supercluster_mapping(lineups, cluster_labels):
    """
    Create mapping from archetype lineup keys to supercluster IDs.
    """
    mapping = {}

    for lineup, cluster_id in zip(lineups, cluster_labels):
        # Create key as sorted archetype string (e.g., "1_2_3_4_5")
        key = '_'.join(map(str, sorted(lineup)))
        mapping[key] = int(cluster_id)

    logging.info(f"Created mapping for {len(mapping)} unique lineup combinations")
    return mapping

def validate_supercluster_coverage(lineups, mapping):
    """
    Validate that all lineup combinations have supercluster assignments.
    """
    coverage_count = 0
    missing = []

    for lineup in lineups:
        key = '_'.join(map(str, sorted(lineup)))
        if key in mapping:
            coverage_count += 1
        else:
            missing.append(key)

    coverage_rate = coverage_count / len(lineups)
    logging.info(f"Supercluster coverage: {coverage_count}/{len(lineups)} ({coverage_rate:.1%})")

    if missing:
        logging.warning(f"Missing mappings for {len(missing)} lineups")
        for key in missing[:5]:  # Show first 5
            logging.warning(f"  Missing: {key}")

    return coverage_rate == 1.0

def analyze_supercluster_characteristics(lineups, cluster_labels, feature_matrix, feature_names):
    """
    Analyze the characteristics of each supercluster to understand playing styles.
    """
    logging.info("\n=== SUPERCLUSTER CHARACTERISTICS ===")

    for cluster_id in range(6):
        # Get lineups in this cluster
        cluster_mask = cluster_labels == cluster_id
        cluster_lineups = [lineups[i] for i in range(len(lineups)) if cluster_mask[i]]
        cluster_features = feature_matrix[cluster_mask]

        if len(cluster_lineups) == 0:
            continue

        logging.info(f"\nSupercluster {cluster_id} ({len(cluster_lineups)} lineups):")

        # Average archetype composition
        avg_composition = np.mean(cluster_features[:, :8], axis=0)  # First 8 features are archetype counts
        logging.info("  Average archetype composition:")
        for i, count in enumerate(avg_composition):
            if count > 0.1:  # Only show archetypes that appear
                logging.info(".2f")

        # Key characteristics
        avg_diversity = np.mean(cluster_features[:, 8])  # diversity feature
        avg_balance = np.mean(cluster_features[:, 9])    # balance feature
        avg_concentration = np.mean(cluster_features[:, 10])  # concentration feature

        logging.info(".2f")
        logging.info(".3f")
        logging.info(".2f")

        # Most common archetype patterns
        archetype_patterns = [tuple(sorted(lineup)) for lineup in cluster_lineups]
        pattern_counts = Counter(archetype_patterns)
        most_common = pattern_counts.most_common(3)
        logging.info("  Most common patterns:")
        for pattern, count in most_common:
            logging.info(f"    {pattern}: {count} lineups")

def save_supercluster_results(mapping, cluster_labels, kmeans_model, scaler, lineups, feature_names, validation_passed):
    """
    Save all supercluster results for use in Bayesian modeling.
    """
    # Create output directory
    import os
    os.makedirs('bootstrap_superclusters', exist_ok=True)

    # Main mapping file (compatible with existing Bayesian prep)
    output_data = {
        'description': 'Bootstrap supercluster assignments from complete 2022-23 archetype combinations',
        'methodology': 'k-means clustering (k=6) on archetype composition features',
        'num_superclusters': 6,
        'num_lineup_combinations': len(mapping),
        'coverage_validation': validation_passed,
        'generated_from': 'complete 2022-23 season inventory (347 unique lineups)',
        'feature_names': feature_names,
        'cluster_sizes': {int(k): int(v) for k, v in Counter(cluster_labels).items()},
        'lineup_assignments': {k: int(v) for k, v in mapping.items()}
    }

    mapping_path = 'bootstrap_superclusters/supercluster_assignments_bootstrap.json'
    with open(mapping_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    logging.info(f"Saved supercluster mapping to {mapping_path}")

    # Save model and scaler for potential future use
    import joblib
    joblib.dump(kmeans_model, 'bootstrap_superclusters/kmeans_model.joblib')
    joblib.dump(scaler, 'bootstrap_superclusters/scaler.joblib')
    logging.info("Saved clustering model and scaler")

    # Save detailed analysis
    analysis_data = {
        'lineup_analysis': {},
        'feature_analysis': {}
    }

    # Analyze each supercluster
    for cluster_id in range(6):
        cluster_mask = cluster_labels == cluster_id
        cluster_lineups = [lineups[i] for i in range(len(lineups)) if cluster_mask[i]]

        if len(cluster_lineups) > 0:
            # Archetype distribution
            all_archetypes = [arch for lineup in cluster_lineups for arch in lineup]
            archetype_dist = Counter(all_archetypes)

            analysis_data['lineup_analysis'][f'supercluster_{cluster_id}'] = {
                'size': len(cluster_lineups),
                'archetype_distribution': dict(archetype_dist),
                'sample_lineups': [list(lineup) for lineup in cluster_lineups[:5]]
            }

    analysis_path = 'bootstrap_superclusters/supercluster_analysis.json'
    with open(analysis_path, 'w') as f:
        json.dump(analysis_data, f, indent=2)
    logging.info(f"Saved detailed analysis to {analysis_path}")

    return mapping_path

def main():
    logging.info("="*80)
    logging.info("GENERATING BOOTSTRAP SUPERCLUSTERS")
    logging.info("="*80)

    # Load complete lineup combinations
    lineups = load_lineup_combinations()
    if not lineups:
        logging.error("No lineup combinations loaded. Run inventory script first.")
        return

    # Create feature vectors
    logging.info("\nCreating lineup feature vectors...")
    feature_matrix, feature_names = create_lineup_features(lineups)

    # Perform clustering
    cluster_labels, kmeans_model, scaler = perform_clustering(feature_matrix)

    # Create mapping
    mapping = create_supercluster_mapping(lineups, cluster_labels)

    # Validate coverage
    coverage_valid = validate_supercluster_coverage(lineups, mapping)

    # Analyze characteristics
    analyze_supercluster_characteristics(lineups, cluster_labels, feature_matrix, feature_names)

    # Save results
    output_path = save_supercluster_results(mapping, cluster_labels, kmeans_model, scaler, lineups, feature_names, coverage_valid)

    # Final summary
    logging.info("\n" + "="*80)
    logging.info("BOOTSTRAP SUPERCLUSTERS COMPLETE")
    logging.info("="*80)

    status = "✅ SUCCESS" if coverage_valid else "⚠️  WARNING"
    logging.info(f"Status: {status}")

    logging.info("\nKey Results:")
    logging.info(f"  - {len(lineups)} unique lineup combinations processed")
    logging.info(f"  - 6 superclusters created")
    logging.info(f"  - 100% coverage validation: {'PASSED' if coverage_valid else 'FAILED'}")
    logging.info(f"  - Mapping saved to: {output_path}")

    if coverage_valid:
        logging.info("\n🎉 Ready for Bayesian model training!")
        logging.info("Next step: Update Bayesian data prep to use bootstrap superclusters")
    else:
        logging.warning("\n⚠️  Coverage issues detected")
        logging.warning("Investigate missing lineup mappings before proceeding")

if __name__ == '__main__':
    main()
