# NBA Lineup Optimizer

This project implements the methodology from the research paper "Algorithmic NBA Player Acquisition" by Brill, Hughes, and Waldbaum. It uses a data-driven approach to NBA player acquisition and lineup optimization, prioritizing team **fit** over individual skill alone.

The project has recently undergone a complete architectural redesign based on first-principles reasoning and is now in the final stages of implementation.

## Current Status

**Date**: October 3, 2025
**Status**: ⚠️ **Operational with Critical Data Gaps**

The project's core infrastructure and analysis tools are fully implemented and functional. However, a comprehensive data audit has revealed critical gaps in advanced player tracking statistics, which impacts the accuracy of player archetypes and, consequently, the lineup recommendations.

### What's Working ✅

*   **Complete Tooling Suite**:
    *   **Model Governance Dashboard**: For structured human validation of model coefficients.
    *   **Player Acquisition Tool**: To find the best 5th player for a 4-player core.
    *   **Interactive Analysis Platform**: A Streamlit UI with 6 analysis modes for deep exploration.
*   **Robust Data Pipeline**: A reliable and resumable data pipeline is in place.
*   **ModelEvaluator Foundation**: A "bulletproof" core library provides a single source of truth for all analysis.
*   **Core Data Populated**: Possession data (574k+), basic shot data, and physical measurements are fully populated.

### What's Not Working ❌

*   **Missing Advanced Tracking Stats**: The final `PlayerArchetypeFeatures` table, which is used for clustering, is missing several categories of advanced tracking data. The data pipeline is failing to populate them, and this was not caught earlier due to flawed verification processes.
    *   **Drive Statistics**: 0% coverage
    *   **Post-up Play**: 0% coverage
    *   **Pull-up Shooting**: 0% coverage
    *   **Paint Touches**: 0% coverage
*   **Impact**: Without this data, player archetypes for certain playstyles (drive-heavy guards, post-up bigs) are likely inaccurate, which reduces the reliability of the model's recommendations.

### Next Steps

The immediate priority is to **debug and fix the data pipeline** to ensure all 48 canonical metrics are correctly populated in the `PlayerArchetypeFeatures` table. Once the data is complete, the player archetypes must be re-generated and the Bayesian model retrained.

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

Check that the core database exists and contains the foundational data.

```bash
python -c "
import sqlite3
conn = sqlite3.connect('src/nba_stats/db/nba_stats.db')
cursor = conn.cursor()
try:
    cursor.execute('SELECT COUNT(*) FROM Players')
    print(f'Players in database: {cursor.fetchone()[0]}')
    cursor.execute('SELECT COUNT(*) FROM PlayerSeasonArchetypes WHERE season = \"2024-25\"')
    print(f'Players with archetypes: {cursor.fetchone()[0]}')
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
Players with archetypes: 270
```

### 3. Launch the Analysis Tools

The project includes two primary user interfaces built with Streamlit.

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

### 4. Run the Complete Demo

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