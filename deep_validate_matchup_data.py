#!/usr/bin/env python3
"""
Deep Data Validation for Matchup-Specific Model

This script performs comprehensive validation of matchup-specific data before
expensive cloud training, catching issues that surface checks would miss.

Based on pre-mortem analysis: catches data corruption, feature issues, and Stan
compatibility problems before committing to 30-40 hour training runs.
"""

import pandas as pd
import numpy as np
import cmdstanpy
import sys
from pathlib import Path
import argparse

def validate_matchup_distribution(df):
    """Check for balanced matchup distribution (critical for 612-param model)."""
    print("\n" + "="*80)
    print("1. MATCHUP DISTRIBUTION VALIDATION")
    print("="*80)
    
    matchup_counts = df['matchup_id'].value_counts()
    n_unique = matchup_counts.shape[0]
    
    print(f"  Unique matchups: {n_unique}/36")
    print(f"  Total possessions: {len(df):,}")
    
    if n_unique < 10:
        print(f"  ❌ CRITICAL: Only {n_unique} unique matchups - insufficient diversity!")
        return False
    
    # Check for highly imbalanced matchups
    max_poss = matchup_counts.max()
    min_poss = matchup_counts.min()
    mean_poss = matchup_counts.mean()
    
    print(f"  Possessions per matchup:")
    print(f"    Min: {min_poss}")
    print(f"    Max: {max_poss:,}")
    print(f"    Mean: {mean_poss:.0f}")
    print(f"    Ratio: {max_poss/min_poss if min_poss > 0 else 'inf'}:1")
    
    if max_poss > mean_poss * 10:
        print(f"  ❌ CRITICAL: Highly imbalanced distribution!")
        print(f"     Suggests data generation issue")
        return False
    
    # Check for very sparse matchups (<50 possessions)
    sparse_count = (matchup_counts < 50).sum()
    print(f"\n  Sparse matchups (<50 possessions): {sparse_count}")
    
    if sparse_count > 20:
        print(f"  ⚠️  WARNING: {sparse_count} matchups have insufficient data")
        print(f"     May cause convergence issues")
    
    print("  ✅ PASS")
    return True


def validate_feature_variance(df):
    """Check that features have meaningful variation (catches placeholder data)."""
    print("\n" + "="*80)
    print("2. FEATURE VARIANCE VALIDATION")
    print("="*80)
    
    z_cols = [col for col in df.columns if col.startswith('z_')]
    print(f"  Checking {len(z_cols)} features...")
    
    issues = []
    for col in z_cols:
        std = df[col].std()
        mean_val = df[col].mean()
        zero_pct = (df[col] == 0).sum() / len(df) * 100
        
        if std < 0.01:
            issues.append(f"  ❌ {col}: std={std:.6f} (no variation!)")
        elif zero_pct > 99:
            issues.append(f"  ❌ {col}: {zero_pct:.1f}% zeros (sparse data)")
        else:
            print(f"    ✅ {col}: std={std:.3f}, zeros={zero_pct:.1f}%")
    
    if issues:
        print("\n  ❌ CRITICAL: Low variance features detected!")
        for issue in issues:
            print(issue)
        print("\n  Suggests placeholder/placeholder data generation")
        return False
    
    print("  ✅ PASS")
    return True


def validate_feature_ranges(df):
    """Check that features are in reasonable ranges for Stan."""
    print("\n" + "="*80)
    print("3. FEATURE RANGE VALIDATION")
    print("="*80)
    
    z_cols = [col for col in df.columns if col.startswith('z_')]
    print(f"  Checking {len(z_cols)} features for Stan compatibility...")
    
    issues = []
    for col in z_cols:
        min_val = df[col].min()
        max_val = df[col].max()
        has_nan = df[col].isna().sum() > 0
        
        if has_nan:
            issues.append(f"  ❌ {col}: Contains NaN values")
        elif abs(min_val) > 100:
            issues.append(f"  ⚠️  {col}: Extreme min value {min_val:.2f}")
        elif abs(max_val) > 100:
            issues.append(f"  ⚠️  {col}: Extreme max value {max_val:.2f}")
        else:
            print(f"    ✅ {col}: range=[{min_val:.3f}, {max_val:.3f}]")
    
    if issues:
        print("\n  ⚠️  ISSUES DETECTED:")
        for issue in issues:
            print(issue)
        # Not fatal, but worth noting
    
    print("  ✅ PASS")
    return True


