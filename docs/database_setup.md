# Database Setup and Schema

The project relies on a central SQLite database to store all data, from raw player statistics to the final model outputs.

- **Database File**: `src/nba_stats/db/nba_stats.db`

## Schema Overview

The database contains numerous tables designed to hold specific slices of NBA data. The most important tables for the core analysis are:

- `Games`: Basic information for each game in a season.
- `Players`: A list of all players with their unique NBA `player_id`.
- `Teams`: A list of all teams with their unique NBA `team_id`.
- `Possessions`: Granular, play-by-play data for each possession.
- `PlayerSalaries`: Player salary information for a given season.
- `PlayerSkills`: Player skill ratings (from DARKO) for a given season.
- `PlayerSeasonRawStats`: A wide table containing the 48 core metrics used for archetype clustering.
- A variety of other tables holding specific stats (`PlayerSeasonDriveStats`, `PlayerSeasonCatchAndShootStats`, etc.).

## Critical Schema Modifications Needed

**Warning:** Before proceeding with the 2024-25 season analysis, the database schema **must** be updated. The current structure of the `PlayerSalaries` and `PlayerSkills` tables is insufficient as it does not link the data to a specific season.

A database migration script should be run to perform the following changes:

### 1. `PlayerSalaries` Table

- **Current Structure**:
  ```
  (PlayerName TEXT, Salary INTEGER)
  ```
- **Problem**: Relies on `PlayerName` for joins, which is unreliable. Critically, it **lacks a `season_id`**, making it impossible to store or query historical salary data.
- **Required Structure**:
  ```sql
  CREATE TABLE PlayerSalaries (
      player_salary_id INTEGER PRIMARY KEY AUTOINCREMENT,
      player_id INTEGER NOT NULL,
      season_id TEXT NOT NULL, -- e.g., "2024-25"
      salary REAL,
      FOREIGN KEY (player_id) REFERENCES Players(player_id)
  );
  ```

### 2. `PlayerSkills` Table

- **Current Structure**: A similar structure that also lacks `player_id` and `season_id`.
- **Problem**: Same as `PlayerSalaries`. The skill ratings are not tied to a specific season, which is essential for the model.
- **Required Structure**:
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

These changes are the **highest priority prerequisite** for any further work on the project. The script `src/nba_stats/scripts/migrate_db.py` is the designated place to implement this schema migration.
