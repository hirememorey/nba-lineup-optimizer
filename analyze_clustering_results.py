#!/usr/bin/env python3
"""
Analyze Clustering Results

This script performs a detailed analysis of the clustering results to understand
why we're getting poor silhouette scores and unbalanced clusters.

Author: AI Assistant
Date: 2025-10-03
"""

import pandas as pd
import numpy as np
import sqlite3
import json
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

def load_data():
    """Load the player data."""
    conn = sqlite3.connect("src/nba_stats/db/nba_stats.db")
    
    # Get player data with names for analysis
    df = pd.read_sql_query("""
        SELECT paf.*, p.player_name
        FROM PlayerArchetypeFeatures paf
        JOIN Players p ON paf.player_id = p.player_id
        WHERE paf.season = '2024-25'
    """, conn)
    
    conn.close()
    return df

def analyze_data_distribution(df):
    """Analyze the distribution of features to understand the data better."""
    print("=== DATA DISTRIBUTION ANALYSIS ===")
    
    # Select numeric features
    numeric_features = df.select_dtypes(include=[np.number]).columns
    numeric_features = [col for col in numeric_features if col not in ['player_id', 'season']]
    
    print(f"Number of features: {len(numeric_features)}")
    print(f"Number of players: {len(df)}")
    
    # Check for features with low variance
    feature_vars = df[numeric_features].var()
    low_var_features = feature_vars[feature_vars < 0.01].index.tolist()
    print(f"Features with very low variance (< 0.01): {len(low_var_features)}")
    if low_var_features:
        print(f"Low variance features: {low_var_features[:10]}...")  # Show first 10
    
    # Check for highly correlated features
    corr_matrix = df[numeric_features].corr().abs()
    high_corr_pairs = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            if corr_matrix.iloc[i, j] > 0.9:
                high_corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_matrix.iloc[i, j]))
    
    print(f"Highly correlated feature pairs (>0.9): {len(high_corr_pairs)}")
    if high_corr_pairs:
        print("Top correlated pairs:")
        for pair in high_corr_pairs[:5]:
            print(f"  {pair[0]} - {pair[1]}: {pair[2]:.3f}")
    
    return numeric_features, low_var_features, high_corr_pairs

def try_different_approaches(df, numeric_features):
    """Try different clustering approaches to see which works best."""
    print("\n=== TRYING DIFFERENT CLUSTERING APPROACHES ===")
    
    # Prepare data
    X = df[numeric_features].fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    approaches = {
        'Raw Features': X_scaled,
        'PCA (95% variance)': None,
        'PCA (80% variance)': None,
        'PCA (99% variance)': None
    }
    
    # Apply PCA with different variance thresholds
    pca_95 = PCA(n_components=0.95)
    approaches['PCA (95% variance)'] = pca_95.fit_transform(X_scaled)
    
    pca_80 = PCA(n_components=0.80)
    approaches['PCA (80% variance)'] = pca_80.fit_transform(X_scaled)
    
    pca_99 = PCA(n_components=0.99)
    approaches['PCA (99% variance)'] = pca_99.fit_transform(X_scaled)
    
    print(f"PCA (95%): {approaches['PCA (95% variance)'].shape[1]} components")
    print(f"PCA (80%): {approaches['PCA (80% variance)'].shape[1]} components")
    print(f"PCA (99%): {approaches['PCA (99% variance)'].shape[1]} components")
    
    # Test different k values for each approach
    k_values = [3, 4, 5, 6, 7, 8, 9, 10]
    results = {}
    
    for approach_name, X_processed in approaches.items():
        print(f"\n--- {approach_name} ---")
        results[approach_name] = {}
        
        for k in k_values:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X_processed)
            
            # Calculate silhouette score
            silhouette = silhouette_score(X_processed, labels)
            
            # Calculate cluster balance
            cluster_sizes = np.bincount(labels)
            min_size = cluster_sizes.min()
            max_size = cluster_sizes.max()
            balance_ratio = min_size / max_size if max_size > 0 else 0
            
            results[approach_name][k] = {
                'silhouette': silhouette,
                'min_size': min_size,
                'max_size': max_size,
                'balance_ratio': balance_ratio,
                'cluster_sizes': cluster_sizes.tolist()
            }
            
            print(f"  k={k}: Silhouette={silhouette:.3f}, Balance={balance_ratio:.3f}, Sizes={cluster_sizes}")
    
    return results

