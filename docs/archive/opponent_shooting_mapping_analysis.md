# PlayerSeasonOpponentShootingStats - API to Database Mapping Analysis

## Executive Summary

The NBA API endpoint `leaguedashplayershotlocations` with `MeasureType=Opponent` returns data in a **fundamentally different structure** than what the existing population script expects. This explains why the table remains empty despite the API returning data.

## Key Findings

### 1. API Response Structure (ACTUAL)
- **Endpoint**: `leaguedashplayershotlocations` with `MeasureType=Opponent`
- **Response Format**: Single `resultSets` object (not array)
- **Headers**: 2 header objects defining shot categories and column names
- **Data**: 33 columns per row (6 basic info + 27 shot data)
- **Shot Categories**: 9 distance ranges from "Less Than 5 ft." to "40+ ft."

### 2. Expected Structure (EXISTING SCRIPT)
- **Expected**: `resultSets` as array with `headers` and `rowSet` properties
- **Expected Headers**: Array of column names
- **Expected Data**: Direct mapping from headers to row values

### 3. Schema Mismatch Details

#### API Response Structure:
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

#### Expected Structure (by existing script):
```json
{
  "resultSets": {
    "headers": [{"columnNames": [...]}],
    "rowSet": [[player_data_array], ...]
  }
}
```

## Field Mapping

### Basic Information Fields
| API Column | Database Column | Notes |
|------------|-----------------|-------|
| `PLAYER_ID` | `player_id` | Direct mapping |
| `PLAYER_NAME` | `player_name_api` | Direct mapping |
| `TEAM_ID` | `team_id` | Direct mapping |
| `TEAM_ABBREVIATION` | `team_code_api` | Direct mapping |
| `AGE` | `age_api` | Direct mapping |
| `NICKNAME` | - | Not stored in database |

### Missing Fields (Not in API)
- `season` - Must be provided as parameter
- `games_played` - Must be fetched from `PlayerSeasonRawStats` table
- `avg_fg_attempted_against_per_game` - Must be calculated from shot data

### Shot Data Fields (9 distance ranges × 3 metrics each = 27 columns)

#### Distance Range Mapping:
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

#### Metric Pattern (repeats for each distance):
| API Pattern | Database Pattern |
|-------------|------------------|
| `OPP_FGM` | `opp_fgm_{suffix}` |
| `OPP_FGA` | `opp_fga_{suffix}` |
| `OPP_FG_PCT` | `opp_fg_pct_{suffix}` |

## Data Transformation Required

### 1. Header Processing
- Extract shot categories from `headers[0]['columnNames']`
- Extract column names from `headers[1]['columnNames']`
- Create mapping between distance ranges and database suffixes

### 2. Row Processing
- Map basic info fields (first 6 columns)
- Process shot data in groups of 3 (FGM, FGA, FG_PCT) for each distance
- Calculate `avg_fg_attempted_against_per_game` as sum of all FGA values divided by games_played

### 3. Data Validation
- Verify player exists in database
- Verify team abbreviation maps to valid team_id
- Fetch games_played from PlayerSeasonRawStats table

## Implementation Strategy

### New Script Requirements:
1. **Parse New API Structure**: Handle the dict-based resultSets format
2. **Dynamic Column Mapping**: Build column mapping based on shot categories
3. **Data Transformation**: Convert API data to database format
4. **Missing Data Handling**: Fetch games_played and calculate derived fields
5. **Error Handling**: Robust validation and error reporting

### Key Differences from Existing Script:
- Different API response parsing logic
- Dynamic column name generation based on shot categories
- Additional data fetching for games_played
- Calculation of avg_fg_attempted_against_per_game

## Conclusion

The existing script fails because it expects a different API response structure. The new endpoint returns data in a more complex format that requires significant parsing and transformation logic. A new script must be written to handle this structure properly.

## Next Steps

1. Create new `populate_opponent_shooting_stats_v2.py` script
2. Implement new API response parsing logic
3. Add dynamic column mapping based on shot categories
4. Integrate with existing database validation logic
5. Test with single player before full population
