# NBA Data Pipeline Architecture

## Overview

This document describes the completely redesigned NBA data pipeline, built using first-principles reasoning and incorporating the critical insights from the post-mortem analysis. The new architecture addresses the core challenge of **data mapping** rather than API reliability, implementing a sparsity-aware approach to handle missing data gracefully.

## Key Insights & Guiding Principles

The previous implementation failed because it focused on the wrong problem. The core challenge is not API reliability—it's **column mapping**. The NBA API works fine, but the data exists in different endpoints with different column names than expected.

The new architecture is built on the following principles:

1.  **Mapping-First Approach**: Understand the data landscape completely before building the system.
2.  **Sparsity-Aware Design**: Build for missing data from the start; don't try to achieve 100% coverage.
3.  **Forensic Data Analysis**: Use comprehensive API reconnaissance to discover all available columns.
4.  **Incremental Validation**: Test and verify each piece before moving to the next.
5.  **Centralized Architecture**: Use a single, robust data fetcher instead of scattered, fragile scripts.

### Architectural Notes & Lessons Learned

A developer picking up this project should be aware of several key architectural decisions and challenges that were overcome during the data population phase. These insights are critical for understanding why the code is structured the way it is and for debugging future issues.

#### 1. The "Sacred Schema" Principle

*   **Problem**: Initial attempts to run the data pipeline resulted in database errors because different scripts contained their own `CREATE TABLE` statements, which conflicted with the official, migrated schema.
*   **Principle**: A data pipeline's integrity relies on a single source of truth for its schema. Application-level code should **never** define or alter the schema on the fly.
*   **Solution**: The authoritative schema is now defined **exclusively** in the database migration scripts. All `CREATE TABLE` statements have been ruthlessly removed from other scripts.

#### 2. Resumption Over Perfection for Long-Running I/O

*   **Problem**: The `populate_possessions.py` script was originally designed as an "all-or-nothing" operation that was architecturally guaranteed to fail due to inevitable network timeouts, losing all progress on each failure.
*   **Principle**: Any long-running process involving network I/O is not just likely to fail—it is guaranteed to fail. A robust system is not one that never fails, but one that gracefully handles failure.
*   **Solution**: The script was refactored to be **resumable and idempotent**. It now queries the database first to see what work has already been done, processes only the missing data, and saves atomically after each unit of work.

#### 3. Defensive Programming Against Unpredictable Data

*   **Problem**: After fixing system-level issues, `ValueError` exceptions occurred due to the unreliability of the `nba_api` for historical data.
*   **Principle**: A robust data pipeline must assume its inputs are "guilty until proven innocent" and defensively validate the *shape* of the data at every step.
*   **Solution**: The lineup inference logic was hardened significantly. The dependency on a failing endpoint was removed, a new algorithm was implemented to find the first five unique players, and a strict validation check was added to enforce the contract of five players, safely skipping and logging any game that violates it.

## Architecture Components

### 1. API Reconnaissance Tool (`api_reconnaissance.py`)

Performs comprehensive forensics on the NBA Stats API to discover all available columns.

*   **Key Features:**
    *   Tests multiple parameter combinations for each endpoint.
    *   Discovers schema variations across different player types.
    *   Generates complete column inventory reports.
    *   Identifies missing metrics upfront.

### 2. Definitive Metric Mapping (`definitive_metric_mapping.py`)

Provides the authoritative mapping between the 47 canonical metrics from the source paper and their actual API sources.

*   **Key Features:**
    *   Maps all 47 metrics to their API endpoints and column names.
    *   Identifies which metrics are missing from the API.
    *   Provides data type information and validation checks.

### 3. Centralized Data Fetcher (`src/nba_stats/api/data_fetcher.py`)

A unified interface for fetching NBA player data with built-in error handling and schema awareness.

*   **Key Features:**
    *   Single interface for all API endpoints.
    *   Built-in rate limiting and retry logic.
    *   Schema-aware data extraction and data type validation.
    *   **Persistent Caching Layer**: All API responses are cached locally in the `.cache/` directory for 24 hours, eliminating redundant network calls and providing resilience.
    *   **Increased Timeout**: The request timeout has been increased to 300 seconds (5 minutes) to handle large, bulk data requests without failing.

### 4. Master Data Pipeline (`master_data_pipeline.py`)

Orchestrates the entire data pipeline with comprehensive validation and reporting.

*   **Key Features:**
    *   Full and incremental pipeline execution.
    *   Comprehensive validation and data quality scoring.
    *   Detailed reporting.

### 5. Data Verification Tool (`data_verification_tool.py`)

Provides comprehensive verification of data completeness, quality, and logical consistency.

*   **Key Features:**
    *   Completeness and quality metrics.
    *   Logical consistency checks.
    *   Sparsity analysis (a key insight from the project's post-mortem).
    *   Anomaly detection.

### 6. Data Imputation Tool (`data_imputation_tool.py`)

Handles missing values using various imputation strategies, implementing the sparsity-aware approach.

*   **Key Features:**
    *   Multiple imputation strategies (mean, median, KNN, Random Forest).
    *   Automatic strategy selection based on data characteristics.
    *   Validation of imputation quality.
