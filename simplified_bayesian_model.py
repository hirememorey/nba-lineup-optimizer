#!/usr/bin/env python3
"""
Simplified Bayesian Model for NBA Lineup Analysis

This script implements a simplified version of the Bayesian model that uses
shared coefficients across matchups to reduce parameter count and improve
convergence.

Author: AI Assistant
Date: October 3, 2025
"""

import pandas as pd
import numpy as np
import pymc as pm
import arviz as az
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimplifiedBayesianModel:
    """Simplified Bayesian model with shared coefficients across matchups."""
    
    def __init__(self, data_path: str = "production_bayesian_data.csv"):
        self.data_path = data_path
        self.data = None
        self.model = None
        self.trace = None
        
    def load_data(self) -> bool:
        """Load the prepared model data."""
        logger.info(f"Loading data from {self.data_path}")
        
        try:
            self.data = pd.read_csv(self.data_path)
            logger.info(f"Loaded {len(self.data)} possessions")
            
            # Log data summary
            logger.info(f"Unique matchups: {len(self.data['matchup'].unique())}")
            logger.info(f"Outcome range: [{self.data['outcome'].min():.3f}, {self.data['outcome'].max():.3f}]")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return False
    
    def create_model(self) -> pm.Model:
        """
        Create a simplified Bayesian model with shared coefficients.
        
        The simplified model is:
        E[y_i] = β_0 + Σ_a β^off_a * Z^off_ia - Σ_a β^def_a * Z^def_ia
        
        This reduces the parameter count from 36 to 7 (1 intercept + 3 offensive + 3 defensive).
        """
        logger.info("Creating simplified Bayesian model...")
        
        with pm.Model() as model:
            # Global intercept
            β_0 = pm.Normal('β_0', mu=0, sigma=1)
            
            # Shared offensive coefficients (must be positive)
            β_off = pm.HalfNormal('β_off', sigma=2, shape=3)
            
            # Shared defensive coefficients (must be positive)  
            β_def = pm.HalfNormal('β_def', sigma=2, shape=3)
            
            # Linear predictor
            μ = β_0
            
            # Add offensive terms
            for a in range(3):  # 3 archetypes
                μ += β_off[a] * self.data[f'z_off_{a}'].values
            
            # Subtract defensive terms
            for a in range(3):  # 3 archetypes
                μ -= β_def[a] * self.data[f'z_def_{a}'].values
            
            # Likelihood
            y = pm.Normal('y', mu=μ, sigma=1, observed=self.data['outcome'].values)
        
        self.model = model
        logger.info("Simplified model created successfully")
        return model
    
    def sample(self, draws: int = 1000, tune: int = 500, chains: int = 2) -> az.InferenceData:
        """Sample from the posterior distribution."""
        logger.info(f"Sampling from posterior (draws={draws}, tune={tune}, chains={chains})")
        
        if self.model is None:
            raise ValueError("Model must be created before sampling")
        
        start_time = time.time()
        
        with self.model:
            self.trace = pm.sample(
                draws=draws,
                tune=tune,
                chains=chains,
                random_seed=42,
                return_inferencedata=True,
                progressbar=True
            )
        
        runtime = time.time() - start_time
        logger.info(f"Sampling completed in {runtime:.1f} seconds")
        return self.trace
    
    def check_convergence(self) -> Dict[str, float]:
        """Check convergence diagnostics."""
        if self.trace is None:
            raise ValueError("Must sample before checking convergence")
        
        logger.info("Checking convergence diagnostics...")
        
        # Get summary statistics
        summary = az.summary(self.trace)
        
        # Extract R-hat and ESS values
        max_rhat = summary['r_hat'].max() if 'r_hat' in summary.columns else 1.0
        min_ess = summary['ess_bulk'].min() if 'ess_bulk' in summary.columns else 0.0
        
        # Check for divergent transitions
        divergent_transitions = 0
        if hasattr(self.trace.posterior, 'diverging'):
            divergent_transitions = self.trace.posterior.diverging.sum().item()
        
        convergence_stats = {
            'max_rhat': float(max_rhat),
            'min_ess': float(min_ess),
            'divergent_transitions': int(divergent_transitions),
            'convergence_passed': max_rhat < 1.01 and min_ess > 400 and divergent_transitions == 0
        }
        
        logger.info(f"Convergence stats: {convergence_stats}")
        
        return convergence_stats
    
    def analyze_coefficients(self) -> pd.DataFrame:
        """Analyze the estimated coefficients."""
        if self.trace is None:
            raise ValueError("Must sample before analyzing coefficients")
        
        logger.info("Analyzing coefficients...")
        
        # Get coefficient summaries
        summary = az.summary(self.trace)
        
        # Add interpretation
        archetypes = ['Big Men', 'Primary Ball Handlers', 'Role Players']
        
        coeff_data = []
        for i, archetype in enumerate(archetypes):
            # Offensive coefficient
            off_coeff = summary.loc[f'β_off[{i}]']
            coeff_data.append({
                'parameter': f'β_off_{i}',
                'archetype': archetype,
                'type': 'Offensive',
                'mean': off_coeff['mean'],
                'std': off_coeff['sd'],
                'hdi_3%': off_coeff['hdi_3%'],
                'hdi_97%': off_coeff['hdi_97%'],
                'r_hat': off_coeff['r_hat'],
                'ess_bulk': off_coeff['ess_bulk']
            })
            
            # Defensive coefficient
            def_coeff = summary.loc[f'β_def[{i}]']
            coeff_data.append({
                'parameter': f'β_def_{i}',
                'archetype': archetype,
                'type': 'Defensive',
                'mean': def_coeff['mean'],
                'std': def_coeff['sd'],
                'hdi_3%': def_coeff['hdi_3%'],
                'hdi_97%': def_coeff['hdi_97%'],
                'r_hat': def_coeff['r_hat'],
                'ess_bulk': def_coeff['ess_bulk']
            })
        
        # Add intercept
        intercept = summary.loc['β_0']
        coeff_data.append({
            'parameter': 'β_0',
            'archetype': 'Global',
            'type': 'Intercept',
            'mean': intercept['mean'],
            'std': intercept['sd'],
            'hdi_3%': intercept['hdi_3%'],
            'hdi_97%': intercept['hdi_97%'],
            'r_hat': intercept['r_hat'],
            'ess_bulk': intercept['ess_bulk']
        })
        
        return pd.DataFrame(coeff_data)
    
    def plot_coefficients(self, save_path: str = "simplified_coefficient_plots.png"):
        """Create visualizations of the coefficients."""
        if self.trace is None:
            raise ValueError("Must sample before plotting")
        
        logger.info("Creating coefficient plots...")
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Simplified Bayesian Model Coefficient Analysis', fontsize=16)
        
        # Plot 1: Coefficient means with credible intervals
        ax1 = axes[0, 0]
        coeff_df = self.analyze_coefficients()
        
        # Separate offensive and defensive coefficients
        off_coeffs = coeff_df[coeff_df['type'] == 'Offensive']
        def_coeffs = coeff_df[coeff_df['type'] == 'Defensive']
        
        x_pos = np.arange(len(off_coeffs))
        ax1.bar(x_pos - 0.2, off_coeffs['mean'], 0.4, 
                yerr=[off_coeffs['mean'] - off_coeffs['hdi_3%'], 
                      off_coeffs['hdi_97%'] - off_coeffs['mean']],
                label='Offensive', alpha=0.7, color='blue')
        ax1.bar(x_pos + 0.2, def_coeffs['mean'], 0.4,
                yerr=[def_coeffs['mean'] - def_coeffs['hdi_3%'],
                      def_coeffs['hdi_97%'] - def_coeffs['mean']],
                label='Defensive', alpha=0.7, color='red')
        
        ax1.set_xlabel('Archetype')
        ax1.set_ylabel('Coefficient Value')
        ax1.set_title('Coefficient Estimates with 94% Credible Intervals')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(off_coeffs['archetype'])
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Trace plots for key parameters
        ax2 = axes[0, 1]
        az.plot_trace(self.trace, var_names=['β_off', 'β_def'])
        ax2.set_title('Trace Plots')
        
        # Plot 3: Posterior distributions
        ax3 = axes[1, 0]
        az.plot_posterior(self.trace, var_names=['β_off', 'β_def'])
        ax3.set_title('Posterior Distributions')
        
        # Plot 4: Model diagnostics
        ax4 = axes[1, 1]
        summary = az.summary(self.trace)
        rhat_values = summary['r_hat'].values
        ess_values = summary['ess_bulk'].values
        
        ax4.scatter(rhat_values, ess_values, alpha=0.7)
        ax4.axvline(x=1.01, color='red', linestyle='--', label='R-hat threshold')
        ax4.axhline(y=400, color='blue', linestyle='--', label='ESS threshold')
        ax4.set_xlabel('R-hat')
        ax4.set_ylabel('ESS')
        ax4.set_title('Convergence Diagnostics')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Plots saved to {save_path}")
    
    def save_results(self, output_dir: str = "simplified_model_results"):
        """Save model results and diagnostics."""
        import os
        from pathlib import Path
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save trace
        self.trace.to_netcdf(output_path / "trace.nc")
        
        # Save coefficient analysis
        coeff_df = self.analyze_coefficients()
        coeff_df.to_csv(output_path / "coefficients.csv", index=False)
        
        # Save convergence stats
        conv_stats = self.check_convergence()
        with open(output_path / "convergence_stats.json", 'w') as f:
            import json
            json.dump(conv_stats, f, indent=2)
        
        # Save model summary
        summary = az.summary(self.trace)
        summary.to_csv(output_path / "model_summary.csv")
        
        logger.info(f"Results saved to {output_path}")

