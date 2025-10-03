# Data Quality Troubleshooting Guide

**Date**: October 3, 2025  
**Status**: ✅ **CRITICAL REFERENCE DOCUMENT**

## Overview

This guide provides solutions for common data quality issues encountered during NBA data pipeline operations. It is based on real issues discovered and resolved during the project's development.

## Quick Diagnosis

**Always start with the comprehensive verification script:**

```bash
python verify_database_sanity.py
```

This will identify the specific issue and provide detailed error messages.

## Common Issues and Solutions

### 1. Drive Statistics Have No Variance (All Identical Values)

**Symptoms:**
- `verify_database_sanity.py` shows "Only X unique values" warning for DRIVES
- All players have identical drive statistics (e.g., all 3.0 drives)

**Root Cause:**
The `populate_player_drive_stats.py` script has a critical bug where it calls the `leaguedashptstats` API for individual players, but this endpoint returns ALL players' data. The script takes the first row and applies it to every player.

**Solution:**
```bash
# The fix has been applied, but if you encounter this issue:
# 1. Check if the bug exists in your version of populate_player_drive_stats.py
# 2. Look for this pattern (WRONG):
#    drive_stats = client.get_player_drive_stats(player_id, season)
#    return dict(zip(headers, rowSet[0]))  # BUG: Always takes first row

# 3. The correct approach is to call the API once for all players:
#    drive_stats = client.get_player_drive_stats(0, season)  # 0 = all players
#    for row in result_set['rowSet']:
#        row_dict = dict(zip(headers, row))
#        # Process each player individually
```

**Verification:**
```bash
sqlite3 src/nba_stats/db/nba_stats.db "SELECT COUNT(DISTINCT drives) FROM PlayerSeasonDriveStats WHERE season = '2024-25';"
# Should return > 100 unique values, not 1 or 2
```

### 2. PlayerArchetypeFeatures Has Wrong Data

**Symptoms:**
- Verification shows data range issues
- Clustering produces nonsensical results

**Root Cause:**
The `PlayerArchetypeFeatures` table was generated from corrupted source data.

**Solution:**
```bash
# Regenerate the archetype features table with corrected source data
python src/nba_stats/scripts/generate_archetype_features.py --season 2024-25
```

**Verification:**
```bash
python verify_database_sanity.py
# Should show all verifications passing
```

### 3. API Timeouts or Empty Responses

**Symptoms:**
- Scripts hang indefinitely
- Empty data in tables
- "No data returned" warnings

**Root Cause:**
NBA Stats API is unreliable and can timeout or return empty responses.

**Solution:**
Follow the "Isolate with curl First" methodology from `docs/api_debugging_methodology.md`:

1. **Test with curl first:**
```bash
curl 'https://stats.nba.com/stats/leaguedashptstats?PlayerID=0&Season=2024-25&PerMode=PerGame&SeasonType=Regular+Season&LeagueID=00&PlayerOrTeam=Player&PtMeasureType=Drives' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'x-nba-stats-token: true' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' \
  -H 'x-nba-stats-origin: stats' \
  -H 'Referer: https://www.nba.com/' \
  --compressed
```

2. **If curl works but Python doesn't:**
   - Check if your Python code matches the working curl parameters
   - Verify headers are identical
   - Check for hardcoded season parameters

3. **If curl fails:**
   - Try different season formats (`2024-25` vs `2023-24`)
   - Check if the endpoint URL has changed
   - Verify the API is accessible

### 4. Data Range Validation Failures

**Symptoms:**
- `verify_database_sanity.py` shows range check failures
- Values outside expected ranges

**Root Cause:**
Expected ranges in verification script are too conservative or data has changed.

**Solution:**
1. **Check if the data is actually reasonable:**
```bash
sqlite3 src/nba_stats/db/nba_stats.db "SELECT MIN(DRIVES), MAX(DRIVES), COUNT(DISTINCT DRIVES) FROM PlayerArchetypeFeatures WHERE season = '2024-25';"
```

2. **Update expected ranges in `verify_database_sanity.py`:**
```python
self.expected_ranges = {
    'DRIVES': (0.0, 25.0),     # Update based on actual data
    'AVGDIST': (0.0, 25.0),    # Update based on actual data
    # ... other ranges
}
```

### 5. Missing Data in Source Tables

**Symptoms:**
- Source table spot-checks fail
- "Max value: 0.0" warnings

**Root Cause:**
Upstream data population scripts failed silently.

**Solution:**
1. **Check which tables are affected:**
```bash
python verify_database_sanity.py
# Look for Layer 1.5 failures
```

2. **Re-run the specific population script:**
```bash
# For drive stats (if fixed):
python src/nba_stats/scripts/populate_player_drive_stats.py --season 2024-25

# For other stats:
python master_data_pipeline.py --season 2024-25
```

3. **Verify the fix:**
```bash
python verify_database_sanity.py
```

### 6. Database Schema Mismatches

**Symptoms:**
- "no such column" errors
- "table doesn't exist" errors

**Root Cause:**
Database schema is out of sync with code expectations.

**Solution:**
1. **Check actual schema:**
```bash
sqlite3 src/nba_stats/db/nba_stats.db ".schema TableName"
```

2. **Run table creation scripts:**
```bash
python src/nba_stats/scripts/create_tables.py
```

3. **Verify with documentation:**
Check `docs/data_dictionary.md` for the correct schema.

## Prevention Strategies

### 1. Always Run Verification First
```bash
python verify_database_sanity.py
```

### 2. Use the "Isolate with curl First" Principle
Never debug Python code when API calls fail. Always test with curl first.

### 3. Check Data Variance
Always verify that data has reasonable variance, not just that it exists.

### 4. Monitor Source Tables
The verification script includes Layer 1.5 specifically to catch silent upstream failures.

## Emergency Recovery

If the database is completely corrupted:

1. **Backup current state:**
```bash
cp src/nba_stats/db/nba_stats.db src/nba_stats/db/nba_stats.db.backup
```

2. **Re-run the entire pipeline:**
```bash
python master_data_pipeline.py --season 2024-25
```

3. **Regenerate archetype features:**
```bash
python src/nba_stats/scripts/generate_archetype_features.py --season 2024-25
```

4. **Verify everything:**
```bash
python verify_database_sanity.py
```

## Getting Help

If you encounter an issue not covered in this guide:

1. **Check the logs:**
   - Look for error messages in the console output
   - Check log files in the project directory

2. **Run verification with verbose output:**
```bash
python verify_database_sanity.py 2>&1 | tee verification.log
```

3. **Check the API directly:**
   - Use the curl commands from `docs/api_debugging_methodology.md`
   - Verify the API is working independently

4. **Review the source code:**
   - Check the specific population script that's failing
   - Look for hardcoded values or incorrect API usage

## Key Principles

1. **Data Quality is Critical**: Never proceed with analysis if verification fails
2. **Isolate External Dependencies**: Test APIs with curl before debugging Python
3. **Verify Variance**: Data should have reasonable variance, not just exist
4. **Check Source Tables**: Silent upstream failures are common and dangerous
5. **Document Everything**: Keep track of what you've tried and what worked

Remember: The verification script is your friend. It will catch 99% of data quality issues before they cause problems in your analysis.
