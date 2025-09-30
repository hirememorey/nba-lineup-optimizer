# Database Setup and Schema

The project relies on a central SQLite database to store all data, from raw player statistics to the final model outputs.

-   **Database File**: `src/nba_stats/db/nba_stats.db`

## Schema Overview

The database contains numerous tables designed to hold specific slices of NBA data. The most important tables for the core analysis are:

-   `Games`: Basic information for each game in a season.
-   `Players`: A list of all players with their unique NBA `player_id`.
-   `Teams`: A list of all teams with their unique NBA `team_id`.
-   `Possessions`: Granular, play-by-play data for each possession.
-   `PlayerSalaries`: Player salary information for a given season.
-   `PlayerSkills`: Player skill ratings (from DARKO) for a given season.
-   `PlayerSeasonRawStats`: A wide table containing the 48 core metrics used for archetype clustering.
-   A variety of other tables holding specific stats (`PlayerSeasonDriveStats`, `PlayerSeasonCatchAndShootStats`, etc.).

Foreign key constraints (`PRAGMA foreign_keys = ON`) are enforced on all database connections to ensure referential integrity.

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
