# Developer Onboarding Guide

**Date**: October 3, 2025  
**Status**: Analysis Phase Complete

## 🎯 Quick Start for New Developers

This guide will help you get up and running with the NBA Lineup Optimizer project quickly and understand the current state of the system.

## 📋 Prerequisites

- Python 3.8+
- Git
- Basic understanding of basketball analytics
- Familiarity with Streamlit (for UI development)

## 🚀 Getting Started

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

### 2. Verify System Status

```bash
# Check if database exists and has data
python -c "
import sqlite3
conn = sqlite3.connect('src/nba_stats/db/nba_stats.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM Players')
print(f'Players in database: {cursor.fetchone()[0]}')
cursor.execute('SELECT COUNT(*) FROM PlayerSeasonArchetypes WHERE season = \"2024-25\"')
print(f'Players with archetypes: {cursor.fetchone()[0]}')
conn.close()
"
```

**Expected Output**:
```
Players in database: 5025
Players with archetypes: 270
```

### 3. Launch the Interactive Tool

```bash
# Start the Streamlit dashboard
python run_interrogation_tool.py
```

This will open the interactive tool at `http://localhost:8501`

### 4. Run the Demo

```bash
# See all capabilities programmatically
python demo_interrogation.py
```

## 🏗️ Project Architecture

### Current State

The project is in the **Analysis Phase** - we have successfully built:
- ✅ **Data Pipeline**: Complete with 270 players and 574,357 possessions
- ✅ **Model Training**: Placeholder implementation with exported coefficients
- ✅ **Interactive Tools**: Streamlit dashboard for real-time analysis
- ✅ **Explainable AI**: Skill vs Fit decomposition for lineup recommendations

### Key Files

```
├── model_interrogation_tool.py      # Main Streamlit dashboard
├── train_bayesian_model.py          # Model training pipeline
├── run_interrogation_tool.py        # Tool launcher
├── demo_interrogation.py            # Programmatic demo
├── model_coefficients.csv           # Trained model coefficients
├── supercluster_coefficients.csv    # Supercluster coefficients
├── src/nba_stats/db/nba_stats.db    # Main database
└── docs/                            # Documentation
```

### Database Schema

The main database (`src/nba_stats/db/nba_stats.db`) contains:

- **Players**: Player information and metadata
- **PlayerSeasonArchetypes**: Archetype assignments for 2024-25
- **PlayerSeasonSkill**: DARKO skill ratings for 2024-25
- **Possessions**: Play-by-play data with complete lineups
- **Archetypes**: Archetype definitions and names

## 🔍 Understanding the System

### Core Concepts

1. **Player Archetypes**: 8 distinct playstyles (e.g., "3&D", "Offensive Juggernauts")
2. **Lineup Superclusters**: 6 tactical styles for 5-player lineups
3. **Skill vs Fit**: Players contribute through both individual skill and team fit
4. **Possession-Level Modeling**: Bayesian model predicts possession outcomes

### Key Classes

#### `ModelInterrogator`
The main class for programmatic analysis:

```python
from model_interrogation_tool import ModelInterrogator

# Initialize and load data
interrogator = ModelInterrogator()
interrogator.connect_database()
interrogator.load_player_data()
interrogator.load_model_coefficients()

# Search for a player
player = interrogator.get_player_by_name("LeBron James")

# Analyze a lineup
lineup_ids = [player1_id, player2_id, player3_id, player4_id, player5_id]
result = interrogator.calculate_lineup_value(lineup_ids)
```

## 🛠️ Development Workflow

### Making Changes

1. **Test Changes**: Always test with the interactive tool
2. **Validate Logic**: Run the basketball logic tests
3. **Update Documentation**: Keep docs in sync with code changes

### Adding New Features

1. **Interactive Tool**: Add new analysis modes to `model_interrogation_tool.py`
2. **Programmatic Interface**: Extend the `ModelInterrogator` class
3. **Model Training**: Update `train_bayesian_model.py` for new features

### Testing

