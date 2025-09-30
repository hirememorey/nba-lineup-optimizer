# NBA Lineup Optimizer

This project implements the methodology from the research paper "Algorithmic NBA Player Acquisition" by Brill, Hughes, and Waldbaum. It uses a data-driven approach to NBA player acquisition and lineup optimization, prioritizing team **fit** over individual skill alone.

The project has recently undergone a complete architectural redesign based on first-principles reasoning and is now ready for analysis.

## Current Status

**Date**: September 30, 2025  
**Status**: ✅ **IMPLEMENTATION COMPLETE - READY FOR PRODUCTION**

The project now includes comprehensive API reliability features, data validation, and robust error handling. All systems are ready for production use.

-   **Data Pipeline Architecture**: Complete with mapping-first, sparsity-aware design
-   **API Reliability**: Cache-first development, comprehensive testing, and retry logic
-   **Data Validation**: Pydantic models ensure data integrity at every step
-   **Observability**: Progress bars, detailed logging, and comprehensive reporting
-   **Resumability**: Pipeline can be interrupted and resumed without data loss
-   **Available Metrics**: 41 of the 47 canonical metrics (87.2%) mapped to NBA API
-   **Ready for Execution**: All systems validated and ready for 2024-25 season data

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

### 2. Validate System (Recommended)

**✅ NEW**: Run comprehensive validation to ensure all systems are working correctly.

```bash
# Complete validation (recommended)
python run_implementation_demo.py

# Or run individual tests
python warm_cache.py --season 2024-25
python test_api_connection.py --season 2024-25
```

### 3. Run the Data Pipeline

**✅ ENHANCED**: The pipeline now includes progress bars, validation, and resumability.

```bash
python master_data_pipeline.py --season 2024-25
```

### 4. Verify Data Quality

Run the verification tool to get a comprehensive report on the quality, completeness, and consistency of the fetched data.

```bash
python data_verification_tool.py
```

### 5. Handle Missing Data (If Needed)

Use the imputation tool to handle any missing values using ML-based strategies.

```bash
python data_imputation_tool.py --strategy auto
```

### 6. Run the Analysis

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
-   **`docs/implementation_guide.md`**: **(NEW)** Complete guide to the new reliability features including cache warming, API testing, data validation, and error handling.
-   **`docs/quick_start.md`**: **(NEW)** Step-by-step instructions for getting started with the enhanced pipeline. 