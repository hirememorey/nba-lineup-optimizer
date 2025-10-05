# Documentation Hub

Welcome to the documentation for the NBA Lineup Optimizer project. This is the central source of truth for understanding and working with this project.

**For new developers, start with the main `README.md` file in the root directory.**

## Quick Start

*   **[README.md](../README.md)**: Project overview, current status, and quick start guide
*   **[CURRENT_STATUS.md](../CURRENT_STATUS.md)**: Detailed current state and next steps
*   **[QUICK_START_GUIDE.md](../QUICK_START_GUIDE.md)**: Step-by-step instructions for getting started

## Core Documentation

### Project Understanding
*   **[Project Overview](./project_overview.md)**: Core concepts, player archetypes, lineup superclusters, and Bayesian modeling approach
*   **[Architecture](./architecture.md)**: System design principles, key decisions, and lessons learned
*   **[Data Dictionary](./data_dictionary.md)**: Definitive reference for the multi-database architecture and table structures

### Data & Analysis
*   **[Data Guide](./data_guide.md)**: Data architecture, multi-database setup, and analysis pipeline workflow
*   **[Troubleshooting Data Quality](./troubleshooting_data_quality.md)**: Practical guide for diagnosing and fixing data quality issues

### Production System
*   **[Production Features](./production_features.md)**: Authentication, data protection, user analytics, monitoring, and admin capabilities
*   **[Deployment Guide](../DEPLOYMENT.md)**: Docker deployment, configuration, and security considerations
*   **[Implementation Guide](./implementation_guide.md)**: Quick-start guide for new developers

## Methodology Deep Dives

*   **[API Debugging](./methodology/api_debugging_methodology.md)**: Essential guide to debugging the NBA Stats API using "Isolate with `curl` First" principle
*   **[Data Verification](./methodology/data_verification_methodology.md)**: Comprehensive methodology for ensuring data quality before clustering analysis
*   **[Archetype Generation](./methodology/archetype_generation_methodology.md)**: Rigorous methodology for generating player archetypes with PCA-based feature engineering
*   **[Lineup Superclusters](./methodology/lineup_supercluster_methodology.md)**: Methodology for generating lineup superclusters with qualitative validation
*   **[Bayesian Modeling](./methodology/bayesian_modeling_implementation.md)**: Core analytical engine implementation and scaling analysis
*   **[Production Bayesian Model](./production_bayesian_model.md)**: Deployed production model documentation and integration instructions
*   **[Opponent Shooting Stats](./methodology/opponent_shooting_stats_implementation.md)**: Implementation details for defensive shooting statistics

## Archived Documentation

Historical and completed implementation documents are available in the [archive](./archive/) directory for reference.