def find_best_approach(results):
    """Find the best approach based on silhouette score and cluster balance."""
    print("\n=== FINDING BEST APPROACH ===")
    
    best_score = -1
    best_approach = None
    best_k = None
    
    for approach_name, approach_results in results.items():
        for k, metrics in approach_results.items():
            # Weighted score: silhouette (70%) + balance (30%)
            weighted_score = 0.7 * metrics['silhouette'] + 0.3 * metrics['balance_ratio']
            
            if weighted_score > best_score:
                best_score = weighted_score
                best_approach = approach_name
                best_k = k
    
    print(f"Best approach: {best_approach} with k={best_k}")
    print(f"Weighted score: {best_score:.3f}")
    print(f"Silhouette: {results[best_approach][best_k]['silhouette']:.3f}")
    print(f"Balance ratio: {results[best_approach][best_k]['balance_ratio']:.3f}")
    print(f"Cluster sizes: {results[best_approach][best_k]['cluster_sizes']}")
    
    return best_approach, best_k, results[best_approach][best_k]

def analyze_archetype_interpretability(df, numeric_features, best_approach, best_k, results):
    """Analyze the interpretability of the best clustering approach."""
    print(f"\n=== ANALYZING ARCHETYPE INTERPRETABILITY ===")
    
    # Prepare data the same way as the best approach
    X = df[numeric_features].fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    if 'PCA' in best_approach:
        if '95%' in best_approach:
            pca = PCA(n_components=0.95)
        elif '80%' in best_approach:
            pca = PCA(n_components=0.80)
        else:  # 99%
            pca = PCA(n_components=0.99)
        X_processed = pca.fit_transform(X_scaled)
    else:
        X_processed = X_scaled
    
    # Perform final clustering
    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_processed)
    
    # Add cluster labels to dataframe
    df_with_clusters = df.copy()
    df_with_clusters['cluster'] = labels
    
    # Analyze each cluster
    print(f"\nCluster Analysis for k={best_k}:")
    for cluster_id in range(best_k):
        cluster_data = df_with_clusters[df_with_clusters['cluster'] == cluster_id]
        print(f"\n--- Cluster {cluster_id} ({len(cluster_data)} players) ---")
        
        # Show top 10 players in this cluster
        print("Top 10 players in this cluster:")
        for i, (_, player) in enumerate(cluster_data.head(10).iterrows()):
            print(f"  {i+1}. {player['player_name']}")
        
        # Analyze feature means for this cluster
        cluster_means = cluster_data[numeric_features].mean()
        top_features = cluster_means.nlargest(5)
        bottom_features = cluster_means.nsmallest(5)
        
        print("Top 5 features (highest means):")
        for feature, value in top_features.items():
            print(f"  {feature}: {value:.3f}")
        
        print("Bottom 5 features (lowest means):")
        for feature, value in bottom_features.items():
            print(f"  {feature}: {value:.3f}")

def main():
    """Main analysis function."""
    print("Starting detailed clustering analysis...")
    
    # Load data
    df = load_data()
    print(f"Loaded {len(df)} players")
    
    # Analyze data distribution
    numeric_features, low_var_features, high_corr_pairs = analyze_data_distribution(df)
    
    # Try different approaches
    results = try_different_approaches(df, numeric_features)
    
    # Find best approach
    best_approach, best_k, best_metrics = find_best_approach(results)
    
    # Analyze interpretability
    analyze_archetype_interpretability(df, numeric_features, best_approach, best_k, results)
    
    # Save results
    analysis_results = {
        'best_approach': best_approach,
        'best_k': best_k,
        'best_metrics': best_metrics,
        'all_results': results,
        'data_issues': {
            'low_var_features': low_var_features,
            'high_corr_pairs': high_corr_pairs[:10]  # Save first 10
        }
    }
    
    with open('clustering_analysis_detailed.json', 'w') as f:
        json.dump(analysis_results, f, indent=2, default=str)
    
    print(f"\nDetailed analysis saved to: clustering_analysis_detailed.json")

if __name__ == "__main__":
    main()
