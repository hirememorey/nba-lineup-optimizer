# PlayerSeasonOpponentShootingStats Implementation

## Overview

This document describes the implementation of the `PlayerSeasonOpponentShootingStats` table population, which was previously failing due to an API response structure mismatch.

## Problem Description

The NBA API endpoint `leaguedashplayershotlocations` with `MeasureType=Opponent` returns data in a fundamentally different structure than other NBA Stats API endpoints:

- **Expected Structure**: `resultSets` as an array of objects
- **Actual Structure**: `resultSets` as a single dict object
- **Impact**: The existing validation logic rejected all responses, resulting in 0 records

## Solution Architecture

### 1. API Client Modification

**File**: `src/nba_stats/api/nba_stats_client.py`

Modified the `get_player_opponent_shooting_stats()` method to:
- Bypass the standard `resultSets` validation that expects an array
- Implement custom validation for the dict-based structure
- Maintain proper error handling and caching

### 2. New Population Script

**File**: `src/nba_stats/scripts/populate_opponent_shooting_stats_v2.py`

Created a new script that:
- Handles the correct API response structure
- Maps 9 distance ranges from API to database fields
- Calculates `avg_fg_attempted_against_per_game` correctly
- Integrates with existing database validation logic

### 3. Data Structure Mapping

#### API Response Structure
```json
{
  "resultSets": {
    "name": "ShotLocations",
    "headers": [
      {
        "name": "SHOT_CATEGORY",
        "columnNames": ["Less Than 5 ft.", "5-9 ft.", ..., "40+ ft."]
      },
      {
        "name": "columns",
        "columnNames": ["PLAYER_ID", "PLAYER_NAME", ..., "OPP_FG_PCT"]
      }
    ],
    "rowSet": [[player_data_array], ...]
  }
}
```

#### Distance Range Mapping
| API Distance | Database Suffix |
|--------------|-----------------|
| "Less Than 5 ft." | `lt_5ft` |
| "5-9 ft." | `5_9ft` |
| "10-14 ft." | `10_14ft` |
| "15-19 ft." | `15_19ft` |
| "20-24 ft." | `20_24ft` |
| "25-29 ft." | `25_29ft` |
| "30-34 ft." | `30_34ft` |
| "35-39 ft." | `35_39ft` |
| "40+ ft." | `40_plus_ft` |

#### Data Processing
- **Basic Info**: First 6 columns (PLAYER_ID, PLAYER_NAME, TEAM_ID, TEAM_ABBREVIATION, AGE, NICKNAME)
- **Shot Data**: Groups of 3 columns per distance (FGM, FGA, FG_PCT)
- **Total FGA Calculation**: Sum of all FGA values across all distances
- **Average Calculation**: Total FGA divided by games_played

## Usage

### Running the Script
```bash
# Run for 2024-25 season
python -m src.nba_stats.scripts.populate_opponent_shooting_stats_v2 --season 2024-25

# Run for different season
python -m src.nba_stats.scripts.populate_opponent_shooting_stats_v2 --season 2023-24
```

### Integration with Master Pipeline

The script integrates with the existing master pipeline by:
- Using the same database connection utilities
- Following the same error handling patterns
- Maintaining compatibility with existing validation logic

## Data Quality Validation

### Current Status (2024-25 Season)
- **Total Records**: 569
- **Unique Players**: 569
- **Unique Teams**: 30 (all NBA teams)
- **Data Quality**: No NULL values in key fields
- **Coverage**: 100% for all active players

### Data Ranges
- **FGM**: 0.0 to 16.3 (opponent field goals made)
- **FGA**: 0.0 to 24.0 (opponent field goal attempts)
- **FG_PCT**: 0.0 to 1.0 (opponent field goal percentage)

## Technical Notes

### Key Implementation Details
1. **Column Mapping**: Dynamic mapping based on shot categories returned by API
2. **Data Transformation**: Handles the complex column structure with repeated names
3. **Error Handling**: Robust validation and error reporting
4. **Caching**: Integrates with existing API client caching system

### Dependencies
- `sqlite3` for database operations
- `common_utils` for database connection and logging
- `nba_stats_client` for API communication
- Existing database schema and validation logic

## Future Considerations

### Potential Improvements
1. **Batch Processing**: Could be optimized for larger datasets
2. **Error Recovery**: Could add more sophisticated retry logic
3. **Data Validation**: Could add more comprehensive data quality checks

### Maintenance
- Monitor API response structure changes
- Update distance mapping if NBA changes shot categories
- Verify data quality after each population run

## Related Files

- `src/nba_stats/scripts/populate_opponent_shooting_stats_v2.py` - Main implementation
- `src/nba_stats/api/nba_stats_client.py` - Modified API client method
- `docs/data_dictionary.md` - Database schema documentation
- `opponent_shooting_mapping_analysis.md` - Detailed technical analysis
