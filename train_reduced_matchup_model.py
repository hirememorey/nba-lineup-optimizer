#!/usr/bin/env python3
"""
Train Reduced Parameter Matchup-Specific Bayesian Model

This script trains the reduced parameter matchup-specific model with:
- 36 matchup intercepts (one per matchup)
- 16 global archetype effects (8 offensive + 8 defensive)
- Total: 52 parameters (vs 612 in full model)

This maintains matchup awareness while ensuring parameter identifiability.
"""

import os
import pandas as pd
import numpy as np
import logging
import argparse
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_bayesian_data(data_path='bayesian_data_2022_23_continuous.csv'):
    """Load the Bayesian training data."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Training data not found: {data_path}")

    logging.info(f"Loading training data from {data_path}")
    df = pd.read_csv(data_path)

    logging.info(f"Loaded {len(df):,} training examples")
    logging.info(f"Columns: {list(df.columns)}")
    logging.info(f"Unique matchups: {df['matchup_id'].nunique()}")
    logging.info(f"Matchup distribution:\n{df['matchup_id'].value_counts().head()}")
    logging.info(f"Sample matchup_ids: {sorted(df['matchup_id'].unique())[:5]}...")

    return df

def prepare_stan_data(df):
    """Prepare data for the reduced parameter Stan model."""
    # Create matchup mapping (string -> index)
    matchup_to_idx = {}
    idx = 0

    for matchup_str in sorted(df['matchup_id'].unique()):
        matchup_to_idx[matchup_str] = idx
        idx += 1

    # Convert matchup strings to indices
    df['matchup_idx'] = df['matchup_id'].map(matchup_to_idx)

    # Verify we have reasonable matchup coverage
    matchup_counts = df['matchup_idx'].value_counts().sort_index()
    logging.info(f"Matchup coverage: min={matchup_counts.min()}, max={matchup_counts.max()}, total_matchups={len(matchup_counts)}")

    # Prepare Stan data
    N = len(df)  # number of observations
    M = len(matchup_to_idx)  # number of matchups (should be ~33-36)
    K = 8  # number of archetypes

    # Outcome variable
    y = df['outcome'].values

    # Matchup indices (0-based for Stan)
    matchup_id = df['matchup_idx'].values.astype(int)

    # Archetype features (z_off_0 to z_off_7, z_def_0 to z_def_7)
    z_off = df[[f'z_off_{i}' for i in range(K)]].values
    z_def = df[[f'z_def_{i}' for i in range(K)]].values

    stan_data = {
        'N': N,
        'M': M,
        'K': K,
        'y': y,
        'matchup_id': matchup_id,  # 0-based indexing for Stan
        'z_off': z_off,
        'z_def': z_def
    }

    logging.info("Prepared Stan data:")
    logging.info(f"  - N (observations): {N:,}")
    logging.info(f"  - M (matchups): {M}")
    logging.info(f"  - K (archetypes): {K}")
    logging.info(f"  - Total parameters: {M + 2*K} (intercepts + global effects)")

    return stan_data, matchup_to_idx

def create_reduced_stan_model():
    """Create the reduced parameter matchup-specific Stan model."""
    stan_code = """
// Reduced Parameter Matchup-Specific Model
// 36 matchup intercepts + 16 global archetype effects = 52 total parameters

data {
    int<lower=1> N;              // number of observations
    int<lower=1> M;              // number of matchups
    int<lower=1> K;              // number of archetypes
    vector[N] y;                 // outcome (net points)
    array[N] int<lower=0, upper=M-1> matchup_id;  // matchup index (0-based)
    matrix[N,K] z_off;           // offensive archetype aggregates
    matrix[N,K] z_def;           // defensive archetype aggregates
}

parameters {
    vector[M] beta_0;                    // matchup-specific intercepts
    vector<lower=0>[K] beta_off_global;  // global offensive archetype effects
    vector<lower=0>[K] beta_def_global;  // global defensive archetype effects
    real<lower=0> sigma;                 // residual standard deviation
}

