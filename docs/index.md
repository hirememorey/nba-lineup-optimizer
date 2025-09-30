# Documentation Hub

Welcome to the documentation for the NBA Player Acquisition Project. This is the central source of truth for understanding and working with this project.

For a new developer, the recommended reading order is:
1.  `README.md` (in the root directory) for a high-level overview and quick start.
2.  `project_overview.md` for the core concepts.
3.  `architecture.md` for the technical design.
4.  `api_debugging_methodology.md` for essential debugging practices.

## Table of Contents

-   **[Project Overview](./project_overview.md)**: A detailed explanation of the core concepts, including player archetypes, lineup superclusters, and the Bayesian modeling approach.

-   **[Architecture](./architecture.md)**: A deep dive into the new data pipeline architecture, the guiding principles behind its design, and key lessons learned.

-   **[API Debugging Methodology](./api_debugging_methodology.md)**: A critical guide to debugging the unofficial NBA Stats API, centered on the "Isolate with `curl` First" principle.

-   **[Data Dictionary](./data_dictionary.md)**: **(NEW)** The definitive reference for the multi-database architecture and table structures.

-   **[Database Setup](./database_setup.md)**: A guide to the project's database schema.

-   **[Data Pipeline Guide](./data_pipeline.md)**: A step-by-step guide on how to populate the database using the legacy data population scripts.

-   **[Data Reconciliation Guide](./data_reconciliation_guide.md)**: A complete guide for achieving 100% data integrity using the enhanced reconciliation system.

-   **[Running the Analysis](./running_the_analysis.md)**: Instructions on how to execute the full analysis pipeline, from generating archetypes to running the final Bayesian model.