```bash
# Test the interactive tool
python run_interrogation_tool.py

# Test programmatic interface
python demo_interrogation.py

# Test model training
python train_bayesian_model.py
```

## 📊 Current Data Status

- **270 players** with complete archetype and skill data for 2024-25 season
- **574,357 possessions** with complete 10-player lineup information
- **8 player archetypes** and **6 lineup superclusters**
- **Trained model coefficients** ready for lineup value calculations

## 🎯 Key Capabilities

### Interactive Analysis

The Streamlit dashboard provides 5 analysis modes:

1. **Data Overview**: Visualize dataset statistics and distributions
2. **Player Explorer**: Search and analyze individual players
3. **Archetype Analysis**: Deep dive into specific player archetypes
4. **Lineup Builder**: Build and analyze 5-player lineups
5. **Model Validation**: Test the model's basketball logic

### Programmatic Analysis

The `ModelInterrogator` class provides:

- **Player Search**: Find players by name with fuzzy matching
- **Lineup Analysis**: Calculate lineup values programmatically
- **Archetype Exploration**: Analyze specific player archetypes
- **Data Access**: Direct access to all analysis capabilities

## 🚨 Important Notes

### Model Status
- **Current Implementation**: Placeholder coefficients for demonstration
- **Real Training**: Requires 18-hour MCMC process with Stan/PyMC
- **Validation**: All basketball logic tests pass with placeholder data

### Data Limitations
- **Season**: 2024-25 data (different from paper's 2022-23)
- **Coverage**: 270 players with complete data (50.6% of skill players)
- **Validation**: Cannot directly replicate paper's specific examples

### Architecture
- **Interrogation-First**: Built for exploration, not presentation
- **Real-time Analysis**: All calculations happen on-demand
- **Extensible**: Easy to add new analysis modes and validation tests

## 🔧 Troubleshooting

### Common Issues

1. **Database Not Found**: Run the data pipeline first
2. **Model Coefficients Missing**: Run `python train_bayesian_model.py`
3. **Streamlit Not Starting**: Check if port 8501 is available

### Debug Commands

```bash
# Check database status
python -c "import sqlite3; conn = sqlite3.connect('src/nba_stats/db/nba_stats.db'); print('Database OK')"

# Check model coefficients
python -c "import pandas as pd; print(pd.read_csv('model_coefficients.csv').head())"

# Test data loading
python -c "from model_interrogation_tool import ModelInterrogator; i = ModelInterrogator(); i.connect_database(); print('Data loading OK')"
```

## 📚 Next Steps

### For New Developers

1. **Explore the System**: Use the interactive tool to understand capabilities
2. **Read the Code**: Start with `model_interrogation_tool.py` and `demo_interrogation.py`
3. **Test Scenarios**: Build lineups and validate model logic
4. **Ask Questions**: Use the interrogation tool to explore "why" questions

### For Experienced Developers

1. **Implement Real Bayesian Training**: Replace placeholder with Stan/PyMC
2. **Add New Analysis Modes**: Extend the interactive tool
3. **Build Player Acquisition Tool**: Create the final recommendation engine
4. **Add Production Features**: User management, result persistence, scalability

## 📖 Additional Resources

- **README.md**: Project overview and quick start
- **CURRENT_STATUS.md**: Detailed current status
- **ANALYSIS_PHASE_STATUS.md**: Analysis phase implementation details
- **IMPLEMENTATION_SUMMARY.md**: Complete implementation summary
- **NEXT_PHASE_README.md**: Next phase planning

## 🤝 Contributing

1. **Fork the Repository**: Create your own fork
2. **Create a Branch**: Use descriptive branch names
3. **Make Changes**: Follow the development workflow
4. **Test Thoroughly**: Ensure all tests pass
5. **Submit PR**: Include clear description of changes

## 📞 Support

For questions or issues:
1. Check the troubleshooting section above
2. Review the documentation in the `docs/` directory
3. Run the demo scripts to understand expected behavior
4. Create an issue with detailed error information

---

**Welcome to the NBA Lineup Optimizer project! The system is ready for exploration and development.**
