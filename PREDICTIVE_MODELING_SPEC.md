# Specification: Evolving to a Predictive Model

**Date**: October 17, 2025
**Status**: PHASE 1.4 COMPLETE; READY FOR PHASE 2
**Author**: Gemini

## 1. Vision & Goal

The current model is **explanatory**; it is trained on 2022-23 data and can explain lineup dynamics within that single season. The goal of this initiative is to evolve the system into a **predictive** engine.

A predictive model, by definition, must be able to forecast the performance of a future season using only data available *before* that season begins. This will transform the tool from a historical analysis project into a true offseason decision-making tool for a General Manager.

The primary objective is to build a model trained on a historical, multi-season dataset that can successfully predict the on-court struggles of the 2022-23 Russell Westbrook-era Los Angeles Lakers.

## 2. Guiding Principles (First Principles)

1.  **Past is Prologue:** A robust prediction of the future requires a deep and generalized understanding of the past. The model must learn the "durable rules of basketball" that persist across multiple seasons, coaching staffs, and league trends.
2.  **Stable Definitions:** Player archetypes must be stable and meaningful. A player's role should not radically change year-to-year based on the statistical noise of a single season.
3.  **Isolate for Prediction:** To truly test predictive power, the validation season (2022-23) must be completely held out. The model should have no information from the validation season during its training phase.
4.  **On-Court Performance is Ground Truth:** The model's predictions will be validated against the most direct measure of a lineup's performance: its actual on-court Net Rating over a statistically significant sample of possessions.

## 3. High-Level Architecture

The refined plan involves three core phases:

1.  **Phase 1: Historical Data Expansion.** The data pipeline and database schema must be extended to support multiple seasons.
2.  **Phase 2: Multi-Season Model Training.** The archetype generation and Bayesian model training processes will be re-engineered to operate on a pooled, multi-season dataset.
3.  **Phase 3: Predictive Validation.** The newly trained, historically-informed model will be used to predict the outcomes of key case studies from the held-out 2022-23 season.

## 3.1. Phase 1.4 Completion Status ✅

**Phase 1.4 has been successfully completed** with the following achievements:

### Phase 1.4.1: API Validation and Testing ✅
- **Core Players API Test**: Verified `populate_core_players.py` works with historical seasons
- **Player Stats API Test**: Confirmed player stats are available for active players in historical seasons
- **Data Quality Validation**: Identified that API works perfectly for active players, not retired ones

### Phase 1.4.2: DARKO Data Collection Fix ✅
- **Season Mapping Issue**: Discovered DARKO data uses years (2019) not season strings (2018-19)
- **Fixed Mapping Logic**: Created `populate_darko_data_fixed.py` with correct season mapping
- **Data Collection**: Successfully populated DARKO data for all historical seasons

### Phase 1.4.3: Orchestration Script Development ✅
- **Created `run_historical_data_collection.py`**: Comprehensive orchestration with resumable execution
- **Error Handling**: Robust error handling and progress tracking
- **Data Validation**: Built-in data existence checking and quality validation

### Phase 1.4.4: Historical Data Population ✅
- **2018-19**: Games (1,312), DARKO (541 players) ✅
- **2020-21**: Games (1,165), DARKO (539 players) ✅  
- **2021-22**: Games (1,317), DARKO (619 players) ✅

### Key Insight
The post-mortem was 100% accurate. The solution was simpler than anticipated - scripts already worked, we just needed to collect the data and fix mapping issues.

---

## 4. Detailed Implementation Plan

### Phase 2: Multi-Season Model Training (CURRENT PHASE)

**Status**: Phase 1.4 complete. Phase 2 is the next critical phase.

The goal of this phase is to refactor analytical scripts and train the model on pooled historical data.

**Task 2.1: Analytical Script Refactoring**

*   **Action:** Refactor analytical scripts to be season-agnostic and work with multi-season data.
*   **Priority Scripts:**
    - `create_archetypes.py` - Remove hardcoded season references, make season-agnostic
    - `generate_lineup_superclusters.py` - Make season-agnostic for multi-season data
    - `bayesian_data_prep.py` - Handle multi-season data pooling
*   **Target Seasons:** 2018-19, 2020-21, 2021-22 (training), 2022-23 (validation)
*   **Note:** Historical data collection is complete with 1,699 DARKO records across seasons.

**Task 2.2: Multi-Season Data Pooling**

