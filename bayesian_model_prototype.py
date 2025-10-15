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
import cmdstanpy
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

STAN_MODEL_PATH = "bayesian_model_k8.stan"
SAMPLE_DATA_PATH = "stratified_sample_10k.csv"

def run_bayesian_prototype():
    """
    Trains the Bayesian model on a single matchup from the stratified sample.
    """
    logging.info("--- Running Bayesian Model Prototype ---")

    # 1. Check for Stan installation
    try:
        # Check if cmdstan is installed and located, if not, install it
        cmdstanpy.install_cmdstan(overwrite=False, verbose=True)
    except Exception as e:
        logging.error(f"Failed to install or find cmdstan. Please install it manually. Error: {e}")
        logging.error("See: https://mc-stan.org/cmdstanpy/installation.html")
        return

    # 2. Load and prepare data
    logging.info(f"Loading sample data from {SAMPLE_DATA_PATH}...")
    try:
        df = pd.read_csv(SAMPLE_DATA_PATH)
    except FileNotFoundError:
        logging.error(f"Sample data file not found at '{SAMPLE_DATA_PATH}'.")
        logging.error("Please run 'bayesian_data_prep.py' first.")
        return

    # Filter for the most frequent matchup to ensure sufficient rows
    if 'matchup_id' not in df.columns:
        logging.error("Column 'matchup_id' not found in sample data.")
        return

    matchup_to_prototype = (
        df['matchup_id'].value_counts().idxmax() if not df.empty else None
    )
    if matchup_to_prototype is None:
        logging.error("Sample data is empty; cannot select a matchup.")
        return

    df_matchup = df[df['matchup_id'] == matchup_to_prototype].copy()
    logging.info(f"Selected prototype matchup '{matchup_to_prototype}' with {len(df_matchup)} possessions.")

    # Prepare data for Stan
    z_off_cols = [f"z_off_{i}" for i in range(8)]
    z_def_cols = [f"z_def_{i}" for i in range(8)]
    
    stan_data = {
        "N": len(df_matchup),
        "y": df_matchup["outcome"].values,
        "z_off": df_matchup[z_off_cols].values,
        "z_def": df_matchup[z_def_cols].values
    }

    # 3. Compile the Stan model
    logging.info(f"Compiling Stan model from {STAN_MODEL_PATH}...")
    try:
        model = cmdstanpy.CmdStanModel(stan_file=STAN_MODEL_PATH)
        logging.info("Model compiled successfully.")
    except Exception as e:
        logging.error(f"Failed to compile Stan model. Error: {e}")
        return

    # 4. Run the MCMC sampler
    logging.info("Running MCMC sampler (this may take a few minutes)...")
    try:
        # Use fewer iterations for the prototype to get fast feedback
        fit = model.sample(
            data=stan_data,
            chains=4,
            parallel_chains=4,
            iter_warmup=500,
            iter_sampling=500,
            show_progress=True
        )
        logging.info("Sampling complete.")
    except Exception as e:
        logging.error(f"Failed during MCMC sampling. Error: {e}")
        return
        
    # 5. Display results
    logging.info("--- Model Results Summary ---")
    print(fit.summary())
    
    # Save the summary to a file for review
    fit.summary().to_csv("bayesian_model_prototype_summary.csv")
    logging.info("Saved model summary to 'bayesian_model_prototype_summary.csv'")

    logging.info("--- Bayesian Model Prototype Complete ---")
    logging.info("Check the summary to ensure coefficients are positive and the model has converged (R_hat ~ 1.0).")

if __name__ == "__main__":
    run_bayesian_prototype()
