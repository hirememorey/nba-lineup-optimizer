"""
Master Data Pipeline

This script orchestrates the entire data pipeline using the new centralized
data fetcher and provides comprehensive validation and reporting.
"""

import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.nba_stats.api.data_fetcher import create_data_fetcher
from canonical_metrics import CANONICAL_48_METRICS
from definitive_metric_mapping import get_missing_metrics, get_available_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('master_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MasterDataPipeline:
    """
    Master pipeline for fetching and validating NBA player data.
    """
    
    def __init__(self, season: str = "2024-25"):
        """Initialize the master pipeline."""
        self.season = season
        self.fetcher = create_data_fetcher()
        self.results = {}
        self.validation_results = {}
        
    def run_full_pipeline(self) -> Dict[str, Any]:
        """
        Run the complete data pipeline.
        
        Returns:
            Dictionary containing all results and validation data
        """
        logger.info("Starting master data pipeline...")
        start_time = time.time()
        
        # Phase 1: Fetch all available data
        logger.info("Phase 1: Fetching all available data...")
        self.results = self.fetcher.fetch_all_available_metrics(self.season)
        
        # Phase 2: Validate data completeness
        logger.info("Phase 2: Validating data completeness...")
        self.validation_results = self.fetcher.validate_data_completeness(self.results)
        
        # Phase 3: Generate reports
        logger.info("Phase 3: Generating reports...")
        self._generate_comprehensive_report()
        
        # Phase 4: Save results
        logger.info("Phase 4: Saving results...")
        self._save_pipeline_results()
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"Pipeline completed in {duration:.2f} seconds")
        
        return {
            "results": self.results,
            "validation": self.validation_results,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
    
    def run_incremental_pipeline(self, metrics: List[str]) -> Dict[str, Any]:
        """
        Run pipeline for specific metrics only.
        
        Args:
            metrics: List of metric names to fetch
            
        Returns:
            Dictionary containing results for specified metrics
        """
        logger.info(f"Running incremental pipeline for {len(metrics)} metrics...")
        
        results = {}
        for metric in metrics:
            logger.info(f"Fetching {metric}...")
            data = self.fetcher.fetch_metric_data(metric, self.season)
            if data:
                results[metric] = data
            else:
                logger.warning(f"Failed to fetch {metric}")
        
        validation = self.fetcher.validate_data_completeness(results)
        
        return {
            "results": results,
            "validation": validation,
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_comprehensive_report(self) -> None:
        """Generate comprehensive pipeline report."""
        report_lines = []
        report_lines.append("# Master Data Pipeline Report")
        report_lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Season: {self.season}")
        report_lines.append("")
        
        # Summary statistics
        total_metrics = len(CANONICAL_48_METRICS)
        available_metrics = len(get_available_metrics())
        missing_metrics = len(get_missing_metrics())
        fetched_metrics = len(self.results)
        
        report_lines.append("## Summary Statistics")
        report_lines.append(f"- Total canonical metrics: {total_metrics}")
        report_lines.append(f"- Available in API: {available_metrics}")
        report_lines.append(f"- Missing from API: {missing_metrics}")
        report_lines.append(f"- Successfully fetched: {fetched_metrics}")
        report_lines.append(f"- Success rate: {(fetched_metrics/available_metrics)*100:.1f}%")
        report_lines.append("")
        
        # Missing metrics
        if missing_metrics > 0:
            report_lines.append("## Missing Metrics")
            for metric in get_missing_metrics():
                mapping = self.fetcher.metric_mappings[metric]
                report_lines.append(f"- {metric}: {mapping.canonical_name} - {mapping.notes}")
            report_lines.append("")
        
        # Data coverage by metric
        report_lines.append("## Data Coverage by Metric")
        for metric, stats in self.validation_results.get("coverage_stats", {}).items():
            report_lines.append(f"- {metric}: {stats['player_count']} players, {stats['coverage_pct']:.1f}% coverage")
        report_lines.append("")
        
        # Failed fetches
        failed_metrics = self.validation_results.get("missing_metrics", [])
        if failed_metrics:
            report_lines.append("## Failed Fetches")
            for metric in failed_metrics:
                report_lines.append(f"- {metric}")
            report_lines.append("")
        
        # Save report
        report_content = "\n".join(report_lines)
        with open("master_pipeline_report.md", "w") as f:
            f.write(report_content)
        
        logger.info("Comprehensive report generated: master_pipeline_report.md")
    
    def _save_pipeline_results(self) -> None:
        """Save pipeline results to JSON files."""
        # Save raw data
        with open("pipeline_results.json", "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Save validation results
        with open("pipeline_validation.json", "w") as f:
            json.dump(self.validation_results, f, indent=2, default=str)
        
        # Save summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "season": self.season,
            "total_metrics": len(CANONICAL_48_METRICS),
            "available_metrics": len(get_available_metrics()),
            "fetched_metrics": len(self.results),
            "missing_metrics": get_missing_metrics(),
            "validation_summary": {
                "total_metrics": self.validation_results.get("total_metrics", 0),
                "fetched_metrics": self.validation_results.get("fetched_metrics", 0),
                "missing_metrics": len(self.validation_results.get("missing_metrics", [])),
                "empty_metrics": len(self.validation_results.get("empty_metrics", []))
            }
        }
        
        with open("pipeline_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        logger.info("Pipeline results saved to JSON files")
    
    def get_data_quality_score(self) -> float:
        """
        Calculate a data quality score based on completeness and coverage.
        
        Returns:
            Score between 0 and 100
        """
        if not self.validation_results:
            return 0.0
        
        total_metrics = self.validation_results.get("total_metrics", 0)
        fetched_metrics = self.validation_results.get("fetched_metrics", 0)
        
        if total_metrics == 0:
            return 0.0
        
        # Base score from fetch success rate
        fetch_score = (fetched_metrics / total_metrics) * 100
        
        # Bonus for data coverage
        coverage_bonus = 0
        coverage_stats = self.validation_results.get("coverage_stats", {})
        if coverage_stats:
            avg_coverage = sum(stats["coverage_pct"] for stats in coverage_stats.values()) / len(coverage_stats)
            coverage_bonus = min(avg_coverage * 0.1, 10)  # Up to 10 bonus points
        
        return min(fetch_score + coverage_bonus, 100.0)

def main():
    """Main entry point for the master pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Master NBA Data Pipeline")
    parser.add_argument("--season", default="2024-25", help="Season to fetch data for")
    parser.add_argument("--metrics", nargs="+", help="Specific metrics to fetch (optional)")
    parser.add_argument("--incremental", action="store_true", help="Run incremental pipeline")
    
    args = parser.parse_args()
    
    pipeline = MasterDataPipeline(season=args.season)
    
    if args.incremental and args.metrics:
        logger.info("Running incremental pipeline...")
        results = pipeline.run_incremental_pipeline(args.metrics)
    else:
        logger.info("Running full pipeline...")
        results = pipeline.run_full_pipeline()
    
    # Print summary
    quality_score = pipeline.get_data_quality_score()
    print(f"\nPipeline completed!")
    print(f"Data quality score: {quality_score:.1f}/100")
    print(f"Results saved to: pipeline_results.json")
    print(f"Report saved to: master_pipeline_report.md")

if __name__ == "__main__":
    main()
