# NBA Data Pipeline Architecture

## Overview

This document describes the NBA data pipeline architecture, which has been designed and refined based on first-principles reasoning and critical insights from post-mortem analyses of past failures. The architecture is built to handle the complexities and unreliability of the unofficial NBA Stats API and to ensure a high degree of data integrity.

## Core Architectural Principles

The system is built on a set of core principles learned from hard-won experience during the project's development.

### 1. Evidence-Driven Development & Data Archaeology

*   **Principle**: Assume documentation is outdated and build based on the ground truth of the data. The project's history is filled with instances where the documented schema or API behavior did not match reality.
*   **Implementation**: Before writing code, the actual database schema was discovered using `sqlite3` commands and API responses were inspected manually. This "data archaeology" informed the creation of an anti-corruption layer (`db_mapping.py`) to handle discrepancies between the expected and actual data structures.

### 2. Validation-First & Contract Enforcement

*   **Principle**: Human trust is a product, not a process. To ensure the reliability of the model, a structured and robust validation process is essential. Furthermore, the contracts between different parts of the system must be automatically enforced to prevent drift.
*   **Implementation**:
    *   **Model Governance Dashboard**: A dedicated Streamlit application for the structured, human-in-the-loop validation of model coefficients. It was built *first* to ensure a trusted path to production for the model.
    *   **Semantic Prototyping**: A fast validation script (`semantic_prototype.py`) runs in 60 seconds (vs. 18 hours for the full model) to check that the analytical logic is sound.
    *   **Continuous Schema Validation**: A `LiveSchemaValidator` checks for data drift at runtime against a set of expectations defined in `schema_expectations.yml`.

### 3. The "Sacred Schema" and Resumability

*   **Principle**: A data pipeline's integrity relies on a single source of truth for its schema, and any long-running I/O process is guaranteed to fail.
*   **Implementation**:
    *   The authoritative database schema is defined **exclusively** in database migration scripts. Application-level code never defines or alters the schema.
    *   Long-running scripts like `populate_possessions.py` are **resumable and idempotent**. They query the database first to see what work has already been completed and process only the missing data.

### 4. Defensive Programming & Single Source of Truth

*   **Principle**: The system must be architecturally incapable of processing incomplete player data, and all tools must use the same core logic to prevent inconsistencies.
*   **Implementation**:
    *   The `ModelEvaluator` library is the **single source of truth** for all lineup analysis.
    *   It operates on a "blessed" set of players with complete data, refusing to process any player with incomplete information. This converts a data quality problem into a clear, manageable error.

### 5. Sparsity-Aware Design

*   **Principle**: Not all data will be available for all players. The system must be built for missing data from the start, rather than trying to achieve 100% coverage for every metric.
*   **Implementation**: Optional enhancement data, like wingspan (which is only available for draft combine attendees), is stored in separate tables with nullable fields (e.g., `PlayerAnthroStats`). This allows the core analysis to proceed without being blocked by sparse, non-essential data.

### 6. Verification at the Right Level of Abstraction

*   **Principle**: The most critical lesson learned was to **always verify the final output table used for analysis**, not just the intermediate source tables.
*   **Implementation**: The verification process now includes checks on the final `PlayerArchetypeFeatures` table to ensure that data has not only been fetched but has also been correctly transformed and loaded into its final destination. Automated data quality gates and end-to-end pipeline tests are now part of the process.

## Key Architectural Components

### 1. Enhanced API Client & Pipeline Robustness

To handle the unreliable nature of the NBA Stats API, the pipeline includes several layers of protection:

*   **Cache-First Development**: A `warm_cache.py` script populates a local cache, allowing development to occur against static, reliable data, decoupling it from the live API.
*   **Silent Failure Detection**: A "Post-Fetch Assertion Layer" in the API client detects when the API returns a `200 OK` status with an empty data set, converting a silent failure into a loud, retryable error.
*   **Intelligent Retry Logic**: The `tenacity` library is used to implement exponential backoff for API requests, only retrying on appropriate, transient error conditions.
*   **Data Integrity Protection**: Pydantic models (`response_models.py`) are used to validate the structure, types, and ranges of all API responses at the system's boundaries, preventing corrupted data from entering the pipeline.

### 2. The ModelEvaluator Core Library

The `ModelEvaluator` is the heart of the analysis system, providing a robust and validated foundation for all tools.

*   **Single Source of Truth**: All tools, including the validation suite, player acquisition tool, and interactive dashboard, use this same library.
*   **Defensive Data Loading**: It only loads the 270 "blessed" players who have complete skill and archetype data, raising an `IncompletePlayerError` if any player in a lineup is not part of this set.
*   **Comprehensive Validation**: The library itself is validated by a suite of 16 technical tests (100% coverage) and 7 basketball intelligence tests (85.7% pass rate).

### 3. Possession-Level Modeling System

This system implements the core methodology from the research paper.

*   **Anti-Corruption Layers**: It includes a `db_mapping.py` layer to handle schema inconsistencies and the `LiveSchemaValidator` to prevent data drift.
*   **Semantic Prototyping**: Allows for rapid validation of the analytical logic before running the full, computationally expensive Bayesian model.
*   **Data Reality**: It was built based on a thorough "data archaeology" process to discover the true state of the database, which led to the discovery of 574,357 possessions with complete lineup data.
