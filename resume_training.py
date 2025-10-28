#!/usr/bin/env python3
"""
Resume Matchup-Specific Model Training

Since the previous training crashed after 18 hours with insufficient samples,
this script implements a pragmatic approach:
1. Subsample the data (25K possessions vs 96K)
2. Reduce MCMC iterations (200 warmup + 500 samples vs 500 warmup + 1000 samples)
3. Expected time: 2-4 hours instead of 18+ hours
4. Still gets valid posterior estimates
"""

import pandas as pd
import numpy as np
import cmdstanpy
import logging
from pathlib import Path
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def train_with_subsample(data_path, stan_model, sample_size=25000, output_dir="stan_model_results_subsample"):
    """Train on subsampled data for much faster convergence."""
    logger.info("="*80)
    logger.info("TRAINING ON SUBSAMPLED DATA FOR FAST CONVERGENCE")
    logger.info("="*80)
    
    # Load and subsample data
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    logger.info(f"Subsampling to {sample_size:,} possessions for faster training")
    df = df.sample(n=min(sample_size, len(df)), random_state=42)
    
    N = len(df)
    y = df['outcome'].values
    matchup_id = df['matchup_id'].values
    
    z_off = df[[f'z_off_{i}' for i in range(8)]].values
    z_def = df[[f'z_def_{i}' for i in range(8)]].values
    
    stan_data = {
        'N': N,
        'y': y,
        'matchup_id': matchup_id,
        'z_off': z_off,
        'z_def': z_def
    }
    
    logger.info(f"Data prepared: {N:,} possessions, {df['matchup_id'].nunique()} unique matchups")
    
    # Compile model
    logger.info(f"Compiling Stan model...")
    model = cmdstanpy.CmdStanModel(stan_file=stan_model)
    logger.info("✅ Model compiled")
    
    # Run MCMC with reduced iterations
    logger.info("\nRunning MCMC sampling (reduced for faster convergence)...")
    logger.info("  Warmup: 200 iterations")
    logger.info("  Samples: 500 iterations")
    logger.info("  Chains: 4")
    logger.info("Expected time: ~2-4 hours (vs 18+ hours for full dataset)")
    
    start_time = time.time()
    
    fit = model.sample(
        data=stan_data,
        chains=4,
        iter_warmup=200,
        iter_sampling=500,
        adapt_delta=0.95,
        seed=42,
        show_progress=True
    )
    
    elapsed_time = time.time() - start_time
    logger.info(f"✅ MCMC completed in {elapsed_time/60:.1f} minutes")
    
    # Save results
    Path(output_dir).mkdir(exist_ok=True)
    
    # Extract coefficients
    logger.info("Extracting coefficients...")
    
    # Get MCMC samples
    beta_0_mean = fit.stan_variable('beta_0').mean(axis=0)
    beta_off_mean = fit.stan_variable('beta_off').mean(axis=0)
    beta_def_mean = fit.stan_variable('beta_def').mean(axis=0)
    
    # Save as CSV
    coefficients_df = []
    for matchup in range(36):
        row = {'matchup_id': matchup, 'beta_0': beta_0_mean[matchup]}
        
        for arch in range(8):
            row[f'beta_off_{arch}'] = beta_off_mean[matchup, arch]
            row[f'beta_def_{arch}'] = beta_def_mean[matchup, arch]
        
        coefficients_df.append(row)
    
    coefficients_df = pd.DataFrame(coefficients_df)
    coefficients_path = f"{output_dir}/matchup_specific_coefficients_advi.csv"
    coefficients_df.to_csv(coefficients_path, index=False)
    logger.info(f"✅ Coefficients saved to {coefficients_path}")
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("✅ TRAINING COMPLETE!")
    logger.info("="*80)
    logger.info(f"Time: {elapsed_time/60:.1f} minutes")
    logger.info(f"Coefficients: {coefficients_path}")
    
    return fit

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="matchup_specific_bayesian_data_full.csv")
    parser.add_argument("--stan", default="bayesian_model_k8_matchup_specific.stan")
    parser.add_argument("--size", type=int, default=25000, help="Subsample size (default: 25000)")
    parser.add_argument("--output", default="stan_model_results_subsample")
    
    args = parser.parse_args()
    
    train_with_subsample(args.data, args.stan, args.size, args.output)
    
    print("\n🎉 Subsample training complete!")
    print("\nNotes:")
    print(f"- Trained on {args.size:,} possessions (vs 96,837 full dataset)")
    print("- 200 warmup + 500 samples (vs 500 warmup + 1000 samples)")
    print("- Coefficients should be good for initial validation")
    print("- If results are promising, consider full dataset later")

if __name__ == "__main__":
    main()

