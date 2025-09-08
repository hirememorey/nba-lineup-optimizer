# Data Pipeline Guide

This document explains how to populate the database with the necessary data for a new NBA season. The process involves running a series of scripts located in `src/nba_stats/scripts/`.

## Orchestration Scripts

The project includes two primary orchestration scripts, `run_phase_1.py` and `run_phase_2.py`, which are designed to run the individual data-gathering scripts in the correct order.

- **`run_phase_1.py`**: Focuses on populating foundational data like teams, players, and games.
- **`run_phase_2.py`**: Focuses on populating the detailed player statistics required for the archetype analysis.

**Recommendation**: For a new season, you should primarily use and modify these orchestration scripts rather than running each script manually.

## Key Data Population Scripts

The following are the most important individual scripts, organized by the phase in which they are typically run.

### Phase 1: Foundational Data

1.  **`populate_teams.py`**: Fetches and populates the `Teams` table with all NBA teams.
2.  **`populate_players.py`**: Populates the `Players` table with all players for the target season.
3.  **`populate_games.py`**: Fetches the schedule for the target season and populates the `Games` table.

### Phase 2: Detailed Player Statistics

This phase involves gathering the 48 detailed metrics required for the player archetype clustering. These scripts often fetch data from different endpoints of the NBA stats API.

- **`populate_player_season_stats.py`**: Gathers traditional per-game and advanced stats.
- **`populate_player_drive_stats.py`**: Gathers player statistics related to driving to the basket.
- **`populate_player_catch_shoot_stats.py`**: Gathers catch-and-shoot statistics.
- **`populate_player_pull_up_stats.py`**: Gathers pull-up shooting statistics.
- **`populate_player_shooting_stats.py`**: Gathers detailed shooting splits from various distances.
- **`populate_player_passing_stats.py`**: Gathers advanced passing data.
- **... and many others**: The `scripts` directory contains scripts for post-ups, rebounding, hustle stats, etc.

### Other Important Scripts

- **`populate_salaries.py`**: This script needs to be modified to load salary data into the newly structured `PlayerSalaries` table (see `database_setup.md`). It should parse the `data/player_salaries_YYYY-YY.csv` file.
- **`populate_player_skill.py`** (or a new script): This script will need to be created or modified to load the DARKO skill ratings from `data/darko_dpm_YYYY-YY.csv` into the new `PlayerSkills` table.
- **`populate_possessions.py`**: This script populates the granular, play-by-play `Possessions` table. This is the largest and most time-consuming data ingestion step.

## How to Add a New Season (e.g., 2024-25)

1.  **Set the Target Season**: The target season is typically controlled by a configuration file. Locate the main config (e.g., `src/nba_stats/config/settings.py` or `population_config.json`) and update the `SEASON` variable to "2024-25".
2.  **Run Phase 1**: Execute `python src/nba_stats/scripts/run_phase_1.py`.
3.  **Run Phase 2**: Execute `python src/nba_stats/scripts/run_phase_2.py`.
4.  **Populate Salaries and Skills**: Run your modified scripts to populate the `PlayerSalaries` and `PlayerSkills` tables for the new season.
5.  **Populate Possessions**: Run `python src/nba_stats/scripts/populate_possessions.py`. Be aware that this may take a significant amount of time to complete.

---

## Architectural Notes & Lessons Learned

A developer picking up this project should be aware of several key architectural decisions and challenges that were overcome during the data population phase. These insights are critical for understanding why the code is structured the way it is and for debugging future issues.

### 1. The "Sacred Schema" Principle

-   **Problem**: Initial attempts to run the data pipeline resulted in database errors because different scripts contained their own `CREATE TABLE` statements, which conflicted with the official, migrated schema. For example, `run_phase_1.py` attempted to create a `PlayerSkills` table with outdated column names.
-   **Principle**: A data pipeline's integrity relies on a single source of truth for its schema. Application-level code should **never** define or alter the schema on the fly.
-   **Solution**: The authoritative schema is now defined **exclusively** in `src/nba_stats/scripts/migrate_db.py`. All `CREATE TABLE` statements have been ruthlessly removed from other scripts (like `run_phase_1.py`). The established workflow is:
    1.  Run the migration script first to create a clean, correct schema.
    2.  Run the population scripts, which now *only* insert data into the pre-existing tables.

### 2. Resumption Over Perfection for Long-Running I/O

-   **Problem**: The `populate_possessions.py` script was originally designed as an "all-or-nothing" operation. It fetched data for all 1,230 games into memory and attempted to save them in a single batch. This was architecturally guaranteed to fail due to inevitable network timeouts, losing all progress on each failure.
-   **Principle**: Any long-running process involving network I/O is not just likely to fail—it is guaranteed to fail. A robust system is not one that never fails, but one that gracefully handles failure.
-   **Solution**: The script was refactored to be **resumable and idempotent**. The new logic is:
    1.  **Query First**: Before fetching any data, it queries the database to get a list of `game_id`s that have already been processed.
    2.  **Process Incrementally**: It then iterates through only the *missing* games.
    3.  **Save Atomically**: The data for each game is saved to the database immediately after it is processed, inside the main loop.
    This transformed the process from a high-stress gamble into a resilient, low-supervision task that can be stopped and started without losing progress.

### 3. Defensive Programming Against Unpredictable Data

-   **Problem**: After fixing the system-level issues, a series of data-level `ValueError` exceptions occurred (`too many values to unpack`, `not enough values to unpack`). This was caused by the unreliability of the `nba_api` for historical data. The initial API call to get starters returned an empty dataframe, and the subsequent logic to infer lineups from play-by-play data did not properly handle edge cases (e.g., games where fewer than 5 players were involved in the initial plays).
-   **Principle**: A system's true complexity is in its edge cases. A robust data pipeline must assume its inputs are "guilty until proven innocent" and defensively validate the *shape* of the data at every step.
-   **Solution**: The lineup inference logic in `populate_possessions.py` was hardened significantly.
    1.  The dependency on the failing `boxscoretraditionalv2` endpoint was removed entirely.
    2.  A new algorithm was implemented to find the *first five unique players* for each team from the chronological play-by-play data.
    3.  A strict validation check (`if len(home_players) != 5:`) was added. This enforces the contract that exactly five players must be found. If this contract is violated, the game is now safely logged and skipped, preventing the script from crashing and allowing the rest of the data to be processed.
