# Running the Analysis Pipeline

Once the database has been fully populated for the target season, you can proceed with the core analysis. This involves generating the player archetypes and lineup superclusters, and then running the main Bayesian model.

The key scripts for this process are located in `src/nba_stats/scripts/`.

## Analysis Steps

### 1. Generate Archetype Features

This step queries the various statistics tables in the database and consolidates the 48 required metrics into a single feature set for each player.

- **Command**:
  ```bash
  python src/nba_stats/scripts/generate_archetype_features.py
  ```
- **Output**: This will create a file (e.g., `archetype_features.csv`) that will be used as the input for the clustering model.

### 2. Generate Lineup Superclusters

This step performs the K-means clustering on lineups to create the six lineup superclusters.

- **Command**:
  ```bash
  python src/nba_stats/scripts/generate_lineup_superclusters.py
  ```

### 3. Run the Bayesian Model

This is the final and most computationally intensive step. It uses the generated archetypes, superclusters, and the possession-level data to fit the Bayesian regression model using Stan.

- **Model File**: `src/nba_stats/models/bayesian_model.stan`
- **Command**:
  ```bash
  python src/nba_stats/scripts/run_bayesian_model.py
  ```
- **Execution Time**: Be aware that this step can take a very long time to run (the paper mentions 18 hours for a single MCMC chain).

## Workflow Summary

To run the full analysis from start to finish for a new season:

1.  **Populate all data** for the season by following the `data_pipeline.md` guide.
2.  **Generate the archetype features**.
3.  **Generate the lineup superclusters**.
4.  **Run the Bayesian model**.

After the model has finished running, the posterior samples of the model's parameters will be saved. These can then be used to perform the player acquisition analysis as described in the paper.