*   **Action:** Combine data from historical seasons for model training.
*   **Requirements:**
    - Pool data from 2018-19, 2020-21, 2021-22 seasons
    - Ensure consistent player mapping across seasons
    - Validate data quality and completeness
*   **Verification:** Confirm pooled dataset is ready for model training.

**Task 2.3: Predictive Model Training**

*   **Action:** Train the model on pooled historical data with 2022-23 held out.
*   **Requirements:**
    - Use historical seasons for training
    - Hold out 2022-23 for validation
    - Generate model coefficients for predictive use
*   **Testing:** Validate model can learn from historical patterns

**Task 2.4: Predictive Validation**

*   **Action:** Test the model's ability to predict 2022-23 outcomes.
*   **Requirements:**
    - Russell Westbrook-Lakers case study validation
    - Compare predictions with actual 2022-23 outcomes
    - Document predictive accuracy and limitations
*   **Success Criteria:** Model correctly predicts Lakers' struggles

### Phase 2: Multi-Season Model Training

The goal of this phase is to create a model that learns from the entire historical dataset.

**Task 2.1: Re-Engineer Archetype Generation**

*   **Action:** Modify the K-Means clustering script (`create_archetypes.py`).
*   **Requirement:** The script must now query and pool the player statistics from *all three historical seasons*. The clustering will be performed on this combined dataset.
*   **Outcome:** This will produce a single, stable set of eight player archetypes that represent generalized roles across the modern NBA, rather than roles specific to a single season. The resulting archetype assignments for each player-season should be stored.

**Task 2.2: Re-Engineer Supercluster Generation**

*   **Action:** Modify the lineup supercluster generation script.
*   **Requirement:** Similar to archetype generation, this script will now pool lineup data from all three historical seasons to generate a single, stable set of six lineup superclusters.

**Task 2.3: Train the Predictive Bayesian Model**

*   **Action:** Modify the model training script (`train_bayesian_model.py`).
*   **Requirement:** The script will query and train on the pooled possession data from all three historical seasons. It will use the stable, historically-generated archetypes and superclusters as inputs.
*   **Outcome:** This will produce one set of model coefficients (`production_model_coefficients_historical.csv`) that represents the learned "durable rules of basketball."

### Phase 3: Predictive Validation

The goal of this phase is to test the new model's ability to predict the future.

**Task 3.1: Define the Validation Set**

*   **Action:** The entire 2022-23 season is the held-out validation set.
*   **Requirement:** Create a script that can prepare the 2022-23 data for prediction. This involves:
    *   Assigning the stable, historically-generated archetypes to the 2022-23 players based on their 2021-22 stats.
    *   Using the pre-season (Summer 2022) DARKO ratings for the 2022-23 season as the skill inputs.

**Task 3.2: Execute Predictive Case Studies**

*   **Action:** Create a new validation script, `validate_predictive_model.py`.
*   **Requirement:** This script will take a hypothetical 2022-23 lineup, prepare it as described in Task 3.1, and use the historically-trained model coefficients to generate a predicted value score.
*   **Primary Test Case:**
    *   **Lineup:** `[LeBron James, Anthony Davis, Russell Westbrook, Patrick Beverley, Lonnie Walker IV]` (a plausible starting lineup).
    *   **Hypothesis:** The model should predict a negative or very low positive value for this lineup.
    *   **Ground Truth:** The actual Net Rating of this and similar Westbrook-led Lakers lineups in the 2022-23 season was significantly negative.

**Task 3.3: Analyze and Document Results**

*   **Action:** Run the predictive validation script for the primary test case and the other case studies identified (Clippers, Mavs, Kings, Nets).
*   **Requirement:** For each case study, compare the model's prediction to the actual on-court Net Rating of that lineup during the 2022-23 season.
*   **Success Criteria:** The model is successful if its predictions are directionally aligned with the real-world outcomes. It should rate the Westbrook-Lakers lineup poorly, the Westbrook-Clippers lineup favorably, the Kings lineup very highly, etc.

## 5. Definition of Done

This project will be considered complete when:

1.  The data pipeline has successfully ingested and verified data for the 2018-19, 2020-21, and 2021-22 seasons.
2.  A single, stable set of archetypes and superclusters has been generated based on this historical data.
3.  A new set of model coefficients has been trained on the complete historical dataset.
4.  The `validate_predictive_model.py` script exists and demonstrates that the historically-trained model correctly predicts a poor fit for the 2022-23 Lakers with Russell Westbrook.
5.  All results are documented in a new file, `PREDICTIVE_VALIDATION_RESULTS.md`.