def main():
    """Main execution function."""
    print("Simplified Bayesian Model Test")
    print("=" * 40)
    
    # Initialize model
    model = SimplifiedBayesianModel()
    
    # Load data
    if not model.load_data():
        print("Failed to load data")
        return
    
    # Create model
    print("Creating simplified model...")
    model.create_model()
    
    # Sample from posterior
    print("Sampling from posterior...")
    start_time = time.time()
    
    try:
        model.sample(draws=1000, tune=500, chains=2)
        
        # Check convergence
        conv_stats = model.check_convergence()
        print(f"\nConvergence Results:")
        print(f"  Max R-hat: {conv_stats['max_rhat']:.3f}")
        print(f"  Min ESS: {conv_stats['min_ess']:.0f}")
        print(f"  Divergent transitions: {conv_stats['divergent_transitions']}")
        print(f"  Convergence passed: {conv_stats['convergence_passed']}")
        
        if conv_stats['convergence_passed']:
            print("\n✓ Model converged successfully!")
            
            # Analyze coefficients
            coeff_df = model.analyze_coefficients()
            print(f"\nCoefficient Analysis:")
            print(coeff_df[['archetype', 'type', 'mean', 'hdi_3%', 'hdi_97%']].to_string(index=False))
            
            # Create plots
            model.plot_coefficients()
            
            # Save results
            model.save_results()
            
            print(f"\n✓ Analysis complete! Results saved to simplified_model_results/")
        else:
            print("\n❌ Model did not converge properly")
            
    except Exception as e:
        print(f"Error during sampling: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
