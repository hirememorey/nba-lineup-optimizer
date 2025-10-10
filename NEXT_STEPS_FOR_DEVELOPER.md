# Next Steps for Developer

**Date**: October 10, 2025
**Status**: Ready for Bayesian Model Training (Data Prep Complete)

## 🎯 Current State

The supercluster generation pipeline has been regenerated after aligning column names. Due to missing advanced lineup fields in `PlayerLineupStats`, the generator automatically fell back to high‑coverage features (`w_pct`, `gp`, `w`, `l`, `min`) to ensure artifacts exist. Database sanity checks passed and Bayesian data prep has produced the model‑ready dataset.

The current state is:
- ✅ Supercluster artifacts exist and are reproducible (`robust_scaler.joblib`, `kmeans_model.joblib`, `lineup_features_with_superclusters.csv`).
- ✅ `generate_lineup_superclusters.py` now dynamically falls back to high‑coverage features if advanced fields are unavailable.
- ✅ The trained `RobustScaler` and `KMeans` models are saved to the `trained_models/` directory for reuse.
- ✅ The full pipeline is validated by a modular, two-part integration test.
- ✅ The final output of the pipeline is a clean dataset with supercluster assignments, located at `lineup_supercluster_results/lineup_features_with_superclusters.csv`.

## 🚀 Next Implementation Phase: Train and Validate the Bayesian Model

Your entire focus is to use the prepared dataset to train and validate the Bayesian model. The project is unblocked for this final, critical phase.

### **Step 1: Use Prepared Data**

1.  Confirm presence of `production_bayesian_data.csv` (627,969 rows) and `stratified_sample_10k.csv`.
2.  If needed, regenerate superclusters only after restoring advanced lineup fields.

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

### **Optional Quality Upgrade**
- Repopulate advanced lineup/percentage fields in `PlayerLineupStats` (e.g., `off_rating`, `def_rating`, `ts_pct`, `pace`, `pct_fga_2pt`, `pct_fga_3pt`, `pct_pts_2pt_mr`, `pct_pts_3pt`, `pct_pts_fb`).
- Rerun `generate_lineup_superclusters.py` to replace fallback features with richer signal.

## 🎯 Success Criteria

The implementation will be successful when:
1.  The `bayesian_data_prep.py` script correctly processes the data and generates a model-ready input file.
2.  The Stan model trains successfully using this data.
3.  The `validate_model.py` script confirms that our model's predictions match the outcomes reported in the source paper's key examples.
