#!/usr/bin/env python3
"""
RunPod Deployment Checklist and File Verification

Validates that all necessary files exist and are ready for RunPod deployment
before committing to cloud training.
"""

import os
from pathlib import Path
import hashlib

REQUIRED_FILES = {
    'matchup_specific_bayesian_data_full.csv': 'Data file (96,837 possessions)',
    'bayesian_model_k8_matchup_specific.stan': 'Stan model file',
    'train_full_matchup_specific_runpod.py': 'Training script',
    'requirements.txt': 'Python dependencies',
}

def verify_files_exist():
    """Check that all required files exist."""
    print("="*80)
    print("FILE EXISTENCE CHECK")
    print("="*80)
    
    missing = []
    for file, description in REQUIRED_FILES.items():
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"  ✅ {file:.<50} {size:>10,} bytes")
        else:
            print(f"  ❌ {file:.<50} MISSING")
            missing.append(file)
    
    if missing:
        print(f"\n❌ Missing {len(missing)} required files:")
        for f in missing:
            print(f"   - {f}")
        return False
    
    print("\n✅ All required files present")
    return True


def verify_file_sizes():
    """Verify files have reasonable sizes."""
    print("\n" + "="*80)
    print("FILE SIZE VERIFICATION")
    print("="*80)
    
    checks = {
        'matchup_specific_bayesian_data_full.csv': (10_000_000, 200_000_000),  # 10MB - 200MB (compressed CSV)
        'bayesian_model_k8_matchup_specific.stan': (1000, 5000),  # 1KB - 5KB
        'train_full_matchup_specific_runpod.py': (5000, 20_000),  # 5KB - 20KB
    }
    
    issues = []
    for file, (min_size, max_size) in checks.items():
        if os.path.exists(file):
            size = os.path.getsize(file)
            if size < min_size:
                print(f"  ⚠️  {file}: {size:,} bytes (suspiciously small)")
                issues.append(file)
            elif size > max_size:
                print(f"  ⚠️  {file}: {size:,} bytes (suspiciously large)")
                issues.append(file)
            else:
                print(f"  ✅ {file}: {size:,} bytes")
        else:
            print(f"  ❌ {file}: MISSING")
            issues.append(file)
    
    if issues:
        print(f"\n❌ File size issues detected")
        return False
    
    print("\n✅ All file sizes reasonable")
    return True


def verify_data_integrity():
    """Quick sanity check on data file."""
    print("\n" + "="*80)
    print("DATA INTEGRITY CHECK")
    print("="*80)
    
    data_file = 'matchup_specific_bayesian_data_full.csv'
    
    if not os.path.exists(data_file):
        print(f"  ❌ {data_file} not found")
        return False
    
    try:
        import pandas as pd
        
        # Read first few lines to check format
        df = pd.read_csv(data_file, nrows=100)
        print(f"  ✅ Data file readable")
        print(f"     Columns: {len(df.columns)}")
        print(f"     Sample rows: {len(df)}")
        
        # Check for required columns
        required_cols = ['outcome', 'matchup_id', 'z_off_0', 'z_def_0']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"  ❌ Missing required columns: {missing_cols}")
            return False
        
        print(f"  ✅ Required columns present")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error reading data file: {e}")
        return False


def estimate_upload_time():
    """Estimate file upload time for RunPod."""
    print("\n" + "="*80)
    print("UPLOAD TIME ESTIMATION")
    print("="*80)
    
    total_size = 0
    for file in REQUIRED_FILES.keys():
        if os.path.exists(file):
            total_size += os.path.getsize(file)
    
    print(f"  Total size: {total_size:,} bytes ({total_size/1_000_000:.1f} MB)")
    
    # Assume 10 MB/s upload speed
    upload_time_seconds = total_size / (10 * 1_000_000)
    upload_time_minutes = upload_time_seconds / 60
    
    print(f"  Estimated upload time: {upload_time_minutes:.1f} minutes")
    print(f"     (assumes 10 MB/s connection)")
    
    return upload_time_minutes < 60  # Should upload in < 1 hour


def main():
    """Run all pre-deployment checks."""
    print("="*80)
    print("RUNPOD DEPLOYMENT PRE-FLIGHT CHECK")
    print("="*80)
    print("Verifying readiness for 30-40 hour cloud training run")
    print()
    
    results = []
    
    results.append(("Files Exist", verify_files_exist()))
    results.append(("File Sizes", verify_file_sizes()))
    results.append(("Data Integrity", verify_data_integrity()))
    results.append(("Upload Feasible", estimate_upload_time()))
    
    # Summary
    print("\n" + "="*80)
    print("READINESS SUMMARY")
    print("="*80)
    
    all_passed = True
    for check, passed in results:
        status = "✅ READY" if passed else "❌ NOT READY"
        print(f"  {check:.<40} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL CHECKS PASSED")
        print("\n📋 NEXT STEPS:")
        print("  1. Review 'deep_validate_matchup_data.py' output")
        print("  2. Prepare RunPod credentials")
        print("  3. Review 'RUNPOD_DEPLOYMENT_GUIDE.md'")
        print("  4. Run: ./runpod_full_training.sh")
        print("\n⏱️  Expected:")
        print("  - Upload time: ~10-30 minutes")
        print("  - Training time: 30-40 hours")
        print("  - Cost: $50-100")
    else:
        print("❌ PRE-DEPLOYMENT CHECKS FAILED")
        print("\n⚠️  DO NOT PROCEED TO RUNPOD")
        print("Fix the issues above before deploying.")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

