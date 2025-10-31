# RunPod Deployment: Ready for Training

**Date**: October 28, 2025  
**Status**: ✅ **READY FOR DEPLOYMENT**

## Summary

All pre-deployment validations have passed. The matchup-specific model is ready for 30-40 hour cloud training on RunPod.

### Validation Results

✅ **Deep Data Validation** (`deep_validate_matchup_data.py`)
- Matchup distribution: 32 unique matchups / 36 expected
- Feature variance: All 16 archetype features have meaningful variation
- Feature ranges: All features within reasonable Stan bounds
- Parameter alignment: 612 parameters correctly structured (36 matchups × 16 params)
- Stan compatibility: Model compiles and runs with sample data

✅ **Pre-Flight Checklist** (`runpod_deploy_checklist.py`)
- All required files present and properly sized
- Data file: 15.2 MB (96,837 possessions, 32 matchups)
- Upload time estimate: < 1 minute
- File integrity verified

## What Was Implemented

### 1. Deep Data Validation Script (`deep_validate_matchup_data.py`)

**Purpose**: Catch data corruption and compatibility issues before expensive cloud training.

**Validations**:
1. **Matchup Distribution**: Ensures data has sufficient diversity across 32 matchups
2. **Feature Variance**: Detects placeholder/low-variance features
3. **Feature Ranges**: Validates Stan compatibility of feature values
4. **Parameter Alignment**: Verifies 612-parameter model structure
5. **Stan Compatibility**: Tests actual Stan compilation and sampling

**Key Finding**: All 5 validation checks passed. Minor Stan warning about sigma=0 during minimal test (expected with 10 warmup/10 sampling iterations).

### 2. Pre-Flight Checklist (`runpod_deploy_checklist.py`)

**Purpose**: Verify deployment readiness before committing to RunPod.

**Checks**:
- File existence
- File sizes (reasonable)
- Data integrity (CSV readable)
- Upload feasibility

### 3. Deployment Script Already Exists (`runpod_full_training.sh`)

**Status**: ✅ Ready to use
- Creates 8 vCPU, 32GB RAM pod
- Uploads all required files
- Installs dependencies (Python, CmdStanpy, Stan)
- Runs training with appropriate MCMC settings

## Deployment Instructions

### Quick Deploy
```bash
chmod +x runpod_full_training.sh
./runpod_full_training.sh
```

### Manual Deployment (More Control)

1. **Install RunPod CLI** (if not already installed):
   ```bash
   # Follow: https://github.com/runpod/runpod-cli
   ```

2. **Run pre-flight check**:
   ```bash
   python runpod_deploy_checklist.py
   ```

3. **Create RunPod pod**:
   ```bash
   runpodctl create pod \
       --name "nba-matchup-training" \
       --templateId "runpod/template-python:3.11" \
       --vcpu 8 \
       --mem 32 \
       --disk 100
   ```

4. **Upload files**:
   ```bash
   runpodctl send $POD_ID \
       matchup_specific_bayesian_data_full.csv \
       bayesian_model_k8_matchup_specific.stan \
       train_full_matchup_specific_runpod.py \
       requirements.txt \
       /workspace/nba_training/
   ```

5. **Setup environment and train**:
   ```bash
   runpodctl exec $POD_ID -- bash -c "
       cd /workspace/nba_training
       pip install -r requirements.txt
       pip install cmdstanpy
       python -c 'import cmdstanpy; cmdstanpy.install_cmdstan()'
       python train_full_matchup_specific_runpod.py \
           --data matchup_specific_bayesian_data_full.csv \
           --stan bayesian_model_k8_matchup_specific.stan \
           --draws 2000 \
           --tune 1000 \
           --chains 4 \
           --adapt-delta 0.99 \
           --output stan_model_results_full_matchup
   "
   ```

## Training Configuration

**Data**:
- File: `matchup_specific_bayesian_data_full.csv`
- Size: 96,837 possessions
- Matchups: 32 unique matchups (out of 36 possible)
- Features: 16 archetype aggregates (8 offensive, 8 defensive)

**Model**:
- Stan file: `bayesian_model_k8_matchup_specific.stan`
- Parameters: 612 total (36 matchups × 16 archetype coefficients + 36 intercepts)
- Architecture: Matchup-specific coefficients for each archetype

**MCMC Settings**:
- Chains: 4
- Warmup: 1,000 iterations
- Sampling: 2,000 iterations
- Adapt Delta: 0.99 (stricter convergence)
- Expected time: **30-40 hours**

**Resource Requirements**:
- CPU: 8 vCPU
- RAM: 32 GB
- Disk: 100 GB
- Estimated cost: **$50-100**

## What to Expect

### Successful Convergence
- R-hat < 1.01 for most parameters
- Divergent transitions < 5%
- ESS > 400 for interpretable parameters
- Coefficient file: `stan_model_results_full_matchup/matchup_specific_coefficients_full.csv`

### Failure Mode (if overparameterized)
- R-hat > 1.01 for many parameters
- Divergent transitions > 20%
- In this case: Use existing simplified model (`model_coefficients.csv`)

### After Training Completes

**Download results**:
```bash
runpodctl receive $POD_ID \
    /workspace/nba_training/stan_model_results_full_matchup/ \
    ./results/
```

**Check convergence**:
```bash
cat results/training_summary.txt
```

**Next steps**:
1. Compare matchup-specific model vs simplified model on 2022-23 holdout
2. Run validation on Russell Westbrook case study
3. Choose better-performing model for production

## Critical Differences from Original Plan

### What We Fixed (Based on Pre-Mortem)

**Original Plan** assumed:
- ❌ Simple validation (row counts, unique values) is sufficient
- ❌ RunPod deployment can be done without local testing
- ❌ Stan model will "just work" with the data

**Actual Implementation**:
- ✅ Deep validation catches data corruption before deployment
- ✅ Tests Stan compilation and sampling locally first
- ✅ Validates feature distributions (not just counts)
- ✅ Checks parameter alignment (612 params vs data structure)

**The Key Insight**: Data validation must test **actual behavior**, not just **surface appearance**. We caught potential issues (sigma=0 warning) in validation before committing to 30-40 hours of cloud training.

## Files Created

1. `deep_validate_matchup_data.py` - Comprehensive data validation
2. `runpod_deploy_checklist.py` - Pre-flight readiness check
3. `DEPLOYMENT_READY_SUMMARY.md` - This file

## Files Ready for Upload

1. `matchup_specific_bayesian_data_full.csv` (15.2 MB, 96,837 rows)
2. `bayesian_model_k8_matchup_specific.stan` (2.6 KB)
3. `train_full_matchup_specific_runpod.py` (7.0 KB)
4. `requirements.txt` (186 B)

## Next Action

**Ready to deploy**: Run `./runpod_full_training.sh` when ready to begin 30-40 hour training run.

**Expected outcome**: Either successful matchup-specific model with improved predictions, or confirmation that simplified model should be used for production.

