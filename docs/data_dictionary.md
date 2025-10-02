# Data Dictionary

**Date**: September 30, 2025  
**Status**: ✅ **CRITICAL REFERENCE DOCUMENT**

## Overview

This document provides the definitive reference for the NBA Lineup Optimizer project's data architecture. The project uses a **multi-database approach** with data distributed across three SQLite database files.

## Database Architecture

### Primary Database: `src/nba_stats/db/nba_stats.db`

This is the main database containing processed, analysis-ready data. It includes:

#### Core Metadata Tables
- **`Players`**: 5,025 players (includes historical data)
- **`Teams`**: 30 teams (current NBA teams)
- **`Games`**: 1,230 games (full 82-game regular season)

#### Advanced Statistics Tables
The 41+ metrics required for archetype analysis are distributed across specialized tables:

- **`PlayerSeasonDriveStats`**: Driving to the basket statistics
  - Key columns: `drives`, `drive_fgm`, `drive_fga`, `drive_fg_pct`, `drive_passes`, `drive_ast`
- **`PlayerSeasonPostUpStats`**: Post-up play statistics
  - Key columns: `possessions`, `frequency_pct`, `points_per_possession`, `fg_pct`
- **`PlayerSeasonCatchAndShootStats`**: Catch-and-shoot statistics
  - Key columns: `catch_shoot_fgm`, `catch_shoot_fga`, `catch_shoot_fg_pct`, `catch_shoot_3pm`
- **`PlayerSeasonPassingStats`**: Advanced passing statistics
  - Key columns: `passes_made`, `potential_assists`, `assist_to_pass_percentage`
- **`PlayerSeasonHustleStats`**: Hustle statistics
- **`PlayerSeasonReboundingStats`**: Rebounding statistics
- **`PlayerSeasonShootingRangeStats`**: Shooting by distance
- **`PlayerSeasonShootingZoneStats`**: Shooting by court zone
- **`PlayerSeasonTrackingTouchesStats`**: Touch statistics
- **`PlayerSeasonElbowTouchStats`**: Elbow touch statistics
- **`PlayerSeasonPaintTouchStats`**: Paint touch statistics
- **`PlayerSeasonOpponentShootingStats`**: Defensive shooting statistics

#### Analysis Tables
- **`PlayerSeasonRawStats`**: Traditional box score statistics (legacy table)
  - **⚠️ WARNING (Oct 2, 2025):** This table is currently being populated **incorrectly**. The pipeline is creating the rows for players but is silently failing to write any of the actual statistical columns (e.g., FGM, FGA, PTS). The table is semantically empty and unusable for analysis until this bug is fixed.
- **`PlayerSeasonAdvancedStats`**: Advanced metrics
  - **⚠️ WARNING (Oct 2, 2025):** This table is currently being populated **incorrectly**. Similar to the raw stats table, it contains player rows but is missing all advanced statistical columns.
- **`PlayerSalaries`**: Player salary information
- **`PlayerSkills`**: Player skill ratings (DARKO)
- **`Possessions`**: Play-by-play possession data
- **`Archetypes`**: Generated player archetypes
- **`ArchetypeLineups`**: Lineup archetype combinations
- **`LineupSuperclusters`**: Lineup supercluster classifications

#### Enhanced Data Tables (NEW)
- **`PlayerAnthroStats`**: Anthropometric data from NBA Draft Combine
  - Key columns: `player_id`, `wingspan_inches`, `height_wo_shoes_inches`, `height_w_shoes_inches`, `weight_pounds`, `standing_reach_inches`, `body_fat_pct`, `hand_length_inches`, `hand_width_inches`
  - **Sparsity**: Only available for draft combine attendees (45-83 players per season)
  - **Purpose**: Physical measurements for enhanced player analysis
- **`PlayerShotMetrics`**: Calculated shot distribution metrics
  - Key columns: `player_id`, `season`, `avgdist`, `zto3r`, `thto10r`, `tento16r`, `sixtto3ptr`, `total_shots`
  - **Metrics**: 5 derivable shot metrics from shot chart data
  - **Purpose**: Shot selection analysis for archetype classification

### Secondary Database: `nba_data.db`

