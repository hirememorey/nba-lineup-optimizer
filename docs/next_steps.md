# Next Steps for 2024-25 Season Analysis

This document outlines the immediate, high-priority tasks required to prepare the project for the analysis of the 2024-25 NBA season.

## Task 1: Database Migration (Critical Blocker)

The single most important and urgent task is to fix the database schema for the `PlayerSalaries` and `PlayerSkills` tables.

- **Objective**: Alter the tables to include `player_id` and `season_id` columns to enable proper data storage and querying.
- **Details**: Specific instructions and the required schema are detailed in the `docs/database_setup.md` file.
- **Implementation**: This logic should be implemented within the existing `src/nba_stats/scripts/migrate_db.py` script. The script should be idempotent, meaning it can be run multiple times without causing errors (e.g., it should check if the columns already exist before trying to add them).

## Task 2: Update Data Population Scripts

Once the database migration is complete, the scripts for populating salaries and skills must be updated.

### `populate_salaries.py`
- **Objective**: Modify this script to parse the `data/player_salaries_2024-25.csv` file and load its contents into the newly structured `PlayerSalaries` table.
- **Key Changes**:
    - The script must map `PlayerName` to a `player_id`. A lookup from the `Players` table will be necessary.
    - It must insert the correct `season_id` ('2024-25') for every record.

### `populate_player_skill.py` (New or Modified Script)
- **Objective**: Create a new script (or modify the existing placeholder) to load the DARKO skill ratings.
- **Source File**: `data/darko_dpm_2024-25.csv`
- **Key Changes**:
    - The script must parse the CSV.
    - It needs to map player names to `player_id`.
    - It must load the `Offensive DARKO` and `Defensive DARKO` ratings into the `offensive_skill_rating` and `defensive_skill_rating` columns, respectively.
    - It must insert the `season_id` ('2024-25') for all records.

## Task 3: Run Full Data Pipeline for 2024-25

After the database and scripts are updated, the full data pipeline must be run to populate the database for the new season.

- **Objective**: Ensure all required data for the 2024-25 season is present in the database.
- **Instructions**: Follow the step-by-step guide in `docs/data_pipeline.md`.

## Task 4: Run the Analysis

With the data in place, the final step is to run the complete analysis pipeline.

- **Objective**: Generate the 2024-25 player archetypes, lineup superclusters, and Bayesian model results.
- **Instructions**: Follow the guide in `docs/running_the_analysis.md`.

These tasks, once completed, will fully prepare the project for generating player acquisition insights for the upcoming season.
