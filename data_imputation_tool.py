"""
Data Imputation Tool

This tool handles missing values in NBA player data using various imputation
strategies, implementing the sparsity-aware approach recommended in the post-mortem.
"""

import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import sys
from datetime import datetime
from sklearn.impute import KNNImputer, SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from canonical_metrics import CANONICAL_48_METRICS
from definitive_metric_mapping import DEFINITIVE_METRIC_MAPPING

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_imputation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataImputationTool:
    """
    Advanced data imputation tool with multiple strategies.
    """
    
    def __init__(self, data_file: str = "pipeline_results.json"):
        """Initialize the imputation tool."""
        self.data_file = data_file
        self.data = self._load_data()
        self.imputation_results = {}
        self.imputation_strategies = {
            "mean": self._impute_mean,
            "median": self._impute_median,
            "mode": self._impute_mode,
            "knn": self._impute_knn,
            "rf": self._impute_random_forest,
            "forward_fill": self._impute_forward_fill,
            "backward_fill": self._impute_backward_fill
        }
        
    def _load_data(self) -> Dict[str, Dict[str, Any]]:
        """Load data from JSON file."""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Data file not found: {self.data_file}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON: {e}")
            return {}
    
    def run_comprehensive_imputation(self, strategy: str = "auto") -> Dict[str, Any]:
        """
        Run comprehensive data imputation.
        
        Args:
            strategy: Imputation strategy ('auto', 'mean', 'median', 'knn', 'rf', etc.)
            
        Returns:
            Dictionary containing imputed data and results
        """
        logger.info(f"Starting comprehensive imputation with strategy: {strategy}")
        
        # Convert data to DataFrame for easier manipulation
        df = self._convert_to_dataframe()
        
        if df.empty:
            logger.error("No data to impute")
            return {}
        
        # Analyze missing patterns
        missing_analysis = self._analyze_missing_patterns(df)
        
        # Choose imputation strategy
        if strategy == "auto":
            strategy = self._choose_optimal_strategy(df, missing_analysis)
        
        # Perform imputation
        logger.info(f"Using imputation strategy: {strategy}")
        imputed_df = self._perform_imputation(df, strategy)
        
        # Validate imputation
        validation_results = self._validate_imputation(df, imputed_df)
        
        # Convert back to original format
        imputed_data = self._convert_from_dataframe(imputed_df)
        
        # Save results
        self._save_imputation_results(imputed_data, validation_results)
        
        self.imputation_results = {
            "original_data": self.data,
            "imputed_data": imputed_data,
            "strategy_used": strategy,
            "missing_analysis": missing_analysis,
            "validation_results": validation_results,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("Comprehensive imputation completed")
        return self.imputation_results
    
    def _convert_to_dataframe(self) -> pd.DataFrame:
        """Convert data dictionary to pandas DataFrame."""
        if not self.data:
            return pd.DataFrame()
        
        # Get all unique player IDs
        all_player_ids = set()
        for player_data in self.data.values():
            all_player_ids.update(player_data.keys())
        
        # Create DataFrame with players as rows and metrics as columns
        df_data = {}
        for metric, player_data in self.data.items():
            df_data[metric] = [player_data.get(player_id) for player_id in all_player_ids]
        
        df = pd.DataFrame(df_data, index=list(all_player_ids))
        return df
    
    def _convert_from_dataframe(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Convert DataFrame back to original data format."""
        imputed_data = {}
        
        for metric in df.columns:
            imputed_data[metric] = {}
            for player_id in df.index:
                value = df.loc[player_id, metric]
                if pd.notna(value):
                    imputed_data[metric][player_id] = value
        
        return imputed_data
    
    def _analyze_missing_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns in missing data."""
        analysis = {
            "missing_by_metric": {},
            "missing_by_player": {},
            "missing_patterns": {},
            "correlation_matrix": None
        }
        
        # Missing by metric
        for metric in df.columns:
            missing_count = df[metric].isna().sum()
            total_count = len(df)
            analysis["missing_by_metric"][metric] = {
                "missing_count": int(missing_count),
                "total_count": total_count,
                "missing_pct": (missing_count / total_count) * 100
            }
        
        # Missing by player
        for player_id in df.index:
            missing_count = df.loc[player_id].isna().sum()
            total_metrics = len(df.columns)
            analysis["missing_by_player"][player_id] = {
                "missing_count": int(missing_count),
                "total_metrics": total_metrics,
                "missing_pct": (missing_count / total_metrics) * 100
            }
        
        # Missing patterns (which metrics are missing together)
        missing_matrix = df.isna()
        analysis["missing_patterns"] = {
            "most_common_patterns": missing_matrix.value_counts().head(10).to_dict(),
            "pattern_diversity": len(missing_matrix.value_counts())
        }
        
        # Correlation of missingness
        if len(df.columns) > 1:
            analysis["correlation_matrix"] = missing_matrix.corr().to_dict()
        
        return analysis
    
    def _choose_optimal_strategy(self, df: pd.DataFrame, missing_analysis: Dict[str, Any]) -> str:
        """
        Choose optimal imputation strategy based on data characteristics.
        This implements the sparsity-aware approach.
        """
        # Calculate overall missing percentage
        total_missing = df.isna().sum().sum()
        total_values = df.size
        missing_pct = (total_missing / total_values) * 100
        
        # Get data types
        numeric_metrics = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_metrics = df.select_dtypes(include=['object']).columns.tolist()
        
        # Choose strategy based on missing percentage and data types
        if missing_pct < 5:
            logger.info("Low missing data - using mean imputation")
            return "mean"
        elif missing_pct < 20:
            if len(numeric_metrics) > len(categorical_metrics):
                logger.info("Moderate missing data with mostly numeric - using KNN imputation")
                return "knn"
            else:
                logger.info("Moderate missing data with mixed types - using median imputation")
                return "median"
        else:
            if len(numeric_metrics) > len(categorical_metrics):
                logger.info("High missing data with mostly numeric - using Random Forest imputation")
                return "rf"
            else:
                logger.info("High missing data with mixed types - using mode imputation")
                return "mode"
    
    def _perform_imputation(self, df: pd.DataFrame, strategy: str) -> pd.DataFrame:
        """Perform imputation using the specified strategy."""
        if strategy not in self.imputation_strategies:
            logger.error(f"Unknown imputation strategy: {strategy}")
            return df
        
        logger.info(f"Performing {strategy} imputation...")
        return self.imputation_strategies[strategy](df)
    
    def _impute_mean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Impute missing values with mean."""
        return df.fillna(df.mean())
    
    def _impute_median(self, df: pd.DataFrame) -> pd.DataFrame:
        """Impute missing values with median."""
        return df.fillna(df.median())
    
    def _impute_mode(self, df: pd.DataFrame) -> pd.DataFrame:
        """Impute missing values with mode."""
        return df.fillna(df.mode().iloc[0])
    
    def _impute_knn(self, df: pd.DataFrame) -> pd.DataFrame:
        """Impute missing values using K-Nearest Neighbors."""
        # Only use numeric columns for KNN
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty:
            logger.warning("No numeric columns for KNN imputation, falling back to mean")
            return self._impute_mean(df)
        
        # Use KNN imputer
        imputer = KNNImputer(n_neighbors=5)
        imputed_numeric = pd.DataFrame(
            imputer.fit_transform(numeric_df),
            columns=numeric_df.columns,
            index=numeric_df.index
        )
        
        # Combine with non-numeric columns
        result_df = df.copy()
        for col in imputed_numeric.columns:
            result_df[col] = imputed_numeric[col]
        
        return result_df
    
    def _impute_random_forest(self, df: pd.DataFrame) -> pd.DataFrame:
        """Impute missing values using Random Forest."""
        # Only use numeric columns for Random Forest
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty:
            logger.warning("No numeric columns for Random Forest imputation, falling back to mean")
            return self._impute_mean(df)
        
        result_df = df.copy()
        
        # Impute each column using other columns as features
        for col in numeric_df.columns:
            if numeric_df[col].isna().any():
                # Prepare data
                feature_cols = [c for c in numeric_df.columns if c != col]
                X = numeric_df[feature_cols]
                y = numeric_df[col]
                
                # Split into known and unknown values
                known_mask = y.notna()
                X_known = X[known_mask]
                y_known = y[known_mask]
                X_unknown = X[~known_mask]
                
                if len(X_known) > 10 and len(X_unknown) > 0:  # Minimum data requirements
                    # Train Random Forest
                    rf = RandomForestRegressor(n_estimators=100, random_state=42)
                    rf.fit(X_known, y_known)
                    
                    # Predict missing values
                    predicted_values = rf.predict(X_unknown)
                    result_df.loc[~known_mask, col] = predicted_values
        
        return result_df
    
    def _impute_forward_fill(self, df: pd.DataFrame) -> pd.DataFrame:
        """Impute missing values using forward fill."""
        return df.fillna(method='ffill')
    
    def _impute_backward_fill(self, df: pd.DataFrame) -> pd.DataFrame:
        """Impute missing values using backward fill."""
        return df.fillna(method='bfill')
    
    def _validate_imputation(self, original_df: pd.DataFrame, imputed_df: pd.DataFrame) -> Dict[str, Any]:
        """Validate the quality of imputation."""
        validation = {
            "missing_before": int(original_df.isna().sum().sum()),
            "missing_after": int(imputed_df.isna().sum().sum()),
            "imputation_rate": 0.0,
            "data_distribution_changes": {},
            "validation_score": 0.0
        }
        
        # Calculate imputation rate
        if validation["missing_before"] > 0:
            validation["imputation_rate"] = (
                (validation["missing_before"] - validation["missing_after"]) / 
                validation["missing_before"]
            ) * 100
        
        # Check distribution changes for numeric columns
        numeric_cols = original_df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in imputed_df.columns:
                original_stats = original_df[col].describe()
                imputed_stats = imputed_df[col].describe()
                
                validation["data_distribution_changes"][col] = {
                    "original_mean": float(original_stats['mean']),
                    "imputed_mean": float(imputed_stats['mean']),
                    "original_std": float(original_stats['std']),
                    "imputed_std": float(imputed_stats['std']),
                    "mean_change_pct": abs(imputed_stats['mean'] - original_stats['mean']) / original_stats['mean'] * 100 if original_stats['mean'] != 0 else 0
                }
        
        # Calculate validation score
        validation["validation_score"] = min(validation["imputation_rate"], 100.0)
        
        return validation
    
    def _save_imputation_results(self, imputed_data: Dict[str, Dict[str, Any]], 
                                validation_results: Dict[str, Any]) -> None:
        """Save imputation results to files."""
        # Save imputed data
        with open("imputed_data.json", "w") as f:
            json.dump(imputed_data, f, indent=2, default=str)
        
        # Save validation results
        with open("imputation_validation.json", "w") as f:
            json.dump(validation_results, f, indent=2, default=str)
        
        # Generate imputation report
        self._generate_imputation_report(validation_results)
        
        logger.info("Imputation results saved to files")
    
    def _generate_imputation_report(self, validation_results: Dict[str, Any]) -> None:
        """Generate imputation report."""
        report_lines = []
        report_lines.append("# Data Imputation Report")
        report_lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Summary
        report_lines.append("## Summary")
        report_lines.append(f"- Missing values before: {validation_results['missing_before']}")
        report_lines.append(f"- Missing values after: {validation_results['missing_after']}")
        report_lines.append(f"- Imputation rate: {validation_results['imputation_rate']:.1f}%")
        report_lines.append(f"- Validation score: {validation_results['validation_score']:.1f}/100")
        report_lines.append("")
        
        # Distribution changes
        if validation_results["data_distribution_changes"]:
            report_lines.append("## Distribution Changes")
            for metric, changes in validation_results["data_distribution_changes"].items():
                report_lines.append(f"### {metric}")
                report_lines.append(f"- Mean change: {changes['mean_change_pct']:.2f}%")
                report_lines.append(f"- Original mean: {changes['original_mean']:.4f}")
                report_lines.append(f"- Imputed mean: {changes['imputed_mean']:.4f}")
                report_lines.append("")
        
        # Save report
        report_content = "\n".join(report_lines)
        with open("imputation_report.md", "w") as f:
            f.write(report_content)
        
        logger.info("Imputation report generated: imputation_report.md")

def main():
    """Main entry point for the imputation tool."""
    import argparse
    
    parser = argparse.ArgumentParser(description="NBA Data Imputation Tool")
    parser.add_argument("--data-file", default="pipeline_results.json", 
                       help="Path to data file to impute")
    parser.add_argument("--strategy", default="auto", 
                       choices=["auto", "mean", "median", "mode", "knn", "rf", "forward_fill", "backward_fill"],
                       help="Imputation strategy to use")
    parser.add_argument("--output", help="Output file for imputed data")
    
    args = parser.parse_args()
    
    imputer = DataImputationTool(data_file=args.data_file)
    results = imputer.run_comprehensive_imputation(strategy=args.strategy)
    
    # Save results
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results["imputed_data"], f, indent=2, default=str)
    
    # Print summary
    validation = results.get("validation_results", {})
    print(f"\nImputation completed!")
    print(f"Imputation rate: {validation.get('imputation_rate', 0):.1f}%")
    print(f"Validation score: {validation.get('validation_score', 0):.1f}/100")
    print(f"Imputed data saved to: imputed_data.json")
    print(f"Report saved to: imputation_report.md")

if __name__ == "__main__":
    main()
