# Quick Start for New Developer

**Last Updated**: October 30, 2025  
**Status**: Project is production-ready with validated simplified model

## What You Need to Know (5-Minute Read)

### ✅ What Works (Use This)
- **Simplified Model**: `model_coefficients.csv` - 17 parameters, fully validated
- **Production Ready**: Converged (R-hat < 1.01, 0 divergences)
- **Validated**: Correctly identifies player fit issues (e.g., Westbrook-LeBron redundancy)
- **Use Case**: Archetype redundancy detection for roster construction

### ⚠️ What We Tried (Don't Repeat This)
- **Matchup-Specific Model**: 612 parameters, attempted but shows 52.5% divergent transitions
- **Issue**: Too complex for available data despite having 158 obs/param
- **Outcome**: Not production-ready, requires different architecture
- **See**: `MATCHUP_MODEL_EVALUATION_SUMMARY.md` for full details

## Essential Files

### Documentation (Read First)
1. **`STATUS.md`** - Current state, what works, what doesn't
2. **`DEVELOPER_HANDOFF.md`** - Complete context on where we left off
3. **`MATCHUP_MODEL_EVALUATION_SUMMARY.md`** - Why matchup-specific model failed

### Production Model
- **`model_coefficients.csv`** - Use this for predictions
- **`production_bayesian_data.csv`** - Training data for simplified model
- **`bayesian_model_k8.stan`** - Simplified Stan model

### Validation Tools
- **`deep_validate_matchup_data.py`** - Comprehensive data validation
- **`runpod_deploy_checklist.py`** - Pre-flight checks before training

## What to Do If You Want to...

### Use the System As-Is
```bash
# The simplified model is already trained and validated
# Just use model_coefficients.csv in your predictions
cat model_coefficients.csv
```

### Understand Why Matchup-Specific Failed
```bash
# Read the evaluation summary
cat MATCHUP_MODEL_EVALUATION_SUMMARY.md

# Check pilot results (high divergence)
ls stan_model_results_pilot/
```

### Try to Improve Matchup-Specific Model
**Read first**: `MATCHUP_MODEL_EVALUATION_SUMMARY.md` recommendations:
1. Hierarchical priors (shrinkage toward global effects)
2. Reduced parameterization (52 params instead of 612)
3. More data (need 306,000+ possessions)
4. Different architecture (soft clustering, latent effects)

### Validate Your Own Changes
```bash
# Run deep validation before any training
python deep_validate_matchup_data.py \
    --data matchup_specific_bayesian_data_full.csv \
    --stan bayesian_model_k8_matchup_specific.stan

# Run pre-flight checklist
python runpod_deploy_checklist.py
```

## Key Lessons Learned

1. **Pilot Testing Saves Time**: Fast 3-4 hour tests caught convergence issues before 40+ hour runs
2. **Data Sufficiency ≠ Model Feasibility**: Having enough data doesn't guarantee convergence if architecture is too complex
3. **Simpler is Better**: The 17-parameter model works well; 612-parameter model doesn't
4. **Always Validate**: Deep validation scripts catch issues early

## Next Steps

### Immediate
- ✅ **Use simplified model** (`model_coefficients.csv`) - it works
- ✅ **Deploy to production** - model is validated and ready

### Future Work
- Consider hierarchical priors for matchup-specific approach
- Explore reduced parameterization (52 params)
- Collect more data if matchup-specific insights are critical
- Or accept limitation of simplified model (works well for redundancy detection)

## Questions?

- **What model should I use?** → Simplified model (`model_coefficients.csv`)
- **Why not matchup-specific?** → Read `MATCHUP_MODEL_EVALUATION_SUMMARY.md`
- **Can I improve it?** → See "Future Work" section in evaluation summary
- **How do I validate changes?** → Use `deep_validate_matchup_data.py`

## Files Created During Evaluation

These files document what we learned:
- `deep_validate_matchup_data.py` - Validation tool (use this!)
- `runpod_deploy_checklist.py` - Pre-flight checks (use this!)
- `MATCHUP_MODEL_EVALUATION_SUMMARY.md` - Full evaluation report
- `stan_model_results_pilot/` - Pilot test results (high divergence)

