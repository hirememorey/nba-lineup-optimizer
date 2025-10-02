# Database Sanity Report

**Database:** `src/nba_stats/db/nba_stats.db`
**Timestamp:** 2025-10-02T10:45:11.363440

## Summary

- ✅ **Passed:** 9/9
- ❌ **Failed:** 0/9

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

### ✅ Check for logical shooting stats (FGM <= FGA)

**Status:** `PASS`

**Description:** Checks for any records where field goals made are greater than field goals attempted.

---

### ✅ Check for logical three-point stats (FG3M <= FG3A)

**Status:** `PASS`

**Description:** Checks for any records where three-pointers made are greater than three-pointers attempted.

---

### ✅ Check for logical free throw stats (FTM <= FTA)

**Status:** `PASS`

**Description:** Checks for any records where free throws made are greater than free throws attempted.

---

### ✅ Check for negative stats

**Status:** `PASS`

**Description:** Checks for any negative values in core statistical columns.

---

### ✅ Check for orphan players in PlayerSeasonRawStats

**Status:** `PASS`

**Description:** Checks for records in `PlayerSeasonRawStats` that don't have a corresponding player in the `Players` table.

---

### ✅ Check for orphan players in PlayerSalaries

**Status:** `PASS`

**Description:** Checks for records in `PlayerSalaries` that don't have a corresponding player in the `Players` table.

---

