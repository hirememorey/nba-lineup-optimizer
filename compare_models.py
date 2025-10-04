#!/usr/bin/env python3
"""
Model Comparison Script

This script compares the results from PyMC and Stan models to validate
that they produce similar results on the same data.
"""

import pandas as pd
import numpy as np
import json

def compare_models():
    """Compare PyMC and Stan model results."""
    print("Model Comparison: PyMC vs Stan")
    print("=" * 40)
    
    # Load PyMC results
    print("\n1. Loading PyMC results...")
    pymc_report = {}
    with open('bayesian_model_report.txt', 'r') as f:
        lines = f.readlines()
        for line in lines:
            if 'Max R-hat:' in line:
                pymc_report['max_rhat'] = float(line.split(':')[1].strip())
            elif 'Min ESS:' in line:
                pymc_report['min_ess'] = float(line.split(':')[1].strip())
            elif 'Divergent transitions:' in line:
                pymc_report['divergent'] = int(line.split(':')[1].strip())
    
    # Load Stan results
    print("2. Loading Stan results...")
    stan_report = {}
    with open('stan_model_report.txt', 'r') as f:
        lines = f.readlines()
        for line in lines:
            if 'Max R-hat:' in line:
                stan_report['max_rhat'] = float(line.split(':')[1].strip())
            elif 'Min ESS:' in line:
                stan_report['min_ess'] = float(line.split(':')[1].strip())
            elif 'Divergent transitions:' in line:
                stan_report['divergent'] = int(line.split(':')[1].strip())
    
    # Load Stan convergence diagnostics
    with open('stan_model_results/convergence_diagnostics.json', 'r') as f:
        stan_convergence = json.load(f)
    
    print("\n3. Convergence Comparison:")
    print(f"PyMC  - Max R-hat: {pymc_report['max_rhat']:.4f}, Min ESS: {pymc_report['min_ess']:.0f}, Divergent: {pymc_report['divergent']}")
    print(f"Stan  - Max R-hat: {stan_convergence['max_rhat']:.4f}, Min ESS: {stan_convergence['min_ess']:.0f}, Divergent: {stan_convergence['divergent_transitions']}")
    
    # Check if both models converged
    pymc_converged = pymc_report['max_rhat'] < 1.01 and pymc_report['min_ess'] > 100
    stan_converged = stan_convergence['max_rhat'] < 1.01 and stan_convergence['min_ess'] > 100
    
    print(f"\n4. Convergence Status:")
    print(f"PyMC converged: {'✅' if pymc_converged else '❌'}")
    print(f"Stan converged: {'✅' if stan_converged else '❌'}")
    
    # Load coefficient data for comparison
    print("\n5. Coefficient Comparison:")
    
    # Load PyMC coefficients (from the report)
    pymc_coeffs = {}
    with open('bayesian_model_report.txt', 'r') as f:
        lines = f.readlines()
        in_coeffs = False
        for line in lines:
            if 'Coefficient Analysis:' in line:
                in_coeffs = True
                continue
            if in_coeffs and line.strip() and not line.startswith(' '):
                if 'β_0[' in line or 'β_off[' in line or 'β_def[' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        param = parts[0]
                        try:
                            mean = float(parts[1])
                            pymc_coeffs[param] = mean
                        except ValueError:
                            # Skip lines that don't have valid float values
                            continue
    
    # Load Stan coefficients
    stan_df = pd.read_csv('stan_model_results/model_summary.csv', index_col=0)
    stan_coeffs = {}
    
    # Map Stan parameter names to PyMC names
    for idx, row in stan_df.iterrows():
        if 'beta_0[' in idx:
            # Convert beta_0[1] to β_0[0] (0-indexed)
            num = int(idx.split('[')[1].split(']')[0]) - 1
            pymc_name = f"β_0[{num}]"
            stan_coeffs[pymc_name] = row['Mean']
        elif 'beta_off[' in idx:
            # Convert beta_off[1,1] to β_off[0,0]
            coords = idx.split('[')[1].split(']')[0].split(',')
            m = int(coords[0]) - 1
            a = int(coords[1]) - 1
            pymc_name = f"β_off[{m}, {a}]"
            stan_coeffs[pymc_name] = row['Mean']
        elif 'beta_def[' in idx:
            # Convert beta_def[1,1] to β_def[0,0]
            coords = idx.split('[')[1].split(']')[0].split(',')
            m = int(coords[0]) - 1
            a = int(coords[1]) - 1
            pymc_name = f"β_def[{m}, {a}]"
            stan_coeffs[pymc_name] = row['Mean']
    
    # Compare coefficients
    print("\n6. Coefficient Values Comparison:")
    print("Parameter".ljust(20) + "PyMC".ljust(12) + "Stan".ljust(12) + "Diff".ljust(12) + "Match")
    print("-" * 70)
    
    matches = 0
    total = 0
    
    for param in sorted(pymc_coeffs.keys()):
        if param in stan_coeffs:
            pymc_val = pymc_coeffs[param]
            stan_val = stan_coeffs[param]
            diff = abs(pymc_val - stan_val)
            relative_diff = diff / abs(pymc_val) if pymc_val != 0 else diff
            
            # Consider a match if relative difference < 20% or absolute difference < 0.01
            is_match = relative_diff < 0.2 or diff < 0.01
            if is_match:
                matches += 1
            total += 1
            
            status = "✅" if is_match else "❌"
            print(f"{param:<20}{pymc_val:<12.4f}{stan_val:<12.4f}{diff:<12.4f}{status}")
    
    print(f"\n7. Overall Assessment:")
    print(f"Parameter matches: {matches}/{total} ({100*matches/total:.1f}%)")
    
    if matches/total > 0.8 and pymc_converged and stan_converged:
        print("✅ MODELS ARE COMPATIBLE - Both converged and coefficients are similar")
        return True
    else:
        print("❌ MODELS DIFFER - Check for implementation issues")
        return False

if __name__ == "__main__":
    success = compare_models()
    if success:
        print("\n🎉 Stan model validation successful!")
    else:
        print("\n⚠️  Stan model validation failed!")
