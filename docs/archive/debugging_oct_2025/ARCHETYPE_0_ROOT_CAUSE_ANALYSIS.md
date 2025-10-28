# Archetype 0 Root Cause Analysis

**Date**: October 26, 2025  
**Issue**: Archetype 0 has zero usage; Archetype 8 data is being lost

## The Bug

### Index Mismatch Between Archetype IDs and Column Indices

**Archetype CSV Files** use IDs: **1, 2, 3, 4, 5, 6, 7, 8**  
**Z-matrix Columns** use indices: **0, 1, 2, 3, 4, 5, 6, 7**

The code creates an off-by-one mapping that:
1. ❌ Leaves column `z_off_0` always empty
2. ❌ Stores archetype 8 in `z_off[8]` which is never retrieved
3. ✅ Uses columns 1-7 for archetypes 1-7

---

## Root Cause Trace

### Step-by-Step Data Flow

#### Step 1: Load Archetype Mappings
```python
# archetypes is a dict: {player_id: archetype_id}
# archetype_id values are 1, 2, 3, 4, 5, 6, 7, 8
```

#### Step 2: For Each Possession
```python
off_arch = [int(archetypes[p]) for p in off_players]
# Example: [1, 4, 5, 6, 8] (five players with archetypes)
```

#### Step 3: Aggregate Skills by Archetype (Line 116)
```python
for i, p in enumerate(off_players):
    z_off[off_arch[i]] += float(darko[p]['o_darko'])
    # If off_arch[i] = 8, stores in z_off[8]
    # Dictionary keys: 1, 2, 3, 4, 5, 6, 7, 8
```

#### Step 4: Write to Output Columns (Line 122)
```python
for a in range(8):  # a is 0, 1, 2, 3, 4, 5, 6, 7
    rec[f'z_off_{a}'] = z_off.get(a, 0.0)
    #                                 ^^^^
    # Looking for dictionary keys 0-7, but keys are 1-8!
```

### The Problem

```python
z_off dictionary has keys: 1, 2, 3, 4, 5, 6, 7, 8
Loop iterates:             0, 1, 2, 3, 4, 5, 6, 7

z_off.get(0) → returns 0.0 (key 0 doesn't exist) ← COLUMN z_off_0 STAYS EMPTY
z_off.get(1) → returns z_off[1] (archetype 1) ✓
z_off.get(2) → returns z_off[2] (archetype 2) ✓
...
z_off.get(7) → returns z_off[7] (archetype 8) ✓
z_off.get(8) → NEVER RETRIEVED (loop stops at 7) ← ARCHETYPE 8 DATA LOST!
```

---

## Current (Broken) Mapping

| CSV Archetype ID | Dictionary Key | Column Index | Column Name | Result |
|------------------|----------------|--------------|-------------|---------|
| 1 | z_off[1] | 0 | z_off_0 | ✅ Empty (wrong column) |
| 2 | z_off[2] | 1 | z_off_1 | ✅ Works |
| 3 | z_off[3] | 2 | z_off_2 | ✅ Works |
| 4 | z_off[4] | 3 | z_off_3 | ✅ Works |
| 5 | z_off[5] | 4 | z_off_4 | ✅ Works |
| 6 | z_off[6] | 5 | z_off_5 | ✅ Works |
| 7 | z_off[7] | 6 | z_off_6 | ✅ Works |
| 8 | z_off[8] | 7 | z_off_7 | ❌ NEVER RETRIEVED |

**Evidence**:
- `z_off_0` has 0 non-zero values (should have archetype 1)
- `z_off_7` has 29,971 non-zero values (should be archetype 8, but actually contains archetype 7)
- Archetype 8 data stored in `z_off[8]` is **completely lost**

---

## Evidence from Multi-Season Data

```
z_off_0: 0 non-zero values        ← Should have archetype 1 data
z_off_1: 170,245 non-zero values  ← Has archetype 1 data
z_off_2: 74,690 non-zero values   ← Has archetype 2 data
z_off_3: 73,049 non-zero values   ← Has archetype 3 data
z_off_4: 208,704 non-zero values  ← Has archetype 4 data
z_off_5: 130,484 non-zero values  ← Has archetype 5 data
z_off_6: 90,340 non-zero values   ← Has archetype 6 data
z_off_7: 29,971 non-zero values   ← Should be archetype 8, but has archetype 7!
```

**Archetype 8 exists** in the CSV files (39 players in 2021-22, 36 in 2020-21), but their data is **completely lost** because it's stored in `z_off[8]` which is never accessed.

---

## The Fix

There are two possible solutions:

### Solution A: Change Column Loop to Access Keys 1-8
```python
# OLD (line 122):
for a in range(8):  # a is 0-7
    rec[f'z_off_{a}'] = z_off.get(a, 0.0)

# NEW:
for a in range(1, 9):  # a is 1-8
    rec[f'z_off_{a-1}'] = z_off.get(a, 0.0)
```

**Mapping**: Archetype 1→z_off_0, Archetype 2→z_off_1, ..., Archetype 8→z_off_7

### Solution B: Change Dictionary Keys to 0-7 (Preferred)
```python
# When loading archetypes (line 26):
archetypes = pd.Series(df['archetype_id'].values - 1, index=df['player_id']).to_dict()
#                                                    ^^^^^ Subtract 1 to get 0-7

# Keep line 122 as is:
for a in range(8):
    rec[f'z_off_{a}'] = z_off.get(a, 0.0)
```

**Mapping**: Archetype IDs are now 0-7 in the dictionary, match column indices 0-7

### Recommendation

**Use Solution B** because:
1. ✅ Aligns archetype IDs with array indices (0-based)
2. ✅ Simplifies code (no conversion needed)
3. ✅ Standard practice in Python to use 0-based indexing
4. ✅ Only requires changing how archetypes are loaded

---

## Impact

- **Current State**: Model effectively trained on 7 archetypes (using columns 1-7)
- **Archetype 8**: Completely lost (8th archetype)
- **Archetype 1**: Mapped to column z_off_1 instead of z_off_0
- **Column 0**: Always empty (no data ever stored there)

**This explains why**:
- Only 3 matchups exist (model broken, supercluster mapping likely also broken)
- Archetype distribution looks wrong
- Model training may not be capturing all player types

---

## Next Steps

1. Apply Solution B in `src/nba_stats/scripts/bayesian_data_prep.py`
2. Re-run multi-season data generation
3. Verify all 8 archetypes have non-zero usage
4. Verify archetype 8 appears in the dataset
5. Regenerate training data with correct mappings

