# Documentation Hub

Welcome to the documentation for the NBA Player Acquisition Project. This is the central source of truth for understanding and working with this project.

For a new developer, the recommended starting point is the main `README.md` file in the root directory.

## Table of Contents

*   **[Project Overview](./project_overview.md)**: A detailed explanation of the core concepts, including player archetypes, lineup superclusters, and the Bayesian modeling approach, based on the source research paper.

*   **[Architecture](./architecture.md)**: A deep dive into the system's design principles, key architectural decisions, and hard-won lessons learned during the project's development.

*   **[Data Guide](./data_guide.md)**: A comprehensive guide to the project's data architecture, including the multi-database setup and the step-by-step workflow for populating the database and running the analysis pipeline.

*   **[Data Dictionary](./data_dictionary.md)**: The definitive reference for the multi-database architecture and table structures.

*   **[API Debugging Methodology](./api_debugging_methodology.md)**: An essential guide to debugging the unofficial NBA Stats API, centered on the "Isolate with `curl` First" principle.

*   **[Data Verification Methodology](./data_verification_methodology.md)**: A comprehensive methodology for ensuring data quality before proceeding to clustering analysis, based on post-mortem insights from previous data quality failures.

*   **[Data Quality Troubleshooting Guide](./troubleshooting_data_quality.md)**: A practical guide for diagnosing and fixing common data quality issues, including the critical drive statistics API bug and other real-world problems encountered during development.

*   **[Archetype Generation Methodology](./archetype_generation_methodology.md)**: A comprehensive guide to the rigorous methodology used to generate player archetypes, including PCA-based feature engineering, multi-metric cluster evaluation, and basketball-meaningful archetype validation.

*   **[Lineup Supercluster Methodology](./lineup_supercluster_methodology.md)**: A comprehensive guide to the methodology used to generate lineup superclusters, including data quality resolution, data density assessment, and qualitative validation framework to ensure basketball-meaningful results.
