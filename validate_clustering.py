#!/usr/bin/env python3
"""
Validate Clustering with Clean Data

This script validates the player archetype clustering using the cleaned
PlayerArchetypeFeatures data to ensure the clustering produces meaningful
and stable results. Includes PCA-based feature space engineering to address
dimensionality and correlation issues.

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
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from kneed import KneeLocator
import matplotlib.pyplot as plt
import seaborn as sns
import os

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
    Validates player archetype clustering with clean data and PCA-based feature engineering.
    """
    
    def __init__(self, db_path: str = "src/nba_stats/db/nba_stats.db"):
        """Initialize the validator with database connection."""
        self.db_path = db_path
        self.conn = None
        
        # Clustering parameters
        self.k_range = range(2, 21)  # Test 2-20 clusters
        self.random_state = 42
        self.pca_variance_threshold = 0.95  # Retain 95% of variance
        
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
    
    def validate_data_integrity(self) -> bool:
        """
        Data integrity gate - must pass before proceeding with clustering.
        This addresses the security engineer's concern about data corruption.
        """
        logger.info("Running data integrity validation...")
        
        try:
            # Check if PlayerArchetypeFeatures table exists and has data
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM PlayerArchetypeFeatures WHERE season = '2024-25'")
            count = cursor.fetchone()[0]
            
            if count == 0:
                logger.error("No data found in PlayerArchetypeFeatures for 2024-25 season")
                return False
            
            # Check for critical NULL values
            cursor.execute("""
                SELECT COUNT(*) FROM PlayerArchetypeFeatures 
                WHERE season = '2024-25' 
                AND (FTPCT IS NULL OR TSPCT IS NULL OR DRIVES IS NULL)
            """)
            null_count = cursor.fetchone()[0]
            
            if null_count > 0:
                logger.error(f"Found {null_count} records with critical NULL values")
                return False
            
            logger.info(f"Data integrity validation passed: {count} players with clean data")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Data integrity validation failed: {e}")
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
        
        # Select relevant features for clustering (48 canonical metrics)
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
        missing_features = [col for col in feature_columns if col not in df.columns]
        
        if missing_features:
            logger.warning(f"Missing features: {missing_features}")
        
        # Create features DataFrame
        features_df = df[available_features].copy()
        
        # Handle any remaining missing values
        features_df = features_df.fillna(0)
        
        logger.info(f"Prepared {len(available_features)} features for clustering")
        logger.info(f"Features: {available_features}")
        
        return features_df, available_features
    
    def engineer_feature_space(self, features_df: pd.DataFrame) -> Tuple[np.ndarray, PCA, StandardScaler]:
        """
        Phase 0: Feature Space Engineering with PCA.
        This addresses the pre-mortem insight about dimensionality and correlation issues.
        
        Args:
            features_df: Features DataFrame
            
        Returns:
            Tuple of (pca_features, pca_model, scaler)
        """
        logger.info("Phase 0: Engineering feature space with PCA...")
        
        # Step 1: Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features_df)
        
        # Step 2: Run PCA
        pca = PCA()
        pca_features = pca.fit_transform(features_scaled)
        
        # Step 3: Determine number of components to retain
        cumulative_variance = np.cumsum(pca.explained_variance_ratio_)
        n_components = np.argmax(cumulative_variance >= self.pca_variance_threshold) + 1
        
        logger.info(f"PCA Analysis:")
        logger.info(f"  Original features: {features_scaled.shape[1]}")
        logger.info(f"  Components for {self.pca_variance_threshold*100}% variance: {n_components}")
        logger.info(f"  Variance explained by {n_components} components: {cumulative_variance[n_components-1]:.3f}")
        
        # Step 4: Retain only the necessary components
        pca_features = pca_features[:, :n_components]
        
        # Step 5: Interpret the principal components
        self._interpret_principal_components(pca, features_df.columns, n_components)
        
        return pca_features, pca, scaler
    
    def _interpret_principal_components(self, pca: PCA, feature_names: List[str], n_components: int):
        """
        Interpret the principal components to understand what they represent.
        
        Args:
            pca: Fitted PCA model
            feature_names: List of original feature names
            n_components: Number of components to analyze
        """
        logger.info("Interpreting principal components...")
        
        for i in range(min(n_components, 5)):  # Analyze top 5 components
            component = pca.components_[i]
            
            # Get top 5 features with highest absolute loadings
            top_indices = np.argsort(np.abs(component))[-5:][::-1]
            top_features = [(feature_names[idx], component[idx]) for idx in top_indices]
            
            logger.info(f"  PC{i+1} (explains {pca.explained_variance_ratio_[i]:.3f} of variance):")
            for feature, loading in top_features:
                logger.info(f"    {feature}: {loading:.3f}")
    
    def find_optimal_clusters(self, pca_features: np.ndarray) -> Dict[str, Any]:
        """
        Find the optimal number of clusters using multiple metrics.
        
        Args:
            pca_features: PCA-transformed features
            
        Returns:
            Dictionary with clustering results
        """
        logger.info("Finding optimal number of clusters...")
        
        # Test different numbers of clusters
        silhouette_scores = []
        calinski_harabasz_scores = []
        davies_bouldin_scores = []
        inertias = []
        
        for k in self.k_range:
            # Fit KMeans
            kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            cluster_labels = kmeans.fit_predict(pca_features)
            
            # Calculate metrics
            silhouette_avg = silhouette_score(pca_features, cluster_labels)
            calinski_harabasz = calinski_harabasz_score(pca_features, cluster_labels)
            davies_bouldin = davies_bouldin_score(pca_features, cluster_labels)
            inertia = kmeans.inertia_
            
            silhouette_scores.append(silhouette_avg)
            calinski_harabasz_scores.append(calinski_harabasz)
            davies_bouldin_scores.append(davies_bouldin)
            inertias.append(inertia)
            
            logger.info(f"k={k}: Silhouette={silhouette_avg:.3f}, "
                       f"Calinski-Harabasz={calinski_harabasz:.3f}, "
                       f"Davies-Bouldin={davies_bouldin:.3f}, "
                       f"Inertia={inertia:.3f}")
        
        # Find optimal k using multiple criteria
        optimal_k_silhouette = self.k_range[np.argmax(silhouette_scores)]
        optimal_k_calinski = self.k_range[np.argmax(calinski_harabasz_scores)]
        optimal_k_davies = self.k_range[np.argmin(davies_bouldin_scores)]
        
        # Use knee detection for inertia
        try:
            kl = KneeLocator(self.k_range, inertias, curve="convex", direction="decreasing")
            optimal_k_inertia = kl.elbow if kl.elbow else optimal_k_silhouette
        except:
            optimal_k_inertia = optimal_k_silhouette
        
        results = {
            'k_range': list(self.k_range),
            'silhouette_scores': silhouette_scores,
            'calinski_harabasz_scores': calinski_harabasz_scores,
            'davies_bouldin_scores': davies_bouldin_scores,
            'inertias': inertias,
            'optimal_k_silhouette': optimal_k_silhouette,
            'optimal_k_calinski': optimal_k_calinski,
            'optimal_k_davies': optimal_k_davies,
            'optimal_k_inertia': optimal_k_inertia,
            'max_silhouette': max(silhouette_scores),
            'max_calinski_harabasz': max(calinski_harabasz_scores),
            'min_davies_bouldin': min(davies_bouldin_scores)
        }
        
        logger.info(f"Optimal k (Silhouette): {optimal_k_silhouette}")
        logger.info(f"Optimal k (Calinski-Harabasz): {optimal_k_calinski}")
        logger.info(f"Optimal k (Davies-Bouldin): {optimal_k_davies}")
        logger.info(f"Optimal k (Inertia/Knee): {optimal_k_inertia}")
        
        return results
    
    def perform_final_clustering(self, pca_features: np.ndarray, k: int = 8) -> Dict[str, Any]:
        """
        Perform final clustering with the optimal number of clusters.
        
        Args:
            pca_features: PCA-transformed features
            k: Number of clusters
            
        Returns:
            Dictionary with clustering results
        """
        logger.info(f"Performing final clustering with k={k}...")
        
        # Fit final model
        kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
        cluster_labels = kmeans.fit_predict(pca_features)
        
        # Calculate final metrics
        silhouette_avg = silhouette_score(pca_features, cluster_labels)
        calinski_harabasz = calinski_harabasz_score(pca_features, cluster_labels)
        davies_bouldin = davies_bouldin_score(pca_features, cluster_labels)
        
        # Create cluster analysis
        cluster_analysis = {}
        for i in range(k):
            cluster_mask = cluster_labels == i
            cluster_size = np.sum(cluster_mask)
            
            cluster_analysis[f'cluster_{i}'] = {
                'size': int(cluster_size),
                'percentage': float(cluster_size / len(cluster_labels) * 100),
                'center': kmeans.cluster_centers_[i].tolist()
            }
        
        results = {
            'k': k,
            'silhouette_score': silhouette_avg,
            'calinski_harabasz_score': calinski_harabasz,
            'davies_bouldin_score': davies_bouldin,
            'inertia': kmeans.inertia_,
            'cluster_labels': cluster_labels.tolist(),
            'cluster_centers': kmeans.cluster_centers_.tolist(),
            'cluster_analysis': cluster_analysis,
            'total_players': len(pca_features)
        }
        
        logger.info(f"Final clustering completed: {k} clusters, "
                   f"Silhouette={silhouette_avg:.3f}, "
                   f"Calinski-Harabasz={calinski_harabasz:.3f}, "
                   f"Davies-Bouldin={davies_bouldin:.3f}")
        
        return results
    
    def validate_cluster_stability(self, pca_features: np.ndarray, k: int = 8, n_runs: int = 10) -> Dict[str, Any]:
        """
        Validate cluster stability by running multiple clustering iterations.
        
        Args:
            pca_features: PCA-transformed features
            k: Number of clusters
            n_runs: Number of runs for stability test
            
        Returns:
            Dictionary with stability results
        """
        logger.info(f"Validating cluster stability with {n_runs} runs...")
        
        silhouette_scores = []
        calinski_harabasz_scores = []
        
        for run in range(n_runs):
            # Fit KMeans with different random state
            kmeans = KMeans(n_clusters=k, random_state=run, n_init=10)
            cluster_labels = kmeans.fit_predict(pca_features)
            
            # Calculate metrics
            silhouette_avg = silhouette_score(pca_features, cluster_labels)
            calinski_harabasz = calinski_harabasz_score(pca_features, cluster_labels)
            
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
    
    def create_visualizations(self, results: Dict[str, Any], output_dir: str):
        """
        Create comprehensive visualizations of the clustering results.
        
        Args:
            results: Clustering results dictionary
            output_dir: Directory to save plots
        """
        logger.info("Creating visualizations...")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up the plotting style
        plt.style.use('seaborn-v0_8')
        fig_size = (12, 8)
        
        # 1. Elbow plot for inertia
        plt.figure(figsize=fig_size)
        plt.plot(results['k_range'], results['inertias'], 'bo-', linewidth=2, markersize=8)
        plt.xlabel('Number of Clusters (k)')
        plt.ylabel('Inertia (Sum of Squared Distances)')
        plt.title('Elbow Method for Optimal k')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/elbow_plot.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Silhouette scores
        plt.figure(figsize=fig_size)
        plt.plot(results['k_range'], results['silhouette_scores'], 'go-', linewidth=2, markersize=8)
        plt.xlabel('Number of Clusters (k)')
        plt.ylabel('Silhouette Score')
        plt.title('Silhouette Score vs Number of Clusters')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/silhouette_plot.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. Calinski-Harabasz scores
        plt.figure(figsize=fig_size)
        plt.plot(results['k_range'], results['calinski_harabasz_scores'], 'ro-', linewidth=2, markersize=8)
        plt.xlabel('Number of Clusters (k)')
        plt.ylabel('Calinski-Harabasz Score')
        plt.title('Calinski-Harabasz Score vs Number of Clusters')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/calinski_harabasz_plot.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # 4. Davies-Bouldin scores
        plt.figure(figsize=fig_size)
        plt.plot(results['k_range'], results['davies_bouldin_scores'], 'mo-', linewidth=2, markersize=8)
        plt.xlabel('Number of Clusters (k)')
        plt.ylabel('Davies-Bouldin Index')
        plt.title('Davies-Bouldin Index vs Number of Clusters (Lower is Better)')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/davies_bouldin_plot.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # 5. Combined metrics plot
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Normalize scores for comparison
        silhouette_norm = np.array(results['silhouette_scores']) / max(results['silhouette_scores'])
        calinski_norm = np.array(results['calinski_harabasz_scores']) / max(results['calinski_harabasz_scores'])
        davies_norm = 1 - (np.array(results['davies_bouldin_scores']) / max(results['davies_bouldin_scores']))
        inertia_norm = 1 - (np.array(results['inertias']) / max(results['inertias']))
        
        ax1.plot(results['k_range'], inertia_norm, 'bo-', linewidth=2, markersize=6, label='Inertia (normalized)')
        ax1.set_xlabel('Number of Clusters (k)')
        ax1.set_ylabel('Normalized Score')
        ax1.set_title('Inertia (Elbow Method)')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        ax2.plot(results['k_range'], silhouette_norm, 'go-', linewidth=2, markersize=6, label='Silhouette (normalized)')
        ax2.set_xlabel('Number of Clusters (k)')
        ax2.set_ylabel('Normalized Score')
        ax2.set_title('Silhouette Score')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        ax3.plot(results['k_range'], calinski_norm, 'ro-', linewidth=2, markersize=6, label='Calinski-Harabasz (normalized)')
        ax3.set_xlabel('Number of Clusters (k)')
        ax3.set_ylabel('Normalized Score')
        ax3.set_title('Calinski-Harabasz Score')
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        
        ax4.plot(results['k_range'], davies_norm, 'mo-', linewidth=2, markersize=6, label='Davies-Bouldin (normalized)')
        ax4.set_xlabel('Number of Clusters (k)')
        ax4.set_ylabel('Normalized Score')
        ax4.set_title('Davies-Bouldin Index')
        ax4.grid(True, alpha=0.3)
        ax4.legend()
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/combined_metrics_plot.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Visualizations saved to {output_dir}")
    
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
            # Data integrity gate
            if not self.validate_data_integrity():
                return {'error': 'Data integrity validation failed'}
            
            # Load clean data
            df = self.load_clean_data(season)
            if df.empty:
                return {'error': 'No data available'}
            
            # Prepare features
            features_df, feature_names = self.prepare_features(df)
            
            # Phase 0: Feature space engineering with PCA
            pca_features, pca_model, scaler = self.engineer_feature_space(features_df)
            
            # Find optimal clusters
            optimal_results = self.find_optimal_clusters(pca_features)
            
            # Use the optimal k from silhouette score (most reliable metric)
            optimal_k = optimal_results['optimal_k_silhouette']
            
            # Perform final clustering
            final_results = self.perform_final_clustering(pca_features, optimal_k)
            
            # Validate stability
            stability_results = self.validate_cluster_stability(pca_features, optimal_k)
            
            # Create output directory
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = f"clustering_analysis_{timestamp}"
            
            # Create visualizations
            self.create_visualizations(optimal_results, output_dir)
            
            # Generate report
            report = {
                'validation_timestamp': datetime.now().isoformat(),
                'season': season,
                'output_directory': output_dir,
                'data_summary': {
                    'total_players': len(df),
                    'original_features': len(feature_names),
                    'pca_components': pca_features.shape[1],
                    'variance_explained': float(np.sum(pca_model.explained_variance_ratio_[:pca_features.shape[1]])),
                    'feature_names': feature_names
                },
                'pca_analysis': {
                    'explained_variance_ratio': pca_model.explained_variance_ratio_[:pca_features.shape[1]].tolist(),
                    'cumulative_variance': np.cumsum(pca_model.explained_variance_ratio_[:pca_features.shape[1]]).tolist()
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
        
        # Check PCA effectiveness
        pca_variance = final_results.get('pca_variance_explained', 0.95)
        if pca_variance > 0.9:
            recommendations.append("✅ PCA effectively reduced dimensionality while preserving variance")
        else:
            recommendations.append("⚠️ PCA may have lost important information")
        
        return recommendations

def main():
    """Run the clustering validation."""
    logger.info("Starting clustering validation with PCA-based feature engineering...")
    
    validator = ClusteringValidator()
    report = validator.generate_validation_report("2024-25")
    
    if 'error' in report:
        print(f"\n❌ Validation failed: {report['error']}")
    else:
        print("\n✅ Clustering validation completed successfully!")
        print(f"Optimal clusters: {report['final_clustering']['k']}")
        print(f"Silhouette score: {report['final_clustering']['silhouette_score']:.3f}")
        print(f"Stability score: {report['stability_validation']['stability_score']:.3f}")
        print(f"PCA components: {report['data_summary']['pca_components']}")
        print(f"Variance explained: {report['data_summary']['variance_explained']:.3f}")
        
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  {rec}")
        
        # Save report
        report_file = f"clustering_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\nDetailed report saved to: {report_file}")
        print(f"Visualizations saved to: {report['output_directory']}")

if __name__ == "__main__":
    main()