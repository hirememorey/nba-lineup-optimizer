#!/usr/bin/env python3
"""
Bayesian Model Scaling Analysis

This script implements the statistical scaling analysis to validate that the
model's coefficient estimates stabilize and their uncertainty shrinks as we
add more data. This proves the model is actually learning, not just fitting to noise.

Author: AI Assistant
Date: October 3, 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import logging
import json
import time
from bayesian_data_prep import BayesianDataPreparer
from bayesian_model_prototype import BayesianModelPrototype

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BayesianScalingAnalyzer:
    """Analyzes how Bayesian model performance scales with data size."""
    
    def __init__(self, db_path: str = "src/nba_stats/db/nba_stats.db"):
        self.db_path = db_path
        self.data_preparer = BayesianDataPreparer(db_path)
        self.results = {}
        
    def create_scaling_samples(self) -> Dict[str, str]:
        """Create samples of different sizes for scaling analysis."""
        logger.info("Creating scaling samples...")
        
        # Load the full dataset
        if not self.data_preparer.load_metadata():
            raise RuntimeError("Failed to load metadata")
        
        # Load full possession data
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT 
            p.game_id,
            p.event_num,
            p.home_player_1_id, p.home_player_2_id, p.home_player_3_id, 
            p.home_player_4_id, p.home_player_5_id,
            p.away_player_1_id, p.away_player_2_id, p.away_player_3_id, 
            p.away_player_4_id, p.away_player_5_id,
            p.offensive_team_id,
            p.defensive_team_id,
            p.score,
            p.score_margin
        FROM Possessions p
        WHERE p.home_player_1_id IS NOT NULL 
        AND p.home_player_2_id IS NOT NULL 
        AND p.home_player_3_id IS NOT NULL 
        AND p.home_player_4_id IS NOT NULL 
        AND p.home_player_5_id IS NOT NULL
        AND p.away_player_1_id IS NOT NULL 
        AND p.away_player_2_id IS NOT NULL 
        AND p.away_player_3_id IS NOT NULL 
        AND p.away_player_4_id IS NOT NULL 
        AND p.away_player_5_id IS NOT NULL
        """
        
        full_data = pd.read_sql_query(query, conn)
        conn.close()
        
        logger.info(f"Loaded {len(full_data)} total possessions")
        
        # Create stratified samples of different sizes
        sample_sizes = [10000, 50000, 100000, 250000]
        sample_files = {}
        
        for size in sample_sizes:
            if size > len(full_data):
                logger.warning(f"Requested sample size {size} exceeds available data {len(full_data)}")
                continue
                
            logger.info(f"Creating sample of size {size}")
            
            # Create stratified sample
            sample = self._create_stratified_sample(full_data, size)
            
            # Prepare data for modeling
            prepared_data = self.data_preparer.prepare_possession_data(sample)
            
            # Save sample
            filename = f"scaling_sample_{size}.csv"
            prepared_data.to_csv(filename, index=False)
            sample_files[str(size)] = filename
            
            logger.info(f"Created {filename} with {len(prepared_data)} possessions")
        
        return sample_files
    
    def _create_stratified_sample(self, data: pd.DataFrame, target_size: int) -> pd.DataFrame:
        """Create a stratified sample ensuring all matchup combinations are represented."""
        # This is a simplified version - in practice, we'd want to ensure
        # all matchup combinations are represented in each sample
        return data.sample(n=min(target_size, len(data)), random_state=42)
    
    def run_scaling_analysis(self, sample_files: Dict[str, str]) -> Dict[str, Dict]:
        """Run the Bayesian model on samples of different sizes."""
        logger.info("Starting scaling analysis...")
        
        results = {}
        
        for size_str, filename in sample_files.items():
            size = int(size_str)
            logger.info(f"Running analysis on sample size {size}")
            
            start_time = time.time()
            
            # Run the model
            model = BayesianModelPrototype(filename)
            
            if not model.load_data():
                logger.error(f"Failed to load data for size {size}")
                continue
            
            model.create_model()
            
            # Use fewer samples for larger datasets to keep runtime reasonable
            if size <= 10000:
                draws, tune, chains = 1000, 500, 2
            elif size <= 50000:
                draws, tune, chains = 500, 250, 2
            else:
                draws, tune, chains = 250, 125, 2
            
            try:
                model.sample(draws=draws, tune=tune, chains=chains)
                convergence = model.check_convergence()
                coeff_summary = model.analyze_coefficients()
                
                runtime = time.time() - start_time
                
                # Extract key coefficient statistics
                key_coeffs = self._extract_key_coefficients(coeff_summary)
                
                results[size_str] = {
                    'runtime': runtime,
                    'convergence': convergence,
                    'coefficients': key_coeffs,
                    'sample_size': size,
                    'success': True
                }
                
                logger.info(f"Completed size {size} in {runtime:.1f} seconds")
                
            except Exception as e:
                logger.error(f"Failed to run model for size {size}: {e}")
                results[size_str] = {
                    'runtime': time.time() - start_time,
                    'error': str(e),
                    'sample_size': size,
                    'success': False
                }
        
        self.results = results
        return results
    
    def _extract_key_coefficients(self, coeff_summary: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Extract key coefficient statistics for analysis."""
        key_coeffs = {}
        
        # Focus on a few key coefficients for analysis
        key_params = ['β_off[0, 0]', 'β_off[0, 1]', 'β_def[0, 0]', 'β_def[0, 1]']
        
        for param in key_params:
            if param in coeff_summary.index:
                row = coeff_summary.loc[param]
                key_coeffs[param] = {
                    'mean': float(row['mean']),
                    'std': float(row['sd']),
                    'hdi_low': float(row['hdi_3%']),
                    'hdi_high': float(row['hdi_97%'])
                }
        
        return key_coeffs
    
    def plot_scaling_results(self, output_path: str = "scaling_analysis.png"):
        """Create visualizations of the scaling analysis results."""
        logger.info("Creating scaling analysis plots...")
        
        if not self.results:
            logger.error("No results to plot")
            return
        
        # Extract data for plotting
        sizes = []
        runtimes = []
        max_rhats = []
        min_esss = []
        
        coeff_means = {param: [] for param in ['β_off[0, 0]', 'β_off[0, 1]', 'β_def[0, 0]', 'β_def[0, 1]']}
        coeff_stds = {param: [] for param in ['β_off[0, 0]', 'β_off[0, 1]', 'β_def[0, 0]', 'β_def[0, 1]']}
        
        for size_str, result in self.results.items():
            if not result.get('success', False):
                continue
                
            size = result['sample_size']
            sizes.append(size)
            runtimes.append(result['runtime'])
            max_rhats.append(result['convergence']['max_rhat'])
            min_esss.append(result['convergence']['min_ess'])
            
            for param in coeff_means.keys():
                if param in result['coefficients']:
                    coeff_means[param].append(result['coefficients'][param]['mean'])
                    coeff_stds[param].append(result['coefficients'][param]['std'])
                else:
                    coeff_means[param].append(np.nan)
                    coeff_stds[param].append(np.nan)
        
        # Create plots
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Bayesian Model Scaling Analysis', fontsize=16)
        
        # Plot 1: Runtime vs Sample Size
        ax1 = axes[0, 0]
        ax1.loglog(sizes, runtimes, 'bo-')
        ax1.set_xlabel('Sample Size')
        ax1.set_ylabel('Runtime (seconds)')
        ax1.set_title('Runtime Scaling')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Convergence (R-hat) vs Sample Size
        ax2 = axes[0, 1]
        ax2.semilogx(sizes, max_rhats, 'ro-')
        ax2.axhline(y=1.01, color='r', linestyle='--', alpha=0.7, label='R-hat = 1.01')
        ax2.set_xlabel('Sample Size')
        ax2.set_ylabel('Max R-hat')
        ax2.set_title('Convergence (R-hat)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Effective Sample Size vs Sample Size
        ax3 = axes[0, 2]
        ax3.semilogx(sizes, min_esss, 'go-')
        ax3.axhline(y=100, color='g', linestyle='--', alpha=0.7, label='ESS = 100')
        ax3.set_xlabel('Sample Size')
        ax3.set_ylabel('Min ESS')
        ax3.set_title('Effective Sample Size')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Coefficient Means vs Sample Size
        ax4 = axes[1, 0]
        for param, means in coeff_means.items():
            if not all(np.isnan(means)):
                ax4.semilogx(sizes, means, 'o-', label=param)
        ax4.set_xlabel('Sample Size')
        ax4.set_ylabel('Coefficient Mean')
        ax4.set_title('Coefficient Stability')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # Plot 5: Coefficient Uncertainty vs Sample Size
        ax5 = axes[1, 1]
        for param, stds in coeff_stds.items():
            if not all(np.isnan(stds)):
                ax5.loglog(sizes, stds, 'o-', label=param)
        ax5.set_xlabel('Sample Size')
        ax5.set_ylabel('Coefficient Std')
        ax5.set_title('Uncertainty Reduction')
        ax5.legend()
        ax5.grid(True, alpha=0.3)
        
        # Plot 6: Coefficient Stability (error bars)
        ax6 = axes[1, 2]
        for param, means in coeff_means.items():
            if not all(np.isnan(means)):
                stds = coeff_stds[param]
                ax6.errorbar(sizes, means, yerr=stds, fmt='o-', label=param, capsize=3)
        ax6.set_xlabel('Sample Size')
        ax6.set_ylabel('Coefficient Value')
        ax6.set_title('Coefficient Estimates with Uncertainty')
        ax6.legend()
        ax6.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Scaling analysis plots saved to {output_path}")
    
    def generate_scaling_report(self, output_path: str = "scaling_analysis_report.txt"):
        """Generate a comprehensive scaling analysis report."""
        logger.info("Generating scaling analysis report...")
        
        with open(output_path, 'w') as f:
            f.write("Bayesian Model Scaling Analysis Report\n")
            f.write("=====================================\n\n")
            
            f.write("Analysis Summary:\n")
            f.write(f"  Total sample sizes tested: {len(self.results)}\n")
            f.write(f"  Successful runs: {sum(1 for r in self.results.values() if r.get('success', False))}\n\n")
            
            f.write("Results by Sample Size:\n")
            f.write("=" * 50 + "\n")
            
            for size_str, result in sorted(self.results.items(), key=lambda x: int(x[0])):
                size = result['sample_size']
                f.write(f"\nSample Size: {size:,}\n")
                f.write("-" * 20 + "\n")
                
                if result.get('success', False):
                    f.write(f"Runtime: {result['runtime']:.1f} seconds\n")
                    f.write(f"Max R-hat: {result['convergence']['max_rhat']:.4f}\n")
                    f.write(f"Min ESS: {result['convergence']['min_ess']:.0f}\n")
                    f.write(f"Divergent transitions: {result['convergence']['divergent_transitions']}\n")
                    
                    f.write("\nKey Coefficients:\n")
                    for param, stats in result['coefficients'].items():
                        f.write(f"  {param}: {stats['mean']:.4f} ± {stats['std']:.4f}\n")
                        f.write(f"    HDI: [{stats['hdi_low']:.4f}, {stats['hdi_high']:.4f}]\n")
                else:
                    f.write(f"Status: FAILED\n")
                    f.write(f"Error: {result.get('error', 'Unknown error')}\n")
            
            # Analysis conclusions
            f.write("\n" + "=" * 50 + "\n")
            f.write("SCALING ANALYSIS CONCLUSIONS\n")
            f.write("=" * 50 + "\n\n")
            
            successful_results = [r for r in self.results.values() if r.get('success', False)]
            
            if len(successful_results) >= 2:
                # Check if coefficients are stabilizing
                sizes = [r['sample_size'] for r in successful_results]
                coeff_stability = self._analyze_coefficient_stability()
                
                f.write("1. Coefficient Stability:\n")
                if coeff_stability['stable']:
                    f.write("   ✅ Coefficients appear to be stabilizing with sample size\n")
                else:
                    f.write("   ⚠️  Coefficients may not be stabilizing - model may be too complex\n")
                
                f.write(f"   Stability score: {coeff_stability['score']:.3f}\n\n")
                
                # Check if uncertainty is decreasing
                f.write("2. Uncertainty Reduction:\n")
                uncertainty_reduction = self._analyze_uncertainty_reduction()
                if uncertainty_reduction['decreasing']:
                    f.write("   ✅ Uncertainty is decreasing with sample size (good learning)\n")
                else:
                    f.write("   ⚠️  Uncertainty not decreasing - may indicate overfitting\n")
                
                f.write(f"   Reduction rate: {uncertainty_reduction['rate']:.3f}\n\n")
                
                # Overall recommendation
                f.write("3. Overall Recommendation:\n")
                if coeff_stability['stable'] and uncertainty_reduction['decreasing']:
                    f.write("   ✅ PROCEED with full-scale model training\n")
                    f.write("   The model shows good learning behavior and is ready for production.\n")
                else:
                    f.write("   ⚠️  CONSIDER model simplification before full training\n")
                    f.write("   The model may be too complex for the available data.\n")
            else:
                f.write("Insufficient successful runs for analysis.\n")
        
        logger.info(f"Scaling analysis report saved to {output_path}")
    
    def _analyze_coefficient_stability(self) -> Dict[str, any]:
        """Analyze whether coefficients are stabilizing across sample sizes."""
        # This is a simplified analysis - in practice, we'd use more sophisticated methods
        successful_results = [r for r in self.results.values() if r.get('success', False)]
        
        if len(successful_results) < 2:
            return {'stable': False, 'score': 0.0}
        
        # Calculate coefficient variance across sample sizes
        coeff_vars = []
        for param in ['β_off[0, 0]', 'β_off[0, 1]', 'β_def[0, 0]', 'β_def[0, 1]']:
            means = []
            for result in successful_results:
                if param in result['coefficients']:
                    means.append(result['coefficients'][param]['mean'])
            
            if len(means) >= 2:
                coeff_vars.append(np.var(means))
        
        # Lower variance indicates more stability
        avg_variance = np.mean(coeff_vars) if coeff_vars else 1.0
        stability_score = 1.0 / (1.0 + avg_variance)  # Higher is better
        
        return {
            'stable': stability_score > 0.5,
            'score': stability_score
        }
    
    def _analyze_uncertainty_reduction(self) -> Dict[str, any]:
        """Analyze whether uncertainty is decreasing with sample size."""
        successful_results = [r for r in self.results.values() if r.get('success', False)]
        
        if len(successful_results) < 2:
            return {'decreasing': False, 'rate': 0.0}
        
        # Calculate average uncertainty reduction
        uncertainty_changes = []
        for param in ['β_off[0, 0]', 'β_off[0, 1]', 'β_def[0, 0]', 'β_def[0, 1]']:
            stds = []
            sizes = []
            for result in successful_results:
                if param in result['coefficients']:
                    stds.append(result['coefficients'][param]['std'])
                    sizes.append(result['sample_size'])
            
            if len(stds) >= 2:
                # Calculate correlation between log(sample_size) and log(std)
                log_sizes = np.log(sizes)
                log_stds = np.log(stds)
                correlation = np.corrcoef(log_sizes, log_stds)[0, 1]
                uncertainty_changes.append(correlation)
        
        avg_correlation = np.mean(uncertainty_changes) if uncertainty_changes else 0.0
        
        return {
            'decreasing': avg_correlation < -0.5,  # Negative correlation means decreasing
            'rate': avg_correlation
        }
    
    def run_complete_analysis(self) -> bool:
        """Run the complete scaling analysis."""
        logger.info("Starting complete scaling analysis...")
        
        try:
            # Create samples
            sample_files = self.create_scaling_samples()
            
            # Run analysis
            results = self.run_scaling_analysis(sample_files)
            
            # Create plots
            self.plot_scaling_results()
            
            # Generate report
            self.generate_scaling_report()
            
            logger.info("Scaling analysis completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error during scaling analysis: {e}")
            return False

def main():
    """Main function."""
    analyzer = BayesianScalingAnalyzer()
    success = analyzer.run_complete_analysis()
    
    if success:
        print("✅ Bayesian scaling analysis completed successfully!")
        print("Check the generated plots and report for results.")
    else:
        print("❌ Failed to run scaling analysis")
        exit(1)

if __name__ == "__main__":
    main()
