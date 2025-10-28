# RunPod Training Analysis: Should We Do It?

**Date**: October 28, 2025  
**Question**: Can we get useful matchup-specific coefficients on RunPod?

## The Math (Using Full 96K Dataset)

| Metric | 25K Subset | 96K Full | Difference |
|--------|-----------|----------|------------|
| **Total obs** | 25,000 | 96,837 | **3.9× more data** |
| **Obs/param (avg)** | 40.8 | **158.3** | **3.9× better** |
| **Divergent transitions** | 91% | ??? | Unknown |
| **Expected time** | 1 hour | **30-40 hours** | Much longer |

## Key Insight from Your Question

**You correctly identified**: The simplified model only detects **redundancy** (both Archetype 4), not **skill-context interactions**.

### What Matchup-Specific Model SHOULD Capture

**Example**: LeBron vs. Westbrook on Lakers

**Simplified Model (Global Coefficients)**:
```
Both are Archetype 4 → Same coefficients
Both have similar DARKO → Similar contributions
Result: Only detects redundancy
```

**Matchup-Specific Model (Theoretical)**:
```
Matchup 12: LeBron's passing skills vs fast break defense = HIGH VALUE
            Westbrook's driving vs packed paint = LOW VALUE
Matchup 23: LeBron's shooting vs perimeter defense = MODERATE VALUE  
            Westbrook's penetration vs drop coverage = MODERATE VALUE
Result: Their skills contribute DIFFERENTLY depending on defensive style
```

## Why This Matters

The matchup-specific model answers questions like:
- **"Which archetype skills matter most against this defensive style?"**
- **"How does archetype value change in different matchup contexts?"**
- **"Is redundancy always bad, or only in certain matchups?"**

The simplified model **cannot** answer these questions.

## RunPod Feasibility Analysis

### ✅ Reasons It Might Work

1. **158 obs/param on average** (excellent!)
2. **24 matchups have >50 obs/param** (should converge)
3. **Only 7 matchups are very sparse** (can be masked/handled)
4. **Full dataset vs subsampled** = 3.9× more data per matchup

### ⚠️ Reasons It Might Still Fail

1. **Sparse matchups still exist** (7 with <20 obs/param)
2. **Divergence might persist** even with more data
3. **Parameter space is complex** (612 parameters to estimate)
4. **Cost**: 30-40 hours × ~$1-3/hour = $30-120

### 🎯 The Real Question

**Will 30-40 hours and $100 get us something useful?**

## What "Useful" Means

Even with SOME divergence, we might get:
- ✅ **24 matchups with good coefficients** (78% of possible matchups)
- ⚠️ **7 matchups with poor coefficients** (mask them in predictions)
- ✅ **Answer to your insight**: How archetype skills vary by matchup
- ✅ **Better than simplified model** for the 24 working matchups

## Recommendation

**YES, use RunPod** if:
1. You want matchup-specific insights
2. You can afford $50-100
3. You're okay with some matchups potentially failing

**Alternative approach**: Train on the **25 matchups that have >500 obs each**

This would be:
- 25 matchups × 16 params = 400 parameters (vs 612)
- Fewer parameters = better convergence
- Still captures matchup-specific effects
- Could train in 15-20 hours instead of 30-40

## Comparison Table

| Approach | Params | Obs/Param | Expected Time | Cost | Success Rate |
|----------|--------|-----------|---------------|------|--------------|
| Full 96K | 612 | 158 | 30-40 hrs | $100 | 75% matchups |
| Subsample | 612 | 41 | 1 hour | $5 | Failed |
| Top 25 matchups | 400 | 194 | 15-20 hrs | $50 | 90% matchups |
| Simplified | 17 | 6,060 | Complete | Done | 100% |

## My Recommendation

**Option B: Train on Top 25 Matchups** (best trade-off)

This gives you:
- Matchup-specific effects (your key insight)
- Better convergence (400 params vs 612)
- Lower cost ($50 vs $100)
- Faster (15-20 hrs vs 30-40 hrs)
- Only lose 7 sparse matchups

Want me to implement this selective-training approach?

