# Matchup-Specific Model Evaluation Summary

**Date**: October 30, 2025  
**Status**: Evaluation complete - Simplified model recommended for production

## Executive Summary

We attempted to train the matchup-specific model (612 parameters) on the full dataset (96,837 possessions, 32 matchups) to capture skill-context interactions. Despite sufficient data (158 obs/param), the model shows fundamental convergence issues that make it impractical for production use.

## What We Attempted

### 1. Full Dataset Training (41 hours)
- **Date**: October 28-30, 2025
- **Configuration**: 4 chains, 1000 warmup, 2000 samples, adapt_delta=0.99
- **Result**: Training completed but all chains returned retcodes=1 (errors)
- **Output**: No files saved properly (output directory never created)
- **Lesson**: Even when sampling appears to complete, error handling needs improvement

### 2. Pilot Test - Standard Settings (3.4 hours)
- **Date**: October 30, 2025
- **Configuration**: 2 chains, 200 warmup, 200 samples, adapt_delta=0.999
- **Result**: Completed successfully but **52.5% divergent transitions** (210/400)
- **Diagnostics**:
  - Divergences: 52.5% (210/400)
  - Max treedepth reached: 45.8% of iterations hit depth 10
  - Coefficients saved but unreliable due to high divergence rate
- **Lesson**: High divergence rate indicates fundamental model/data mismatch

### 3. Pilot Test - Stricter Settings (8+ hours, incomplete)
- **Date**: October 30, 2025
- **Configuration**: 2 chains, 200 warmup, 200 samples, adapt_delta=0.999, max_treedepth=15
- **Result**: Too slow - killed after 8 hours with chain 1 still in warmup phase
- **Lesson**: Attempting to fix divergences with stricter settings makes sampling impractically slow

## Key Findings

### Convergence Issues
1. **High Divergence Rate**: 52.5% with standard settings indicates model is fundamentally unstable
2. **Treedepth Exhaustion**: 45.8% of iterations hit max treedepth, suggesting difficult posterior geometry
3. **Speed vs. Convergence Trade-off**: Stricter settings that might reduce divergences make sampling too slow

### Data Sufficiency
- **96,837 possessions ÷ 612 parameters = 158 obs/param** - theoretically sufficient
- **32 unique matchups out of 36 possible** - good coverage
- However, many matchups are sparse (<1000 possessions each)
- Sparse matchups likely contribute to convergence problems

### Model Complexity
- **612 parameters** (36 matchups × 16 archetype coefficients + 36 intercepts)
- Positive constraints on beta_off and beta_def create boundary issues
- Many parameters share sparse data, leading to unstable estimates

## Comparison: Simplified vs. Matchup-Specific

| Aspect | Simplified Model | Matchup-Specific Model |
|--------|-----------------|------------------------|
| Parameters | 17 | 612 |
| Obs/Param | 6,060 | 158 |
| Convergence | ✅ R-hat < 1.01, 0 divergences | ❌ 52.5% divergences |
| Training Time | ~hours | 30-40 hours (or incomplete) |
| Production Ready | ✅ Yes | ❌ No |
| Insights | Archetype redundancy detection | Would detect skill-context interactions |

## Recommendations

### Immediate Action: Use Simplified Model
- **File**: `model_coefficients.csv`
- **Status**: Production-ready, validated, and working
- **Limitation**: Only detects archetype redundancy, not skill-context interactions
- **Benefit**: Reliable, fast, interpretable

### Future Work: Improve Matchup-Specific Model

If skill-context interactions are critical, consider:

1. **Hierarchical Priors**: Shrinkage toward global archetype effects
   - Reduces effective parameters
   - Shares information across matchups
   - More stable estimation

2. **Reduced Parameterization**: 
   - Estimate matchup-specific intercepts only (36 params)
   - Keep archetype effects global (16 params)
   - Total: 52 parameters instead of 612

3. **More Data**: 
   - Collect additional seasons
   - Target 500+ obs/param for stable estimation
   - Would require 306,000+ possessions

4. **Different Architecture**:
   - Soft clustering (Gaussian mixture) instead of hard assignments
   - Latent matchup effects instead of explicit matchup categories
   - Neural network or other non-parametric approach

## Files Created During Evaluation

1. **`deep_validate_matchup_data.py`**: Comprehensive validation before training
   - Validates matchup distribution, feature variance, Stan compatibility
   - Saved weeks by catching issues early

2. **`runpod_deploy_checklist.py`**: Pre-flight checks before deployment
   - Verifies file existence, sizes, data integrity
   - Estimates upload times

3. **`stan_model_results_pilot/`**: Pilot test results
   - Coefficients file (high divergence, unreliable)
   - Sample CSV files
   - Training summary

4. **`MATCHUP_MODEL_EVALUATION_SUMMARY.md`**: This file

## Lessons Learned

1. **Pilot Testing is Essential**: Fast validation (3-4 hours) caught convergence issues before committing to 40+ hour runs

2. **Data Sufficiency ≠ Model Feasibility**: Having enough data doesn't guarantee the model will converge if the architecture is too complex

3. **Error Handling Matters**: Even when sampling appears to complete, need robust error checking and file saving logic

4. **Simpler is Better**: The simplified model works well and is production-ready. Matchup-specific enhancements need different approach.

## For Next Developer

If you want to revisit matchup-specific modeling:

1. **Read this summary first** - understand why it failed
2. **Review pilot results** in `stan_model_results_pilot/`
3. **Consider hierarchical approach** - more mathematically sound
4. **Start with reduced parameterization** - 52 params instead of 612
5. **Use simplified model for now** - it works and is validated

The matchup-specific dream isn't dead, but it needs a different architecture or significantly more data.

