# New NBA Data Pipeline Architecture

## Overview

This document describes the completely redesigned NBA data pipeline, built using first-principles reasoning and incorporating the critical insights from the post-mortem analysis. The new architecture addresses the core challenge of **data mapping** rather than API reliability, implementing a sparsity-aware approach to handle missing data gracefully.

## Key Insights from Post-Mortem

The previous implementation failed because it focused on the wrong problem. The core challenge is not API reliability—it's **column mapping**. The NBA API works fine, but the data exists in different endpoints with different column names than expected.

### Critical Success Factors

1. **Mapping-First Approach**: Understand the data landscape completely before building the system
2. **Sparsity-Aware Design**: Build for missing data from the start, don't try to achieve 100% coverage
3. **Forensic Data Analysis**: Use comprehensive API reconnaissance to discover all available columns
4. **Incremental Validation**: Test and verify each piece before moving to the next

## Architecture Components

### 1. Canonical Metrics Definition (`canonical_metrics.py`)

Defines the 47 archetype metrics required for player clustering, extracted from the source paper.

```python
CANONICAL_48_METRICS = [
    "FTPCT", "TSPCT", "THPAr", "FTr", "TRBPCT", "ASTPCT",
    # ... 41 more metrics
]
```

### 2. API Reconnaissance Tool (`api_reconnaissance.py`)

Performs comprehensive forensics on the NBA Stats API to discover all available columns.

**Key Features:**
- Tests multiple parameter combinations for each endpoint
- Discovers schema variations across different player types
- Generates complete column inventory reports
- Identifies missing metrics upfront

**Usage:**
```bash
python api_reconnaissance.py
```

### 3. Definitive Metric Mapping (`definitive_metric_mapping.py`)

Provides the authoritative mapping between canonical metrics and their actual API sources.

**Key Features:**
- Maps all 47 metrics to their API endpoints and column names
- Identifies which metrics are missing from the API
- Provides data type information for each metric
- Includes validation and completeness checks

**Results:**
- 41 metrics available in API
- 6 metrics missing (shot distance metrics, wingspan)
- Complete mapping documentation

### 4. Centralized Data Fetcher (`src/nba_stats/api/data_fetcher.py`)

Unified interface for fetching NBA player data with built-in error handling and schema awareness.

**Key Features:**
- Single interface for all API endpoints
- Built-in rate limiting and retry logic
- Schema-aware data extraction
- Comprehensive error handling
- Data type validation

**Usage:**
```python
from src.nba_stats.api.data_fetcher import create_data_fetcher

fetcher = create_data_fetcher()
data = fetcher.fetch_all_available_metrics("2024-25")
```

### 5. Master Data Pipeline (`master_data_pipeline.py`)

Orchestrates the entire data pipeline with comprehensive validation and reporting.

**Key Features:**
- Full pipeline execution
- Incremental pipeline for specific metrics
- Comprehensive validation
- Data quality scoring
- Detailed reporting

**Usage:**
```bash
# Full pipeline
python master_data_pipeline.py --season 2024-25

# Incremental pipeline
python master_data_pipeline.py --incremental --metrics FTPCT TSPCT
```

### 6. Data Verification Tool (`data_verification_tool.py`)

Comprehensive verification of data completeness, quality, and logical consistency.

**Key Features:**
- Completeness analysis
- Data quality metrics
- Logical consistency checks
- Sparsity analysis (key insight from post-mortem)
- Anomaly detection

**Usage:**
```bash
python data_verification_tool.py --data-file pipeline_results.json
```

### 7. Data Imputation Tool (`data_imputation_tool.py`)

Handles missing values using various imputation strategies, implementing the sparsity-aware approach.

**Key Features:**
- Multiple imputation strategies (mean, median, KNN, Random Forest)
- Automatic strategy selection based on data characteristics
- Sparsity-aware imputation
- Validation of imputation quality

**Usage:**
```bash
python data_imputation_tool.py --strategy auto
```

## Data Flow

```
1. API Reconnaissance → Discover all available columns
2. Metric Mapping → Map canonical metrics to API sources
3. Data Fetching → Fetch data using centralized fetcher
4. Verification → Validate data quality and completeness
5. Imputation → Handle missing values sparsity-aware
6. Analysis → Ready for archetype clustering
```

