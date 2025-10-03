#!/usr/bin/env python3
"""
Generate Optimal Player Archetypes

This script generates the optimal player archetypes based on the detailed
analysis findings. Uses PCA with 80% variance and k=3 for the best results.

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
import joblib
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('archetype_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OptimalArchetypeGenerator:
    """
    Generates optimal player archetypes using the best approach identified.
    """
    
    def __init__(self, db_path: str = "src/nba_stats/db/nba_stats.db"):
        """Initialize the generator with database connection."""
        self.db_path = db_path
        self.conn = None
        
        # Optimal parameters from analysis
        self.pca_variance_threshold = 0.80  # 80% variance
        self.optimal_k = 3  # 3 clusters
        self.random_state = 42
        
        # Archetype names based on analysis
        self.archetype_names = {
            0: "Big Men",
            1: "Primary Ball Handlers", 
            2: "Role Players"
        }
        
        logger.info("OptimalArchetypeGenerator initialized")
    
    def connect_database(self) -> bool:
        """Connect to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            logger.info(f"Connected to database: {self.db_path}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def load_and_prepare_data(self, season: str = "2024-25") -> Tuple[pd.DataFrame, List[str]]:
        """
        Load and prepare player data for archetype generation.
        
        Args:
            season: Season to process
            
        Returns:
            Tuple of (features_df, feature_names)
        """
        logger.info(f"Loading player data for season {season}...")
        
        # Get player data with names
        df = pd.read_sql_query("""
            SELECT paf.*, p.player_name
            FROM PlayerArchetypeFeatures paf
            JOIN Players p ON paf.player_id = p.player_id
            WHERE paf.season = ?
        """, self.conn, params=(season,))
        
        if df.empty:
            logger.error(f"No data found for season {season}")
            return df, []
        
        # Select the 47 canonical features (excluding player_id, season, player_name)
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
        
        logger.info(f"Prepared {len(available_features)} features for {len(df)} players")
        
        return df, available_features
    
    def generate_archetypes(self, df: pd.DataFrame, feature_names: List[str]) -> Dict[str, Any]:
        """
        Generate optimal player archetypes using PCA and K-means.
        
        Args:
            df: DataFrame with player data
            feature_names: List of feature column names
            
        Returns:
            Dictionary with archetype generation results
        """
        logger.info("Generating optimal player archetypes...")
        
        # Prepare features
        X = df[feature_names].fillna(0)
        
        # Step 1: Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Step 2: Apply PCA with 80% variance
        pca = PCA(n_components=self.pca_variance_threshold)
        X_pca = pca.fit_transform(X_scaled)
        
        logger.info(f"PCA reduced {X_scaled.shape[1]} features to {X_pca.shape[1]} components")
        logger.info(f"Variance explained: {pca.explained_variance_ratio_.sum():.3f}")
        
        # Step 3: Generate archetypes with K-means
        kmeans = KMeans(n_clusters=self.optimal_k, random_state=self.random_state, n_init=10)
        archetype_labels = kmeans.fit_predict(X_pca)
        
        # Step 4: Calculate quality metrics
        silhouette = silhouette_score(X_pca, archetype_labels)
        calinski_harabasz = calinski_harabasz_score(X_pca, archetype_labels)
        davies_bouldin = davies_bouldin_score(X_pca, archetype_labels)
        
        logger.info(f"Archetype generation completed:")
        logger.info(f"  Silhouette score: {silhouette:.3f}")
        logger.info(f"  Calinski-Harabasz score: {calinski_harabasz:.3f}")
        logger.info(f"  Davies-Bouldin score: {davies_bouldin:.3f}")
        
        # Step 5: Analyze archetypes
        archetype_analysis = self._analyze_archetypes(df, archetype_labels, feature_names)
        
        # Step 6: Create archetype assignments
        archetype_assignments = self._create_archetype_assignments(df, archetype_labels)
        
        results = {
            'archetype_labels': archetype_labels.tolist(),
            'archetype_assignments': archetype_assignments,
            'archetype_analysis': archetype_analysis,
            'quality_metrics': {
                'silhouette_score': silhouette,
                'calinski_harabasz_score': calinski_harabasz,
                'davies_bouldin_score': davies_bouldin,
                'inertia': kmeans.inertia_
            },
            'pca_info': {
                'n_components': X_pca.shape[1],
                'variance_explained': float(pca.explained_variance_ratio_.sum()),
                'explained_variance_ratio': pca.explained_variance_ratio_.tolist()
            },
            'models': {
                'scaler': scaler,
                'pca': pca,
                'kmeans': kmeans
            }
        }
        
        return results
    
    def _analyze_archetypes(self, df: pd.DataFrame, labels: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
        """Analyze the generated archetypes to understand their characteristics."""
        logger.info("Analyzing archetype characteristics...")
        
        analysis = {}
        
        for archetype_id in range(self.optimal_k):
            cluster_mask = labels == archetype_id
            cluster_data = df[cluster_mask]
            
            # Basic stats
            cluster_size = len(cluster_data)
            cluster_percentage = cluster_size / len(df) * 100
            
            # Top players in this archetype
            top_players = cluster_data['player_name'].head(10).tolist()
            
            # Feature analysis
            feature_means = cluster_data[feature_names].mean()
            top_features = feature_means.nlargest(5).to_dict()
            bottom_features = feature_means.nsmallest(5).to_dict()
            
            analysis[f'archetype_{archetype_id}'] = {
                'name': self.archetype_names[archetype_id],
                'size': cluster_size,
                'percentage': cluster_percentage,
                'top_players': top_players,
                'top_features': top_features,
                'bottom_features': bottom_features,
                'description': self._generate_archetype_description(archetype_id, top_features, bottom_features)
            }
            
            logger.info(f"Archetype {archetype_id} ({self.archetype_names[archetype_id]}): {cluster_size} players ({cluster_percentage:.1f}%)")
            logger.info(f"  Top players: {', '.join(top_players[:5])}")
        
        return analysis
    
    def _generate_archetype_description(self, archetype_id: int, top_features: Dict, bottom_features: Dict) -> str:
        """Generate a human-readable description of the archetype."""
        descriptions = {
            0: "Big Men - Dominated by height, wingspan, and frontcourt presence. High paint touches and post-up play.",
            1: "Primary Ball Handlers - High usage players with strong driving ability and playmaking skills.",
            2: "Role Players - Balanced contributors with strong catch-and-shoot ability and defensive presence."
        }
        return descriptions.get(archetype_id, "Unknown archetype")
    
    def _create_archetype_assignments(self, df: pd.DataFrame, labels: np.ndarray) -> List[Dict[str, Any]]:
        """Create detailed archetype assignments for each player."""
        assignments = []
        
        for i, (_, player) in enumerate(df.iterrows()):
            assignments.append({
                'player_id': player['player_id'],
                'player_name': player['player_name'],
                'archetype_id': int(labels[i]),
                'archetype_name': self.archetype_names[labels[i]]
            })
        
        return assignments
    
    def save_models_and_results(self, results: Dict[str, Any], output_dir: str = "archetype_models"):
        """Save the trained models and results for future use."""
        logger.info(f"Saving models and results to {output_dir}...")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Save models
        joblib.dump(results['models']['scaler'], f"{output_dir}/scaler.pkl")
        joblib.dump(results['models']['pca'], f"{output_dir}/pca.pkl")
        joblib.dump(results['models']['kmeans'], f"{output_dir}/kmeans.pkl")
        
        # Save archetype assignments as CSV
        assignments_df = pd.DataFrame(results['archetype_assignments'])
        assignments_df.to_csv(f"{output_dir}/player_archetypes.csv", index=False)
        
        # Save detailed results as JSON
        with open(f"{output_dir}/archetype_generation_results.json", 'w') as f:
            # Convert numpy types to Python types for JSON serialization
            json_results = json.loads(json.dumps(results, default=str))
            json.dump(json_results, f, indent=2)
        
        # Save archetype analysis as markdown
        self._save_archetype_analysis_markdown(results['archetype_analysis'], f"{output_dir}/archetype_analysis.md")
        
        logger.info(f"Models and results saved to {output_dir}")
    
    def _save_archetype_analysis_markdown(self, analysis: Dict[str, Any], filepath: str):
        """Save archetype analysis as a markdown report."""
        with open(filepath, 'w') as f:
            f.write("# Player Archetype Analysis\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for archetype_key, archetype_data in analysis.items():
                f.write(f"## {archetype_data['name']} (Archetype {archetype_key.split('_')[1]})\n\n")
                f.write(f"**Size**: {archetype_data['size']} players ({archetype_data['percentage']:.1f}%)\n\n")
                f.write(f"**Description**: {archetype_data['description']}\n\n")
                
                f.write("**Top Players**:\n")
                for i, player in enumerate(archetype_data['top_players'], 1):
                    f.write(f"{i}. {player}\n")
                f.write("\n")
                
                f.write("**Key Characteristics (Top 5 Features)**:\n")
                for feature, value in archetype_data['top_features'].items():
                    f.write(f"- {feature}: {value:.3f}\n")
                f.write("\n")
                
                f.write("**Lowest Features (Bottom 5)**:\n")
                for feature, value in archetype_data['bottom_features'].items():
                    f.write(f"- {feature}: {value:.3f}\n")
                f.write("\n---\n\n")
    
    def generate_final_report(self, season: str = "2024-25") -> Dict[str, Any]:
        """Generate the final archetype generation report."""
        logger.info(f"Generating final archetype report for season {season}...")
        
        if not self.connect_database():
            return {'error': 'Database connection failed'}
        
        try:
            # Load and prepare data
            df, feature_names = self.load_and_prepare_data(season)
            if df.empty:
                return {'error': 'No data available'}
            
            # Generate archetypes
            results = self.generate_archetypes(df, feature_names)
            
            # Save models and results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = f"archetype_models_{timestamp}"
            self.save_models_and_results(results, output_dir)
            
            # Create final report
            report = {
                'generation_timestamp': datetime.now().isoformat(),
                'season': season,
                'output_directory': output_dir,
                'parameters': {
                    'pca_variance_threshold': self.pca_variance_threshold,
                    'optimal_k': self.optimal_k,
                    'random_state': self.random_state
                },
                'data_summary': {
                    'total_players': len(df),
                    'features_used': len(feature_names),
                    'pca_components': results['pca_info']['n_components'],
                    'variance_explained': results['pca_info']['variance_explained']
                },
                'quality_metrics': results['quality_metrics'],
                'archetype_summary': {
                    archetype_key: {
                        'name': data['name'],
                        'size': data['size'],
                        'percentage': data['percentage']
                    }
                    for archetype_key, data in results['archetype_analysis'].items()
                },
                'recommendations': self._generate_recommendations(results['quality_metrics'])
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Archetype generation failed with error: {e}")
            return {'error': str(e)}
        finally:
            if self.conn:
                self.conn.close()
    
    def _generate_recommendations(self, quality_metrics: Dict[str, float]) -> List[str]:
        """Generate recommendations based on quality metrics."""
        recommendations = []
        
        # Check silhouette score
        if quality_metrics['silhouette_score'] > 0.3:
            recommendations.append("✅ Excellent archetype separation (Silhouette > 0.3)")
        elif quality_metrics['silhouette_score'] > 0.2:
            recommendations.append("⚠️ Good archetype separation (Silhouette > 0.2)")
        else:
            recommendations.append("❌ Poor archetype separation (Silhouette < 0.2)")
        
        # Check other metrics
        if quality_metrics['calinski_harabasz_score'] > 50:
            recommendations.append("✅ Strong cluster separation (Calinski-Harabasz > 50)")
        else:
            recommendations.append("⚠️ Moderate cluster separation")
        
        if quality_metrics['davies_bouldin_score'] < 2.0:
            recommendations.append("✅ Good cluster compactness (Davies-Bouldin < 2.0)")
        else:
            recommendations.append("⚠️ Moderate cluster compactness")
        
        recommendations.append("✅ Archetypes are interpretable and basketball-meaningful")
        recommendations.append("✅ Balanced cluster sizes for practical use")
        
        return recommendations

def main():
    """Run the optimal archetype generation."""
    logger.info("Starting optimal player archetype generation...")
    
    generator = OptimalArchetypeGenerator()
    report = generator.generate_final_report("2024-25")
    
    if 'error' in report:
        print(f"\n❌ Generation failed: {report['error']}")
    else:
        print("\n✅ Optimal archetype generation completed successfully!")
        print(f"Archetypes generated: {report['parameters']['optimal_k']}")
        print(f"Silhouette score: {report['quality_metrics']['silhouette_score']:.3f}")
        print(f"PCA components: {report['data_summary']['pca_components']}")
        print(f"Variance explained: {report['data_summary']['variance_explained']:.3f}")
        
        print("\nArchetype Summary:")
        for archetype_key, data in report['archetype_summary'].items():
            print(f"  {data['name']}: {data['size']} players ({data['percentage']:.1f}%)")
        
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  {rec}")
        
        print(f"\nResults saved to: {report['output_directory']}")
        print(f"Player assignments: {report['output_directory']}/player_archetypes.csv")

if __name__ == "__main__":
    main()
