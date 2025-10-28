# Matchup-Specific Model Failure Analysis

**Date**: October 28, 2025  
**Diagnosis**: ❌ **MODEL FAILED - Fundamentally Overparameterized**

## Critical Diagnostics

From the training output:

```
Chain 1: 458 divergent transitions (91.6%)
Chain 2: 466 divergent transitions (93.2%)  
Chain 3: 470 divergent transitions (94.0%)
Chain 4: 462 divergent transitions (92.4%)
```

**Result**: 91-94% divergent transitions = **MODEL IS BROKEN**

## First Principles Analysis

### Problem #1: Overparameterization

**Parameters**: 612 total
- 36 intercepts
- 288 offensive coefficients (36 matchups × 8 archetypes)
- 288 defensive coefficients (36 matchups × 8 archetypes)

**Data**: 25,000 possessions (subsampled from 96K)

**Ratio**: 25,000 observations / 612 parameters = **40.8 obs/param**

### Why This Fails

**Rule of thumb**: Need **≥50-100 obs/param for stable MCMC**

- Our ratio: **40.8 obs/param** ❌
- Many parameters share sparse data (only 32/36 matchups exist)
- Sparse matchups get few possessions → unstable estimates → divergences

### Problem #2: Constrained Priors Causing Issues

Stan model line 24-25:
```stan
matrix<lower=0>[36, 8] beta_off;  // Must be positive
matrix<lower=0>[36, 8] beta_def;  // Must be positive  
```

**The Issue**: With <50 obs/param + positive constraints + sparse matchups:
- HMC hits the boundary (parameter → 0)
- Creates sharp corners in parameter space
- HMC diverges trying to explore these boundaries
- Results in 91% divergent transitions

### Evidence from Coefficients

Looking at the saved coefficients:

**Matchup 0**: Most coefficients ≈ 6e-06 (essentially zero)
- Only 11,898 possessions for this matchup
- Spread across 8 archetypes = ~1,487 per archetype
- Not enough data!

**Matchup 1**: Coefficients = 0.311 to 3.16 (reasonable)
- Only 1,898 possessions
- Better distribution but still sparse

**Matchup 35**: Most coefficients ≈ 1e-05 (essentially zero)  
- Only 504 possessions!
- For 16 parameters = 31 obs/parameter
- Completely insufficient

### The Mathematics

For a binomial-like parameter (bounded parameter space):
- Need **≥100 observations** per parameter for stable inference
- We have **~40 observations** per parameter on average
- For sparse matchups (like matchup 35), we have **~31 obs/16 params = 1.9 obs/param**

This is **fundamentally insufficient**.

## Root Cause

**The matchup-specific model is too complex for available data**.

Even with 96,837 possessions, you have:
- Only 32 unique matchups (not all 36 exist)
- Many matchups have <1000 possessions
- With 16 parameters per matchup, some matchups get <50 obs/param

**This model architecture CANNOT work** without much more data.

## Solutions

### Option A: Simplified Architecture (RECOMMENDED)

Use the existing **simplified model** that already works:
- 17 parameters total (1 intercept + 8 offensive + 8 defensive)
- Trained on 103,047 possessions
- **R-hat < 1.01** (converged!)
- Already validated

**Why this works**:
- 17 params vs 612 params = 36× simpler
- All archetype coefficients are global (not matchup-specific)
- 103K / 17 = 6,060 obs/param (excellent!)

### Option B: Reduced Matchup Complexity

If you really need matchup-specific effects:
1. **Reduce matchups**: Use 3×3 supercluster system (9 matchups vs 36)
2. **Reduce parameters**: Estimate aggregate effects, not per-archetype
3. **Result**: 9 matchups × ~8 params = 72 total (manageable)

### Option C: Accept Current Model (NOT RECOMMENDED)

The coefficients are **meaningless**:
- 91% divergent transitions
- Many near-zero (sparse data)
- Can't trust any inference

## Recommendation

**STOP using the matchup-specific approach**. Use the proven simplified model instead:

- File: `production_bayesian_data.csv` 
- Model: `bayesian_model_k8.stan`
- Coefficients: `model_coefficients.csv` (already trained!)
- Status: ✅ **VALIDATED**

The simplified model already:
- Passes convergence diagnostics
- Has interpretable coefficients  
- Correctly identifies fit issues (Westbrook-Lakers case)
- Production-ready

## Lesson Learned

This is a classic example of **overparameterization**:
- 612 parameters is too ambitious
- Need ≥10× more data for this architecture
- The matchup-specific dream is mathematically infeasible with current data

The simplified model is not a "compromise" - it's the **correct** choice for this dataset.

