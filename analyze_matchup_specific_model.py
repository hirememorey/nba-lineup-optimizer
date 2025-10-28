#!/usr/bin/env python3
"""
Analyze Requirements for Matchup-Specific Bayesian Model

This script analyzes what it would take to implement the full paper methodology
with matchup-specific coefficients (β_off_a,mi and β_def_a,mi).
"""

import pandas as pd
import numpy as np

def analyze_requirements():
    print("="*80)
    print("ANALYSIS: MATCHUP-SPECIFIC MODEL REQUIREMENTS")
    print("="*80)
    
    # Load the multi-season data
    df = pd.read_csv('multi_season_bayesian_data.csv')
    
    print(f"\nCurrent Data:")
    print(f"  Total possessions: {len(df):,}")
    print(f"  Unique matchups: {df['matchup_id'].nunique()}")
    
    # Analyze matchup distribution
    matchup_counts = df['matchup_id'].value_counts().sort_values(ascending=False)
    
    print(f"\nMatchup Distribution:")
    print(f"  Matchups with data: {len(matchup_counts)}/36 possible")
    print(f"  Mean possessions per matchup: {len(df) / len(matchup_counts):.0f}")
    print(f"  Median possessions per matchup: {matchup_counts.median():.0f}")
    print(f"  Min possessions: {matchup_counts.min()}")
    print(f"  Max possessions: {matchup_counts.max()}")
    
    print(f"\nTop 10 Matchups:")
    for matchup, count in matchup_counts.head(10).items():
        pct = (count / len(df)) * 100
        print(f"  {matchup}: {count:,} ({pct:.1f}%)")
    
    # Parameter count analysis
    num_archetypes = 8
    num_matchups = len(matchup_counts)
    
    print(f"\n" + "="*80)
    print("PARAMETER COUNT ANALYSIS")
    print("="*80)
    
    print(f"\nCurrent Simplified Model:")
    print(f"  Intercept: 1")
    print(f"  β_off (archetypes): {num_archetypes}")
    print(f"  β_def (archetypes): {num_archetypes}")
    print(f"  σ (error): 1")
    print(f"  TOTAL: {1 + num_archetypes * 2 + 1} parameters")
    
    print(f"\nMatchup-Specific Model (Paper Methodology):")
    print(f"  Intercepts (per matchup): {num_matchups}")
    print(f"  β_off_a,mi (archetype × matchup): {num_archetypes} × {num_matchups} = {num_archetypes * num_matchups}")
    print(f"  β_def_a,mi (archetype × matchup): {num_archetypes} × {num_matchups} = {num_archetypes * num_matchups}")
    print(f"  σ (error): 1")
    print(f"  TOTAL: {num_matchups + (num_archetypes * num_matchups) * 2 + 1} parameters")
    
    total_params = num_matchups + (num_archetypes * num_matchups) * 2 + 1
    print(f"\n  That's {total_params} parameters vs {1 + num_archetypes * 2 + 1} currently")
    
    # Data adequacy check
    print(f"\n" + "="*80)
    print("DATA ADEQUACY ASSESSMENT")
    print("="*80)
    
    observations_per_param = len(df) / total_params
    print(f"\n  Observations per parameter: {observations_per_param:.1f}")
    
    sparse_matchups = (matchup_counts < 100).sum()
    print(f"  Matchups with <100 possessions: {sparse_matchups}/{len(matchup_counts)}")
    
    if observations_per_param >= 10:
        print(f"  ✅ Data appears sufficient (recommended: ≥5-10 obs/param)")
    else:
        print(f"  ⚠️  Data may be insufficient (<5 obs/param)")
    
    # Computational complexity
    print(f"\n" + "="*80)
    print("COMPUTATIONAL REQUIREMENTS")
    print("="*80)
    
    print(f"\nSampling Complexity:")
    print(f"  Current: O({len(df)} × {num_archetypes * 2}) per iteration")
    print(f"  Matchup-specific: O({len(df)} × {num_archetypes * num_matchups * 2}) per iteration")
    
    estimated_slowdown = (num_archetypes * num_matchups * 2) / (num_archetypes * 2)
    print(f"  Estimated slowdown: ~{estimated_slowdown:.0f}x")
    
    # Recommended approach
    print(f"\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    print(f"\n1. DATA REQUIREMENTS:")
    print(f"   - Current: {len(df):,} rows")
    print(f"   - Recommended for full model: {total_params * 10:,}+ rows")
    print(f"   - Gap: {max(0, total_params * 10 - len(df)):,} more rows needed")
    
    print(f"\n2. STAN MODEL CHANGES NEEDED:")
    print(f"   - Add matchup index to data block")
    print(f"   - Change parameters from vector[8] to matrix[8, {num_matchups}]")
    print(f"   - Update likelihood to use matchup-specific coefficients")
    
    print(f"\n3. ALTERNATIVES:")
    print(f"   Option A: Hierarchical model (partial pooling across matchups)")
    print(f"   Option B: Regroup sparse matchups into meta-clusters")
    print(f"   Option C: Stay with simplified model (current approach)")
    
    # Check for sparse matchups
    print(f"\n4. QUALITY CHECK:")
    if sparse_matchups > 10:
        print(f"   ⚠️  {sparse_matchups} matchups have <100 possessions")
        print(f"   Consider regrouping or hierarchical priors")
    else:
        print(f"   ✅ Most matchups have sufficient data")

if __name__ == '__main__':
    analyze_requirements()

