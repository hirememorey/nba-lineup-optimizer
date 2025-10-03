#!/usr/bin/env python3
"""
Validate Clustering with Clean Data

This script validates the player archetype clustering using the cleaned
PlayerArchetypeFeatures data to ensure the clustering produces meaningful
and stable results.

Author: AI Assistant
Date: 2025-10-03
"""

import pandas as pd
import numpy as np
import sqlite3
import logging
from typing import Dict, List, Tuple, Optional, Any
import json
from datetime import datetime
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('clustering_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ClusteringValidator:
    """
    Validates player archetype clustering with clean data.
    """
    
    def __init__(self, db_path: str = "src/nba_stats/db/nba_stats.db"):
        """Initialize the validator with database connection."""
        self.db_path = db_path
        self.conn = None
        
        # Clustering parameters
        self.k_range = range(2, 11)  # Test 2-10 clusters
        self.random_state = 42
        
        logger.info("ClusteringValidator initialized")
    
    def connect_database(self) -> bool:
        """Connect to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            logger.info(f"Connected to database: {self.db_path}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def load_clean_data(self, season: str = "2024-25") -> pd.DataFrame:
        """
        Load clean player data for clustering.
        
        Args:
            season: Season to process
            
        Returns:
            DataFrame with clean player data
        """
        logger.info(f"Loading clean player data for season {season}...")
        
        # Get all data for the season
        df = pd.read_sql_query("""
            SELECT * FROM PlayerArchetypeFeatures 
            WHERE season = ?
        """, self.conn, params=(season,))
        
        if df.empty:
            logger.error(f"No data found for season {season}")
            return df
        
        logger.info(f"Loaded {len(df)} players with clean data")
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Prepare features for clustering.
        
        Args:
            df: Input DataFrame with player data
            
        Returns:
            Tuple of (features_df, feature_names)
        """
        logger.info("Preparing features for clustering...")
        
        # Select relevant features for clustering
        feature_columns = [
            'FTPCT', 'TSPCT', 'THPAr', 'FTr', 'TRBPCT', 'ASTPCT',
            'AVGDIST', 'Zto3r', 'THto10r', 'TENto16r', 'SIXTto3PTr',
            'HEIGHT', 'WINGSPAN', 'FRNTCTTCH', 'TOP',
            'AVGSECPERTCH', 'AVGDRIBPERTCH', 'ELBWTCH',
            'POSTUPS', 'PNTTOUCH', 'DRIVES', 'DRFGA',
            'DRPTSPCT', 'DRPASSPCT', 'DRASTPCT', 'DRTOVPCT',
            'DRPFPCT', 'DRIMFGPCT', 'CSFGA', 'CS3PA',
            'PASSESMADE', 'SECAST', 'POTAST', 'PUFGA', 'PU3PA',
            'PSTUPFGA', 'PSTUPPTSPCT', 'PSTUPPASSPCT', 'PSTUPASTPCT',
            'PSTUPTOVPCT', 'PNTTCHS', 'PNTFGA', 'PNTPTSPCT',
            'PNTPASSPCT', 'PNTASTPCT', 'PNTTVPCT',
            'AVGFGATTEMPTEDAGAINSTPERGAME'
        ]
        
        # Filter to only include columns that exist in the data
        available_features = [col for col in feature_columns if col in df.columns]
        
        # Create features DataFrame
        features_df = df[available_features].copy()
        
        # Handle any remaining missing values
        features_df = features_df.fillna(0)
        
        logger.info(f"Prepared {len(available_features)} features for clustering")
        logger.info(f"Features: {available_features}")
        
        return features_df, available_features
    
    def find_optimal_clusters(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Find the optimal number of clusters using multiple metrics.
        
        Args:
            features_df: Features DataFrame
            
        Returns:
            Dictionary with clustering results
        """
        logger.info("Finding optimal number of clusters...")
        
        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features_df)
        
        # Test different numbers of clusters
        silhouette_scores = []
        calinski_harabasz_scores = []
        inertias = []
        
        for k in self.k_range:
            # Fit KMeans
            kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            cluster_labels = kmeans.fit_predict(features_scaled)
            
            # Calculate metrics
            silhouette_avg = silhouette_score(features_scaled, cluster_labels)
            calinski_harabasz = calinski_harabasz_score(features_scaled, cluster_labels)
            inertia = kmeans.inertia_
            
            silhouette_scores.append(silhouette_avg)
            calinski_harabasz_scores.append(calinski_harabasz)
            inertias.append(inertia)
            
            logger.info(f"k={k}: Silhouette={silhouette_avg:.3f}, "
                       f"Calinski-Harabasz={calinski_harabasz:.3f}, "
                       f"Inertia={inertia:.3f}")
        
        # Find optimal k
        optimal_k_silhouette = self.k_range[np.argmax(silhouette_scores)]
        optimal_k_calinski = self.k_range[np.argmax(calinski_harabasz_scores)]
        
        results = {
            'k_range': list(self.k_range),
            'silhouette_scores': silhouette_scores,
            'calinski_harabasz_scores': calinski_harabasz_scores,
            'inertias': inertias,
            'optimal_k_silhouette': optimal_k_silhouette,
            'optimal_k_calinski': optimal_k_calinski,
            'max_silhouette': max(silhouette_scores),
            'max_calinski_harabasz': max(calinski_harabasz_scores)
        }
        
        logger.info(f"Optimal k (Silhouette): {optimal_k_silhouette}")
        logger.info(f"Optimal k (Calinski-Harabasz): {optimal_k_calinski}")
        
        return results
    
    def perform_final_clustering(self, features_df: pd.DataFrame, k: int = 8) -> Dict[str, Any]:
        """
        Perform final clustering with the optimal number of clusters.
        
        Args:
            features_df: Features DataFrame
            k: Number of clusters
            
        Returns:
            Dictionary with clustering results
        """
        logger.info(f"Performing final clustering with k={k}...")
        
        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features_df)
        
        # Fit final model
        kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
        cluster_labels = kmeans.fit_predict(features_scaled)
        
        # Calculate final metrics
        silhouette_avg = silhouette_score(features_scaled, cluster_labels)
        calinski_harabasz = calinski_harabasz_score(features_scaled, cluster_labels)
        
        # Get cluster centers
        cluster_centers = scaler.inverse_transform(kmeans.cluster_centers_)
        
        # Create cluster analysis
        cluster_analysis = {}
        for i in range(k):
            cluster_mask = cluster_labels == i
            cluster_size = np.sum(cluster_mask)
            
            cluster_analysis[f'cluster_{i}'] = {
                'size': int(cluster_size),
                'percentage': float(cluster_size / len(cluster_labels) * 100),
                'center': cluster_centers[i].tolist()
            }
        
        results = {
            'k': k,
            'silhouette_score': silhouette_avg,
            'calinski_harabasz_score': calinski_harabasz,
            'inertia': kmeans.inertia_,
            'cluster_labels': cluster_labels.tolist(),
            'cluster_centers': cluster_centers.tolist(),
            'cluster_analysis': cluster_analysis,
            'total_players': len(features_df)
        }
        
        logger.info(f"Final clustering completed: {k} clusters, "
                   f"Silhouette={silhouette_avg:.3f}, "
                   f"Calinski-Harabasz={calinski_harabasz:.3f}")
        
        return results
    
    def validate_cluster_stability(self, features_df: pd.DataFrame, k: int = 8, n_runs: int = 10) -> Dict[str, Any]:
        """
        Validate cluster stability by running multiple clustering iterations.
        
        Args:
            features_df: Features DataFrame
            k: Number of clusters
            n_runs: Number of runs for stability test
            
        Returns:
            Dictionary with stability results
        """
        logger.info(f"Validating cluster stability with {n_runs} runs...")
        
        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features_df)
        
        silhouette_scores = []
        calinski_harabasz_scores = []
        
        for run in range(n_runs):
            # Fit KMeans with different random state
            kmeans = KMeans(n_clusters=k, random_state=run, n_init=10)
            cluster_labels = kmeans.fit_predict(features_scaled)
            
            # Calculate metrics
            silhouette_avg = silhouette_score(features_scaled, cluster_labels)
            calinski_harabasz = calinski_harabasz_score(features_scaled, cluster_labels)
            
            silhouette_scores.append(silhouette_avg)
            calinski_harabasz_scores.append(calinski_harabasz)
        
        stability_results = {
            'n_runs': n_runs,
            'silhouette_scores': silhouette_scores,
            'calinski_harabasz_scores': calinski_harabasz_scores,
            'silhouette_mean': np.mean(silhouette_scores),
            'silhouette_std': np.std(silhouette_scores),
            'calinski_harabasz_mean': np.mean(calinski_harabasz_scores),
            'calinski_harabasz_std': np.std(calinski_harabasz_scores),
            'stability_score': 1 - np.std(silhouette_scores) / np.mean(silhouette_scores)
        }
        
        logger.info(f"Stability validation completed: "
                   f"Silhouette mean={stability_results['silhouette_mean']:.3f}±{stability_results['silhouette_std']:.3f}, "
                   f"Stability score={stability_results['stability_score']:.3f}")
        
        return stability_results
    
    def generate_validation_report(self, season: str = "2024-25") -> Dict[str, Any]:
        """
        Generate a comprehensive validation report.
        
        Args:
            season: Season to validate
            
        Returns:
            Dictionary with validation report
        """
        logger.info(f"Generating comprehensive validation report for season {season}...")
        
        if not self.connect_database():
            return {'error': 'Database connection failed'}
        
        try:
            # Load clean data
            df = self.load_clean_data(season)
            if df.empty:
                return {'error': 'No data available'}
            
            # Prepare features
            features_df, feature_names = self.prepare_features(df)
            
            # Find optimal clusters
            optimal_results = self.find_optimal_clusters(features_df)
            
            # Use the optimal k from silhouette score
            optimal_k = optimal_results['optimal_k_silhouette']
            
            # Perform final clustering
            final_results = self.perform_final_clustering(features_df, optimal_k)
            
            # Validate stability
            stability_results = self.validate_cluster_stability(features_df, optimal_k)
            
            # Generate report
            report = {
                'validation_timestamp': datetime.now().isoformat(),
                'season': season,
                'data_summary': {
                    'total_players': len(df),
                    'features_used': len(feature_names),
                    'feature_names': feature_names
                },
                'optimal_clustering': optimal_results,
                'final_clustering': final_results,
                'stability_validation': stability_results,
                'recommendations': self._generate_recommendations(optimal_results, final_results, stability_results)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Validation failed with error: {e}")
            return {'error': str(e)}
        finally:
            if self.conn:
                self.conn.close()
    
    def _generate_recommendations(self, optimal_results: Dict, final_results: Dict, stability_results: Dict) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Check silhouette score
        if final_results['silhouette_score'] > 0.5:
            recommendations.append("✅ Excellent clustering quality (Silhouette > 0.5)")
        elif final_results['silhouette_score'] > 0.3:
            recommendations.append("⚠️ Good clustering quality (Silhouette > 0.3)")
        else:
            recommendations.append("❌ Poor clustering quality (Silhouette < 0.3)")
        
        # Check stability
        if stability_results['stability_score'] > 0.9:
            recommendations.append("✅ Excellent cluster stability")
        elif stability_results['stability_score'] > 0.8:
            recommendations.append("⚠️ Good cluster stability")
        else:
            recommendations.append("❌ Poor cluster stability")
        
        # Check cluster size distribution
        cluster_sizes = [analysis['size'] for analysis in final_results['cluster_analysis'].values()]
        min_size = min(cluster_sizes)
        max_size = max(cluster_sizes)
        
        if min_size > 10:
            recommendations.append("✅ All clusters have sufficient size (>10 players)")
        else:
            recommendations.append("⚠️ Some clusters are too small (<10 players)")
        
        if max_size / min_size < 5:
            recommendations.append("✅ Good cluster size balance")
        else:
            recommendations.append("⚠️ Unbalanced cluster sizes")
        
        return recommendations

def main():
    """Run the clustering validation."""
    logger.info("Starting clustering validation with clean data...")
    
    validator = ClusteringValidator()
    report = validator.generate_validation_report("2024-25")
    
    if 'error' in report:
        print(f"\n❌ Validation failed: {report['error']}")
    else:
        print("\n✅ Clustering validation completed successfully!")
        print(f"Optimal clusters: {report['final_clustering']['k']}")
        print(f"Silhouette score: {report['final_clustering']['silhouette_score']:.3f}")
        print(f"Stability score: {report['stability_validation']['stability_score']:.3f}")
        
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  {rec}")
        
        # Save report
        report_file = f"clustering_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\nDetailed report saved to: {report_file}")

if __name__ == "__main__":
    main()
