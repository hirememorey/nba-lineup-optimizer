# Developer Handoff: NBA Lineup Optimizer

**Date**: October 30, 2025  
**Status**: ✅ **PRODUCTION READY** - Simplified model validated. Matchup-specific model evaluated but shows convergence issues.  
**Critical Context**: Simplified model is production-ready. Matchup-specific model attempted but requires different architecture.

## Where We Are

### ✅ Completed Work

1. **Data Generation Fixed**: Discovered and fixed critical bug where all possessions were assigned to matchup_id = 35
   - Modified `generate_matchup_specific_bayesian_data.py` to use pre-computed assignment maps
   - Validated on 10K, 50K, 100K, and full 96K datasets
   - **Result**: 32 unique matchups (89% coverage) with 96,837 training-ready possessions

2. **Matchup-Specific Model Evaluated**: Attempted local training of full model (612 parameters)
   - **Full dataset (96K data, 41 hours)**: Completed but all chains returned errors (retcodes=1)
   - **Pilot test (200/200 iterations, 3.4 hours)**: 52.5% divergent transitions - model fundamentally unstable
   - **Stricter settings test**: Too slow (8+ hours just for warmup) - impractical
   - **Conclusion**: Model is too complex for available data, requires different architecture

3. **Current Models Available**:
   - ✅ **Simplified model (17 params)**: `model_coefficients.csv` - **PRODUCTION READY AND VALIDATED**
   - ⚠️ **Matchup-specific model (612 params)**: Evaluated but shows convergence issues - not production-ready

### 🎯 Current Status

**Simplified model works perfectly**: Validated, converged (R-hat < 1.01, 0 divergences), correctly identifies archetype redundancy (e.g., Westbrook-LeBron case). This is what you should use for production.

**Matchup-specific model needs rethinking**: The 612-parameter architecture is too complex despite having sufficient data. Future work should consider hierarchical priors, reduced parameterization, or different architecture. See `MATCHUP_MODEL_EVALUATION_SUMMARY.md` for details.

## What to Do Next

### Immediate Action: Use Simplified Model for Production

**Recommended**: Deploy the simplified model (`model_coefficients.csv`) which is:
- ✅ Validated and working
- ✅ Converged (R-hat < 1.01, 0 divergences)  
- ✅ Correctly identifies player fit issues
- ✅ Production-ready

**Files**:
- Model coefficients: `model_coefficients.csv`
- Training data: `production_bayesian_data.csv`
- Validation results: See Phase 3 validation in STATUS.md

### Future Work: Improve Matchup-Specific Approach

**If skill-context interactions are critical**, see `MATCHUP_MODEL_EVALUATION_SUMMARY.md` for detailed recommendations:

1. **Hierarchical Priors**: Shrinkage toward global effects (recommended)
2. **Reduced Parameterization**: 52 params instead of 612
3. **More Data**: Need 500+ obs/param (306,000+ possessions)
4. **Different Architecture**: Soft clustering, latent effects, non-parametric

### Tools and Scripts Available

**For Validation**:
- `deep_validate_matchup_data.py` - Comprehensive data validation before training
- `runpod_deploy_checklist.py` - Pre-flight checks for deployment

**For Training** (if revisiting matchup-specific approach):
- `train_full_matchup_specific_runpod.py` - Training script (can run locally or on cloud)
- `matchup_specific_bayesian_data_full.csv` - Full dataset (96,837 possessions)
- `bayesian_model_k8_matchup_specific.stan` - Stan model file

**Note**: These files exist but the matchup-specific approach showed convergence issues. See evaluation summary before attempting another training run.

### How to Evaluate Results

```python
# Check convergence diagnostics
# Look for R-hat < 1.01, ESS > 400
# Divergent transitions should be <1%

# If good convergence:
# → Proceed to validation on 2022-23 holdout
# → Compare to simplified model predictions
# → Deploy the better-performing model
```

## Current Project State

### ✅ Working Production System

