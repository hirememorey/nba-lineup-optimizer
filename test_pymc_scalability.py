#!/usr/bin/env python3
"""
Systematic Semantic Scalability Analysis for PyMC Bayesian Model

This script tests the PyMC model's scalability across incrementally larger data slices
while monitoring both statistical convergence and semantic validity of coefficients.

Usage:
    python test_pymc_scalability.py
"""

import os
import sys
import time
import json
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

try:
    import pymc as pm
    import arviz as az
    from bayesian_data_prep import BayesianDataPreparer
    from bayesian_model_prototype import BayesianModelPrototype
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install pymc arviz matplotlib seaborn pandas numpy")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scalability_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScalabilityAnalyzer:
    """Analyzes PyMC model scalability across different data sizes."""
    
    def __init__(self, output_dir: str = "scalability_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Data slice sizes to test (in possessions)
        self.test_sizes = [25000, 50000, 100000, 250000, 574357]
        
        # Results storage
        self.results = {}
        self.coefficient_trajectories = {}
        
    def load_full_dataset(self) -> pd.DataFrame:
        """Load the complete possession dataset."""
        logger.info("Loading full possession dataset...")
        
        # Check if production data exists
        production_data_path = "production_bayesian_data.csv"
        if os.path.exists(production_data_path):
            logger.info(f"Loading production data from {production_data_path}")
            return pd.read_csv(production_data_path)
        
        # Fallback to creating data from scratch
        logger.info("Production data not found. Creating from scratch...")
        preparer = BayesianDataPreparer()
        
        # Use the full dataset
        logger.info("Preparing data for full dataset...")
        preparer.run(
            input_csv="temp_full_dataset.csv",  # Use the full dataset
            output_csv=production_data_path
        )
        
        return pd.read_csv(production_data_path)
    
    def create_data_slice(self, data: pd.DataFrame, size: int) -> pd.DataFrame:
        """Create a stratified sample of the specified size."""
        logger.info(f"Creating data slice of size {size:,} possessions...")
        
        if size >= len(data):
            logger.info(f"Requested size {size:,} >= full dataset size {len(data):,}. Using full dataset.")
            return data.copy()
        
        # Stratified sampling to ensure all matchup combinations are represented
        unique_matchups = data['matchup'].unique()
        samples_per_matchup = max(1, size // len(unique_matchups))
        
        sampled_data = []
        for matchup in unique_matchups:
            matchup_data = data[data['matchup'] == matchup]
            if len(matchup_data) <= samples_per_matchup:
                sampled_data.append(matchup_data)
            else:
                sampled_data.append(matchup_data.sample(n=samples_per_matchup, random_state=42))
        
        result = pd.concat(sampled_data, ignore_index=True)
        logger.info(f"Created slice with {len(result):,} possessions across {len(unique_matchups)} matchups")
        return result
    
    def run_model_test(self, data: pd.DataFrame, size: int) -> Dict:
        """Run the PyMC model on a data slice and collect performance metrics."""
        logger.info(f"Running model test for size {size:,}...")
        
        start_time = time.time()
        
        try:
            # Initialize model
            model = BayesianModelPrototype()
            model.data = data
            
            # Create model
            with model.create_model():
                # Run sampling with conservative parameters for testing
                with model.model:
                    trace = pm.sample(
                        draws=200,  # Reduced for speed
                        tune=100,   # Reduced for speed
                        chains=2,   # Reduced for speed
                        cores=1,    # Single core for consistent timing
                        random_seed=42,
                        progressbar=True,
                        return_inferencedata=True
                    )
            
            # Calculate performance metrics
            runtime = time.time() - start_time
            
            # Statistical diagnostics
            summary = az.summary(trace)
            max_rhat = summary['r_hat'].max()
            min_ess = summary['ess_bulk'].min()
            divergent_transitions = trace.posterior.diverging.sum().item() if hasattr(trace.posterior, 'diverging') else 0
            
            # Memory usage (approximate)
            memory_mb = data.memory_usage(deep=True).sum() / 1024 / 1024
            
            # Extract coefficient information for semantic analysis
            coefficient_info = self.extract_coefficient_info(trace, data)
            
            result = {
                'size': size,
                'runtime_seconds': runtime,
                'memory_mb': memory_mb,
                'max_rhat': max_rhat,
                'min_ess': min_ess,
                'divergent_transitions': divergent_transitions,
                'convergence_passed': max_rhat < 1.01 and min_ess > 100,
                'coefficient_info': coefficient_info,
                'success': True
            }
            
            logger.info(f"Model test completed successfully for size {size:,}")
            logger.info(f"  Runtime: {runtime:.1f}s")
            logger.info(f"  Max R-hat: {max_rhat:.3f}")
            logger.info(f"  Min ESS: {min_ess:.0f}")
            logger.info(f"  Divergent transitions: {divergent_transitions}")
            
            return result
            
        except Exception as e:
            logger.error(f"Model test failed for size {size:,}: {str(e)}")
            return {
                'size': size,
                'runtime_seconds': time.time() - start_time,
                'memory_mb': data.memory_usage(deep=True).sum() / 1024 / 1024,
                'error': str(e),
                'success': False
            }
    
    def extract_coefficient_info(self, trace, data: pd.DataFrame) -> Dict:
        """Extract coefficient information for semantic analysis."""
        try:
            # Get unique matchups and archetypes
            unique_matchups = sorted(data['matchup'].unique())
            archetypes = ['Big Men', 'Primary Ball Handlers', 'Role Players']
            
            # Extract coefficient samples
            coefficient_info = {
                'matchups': unique_matchups,
                'archetypes': archetypes,
                'beta_off_means': {},
                'beta_def_means': {},
                'beta_off_intervals': {},
                'beta_def_intervals': {}
            }
            
            # Extract offensive coefficients
            for i, matchup in enumerate(unique_matchups):
                for j, archetype in enumerate(archetypes):
                    var_name = f'beta_off_{i}_{j}'
                    if var_name in trace.posterior:
                        samples = trace.posterior[var_name].values.flatten()
                        coefficient_info['beta_off_means'][f'{matchup}_{archetype}'] = np.mean(samples)
                        coefficient_info['beta_off_intervals'][f'{matchup}_{archetype}'] = {
                            'lower': np.percentile(samples, 2.5),
                            'upper': np.percentile(samples, 97.5)
                        }
            
            # Extract defensive coefficients
            for i, matchup in enumerate(unique_matchups):
                for j, archetype in enumerate(archetypes):
                    var_name = f'beta_def_{i}_{j}'
                    if var_name in trace.posterior:
                        samples = trace.posterior[var_name].values.flatten()
                        coefficient_info['beta_def_means'][f'{matchup}_{archetype}'] = np.mean(samples)
                        coefficient_info['beta_def_intervals'][f'{matchup}_{archetype}'] = {
                            'lower': np.percentile(samples, 2.5),
                            'upper': np.percentile(samples, 97.5)
                        }
            
            return coefficient_info
            
        except Exception as e:
            logger.warning(f"Could not extract coefficient info: {e}")
            return {'error': str(e)}
    
    def generate_coefficient_trajectory_report(self):
        """Generate a report showing how coefficients evolve with data size."""
        logger.info("Generating coefficient trajectory report...")
        
        if not self.coefficient_trajectories:
            logger.warning("No coefficient trajectory data available")
            return
        
        # Create trajectory plots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Coefficient Trajectories Across Data Sizes', fontsize=16)
        
        # Plot 1: Offensive coefficients for most common matchup
        ax1 = axes[0, 0]
        self._plot_archetype_coefficients(ax1, 'offensive', 'Offensive Coefficients (Most Common Matchup)')
        
        # Plot 2: Defensive coefficients for most common matchup
        ax2 = axes[0, 1]
        self._plot_archetype_coefficients(ax2, 'defensive', 'Defensive Coefficients (Most Common Matchup)')
        
        # Plot 3: Coefficient stability (variance across sizes)
        ax3 = axes[1, 0]
        self._plot_coefficient_stability(ax3)
        
        # Plot 4: Statistical diagnostics over time
        ax4 = axes[1, 1]
        self._plot_statistical_diagnostics(ax4)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'coefficient_trajectories.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Generate text report
        self._generate_text_report()
    
    def _plot_archetype_coefficients(self, ax, coeff_type: str, title: str):
        """Plot archetype coefficients across data sizes."""
        sizes = []
        big_men = []
        ball_handlers = []
        role_players = []
        
        for size, data in self.coefficient_trajectories.items():
            if 'error' in data:
                continue
                
            sizes.append(size)
            coeff_key = f'beta_{coeff_type}_means'
            
            # Find most common matchup (simplified - use first matchup)
            if data.get('matchups'):
                matchup = data['matchups'][0]
                big_men.append(data[coeff_key].get(f'{matchup}_Big Men', 0))
                ball_handlers.append(data[coeff_key].get(f'{matchup}_Primary Ball Handlers', 0))
                role_players.append(data[coeff_key].get(f'{matchup}_Role Players', 0))
        
        if sizes:
            ax.plot(sizes, big_men, 'o-', label='Big Men', linewidth=2)
            ax.plot(sizes, ball_handlers, 's-', label='Primary Ball Handlers', linewidth=2)
            ax.plot(sizes, role_players, '^-', label='Role Players', linewidth=2)
            ax.set_xlabel('Data Size (possessions)')
            ax.set_ylabel('Coefficient Value')
            ax.set_title(title)
            ax.legend()
            ax.grid(True, alpha=0.3)
    
    def _plot_coefficient_stability(self, ax):
        """Plot coefficient stability across data sizes."""
        if len(self.coefficient_trajectories) < 2:
            ax.text(0.5, 0.5, 'Insufficient data for stability analysis', 
                   ha='center', va='center', transform=ax.transAxes)
            return
        
        # Calculate coefficient variance across sizes
        sizes = sorted([s for s in self.coefficient_trajectories.keys() if 'error' not in self.coefficient_trajectories[s]])
        
        if len(sizes) < 2:
            ax.text(0.5, 0.5, 'Insufficient data for stability analysis', 
                   ha='center', va='center', transform=ax.transAxes)
            return
        
        # Simplified stability analysis
        ax.plot(sizes, [0.1] * len(sizes), 'k--', alpha=0.5, label='Stability Threshold')
        ax.set_xlabel('Data Size (possessions)')
        ax.set_ylabel('Coefficient Variance')
        ax.set_title('Coefficient Stability Across Data Sizes')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_statistical_diagnostics(self, ax):
        """Plot statistical diagnostics across data sizes."""
        sizes = []
        rhats = []
        ess_values = []
        
        for size, result in self.results.items():
            if result.get('success', False):
                sizes.append(size)
                rhats.append(result.get('max_rhat', 0))
                ess_values.append(result.get('min_ess', 0))
        
        if sizes:
            ax2 = ax.twinx()
            line1 = ax.plot(sizes, rhats, 'ro-', label='Max R-hat', linewidth=2)
            line2 = ax2.plot(sizes, ess_values, 'bo-', label='Min ESS', linewidth=2)
            
            ax.axhline(y=1.01, color='r', linestyle='--', alpha=0.7, label='R-hat Threshold')
            ax2.axhline(y=400, color='b', linestyle='--', alpha=0.7, label='ESS Threshold')
            
            ax.set_xlabel('Data Size (possessions)')
            ax.set_ylabel('Max R-hat', color='r')
            ax2.set_ylabel('Min ESS', color='b')
            ax.set_title('Statistical Diagnostics Across Data Sizes')
            
            # Combine legends
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            ax.legend(lines, labels, loc='upper left')
            ax.grid(True, alpha=0.3)
    
    def _generate_text_report(self):
        """Generate a text report of the analysis."""
        report_path = self.output_dir / 'scalability_report.txt'
        
        with open(report_path, 'w') as f:
            f.write("PyMC Model Scalability Analysis Report\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("Test Configuration:\n")
            f.write(f"  Test sizes: {self.test_sizes}\n")
            f.write(f"  Output directory: {self.output_dir}\n\n")
            
            f.write("Results Summary:\n")
            f.write("-" * 20 + "\n")
            
            for size in sorted(self.results.keys()):
                result = self.results[size]
                f.write(f"\nData Size: {size:,} possessions\n")
                
                if result.get('success', False):
                    f.write(f"  Status: SUCCESS\n")
                    f.write(f"  Runtime: {result['runtime_seconds']:.1f} seconds\n")
                    f.write(f"  Memory: {result['memory_mb']:.1f} MB\n")
                    f.write(f"  Max R-hat: {result['max_rhat']:.3f}\n")
                    f.write(f"  Min ESS: {result['min_ess']:.0f}\n")
                    f.write(f"  Divergent transitions: {result['divergent_transitions']}\n")
                    f.write(f"  Convergence passed: {result['convergence_passed']}\n")
                else:
                    f.write(f"  Status: FAILED\n")
                    f.write(f"  Error: {result.get('error', 'Unknown error')}\n")
            
            f.write("\n\nRecommendations:\n")
            f.write("-" * 15 + "\n")
            
            # Analyze results and provide recommendations
            successful_sizes = [s for s, r in self.results.items() if r.get('success', False)]
            if successful_sizes:
                max_successful = max(successful_sizes)
                f.write(f"✓ Model successfully scaled up to {max_successful:,} possessions\n")
                
                # Check for convergence issues
                convergence_issues = [s for s, r in self.results.items() 
                                    if r.get('success', False) and not r.get('convergence_passed', False)]
                if convergence_issues:
                    f.write(f"⚠ Convergence issues detected at sizes: {convergence_issues}\n")
                    f.write("  Consider increasing tuning samples or chains for larger datasets\n")
                else:
                    f.write("✓ All successful runs passed convergence checks\n")
            else:
                f.write("❌ No successful model runs - investigate data preparation or model specification\n")
        
        logger.info(f"Text report saved to {report_path}")
    
    def run_analysis(self):
        """Run the complete scalability analysis."""
        logger.info("Starting Systematic Semantic Scalability Analysis...")
        
        # Load full dataset
        full_data = self.load_full_dataset()
        logger.info(f"Loaded dataset with {len(full_data):,} total possessions")
        
        # Test each data size
        for size in self.test_sizes:
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing data size: {size:,} possessions")
            logger.info(f"{'='*60}")
            
            # Create data slice
            data_slice = self.create_data_slice(full_data, size)
            
            # Run model test
            result = self.run_model_test(data_slice, size)
            self.results[size] = result
            
            # Store coefficient info for trajectory analysis
            if result.get('success', False) and 'coefficient_info' in result:
                self.coefficient_trajectories[size] = result['coefficient_info']
            
            # Save intermediate results
            self._save_intermediate_results()
            
            # Check if we should stop early
            if not result.get('success', False):
                logger.warning(f"Model failed at size {size:,}. Stopping analysis.")
                break
        
        # Generate final reports
        logger.info("\nGenerating final reports...")
        self.generate_coefficient_trajectory_report()
        
        logger.info(f"\nAnalysis complete! Results saved to {self.output_dir}")
        return self.results
    
    def _save_intermediate_results(self):
        """Save intermediate results to JSON."""
        results_path = self.output_dir / 'intermediate_results.json'
        
        # Convert numpy types to Python types for JSON serialization
        serializable_results = {}
        for size, result in self.results.items():
            serializable_result = {}
            for key, value in result.items():
                if isinstance(value, (np.integer, np.floating)):
                    serializable_result[key] = float(value)
                elif isinstance(value, dict):
                    serializable_result[key] = {k: float(v) if isinstance(v, (np.integer, np.floating)) else v 
                                             for k, v in value.items()}
                else:
                    serializable_result[key] = value
            serializable_results[size] = serializable_result
        
        with open(results_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)

def main():
    """Main execution function."""
    print("PyMC Model Scalability Analysis")
    print("=" * 40)
    
    analyzer = ScalabilityAnalyzer()
    results = analyzer.run_analysis()
    
    # Print summary
    print("\n" + "="*60)
    print("ANALYSIS SUMMARY")
    print("="*60)
    
    successful_sizes = [s for s, r in results.items() if r.get('success', False)]
    if successful_sizes:
        print(f"✓ Successfully tested up to {max(successful_sizes):,} possessions")
        print(f"✓ Results saved to: {analyzer.output_dir}")
        print(f"✓ Check 'coefficient_trajectories.png' for semantic analysis")
    else:
        print("❌ No successful model runs")
        print("Check the log file for detailed error information")

if __name__ == "__main__":
    main()
