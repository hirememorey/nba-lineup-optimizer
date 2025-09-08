# Next Steps for 2024-25 Season Analysis

This document outlines the immediate, high-priority tasks required to prepare the project for the analysis of the 2024-25 NBA season.

**`[COMPLETED]`** ~~## Task 1: Database Migration (Critical Blocker)~~

- **Status**: ✅ Done.
- **Objective**: Alter the tables to include `player_id` and `season_id` columns to enable proper data storage and querying.
- **Implementation**: The `src/nba_stats/scripts/migrate_db.py` script now safely handles this, archiving old tables if they exist.

**`[COMPLETED]`** ~~## Task 2: Update Data Population Scripts~~

- **Status**: ✅ Done.
- **Objective**: Modify the population scripts to load the 2024-25 CSV data into the new table structures.
- **Implementation**:
    - `populate_salaries.py` now reads directly from `data/player_salaries_2024-25.csv`.
    - `populate_player_skill.py` now reads directly from `data/darko_dpm_2024-25.csv`.

---

### **`[CURRENT TASK]`** Task 3: Debug and Fix Possession Data Population

- **Status**: 🚧 **BLOCKED**
- **Objective**: Populate the `Possessions` table with granular, play-by-play data for the entire season by running `src/nba_stats/scripts/populate_possessions.py`.
- **The Blocker**: The script is currently failing. Initial debugging revealed that the structure of the data objects returned by the `nba_api` library has likely changed since the script was originally written. The script's assumptions about where to find data (e.g., a `.game_summary` attribute) are no longer valid, causing `AttributeError` exceptions.

#### **Recommended Next Action: API Health Check**

Before attempting further fixes, the immediate next step is to investigate and validate the current structure of the `nba_api` objects.

1.  **Isolate the Problem**: Create a temporary test script (e.g., `api_test.py`).
2.  **Instantiate Core Objects**: In the test script, import `playbyplayv2` and `boxscoretraditionalv2` and instantiate them with a single, hard-coded `game_id`.
3.  **Inspect Live Objects**: Use tools like `dir()` and `vars()` to thoroughly inspect the live `pbp` and `boxscore` objects. The goal is to answer:
    -   Where is the game summary data (home/away team IDs) located now?
    -   How are the actual DataFrames (box score, play-by-play events) meant to be accessed? Is it still `.get_data_frames()`?
4.  **Update the Script**: Once the correct data access patterns are discovered, refactor `populate_possessions.py` to match the *actual* current API contract.

---

### Task 4: Run Full Data Pipeline for 2024-25

- **Status**: ⏳ PENDING (Blocked by Task 3)
- **Objective**: Ensure all required data for the 2024-25 season is present in the database.
- **Instructions**: Once the possession script is fixed, the remaining steps in `docs/data_pipeline.md` can be completed.

### Task 5: Run the Analysis

- **Status**: ⏳ PENDING
- **Objective**: Generate the 2024-25 player archetypes, lineup superclusters, and Bayesian model results.
- **Instructions**: Follow the guide in `docs/running_the_analysis.md`.
