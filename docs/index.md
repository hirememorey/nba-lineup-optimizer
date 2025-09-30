# Welcome to the NBA Player Acquisition Project

This repository contains the code and documentation for the "Algorithmic NBA Player Acquisition" project. The goal of this project is to provide a data-driven framework for evaluating NBA players based not just on their individual skill, but on how well they **fit** within different team structures and strategies.

## Documentation Hub

This `docs` directory is the central source of truth for understanding and working with this project.

- **[Project Overview](./project_overview.md)**: Start here for a detailed explanation of the core concepts, including player archetypes, lineup superclusters, and the Bayesian modeling approach.

- **[Database Setup](./database_setup.md)**: Provides a guide to the project's database schema and outlines the **critical, high-priority modifications** needed before running the analysis.

- **[Data Pipeline Guide](./data_pipeline.md)**: A step-by-step guide on how to populate the database with data for a new NBA season using the provided scripts.

- **[Running the Analysis](./running_the_analysis.md)**: Instructions on how to execute the full analysis pipeline, from generating archetypes to running the final Bayesian model.

- **[Next Steps for 2024-25 Season](./next_steps.md)**: A checklist of the immediate tasks required to get the project ready for the 2024-25 NBA season.

- **[Data Integrity Verification](./data_integrity_verification.md)**: Comprehensive report on data quality verification and validation results.

- **[Data Verification Summary](./data_verification_summary.md)**: Executive summary of current data status and verification results (Updated: September 30, 2025).

- **[Data Reconciliation Guide](./data_reconciliation_guide.md)**: Complete guide for achieving 100% data integrity using the enhanced reconciliation system.

- **[API Reliability Improvements](./api_reliability_improvements.md)**: Documentation of architectural improvements to address NBA API reliability issues and data corruption.

- **[API Debugging Methodology](./api_debugging_methodology.md)**: Critical methodology for debugging NBA API issues using the "Isolate with curl First" principle.

## Getting Started

For a new developer, the recommended reading order is:
1.  `project_overview.md`
2.  `data_verification_summary.md` (start here for current status)
3.  `api_reliability_improvements.md` (critical: understand data integrity issues)
4.  `api_debugging_methodology.md` (essential: how to debug API issues)
5.  `database_setup.md`
6.  `data_integrity_verification.md`
7.  `data_reconciliation_guide.md` (if you want 100% data integrity)
8.  `next_steps.md`

This will provide a full conceptual understanding of the project, verification status, reconciliation capabilities, and a clear picture of the immediate tasks at hand.
