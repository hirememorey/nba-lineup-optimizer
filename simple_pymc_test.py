#!/usr/bin/env python3
"""
Simple PyMC Model Test

This script runs a quick test of the PyMC model on the available data
to check for basic functionality and performance.
"""

import os
import sys
import time
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

try:
    import pymc as pm
    import arviz as az
    from bayesian_model_prototype import BayesianModelPrototype
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

def main():
    print("Simple PyMC Model Test")
    print("=" * 30)
    
    # Load the available data
    data_path = "production_bayesian_data.csv"
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found")
        return
    
    print(f"Loading data from {data_path}...")
    data = pd.read_csv(data_path)
    print(f"Loaded {len(data):,} possessions")
    
    # Check data structure
    print(f"Columns: {list(data.columns)}")
    print(f"Unique matchups: {data['matchup'].nunique()}")
    print(f"Matchup distribution:")
    print(data['matchup'].value_counts())
    
    # Test with a small sample first
    sample_size = min(5000, len(data))
    print(f"\nTesting with {sample_size:,} possessions...")
    
    sample_data = data.sample(n=sample_size, random_state=42)
    
    # Initialize model
    print("Initializing model...")
    model = BayesianModelPrototype()
    model.data = sample_data
    
    # Create and run model
    print("Creating model...")
    start_time = time.time()
    
    try:
        with model.create_model():
            print("Model created successfully")
            
            # Run a very short sampling for testing
            print("Running MCMC sampling...")
            with model.model:
                trace = pm.sample(
                    draws=100,  # Very short for testing
                    tune=50,    # Very short for testing
                    chains=2,
                    cores=1,
                    random_seed=42,
                    progressbar=True,
                    return_inferencedata=True
                )
        
        runtime = time.time() - start_time
        print(f"Sampling completed in {runtime:.1f} seconds")
        
        # Check diagnostics
        summary = az.summary(trace)
        print(f"\nDiagnostics:")
        print(f"Max R-hat: {summary['r_hat'].max():.3f}")
        print(f"Min ESS: {summary['ess_bulk'].min():.0f}")
        
        # Check for divergent transitions
        if hasattr(trace.posterior, 'diverging'):
            divergences = trace.posterior.diverging.sum().item()
            print(f"Divergent transitions: {divergences}")
        
        print("\n✓ Model test completed successfully!")
        
        # Now test with full dataset
        print(f"\nTesting with full dataset ({len(data):,} possessions)...")
        model.data = data
        
        with model.create_model():
            print("Full model created successfully")
            
            # Run a short sampling on full data
            print("Running MCMC sampling on full data...")
            start_time = time.time()
            
            with model.model:
                trace_full = pm.sample(
                    draws=200,
                    tune=100,
                    chains=2,
                    cores=1,
                    random_seed=42,
                    progressbar=True,
                    return_inferencedata=True
                )
            
            runtime = time.time() - start_time
            print(f"Full data sampling completed in {runtime:.1f} seconds")
            
            # Check diagnostics
            summary_full = az.summary(trace_full)
            print(f"\nFull data diagnostics:")
            print(f"Max R-hat: {summary_full['r_hat'].max():.3f}")
            print(f"Min ESS: {summary_full['ess_bulk'].min():.0f}")
            
            if hasattr(trace_full.posterior, 'diverging'):
                divergences = trace_full.posterior.diverging.sum().item()
                print(f"Divergent transitions: {divergences}")
            
            print("\n✓ Full data test completed successfully!")
            
    except Exception as e:
        print(f"Error during model execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
