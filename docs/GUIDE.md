# NBA Lineup Optimizer: The Complete Guide

This guide provides all the necessary instructions for setting up, running, and deploying the NBA Lineup Optimizer, whether you are a fan, a developer, or an administrator.

---

## 1. For the Fan: Running the Fan-Friendly Dashboard

This version of the tool translates complex analytics into intuitive basketball language.

### Quick Start

1.  **Run the Dashboard**:
    ```bash
    # Start the fan-friendly dashboard from your terminal
    python run_fan_dashboard.py
    ```

2.  **Open in Your Browser**:
    Navigate to `http://localhost:8501`.

### Features
-   **Team Selection**: Choose from all 30 NBA teams to see their current roster and needs.
-   **Player Search**: Find any player by name and get an instant analysis of how they would fit on a selected team.
-   **Basketball Language**: Explanations are in terms of positions (PG, SG) and roles (Playmaker, 3&D Wing), not statistical jargon.
-   **Free Agent Recommendations**: Get a list of available players who would best address your team's needs.

---

## 2. For the Developer: Local Setup

This section is for developers who need to run the full application in a local development environment.

### Prerequisites

*   Python 3.9+
*   Git

### Setup Instructions

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/your-repo/nba-lineup-optimizer.git
    cd nba-lineup-optimizer
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    pip install -r requirements_streamlit.txt
    ```

3.  **Ensure Data is in Place**:
    The core database is included in the repository, but some scripts depend on generated files. Before running any analysis, ensure the main data pipeline has been run at least once.
    ```bash
    # Verify the database is healthy and contains the necessary tables
    python verify_database_sanity.py
    # Expected output: "🎉 ALL CRITICAL VERIFICATIONS PASSED"
    ```

4.  **Run in Development Mode**:
    To run the full production dashboard locally with authentication disabled for easier testing:
    ```bash
    export ENVIRONMENT=development
    export ENABLE_AUTH=false
    
    # Run the production dashboard application
    python production_dashboard.py
    ```
    The application will be available at `http://localhost:8502`.

---

## 3. For the Administrator: Production Deployment

This section covers deploying the application to a production environment with all features, including authentication and monitoring, enabled.

### Option A: Docker Deployment (Recommended)

This is the simplest and most reliable way to deploy the entire system.

1.  **Setup**: Ensure Docker and Docker Compose are installed on your server.
2.  **Deploy**:
    ```bash
    # From the project root, build and start all services in the background
    docker-compose up -d
    ```
3.  **Monitor**:
    ```bash
    # View the logs from all running containers
    docker-compose logs -f
    ```
4.  **Access**: The application will be available at `http://localhost:8502` (or your server's public IP).

### Option B: Direct Python Deployment

This method is for environments where Docker is not available.

1.  **Setup**: Ensure all prerequisites from the developer setup are met.
2.  **Configure Environment**: Create a `.env` file for your production settings. A `env.example` is provided as a template.
    ```bash
    # Set production environment variables
    export ENVIRONMENT=production
    export ENABLE_AUTH=true
    export SECRET_KEY='your-super-secret-key-here'
    export ADMIN_PASSWORD='your-secure-admin-password'
    export USER_PASSWORD='your-secure-user-password'
    ```
3.  **Run the Application**:
    ```bash
    # This script will start the Streamlit application with production settings
    python run_production.py
    ```

### Default Credentials

When authentication is enabled, the default credentials are:
-   **Admin**: `admin` / `admin123`
-   **User**: `user` / `user123`

⚠️ **It is critical to change these passwords in a production environment via environment variables.**

---

## 4. For the Developer: Validation and Testing

This section covers validating the model and running tests to ensure the system works correctly.

### Ground Truth Validation

Before making changes or running analysis, validate that the core basketball principles are working correctly:

```bash
# Run comprehensive ground truth validation
python3 ground_truth_validation.py
```

**Expected Output**:
- ✅ Westbrook Cases (PASS): Lakers improve without Westbrook
- ✅ Skill Balance (PASS): Balanced lineups outperform imbalanced
- ❌ Archetype Diversity (FAIL): Redundancy penalty needs refinement

### Multi-Season Model Validation

The system now includes a trained multi-season Bayesian model. Test the model's predictive capabilities:

```bash
# Phase 3: Generate 2022-23 validation Z-matrix
python3 generate_2022_23_validation.py

# Phase 3: Test multi-season model predictions
python3 validate_multi_season_model.py --season 2022-23 --cases lakers pacers suns

# Phase 3: Russell Westbrook case study validation
python3 validate_westbrook_case.py
```

**Current Model Status** (Phase 2 Complete):
- ✅ **103,047 training possessions** across 2018-19, 2020-21, 2021-22
- ✅ **All 8 archetypes** validated with non-zero aggregations
- ✅ **36 unique matchups** operational (6×6 supercluster system)
- ✅ **Model convergence**: R-hat < 1.01, 0 divergent transitions
- ⚠️ **Simplified model**: Archetype × skill effects (no matchup-specific parameters)

**Phase 3 Validation Targets**:
- **Lakers**: Test prediction of Westbrook redundancy issues
- **Pacers**: Validate defensive archetype recommendations
- **Suns**: Assess offensive juggernaut balance recommendations

### Testing Individual Components

```bash
# Test the custom 2022-23 evaluator directly
python3 simple_2022_23_evaluator.py

# Run the full test suite
python3 -m pytest

# Run specific test categories
python3 -m pytest tests/ -k "validation"  # Validation tests only
python3 -m pytest tests/ -k "pipeline"    # Pipeline tests only
```

### Troubleshooting Validation Issues

1. **Database Not Found**:
   ```bash
   # Ensure database exists
   ls -la src/nba_stats/db/nba_stats.db
   ```

2. **Missing Players**:
   ```bash
   # Check if 2022-23 data is loaded
   python3 -c "
   import sqlite3
   conn = sqlite3.connect('src/nba_stats/db/nba_stats.db')
   cursor = conn.cursor()
   cursor.execute('SELECT COUNT(*) FROM PlayerArchetypeFeatures_2022_23')
   print(f'2022-23 players: {cursor.fetchone()[0]}')
   conn.close()
   "
   ```

3. **Import Errors**:
   ```bash
   # Ensure you're in the project root directory
   pwd
   # Should show: /path/to/lineupOptimizer
   ```

### Success Criteria

**Phase 2 (Multi-Season Model) - ✅ COMPLETED:**
- ✅ Multi-season Bayesian model trained with R-hat < 1.01 convergence
- ✅ All 8 archetypes validated with non-zero aggregations
- ✅ 36 unique matchups operational (6×6 supercluster system)
- ✅ 103,047 training possessions processed successfully
- ✅ Archetype index bug resolved (1-8 IDs → 0-7 indices)

**Phase 3 (Predictive Validation) - In Progress:**
- [ ] 2022-23 validation Z-matrix generated successfully
- [ ] Model predictions evaluated against holdout outcomes
- [ ] Russell Westbrook-Lakers case study validated
- [ ] Predictive performance documented and assessed

The system is properly validated when:
- ✅ Multi-season model predicts 2022-23 outcomes with reasonable accuracy
- ✅ Westbrook redundancy case identified correctly
- ✅ Model generalizes across different seasons
- ✅ All archetype effects have basketball-intelligent interpretations