Contains raw player tracking data from the NBA API:
- `player_tracking_catch_shoot`
- `player_tracking_driving`
- `player_tracking_elbow_touch`
- `player_tracking_paint_touch`
- `player_tracking_passing`
- `player_tracking_post_touch`
- `player_tracking_pull_up_shot`
- `player_tracking_speeddistance`

### Tertiary Database: `nba_lineup_data.db`

Contains lineup-specific data:
- `Games`, `Teams`, `Players` (duplicate metadata)
- `LineupSeasonStats`
- `PlayerSeasonAdvancedStats`
- `PlayerSeasonDriveStats`
- `PlayerSeasonHustleStats`
- `PlayerSeasonRawStats`

## Critical Data Quality Issues

### ⚠️ Schema Drift Warning

The `schema.sql` file in the project root is **dangerously outdated** and does not reflect the actual database structure. Do not rely on it for development.

### ⚠️ Critical Data Persistence Bug

As of October 2, 2025, a comprehensive sanity check has revealed that the `PlayerSeasonRawStats` and `PlayerSeasonAdvancedStats` tables are not being populated correctly. The data pipeline is failing to write the actual statistical columns to these tables, rendering them unusable. This bug must be fixed before any analysis can proceed. See `CURRENT_STATUS.md` for more details.

### ⚠️ Missing 2024-25 Season Data

As of September 30, 2025, the advanced statistics tables appear to be empty for the 2024-25 season. This indicates that the data pipeline has not been successfully run for this season.

## Data Pipeline Status

### Required Next Steps

1. **Run the Master Data Pipeline**:
   ```bash
   python master_data_pipeline.py --season 2024-25
   ```

2. **Verify Data Population**:
   ```bash
   python data_verification_tool.py
   ```

3. **Handle Missing Data** (if needed):
   ```bash
   python data_imputation_tool.py --strategy auto
   ```

## Data Access Patterns

### Querying Advanced Metrics

To access the 41+ metrics required for archetype analysis, you must query multiple specialized tables:

```sql
-- Example: Get drive statistics for a player
SELECT player_id, drives, drive_fgm, drive_fga, drive_fg_pct
FROM PlayerSeasonDriveStats 
WHERE season = '2024-25' AND player_id = ?;

-- Example: Get post-up statistics for a player
SELECT player_id, possessions, frequency_pct, points_per_possession
FROM PlayerSeasonPostUpStats 
WHERE season = '2024-25' AND player_id = ?;
```

### Data Completeness Check

Before running the analysis, verify data completeness:

```sql
-- Check for NULL values in key metrics
SELECT 
    'drives' as metric,
    100.0 * SUM(CASE WHEN drives IS NULL THEN 1 ELSE 0 END) / COUNT(*) as null_percentage
FROM PlayerSeasonDriveStats 
WHERE season = '2024-25'
UNION ALL
SELECT 
    'post_up_possessions' as metric,
    100.0 * SUM(CASE WHEN possessions IS NULL THEN 1 ELSE 0 END) / COUNT(*) as null_percentage
FROM PlayerSeasonPostUpStats 
WHERE season = '2024-25';
```

## Migration Notes

This multi-database architecture was developed to handle the complexity of NBA data sources and the need for specialized processing of different metric types. The architecture allows for:

1. **Separation of Concerns**: Raw API data is stored separately from processed analysis data
2. **Performance Optimization**: Specialized tables can be indexed for specific query patterns
3. **Data Integrity**: Foreign key constraints ensure referential integrity across the system

## Troubleshooting

### Common Issues

1. **Empty Advanced Stats Tables**: Run the master data pipeline for the target season
2. **Schema Mismatches**: Always check actual table schemas using `sqlite3 database.db ".schema TableName"`
3. **Missing Season Data**: Verify the season parameter in data population scripts

### Verification Commands

```bash
# Check table structure
sqlite3 src/nba_stats/db/nba_stats.db ".schema TableName"

# Check row counts
sqlite3 src/nba_stats/db/nba_stats.db "SELECT COUNT(*) FROM TableName WHERE season = '2024-25';"

# Check for NULL values
sqlite3 src/nba_stats/db/nba_stats.db "SELECT COUNT(*) FROM TableName WHERE column_name IS NULL;"
```
