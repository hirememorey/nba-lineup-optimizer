# Critical Issue: Matchup-Specific Data Generation

**Date**: October 27, 2025  
**Status**: 🚨 **CRITICAL BUG IDENTIFIED** - Cannot proceed with training

## The Problem

During Phase 0 validation testing, we discovered that **ALL possessions are being assigned to matchup_id = 35** (the maximum matchup value). This means:

- **All offensive lineups** → supercluster 5  
- **All defensive lineups** → supercluster 5  
- **Result**: Only 1 unique matchup out of 36 possible (6×6 matrix)

## Root Cause Analysis

### Issue #1: Placeholder Feature Generation

The `_extract_lineup_features()` function (lines 113-157 in `generate_matchup_specific_bayesian_data.py`) is **generating placeholder estimates** rather than real lineup statistics:

```python
def _extract_lineup_features(archetypes_list: list, season: str) -> dict:
    """Extract lineup features for clustering (must match the 14 features used in multi-season model)."""
    # ... placeholder code ...
    
    # For the prototype, we'll create reasonable estimates based on archetype composition
    # In production, these would be calculated from actual lineup performance data
```

**The Problem**: All lineups get VERY similar features because:
1. Most features are hardcoded to league averages (w_pct=0.5, plus_minus=0.0, off_rating=100, pace=100)
2. Only minor variations based on archetype counts
3. No actual lineup performance data is used

### Issue #2: Feature Calculation Missing

The multi-season supercluster model expects these 14 features:
- `w_pct` - Win percentage
- `plus_minus` - Net rating  
- `off_rating` - Offensive rating
- `pace` - Pace
- `ast_pct` - Assist percentage
- `ast_to` - Assist-to-turnover ratio
- `pct_fga_2pt` - 2pt shot attempt percentage
- `pct_fga_3pt` - 3pt shot attempt percentage  
- `pct_pts_2pt` - 2pt point percentage
- `pct_pts_2pt_mr` - Mid-range point percentage
- `pct_pts_3pt` - 3pt point percentage
- `pct_pts_ft` - Free throw point percentage
- `pct_pts_off_tov` - Points off turnover percentage
- `pct_pts_paint` - Paint scoring percentage

**Current State**: None of these are calculated from actual lineup data in the database!

### Evidence from Validation Tests

```
10K test: 1,374 possessions → ALL assigned to matchup 35
50K test: 7,081 possessions → ALL assigned to matchup 35

Expected: Should have distribution across all 36 matchups
Actual: Only matchup 35 (5×6 + 5 = 35)
```

## Impact

**This is a BLOCKER**:
- ✅ Data generation pipeline works (no crashes)
- ❌ All data is invalid (no matchup diversity)
- ❌ Model cannot learn matchup-specific effects
- ❌ Training would be meaningless (all possessions have same matchup_id)

## The Real Issue

Looking back at STATUS.md (October 27, 2025):

> **Phase 1 Complete**: Matchup-specific architecture (36×16 parameters) validated on prototype. Prototype validated on 1,374 possessions

**Critical Discovery**: The "validation" was on **placeholder features**, not real lineup data! The phase 1 prototype appears to have been working with fake/simplified features.

## What Needs to Be Fixed

### Option A: Calculate Real Lineup Features (RECOMMENDED)

1. **Query actual lineup performance data** from the database
2. **Calculate the 14 required features** from real statistics
3. **Join PlayerLineupStats or similar tables** to get actual metrics
4. **Re-generate all matchup-specific datasets**

### Option B: Use Simplified Archetype-Based Features

Since we don't have real lineup data readily available:
1. **Generate realistic feature variations** based on archetype compositions
2. **Use archetype statistics** to create plausible feature ranges
3. **Ensure diversity** across the 6 superclusters

### Option C: Skip Matchup-Specific Model

If real lineup features are not feasible:
1. **Use the simplified model** (already validated)
2. **Focus on archetype × archetype interactions** instead of supercluster matchups
3. **Reduce model complexity** to match available data

## Recommended Action

**STOP Phase 2.1 training**. Before proceeding, we must:

1. ✅ **Detect the issue** (COMPLETED - pre-mortem worked!)
2. 🔄 **Investigate available lineup data** in the database
3. 🔄 **Design feature calculation approach**
4. 🔄 **Re-implement _extract_lineup_features() with real data**
5. 🔄 **Re-run validation tests**
6. 🔄 **Proceed with training only if matchup diversity is achieved**

## Lessons Learned

The pre-mortem was **absolutely correct**! The critical assumption that failed was:
> "The data generation pipeline produces valid, diverse matchup assignments"

This assumption was **completely wrong**. By validating before training, we caught this in 10 seconds instead of 6 weeks.

## Next Steps

1. **Investigate database**: What lineup performance data is available?
2. **Design solution**: How to calculate 14 real features from available data?
3. **Implement fix**: Re-build feature extraction with real data
4. **Re-validate**: Run validation tests again
5. **Proceed**: Only if matchup diversity ≥ 10-20 matchups


