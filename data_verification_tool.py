"""
Data Verification Tool

This tool provides comprehensive verification of NBA player data for completeness,
logical consistency, and quality. It implements the sparsity-aware approach
recommended in the post-mortem.
"""

import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from canonical_metrics import CANONICAL_48_METRICS
from definitive_metric_mapping import DEFINITIVE_METRIC_MAPPING, get_missing_metrics, get_available_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_verification.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataVerificationTool:
    """
    Comprehensive data verification tool with sparsity-aware validation.
    """
    
    def __init__(self, data_file: str = "pipeline_results.json"):
        """Initialize the verification tool."""
        self.data_file = data_file
        self.data = self._load_data()
        self.verification_results = {}
        
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
    
    def run_comprehensive_verification(self) -> Dict[str, Any]:
        """
        Run comprehensive data verification.
        
        Returns:
            Dictionary containing all verification results
        """
        logger.info("Starting comprehensive data verification...")
        
        # Phase 1: Basic completeness check
        logger.info("Phase 1: Checking basic completeness...")
        completeness_results = self._check_completeness()
        
        # Phase 2: Data quality analysis
        logger.info("Phase 2: Analyzing data quality...")
        quality_results = self._analyze_data_quality()
        
        # Phase 3: Logical consistency checks
        logger.info("Phase 3: Checking logical consistency...")
        consistency_results = self._check_logical_consistency()
        
        # Phase 4: Sparsity analysis
        logger.info("Phase 4: Analyzing data sparsity...")
        sparsity_results = self._analyze_sparsity()
        
        # Phase 5: Generate verification report
        logger.info("Phase 5: Generating verification report...")
        self._generate_verification_report({
            "completeness": completeness_results,
            "quality": quality_results,
            "consistency": consistency_results,
            "sparsity": sparsity_results
        })
        
        self.verification_results = {
            "completeness": completeness_results,
            "quality": quality_results,
            "consistency": consistency_results,
            "sparsity": sparsity_results,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("Comprehensive verification completed")
        return self.verification_results
    
    def _check_completeness(self) -> Dict[str, Any]:
        """Check basic data completeness."""
        results = {
            "total_metrics": len(CANONICAL_48_METRICS),
            "available_metrics": len(get_available_metrics()),
            "fetched_metrics": len(self.data),
            "missing_metrics": [],
            "empty_metrics": [],
            "completeness_score": 0.0
        }
        
        # Check for missing metrics
        for metric in CANONICAL_48_METRICS:
            if metric not in self.data:
                results["missing_metrics"].append(metric)
        
        # Check for empty metrics
        for metric, player_data in self.data.items():
            if not player_data or len(player_data) == 0:
                results["empty_metrics"].append(metric)
        
        # Calculate completeness score
        if results["available_metrics"] > 0:
            results["completeness_score"] = (results["fetched_metrics"] / results["available_metrics"]) * 100
        
        return results
    
    def _analyze_data_quality(self) -> Dict[str, Any]:
        """Analyze data quality metrics."""
        results = {
            "metric_quality": {},
            "overall_quality_score": 0.0,
            "data_types": {},
            "value_ranges": {}
        }
        
        for metric, player_data in self.data.items():
            if not player_data:
                continue
                
            # Convert to pandas Series for easier analysis
            values = pd.Series(list(player_data.values()))
            
            # Basic quality metrics
            non_null_count = values.notna().sum()
            null_count = values.isna().sum()
            total_count = len(values)
            
            quality_metrics = {
                "total_players": total_count,
                "non_null_count": int(non_null_count),
                "null_count": int(null_count),
                "completeness_pct": (non_null_count / total_count) * 100 if total_count > 0 else 0,
                "unique_values": int(values.nunique()),
                "data_type": str(values.dtype)
            }
            
            # Value range analysis
            if non_null_count > 0:
                numeric_values = pd.to_numeric(values, errors='coerce')
                if not numeric_values.isna().all():
                    quality_metrics.update({
                        "min_value": float(numeric_values.min()),
                        "max_value": float(numeric_values.max()),
                        "mean_value": float(numeric_values.mean()),
                        "std_value": float(numeric_values.std())
                    })
            
            results["metric_quality"][metric] = quality_metrics
        
        # Calculate overall quality score
        if results["metric_quality"]:
            avg_completeness = np.mean([m["completeness_pct"] for m in results["metric_quality"].values()])
            results["overall_quality_score"] = avg_completeness
        
        return results
    
    def _check_logical_consistency(self) -> Dict[str, Any]:
        """Check for logical consistency in the data."""
        results = {
            "consistency_checks": {},
            "anomalies": [],
            "consistency_score": 0.0
        }
        
        # Check percentage metrics are between 0 and 100
        percentage_metrics = [metric for metric, mapping in DEFINITIVE_METRIC_MAPPING.items() 
                            if mapping.get("data_type") == "percentage" and metric in self.data]
        
        for metric in percentage_metrics:
            player_data = self.data[metric]
            if not player_data:
                continue
                
            values = pd.Series(list(player_data.values()))
            numeric_values = pd.to_numeric(values, errors='coerce')
            
            # Check for values outside 0-100 range
            invalid_values = numeric_values[(numeric_values < 0) | (numeric_values > 100)]
            if len(invalid_values) > 0:
                results["anomalies"].append({
                    "metric": metric,
                    "type": "percentage_out_of_range",
                    "count": len(invalid_values),
                    "values": invalid_values.tolist()[:10]  # First 10 examples
                })
        
        # Check for negative counts
        count_metrics = [metric for metric, mapping in DEFINITIVE_METRIC_MAPPING.items() 
                        if mapping.get("data_type") == "count" and metric in self.data]
        
        for metric in count_metrics:
            player_data = self.data[metric]
            if not player_data:
                continue
                
            values = pd.Series(list(player_data.values()))
            numeric_values = pd.to_numeric(values, errors='coerce')
            
            # Check for negative values
            negative_values = numeric_values[numeric_values < 0]
            if len(negative_values) > 0:
                results["anomalies"].append({
                    "metric": metric,
                    "type": "negative_count",
                    "count": len(negative_values),
                    "values": negative_values.tolist()[:10]
                })
        
        # Calculate consistency score
        total_checks = len(percentage_metrics) + len(count_metrics)
        anomaly_count = len(results["anomalies"])
        if total_checks > 0:
            results["consistency_score"] = max(0, (total_checks - anomaly_count) / total_checks * 100)
        
        return results
    
    def _analyze_sparsity(self) -> Dict[str, Any]:
        """
        Analyze data sparsity using the sparsity-aware approach.
        This is the key insight from the post-mortem.
        """
        results = {
            "sparsity_by_metric": {},
            "player_coverage": {},
            "sparsity_recommendations": [],
            "sparsity_score": 0.0
        }
        
        # Analyze sparsity by metric
        for metric, player_data in self.data.items():
            if not player_data:
                continue
                
            values = pd.Series(list(player_data.values()))
            non_null_count = values.notna().sum()
            total_count = len(values)
            sparsity_pct = (1 - (non_null_count / total_count)) * 100 if total_count > 0 else 100
            
            results["sparsity_by_metric"][metric] = {
                "total_players": total_count,
                "non_null_players": int(non_null_count),
                "sparsity_pct": sparsity_pct,
                "sparsity_level": self._classify_sparsity_level(sparsity_pct)
            }
        
        # Analyze player coverage (how many metrics each player has)
        all_player_ids = set()
        for player_data in self.data.values():
            all_player_ids.update(player_data.keys())
        
        for player_id in all_player_ids:
            player_metrics = 0
            for player_data in self.data.values():
                if player_id in player_data and player_data[player_id] is not None:
                    player_metrics += 1
            
            results["player_coverage"][player_id] = {
                "metrics_available": player_metrics,
                "total_metrics": len(self.data),
                "coverage_pct": (player_metrics / len(self.data)) * 100 if self.data else 0
            }
        
        # Generate sparsity recommendations
        high_sparsity_metrics = [metric for metric, stats in results["sparsity_by_metric"].items() 
                               if stats["sparsity_level"] == "high"]
        
        if high_sparsity_metrics:
            results["sparsity_recommendations"].append({
                "type": "high_sparsity_metrics",
                "metrics": high_sparsity_metrics,
                "recommendation": "Consider imputation or alternative data sources"
            })
        
        # Calculate overall sparsity score
        if results["sparsity_by_metric"]:
            avg_sparsity = np.mean([stats["sparsity_pct"] for stats in results["sparsity_by_metric"].values()])
            results["sparsity_score"] = max(0, 100 - avg_sparsity)  # Lower sparsity = higher score
        
        return results
    
    def _classify_sparsity_level(self, sparsity_pct: float) -> str:
        """Classify sparsity level based on percentage."""
        if sparsity_pct < 10:
            return "low"
        elif sparsity_pct < 30:
            return "medium"
        else:
            return "high"
    
    def _generate_verification_report(self, results: Dict[str, Any]) -> None:
        """Generate comprehensive verification report."""
        report_lines = []
        report_lines.append("# Data Verification Report")
        report_lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Summary
        completeness = results["completeness"]
        quality = results["quality"]
        consistency = results["consistency"]
        sparsity = results["sparsity"]
        
        report_lines.append("## Summary")
        report_lines.append(f"- Total metrics: {completeness['total_metrics']}")
        report_lines.append(f"- Fetched metrics: {completeness['fetched_metrics']}")
        report_lines.append(f"- Completeness score: {completeness['completeness_score']:.1f}%")
        report_lines.append(f"- Quality score: {quality['overall_quality_score']:.1f}%")
        report_lines.append(f"- Consistency score: {consistency['consistency_score']:.1f}%")
        report_lines.append(f"- Sparsity score: {sparsity['sparsity_score']:.1f}%")
        report_lines.append("")
        
        # Missing metrics
        if completeness["missing_metrics"]:
            report_lines.append("## Missing Metrics")
            for metric in completeness["missing_metrics"]:
                report_lines.append(f"- {metric}")
            report_lines.append("")
        
        # Data quality by metric
        report_lines.append("## Data Quality by Metric")
        for metric, stats in quality["metric_quality"].items():
            report_lines.append(f"### {metric}")
            report_lines.append(f"- Players: {stats['total_players']}")
            report_lines.append(f"- Completeness: {stats['completeness_pct']:.1f}%")
            report_lines.append(f"- Unique values: {stats['unique_values']}")
            if 'mean_value' in stats:
                report_lines.append(f"- Mean: {stats['mean_value']:.2f}")
                report_lines.append(f"- Range: {stats['min_value']:.2f} - {stats['max_value']:.2f}")
            report_lines.append("")
        
        # Anomalies
        if consistency["anomalies"]:
            report_lines.append("## Data Anomalies")
            for anomaly in consistency["anomalies"]:
                report_lines.append(f"- {anomaly['metric']}: {anomaly['type']} ({anomaly['count']} instances)")
            report_lines.append("")
        
        # Sparsity analysis
        report_lines.append("## Sparsity Analysis")
        high_sparsity = [metric for metric, stats in sparsity["sparsity_by_metric"].items() 
                        if stats["sparsity_level"] == "high"]
        if high_sparsity:
            report_lines.append("### High Sparsity Metrics")
            for metric in high_sparsity:
                stats = sparsity["sparsity_by_metric"][metric]
                report_lines.append(f"- {metric}: {stats['sparsity_pct']:.1f}% missing")
            report_lines.append("")
        
        # Recommendations
        if sparsity["sparsity_recommendations"]:
            report_lines.append("## Recommendations")
            for rec in sparsity["sparsity_recommendations"]:
                report_lines.append(f"- {rec['recommendation']}")
                if "metrics" in rec:
                    report_lines.append(f"  - Affected metrics: {', '.join(rec['metrics'])}")
            report_lines.append("")
        
        # Save report
        report_content = "\n".join(report_lines)
        with open("data_verification_report.md", "w") as f:
            f.write(report_content)
        
        logger.info("Verification report generated: data_verification_report.md")
    
    def get_overall_health_score(self) -> float:
        """
        Calculate overall data health score.
        
        Returns:
            Score between 0 and 100
        """
        if not self.verification_results:
            return 0.0
        
        completeness = self.verification_results.get("completeness", {})
        quality = self.verification_results.get("quality", {})
        consistency = self.verification_results.get("consistency", {})
        sparsity = self.verification_results.get("sparsity", {})
        
        # Weighted average of all scores
        weights = {
            "completeness": 0.3,
            "quality": 0.3,
            "consistency": 0.2,
            "sparsity": 0.2
        }
        
        scores = {
            "completeness": completeness.get("completeness_score", 0),
            "quality": quality.get("overall_quality_score", 0),
            "consistency": consistency.get("consistency_score", 0),
            "sparsity": sparsity.get("sparsity_score", 0)
        }
        
        overall_score = sum(scores[key] * weights[key] for key in scores.keys())
        return min(overall_score, 100.0)

def main():
    """Main entry point for the verification tool."""
    import argparse
    
    parser = argparse.ArgumentParser(description="NBA Data Verification Tool")
    parser.add_argument("--data-file", default="pipeline_results.json", 
                       help="Path to data file to verify")
    parser.add_argument("--output", help="Output file for verification results")
    
    args = parser.parse_args()
    
    verifier = DataVerificationTool(data_file=args.data_file)
    results = verifier.run_comprehensive_verification()
    
    # Save results
    output_file = args.output or "verification_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    # Print summary
    health_score = verifier.get_overall_health_score()
    print(f"\nVerification completed!")
    print(f"Overall health score: {health_score:.1f}/100")
    print(f"Results saved to: {output_file}")
    print(f"Report saved to: data_verification_report.md")

if __name__ == "__main__":
    main()
