#!/usr/bin/env python3
"""
Bayesian Model Prototype using PyMC

This script implements a prototype of the Bayesian possession-level model
using PyMC for fast validation. This allows us to test the model structure
and behavior before committing to the full Stan implementation.

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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BayesianModelPrototype:
    """Prototype Bayesian model for possession-level analysis."""
    
    def __init__(self, data_path: str = "bayesian_model_data.csv"):
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
        Create the Bayesian model based on the research paper.
        
        The model is:
        E[y_i] = β_0,m_i + Σ_a β^off_a,m_i * Z^off_ia - Σ_a β^def_a,m_i * Z^def_ia
        
        Where:
        - y_i is the outcome of possession i
        - m_i is the matchup (offensive supercluster, defensive supercluster)
        - a is the archetype (0=Big Men, 1=Primary Ball Handlers, 2=Role Players)
        - Z^off_ia is the aggregated offensive skill for archetype a in possession i
        - Z^def_ia is the aggregated defensive skill for archetype a in possession i
        - β^off_a,m and β^def_a,m are the coefficients to be estimated
        """
        logger.info("Creating Bayesian model...")
        
        # Get unique matchups
        matchups = sorted(self.data['matchup'].unique())
        matchup_to_idx = {m: i for i, m in enumerate(matchups)}
        
        # Create matchup indices
        matchup_idx = np.array([matchup_to_idx[m] for m in self.data['matchup']])
        
        with pm.Model() as model:
            # Priors for matchup-specific intercepts
            β_0 = pm.Normal('β_0', mu=0, sigma=1, shape=len(matchups))
            
            # Priors for offensive coefficients (must be positive)
            β_off = pm.HalfNormal('β_off', sigma=5, shape=(len(matchups), 3))
            
            # Priors for defensive coefficients (must be positive)
            β_def = pm.HalfNormal('β_def', sigma=5, shape=(len(matchups), 3))
            
            # Linear predictor
            μ = β_0[matchup_idx]
            
            # Add offensive terms
            for a in range(3):  # 3 archetypes
                μ += β_off[matchup_idx, a] * self.data[f'z_off_{a}'].values
            
            # Subtract defensive terms
            for a in range(3):  # 3 archetypes
                μ -= β_def[matchup_idx, a] * self.data[f'z_def_{a}'].values
            
            # Likelihood
            y = pm.Normal('y', mu=μ, sigma=1, observed=self.data['outcome'].values)
        
        self.model = model
        logger.info("Model created successfully")
        return model
    
    def sample(self, draws: int = 1000, tune: int = 500, chains: int = 2) -> az.InferenceData:
        """
        Sample from the posterior distribution.
        
        Args:
            draws: Number of posterior samples
            tune: Number of tuning samples
            chains: Number of chains
        """
        logger.info(f"Sampling from posterior (draws={draws}, tune={tune}, chains={chains})")
        
        if self.model is None:
            raise ValueError("Model must be created before sampling")
        
        with self.model:
            self.trace = pm.sample(
                draws=draws,
                tune=tune,
                chains=chains,
                random_seed=42,
                return_inferencedata=True
            )
        
        logger.info("Sampling completed successfully")
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
        divergent_transitions = summary['r_hat'].isna().sum() if 'r_hat' in summary.columns else 0
        
        convergence_stats = {
            'max_rhat': float(max_rhat),
            'min_ess': float(min_ess),
            'divergent_transitions': int(divergent_transitions)
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
        
        # Filter for coefficient parameters
        coeff_summary = summary[summary.index.str.contains('β_')]
        
        # Add interpretation
        coeff_summary['interpretation'] = self._interpret_coefficients(coeff_summary)
        
        return coeff_summary
    
    def _interpret_coefficients(self, summary: pd.DataFrame) -> List[str]:
        """Add human-readable interpretation to coefficients."""
        interpretations = []
        
        for idx in summary.index:
            if 'β_0' in idx:
                interpretations.append("Matchup intercept")
            elif 'β_off' in idx:
                interpretations.append("Offensive skill coefficient")
            elif 'β_def' in idx:
                interpretations.append("Defensive skill coefficient")
            else:
                interpretations.append("Unknown parameter")
        
        return interpretations
    
    def plot_coefficients(self, save_path: str = "coefficient_plots.png"):
        """Create visualizations of the coefficients."""
        if self.trace is None:
            raise ValueError("Must sample before plotting")
        
        logger.info("Creating coefficient plots...")
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Bayesian Model Coefficient Analysis', fontsize=16)
        
        # Plot 1: Intercepts by matchup
        ax1 = axes[0, 0]
        β_0_data = self.trace.posterior['β_0'].values.reshape(-1, self.trace.posterior['β_0'].shape[-1])
        ax1.boxplot(β_0_data)
        ax1.set_title('Matchup Intercepts (β_0)')
        ax1.set_xlabel('Matchup')
        ax1.set_ylabel('Value')
        
        # Plot 2: Offensive coefficients
        ax2 = axes[0, 1]
        β_off_data = self.trace.posterior['β_off'].values.reshape(-1, self.trace.posterior['β_off'].shape[-1])
        ax2.boxplot(β_off_data)
        ax2.set_title('Offensive Coefficients (β_off)')
        ax2.set_xlabel('Archetype')
        ax2.set_ylabel('Value')
        
        # Plot 3: Defensive coefficients
        ax3 = axes[1, 0]
        β_def_data = self.trace.posterior['β_def'].values.reshape(-1, self.trace.posterior['β_def'].shape[-1])
        ax3.boxplot(β_def_data)
        ax3.set_title('Defensive Coefficients (β_def)')
        ax3.set_xlabel('Archetype')
        ax3.set_ylabel('Value')
        
        # Plot 4: Trace plots for key parameters
        ax4 = axes[1, 1]
        # Plot trace for first offensive coefficient
        β_off_trace = self.trace.posterior['β_off'][:, :, 0].values.flatten()
        ax4.plot(β_off_trace)
        ax4.set_title('Trace Plot: β_off[0,0]')
        ax4.set_xlabel('Sample')
        ax4.set_ylabel('Value')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Plots saved to {save_path}")
    
    def generate_report(self, output_path: str = "bayesian_model_report.txt"):
        """Generate a comprehensive model report."""
        if self.trace is None:
            raise ValueError("Must sample before generating report")
        
        logger.info("Generating model report...")
        
        with open(output_path, 'w') as f:
            f.write("Bayesian Model Prototype Report\n")
            f.write("==============================\n\n")
            
            # Data summary
            f.write("Data Summary:\n")
            f.write(f"  Total possessions: {len(self.data)}\n")
            f.write(f"  Unique matchups: {len(self.data['matchup'].unique())}\n")
            f.write(f"  Outcome statistics:\n")
            f.write(f"    Mean: {self.data['outcome'].mean():.4f}\n")
            f.write(f"    Std: {self.data['outcome'].std():.4f}\n\n")
            
            # Convergence diagnostics
            convergence = self.check_convergence()
            f.write("Convergence Diagnostics:\n")
            f.write(f"  Max R-hat: {convergence['max_rhat']:.4f}\n")
            f.write(f"  Min ESS: {convergence['min_ess']:.0f}\n")
            f.write(f"  Divergent transitions: {convergence['divergent_transitions']}\n\n")
            
            # Coefficient analysis
            coeff_summary = self.analyze_coefficients()
            f.write("Coefficient Analysis:\n")
            f.write(coeff_summary.to_string())
            f.write("\n\n")
            
            # Model validation
            f.write("Model Validation:\n")
            if convergence['max_rhat'] < 1.01:
                f.write("  ✅ R-hat values indicate good convergence\n")
            else:
                f.write("  ⚠️  R-hat values suggest convergence issues\n")
            
            if convergence['min_ess'] > 100:
                f.write("  ✅ Effective sample size is adequate\n")
            else:
                f.write("  ⚠️  Effective sample size may be insufficient\n")
        
        logger.info(f"Report saved to {output_path}")
    
    def run_prototype(self, draws: int = 1000, tune: int = 500, chains: int = 2) -> bool:
        """Run the complete prototype analysis."""
        logger.info("Starting Bayesian model prototype...")
        
        try:
            # Load data
            if not self.load_data():
                return False
            
            # Create model
            self.create_model()
            
            # Sample from posterior
            self.sample(draws=draws, tune=tune, chains=chains)
            
            # Check convergence
            convergence = self.check_convergence()
            
            # Analyze coefficients
            coeff_summary = self.analyze_coefficients()
            
            # Create plots
            self.plot_coefficients()
            
            # Generate report
            self.generate_report()
            
            logger.info("Prototype analysis completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error during prototype analysis: {e}")
            return False

def main():
    """Main function."""
    prototype = BayesianModelPrototype()
    success = prototype.run_prototype(draws=1000, tune=500, chains=2)
    
    if success:
        print("✅ Bayesian model prototype completed successfully!")
        print("Check the generated plots and report for results.")
    else:
        print("❌ Failed to run Bayesian model prototype")
        exit(1)

if __name__ == "__main__":
    main()
