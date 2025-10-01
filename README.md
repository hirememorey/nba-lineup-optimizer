# NBA Lineup Optimizer

This project implements the methodology from the research paper "Algorithmic NBA Player Acquisition" by Brill, Hughes, and Waldbaum. It uses a data-driven approach to NBA player acquisition and lineup optimization, prioritizing team **fit** over individual skill alone.

The project has recently undergone a complete architectural redesign based on first-principles reasoning and is now ready for analysis.

## Current Status

**Date**: October 1, 2025  
**Status**: ✅ **OPERATIONAL - API ISSUES RESOLVED**

The project's robust testing suite has successfully identified and resolved the upstream NBA Stats API issues. The data pipeline is **now fully operational** for the 2024-25 season.

The investigation revealed that the API failures were due to outdated request headers. The NBA Stats API now requires a complete set of modern, browser-generated headers for successful requests. This has been resolved and documented.

-   **Data Pipeline Architecture**: Complete with mapping-first, sparsity-aware design
-   **API Reliability**: Cache-first development, comprehensive testing, and retry logic
-   **Semantic Data Verification**: NEW - Validates data quality before pipeline execution
-   **Data Validation**: Pydantic models ensure data integrity at every step
-   **Observability**: Progress bars, detailed logging, and comprehensive reporting
-   **Resumability**: Pipeline can be interrupted and resumed without data loss
-   **API Status**: ✅ **OPERATIONAL** - See `docs/metric_investigation_summary.md`
-   **Missing Metrics Investigation**: ✅ **COMPLETE** - 6 of 7 missing metrics identified and sourced
-   **Data Quality Score**: Ready for validation
-   **Player Coverage**: Ready for population

## Quick Start Guide

**✅ READY TO PROCEED:** The data pipeline is now fully operational. The API issues have been resolved and the system is ready for data collection.

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

**✅ NEW**: Run comprehensive validation to confirm the current system status. This is the best first step.

```bash
# This will run all checks and confirm the system is operational.
python run_implementation_demo.py

# You can also run the API smoke test directly.
python test_api_connection.py --season 2024-25
```
**Expected Outcome**: The smoke test should now pass. Review the generated `api_smoke_test_report.md` for detailed results.

### 3. Verify Data Quality (CRITICAL)

**✅ NEW**: Always run semantic data verification before the pipeline to prevent data quality issues.

```bash
python verify_semantic_data.py --season 2024-25
```

### 4. Run the Data Pipeline

**✅ READY TO EXECUTE**: The pipeline is now operational and ready to collect data.

```bash
# This command should now execute successfully.
python master_data_pipeline.py --season 2024-25
```

### 5. Verify Data Quality

Run the verification tool to get a comprehensive report on the quality, completeness, and consistency of the fetched data.

```bash
python data_verification_tool.py
```

### 6. Handle Missing Data (If Needed)

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

## Missing Metrics Investigation

**Status**: ✅ **COMPLETE** - October 1, 2025

A comprehensive investigation was conducted to identify sources for the 7 missing canonical metrics required by the source paper. The investigation used a `curl`-first, manual validation approach to ensure accuracy.

**Key Findings**:
- **6 of 7 metrics identified and sourced**: `AVGDIST`, `Zto3r`, `THto10r`, `TENto16r`, `SIXTto3PTr`, and `HEIGHT`
- **1 metric requires external sourcing**: `WINGSPAN` (not available via NBA Stats API)
- **Critical technical requirement**: NBA Stats API now requires complete browser-generated headers for all requests

**Implementation Plan**: See `docs/metric_investigation_summary.md` for detailed findings and implementation recommendations.

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