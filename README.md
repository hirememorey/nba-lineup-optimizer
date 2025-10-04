# NBA Lineup Optimizer

This project implements the methodology from the research paper "Algorithmic NBA Player Acquisition" by Brill, Hughes, and Waldbaum. It uses a data-driven approach to NBA player acquisition and lineup optimization, prioritizing team **fit** over individual skill alone.

The project has recently undergone a complete architectural redesign based on first-principles reasoning and is now in the final stages of implementation.

## Current Status

**Date**: October 3, 2025
**Status**: ✅ **MODEL INTEGRATION COMPLETE**

The project has successfully completed all core components: player archetype generation, lineup supercluster analysis, and Bayesian modeling implementation. A production-ready Bayesian model has been deployed and fully integrated with a new `SimpleModelEvaluator` that uses the 7-parameter production model. The system now includes a unified interface for model switching, comprehensive comparison tools, and performance optimization.

### What's Working ✅

*   **Complete Tooling Suite**:
    *   **Enhanced Model Dashboard**: Unified interface with model switching, comparison, and performance monitoring.
    *   **Model Governance Dashboard**: For structured human validation of model coefficients.
    *   **Model Comparison Dashboard**: For side-by-side validation of original vs production models.
    *   **Player Acquisition Tool**: To find the best 5th player for a 4-player core.
    *   **Interactive Analysis Platform**: A Streamlit UI with 6 analysis modes for deep exploration.
*   **Robust Data Pipeline**: A reliable and resumable data pipeline is in place.
*   **ModelEvaluator Foundation**: A "bulletproof" core library provides a single source of truth for all analysis.
*   **Complete Data Coverage**: All critical player tracking statistics are now fully populated:
    *   **Player Archetype Coverage**: 651 players (100% coverage with fallback assignments)
    *   **Possession Data**: 574,357 possessions with complete lineup data
    *   **Drive Statistics**: 100% coverage with proper variance
    *   **All Advanced Metrics**: 100% coverage for 48 canonical features
*   **Comprehensive Database**: 651 players with complete archetype assignments, 574k+ possessions, and all supporting data.

### Player Archetypes Generated ✅ (October 3, 2025)

*   **Optimal K-Value Determination**: ✅ **COMPLETED** - Used rigorous multi-metric evaluation to determine k=3 with PCA (80% variance) as optimal
*   **Feature Space Engineering**: ✅ **COMPLETED** - Implemented PCA-based dimensionality reduction (47 → 13 components, 81.9% variance)
*   **Basketball-Meaningful Archetypes**: ✅ **COMPLETED** - Generated three interpretable archetypes:
    *   **Big Men** (51 players, 18.7%): Valančiūnas, Davis, Gobert, Giannis
    *   **Primary Ball Handlers** (86 players, 31.5%): LeBron, Curry, Durant, Harden  
    *   **Role Players** (136 players, 49.8%): Horford, Lopez, Batum, Holiday
*   **Quality Metrics**: ✅ **VALIDATED** - Silhouette score: 0.235, Cluster balance: 0.375, Basketball interpretability: ✅
*   **Model Persistence**: ✅ **COMPLETED** - All models and results saved for reproducibility

### Lineup Superclusters Generated ✅ (October 3, 2025)

*   **Data Quality Resolution**: ✅ **COMPLETED** - Resolved critical data quality issue where 295 players were missing archetype assignments
*   **Fallback Assignment Strategy**: ✅ **COMPLETED** - Implemented basketball-meaningful fallback assignments for players with <1000 minutes
*   **Data Density Assessment**: ✅ **COMPLETED** - Discovered 17 unique archetype lineups, adjusted clustering approach accordingly
*   **Qualitative Validation Framework**: ✅ **COMPLETED** - Built comprehensive "sniff test" for supercluster validation
*   **Basketball-Meaningful Superclusters**: ✅ **COMPLETED** - Generated two interpretable superclusters:
    *   **Supercluster 0**: "Balanced Lineups" (30% Big Men, 40% Ball Handlers, 30% Role Players)
    *   **Supercluster 1**: "Role Player Heavy" (87% Role Players)
*   **Quality Metrics**: ✅ **VALIDATED** - Silhouette score: 0.381, Basketball interpretability: ✅

### Bayesian Modeling Implementation ✅ (October 3, 2025)

The project has successfully implemented and deployed a production-ready Bayesian possession-level modeling pipeline:

*   **Data Preparation Pipeline**: ✅ **COMPLETED** - Built comprehensive data transformation module that converts possession data into model-ready format with Z matrix calculations
*   **Production Model**: ✅ **DEPLOYED** - Simplified Bayesian model with shared coefficients achieves perfect convergence (R-hat: 1.000, ESS: 2,791) in 85 seconds
*   **Model Architecture**: ✅ **OPTIMIZED** - Simplified model: E[y_i] = β_0 + Σ_a β^off_a * Z^off_ia - Σ_a β^def_a * Z^def_ia
*   **Scalability**: ✅ **VALIDATED** - Model processes 96k possessions efficiently with excellent statistical properties
*   **Coefficient Analysis**: ✅ **COMPLETED** - Generated interpretable coefficients for all 3 player archetypes

### Model Integration ✅ (October 3, 2025)

The project has successfully integrated the production model with comprehensive validation tools:

