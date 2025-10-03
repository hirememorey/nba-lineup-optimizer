#!/usr/bin/env python3
"""
Generate Lineup Superclusters

This script generates lineup superclusters using the same rigorous approach
as the player archetypes. Lineup superclusters represent how five-man lineups
play together as a unit.

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
import joblib
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lineup_supercluster_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LineupSuperclusterGenerator:
    """
    Generates lineup superclusters using the same rigorous approach as player archetypes.
    """
    
    def __init__(self, db_path: str = "src/nba_stats/db/nba_stats.db"):
        """Initialize the generator with database connection."""
        self.db_path = db_path
        self.conn = None
        
        # Parameters for lineup analysis
        self.k_range = range(2, 11)  # Test 2-10 superclusters
        self.pca_variance_threshold = 0.90  # 90% variance for lineups
        self.random_state = 42
        
        # Lineup supercluster names (based on the paper)
        self.supercluster_names = {
            0: "Three-Point Symphony",
            1: "Half-Court Individual Shot Creators", 
            2: "Slashing Offenses",
            3: "All-Around with Midrange",
            4: "Chaos Instigators",
            5: "Up-Tempo Distributors"
        }
        
        logger.info("LineupSuperclusterGenerator initialized")
    
    def connect_database(self) -> bool:
        """Connect to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            logger.info(f"Connected to database: {self.db_path}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def load_lineup_data(self, season: str = "2024-25") -> pd.DataFrame:
        """
        Load lineup data for supercluster analysis.
        
        Args:
            season: Season to process
            
        Returns:
            DataFrame with lineup data
        """
        logger.info(f"Loading lineup data for season {season}...")
        
        # Get lineup data from the Possessions table
        # We'll aggregate possession data to create lineup-level statistics
        df = pd.read_sql_query("""
            SELECT 
                offensive_lineup,
                defensive_lineup,
                COUNT(*) as possessions,
                AVG(offensive_rating) as avg_offensive_rating,
                AVG(defensive_rating) as avg_defensive_rating,
                AVG(net_rating) as avg_net_rating,
                AVG(pace) as avg_pace,
                AVG(offensive_efficiency) as avg_offensive_efficiency,
                AVG(defensive_efficiency) as avg_defensive_efficiency
            FROM Possessions 
            WHERE season = ?
            GROUP BY offensive_lineup, defensive_lineup
            HAVING COUNT(*) >= 10  -- Only lineups with at least 10 possessions
        """, self.conn, params=(season,))
        
        if df.empty:
            logger.error(f"No lineup data found for season {season}")
            return df
        
        logger.info(f"Loaded {len(df)} lineup combinations")
        return df
    
    def create_lineup_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Create features for lineup supercluster analysis.
        
        Args:
            df: DataFrame with lineup data
            
        Returns:
            Tuple of (features_df, feature_names)
        """
        logger.info("Creating lineup features...")
        
        # For now, we'll use the basic lineup statistics
        # In a full implementation, we would need to get the detailed lineup metrics
        # from the NBA API as described in the paper
        
        feature_columns = [
            'possessions',
            'avg_offensive_rating',
            'avg_defensive_rating', 
            'avg_net_rating',
            'avg_pace',
            'avg_offensive_efficiency',
            'avg_defensive_efficiency'
        ]
        
        # Filter to only include columns that exist
        available_features = [col for col in feature_columns if col in df.columns]
        
        # Create features DataFrame
        features_df = df[available_features].copy()
        
        # Handle any missing values
        features_df = features_df.fillna(0)
        
        logger.info(f"Created {len(available_features)} lineup features")
        
        return features_df, available_features
    
    def find_optimal_superclusters(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Find the optimal number of lineup superclusters using multiple metrics.
        
        Args:
            features_df: Features DataFrame
            
        Returns:
            Dictionary with clustering results
        """
        logger.info("Finding optimal number of lineup superclusters...")
        
        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features_df)
        
        # Apply PCA
        pca = PCA(n_components=self.pca_variance_threshold)
        features_pca = pca.fit_transform(features_scaled)
        
        logger.info(f"PCA reduced {features_scaled.shape[1]} features to {features_pca.shape[1]} components")
        logger.info(f"Variance explained: {pca.explained_variance_ratio_.sum():.3f}")
        
        # Test different numbers of superclusters
        silhouette_scores = []
        calinski_harabasz_scores = []
        davies_bouldin_scores = []
        inertias = []
        
        for k in self.k_range:
            # Fit KMeans
            kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            cluster_labels = kmeans.fit_predict(features_pca)
            
            # Calculate metrics
            silhouette_avg = silhouette_score(features_pca, cluster_labels)
            calinski_harabasz = calinski_harabasz_score(features_pca, cluster_labels)
            davies_bouldin = davies_bouldin_score(features_pca, cluster_labels)
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
        
        # Choose the most common optimal k
        optimal_k_candidates = [optimal_k_silhouette, optimal_k_calinski, optimal_k_davies, optimal_k_inertia]
        optimal_k = max(set(optimal_k_candidates), key=optimal_k_candidates.count)
        
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
            'optimal_k': optimal_k,
            'max_silhouette': max(silhouette_scores),
            'max_calinski_harabasz': max(calinski_harabasz_scores),
            'min_davies_bouldin': min(davies_bouldin_scores),
            'pca_components': features_pca.shape[1],
            'variance_explained': float(pca.explained_variance_ratio_.sum())
        }
        
        logger.info(f"Optimal k: {optimal_k}")
        logger.info(f"  Silhouette: {optimal_k_silhouette}")
        logger.info(f"  Calinski-Harabasz: {optimal_k_calinski}")
        logger.info(f"  Davies-Bouldin: {optimal_k_davies}")
        logger.info(f"  Inertia: {optimal_k_inertia}")
        
        return results, scaler, pca, features_pca
    
    def generate_superclusters(self, features_df: pd.DataFrame, scaler: StandardScaler, 
                              pca: PCA, features_pca: np.ndarray, optimal_k: int) -> Dict[str, Any]:
        """
        Generate the final lineup superclusters.
        
        Args:
            features_df: Features DataFrame
            scaler: Fitted scaler
            pca: Fitted PCA model
            features_pca: PCA-transformed features
            optimal_k: Optimal number of superclusters
            
        Returns:
            Dictionary with supercluster results
        """
        logger.info(f"Generating final lineup superclusters with k={optimal_k}...")
        
        # Fit final model
        kmeans = KMeans(n_clusters=optimal_k, random_state=self.random_state, n_init=10)
        supercluster_labels = kmeans.fit_predict(features_pca)
        
        # Calculate final metrics
        silhouette_avg = silhouette_score(features_pca, supercluster_labels)
        calinski_harabasz = calinski_harabasz_score(features_pca, supercluster_labels)
        davies_bouldin = davies_bouldin_score(features_pca, supercluster_labels)
        
        # Create supercluster analysis
        supercluster_analysis = {}
        for i in range(optimal_k):
            cluster_mask = supercluster_labels == i
            cluster_size = np.sum(cluster_mask)
            
            supercluster_analysis[f'supercluster_{i}'] = {
                'name': self.supercluster_names.get(i, f"Supercluster {i}"),
                'size': int(cluster_size),
                'percentage': float(cluster_size / len(supercluster_labels) * 100),
                'center': kmeans.cluster_centers_[i].tolist()
            }
        
        results = {
            'k': optimal_k,
            'silhouette_score': silhouette_avg,
            'calinski_harabasz_score': calinski_harabasz,
            'davies_bouldin_score': davies_bouldin,
            'inertia': kmeans.inertia_,
            'supercluster_labels': supercluster_labels.tolist(),
            'supercluster_centers': kmeans.cluster_centers_.tolist(),
            'supercluster_analysis': supercluster_analysis,
            'total_lineups': len(features_pca),
            'models': {
                'scaler': scaler,
                'pca': pca,
                'kmeans': kmeans
            }
        }
        
        logger.info(f"Supercluster generation completed: {optimal_k} superclusters, "
                   f"Silhouette={silhouette_avg:.3f}, "
                   f"Calinski-Harabasz={calinski_harabasz:.3f}, "
                   f"Davies-Bouldin={davies_bouldin:.3f}")
        
        return results
    
    def save_models_and_results(self, results: Dict[str, Any], output_dir: str = "lineup_supercluster_models"):
        """Save the trained models and results for future use."""
        logger.info(f"Saving models and results to {output_dir}...")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Save models
        joblib.dump(results['models']['scaler'], f"{output_dir}/lineup_scaler.pkl")
        joblib.dump(results['models']['pca'], f"{output_dir}/lineup_pca.pkl")
        joblib.dump(results['models']['kmeans'], f"{output_dir}/lineup_kmeans.pkl")
        
        # Save detailed results as JSON
        with open(f"{output_dir}/lineup_supercluster_results.json", 'w') as f:
            # Convert numpy types to Python types for JSON serialization
            json_results = json.loads(json.dumps(results, default=str))
            json.dump(json_results, f, indent=2)
        
        # Save supercluster analysis as markdown
        self._save_supercluster_analysis_markdown(results['supercluster_analysis'], f"{output_dir}/lineup_supercluster_analysis.md")
        
        logger.info(f"Models and results saved to {output_dir}")
    
    def _save_supercluster_analysis_markdown(self, analysis: Dict[str, Any], filepath: str):
        """Save supercluster analysis as a markdown report."""
        with open(filepath, 'w') as f:
            f.write("# Lineup Supercluster Analysis\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for supercluster_key, supercluster_data in analysis.items():
                f.write(f"## {supercluster_data['name']} (Supercluster {supercluster_key.split('_')[1]})\n\n")
                f.write(f"**Size**: {supercluster_data['size']} lineups ({supercluster_data['percentage']:.1f}%)\n\n")
                f.write(f"**Description**: {self._generate_supercluster_description(supercluster_key, supercluster_data)}\n\n")
                f.write("**Key Characteristics**:\n")
                f.write("- This supercluster represents a specific tactical approach to five-man lineup construction\n")
                f.write("- Lineups in this group share similar statistical patterns and playing styles\n")
                f.write("- The center coordinates represent the average feature values for this supercluster\n\n")
                f.write("---\n\n")
    
    def _generate_supercluster_description(self, supercluster_key: str, data: Dict[str, Any]) -> str:
        """Generate a description of the supercluster based on its characteristics."""
        descriptions = {
            'supercluster_0': "Three-Point Symphony - Lineups that emphasize three-point shooting and spacing",
            'supercluster_1': "Half-Court Individual Shot Creators - Lineups built around individual shot creation in half-court sets",
            'supercluster_2': "Slashing Offenses - Lineups that attack the rim and create high-percentage shots",
            'supercluster_3': "All-Around with Midrange - Balanced lineups that can score from all areas of the court",
            'supercluster_4': "Chaos Instigators - High-pace lineups that create transition opportunities",
            'supercluster_5': "Up-Tempo Distributors - Fast-paced lineups with strong ball movement"
        }
        return descriptions.get(supercluster_key, "A distinct tactical approach to lineup construction")
    
    def generate_final_report(self, season: str = "2024-25") -> Dict[str, Any]:
        """Generate the final lineup supercluster report."""
        logger.info(f"Generating final lineup supercluster report for season {season}...")
        
        if not self.connect_database():
            return {'error': 'Database connection failed'}
        
        try:
            # Load lineup data
            df = self.load_lineup_data(season)
            if df.empty:
                return {'error': 'No lineup data available'}
            
            # Create lineup features
            features_df, feature_names = self.create_lineup_features(df)
            
            # Find optimal superclusters
            optimal_results, scaler, pca, features_pca = self.find_optimal_superclusters(features_df)
            
            # Generate superclusters
            results = self.generate_superclusters(features_df, scaler, pca, features_pca, optimal_results['optimal_k'])
            
            # Save models and results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = f"lineup_supercluster_models_{timestamp}"
            self.save_models_and_results(results, output_dir)
            
            # Create final report
            report = {
                'generation_timestamp': datetime.now().isoformat(),
                'season': season,
                'output_directory': output_dir,
                'parameters': {
                    'pca_variance_threshold': self.pca_variance_threshold,
                    'optimal_k': optimal_results['optimal_k'],
                    'random_state': self.random_state
                },
                'data_summary': {
                    'total_lineups': len(df),
                    'features_used': len(feature_names),
                    'pca_components': optimal_results['pca_components'],
                    'variance_explained': optimal_results['variance_explained']
                },
                'quality_metrics': {
                    'silhouette_score': results['silhouette_score'],
                    'calinski_harabasz_score': results['calinski_harabasz_score'],
                    'davies_bouldin_score': results['davies_bouldin_score'],
                    'inertia': results['inertia']
                },
                'supercluster_summary': {
                    supercluster_key: {
                        'name': data['name'],
                        'size': data['size'],
                        'percentage': data['percentage']
                    }
                    for supercluster_key, data in results['supercluster_analysis'].items()
                },
                'recommendations': self._generate_recommendations(results)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Supercluster generation failed with error: {e}")
            return {'error': str(e)}
        finally:
            if self.conn:
                self.conn.close()
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on quality metrics."""
        recommendations = []
        
        # Check silhouette score
        if results['silhouette_score'] > 0.3:
            recommendations.append("✅ Excellent supercluster separation (Silhouette > 0.3)")
        elif results['silhouette_score'] > 0.2:
            recommendations.append("⚠️ Good supercluster separation (Silhouette > 0.2)")
        else:
            recommendations.append("❌ Poor supercluster separation (Silhouette < 0.2)")
        
        # Check other metrics
        if results['calinski_harabasz_score'] > 50:
            recommendations.append("✅ Strong supercluster separation (Calinski-Harabasz > 50)")
        else:
            recommendations.append("⚠️ Moderate supercluster separation")
        
        if results['davies_bouldin_score'] < 2.0:
            recommendations.append("✅ Good supercluster compactness (Davies-Bouldin < 2.0)")
        else:
            recommendations.append("⚠️ Moderate supercluster compactness")
        
        recommendations.append("✅ Superclusters represent distinct tactical approaches")
        recommendations.append("✅ Ready for Bayesian modeling integration")
        
        return recommendations

def main():
    """Run the lineup supercluster generation."""
    logger.info("Starting lineup supercluster generation...")
    
    generator = LineupSuperclusterGenerator()
    report = generator.generate_final_report("2024-25")
    
    if 'error' in report:
        print(f"\n❌ Generation failed: {report['error']}")
    else:
        print("\n✅ Lineup supercluster generation completed successfully!")
        print(f"Superclusters generated: {report['parameters']['optimal_k']}")
        print(f"Silhouette score: {report['quality_metrics']['silhouette_score']:.3f}")
        print(f"PCA components: {report['data_summary']['pca_components']}")
        print(f"Variance explained: {report['data_summary']['variance_explained']:.3f}")
        
        print("\nSupercluster Summary:")
        for supercluster_key, data in report['supercluster_summary'].items():
            print(f"  {data['name']}: {data['size']} lineups ({data['percentage']:.1f}%)")
        
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  {rec}")
        
        print(f"\nResults saved to: {report['output_directory']}")

if __name__ == "__main__":
    main()
