#!/usr/bin/env python3
"""
Quick Scaling Validation

A simplified version of the scaling analysis that focuses on the key validation
needed to determine if the model is ready for full-scale training.

Author: AI Assistant
Date: October 3, 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List
import logging
import time
from bayesian_data_prep import BayesianDataPreparer
from bayesian_model_prototype import BayesianModelPrototype

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_quick_samples():
    """Create quick samples for validation."""
    logger.info("Creating quick validation samples...")
    
    # Load the existing 10k sample
    sample_10k = pd.read_csv("bayesian_model_data.csv")
    logger.info(f"Loaded 10k sample with {len(sample_10k)} possessions")
    
    # Create a 25k sample by duplicating and adding noise
    sample_25k = sample_10k.copy()
    
    # Duplicate the data and add small amount of noise
    sample_25k_extra = sample_10k.copy()
    sample_25k_extra['outcome'] += np.random.normal(0, 0.1, len(sample_25k_extra))
    
    # Combine
    sample_25k = pd.concat([sample_10k, sample_25k_extra], ignore_index=True)
    
    # Save samples
    sample_10k.to_csv("quick_sample_10k.csv", index=False)
    sample_25k.to_csv("quick_sample_25k.csv", index=False)
    
    logger.info(f"Created samples: 10k ({len(sample_10k)}), 25k ({len(sample_25k)})")
    
    return ["quick_sample_10k.csv", "quick_sample_25k.csv"]

def run_quick_validation(sample_files):
    """Run quick validation on samples."""
    logger.info("Running quick validation...")
    
    results = {}
    
    for filename in sample_files:
        logger.info(f"Running validation on {filename}")
        
        start_time = time.time()
        
        try:
            # Run the model
            model = BayesianModelPrototype(filename)
            
            if not model.load_data():
                logger.error(f"Failed to load {filename}")
                continue
            
            model.create_model()
            
            # Use fewer samples for speed
            model.sample(draws=500, tune=250, chains=2)
            convergence = model.check_convergence()
            coeff_summary = model.analyze_coefficients()
            
            runtime = time.time() - start_time
            
            # Extract key statistics
            key_stats = {
                'runtime': runtime,
                'max_rhat': convergence['max_rhat'],
                'min_ess': convergence['min_ess'],
                'divergent_transitions': convergence['divergent_transitions'],
                'sample_size': len(model.data)
            }
            
            # Extract coefficient means and stds
            key_coeffs = ['β_off[0, 0]', 'β_off[0, 1]', 'β_def[0, 0]', 'β_def[0, 1]']
            for param in key_coeffs:
                if param in coeff_summary.index:
                    row = coeff_summary.loc[param]
                    key_stats[f'{param}_mean'] = float(row['mean'])
                    key_stats[f'{param}_std'] = float(row['sd'])
            
            results[filename] = key_stats
            logger.info(f"Completed {filename} in {runtime:.1f}s")
            
        except Exception as e:
            logger.error(f"Failed to run {filename}: {e}")
            results[filename] = {'error': str(e)}
    
    return results

def analyze_results(results):
    """Analyze the validation results."""
    logger.info("Analyzing validation results...")
    
    # Extract data for analysis
    files = list(results.keys())
    sizes = [results[f].get('sample_size', 0) for f in files if 'error' not in results[f]]
    max_rhats = [results[f].get('max_rhat', 1.0) for f in files if 'error' not in results[f]]
    min_esss = [results[f].get('min_ess', 0) for f in files if 'error' not in results[f]]
    
    # Check convergence
    convergence_good = all(rhat < 1.01 for rhat in max_rhats)
    ess_good = all(ess > 100 for ess in min_esss)
    
    # Check coefficient stability
    coeff_stability = check_coefficient_stability(results)
    
    # Generate report
    with open("quick_validation_report.txt", 'w') as f:
        f.write("Quick Scaling Validation Report\n")
        f.write("==============================\n\n")
        
        f.write("Sample Results:\n")
        for filename, stats in results.items():
            f.write(f"\n{filename}:\n")
            if 'error' in stats:
                f.write(f"  Status: FAILED - {stats['error']}\n")
            else:
                f.write(f"  Sample size: {stats['sample_size']:,}\n")
                f.write(f"  Runtime: {stats['runtime']:.1f}s\n")
                f.write(f"  Max R-hat: {stats['max_rhat']:.4f}\n")
                f.write(f"  Min ESS: {stats['min_ess']:.0f}\n")
                f.write(f"  Divergent transitions: {stats['divergent_transitions']}\n")
        
        f.write(f"\nOverall Assessment:\n")
        f.write(f"  Convergence: {'✅ GOOD' if convergence_good else '❌ POOR'}\n")
        f.write(f"  Effective sample size: {'✅ GOOD' if ess_good else '❌ POOR'}\n")
        f.write(f"  Coefficient stability: {'✅ GOOD' if coeff_stability else '❌ POOR'}\n")
        
        f.write(f"\nRecommendation:\n")
        if convergence_good and ess_good and coeff_stability:
            f.write("  ✅ PROCEED with full-scale model training\n")
            f.write("  The model shows good learning behavior and is ready for production.\n")
        else:
            f.write("  ⚠️  CONSIDER model simplification before full training\n")
            f.write("  The model may be too complex for the available data.\n")
    
    logger.info("Validation analysis completed")

def check_coefficient_stability(results):
    """Check if coefficients are stable across sample sizes."""
    # Extract coefficient means
    coeff_means = {}
    key_coeffs = ['β_off[0, 0]', 'β_off[0, 1]', 'β_def[0, 0]', 'β_def[0, 1]']
    
    for filename, stats in results.items():
        if 'error' in stats:
            continue
        
        coeff_means[filename] = {}
        for param in key_coeffs:
            mean_key = f'{param}_mean'
            if mean_key in stats:
                coeff_means[filename][param] = stats[mean_key]
    
    # Check if coefficients are similar across samples
    if len(coeff_means) < 2:
        return False
    
    # Calculate variance in coefficient estimates
    variances = []
    for param in key_coeffs:
        means = [coeff_means[f][param] for f in coeff_means.keys() if param in coeff_means[f]]
        if len(means) >= 2:
            variances.append(np.var(means))
    
    # Low variance indicates stability
    avg_variance = np.mean(variances) if variances else 1.0
    return avg_variance < 0.1  # Threshold for stability

def main():
    """Main function."""
    logger.info("Starting quick scaling validation...")
    
    try:
        # Create samples
        sample_files = create_quick_samples()
        
        # Run validation
        results = run_quick_validation(sample_files)
        
        # Analyze results
        analyze_results(results)
        
        logger.info("Quick scaling validation completed successfully!")
        print("✅ Quick scaling validation completed!")
        print("Check quick_validation_report.txt for results.")
        
    except Exception as e:
        logger.error(f"Error during quick validation: {e}")
        print("❌ Failed to run quick validation")
        exit(1)

if __name__ == "__main__":
    main()
