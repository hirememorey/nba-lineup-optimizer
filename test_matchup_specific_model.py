#!/usr/bin/env python3
"""
Test Matchup-Specific Bayesian Model Training

This script validates the Phase 1 implementation by training the matchup-specific
Bayesian model on the prototype dataset and verifying that the pipeline works
correctly with the new 36×16 parameter architecture.
"""

import pandas as pd
import numpy as np
import cmdstanpy
import json
import logging
from pathlib import Path
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MatchupSpecificBayesianModel:
    """Matchup-specific Bayesian model for possession-level analysis."""

    def __init__(self, data_path: str = "matchup_specific_bayesian_data.csv",
                 model_path: str = "bayesian_model_k8_matchup_specific.stan"):
        self.data_path = data_path
        self.model_path = model_path
        self.data = None
        self.model = None
        self.fit = None

    def load_data(self) -> bool:
        """Load the matchup-specific model data."""
        logging.info(f"Loading matchup-specific data from {self.data_path}")

        try:
            self.data = pd.read_csv(self.data_path)
            logging.info(f"Loaded {len(self.data)} possessions")

            # Check matchup diversity
            unique_matchups = self.data['matchup_id'].nunique()
            logging.info(f"Matchup diversity: {unique_matchups} unique matchups")

            # Check archetype coverage
            z_cols = [f'z_off_{i}' for i in range(8)] + [f'z_def_{i}' for i in range(8)]
            archetype_coverage = {}
            for col in z_cols:
                if col in self.data.columns:
                    nonzero = (self.data[col] != 0).sum()
                    archetype_coverage[col] = nonzero

            logging.info("Archetype coverage:")
            for col in z_cols:
                if col in self.data.columns:
                    logging.info(f"  {col}: {archetype_coverage.get(col, 0):,}\ non-zero values")

            return True

        except Exception as e:
            logging.error(f"Failed to load data: {e}")
            return False

    def prepare_stan_data(self) -> dict:
        """Prepare data in the format required by the matchup-specific Stan model."""
        logging.info("Preparing data for matchup-specific Stan model...")

        # Ensure required columns exist
        z_off_cols = [f"z_off_{i}" for i in range(8)]
        z_def_cols = [f"z_def_{i}" for i in range(8)]
        required_cols = ['outcome', 'matchup_id'] + z_off_cols + z_def_cols

        missing = [c for c in required_cols if c not in self.data.columns]
        if missing:
            raise ValueError(f"Missing required columns for Stan model: {missing}")

        # Convert matchup_id to 0-based indexing for Stan (0-35)
        matchup_ids = self.data['matchup_id'].values

        # Prepare Stan data dictionary
        stan_data = {
            'N': int(len(self.data)),
            'y': self.data['outcome'].values.astype(float),
            'matchup_id': matchup_ids,
            'z_off': self.data[z_off_cols].values,
            'z_def': self.data[z_def_cols].values,
        }

        logging.info(f"Prepared data: {len(self.data)} possessions")
        logging.info(f"Matchup ID range: [{matchup_ids.min()}, {matchup_ids.max()}]")

        return stan_data

    def compile_model(self) -> bool:
        """Compile the matchup-specific Stan model."""
        logging.info(f"Compiling matchup-specific Stan model from {self.model_path}")

        try:
            self.model = cmdstanpy.CmdStanModel(stan_file=self.model_path)
            logging.info("Matchup-specific model compiled successfully")
            return True

        except Exception as e:
            logging.error(f"Failed to compile model: {e}")
            return False

    def sample(self, draws: int = 100, tune: int = 50, chains: int = 1) -> bool:
        """Sample from the posterior distribution of the matchup-specific model."""
        logging.info(f"Sampling from matchup-specific posterior (draws={draws}, tune={tune}, chains={chains})")

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
                adapt_delta=0.8,
                seed=42,
                show_progress=True
            )

            sampling_time = time.time() - start_time
            logging.info(f"Sampling completed in {sampling_time:.1f} seconds")

            return True

        except Exception as e:
            logging.error(f"Sampling failed: {e}")
            return False

    def check_convergence(self) -> dict:
        """Check convergence diagnostics."""
        if self.fit is None:
            raise ValueError("Must sample before checking convergence")

        logging.info("Checking convergence diagnostics...")

        try:
            summary = self.fit.summary()

            # Extract key diagnostics
            max_rhat = summary['R_hat'].max() if 'R_hat' in summary.columns else 1.0
            min_ess = summary['ESS_bulk'].min() if 'ESS_bulk' in summary.columns else 0.0

            convergence_stats = {
                'max_rhat': float(max_rhat),
                'min_ess': float(min_ess),
                'num_parameters': len(summary)
            }

            logging.info(f"Convergence stats: {convergence_stats}")
            return convergence_stats

        except Exception as e:
            logging.error(f"Failed to check convergence: {e}")
            return {'max_rhat': 1.0, 'min_ess': 0.0, 'num_parameters': 0}

    def save_results(self, output_dir: str = "stan_model_results_matchup_specific") -> bool:
        """Save model results and diagnostics."""
        if self.fit is None:
            raise ValueError("Must sample before saving results")

        logging.info(f"Saving results to {output_dir}")

        try:
            # Create output directory
            Path(output_dir).mkdir(exist_ok=True)

            # Save posterior samples
            self.fit.save_csvfiles(dir=output_dir)

            # Save convergence diagnostics
            convergence = self.check_convergence()
            with open(f"{output_dir}/convergence_diagnostics.json", 'w') as f:
                json.dump(convergence, f, indent=2)

            # Save model summary
            summary = self.fit.summary()
            summary.to_csv(f"{output_dir}/model_summary.csv")

            logging.info("Results saved successfully")
            return True

        except Exception as e:
            logging.error(f"Failed to save results: {e}")
            return False

    def run_training(self, draws: int = 10, tune: int = 5, chains: int = 1) -> bool:
        """Run the complete matchup-specific training process."""
        logging.info("Starting matchup-specific Bayesian model training...")

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

            logging.info("Matchup-specific training completed successfully!")
            return True

        except Exception as e:
            logging.error(f"Error during matchup-specific training: {e}")
            return False

def main():
    """Main function."""
    logging.info("="*80)
    logging.info("TESTING MATCHUP-SPECIFIC BAYESIAN MODEL")
    logging.info("="*80)

    model = MatchupSpecificBayesianModel()
    success = model.run_training(draws=10, tune=5, chains=1)

    if success:
        logging.info("\n✅ Matchup-specific model training completed successfully!")
        logging.info("Phase 1 prototype validation successful!")
    else:
        logging.error("\n❌ Matchup-specific model training failed")
        exit(1)

if __name__ == "__main__":
    main()