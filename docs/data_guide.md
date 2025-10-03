# A Developer's Guide to the Data Pipeline

This document provides a comprehensive guide to the project's data architecture, pipeline, and analysis workflow.

## Data Architecture

The project uses a **multi-database approach** with data distributed across three SQLite database files to separate raw data from processed, analysis-ready data. The definitive schema for all tables can be found in `docs/data_dictionary.md`.

*   **Primary Database (`src/nba_stats/db/nba_stats.db`)**: The main database containing processed, analysis-ready data.
*   **Secondary Database (`nba_data.db`)**: Contains raw player tracking data from the NBA API.
*   **Tertiary Database (`nba_lineup_data.db`)**: Contains lineup-specific data.

**CRITICAL NOTE**: The `schema.sql` file in the project root is dangerously outdated. **Do not trust it.** The single source of truth for the database schema is in the database migration scripts and can be inspected directly with `sqlite3`.

## Current Data Status (October 3, 2025)

**✅ FULLY OPERATIONAL**: All critical data gaps have been resolved. The database now contains comprehensive coverage of the 48 canonical metrics required for archetype analysis. A critical drive statistics API usage bug has been fixed, and a comprehensive three-layer verification system is now in place.

### Data Coverage Summary:
- **PlayerArchetypeFeatures**: 273 players with complete feature set and proper variance
- **Drive Statistics**: 579 players (100% coverage with 129 unique drive values)
- **Post-up Play**: 569 players (100% coverage)
- **Pull-up Shooting**: 569 players (100% coverage)
- **Paint Touches**: 569 players (100% coverage)
- **Front Court Touches**: 569 players (100% coverage)
- **Elbow Touches**: 569 players (100% coverage)
- **Passing Stats**: 569 players (100% coverage)
- **Opponent Shooting Stats**: 569 players (100% coverage for 2024-25 season)
- **Possessions**: 574,357 total possessions
- **Player Salaries**: 916 players
- **Player Skills**: 1,026 players

### Recent Critical Fixes Applied (October 3, 2025):
1. **Drive Stats API Usage Bug**: ✅ **RESOLVED** - Fixed critical bug where individual player API calls were returning identical data for all players. Now properly calls league-wide endpoint and processes each player individually (1 unique value → 129 unique values)
2. **Drive Stats Percentage Columns**: ✅ **RESOLVED** - Fixed 100% NULL values in `drive_pass_pct` and other percentage columns by implementing proper calculation logic in `fix_drive_stats_percentages.py`
3. **Shot Metrics Table References**: ✅ **RESOLVED** - Fixed incorrect table joins in feature generation script. Updated `generate_archetype_features.py` to use `PlayerShotMetrics` table instead of attempting to aggregate from `PlayerShotChart`
4. **Comprehensive Data Verification Pipeline**: ✅ **IMPLEMENTED** - Created `verify_database_sanity.py` with three-layer verification system to catch data quality issues before they propagate through the analysis pipeline
5. **Feature Generation**: ✅ **UPDATED** - Regenerated `PlayerArchetypeFeatures` table with corrected data sources and calculations

### Previous Major Fixes:
- **PlayerSeasonOpponentShootingStats**: ✅ **RESOLVED** - Fixed API response structure mismatch. The NBA API endpoint returns `resultSets` as a dict instead of a list, which was causing validation failures. Created new script `populate_opponent_shooting_stats_v2.py` and updated API client method to handle this special case. Now contains 569 records for 2024-25 season.

## Data Verification Workflow

**CRITICAL**: Before proceeding with any analysis, always run the comprehensive database verification:

```bash
# Run comprehensive database sanity verification
python verify_database_sanity.py
```

This script performs a three-layer verification:
- **Layer 1**: Structural & Volume Verification (table counts, NULL checks)
- **Layer 1.5**: Source Table Spot-Checks (prevents silent upstream failures)
- **Layer 2**: Data Range & Distribution Validation (statistical checks)
- **Layer 3**: Cross-Table Consistency Check (data integrity)

**Expected Output**: `🎉 ALL CRITICAL VERIFICATIONS PASSED`

If verification fails, do not proceed with analysis. The script will identify specific issues that must be resolved first.

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
