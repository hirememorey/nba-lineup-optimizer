# NBA Lineup Optimizer

This project implements the methodology from the research paper "Algorithmic NBA Player Acquisition" by Brill, Hughes, and Waldbaum. It uses a data-driven approach to NBA player acquisition and lineup optimization, prioritizing team **fit** over individual skill alone.

The project has recently undergone a complete architectural redesign based on first-principles reasoning and is now ready for analysis.

## Current Status

**Date**: September 30, 2025  
**Status**: ⚠️ **DATA PIPELINE NEEDS EXECUTION - ARCHITECTURE READY**

The new data pipeline architecture is complete and robust, but requires execution for the 2024-25 season.

-   **Data Pipeline Architecture**: The new mapping-first, sparsity-aware pipeline is complete and ready for execution.
-   **Available Metrics**: 41 of the 47 canonical metrics (87.2%) required by the paper have been successfully mapped to the NBA API.
-   **Known Missing Metrics**: 6 metrics (related to average shot distance and wingspan) are confirmed to be unavailable from the primary API endpoints. The system is designed to handle this.
-   **Critical Finding**: The advanced statistics tables are currently empty for the 2024-25 season, indicating the data pipeline has not been run for this season.
-   **Next Step**: Execute the master data pipeline to populate the database with 2024-25 season data.

## Quick Start Guide

### 1. Setup

Clone the repository and install the required dependencies.

```bash
git clone https://github.com/your-repo/nba-lineup-optimizer.git
cd nba-lineup-optimizer
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the Data Pipeline

**⚠️ REQUIRED**: This command orchestrates the entire process of discovering, fetching, and validating the data required for the analysis. This must be run before proceeding to analysis.

```bash
python master_data_pipeline.py --season 2024-25
```

### 3. Verify Data Quality

Run the verification tool to get a comprehensive report on the quality, completeness, and consistency of the fetched data.

```bash
python data_verification_tool.py
```

### 4. Handle Missing Data (If Needed)

Use the imputation tool to handle any missing values using ML-based strategies.

```bash
python data_imputation_tool.py --strategy auto
```

### 5. Run the Analysis

With a clean dataset, you can now proceed to the analysis phase.

```bash
# Follow the instructions in the "Running the Analysis" guide
```

## Data Architecture

The project uses a multi-database architecture with data distributed across three SQLite files:

- **Primary Database**: `src/nba_stats/db/nba_stats.db` - Contains processed, analysis-ready data
- **Secondary Database**: `nba_data.db` - Contains raw player tracking data
- **Tertiary Database**: `nba_lineup_data.db` - Contains lineup-specific data

For detailed information about the database structure, see `docs/data_dictionary.md`.

## Documentation

For a deeper understanding of the project, please refer to the comprehensive documentation:

-   **`docs/index.md`**: The central hub and table of contents for all documentation.
-   **`docs/project_overview.md`**: A detailed explanation of the core concepts (player archetypes, lineup superclusters, Bayesian modeling).
-   **`docs/architecture.md`**: A deep dive into the new data pipeline architecture, design principles, and lessons learned.
-   **`docs/data_dictionary.md`**: **(NEW)** The definitive reference for the multi-database architecture and table structures.
-   **`docs/database_setup.md`**: Updated guide to the database schema and setup.
-   **`docs/api_debugging_methodology.md`**: **(Recommended Reading)** The essential guide to debugging the unofficial NBA Stats API using the "Isolate with `curl` First" principle. 