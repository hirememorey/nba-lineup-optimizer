# Database Sanity Report

### Executive Summary (Oct 2, 2025)

This report identified a **critical, silent bug** in the data pipeline's database write operation.

- **Finding:** The `PlayerSeasonRawStats` and `PlayerSeasonAdvancedStats` tables exist and contain the correct number of player rows, but they are **missing all statistical columns** (e.g., `fgm`, `fga`, `pts`, `ast`).
- **Root Cause:** The script responsible for populating these tables is failing to map the processed data to the correct database columns, resulting in a silent schema mismatch.
- **Conclusion:** The database is currently **unusable for analysis**. The immediate priority is to debug and fix the persistence logic in the master data pipeline.

---

**Database:** `src/nba_stats/db/nba_stats.db`
**Timestamp:** 2025-10-02T09:59:37.170931

## Summary

- ✅ **Passed:** 5/9
- ❌ **Failed:** 4/9

## Detailed Check Results

### ✅ Check for PlayerSeasonRawStats table

**Status:** `PASS`

**Description:** Verifies that the essential `PlayerSeasonRawStats` table exists.

---

### ✅ Check for PlayerSeasonAdvancedStats table

**Status:** `PASS`

**Description:** Verifies that the essential `PlayerSeasonAdvancedStats` table exists.

---

### ✅ Check for data in PlayerSeasonRawStats

**Status:** `PASS`

**Description:** Verifies that `PlayerSeasonRawStats` has a reasonable amount of data for the season ( > 500 players).

---

### ❌ Check for logical shooting stats (FGM <= FGA)

**Status:** `ERROR`

**Description:** Checks for any records where field goals made are greater than field goals attempted.

**Error:**
```
no such column: fgm
```

---

### ❌ Check for logical three-point stats (FG3M <= FG3A)

**Status:** `ERROR`

**Description:** Checks for any records where three-pointers made are greater than three-pointers attempted.

**Error:**
```
no such column: fg3m
```

---

### ❌ Check for logical free throw stats (FTM <= FTA)

**Status:** `ERROR`

**Description:** Checks for any records where free throws made are greater than free throws attempted.

**Error:**
```
no such column: ftm
```

---

### ❌ Check for negative stats

**Status:** `ERROR`

**Description:** Checks for any negative values in core statistical columns.

**Error:**
```
no such column: minutes
```

---

### ✅ Check for orphan players in PlayerSeasonRawStats

**Status:** `PASS`

**Description:** Checks for records in `PlayerSeasonRawStats` that don't have a corresponding player in the `Players` table.

---

### ✅ Check for orphan players in PlayerSalaries

**Status:** `PASS`

**Description:** Checks for records in `PlayerSalaries` that don't have a corresponding player in the `Players` table.

---

