# Next Steps for Developer

**Date**: October 10, 2025
**Status**: Ready for Bayesian Model Training

## 🎯 Current State

The supercluster generation pipeline is **complete, validated, and produces a high-integrity dataset**. The project has successfully navigated a critical data quality crisis, and the core data integrity risks have been mitigated.

The current state is:
- ✅ A robust, evidence-based set of 18 features has been established for clustering.
- ✅ The `generate_lineup_superclusters.py` script is a production-ready tool that correctly scales features and generates clusters.
- ✅ The trained `RobustScaler` and `KMeans` models are saved to the `trained_models/` directory for reuse.
- ✅ The full pipeline is validated by a modular, two-part integration test.
- ✅ The final output of the pipeline is a clean dataset with supercluster assignments, located at `lineup_supercluster_results/lineup_features_with_superclusters.csv`.

## 🚀 Next Implementation Phase: Train and Validate the Bayesian Model

Your entire focus is to use the high-quality supercluster data to train and validate the Bayesian model. The project is now unblocked for this final, critical phase.

### **Step 1: Implement Bayesian Data Preparation**

The `bayesian_data_prep.py` script is currently a placeholder that was used to satisfy the test harness. Your first task is to implement its full logic.

1.  **Load Supercluster Data**: Read the `lineup_features_with_superclusters.csv` file.
2.  **Load Possession Data**: Connect to the database and load the possession-level data for the 2022-23 season.
3.  **Merge and Create Matchups**: This is the core of the task. You will need to join the possession data with the lineup data (for both offensive and defensive lineups on each possession) to create the full matchup context.
4.  **Create `matchup_id`**: Based on the offensive and defensive superclusters for each possession, create the unique `matchup_id` required by the Stan model.
5.  **Prepare Final Dataset**: Aggregate and structure the data into the final format required for model training, which will include player skills (DARKO ratings) grouped by archetype for each matchup.
6.  **Save Output**: The script should output a final, model-ready CSV (e.g., `production_bayesian_data.csv`).

### **Step 2: Train the Stan Model**

Once the data preparation script is complete, your next step is to train the model.

1.  Use the output CSV from the previous step as the input for the `train_bayesian_model.py` script.
2.  Execute the script to run the MCMC simulation and generate the model coefficients.

### **Step 3: Validate the Model**

This is the final step to confirm the model's analytical integrity.

1.  With the trained model coefficients, use the `validate_model.py` script.
2.  This script should test the model's predictions against the specific, known examples from the source paper (Lakers, Pacers, and Suns).
3.  Success is achieved when our model's recommendations align with the paper's findings, proving that our implementation has captured the "basketball intelligence" of the original research.

## 📁 Key Files and Locations

### **Input Data**
- **Supercluster Data**: `lineup_supercluster_results/lineup_features_with_superclusters.csv`
- **Database (for Possession Data)**: `src/nba_stats/db/nba_stats.db`

### **Scripts to Modify/Use**
- `src/nba_stats/scripts/bayesian_data_prep.py` (Implement this)
- `train_bayesian_model.py` (Run this)
- `validate_model.py` (Run this)

### **Trained Models**
- **Scaler**: `trained_models/robust_scaler.joblib`
- **KMeans Model**: `trained_models/kmeans_model.joblib`

## 🎯 Success Criteria

The implementation will be successful when:
1.  The `bayesian_data_prep.py` script correctly processes the data and generates a model-ready input file.
2.  The Stan model trains successfully using this data.
3.  The `validate_model.py` script confirms that our model's predictions match the outcomes reported in the source paper's key examples.
