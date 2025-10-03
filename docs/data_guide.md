# A Developer's Guide to the Data Pipeline

This document provides a comprehensive guide to the project's data architecture, pipeline, and analysis workflow.

## Data Architecture

The project uses a **multi-database approach** with data distributed across three SQLite database files to separate raw data from processed, analysis-ready data. The definitive schema for all tables can be found in `docs/data_dictionary.md`.

*   **Primary Database (`src/nba_stats/db/nba_stats.db`)**: The main database containing processed, analysis-ready data.
*   **Secondary Database (`nba_data.db`)**: Contains raw player tracking data from the NBA API.
*   **Tertiary Database (`nba_lineup_data.db`)**: Contains lineup-specific data.

**CRITICAL NOTE**: The `schema.sql` file in the project root is dangerously outdated. **Do not trust it.** The single source of truth for the database schema is in the database migration scripts and can be inspected directly with `sqlite3`.

## Current Data Status (October 3, 2025)

**✅ FULLY OPERATIONAL**: All critical data gaps have been resolved. The database now contains comprehensive coverage of the 48 canonical metrics required for archetype analysis.

### Data Coverage Summary:
- **PlayerArchetypeFeatures**: 270 players with complete feature set
- **Drive Statistics**: 269 players (99.6% coverage)
- **Post-up Play**: 137 players (50.7% coverage)  
- **Pull-up Shooting**: 263 players (97.4% coverage)
- **Paint Touches**: 270 players (100% coverage)
- **Front Court Touches**: 270 players (100% coverage)
- **Elbow Touches**: 270 players (100% coverage)
- **Passing Stats**: 270 players (100% coverage)
- **Possessions**: 574,357 total possessions
- **Player Salaries**: 916 players
- **Player Skills**: 1,026 players

### Recent Fixes Applied:
1. **Import Issues**: Fixed missing `import logging` statements in multiple population scripts
2. **Settings Import**: Uncommented settings import in `common_utils.py`
3. **Schema Mismatches**: Fixed column mapping issues in elbow touch stats
4. **Data Integration**: Regenerated `PlayerArchetypeFeatures` table with all newly populated data

### Known Issues:
- **PlayerSeasonOpponentShootingStats**: 0 records (NBA API endpoint returning empty responses - API-side issue, not code problem)

## Data and Analysis Pipeline Workflow

The process of populating the database and running the analysis should be performed in the following order.

### Step 1: Data Population

The project uses a unified `master_data_pipeline.py` script to orchestrate the entire data collection process. It is strongly recommended to use this script rather than the individual population scripts.

**1. Verify API Connectivity & Data Quality:**
Before running the full pipeline, always run the pre-flight checks. These tools were developed to prevent critical failures where data appears structurally valid but is semantically incorrect.

```bash
# First, ensure the API is working correctly
python test_api_connection.py --season 2024-25

# Second, validate that the API is returning semantically correct data
python verify_semantic_data.py --season 2024-25
```

**2. Execute the Master Pipeline:**
This single command handles all data collection for the 48 canonical metrics, including robust error handling, retries, and validation.

```bash
python master_data_pipeline.py --season 2024-25
```

### Step 2: Data Reconciliation

After the main pipeline has run, you will likely have ~70% coverage for player salary and skill data. To achieve 100% coverage, you must run the interactive reconciliation tool. This tool handles name discrepancies and allows you to create missing players.

```bash
# Install required package
pip install rapidfuzz

# Run the interactive reconciliation tool
python src/nba_stats/scripts/fix_player_names.py
```

Follow the on-screen prompts to match names from the CSV files to players in the database. Once complete, re-run the `populate_salaries.py` and `populate_player_skill.py` scripts to finalize the data ingestion.

### Step 3: Core Analysis

Once the database is fully populated, you can proceed with the core analysis.

**1. Generate Archetype Features:**
This script consolidates the 48 required metrics into a single feature set for each player.

```bash
python src/nba_stats/scripts/generate_archetype_features.py
```

**2. Generate Lineup Superclusters:**
This step performs K-means clustering on lineups to create the six lineup superclusters.

```bash
python src/nba_stats/scripts/generate_lineup_superclusters.py
```

**3. Run the Bayesian Model:**
This is the final, computationally intensive step that fits the Bayesian regression model.

```bash
python src/nba_stats/scripts/run_bayesian_model.py
```
**Note**: This can take a very long time to run (the paper mentions 18 hours).

After the model has finished, the posterior samples of its parameters will be saved and can be used by the analysis tools.