model {
    // Weakly informative priors
    beta_0 ~ normal(0, 5);
    beta_off_global ~ normal(0, 5);
    beta_def_global ~ normal(0, 5);
    sigma ~ cauchy(0, 2.5);

    // Likelihood with global archetype effects
    for (n in 1:N) {
        int m = matchup_id[n] + 1;  // Convert to 1-based for vector indexing
        real mu = beta_0[m] +
                 dot_product(z_off[n], beta_off_global) -
                 dot_product(z_def[n], beta_def_global);
        y[n] ~ normal(mu, sigma);
    }
}

generated quantities {
    vector[N] log_lik;
    vector[N] y_pred;

    for (n in 1:N) {
        int m = matchup_id[n] + 1;
        real mu = beta_0[m] +
                 dot_product(z_off[n], beta_off_global) -
                 dot_product(z_def[n], beta_def_global);

        log_lik[n] = normal_lpdf(y[n] | mu, sigma);
        y_pred[n] = normal_rng(mu, sigma);
    }
}
"""

    # Save Stan model
    model_path = 'reduced_matchup_model.stan'
    with open(model_path, 'w') as f:
        f.write(stan_code)

    logging.info(f"Created reduced parameter Stan model: {model_path}")
    return model_path

def train_model(stan_data, stan_model_path, output_dir='stan_model_results_reduced'):
    """Train the reduced parameter Bayesian model using CmdStanPy."""
    try:
        import cmdstanpy
    except ImportError:
        raise ImportError("cmdstanpy not installed. Run: pip install cmdstanpy")

    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)

    # Compile model
    logging.info("Compiling reduced parameter Stan model...")
    model = cmdstanpy.CmdStanModel(stan_file=stan_model_path)

    # Training configuration (conservative for convergence)
    logging.info("Starting MCMC sampling...")
    logging.info("Configuration: 4 chains, 1000 warmup, 2000 sampling iterations")

    fit = model.sample(
        data=stan_data,
        chains=4,
        iter_warmup=1000,
        iter_sampling=2000,
        adapt_delta=0.95,  # Conservative for convergence
        max_treedepth=12,
        output_dir=output_dir,
        show_progress=True
    )

    # Save summary
    summary_path = f"{output_dir}/model_summary.txt"
    with open(summary_path, 'w') as f:
        f.write(str(fit.summary()))
    logging.info(f"Saved model summary to {summary_path}")

    # Extract coefficients
    coefficients = extract_coefficients(fit, stan_data['M'], stan_data['K'])
    coeff_path = f"{output_dir}/reduced_matchup_coefficients.csv"
    coefficients.to_csv(coeff_path, index=False)
    logging.info(f"Saved coefficients to {coeff_path}")

    # Check convergence
    convergence_ok = check_convergence(fit)
    if convergence_ok:
        logging.info("✅ Model converged successfully!")
    else:
        logging.warning("⚠️  Model may not have fully converged")

    return fit, coefficients

def extract_coefficients(fit, M, K):
    """Extract and organize model coefficients."""
    summary = fit.summary()

    coefficients = []

    # Extract beta_0 (intercepts)
    for m in range(M):
        param_name = f'beta_0[{m+1}]'
        if param_name in summary.index:
            row = summary.loc[param_name]
            coefficients.append({
                'parameter': f'beta_0_matchup_{m}',
                'matchup': m,
                'archetype': 'intercept',
                'skill_type': 'intercept',
                'mean': row['Mean'],
                'std': row['StdDev'],
                'r_hat': row['R_hat'],
                'ess': row['ESS']
            })

    # Extract beta_off_global
    for k in range(K):
        param_name = f'beta_off_global[{k+1}]'
        if param_name in summary.index:
            row = summary.loc[param_name]
            coefficients.append({
                'parameter': f'beta_off_global_arch_{k}',
                'matchup': 'global',
                'archetype': k,
                'skill_type': 'offensive',
                'mean': row['Mean'],
                'std': row['StdDev'],
                'r_hat': row['R_hat'],
                'ess': row['ESS']
            })

    # Extract beta_def_global
    for k in range(K):
        param_name = f'beta_def_global[{k+1}]'
        if param_name in summary.index:
            row = summary.loc[param_name]
            coefficients.append({
                'parameter': f'beta_def_global_arch_{k}',
                'matchup': 'global',
                'archetype': k,
                'skill_type': 'defensive',
                'mean': row['Mean'],
                'std': row['StdDev'],
                'r_hat': row['R_hat'],
                'ess': row['ESS']
            })

    return pd.DataFrame(coefficients)

def check_convergence(fit):
    """Check model convergence diagnostics."""
    summary = fit.summary()

    # Check R-hat values
    max_rhat = summary['R_hat'].max()
    bad_rhat = (summary['R_hat'] > 1.01).sum()

    # Check ESS values
    min_ess = summary['ESS'].min()
    low_ess = (summary['ESS'] < 400).sum()

    logging.info("Convergence diagnostics:")
    logging.info(f"  - Max R-hat: {max_rhat:.3f} (should be < 1.01)")
    logging.info(f"  - Parameters with R-hat > 1.01: {bad_rhat}")
    logging.info(f"  - Min ESS: {min_ess:.0f} (should be > 400)")
    logging.info(f"  - Parameters with ESS < 400: {low_ess}")

    # Check for divergent transitions
    if hasattr(fit, 'sampler_diagnostics'):
        try:
            diagnostics = fit.sampler_diagnostics()
            if 'divergent__' in diagnostics:
                divergent = diagnostics['divergent__'].sum()
                logging.info(f"  - Divergent transitions: {divergent}")
                if divergent > 0:
                    logging.warning(f"⚠️  {divergent} divergent transitions detected")
        except:
            pass

    # Overall assessment
    convergence_ok = (max_rhat < 1.01) and (min_ess > 400) and (bad_rhat == 0)
    return convergence_ok

def main():
    parser = argparse.ArgumentParser(description='Train reduced parameter matchup-specific model')
    parser.add_argument('--output-dir', type=str, default='stan_model_results_reduced',
                       help='Directory to save model results (default: stan_model_results_reduced)')
    args = parser.parse_args()

    logging.info("="*80)
    logging.info("TRAINING REDUCED PARAMETER MATCHUP-SPECIFIC MODEL")
    logging.info("="*80)

    # Load training data
    df = load_bayesian_data()

    # Prepare Stan data
    stan_data, matchup_mapping = prepare_stan_data(df)

    # Create Stan model
    stan_model_path = create_reduced_stan_model()

    # Train model
    logging.info("\nStarting model training...")
    fit, coefficients = train_model(stan_data, stan_model_path, output_dir=args.output_dir)

    # Summary
    logging.info("\n" + "="*80)
    logging.info("REDUCED MODEL TRAINING COMPLETE")
    logging.info("="*80)

    logging.info("\nModel Summary:")
    logging.info(f"  - Training examples: {len(df):,}")
    logging.info(f"  - Matchups: {stan_data['M']}")
    logging.info(f"  - Archetypes: {stan_data['K']}")
    logging.info(f"  - Total parameters: {len(coefficients)}")
    logging.info(f"  - Coefficients saved: {len(coefficients)} rows")

    # Validate we have the expected number of parameters
    expected_params = stan_data['M'] + 2 * stan_data['K']  # intercepts + off + def
    actual_params = len(coefficients)
    logging.info(f"  - Expected parameters: {expected_params}")
    logging.info(f"  - Actual parameters: {actual_params}")

    if actual_params == expected_params:
        logging.info("  ✅ Parameter count matches expectations")
    else:
        logging.warning(f"  ⚠️  Parameter count mismatch: expected {expected_params}, got {actual_params}")

    # Save matchup mapping for later use
    matchup_df = pd.DataFrame([
        {'matchup_id': k, 'matchup_idx': v, 'count': df[df['matchup_id'] == k].shape[0]}
        for k, v in matchup_mapping.items()
    ])
    matchup_df.to_csv(f'{args.output_dir}/matchup_mapping.csv', index=False)
    logging.info("Saved matchup mapping for reference")

    logging.info("\n🎉 Reduced parameter matchup-specific model trained successfully!")
    logging.info("Next steps:")
    logging.info("  1. Validate model performance against simplified model")
    logging.info("  2. Test on 2022-23 holdout data")
    logging.info("  3. Check if global archetype effects provide meaningful insights")

if __name__ == '__main__':
    main()

