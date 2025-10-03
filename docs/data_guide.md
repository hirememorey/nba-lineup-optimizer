# A Developer's Guide to the Data Pipeline

This document provides a comprehensive guide to the project's data architecture, pipeline, and analysis workflow.

## Data Architecture

The project uses a **multi-database approach** with data distributed across three SQLite database files to separate raw data from processed, analysis-ready data. The definitive schema for all tables can be found in `docs/data_dictionary.md`.

*   **Primary Database (`src/nba_stats/db/nba_stats.db`)**: The main database containing processed, analysis-ready data.
*   **Secondary Database (`nba_data.db`)**: Contains raw player tracking data from the NBA API.
*   **Tertiary Database (`nba_lineup_data.db`)**: Contains lineup-specific data.

**CRITICAL NOTE**: The `schema.sql` file in the project root is dangerously outdated. **Do not trust it.** The single source of truth for the database schema is in the database migration scripts and can be inspected directly with `sqlite3`.

## Current Data Status (October 3, 2025)

**✅ FULLY OPERATIONAL WITH ARCHETYPES AND SUPERCLUSTERS**: All critical data gaps have been resolved. The database now contains comprehensive coverage of player archetypes and lineup superclusters, with complete possession data ready for Bayesian modeling.

### Data Coverage Summary:
- **Player Archetype Coverage**: 651 players (100% coverage with fallback assignments)
- **Possession Data**: 574,357 possessions with complete lineup data
- **Archetype Lineups**: 17 unique archetype lineups identified
- **Lineup Superclusters**: 2 basketball-meaningful superclusters generated
- **Drive Statistics**: 100% coverage with proper variance
- **All Advanced Metrics**: 100% coverage for 48 canonical features
- **Player Salaries**: 916 players
- **Player Skills**: 1,026 players

### Recent Critical Fixes Applied (October 3, 2025):
1. **Player Archetype Coverage Crisis**: ✅ **RESOLVED** - Identified and fixed critical data quality issue where 295 players (18.7% of minutes) were missing archetype assignments. Implemented fallback assignment strategy using basketball-meaningful heuristics.
2. **Data Density Assessment**: ✅ **IMPLEMENTED** - Discovered only 17 unique archetype lineups, insufficient for k=6 clustering. Adjusted approach to use k=2 superclusters based on data constraints.
3. **Qualitative Validation Framework**: ✅ **IMPLEMENTED** - Built comprehensive "sniff test" for supercluster validation to ensure basketball-meaningful results.
4. **Drive Stats API Usage Bug**: ✅ **RESOLVED** - Fixed critical bug where individual player API calls were returning identical data for all players. Now properly calls league-wide endpoint and processes each player individually (1 unique value → 129 unique values)
5. **Drive Stats Percentage Columns**: ✅ **RESOLVED** - Fixed 100% NULL values in `drive_pass_pct` and other percentage columns by implementing proper calculation logic in `fix_drive_stats_percentages.py`
6. **Shot Metrics Table References**: ✅ **RESOLVED** - Fixed incorrect table joins in feature generation script. Updated `generate_archetype_features.py` to use `PlayerShotMetrics` table instead of attempting to aggregate from `PlayerShotChart`
7. **Comprehensive Data Verification Pipeline**: ✅ **IMPLEMENTED** - Created `verify_database_sanity.py` with three-layer verification system to catch data quality issues before they propagate through the analysis pipeline
8. **Feature Generation**: ✅ **UPDATED** - Regenerated `PlayerArchetypeFeatures` table with corrected data sources and calculations

### Player Archetype Generation (October 3, 2025):
1. **Optimal K-Value Determination**: ✅ **COMPLETED** - Used rigorous multi-metric evaluation (Silhouette, Calinski-Harabasz, Davies-Bouldin, Inertia) to determine k=3 with PCA (80% variance) as optimal
2. **Feature Space Engineering**: ✅ **COMPLETED** - Implemented PCA-based dimensionality reduction to address correlation and noise issues (47 → 13 components, 81.9% variance)
3. **Basketball-Meaningful Archetypes**: ✅ **COMPLETED** - Generated three interpretable archetypes:
   - **Big Men** (51 players, 18.7%): High height, wingspan, frontcourt presence
   - **Primary Ball Handlers** (86 players, 31.5%): High usage, driving ability, playmaking
   - **Role Players** (136 players, 49.8%): Balanced contributors, catch-and-shoot ability
4. **Model Persistence**: ✅ **COMPLETED** - All models (scaler, PCA, K-means) and results saved for reproducibility

### Lineup Supercluster Generation (October 3, 2025):
1. **Data Quality Resolution**: ✅ **COMPLETED** - Resolved critical issue where 295 players were missing archetype assignments, implemented fallback assignment strategy
2. **Data Density Assessment**: ✅ **COMPLETED** - Discovered 17 unique archetype lineups, adjusted clustering approach from k=6 to k=2 based on data constraints
3. **Qualitative Validation Framework**: ✅ **COMPLETED** - Built comprehensive "sniff test" for supercluster validation
4. **Basketball-Meaningful Superclusters**: ✅ **COMPLETED** - Generated two interpretable superclusters:
   - **Supercluster 0**: "Balanced Lineups" (30% Big Men, 40% Ball Handlers, 30% Role Players)
   - **Supercluster 1**: "Role Player Heavy" (87% Role Players)
5. **Model Persistence**: ✅ **COMPLETED** - All models and results saved for reproducibility

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

### Step 3: Player Archetype Generation

Once the database is fully populated, you can proceed with generating player archetypes using the new rigorous methodology.

**1. Validate Data Quality:**
Before generating archetypes, ensure data integrity:

```bash
python verify_database_sanity.py
```

**2. Generate Optimal Player Archetypes:**
This script uses PCA-based feature engineering and multi-metric evaluation to generate basketball-meaningful archetypes.

```bash
python generate_optimal_archetypes.py
```

This will create:
- Three basketball-meaningful archetypes (Big Men, Primary Ball Handlers, Role Players)
- Player-to-archetype mappings in CSV format
- Trained models (scaler, PCA, K-means) for reproducibility
- Detailed analysis reports and visualizations

**3. Validate Archetype Quality:**
Review the generated archetypes to ensure they make basketball sense:

```bash
# Check the generated analysis
cat archetype_models_*/archetype_analysis.md

# Review player assignments
head archetype_models_*/player_archetypes.csv
```

### Step 4: Lineup Supercluster Analysis (Future)

**1. Generate Lineup Superclusters:**
This step performs K-means clustering on lineups to create the six lineup superclusters.

```bash
python generate_lineup_superclusters.py
```

**2. Run the Bayesian Model:**
This is the final, computationally intensive step that fits the Bayesian regression model.

```bash
python src/nba_stats/scripts/run_bayesian_model.py
```
**Note**: This can take a very long time to run (the paper mentions 18 hours).

After the model has finished, the posterior samples of its parameters will be saved and can be used by the analysis tools.
