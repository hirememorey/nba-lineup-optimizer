# Data Coverage Shortfall Investigation

**Date**: October 26, 2025  
**Issue**: Multi-season Bayesian data file contains only 13.1% of expected possessions

---

## Executive Summary

The `multi_season_bayesian_data.csv` file contains **231,310 rows** instead of the expected **1,770,051 possessions**, representing only **13.1% coverage**. The root cause is an **ultra-strict filtering requirement** that drops possessions when any of the 10 players lack archetype or DARKO data.

---

## The Filtering Logic (Root Cause)

### Current Implementation

```python
# Line 104 in bayesian_data_prep.py
if not all(p in archetypes and p in darko for p in home+away):
    continue
```

**Requirement**: ALL 10 players (5 home + 5 away) must have:
1. Archetype assignment
2. DARKO rating

**Result**: If ANY player fails, the ENTIRE possession is dropped.

---

## Data Coverage by Season

| Season   | DB Total  | File Rows  | Coverage | Pass Rate |
|----------|-----------|------------|----------|-----------|
| 2018-19  | 621,523   | 43,377     | 7.0%     | ~7.0%     |
| 2020-21  | 538,444   | 74,688     | 13.9%    | ~13.9%    |
| 2021-22  | 610,084   | 113,245    | 18.6%    | ~18.6%    |
| **Total** | **1,770,051** | **231,310** | **13.1%** | **13.1%** |

**Observation**: Pass rate improves over time (7% → 18.6%), suggesting archetype data coverage improves in later seasons.

---

## Why 87% of Data is Dropped

### Archetype Coverage Gap

**Per Season**:
- ~340 unique players appear in possessions
- ~200-250 players have archetype data
- ~231-252 players have both archetype AND DARKO data
- **Coverage: ~64% of players**

### The Mathematics of Failure

With 10 players per possession and 64% coverage:
- Probability all 5 offensive players have data: 0.64^5 = **1.1%**
- Probability all 5 defensive players have data: 0.64^5 = **1.1%**
- Probability all 10 players have data: 0.64^10 = **0.01%**

**Actual observed rate**: 7-19% (better than theory, likely because top players play more minutes)

### Why Players Are Missing

1. **Minor players** subbed in for brief moments
2. **Injury replacements** - deep bench players getting minutes
3. **Two-way contracts** - G-league players with limited NBA time
4. **Call-ups** - late season additions without full-season data
5. **Rotation players** outside top 250 in minutes played

---

## Evidence from the Code

### Archetype Data Availability

```python
# Historical seasons have limited archetype coverage:
# 2018-19: 234 players with archetype data (61% of possession players)
# 2020-21: 229 players with archetype data (61% of possession players)
# 2021-22: 254 players with archetype data (64% of possession players)
```

### DARKO Data Availability

```
# DARKO has broader coverage:
# 2018-19: 541 players with DARKO ratings
# 2020-21: 539 players with DARKO ratings
# 2021-22: 619 players with DARKO ratings

# But overlap with archetypes is limited:
# 2018-19: 231 players (61% coverage)
# 2020-21: 226 players (61% coverage)
# 2021-22: 252 players (64% coverage)
```

---

## The Real Question

### Is 231,310 Possessions Sufficient?

**Comparison**:
- **Paper's dataset**: 2022-23 only with ~612,620 possessions
- **Our dataset**: 231,310 possessions across 3 seasons (~77K avg/season)
- **Ratio**: 38% of paper's single-season size, but across 3 seasons

### Considerations

**Arguments FOR 231K being sufficient**:
- ✅ Multi-season provides more matchup diversity
- ✅ ~77K/season average is substantial
- ✅ Model learns from 3x the number of unique matchups
- ✅ Bayesian models can work with less data

**Arguments AGAINST**:
- ❌ Only 13.1% of available data used
- ❌ Systematically biased toward starter-heavy lineups
- ❌ Potentially misses role player interactions
- ❌ Much smaller than paper's dataset

---

## Potential Solutions

### Option A: Expand Archetype Coverage (RECOMMENDED)
**Action**: Generate archetype features for ALL 340+ players per season  
**Pros**: Use all 1.77M possessions, best model performance  
**Cons**: Time-intensive, requires running feature generation pipeline  

**Implementation**:
```bash
# For each historical season:
python src/nba_stats/scripts/generate_archetype_features.py --season 2018-19 --min-minutes 500
python src/nba_stats/scripts/generate_archetype_features.py --season 2020-21 --min-minutes 500
python src/nba_stats/scripts/generate_archetype_features.py --season 2021-22 --min-minutes 500
```

### Option B: Relax Filtering Requirements
**Action**: Allow missing players with default archetype or imputation  
**Pros**: Quick to implement, recovers ~500K-800K additional possessions  
**Cons**: Introduces modeling assumptions, may impact model quality  

**Implementation**:
```python
# Use most common archetype as default for missing players
DEFAULT_ARCHETYPE = 4  # Versatile Frontcourt Player (most common)

for missing_player in home+away:
    if missing_player not in archetypes:
        archetypes[missing_player] = DEFAULT_ARCHETYPE
```

### Option C: Filter to High-Quality Possessions Only
**Action**: Keep only possessions with full starter lineups  
**Pros**: Simple, ensures quality data  
**Cons**: Further reduces dataset, may bias toward certain game situations  

**Current State**: This is essentially what Option A does by filtering to top players

### Option D: Progressive Enhancement Strategy
**Phase 1**: Proceed with 231K possessions (current state)  
**Phase 2**: Expand archetype coverage as time permits  
**Phase 3**: Retrain model with full dataset  

---

## Recommendation

**Recommended Approach**: **Option A - Expand Archetype Coverage**

1. **Immediate**: Proceed with 231K possessions for initial model training
2. **Short-term**: Generate archetype features for all players (drop min-minutes requirement)
3. **Medium-term**: Regenerate multi-season dataset with full 1.77M possessions
4. **Long-term**: Retrain model with complete dataset

**Rationale**:
- 231K is sufficient for initial proof-of-concept
- Model validation can proceed in parallel with data expansion
- Full dataset will provide more robust model
- Archetype feature generation is automated and can run in background

---

## Current State Summary

✅ **What Works**:
- Database has all 1.77M possessions
- Archetype tables exist for all seasons  
- DARKO ratings available for all seasons
- Filtering pipeline works (just very strict)

❌ **What's Broken**:
- Only 64% player coverage for archetype features
- Only 13.1% of possessions pass filtering
- Model trained on starter-heavy lineups only
- Potential bias in training data

⚠️ **What's Unknown**:
- Whether 231K possessions is sufficient for multi-season model
- Impact of missing role players on model performance
- Whether the bias toward starters affects predictions

---

## Next Steps

1. ✅ Document the issue (this report)
2. 🔄 Proceed with Phase 2 training on 231K possessions
3. 🔄 Run archetype feature generation for ALL players in parallel
4. 🔄 Regenerate multi-season dataset when complete
5. 🔄 Retrain model with full 1.77M possessions
6. 🔄 Compare model performance

**Conclusion**: The data shortfall is **understood and documented**. We can proceed with Phase 2 using the available 231K possessions while expanding archetype coverage in parallel for future improved model training.

