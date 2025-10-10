# NBA Lineup Optimizer: Architecture and Principles

This document describes the high-level architecture of the NBA Lineup Optimizer and the core principles that guide its development. These principles are based on hard-won experience and are critical for any developer working on this project.

---

## 1. Guiding Principles

### 1.1. Validation-First Approach
The most critical principle is to validate our work against a known ground truth before scaling to new data or more complex models.

*   **Implementation**: The entire project is oriented around reproducing the exact methodology and results from the source research paper ("Algorithmic NBA Player Acquisition"). The paper's 2022-23 dataset and its specific examples (Lakers, Pacers, Suns) are treated as the absolute ground truth. Only after this validation is successful will the methodology be applied to more current data.

### 1.2. Prototype, Verify, Harden
For complex tasks like the Bayesian model implementation, we follow a staged approach to de-risk development.

*   **Implementation**:
    1.  **Prototype**: Solve the highest-risk data transformations and logic on a small, isolated scale (`semantic_prototype.py`).
    2.  **Verify**: Apply the prototype logic to the full dataset to identify all data quality issues and statistical pathologies at scale (`verify_semantic_data.py`).
    3.  **Harden**: Build the final, robust pipeline or script (`bayesian_data_prep.py`) with explicit logic to handle the issues discovered during verification.

### 1.3. Trace the Full Data Lifecycle
Instead of assuming scripts work based on their names, we adopt a forensic approach to trace the data's journey from source to destination, auditing the inputs and outputs at each step to find the exact point of failure.

### 1.4. Evidence-Driven Development (Data Archaeology)
We assume documentation and schemas can be outdated. Before writing code that depends on a data source, we inspect the raw data directly (e.g., via `sqlite3` or by inspecting API responses with `curl`) to discover its true structure.

---

## 2. System Architecture

The project is a modular Python application built around a core analytical engine.

### 2.1. Core Components
*   **Data Pipeline (`master_data_pipeline.py`)**: A collection of scripts responsible for fetching raw data from various sources (NBA Stats API, Kaggle, etc.) and populating a local SQLite database. The pipeline is designed to be resumable and idempotent.
*   **Database (`src/nba_stats/db/nba_stats.db`)**: A SQLite database that serves as the single source of truth for all raw and processed data, including player stats, possession data, and archetype features.
*   **Analytical Engine (Bayesian Model)**: A series of scripts that implement the core methodology from the source paper. This includes:
    *   `src/nba_stats/scripts/bayesian_data_prep.py`: Prepares the final model-ready dataset, streaming `Possessions`, aggregating DARKO by archetype, assigning superclusters from archetype lineups, and writing `production_bayesian_data.csv` + `stratified_sample_10k.csv`.
    *   `bayesian_model_k8.stan`: A Stan file defining the statistical model.
    *   `bayesian_model_prototype.py`: A script for quickly testing the model on a sample.
*   **User Interfaces**:
    *   `fan_friendly_dashboard.py`: A Streamlit application for non-technical users.
    *   `production_dashboard.py`: A full-featured Streamlit application for developers and administrators, including authentication and monitoring.

### 2.2. Data Flow
1.  **Ingestion**: The `master_data_pipeline.py` and other `populate_*.py` scripts fetch data and store it in the `nba_stats.db`.
2.  **Preparation**: For the Bayesian model, `src/nba_stats/scripts/bayesian_data_prep.py` reads from the database, performs transformations (Z aggregation by archetype, matchup_id construction), and outputs `production_bayesian_data.csv` and `stratified_sample_10k.csv`.
3.  **Modeling**: The Stan model is trained on the prepared CSV to produce coefficients.
4.  **Presentation**: The dashboards read from the database and use the model's outputs to provide analysis to the user.

---

## 3. Core Concepts (from the Source Paper)

The model is built on the premise that a player's value is deeply contextual, depending on their role and how it interacts with teammates and opponents.

*   **Player Archetypes (k=8)**: Players are clustered into one of eight archetypes (e.g., "Scoring Wing," "Defensive Minded Guard") based on 48 canonical metrics that describe their style of play.
*   **Lineup Superclusters**: Five-player lineups are themselves clustered into groups based on their collective play style (e.g., "Three-Point Symphony," "Slashing Offenses"). This is a critical component that is currently implemented as a placeholder.
*   **Bayesian Possession-Level Modeling**: The core of the project. A Bayesian regression model estimates the outcome of a single possession based on the matchup between the offensive and defensive superclusters and the aggregated skill (DARKO ratings) of the players in each archetype.
