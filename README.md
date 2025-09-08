# NBA Lineup Optimizer

This project implements the methodology from the research paper "Algorithmic NBA Player Acquisition" by Brill, Hughes, and Waldbaum, adapting it to analyze the 2024-25 NBA season. The goal is to create a data-driven approach to NBA player acquisition and lineup optimization using modern statistical methods.

## Project Overview

The project uses a combination of NBA statistics, player tracking data, and advanced metrics (DARKO) to:
1. Generate player archetypes through clustering
2. Create lineup superclusters
3. Build a Bayesian regression model for possession-level analysis
4. Optimize player acquisition decisions

## Current Status

### Completed
- ✅ **Database Migration**: The schema for `PlayerSalaries` and `PlayerSkills` has been updated to be season-aware.
- ✅ **Core Data Population**: Scripts for populating salaries and DARKO skill ratings from local CSVs for the 2024-25 season have been updated and successfully run.
- ✅ **Initial Analysis Pipeline**: Phase 1 and Phase 2 scripts (`run_phase_1.py`, `run_phase_2.py`) run successfully, generating initial archetype data.

### In Progress
- 🚧 **Possession-Level Data Collection (Blocked)**: The `populate_possessions.py` script is the current focus. It is failing due to breaking changes in the `nba_api` library's data structures. This is the primary blocker for the project. See `docs/next_steps.md` for a detailed debugging plan.

### Pending
- ⏳ **Bayesian Regression Model Implementation** (Section 2.2)
- ⏳ **Player Acquisition Analysis** (Section 3)

## Project Structure

```
src/nba_stats/
├── api/                 # NBA API integration
├── config/             # Configuration files
├── db/                 # Database management
├── models/             # Data models
├── scripts/            # Data processing scripts
└── utils/             # Utility functions
```

## Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/hirememorey/nba-lineup-optimizer.git
cd nba-lineup-optimizer
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python src/nba_stats/scripts/create_tables.py
```

5. Run Phase 1 data population:
```bash
python src/nba_stats/scripts/run_phase_1.py
```

6. Run Phase 2 feature engineering:
```bash
python src/nba_stats/scripts/run_phase_2.py
```

## Data Sources

- NBA Stats API: Player and team statistics
- DARKO DPM: Player offensive and defensive skill ratings
- Play-by-play data: Possession-level analysis

## Database

The project uses SQLite for data storage. The database file (`nba_stats.db`) is excluded from version control due to its size. You'll need to generate it locally using the setup instructions above.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Research paper: "Algorithmic NBA Player Acquisition" by Brill, Hughes, and Waldbaum
- NBA Stats API for data access
- DARKO DPM for player skill ratings 