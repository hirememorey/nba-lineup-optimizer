# Next Steps for Developer

**Date**: October 10, 2025
**Status**: 2022‑23 lineup stats repopulated; superclusters regenerated using full validated features (no fallback)

## 🎯 Current State

- Fixed `PlayerLineupStats` ingestion to union keys across measure types and corrected snake_case for Scoring headers (e.g., `PCT_FGA_2PT` -> `pct_fga_2pt`). Schema migration added for missing columns.
- Re-populated 2022‑23 (4,968 rows). Coverage (non‑null counts): `pct_fga_2pt`, `pct_fga_3pt`, `pct_pts_2pt_mr`, `pct_pts_3pt` ≈ 2,000 each.
- Supercluster generation now uses the 18 validated features without fallback; 21 complete rows used for clustering output.

The current state is:
- ✅ Supercluster artifacts exist and are reproducible (`robust_scaler.joblib`, `kmeans_model.joblib`, `lineup_features_with_superclusters.csv`).
- ✅ `generate_lineup_superclusters.py` now dynamically falls back to high‑coverage features if advanced fields are unavailable.
- ✅ The trained `RobustScaler` and `KMeans` models are saved to the `trained_models/` directory for reuse.
- ✅ The full pipeline is validated by a modular, two-part integration test.
- ✅ The final output of the pipeline is a clean dataset with supercluster assignments, located at `lineup_supercluster_results/lineup_features_with_superclusters.csv`.

## 🚀 Next Implementation Phase: Train and Validate the Bayesian Model

Your entire focus is to use the prepared dataset to train and validate the Bayesian model. The project is unblocked for this final, critical phase.

### **Step 1: Train model**

1. Train the Stan model with `production_bayesian_data.csv` via `train_bayesian_model.py`.
2. Validate coefficients vs paper examples with `validate_model.py` (Lakers, Pacers, Suns).

### **Optional Step 2: Improve Scoring coverage**

1. Investigate season(s) and endpoints to improve non‑null coverage of `pct_fga_2pt`, `pct_fga_3pt`, `pct_pts_2pt_mr`, `pct_pts_3pt`.
2. If coverage improves, re-run lineup population and regenerate superclusters to increase the validated‑features sample size.

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
