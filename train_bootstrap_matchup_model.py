#!/usr/bin/env python3
"""
Train Matchup-Specific Bayesian Model with Bootstrap Superclusters

This script trains the matchup-specific Bayesian model using the complete 2022-23 dataset
with bootstrap superclusters that provide 100% coverage and no filtering losses.

Methodology:
1. Load the complete Bayesian dataset (982K examples, 33 matchups)
2. Train matchup-specific Stan model (33 matchups × 16 parameters = 528 total)
3. Validate convergence and extract coefficients
4. Compare performance against simplified model

This implements the original paper's approach but with complete data coverage.
"""

import os
import pandas as pd
import numpy as np
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_bayesian_data(data_path='production_bayesian_data.csv'):
    """Load the Bayesian training data."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Training data not found: {data_path}")

    logging.info(f"Loading training data from {data_path}")
    df = pd.read_csv(data_path)

    logging.info(f"Loaded {len(df):,} training examples")
    logging.info(f"Columns: {list(df.columns)}")
    logging.info(f"Unique matchups: {df['matchup_id'].nunique()}")
    logging.info(f"Matchup distribution:\n{df['matchup_id'].value_counts().head()}")

    return df

def prepare_stan_data(df):
    """Prepare data for Stan model."""
    # Extract matchup indices from matchup_id strings like "2_vs_3"
    matchup_to_idx = {}
    idx = 0

    for matchup_str in sorted(df['matchup_id'].unique()):
        off_sc, def_sc = map(int, matchup_str.split('_vs_'))
        matchup_to_idx[matchup_str] = idx
        idx += 1

    # Convert matchup strings to indices
    df['matchup_idx'] = df['matchup_id'].map(matchup_to_idx)

    # Prepare Stan data
    N = len(df)  # number of observations
    M = len(matchup_to_idx)  # number of matchups (should be ~36)

    # Outcome variable
    y = df['outcome'].values

    # Matchup indices (0-based for Stan)
    matchup_id = df['matchup_idx'].values.astype(int)

    # Archetype features (z_off_0 to z_off_7, z_def_0 to z_def_7)
    z_off = df[[f'z_off_{i}' for i in range(8)]].values
    z_def = df[[f'z_def_{i}' for i in range(8)]].values

    stan_data = {
        'N': N,
        'M': M,
        'K': 8,  # number of archetypes
        'y': y,
        'matchup_id': matchup_id + 1,  # Stan uses 1-based indexing
        'z_off': z_off,
        'z_def': z_def
    }

    logging.info(f"Prepared Stan data:")
    logging.info(f"  - N (observations): {N:,}")
    logging.info(f"  - M (matchups): {M}")
    logging.info(f"  - K (archetypes): {stan_data['K']}")
    logging.info(f"  - Parameters: {M} × {stan_data['K'] * 2} = {M * stan_data['K'] * 2}")

    return stan_data, matchup_to_idx

def create_stan_model():
    """Create the matchup-specific Stan model."""
    stan_code = """
data {
    int<lower=1> N;           // number of observations
    int<lower=1> M;           // number of matchups
    int<lower=1> K;           // number of archetypes
    vector[N] y;              // outcome (net points)
    int<lower=1,upper=M> matchup_id[N];  // matchup index for each observation
    matrix[N,K] z_off;        // offensive archetype aggregates
    matrix[N,K] z_def;        // defensive archetype aggregates
}

parameters {
    real beta_0[M];           // matchup-specific intercepts
    matrix<lower=0>[M,K] beta_off;  // offensive coefficients (positive)
    matrix<lower=0>[M,K] beta_def;  // defensive coefficients (positive)
    real<lower=0> sigma;      // residual standard deviation
}

model {
    // Priors
    beta_0 ~ normal(0, 1);
    for (m in 1:M) {
        beta_off[m] ~ normal(0, 0.5);  // Weak positive prior
        beta_def[m] ~ normal(0, 0.5);  // Weak positive prior
    }
    sigma ~ normal(0, 1);

    // Likelihood
    for (n in 1:N) {
        int m = matchup_id[n];
        real mu = beta_0[m];

        // Add archetype contributions
        for (k in 1:K) {
            mu += beta_off[m,k] * z_off[n,k] - beta_def[m,k] * z_def[n,k];
        }

        y[n] ~ normal(mu, sigma);
    }
}

