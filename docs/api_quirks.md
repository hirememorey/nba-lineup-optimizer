# NBA Stats API Quirks and Inconsistencies

**Date**: October 1, 2025  
**Status**: 🔍 **INVESTIGATION IN PROGRESS**

This document catalogs the discovered quirks and inconsistencies in the NBA Stats API responses, based on forensic analysis of cached responses. This knowledge is critical for maintaining the API client and preventing future debugging cycles.

## Methodology

We use a "cache-first" debugging approach:
1. Examine cached JSON responses in `src/nba_stats/.cache/`
2. Document the actual structure and content
3. Fix our code to match the API's reality, not our assumptions

## Critical Findings

### Response Structure Inconsistencies

#### `resultSets` Structure Variations
- **Some endpoints**: `resultSets` is an array of objects `[{...}]`
- **Other endpoints**: `resultSets` is a single object `{...}`
- **Impact**: Parsing logic must handle both cases

### Column Name Mappings

#### Free Throw Metrics
- **Expected**: `FTPCT`, `FTr`
- **Actual in Base Stats**: `FT_PCT`, `FTA`
- **Actual in Advanced Stats**: Different column names entirely
- **Impact**: Metric mapping configuration needs correction

### Endpoint-Specific Quirks

*[To be populated as investigations progress]*

## Investigation Log

### 2025-10-01: Initial Investigation
- Started forensic analysis of 5 critical API failures
- Created `api_forensics.ipynb` for systematic investigation
- Identified cache-first methodology as most effective approach

### 2025-10-01: Resolution Complete ✅
- **All 5 critical failures resolved** using cache-first debugging approach
- **Smoke test success rate**: 92% (23/25 tests passed)
- **Critical failures**: 0 (down from 5)

## Root Causes Identified and Fixed

### 1. Test Validation Logic Mismatch
- **Issue**: Tests expected raw API responses but methods returned processed data
- **Fix**: Updated test validation to use `is_data_test=True` for processed data methods
- **Files**: `test_api_connection.py`

### 2. Data Fetcher Method Mismatch  
- **Issue**: Data fetcher called wrong method for base stats (processed vs raw response)
- **Fix**: Created `get_league_player_base_stats()` method for raw API responses
- **Files**: `src/nba_stats/api/nba_stats_client.py`, `src/nba_stats/api/data_fetcher.py`

### 3. Incorrect Metric Column Mappings
- **Issue**: FTr metric mapped to non-existent column `FTA_PG` in advanced stats
- **Fix**: Updated mapping to use `FTA` from base stats endpoint
- **Files**: `definitive_metric_mapping.py`

## Files Modified

- `api_forensics.ipynb`: Forensic analysis notebook with complete resolution
- `docs/api_quirks.md`: This documentation file
- `test_api_connection.py`: Fixed test validation logic
- `src/nba_stats/api/nba_stats_client.py`: Added `get_league_player_base_stats()` method
- `src/nba_stats/api/data_fetcher.py`: Updated to use correct base stats method
- `definitive_metric_mapping.py`: Fixed FTr metric column mapping
