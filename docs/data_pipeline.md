# Data Pipeline Guide

**Status**: ✅ **OPERATIONAL - 2024-25 SEASON READY**

This document explains how to populate the database with the necessary data for a new NBA season. The project now uses a unified `master_data_pipeline.py` script that orchestrates the entire data collection process with built-in validation and error handling.

**Recent Update**: The API issues have been resolved and the pipeline is now fully operational for the 2024-25 season.

**Latest Enhancement**: Added robust wingspan data integration and shot metrics calculation with silent failure detection and dependency management.

## Primary Pipeline Script

**✅ NEW**: The project now uses a single, comprehensive pipeline script:

- **`master_data_pipeline.py`**: The main orchestration script that handles the complete data collection process with:
  - Semantic data verification before pipeline execution
  - Progress bars and real-time logging
  - Automatic retry logic for failed requests
  - Data quality validation
  - Comprehensive reporting

**Recommendation**: Always use `master_data_pipeline.py` for new seasons. The individual scripts in `src/nba_stats/scripts/` are still available for debugging or custom workflows.

## Pre-Pipeline Validation

**✅ CRITICAL**: Before running the full pipeline, always run semantic data verification:

```bash
python verify_semantic_data.py --season 2024-25
```

This tool validates that the NBA API is returning semantically correct data and prevents the critical failure mode where "data looks valid but is semantically wrong, leading to garbage analysis results."

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
- **`populate_player_anthro.py`**: **NEW** - Fetches anthropometric data (wingspan, height, weight) from NBA Draft Combine.
- **`populate_player_shot_metrics.py`**: **NEW** - Calculates 5 derivable shot metrics from shot chart data.
- **... and many others**: The `scripts` directory contains scripts for post-ups, rebounding, hustle stats, etc.

### Other Important Scripts

- **`populate_salaries.py`**: This script needs to be modified to load salary data into the newly structured `PlayerSalaries` table (see `database_setup.md`). It should parse the `data/player_salaries_YYYY-YY.csv` file.
- **`populate_player_skill.py`** (or a new script): This script will need to be created or modified to load the DARKO skill ratings from `data/darko_dpm_YYYY-YY.csv` into the new `PlayerSkills` table.
- **`populate_possessions.py`**: This script populates the granular, play-by-play `Possessions` table. This is the largest and most time-consuming data ingestion step.

## How to Add a New Season (e.g., 2024-25)

**✅ UPDATED PROCESS**: The new pipeline process is much simpler and more reliable:

1.  **Verify API Connectivity**: First, ensure the API is working correctly:
    ```bash
    python test_api_connection.py --season 2024-25
    ```

2.  **Run Semantic Data Verification**: Validate that the API is returning semantically correct data:
    ```bash
    python verify_semantic_data.py --season 2024-25
    ```
    **Critical**: This step prevents the failure mode where data looks valid but produces garbage analysis results.

3.  **Execute Master Pipeline**: Run the complete data pipeline:
    ```bash
    python master_data_pipeline.py --season 2024-25
    ```
    This single command handles all data collection, validation, and reporting.

4.  **Verify Data Quality**: Check the generated reports:
    - `master_pipeline_report.md`: Pipeline execution summary
    - `semantic_data_verification_report.md`: Data quality validation
    - `pipeline_results.json`: Detailed results and metrics

5.  **Handle Missing Data (If Needed)**: If any metrics are missing, use the imputation tool:
    ```bash
    python data_imputation_tool.py --strategy auto
    ```

6.  **Populate Additional Data (Optional)**: For complete analysis, you may also need:
    - **Salaries**: Run `python populate_salaries.py` to load salary data
    - **Skills**: Run scripts to load DARKO skill ratings
    - **Possessions**: Run `python src/nba_stats/scripts/populate_possessions.py` for play-by-play data

## Legacy Process (For Reference)

The old two-phase process is still available but not recommended:
- **Phase 1**: `python src/nba_stats/scripts/run_phase_1.py`
- **Phase 2**: `python src/nba_stats/scripts/run_phase_2.py`

Use the new `master_data_pipeline.py` process instead for better reliability and validation.

## New Features: Wingspan Data & Shot Metrics

### Wingspan Data Integration

**Problem Solved**: The original pipeline was missing wingspan data, which is crucial for player archetype analysis.

**Solution**: 
- **`populate_player_anthro.py`**: Fetches anthropometric data from NBA Draft Combine API
- **Sparsity-Aware Design**: Data is highly sparse (only available for draft combine attendees)
- **Separate Table**: `PlayerAnthroStats` table with nullable fields for optional enhancement data
- **Silent Failure Detection**: Post-fetch assertion layer prevents data corruption from API failures

**Data Coverage**: 
- 45-83 players per season (draft combine attendees only)
- 100% coverage when data exists
- Includes wingspan, height, weight, standing reach, hand measurements

### Shot Metrics Calculation

**Problem Solved**: Need to calculate 5 derivable shot metrics from existing shot chart data.

**Solution**:
- **`populate_player_shot_metrics.py`**: Calculates metrics from `PlayerShotChart` table
- **5 Key Metrics**: AVGDIST, Zto3r, THto10r, TENto16r, SIXTto3PTr
- **Dependency Management**: Requires shot chart data to be populated first
- **Performance Optimized**: Uses efficient SQL queries for batch processing

**Validation Process**:
- **`validate_shot_metric_logic.ipynb`**: Notebook for perfecting calculation logic
- **`wingspan_recon.ipynb`**: Notebook for data sparsity analysis
- **Isolation Testing**: Logic validated on diverse player sample before production

### Enhanced Error Handling

**Silent Failure Detection**: The NBA Stats API often returns `200 OK` with empty data. Our Post-Fetch Assertion Layer detects this and converts silent failures into retryable errors.

**Dependency Management**: All scripts include pre-run checks to ensure upstream data exists before processing.

**Idempotent Operations**: All scripts can be run multiple times safely without data corruption.