## Key Improvements

### 1. Mapping-First Approach
- **Before**: Assumed data structure, built system, then discovered mapping issues
- **After**: Complete API reconnaissance first, then build system around discovered reality

### 2. Sparsity-Aware Design
- **Before**: Tried to achieve 100% data coverage
- **After**: Built for missing data from the start, graceful degradation

### 3. Centralized Architecture
- **Before**: Scattered scripts with fragile per-player API calls
- **After**: Single data fetcher with robust error handling

### 4. Comprehensive Validation
- **Before**: Basic data checks
- **After**: Multi-dimensional validation including sparsity analysis

### 5. Incremental Development
- **Before**: Build everything, then discover it doesn't work
- **After**: Test each piece before moving to the next

## Usage Guide

### Quick Start

1. **Run API Reconnaissance:**
   ```bash
   python api_reconnaissance.py
   ```

2. **Run Full Pipeline:**
   ```bash
   python master_data_pipeline.py
   ```

3. **Verify Data Quality:**
   ```bash
   python data_verification_tool.py
   ```

4. **Handle Missing Data:**
   ```bash
   python data_imputation_tool.py --strategy auto
   ```

### Advanced Usage

1. **Incremental Pipeline:**
   ```bash
   python master_data_pipeline.py --incremental --metrics FTPCT TSPCT ASTPCT
   ```

2. **Custom Imputation:**
   ```bash
   python data_imputation_tool.py --strategy knn --data-file custom_data.json
   ```

3. **Specific Verification:**
   ```bash
   python data_verification_tool.py --data-file imputed_data.json
   ```

## File Structure

```
├── canonical_metrics.py              # 47 canonical archetype metrics
├── metric_to_script_mapping.py      # Maps metrics to population scripts
├── api_reconnaissance.py            # API forensics tool
├── definitive_metric_mapping.py     # Authoritative metric mapping
├── master_data_pipeline.py          # Main orchestration script
├── data_verification_tool.py        # Data quality verification
├── data_imputation_tool.py          # Missing data imputation
├── src/nba_stats/api/
│   └── data_fetcher.py              # Centralized data fetcher
└── reports/                         # Generated reports
    ├── api_column_inventory_report.md
    ├── definitive_metric_mapping_report.md
    ├── master_pipeline_report.md
    ├── data_verification_report.md
    └── imputation_report.md
```

## Data Quality Metrics

The new architecture provides comprehensive data quality metrics:

- **Completeness Score**: Percentage of metrics successfully fetched
- **Quality Score**: Average data completeness across all metrics
- **Consistency Score**: Percentage of metrics passing logical consistency checks
- **Sparsity Score**: Quality of data coverage accounting for missing values
- **Overall Health Score**: Weighted combination of all quality metrics

## Missing Metrics

The following 6 metrics are not available in the current NBA API and require alternative approaches:

1. `AVGDIST` - Average Shot Distance
2. `Zto3r` - Zone to 3-Point Range
3. `THto10r` - Three to Ten Range
4. `TENto16r` - Ten to Sixteen Range
5. `SIXTto3PTr` - Sixteen to 3-Point Range
6. `WINGSPAN` - Player Wingspan

**Recommendations:**
- Shot distance metrics: May be available in shot chart data or need calculation
- Wingspan: May be available in draft combine data

## Next Steps

1. **Investigate Missing Metrics**: Research alternative data sources for the 6 missing metrics
2. **Refactor Existing Scripts**: Update population scripts to use the new data fetcher
3. **Implement Archetype Clustering**: Use the cleaned data for player archetype analysis
4. **Add Monitoring**: Implement data quality monitoring and alerting
5. **Optimize Performance**: Add caching and parallel processing for large datasets

## Lessons Learned

1. **Start with data forensics, not code architecture**
2. **Embrace the mapping problem as the core challenge**
3. **Build incrementally with verification at each step**
4. **Use sparsity-aware approaches from the start**
5. **Focus on the most important metrics first**

This new architecture provides a solid foundation for reliable NBA player data analysis, addressing the core challenges identified in the post-mortem while maintaining the flexibility to handle the inherent sparsity of sports data.