generated quantities {
    // Log likelihood for model comparison
    vector[N] log_lik;
    for (n in 1:N) {
        int m = matchup_id[n];
        real mu = beta_0[m];

        for (k in 1:K) {
            mu += beta_off[m,k] * z_off[n,k] - beta_def[m,k] * z_def[n,k];
        }

        log_lik[n] = normal_lpdf(y[n] | mu, sigma);
    }
}
"""

    # Save Stan model
    model_path = 'bootstrap_matchup_model.stan'
    with open(model_path, 'w') as f:
        f.write(stan_code)

    logging.info(f"Created Stan model: {model_path}")
    return model_path

def train_model(stan_data, stan_model_path, output_dir='stan_model_results_bootstrap'):
    """Train the Bayesian model using CmdStanPy."""
    try:
        import cmdstanpy
    except ImportError:
        raise ImportError("cmdstanpy not installed. Run: pip install cmdstanpy")

    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)

    # Compile model
    logging.info("Compiling Stan model...")
    model = cmdstanpy.CmdStanModel(stan_file=stan_model_path)

    # Training configuration (similar to original paper)
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
    coeff_path = f"{output_dir}/bootstrap_matchup_coefficients.csv"
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
    # Get posterior means
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
                'mean': row['Mean'],
                'std': row['StdDev'],
                'r_hat': row['R_hat'],
                'ess': row['ESS']
            })

    # Extract beta_off
    for m in range(M):
        for k in range(K):
            param_name = f'beta_off[{m+1},{k+1}]'
            if param_name in summary.index:
                row = summary.loc[param_name]
                coefficients.append({
                    'parameter': f'beta_off_matchup_{m}_arch_{k}',
                    'matchup': m,
                    'archetype': k,
                    'skill_type': 'offensive',
                    'mean': row['Mean'],
                    'std': row['StdDev'],
                    'r_hat': row['R_hat'],
                    'ess': row['ESS']
                })

    # Extract beta_def
    for m in range(M):
        for k in range(K):
            param_name = f'beta_def[{m+1},{k+1}]'
            if param_name in summary.index:
                row = summary.loc[param_name]
                coefficients.append({
                    'parameter': f'beta_def_matchup_{m}_arch_{k}',
                    'matchup': m,
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

    logging.info(f"Convergence diagnostics:")
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
    logging.info("="*80)
    logging.info("TRAINING BOOTSTRAP MATCHUP-SPECIFIC MODEL")
    logging.info("="*80)

    # Load training data
    df = load_bayesian_data()

    # Prepare Stan data
    stan_data, matchup_mapping = prepare_stan_data(df)

    # Create Stan model
    stan_model_path = create_stan_model()

    # Train model
    logging.info("\nStarting model training...")
    fit, coefficients = train_model(stan_data, stan_model_path)

    # Summary
    logging.info("\n" + "="*80)
    logging.info("BOOTSTRAP MODEL TRAINING COMPLETE")
    logging.info("="*80)

    logging.info("\nModel Summary:")
    logging.info(f"  - Training examples: {len(df):,}")
    logging.info(f"  - Matchups: {stan_data['M']}")
    logging.info(f"  - Archetypes: {stan_data['K']}")
    logging.info(f"  - Total parameters: {len(coefficients)}")
    logging.info(f"  - Coefficients saved: {len(coefficients)} rows")

    # Validate we have the expected number of parameters
    expected_params = stan_data['M'] * (1 + 2 * stan_data['K'])  # intercepts + off + def
    actual_params = len(coefficients)
    logging.info(f"  - Expected parameters: {expected_params}")
    logging.info(f"  - Actual parameters: {actual_params}")

    if actual_params == expected_params:
        logging.info("  ✅ Parameter count matches expectations")
    else:
        logging.warning(f"  ⚠️  Parameter count mismatch: expected {expected_params}, got {actual_params}")

    logging.info("\n🎉 Bootstrap matchup-specific model trained successfully!")
    logging.info("Next steps:")
    logging.info("  1. Validate model performance against simplified model")
    logging.info("  2. Test on 2022-23 holdout data")
    logging.info("  3. Compare predictions for Lakers/Pacers/Suns cases")

if __name__ == '__main__':
    main()