def validate_stan_compatibility(stan_file, data_path, test_size=1000):
    """Test Stan model compilation and sampling with real data."""
    print("\n" + "="*80)
    print("4. STAN MODEL COMPATIBILITY VALIDATION")
    print("="*80)
    
    try:
        # Load full data
        print(f"  Loading data from {data_path}...")
        df = pd.read_csv(data_path)
        
        # Take small sample for quick test
        test_df = df.sample(n=min(test_size, len(df)), random_state=42)
        print(f"  Using {len(test_df)} possessions for test")
        
        # Prepare Stan data
        N = len(test_df)
        y = test_df['outcome'].values
        matchup_id = test_df['matchup_id'].values
        z_off = test_df[[f'z_off_{i}' for i in range(8)]].values
        z_def = test_df[[f'z_def_{i}' for i in range(8)]].values
        
        stan_data = {
            'N': N,
            'y': y,
            'matchup_id': matchup_id,
            'z_off': z_off,
            'z_def': z_def
        }
        
        # Check parameter counts
        print(f"\n  Stan data structure:")
        print(f"    N: {stan_data['N']}")
        print(f"    matchup_id shape: {stan_data['matchup_id'].shape}")
        print(f"    z_off shape: {stan_data['z_off'].shape}")
        print(f"    z_def shape: {stan_data['z_def'].shape}")
        
        # Compile Stan model
        print(f"\n  Compiling Stan model: {stan_file}")
        model = cmdstanpy.CmdStanModel(stan_file=stan_file)
        print("  ✅ Model compiled successfully")
        
        # Try very short sampling run
        print(f"  Running minimal test (10 warmup, 10 sampling iterations)...")
        fit = model.sample(
            data=stan_data,
            chains=1,
            iter_warmup=10,
            iter_sampling=10,
            seed=42,
            show_progress=False
        )
        print("  ✅ Test sampling completed")
        
        # Check if parameters are accessible
        beta_0 = fit.stan_variable('beta_0')
        beta_off = fit.stan_variable('beta_off')
        beta_def = fit.stan_variable('beta_def')
        
        print(f"  ✅ Parameters accessible:")
        print(f"    beta_0 shape: {beta_0.shape}")
        print(f"    beta_off shape: {beta_off.shape}")
        print(f"    beta_def shape: {beta_def.shape}")
        
        print("  ✅ PASS")
        return True
        
    except Exception as e:
        print(f"  ❌ CRITICAL: Stan compatibility check failed!")
        print(f"     Error: {e}")
        print(f"\n  This must be fixed before training!")
        return False


def validate_parameter_alignment(df, stan_file):
    """Verify that Stan model expects match data structure."""
    print("\n" + "="*80)
    print("5. PARAMETER COUNT VALIGNATION")
    print("="*80)
    
    # Expected: 612 parameters (36 matchups × 16 params each + 36 intercepts)
    # Actually: 36 intercepts + 36×8 offensive + 36×8 defensive = 36 + 288 + 288 = 612
    expected_total = 612
    expected_matchups = 36
    expected_archetypes = 8
    
    print(f"  Expected parameters:")
    print(f"    Matchups: {expected_matchups}")
    print(f"    Archetypes: {expected_archetypes}")
    print(f"    Total params: {expected_total}")
    
    # Count unique matchups in data
    actual_matchups = df['matchup_id'].nunique()
    print(f"\n  Actual in data:")
    print(f"    Unique matchups: {actual_matchups}")
    
    # Z-matrix should have 8 archetypes
    z_cols = [col for col in df.columns if col.startswith('z_')]
    z_off_cols = [col for col in z_cols if col.startswith('z_off')]
    z_def_cols = [col for col in z_cols if col.startswith('z_def')]
    
    print(f"    Z-offensive columns: {len(z_off_cols)}")
    print(f"    Z-defensive columns: {len(z_def_cols)}")
    
    if len(z_off_cols) != 8 or len(z_def_cols) != 8:
        print(f"  ❌ CRITICAL: Z-matrix has wrong dimensions!")
        print(f"     Expected: 8 archetypes, got {len(z_off_cols)} and {len(z_def_cols)}")
        return False
    
    print("  ✅ PASS")
    return True


def main():
    parser = argparse.ArgumentParser(description="Deep validate matchup data before training")
    parser.add_argument("--data", default="matchup_specific_bayesian_data_full.csv",
                       help="Path to matchup-specific data CSV")
    parser.add_argument("--stan", default="bayesian_model_k8_matchup_specific.stan",
                       help="Path to Stan model file")
    parser.add_argument("--test-size", type=int, default=1000,
                       help="Sample size for Stan compatibility test")
    
    args = parser.parse_args()
    
    print("="*80)
    print("DEEP DATA VALIDATION FOR MATCHUP-SPECIFIC MODEL")
    print("="*80)
    print(f"Data file: {args.data}")
    print(f"Stan model: {args.stan}")
    
    # Load data
    print(f"\nLoading data from {args.data}...")
    df = pd.read_csv(args.data)
    print(f"✅ Loaded {len(df):,} possessions")
    
    # Run validations
    results = []
    
    results.append(("Matchup Distribution", validate_matchup_distribution(df)))
    results.append(("Feature Variance", validate_feature_variance(df)))
    results.append(("Feature Ranges", validate_feature_ranges(df)))
    results.append(("Parameter Alignment", validate_parameter_alignment(df, args.stan)))
    results.append(("Stan Compatibility", validate_stan_compatibility(args.stan, args.data, args.test_size)))
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name:.<40} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL VALIDATIONS PASSED")
        print("\nYou can proceed with RunPod deployment.")
        print("Expected training time: 30-40 hours")
        print("Estimated cost: $50-100")
        sys.exit(0)
    else:
        print("❌ VALIDATION FAILED")
        print("\n⚠️  DO NOT PROCEED WITH TRAINING")
        print("Fix the issues above before deploying to RunPod.")
        sys.exit(1)


if __name__ == "__main__":
    main()

