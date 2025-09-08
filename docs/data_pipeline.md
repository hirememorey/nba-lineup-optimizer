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
