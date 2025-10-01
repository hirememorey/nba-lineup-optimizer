# Documentation Hub

Welcome to the documentation for the NBA Player Acquisition Project. This is the central source of truth for understanding and working with this project.

**Status**: ✅ **OPERATIONAL - CONTRACT AUDIT COMPLETE**

The data pipeline verification system has been completely resolved through a comprehensive "Zero-Trust Forensic Audit" that identified and fixed fundamental contract mismatches between data producers and consumers. The data pipeline is now fully operational with 100% verification success rate and automated contract enforcement. Please see the main `README.md` for more details.

For a new developer, the recommended reading order is:
1.  `README.md` (in the root directory) for a high-level overview and current status.
2.  `project_overview.md` for the core concepts.
3.  `architecture.md` for the technical design.
4.  `api_debugging_methodology.md` for essential debugging practices.
5.  `implementation_guide.md` for the new reliability features.

## Table of Contents

-   **[Project Overview](./project_overview.md)**: A detailed explanation of the core concepts, including player archetypes, lineup superclusters, and the Bayesian modeling approach.

-   **[Architecture](./architecture.md)**: A deep dive into the new data pipeline architecture, the guiding principles behind its design, and key lessons learned.

-   **[API Debugging Methodology](./api_debugging_methodology.md)**: A critical guide to debugging the unofficial NBA Stats API, centered on the "Isolate with `curl` First" principle.

-   **[Data Dictionary](./data_dictionary.md)**: **(NEW)** The definitive reference for the multi-database architecture and table structures.

-   **[Database Setup](./database_setup.md)**: A guide to the project's database schema.

-   **[Data Pipeline Guide](./data_pipeline.md)**: A step-by-step guide on how to populate the database using the legacy data population scripts.

-   **[Data Reconciliation Guide](./data_reconciliation_guide.md)**: A complete guide for achieving 100% data integrity using the enhanced reconciliation system.

-   **[Running the Analysis](./running_the_analysis.md)**: Instructions on how to execute the full analysis pipeline, from generating archetypes to running the final Bayesian model.

-   **[Implementation Guide](./implementation_guide.md)**: **(NEW)** Complete guide to the new reliability features including cache warming, API testing, data validation, and error handling.

-   **[Semantic Data Verification](./semantic_data_verification.md)**: **(NEW)** Critical tool for validating data quality before pipeline execution. Prevents the failure mode where data looks valid but produces garbage analysis results.

-   **[Verification Quick Start](./verification_quick_start.md)**: **(NEW)** Quick start guide for the corrected verification system and contract enforcement tests.

-   **[Quick Start Guide](./quick_start.md)**: **(NEW)** Step-by-step instructions for getting started with the enhanced pipeline.

-   **[Metric Investigation Summary](./metric_investigation_summary.md)**: **(NEW)** Complete findings from the investigation into the 7 missing canonical metrics, including sources and implementation recommendations.

-   **[Golden Cohort Validation](../GOLDEN_COHORT_VALIDATION.md)**: **(NEW)** Deep data integrity validation tool for identifying subtle data corruption issues.

-   **[Implementation Status](../IMPLEMENTATION_STATUS.md)**: **(NEW)** Current implementation status and next steps for completing the data pipeline.
