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

*   **[Bayesian Modeling Implementation](./bayesian_modeling_implementation.md)**: A comprehensive guide to the Bayesian possession-level modeling system, including data preparation pipeline, prototype model validation, and scaling analysis. This is the core analytical engine of the project.

*   **[Production Bayesian Model](./production_bayesian_model.md)**: Documentation for the deployed production model, including architecture decisions, performance metrics, and integration instructions. This is the operational model currently in use.

*   **[Model Integration Guide](../IMPLEMENTATION_COMPLETE.md)**: Complete documentation of the model integration implementation, including the Model Factory, Enhanced Dashboard, and performance optimization features.

*   **[Production Implementation Summary](../IMPLEMENTATION_SUMMARY.md)**: Complete documentation of the production system implementation, including authentication, monitoring, user management, and deployment.

*   **[Production Features](./production_features.md)**: Detailed documentation of all production features including authentication, data protection, user analytics, monitoring, and administrative capabilities.

*   **[Deployment Guide](../DEPLOYMENT.md)**: Comprehensive deployment documentation for production systems, including Docker deployment, configuration, and security considerations.

*   **[Implementation Guide](./implementation_guide.md)**: A quick-start guide for new developers joining the project, covering the current state, key insights, and next steps for continued development.