*   **SimpleModelEvaluator**: ✅ **COMPLETED** - Independent 7-parameter model evaluator using production coefficients
*   **Model Factory**: ✅ **COMPLETED** - Unified interface for both model evaluators with fallback mechanisms
*   **Enhanced Model Dashboard**: ✅ **COMPLETED** - User-friendly interface with model switching and comparison
*   **Performance Optimization**: ✅ **COMPLETED** - Lazy loading, caching, and performance monitoring
*   **Integration Test Suite**: ✅ **COMPLETED** - Comprehensive testing validates both systems work correctly
*   **UI Compatibility**: ✅ **COMPLETED** - Seamless integration with existing analysis tools

### Key Architectural Decision

**Simplified Model Architecture**: The original research paper specified matchup-specific coefficients (36 parameters), but our data only contains 4 unique matchups. This created an impossible parameter-to-data ratio. The solution was a simplified model with shared coefficients across matchups (7 parameters), which is more robust and generalizable.

## Getting Started

### Prerequisites

*   Python 3.8+
*   Git

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/your-repo/nba-lineup-optimizer.git
cd nba-lineup-optimizer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements_streamlit.txt
```

### 2. Verify Database Status

**CRITICAL**: Always run the comprehensive database verification before proceeding with analysis.

```bash
# Run comprehensive database sanity verification
python verify_database_sanity.py
```

**Expected Output**:
```
🎉 ALL CRITICAL VERIFICATIONS PASSED
Database is ready for clustering analysis
```

If verification fails, do not proceed with analysis. The verification script will identify specific data quality issues that must be resolved first.

For a quick status check, you can also run:

```bash
python -c "
import sqlite3
conn = sqlite3.connect('src/nba_stats/db/nba_stats.db')
cursor = conn.cursor()
try:
    cursor.execute('SELECT COUNT(*) FROM Players')
    print(f'Players in database: {cursor.fetchone()[0]}')
    cursor.execute('SELECT COUNT(*) FROM PlayerArchetypeFeatures WHERE season = \"2024-25\"')
    print(f'Players with archetype features: {cursor.fetchone()[0]}')
except sqlite3.OperationalError as e:
    print(f'An error occurred: {e}')
    print('Please ensure the database has been initialized correctly.')
finally:
    conn.close()
"
```
**Expected Output**:
```
Players in database: 5025
Players with archetype features: 273
```

### 3. Launch the Analysis Tools

The project includes multiple user interfaces built with Streamlit.

**Launch the Enhanced Model Dashboard (RECOMMENDED):**
```bash
# Start the enhanced dashboard with model switching
python run_enhanced_dashboard.py
```
This will open the enhanced dashboard at `http://localhost:8502`, featuring:
- **Model Switching**: Easy toggle between original and production models
- **Side-by-Side Comparison**: Compare both models on the same lineup
- **Performance Monitoring**: Real-time metrics and caching statistics
- **User-Friendly Interface**: Sample lineups and intuitive controls

**Launch the Complete Analysis Platform:**
```bash
# Start the main Streamlit dashboard
python run_interrogation_tool.py
```
This will open the main analysis platform at `http://localhost:8501`, where you can explore data, build lineups, and use the player acquisition tool.

**Launch the Model Governance Dashboard:**
```bash
# Start the governance dashboard
python run_governance_dashboard.py
```
This will open the governance dashboard at `http://localhost:8502`, which is used for validating and comparing different versions of the model coefficients.

**Launch the Model Comparison Dashboard:**
```bash
# Start the model comparison dashboard
python run_model_comparison.py
```
This will open the comparison dashboard at `http://localhost:8503`, which provides side-by-side validation between the original and production models.

### 4. Test Model Integration

To validate that both model evaluators work correctly together:
```bash
# Run integration tests
python test_model_integration.py
```
This will test both the original ModelEvaluator and the new SimpleModelEvaluator, ensuring they work correctly together.

### 5. Using the Model Factory in Code

The new model factory provides a unified interface for both model evaluators:

```python
from src.nba_stats.model_factory import ModelFactory, evaluate_lineup

# Evaluate with production model
result = evaluate_lineup([2544, 101108, 201142, 201143, 201144], "simple")
print(f"Predicted outcome: {result.predicted_outcome}")
print(f"Model type: {result.model_type}")

# Evaluate with fallback (automatically falls back to other model if primary fails)
result = ModelFactory.evaluate_lineup_with_fallback(lineup, "simple")

# Get available models
available_models = ModelFactory.get_available_models()
for model in available_models:
    print(f"{model['name']}: {model['description']}")
```

### 6. Run the Complete Demo

To see an overview of all the project's capabilities from the command line, run the interactive demo:
```bash
# Interactive menu for all tools
python demo_implementation.py
```

## Documentation

For a deeper understanding of the project's concepts, architecture, and data, please refer to the documents in the `/docs` directory. The most important ones are:

*   **`docs/project_overview.md`**: A detailed explanation of the core concepts from the source paper.
*   **`docs/architecture.md`**: A deep dive into the system's design principles and key architectural decisions.
*   **`docs/data_dictionary.md`**: The definitive reference for the project's multi-database schema.
*   **`docs/api_debugging_methodology.md`**: An essential guide to debugging the unofficial NBA Stats API using the "Isolate with `curl` First" principle. 