#!/usr/bin/env python3
"""
Train Full Matchup-Specific Model for Cloud Deployment

This script trains the matchup-specific model on the complete 96,837 possession
dataset. Designed for RunPod or other cloud compute environments that can handle
30-40 hour training runs.

Configuration:
- Data: matchup_specific_bayesian_data_full.csv (96,837 possessions, 32 matchups)
- Model: bayesian_model_k8_matchup_specific.stan
- Parameters: 612 (36 matchups × 16 params each)
- Expected: 30-40 hours training time
"""

import pandas as pd
import numpy as np
import cmdstanpy
import logging
import argparse
from pathlib import Path
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def train_full_matchup_specific_model(
    data_path: str = "matchup_specific_bayesian_data_full.csv",
    stan_model: str = "bayesian_model_k8_matchup_specific.stan",
    draws: int = 2000,
    tune: int = 1000,
    chains: int = 4,
    adapt_delta: float = 0.99,  # Higher = stricter convergence
    output_dir: str = "stan_model_results_full_matchup"
):
    """Train the matchup-specific model on FULL dataset."""
    logger.info("="*80)
    logger.info("TRAINING FULL MATCHUP-SPECIFIC MODEL")
    logger.info("="*80)
    
    start_time = time.time()
    
    # Load FULL data
    logger.info(f"Loading FULL dataset from {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df):,} possessions (FULL DATASET)")
    logger.info(f"Unique matchups: {df['matchup_id'].nunique()}/36")
    
    # Prepare Stan data
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
    
    logger.info(f"\nData Summary:")
    logger.info(f"  Observations: {N:,}")
    logger.info(f"  Unique matchups: {df['matchup_id'].nunique()}/36")
    logger.info(f"  Parameters: 612")
    logger.info(f"  Obs/param: {N/612:.1f}")
    logger.info(f"  Z-off shape: {z_off.shape}")
    logger.info(f"  Z-def shape: {z_def.shape}")
    
    # Compile Stan model
    logger.info(f"\nCompiling Stan model...")
    model = cmdstanpy.CmdStanModel(stan_file=stan_model)
    logger.info("✅ Model compiled")
    
    # Run MCMC sampling (THIS WILL TAKE 30-40 HOURS)
    logger.info(f"\nStarting MCMC sampling:")
    logger.info(f"  Chains: {chains}")
    logger.info(f"  Warmup iterations: {tune}")
    logger.info(f"  Posterior samples: {draws}")
    logger.info(f"  Adapt delta: {adapt_delta}")
    logger.info(f"\n⚠️  EXPECTED TIME: 30-40 HOURS")
    logger.info(f"    This is normal for 612 parameters × 96K observations")
    
    sampling_start = time.time()
    
    fit = model.sample(
        data=stan_data,
        chains=chains,
        iter_warmup=tune,
        iter_sampling=draws,
        adapt_delta=adapt_delta,
        seed=42,
        show_progress=True
    )
    
    sampling_time = time.time() - sampling_start
    total_time = time.time() - start_time
    
    logger.info(f"\n✅ Sampling completed in {sampling_time/3600:.1f} hours")
    logger.info(f"✅ Total training time: {total_time/3600:.1f} hours")
    
    # Check diagnostics
    logger.info("\n" + "="*80)
    logger.info("DIAGNOSTICS")
    logger.info("="*80)
    
    diagnostics = fit.diagnose()
    logger.info(diagnostics)
    
    # Save results
    logger.info(f"\nSaving results to {output_dir}")
    Path(output_dir).mkdir(exist_ok=True)
    fit.save_csvfiles(dir=output_dir)
    logger.info(f"✅ Samples saved to {output_dir}/")
    
    # Extract coefficients
    logger.info("\nExtracting coefficient means...")
    beta_0 = fit.stan_variable('beta_0')
    beta_off = fit.stan_variable('beta_off')
    beta_def = fit.stan_variable('beta_def')
    
    beta_0_mean = np.mean(beta_0, axis=0)
    beta_off_mean = np.mean(beta_off, axis=0)
    beta_def_mean = np.mean(beta_def, axis=0)
    
    # Save coefficient CSV
    coefficients_df = []
    for matchup in range(36):
        row = {'matchup_id': matchup}
        row['beta_0'] = beta_0_mean[matchup]
        
        for arch in range(8):
            row[f'beta_off_{arch}'] = beta_off_mean[matchup, arch]
            row[f'beta_def_{arch}'] = beta_def_mean[matchup, arch]
        
        coefficients_df.append(row)
    
    coefficients_df = pd.DataFrame(coefficients_df)
    coefficients_path = f"{output_dir}/matchup_specific_coefficients_full.csv"
    coefficients_df.to_csv(coefficients_path, index=False)
    logger.info(f"✅ Coefficients saved to {coefficients_path}")
    logger.info(f"   Shape: {coefficients_df.shape} (36 matchups × 17 coefficients)")
    
    # Generate summary
    summary_path = f"{output_dir}/full_training_summary.txt"
    with open(summary_path, 'w') as f:
        f.write("FULL MATCHUP-SPECIFIC MODEL TRAINING SUMMARY\n")
        f.write("="*80 + "\n\n")
        f.write(f"Dataset: {data_path}\n")
        f.write(f"Observations: {len(df):,}\n")
        f.write(f"Unique Matchups: {df['matchup_id'].nunique()}/36\n")
        f.write(f"Parameters: 612 (36 × 16)\n")
        f.write(f"Training Time: {sampling_time/3600:.1f} hours\n")
        f.write(f"\nOutputs:\n")
        f.write(f"  Coefficients: {coefficients_path}\n")
        f.write(f"  Samples: {output_dir}/\n")
    
    logger.info(f"✅ Summary saved to {summary_path}")
    
    logger.info("\n" + "="*80)
    logger.info("✅ TRAINING COMPLETE!")
    logger.info("="*80)
    
    return fit

def main():
    parser = argparse.ArgumentParser(description="Train full matchup-specific model")
    parser.add_argument("--data", default="matchup_specific_bayesian_data_full.csv")
    parser.add_argument("--stan", default="bayesian_model_k8_matchup_specific.stan")
    parser.add_argument("--draws", type=int, default=2000)
    parser.add_argument("--tune", type=int, default=1000)
    parser.add_argument("--chains", type=int, default=4)
    parser.add_argument("--adapt-delta", type=float, default=0.99, dest="adapt_delta")
    parser.add_argument("--output", default="stan_model_results_full_matchup")
    
    args = parser.parse_args()
    
    success = train_full_matchup_specific_model(
        data_path=args.data,
        stan_model=args.stan,
        draws=args.draws,
        tune=args.tune,
        chains=args.chains,
        adapt_delta=args.adapt_delta,
        output_dir=args.output
    )
    
    if success:
        print("\n✅ Full matchup-specific model training completed!")
        print(f"📊 Results: {args.output}/")
        print(f"📈 Coefficients: {args.output}/matchup_specific_coefficients_full.csv")
    else:
        print("\n❌ Failed to train full matchup-specific model")
        exit(1)

if __name__ == "__main__":
    main()