**Simplified Model** (`model_coefficients.csv`):
- 17 parameters
- Converged perfectly (R-hat < 1.01)
- Validated on 2022-23 holdout (MSE: 0.309)
- Detects archetype redundancy correctly
- **Status**: Ready to deploy

**Limitation**: Cannot detect skill-context interactions

### ⏳ Proposed Enhanced System

**Matchup-Specific Model** (needs training):
- 612 parameters (36 matchups × 16)
- Should detect skill-context interactions
- Needs full-dataset training on RunPod
- **Status**: Ready to train

**Goal**: Deploy this if it converges better than simplified model

## Key Files and What They Do

### Training & Data Generation

- `generate_matchup_specific_bayesian_data.py`: Creates matchup-specific datasets
  - Usage: `python generate_matchup_specific_bayesian_data.py --size full`
  - Output: `matchup_specific_bayesian_data_full.csv`

- `train_full_matchup_specific_runpod.py`: Trains matchup-specific model
  - Usage: Run on RunPod (30-40 hours)
  - Output: `stan_model_results_full_matchup/matchup_specific_coefficients_full.csv`

### Current Working Model

- `model_coefficients.csv`: Simplified model coefficients (17 params)
- `production_bayesian_data.csv`: Training data for simplified model
- `bayesian_model_k8.stan`: Simplified Stan model

### Diagnostics & Analysis

- `validate_matchup_data_generation.py`: Validates data generation at different scales
- `COEFFICIENT_ANALYSIS.md`: Why matchup-specific model failed initially
- `FINAL_RECOMMENDATION.md`: Recommendation to use simplified model
- `RUNPOD_ANALYSIS.md`: Feasibility of full dataset training

## Decisions Made

### Why Matchup-Specific Over Simplified?

**From the developer's insight**:
> "The simplified model only detects redundancy (same archetype), not how skills contribute differently in different matchup contexts"

**Translation**: 
- LeBron and Westbrook might both be Archetype 4
- But their skills should contribute differently against different defenses
- Matchup-specific model captures this; simplified model cannot

### Why RunPod Training?

- **Local constraints**: 18-hour training crashed at 73%
- **Cloud benefits**: Can run 30-40 hours without interruption
- **Economics**: $50-100 for full training vs. weeks of retry attempts

## What Success Looks Like

After RunPod training completes, you should have:

1. `stan_model_results_full_matchup/matchup_specific_coefficients_full.csv`
   - Contains 612 coefficient values (36 matchups × 16 params)
   
2. Convergence diagnostics
   - Should show R-hat < 1.01 for most matchups
   - ESS > 400 for interpretable parameters

3. Ability to compare models
   - Run both simplified and matchup-specific on 2022-23 validation
   - Choose the better-performing model for production

## Next Steps After Training

1. **Download results** from RunPod
2. **Extract coefficients** (already done by script)
3. **Run validation** on 2022-23 holdout data
4. **Compare models** (simplified vs. matchup-specific)
5. **Deploy the better model** for production recommendations

## Troubleshooting

### If training fails again:

**Option 1**: Use simplified model (already works!)  
**Option 2**: Train only on top 25 matchups (400 params vs 612)  
**Option 3**: Use hierarchical model (global + matchup effects)

### If training succeeds:

**Celebrate!** You have a more sophisticated model that captures matchup context.  
Deploy and validate against real NBA outcomes.

## Questions to Answer

For the next developer:

1. **Does matchup-specific model converge** on full dataset?
2. **Does it improve predictions** vs. simplified model?
3. **Which model to deploy** for production?
4. **How to handle** sparse matchups in predictions?

These are the open questions that RunPod training will answer.

## Quick Start for New Developer

1. Read: `DEVELOPER_HANDOFF.md` (this file)
2. Review: `RUNPOD_ANALYSIS.md` for feasibility analysis  
3. Deploy: Run `./runpod_full_training.sh` on RunPod
4. Wait: 30-40 hours
5. Download: Results from RunPod
6. Validate: Compare models on 2022-23 holdout
7. Deploy: Choose better model for production

Good luck! 🏀

