# Next Steps for Developer

**Date**: October 10, 2025
**Status**: Ready for Test-Driven Implementation of the Bayesian Data Pipeline

## 🎯 Current State

A critical data pipeline bug has been fixed, and the project is now ready for the final data transformation phase. The current state is:
- ✅ The `PlayerLineupStats` table is fully and correctly populated with 4,968 records for the 2022-23 season.
- ✅ A **Feature Feasibility Study** has confirmed that `PlayerLineupStats` contains all 18 features required for the lineup supercluster analysis.
- ✅ A complete **Integration Test Harness** has been built to validate the entire data pipeline, from input lineups to the final data format required by the Stan model.

## 🚀 Next Implementation Phase: Make The Test Pass

Your entire focus is to make the integration test at `tests/test_bayesian_pipeline_integrity.py` pass with the *real* data pipeline scripts. This test is your primary development tool. It will guide you through fixing the existing scripts and ensuring the data is transformed correctly.

### **Step 1: Understand the Test Harness**

Before writing any code, familiarize yourself with these three files:
1.  `tests/test_bayesian_pipeline_integrity.py`: The main test script. Notice how it loads input data, calls placeholder functions, and compares the result to an expected output.
2.  `tests/ground_truth_test_lineups.csv`: The simple, hand-crafted input data for the test.
3.  `tests/ground_truth_stan_input.csv`: The "answer key". This is the *exact* output the final data pipeline should produce from the input file.

Run the test now. It should pass, because it currently uses dummy functions designed to produce the correct output.

```bash
python3 -m unittest tests/test_bayesian_pipeline_integrity.py
```

### **Step 2: Implement Lineup Supercluster Generation**

1.  Open `tests/test_bayesian_pipeline_integrity.py`.
2.  Replace the placeholder function `generate_lineup_superclusters` with an import and call to the **actual** script responsible for this logic (likely `src/nba_stats/scripts/generate_lineup_superclusters.py`).
3.  Run the test. **It will fail.**
4.  Your task is to debug and modify the `generate_lineup_superclusters.py` script until the test passes. You will need to:
    -   Read the 18 required features from the `PlayerLineupStats` table.
    -   Perform K-Means clustering (k=6) as described in the source paper.
    -   Assign a `supercluster_id` to each lineup.
    -   Ensure the function returns a DataFrame that allows the test to pass the first stage.

### **Step 3: Implement Bayesian Data Preparation**

1.  Once the supercluster test is passing, repeat the process for the `prepare_bayesian_data` placeholder function.
2.  Replace it with a call to the **actual** script that prepares the final Stan model input (e.g., `bayesian_data_prep.py`).
3.  Run the test. It will fail.
4.  Your task is to debug and modify that script until the final output **exactly matches** the `tests/ground_truth_stan_input.csv` file. This includes creating the correct `matchup_id`.

## 📁 Key Files and Locations

### **Test Harness**
- **Test Script**: `tests/test_bayesian_pipeline_integrity.py`
- **Test Input Data**: `tests/ground_truth_test_lineups.csv`
- **Expected Test Output**: `tests/ground_truth_stan_input.csv`

### **Database**
- **Location**: `src/nba_stats/db/nba_stats.db`
- **Key Table**: `PlayerLineupStats` (This is your source data for the supercluster script).

### **Scripts to Modify**
- `src/nba_stats/scripts/generate_lineup_superclusters.py` (or equivalent)
- `src/nba_stats/scripts/bayesian_data_prep.py` (or equivalent)

## 🎯 Success Criteria

The implementation will be successful when:
1.  The `test_full_pipeline_integrity` test in `tests/test_bayesian_pipeline_integrity.py` passes.
2.  The test is no longer using any placeholder or dummy functions. It is calling the real, modified data pipeline scripts.

## 📚 Reference Materials

- **Original Paper**: `source_paper.md` - Contains the methodology for superclustering.
- **Current Status**: `CURRENT_STATUS.md` - Detailed implementation status.
- **Data Status**: `PHASE_1_DATA_STATUS.md` - Complete data inventory

## 🚨 Important Notes

1. **Database Path**: Always use `src/nba_stats/db/nba_stats.db` (not root directory)
2. **Season Filter**: Use `game_id LIKE '00222%'` for 2022-23 possessions
3. **Archetype Validation**: The k=8 clustering has been validated - don't modify
4. **Data Quality**: All data has been sanity-checked and is ready for use

## 🎉 Ready to Proceed

The foundation is solid and all prerequisites are met. The next developer can immediately begin implementing the Bayesian model with confidence that the data is complete and validated.
