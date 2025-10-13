# Next Steps for Developer

**Date**: October 10, 2025
**Status**: 2022‑23 lineup stats repopulated; superclusters regenerated with fallback (awaiting scoring share fields)

## 🎯 Current State

- Fixed `PlayerLineupStats` ingestion to union all fetched keys; re-populated 2022‑23 (4,968 rows).
- Advanced fields now present: `off_rating`, `def_rating`, `ts_pct`, `pace`, `efg_pct`, `ast_pct`, `ast_to`, `oreb_pct`, `dreb_pct`, `reb_pct`, `tm_tov_pct`.
- Still missing: `pct_fga_2pt`, `pct_fga_3pt`, `pct_pts_2pt_mr`, `pct_pts_3pt` from insert column set; clustering fell back.

The current state is:
- ✅ Supercluster artifacts exist and are reproducible (`robust_scaler.joblib`, `kmeans_model.joblib`, `lineup_features_with_superclusters.csv`).
- ✅ `generate_lineup_superclusters.py` now dynamically falls back to high‑coverage features if advanced fields are unavailable.
- ✅ The trained `RobustScaler` and `KMeans` models are saved to the `trained_models/` directory for reuse.
- ✅ The full pipeline is validated by a modular, two-part integration test.
- ✅ The final output of the pipeline is a clean dataset with supercluster assignments, located at `lineup_supercluster_results/lineup_features_with_superclusters.csv`.

## 🚀 Next Implementation Phase: Train and Validate the Bayesian Model

Your entire focus is to use the prepared dataset to train and validate the Bayesian model. The project is unblocked for this final, critical phase.

### **Step 1: Restore scoring share fields (recommended path)**

1. Confirm the lineup Scoring measure headers (cache used): `src/nba_stats/.cache/643e51baf99fca47beec004f63212eb7.json`.
2. Ensure `pct_fga_2pt`, `pct_fga_3pt`, `pct_pts_2pt_mr`, `pct_pts_3pt` map to snake_case in aggregation (they should already); verify they appear across enough rows.
3. Re-run lineup population for 2022‑23 and 2024‑25, check `nba_stats.log` for "Advanced present" and ensure the four pct_* fields are included.
4. Re-run `generate_lineup_superclusters.py`; confirm validated 18 features are used without fallback.

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

### **Alternate Path (if blocked on pct_*):**
- Proceed with model training using fallback superclusters to unblock downstream validation, then backfill scoring shares and upgrade clustering.

## 🎯 Success Criteria

The implementation will be successful when:
1.  The `bayesian_data_prep.py` script correctly processes the data and generates a model-ready input file.
2.  The Stan model trains successfully using this data.
3.  The `validate_model.py` script confirms that our model's predictions match the outcomes reported in the source paper's key examples.
