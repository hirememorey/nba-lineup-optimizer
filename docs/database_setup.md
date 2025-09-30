# Database Setup and Schema

**⚠️ IMPORTANT**: This document has been updated to reflect the actual database architecture discovered during the September 30, 2025 sanity check.

## Multi-Database Architecture

The project uses a **multi-database approach** with data distributed across three SQLite database files:

### Primary Database: `src/nba_stats/db/nba_stats.db`
This is the main database containing processed, analysis-ready data.

### Secondary Database: `nba_data.db`
Contains raw player tracking data from the NBA API.

### Tertiary Database: `nba_lineup_data.db`
Contains lineup-specific data and some duplicate metadata.

## Schema Overview

The primary database contains numerous specialized tables designed to hold specific slices of NBA data. The most important tables for the core analysis are:

-   `Games`: Basic information for each game in a season (1,230 games for full season).
-   `Players`: A list of all players with their unique NBA `player_id` (5,025 players including historical data).
-   `Teams`: A list of all teams with their unique NBA `team_id` (30 current NBA teams).
-   `Possessions`: Granular, play-by-play data for each possession.
-   `PlayerSalaries`: Player salary information for a given season.
-   `PlayerSkills`: Player skill ratings (from DARKO) for a given season.

### Advanced Statistics Tables

The 41+ metrics required for archetype analysis are distributed across specialized tables:

-   `PlayerSeasonDriveStats`: Driving to the basket statistics
-   `PlayerSeasonPostUpStats`: Post-up play statistics  
-   `PlayerSeasonCatchAndShootStats`: Catch-and-shoot statistics
-   `PlayerSeasonPassingStats`: Advanced passing statistics
-   `PlayerSeasonHustleStats`: Hustle statistics
-   `PlayerSeasonReboundingStats`: Rebounding statistics
-   `PlayerSeasonShootingRangeStats`: Shooting by distance
-   `PlayerSeasonShootingZoneStats`: Shooting by court zone
-   `PlayerSeasonTrackingTouchesStats`: Touch statistics
-   `PlayerSeasonElbowTouchStats`: Elbow touch statistics
-   `PlayerSeasonPaintTouchStats`: Paint touch statistics
-   `PlayerSeasonOpponentShootingStats`: Defensive shooting statistics

### Legacy Table

-   `PlayerSeasonRawStats`: Traditional box score statistics (legacy table - does not contain the 48 core metrics as previously documented).

Foreign key constraints (`PRAGMA foreign_keys = ON`) are enforced on all database connections to ensure referential integrity.

## ⚠️ Critical Schema Warning

The `schema.sql` file in the project root is **dangerously outdated** and does not reflect the actual database structure. Always verify table schemas using:

```bash
sqlite3 src/nba_stats/db/nba_stats.db ".schema TableName"
```

For the complete data dictionary, see `docs/data_dictionary.md`.

## Key Table Structures

Below are the schemas for the critical tables that were updated to support multi-season data and reliable joins.

### `PlayerSalaries` Table

This table links players to their salary for a specific season.

```sql
CREATE TABLE PlayerSalaries (
    player_salary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    season_id TEXT NOT NULL, -- e.g., "2024-25"
    salary REAL,
    FOREIGN KEY (player_id) REFERENCES Players(player_id)
);
```

### `PlayerSkills` Table

This table stores player skill ratings (e.g., from DARKO) for a specific season.

```sql
CREATE TABLE PlayerSkills (
    player_skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    season_id TEXT NOT NULL,
    offensive_skill_rating REAL,
    defensive_skill_rating REAL,
    skill_metric_source TEXT NOT NULL, -- e.g., 'DARKO'
    FOREIGN KEY (player_id) REFERENCES Players(player_id)
);
```
