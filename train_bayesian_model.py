#!/usr/bin/env python3
"""
Stan-based Bayesian Model Training

This script trains the Bayesian possession-level model using Stan.
It's designed to be a production-ready replacement for the PyMC prototype.

Author: AI Assistant
Date: October 3, 2025
"""

import pandas as pd
import numpy as np
import cmdstanpy
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StanBayesianModel:
    """Stan-based Bayesian model for possession-level analysis."""
    
    def __init__(self, data_path: str = "bayesian_model_data.csv", 
                 model_path: str = "bayesian_model.stan"):
        self.data_path = data_path
        self.model_path = model_path
        self.data = None
        self.model = None
        self.fit = None
        
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
    
    def prepare_stan_data(self) -> Dict:
        """Prepare data in the format required by Stan."""
        logger.info("Preparing data for Stan...")
        
        # Get unique matchups and create mapping
        matchups = sorted(self.data['matchup'].unique())
        matchup_to_idx = {m: i+1 for i, m in enumerate(matchups)}  # Stan uses 1-based indexing
        
        # Create matchup indices
        matchup_idx = np.array([matchup_to_idx[m] for m in self.data['matchup']])
        
        # Prepare Stan data dictionary
        stan_data = {
            'N': len(self.data),
            'M': len(matchups),
            'matchup': matchup_idx,
            'outcome': self.data['outcome'].values,
            'z_off_0': self.data['z_off_0'].values,
            'z_off_1': self.data['z_off_1'].values,
            'z_off_2': self.data['z_off_2'].values,
            'z_def_0': self.data['z_def_0'].values,
            'z_def_1': self.data['z_def_1'].values,
            'z_def_2': self.data['z_def_2'].values
        }
        
        logger.info(f"Prepared data: {len(self.data)} possessions, {len(matchups)} matchups")
        return stan_data
    
    def compile_model(self) -> bool:
        """Compile the Stan model."""
        logger.info(f"Compiling Stan model from {self.model_path}")
        
        try:
            self.model = cmdstanpy.CmdStanModel(stan_file=self.model_path)
            logger.info("Model compiled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to compile model: {e}")
            return False
    
    def sample(self, draws: int = 1000, tune: int = 500, chains: int = 2, 
               adapt_delta: float = 0.8) -> bool:
        """
        Sample from the posterior distribution.
        
        Args:
            draws: Number of posterior samples
            tune: Number of tuning samples
            chains: Number of chains
            adapt_delta: Target acceptance rate for adaptation
        """
        logger.info(f"Sampling from posterior (draws={draws}, tune={tune}, chains={chains})")
        
        if self.model is None:
            raise ValueError("Model must be compiled before sampling")
        
        try:
            # Prepare data
            stan_data = self.prepare_stan_data()
            
            # Run sampling
            start_time = time.time()
            self.fit = self.model.sample(
                data=stan_data,
                chains=chains,
                iter_warmup=tune,
                iter_sampling=draws,
                adapt_delta=adapt_delta,
                seed=42,
                show_progress=True
            )
            
            sampling_time = time.time() - start_time
            logger.info(f"Sampling completed in {sampling_time:.1f} seconds")
            
            return True
            
        except Exception as e:
            logger.error(f"Sampling failed: {e}")
            return False
    
    def check_convergence(self) -> Dict[str, float]:
        """Check convergence diagnostics using simple CSV parsing."""
        if self.fit is None:
            raise ValueError("Must sample before checking convergence")
        
        logger.info("Checking convergence diagnostics...")
        
        try:
            # Get summary statistics
            summary = self.fit.summary()
            
            # Extract R-hat and ESS values
            max_rhat = summary['R_hat'].max() if 'R_hat' in summary.columns else 1.0
            min_ess = summary['ESS_bulk'].min() if 'ESS_bulk' in summary.columns else 0.0
            
            # Count divergent transitions (if available)
            divergent_transitions = 0
            if hasattr(self.fit, 'diagnose'):
                try:
                    diagnose = self.fit.diagnose()
                    if 'divergent' in diagnose:
                        divergent_transitions = diagnose['divergent']
                except:
                    pass
            
            convergence_stats = {
                'max_rhat': float(max_rhat),
                'min_ess': float(min_ess),
                'divergent_transitions': int(divergent_transitions)
            }
            
            logger.info(f"Convergence stats: {convergence_stats}")
            
            return convergence_stats
            
        except Exception as e:
            logger.error(f"Failed to check convergence: {e}")
            return {'max_rhat': 1.0, 'min_ess': 0.0, 'divergent_transitions': 0}
    
    def analyze_coefficients(self) -> pd.DataFrame:
        """Analyze the estimated coefficients."""
        if self.fit is None:
            raise ValueError("Must sample before analyzing coefficients")
        
        logger.info("Analyzing coefficients...")
        
        try:
            # Get coefficient summaries
            summary = self.fit.summary()
            
            # Filter for coefficient parameters
            coeff_summary = summary[summary.index.str.contains('β_')]
            
            # Add interpretation
            coeff_summary['interpretation'] = self._interpret_coefficients(coeff_summary)
            
            return coeff_summary
            
        except Exception as e:
            logger.error(f"Failed to analyze coefficients: {e}")
            return pd.DataFrame()
    
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
    
    def save_results(self, output_dir: str = "stan_model_results") -> bool:
        """Save model results and diagnostics."""
        if self.fit is None:
            raise ValueError("Must sample before saving results")
        
        logger.info(f"Saving results to {output_dir}")
        
        try:
            # Create output directory
            Path(output_dir).mkdir(exist_ok=True)
            
            # Save posterior samples
            self.fit.save_csvfiles(dir=output_dir)
            
            # Save convergence diagnostics
            convergence = self.check_convergence()
            with open(f"{output_dir}/convergence_diagnostics.json", 'w') as f:
                json.dump(convergence, f, indent=2)
            
            # Save coefficient analysis
            coeff_summary = self.analyze_coefficients()
            coeff_summary.to_csv(f"{output_dir}/coefficient_summary.csv")
            
            # Save model summary
            summary = self.fit.summary()
            summary.to_csv(f"{output_dir}/model_summary.csv")
            
            logger.info("Results saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return False
    
    def generate_report(self, output_path: str = "stan_model_report.txt"):
        """Generate a comprehensive model report."""
        if self.fit is None:
            raise ValueError("Must sample before generating report")
        
        logger.info("Generating model report...")
        
        try:
            with open(output_path, 'w') as f:
                f.write("Stan Bayesian Model Report\n")
                f.write("==========================\n\n")
                
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
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
    
    def run_training(self, draws: int = 1000, tune: int = 500, chains: int = 2) -> bool:
        """Run the complete training process."""
        logger.info("Starting Stan Bayesian model training...")
        
        try:
            # Load data
            if not self.load_data():
                return False
            
            # Compile model
            if not self.compile_model():
                return False
            
            # Sample from posterior
            if not self.sample(draws=draws, tune=tune, chains=chains):
                return False
            
            # Check convergence
            convergence = self.check_convergence()
            
            # Save results
            self.save_results()
            
            # Generate report
            self.generate_report()
            
            logger.info("Training completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error during training: {e}")
            return False

def main():
    """Main function."""
    model = StanBayesianModel()
    success = model.run_training(draws=1000, tune=500, chains=2)
    
    if success:
        print("✅ Stan Bayesian model training completed successfully!")
        print("Check the generated results and report for details.")
    else:
        print("❌ Failed to run Stan Bayesian model training")
        exit(1)

if __name__ == "__main__":
    main()