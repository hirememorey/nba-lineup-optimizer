# Developer Handoff: NBA Lineup Optimizer - RunPod Deployment

**Date**: October 28, 2025  
**Status**: Ready for RunPod deployment of matchup-specific model  
**Critical Context**: The matchup-specific model offers insights the simplified model cannot

## Where We Are

### ✅ Completed Work

1. **Data Generation Fixed**: Discovered and fixed critical bug where all possessions were assigned to matchup_id = 35
   - Modified `generate_matchup_specific_bayesian_data.py` to use pre-computed assignment maps
   - Validated on 10K, 50K, 100K, and full 96K datasets
   - **Result**: 32 unique matchups (89% coverage) with 96,837 training-ready possessions

2. **Training Attempted**: Tried to train matchup-specific model (612 parameters)
   - **Subsample (25K data)**: Failed with 91% divergent transitions
   - **Root cause**: Overparameterized (40.8 obs/param is insufficient)
   - **Full dataset (96K data)**: Not attempted yet
   - **Math**: 96K ÷ 612 params = **158 obs/param** (should work!)

3. **Current Models Available**:
   - ✅ Simplified model (17 params): `model_coefficients.csv` - **PRODUCTION READY**
   - ⏳ Matchup-specific model (612 params): Not yet trained on full dataset

### 🎯 Why Matchup-Specific Model is Important

**Critical insight discovered**: The simplified model only detects **redundancy** (both players same archetype), not **skill-context interactions** (how archetype skills contribute differently in different matchup contexts).

This is exactly what the matchup-specific model should capture but hasn't been trained yet.

## What to Do Next

### Recommended Approach: Train Full Dataset on RunPod

**Why this is the right move**:
- Full dataset: **96,837 possessions ÷ 612 parameters = 158 obs/param**
- **24 matchups** have >50 obs/param (should converge well)
- Only **7 matchups** are very sparse (can handle gracefully)
- This addresses the core insight about skill-context interactions

### Files Ready for RunPod

1. **Training Script**: `train_full_matchup_specific_runpod.py` ✅
2. **Data File**: `matchup_specific_bayesian_data_full.csv` (96K possessions) ✅
3. **Stan Model**: `bayesian_model_k8_matchup_specific.stan` ✅
4. **Deployment Script**: `runpod_full_training.sh` ✅

### RunPod Configuration

```bash
# Estimated cost and time
Expected time: 30-40 hours
Estimated cost: $50-100 (RunPod pricing)
CPU/RAM: 8 vCPU, 32 GB RAM sufficient
```

### Steps to Deploy

```bash
# 1. Make script executable
chmod +x runpod_full_training.sh

# 2. Review and adjust if needed
cat runpod_full_training.sh

# 3. Run on RunPod
./runpod_full_training.sh

# 4. Monitor progress
# (Check logs via RunPod CLI)

# 5. Download results when complete
# (Results will be in stan_model_results_full_matchup/)
```

## What to Expect

### Possible Outcomes

**Scenario A: Successful Convergence** ✅
- Most matchups (24/36) have R-hat < 1.01
- Coefficients are interpretable
- **Use these for production** (more insights than simplified model)

**Scenario B: Partial Convergence** ⚠️
- Some matchups converge, others don't
- **Mask the non-convergent matchups** in predictions
- Use simplified model fallback for sparse matchups
- **Still useful**: 25 good matchups > 0 good matchups

**Scenario C: Failed Again** ❌
- If divergence persists even on full dataset
- **Use simplified model** for production
- Matchup-specific modeling requires different architecture or more data

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

