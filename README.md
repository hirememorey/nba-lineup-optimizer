# NBA Lineup Optimizer

This project implements the methodology from the research paper "Algorithmic NBA Player Acquisition" by Brill, Hughes, and Waldbaum, adapting it to analyze the 2024-25 NBA season. The goal is to create a data-driven approach to NBA player acquisition and lineup optimization using modern statistical methods.

## 🚀 New Architecture (September 2025)

**BREAKING CHANGE**: The project has been completely redesigned using first-principles reasoning and insights from comprehensive post-mortem analysis. The new architecture addresses the core challenge of **data mapping** rather than API reliability, implementing a sparsity-aware approach to handle missing data gracefully.

### Key Improvements
- **Mapping-First Approach**: Complete API reconnaissance before building the system
- **Sparsity-Aware Design**: Built for missing data from the start, not 100% coverage
- **Centralized Data Fetcher**: Single interface for all API endpoints with robust error handling
- **Comprehensive Validation**: Multi-dimensional data quality scoring and verification
- **Advanced Imputation**: ML-based missing data handling (KNN, Random Forest, etc.)

### Quick Start with New Architecture

1. **Run API Reconnaissance** (discovers all available data):
   ```bash
   python api_reconnaissance.py
   ```

2. **Run Full Data Pipeline**:
   ```bash
   python master_data_pipeline.py --season 2024-25
   ```

3. **Verify Data Quality**:
   ```bash
   python data_verification_tool.py
   ```

4. **Handle Missing Data**:
   ```bash
   python data_imputation_tool.py --strategy auto
   ```

See `NEW_ARCHITECTURE_README.md` for complete documentation of the new system.

## Project Overview

The project uses a combination of NBA statistics, player tracking data, and advanced metrics (DARKO) to:
1. Generate player archetypes through clustering
2. Create lineup superclusters
3. Build a Bayesian regression model for possession-level analysis
4. Optimize player acquisition decisions

## Current Status

### ✅ New Architecture Completed
- **47 Canonical Metrics**: Extracted and mapped from source paper
- **API Reconnaissance**: Discovered 240 unique columns across 5 endpoints
- **Definitive Mapping**: 41 metrics available in API, 6 missing (shot distance, wingspan)
- **Centralized Data Fetcher**: Unified interface with schema awareness
- **Master Pipeline**: Comprehensive orchestration with validation
- **Data Verification**: Multi-dimensional quality analysis
- **Imputation System**: Advanced ML-based missing data handling

### 📊 Data Quality Status
- **Available Metrics**: 41/47 (87.2%)
- **Missing Metrics**: 6 (shot distance metrics, wingspan)
- **Data Quality Score**: Calculated via comprehensive validation
- **Sparsity-Aware**: Built to handle missing data gracefully

### 🎯 Ready for Analysis
- **Clean Data Pipeline**: Robust fetching with comprehensive validation
- **Missing Data Handling**: Advanced imputation strategies available
- **Quality Monitoring**: Multi-dimensional scoring and reporting
- **Incremental Development**: Test individual components before full pipeline

## Project Structure

### New Architecture Files
```
├── canonical_metrics.py              # 47 canonical archetype metrics
├── metric_to_script_mapping.py      # Maps metrics to population scripts
├── api_reconnaissance.py            # API forensics tool
├── definitive_metric_mapping.py     # Authoritative metric mapping
├── master_data_pipeline.py          # Main orchestration script
├── data_verification_tool.py        # Data quality verification
├── data_imputation_tool.py          # Missing data imputation
├── NEW_ARCHITECTURE_README.md       # Complete new architecture docs
└── reports/                         # Generated reports
    ├── api_column_inventory_report.md
    ├── definitive_metric_mapping_report.md
    ├── master_pipeline_report.md
    ├── data_verification_report.md
    └── imputation_report.md
```

### Legacy Structure
```
src/nba_stats/
├── api/                 # NBA API integration (legacy + new data_fetcher.py)
├── config/             # Configuration files
├── db/                 # Database management
├── models/             # Data models
├── scripts/            # Data processing scripts (legacy)
└── utils/             # Utility functions
```

## Setup Instructions

### New Architecture (Recommended)

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

4. Run API reconnaissance (discovers all available data):
```bash
python api_reconnaissance.py
```

5. Run the master data pipeline:
```bash
python master_data_pipeline.py --season 2024-25
```

6. Verify data quality:
```bash
python data_verification_tool.py
```

7. Handle missing data (if needed):
```bash
python data_imputation_tool.py --strategy auto
```

### Legacy Setup (Deprecated)

The legacy setup is still available but not recommended due to data quality issues:

1-3. Same as above

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