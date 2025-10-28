#!/usr/bin/env python3
"""
Validate Matchup-Specific Data Generation at Scale

This script tests the matchup-specific data generation pipeline on increasing
dataset sizes to identify failure points before committing to full training.

Tests:
1. 10K possessions (prototype size) ✅ Already works
2. 50K possessions (target for Phase 2.1)
3. 100K possessions (target for Phase 2.2)
4. Full dataset (~231K)
"""

import os
import sys
import time
import traceback
import psutil
import pandas as pd
from pathlib import Path

# Configuration
TEST_SIZES = [10000, 50000, 100000, None]  # None = full dataset
OUTPUT_DIR = Path("validation_results")
OUTPUT_DIR.mkdir(exist_ok=True)

def validate_data_generation(size):
    """Test data generation at a given size."""
    print(f"\n{'='*80}")
    size_str = f"{size:,}" if size else "FULL"
    print(f"TESTING DATASET SIZE: {size_str}")
    print(f"{'='*80}")
    
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    try:
        # Import and run the generation with size parameter
        sys.path.insert(0, os.getcwd())
        from generate_matchup_specific_bayesian_data import prepare_matchup_specific_bayesian_data
        
        print(f"  Generating matchup-specific dataset...")
        
        # Run the generation
        prepare_matchup_specific_bayesian_data(size_limit=size)
        
        # Determine output path
        if size:
            output_path = f"matchup_specific_bayesian_data_{size}.csv"
        else:
            output_path = "matchup_specific_bayesian_data_full.csv"
        
        # Check if output exists
        if os.path.exists(output_path):
            print(f"  ✅ Output file created: {output_path}")
            
            # Read and validate
            df = pd.read_csv(output_path)
            
            print(f"  📊 Dataset Statistics:")
            print(f"     Rows: {len(df):,}")
            print(f"     Columns: {len(df.columns)}")
            
            # Validate matchup_id range
            matchup_ids = df['matchup_id'].unique()
            min_matchup = matchup_ids.min()
            max_matchup = matchup_ids.max()
            
            print(f"  🎯 Matchup Validation:")
            print(f"     Unique matchups: {len(matchup_ids)}")
            print(f"     Range: {min_matchup}-{max_matchup}")
            
            if min_matchup < 0 or max_matchup > 35:
                print(f"     ❌ ERROR: Matchup IDs out of range!")
                return False
            else:
                print(f"     ✅ Matchup IDs in valid range")
            
            # Check for sparse matchups
            matchup_counts = df['matchup_id'].value_counts()
            sparse_count = (matchup_counts < 10).sum()
            
            print(f"  📉 Sparse Matchup Check:")
            print(f"     Matchups with <10 possessions: {sparse_count}")
            if sparse_count > 0:
                print(f"     ⚠️  Warning: {sparse_count} matchups may have insufficient data")
            
            # Check Z-matrix completeness
            z_columns = [col for col in df.columns if col.startswith('z_')]
            print(f"  🧮 Z-Matrix Validation:")
            print(f"     Z-columns: {len(z_columns)}")
            
            non_zero_archetypes = []
            for i in range(8):
                z_off_col = f'z_off_{i}'
                z_def_col = f'z_def_{i}'
                if z_off_col in df.columns:
                    non_zero_off = (df[z_off_col] != 0).sum()
                    non_zero_def = (df[z_def_col] != 0).sum()
                    if non_zero_off > 0 or non_zero_def > 0:
                        non_zero_archetypes.append(i)
            
            print(f"     Archetypes with data: {len(non_zero_archetypes)}/8")
            if len(non_zero_archetypes) < 8:
                print(f"     ⚠️  Warning: Some archetypes have no data")
            
            elapsed = time.time() - start_time
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_used = end_memory - start_memory
            
            print(f"  ⏱️  Performance:")
            print(f"     Time: {elapsed:.1f}s")
            print(f"     Memory (peak): {end_memory:.1f} MB")
            print(f"     Memory (used): {memory_used:.1f} MB")
            print(f"     Rate: {len(df)/elapsed:.0f} rows/sec")
            
            return True
            
        else:
            print(f"  ❌ No output file created")
            return False
            
    except MemoryError:
        print(f"  ❌ MEMORY ERROR at size {size}")
        print(f"     Dataset too large for available memory")
        return False
        
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        print(f"     {traceback.format_exc()}")
        return False

def main():
    """Run validation tests at increasing sizes."""
    print("="*80)
    print("MATCHUP-SPECIFIC DATA GENERATION VALIDATION")
    print("="*80)
    
    results = {}
    
    for size in TEST_SIZES:
        passed = validate_data_generation(size)
        results[size] = passed
        
        if not passed:
            print(f"\n❌ STOPPING: Failed at size {size}")
            print(f"   Previous successful size should be used for training")
            break
    
    # Summary
    print(f"\n{'='*80}")
    print("VALIDATION SUMMARY")
    print(f"{'='*80}")
    
    for size, passed in results.items():
        size_str = f"{size:,}" if size else "FULL"
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {size_str:>10}: {status}")
    
    # Recommendation
    print(f"\n{'='*80}")
    print("RECOMMENDATION")
    print(f"{'='*80}")
    
    successful_sizes = [size for size, passed in results.items() if passed]
    if successful_sizes:
        max_successful = max(successful_sizes) if successful_sizes[0] else None
        max_str = f"{max_successful:,}" if max_successful else "FULL"
        print(f"  ✅ Largest successful test: {max_str}")
        print(f"  🎯 Recommended training size: {max_str}")
    else:
        print(f"  ❌ No successful tests - need to debug generation script")

if __name__ == "__main__":
    main()

