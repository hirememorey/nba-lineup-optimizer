# Quick Start Guide

**Status**: ❌ **WARNING: API FAILURES DETECTED**

This guide provides step-by-step instructions for getting started. Please note that the data pipeline is **not operational** due to failures in the upstream NBA Stats API.

## Prerequisites

- Python 3.8 or higher
- Internet connection
- 2GB free disk space

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd lineupOptimizer
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**:
   ```bash
   python -c "import tqdm, tenacity, pydantic; print('Dependencies installed successfully')"
   ```

## Quick Start (5 minutes)

**⚠️ The following steps will demonstrate the API failure. Do not expect the pipeline to complete successfully.**

### Step 1: Warm the Cache
```bash
python warm_cache.py --season 2024-25
```
**What this does**: Populates local cache with representative NBA data to prevent API issues during development.

**Expected output**:
```
✓ Cache warming completed successfully
✓ 45 requests cached
✓ Cache integrity verified
```

### Step 2: Test API Connectivity
```bash
python test_api_connection.py --season 2024-25
```
**What this does**: Validates that all critical API endpoints are working correctly.

**Expected output**:
```
❌ Smoke test failed - DO NOT PROCEED
```
Review the `api_smoke_test_report.md` for detailed error information.

### Step 3: Verify Data Quality (CRITICAL)
```bash
python verify_semantic_data.py --season 2024-25
```
**What this does**: Validates that the API is returning semantically correct data before running the full pipeline. This prevents the critical failure mode where data looks valid but produces garbage analysis results.

**Expected output**:
```
✅ Semantic verification passed - Data quality validated
```

### Step 4: Run the Pipeline
```bash
python master_data_pipeline.py --season 2024-25
```
**What this does**: This will attempt to run the pipeline and fail due to the API errors.

**Expected output**:
The pipeline will exit with errors. Check `master_pipeline.log` for details.

## Complete Validation (10 minutes)

For maximum confidence, run the complete implementation demo:

```bash
python run_implementation_demo.py
```

This is the recommended first step, as it will run all pre-flight checks and confirm the API failures.

## What You'll See

### Progress Bars
```
Processing games: 100%|██████████| 1230/1230 [45:30<00:00, 2.1s/game]
Fetching metrics: 100%|██████████| 41/41 [12:15<00:00, 1.2s/metric]
```

### Real-time Logging
```
2025-09-30 10:15:30 - INFO - Fetching metric: FTPCT
2025-09-30 10:15:31 - INFO - ✓ Extracted 450 player records for FTPCT
2025-09-30 10:15:32 - INFO - Fetching metric: TSPCT
```

### Generated Reports
- `cache_warming_report.md`: Cache warming results
- `api_smoke_test_report.md`: API test results
- `master_pipeline_report.md`: Pipeline execution results

## Troubleshooting

### If cache warming fails:
```bash
# Clear cache and retry
rm -rf .cache/
python warm_cache.py --season 2024-25
```

### If API tests fail:
```bash
# Check the generated report for details
cat api_smoke_test_report.md

# Check internet connection
ping stats.nba.com

# Run quick test
python test_api_connection.py --season 2024-25 --quick
```

### If semantic verification fails:
```bash
# Check the detailed report
cat semantic_data_verification_report.md

# Run with verbose logging
python verify_semantic_data.py --season 2024-25 --verbose
```

### If pipeline fails:
```bash
# Check logs
tail -f master_pipeline.log

# The pipeline is resumable, but it will continue to fail until the API issues are resolved.
python master_data_pipeline.py --season 2024-25
```

## Next Steps

The next steps are blocked until the API failures identified by the smoke test are resolved.

Once the pipeline completes successfully:

1. **Verify data quality**:
   ```bash
   python data_verification_tool.py
   ```

2. **Handle missing data** (if needed):
   ```bash
   python data_imputation_tool.py --strategy auto
   ```

3. **Run the analysis**:
   ```bash
   # Follow instructions in docs/running_the_analysis.md
   ```

## Key Features

### ✅ **Reliability**
- Cache-first development prevents API issues
- Comprehensive testing before pipeline runs
- Automatic retry logic for failed requests
- **These features are currently protecting the system by preventing execution with a faulty API.**

### ✅ **Observability**
- Real-time progress bars
- Detailed logging
- Comprehensive reporting

### ✅ **Resumability**
- Can restart from any point
- No data loss on interruption
- Atomic database operations

### ✅ **Data Integrity**
- Pydantic validation at every step
- Type checking and range validation
- Clear error messages

## File Structure

```
├── warm_cache.py                    # Cache warming
├── test_api_connection.py          # API testing
├── verify_semantic_data.py         # Data quality validation (NEW)
├── master_data_pipeline.py         # Main pipeline
├── run_implementation_demo.py      # Complete demo
├── .cache/                         # Cached API data
├── *.log                          # Log files
├── *.md                           # Generated reports
└── src/nba_stats/api/
    ├── response_models.py          # Data validation
    ├── data_fetcher.py            # Enhanced fetcher
    └── nba_stats_client.py        # API client
```

## Support

If you encounter issues:

1. **Check the logs**: Look for error messages in `*.log` files
2. **Review reports**: Generated `*.md` files contain detailed information, especially `api_smoke_test_report.md`.
3. **Run validation**: Use `python run_implementation_demo.py` for a complete system check.
4. **Check documentation**: See `docs/implementation_guide.md` for detailed troubleshooting

The system is designed to be robust and self-diagnosing. The current failures are an example of the system working correctly to prevent bad data from entering the pipeline.
