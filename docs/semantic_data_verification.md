# Semantic Data Verification Guide

**Status**: ✅ **CRITICAL TOOL - ALWAYS RUN BEFORE PIPELINE**

This document explains the semantic data verification tool (`verify_semantic_data.py`) that validates data quality before running the full data pipeline. This tool addresses the critical failure mode identified in our pre-mortem analysis.

## Why Semantic Verification is Critical

The pre-mortem analysis revealed a critical failure mode: **"The data looks valid but is semantically wrong, leading to garbage analysis results."**

This happens when:
- API responses have valid JSON structure but contain incorrect data
- Data fields are present but contain nonsensical values
- Response format changes subtly, breaking downstream analysis
- Data appears complete but lacks semantic meaning

## What the Tool Validates

### 1. Data Completeness
- Ensures all critical fields are present
- Validates that required data is not missing
- Checks for empty or null values in key fields

### 2. Data Consistency
- Validates that values make sense for basketball
- Checks for reasonable ranges (e.g., shooting percentages 0-100%)
- Ensures data relationships are logical

### 3. Data Freshness
- Verifies that recent data is available
- Checks that the season data is current
- Validates data timestamps

### 4. Data Structure
- Ensures response format matches expectations
- Validates that API responses have expected structure
- Checks for proper data types

## Usage

### Basic Usage
```bash
python verify_semantic_data.py --season 2024-25
```

### Verbose Output
```bash
python verify_semantic_data.py --season 2024-25 --verbose
```

### Help
```bash
python verify_semantic_data.py --help
```

## Output

The tool generates two outputs:

### 1. Console Output
```
2025-09-30 14:46:27 - INFO - Starting semantic data verification for season: 2024-25
2025-09-30 14:46:27 - INFO - Check 1: API Response Structure
2025-09-30 14:46:28 - INFO - ✓ Team API response structure: PASSED
2025-09-30 14:46:29 - INFO - ✓ Player API response structure: PASSED
2025-09-30 14:46:29 - INFO - Check 2: Data Completeness
2025-09-30 14:46:30 - INFO - ✓ Player data completeness: PASSED
2025-09-30 14:46:30 - INFO - Check 3: Data Consistency
2025-09-30 14:46:31 - INFO - ✓ Player stats consistency: PASSED
2025-09-30 14:46:31 - INFO - Check 4: Data Freshness
2025-09-30 14:46:32 - INFO - ✓ Data freshness: PASSED
2025-09-30 14:46:32 - INFO - 
2025-09-30 14:46:32 - INFO - ========================================
2025-09-30 14:46:32 - INFO - SEMANTIC VERIFICATION COMPLETE
2025-09-30 14:46:32 - INFO - ========================================
2025-09-30 14:46:32 - INFO - Total checks: 4
2025-09-30 14:46:32 - INFO - Passed: 4
2025-09-30 14:46:32 - INFO - Failed: 0
2025-09-30 14:46:32 - INFO - Success rate: 100.0%
2025-09-30 14:46:32 - INFO - Duration: 5.23 seconds
2025-09-30 14:46:32 - INFO - 
2025-09-30 14:46:32 - INFO - ✅ SEMANTIC VERIFICATION PASSED
2025-09-30 14:46:32 - INFO - Data quality validated - Safe to proceed with pipeline
```

### 2. Detailed Report
The tool generates `semantic_data_verification_report.md` with comprehensive details about each validation check.

## Validation Checks

### Check 1: API Response Structure
- **Team API**: Validates that team data is returned in expected format
- **Player API**: Validates that player data is returned in expected format
- **Critical**: Must pass for pipeline to work

### Check 2: Data Completeness
- **Player Coverage**: Ensures sufficient number of players are returned
- **Required Fields**: Validates that critical fields are present
- **Data Volume**: Checks that data volume is reasonable

### Check 3: Data Consistency
- **Value Ranges**: Validates that statistical values are within reasonable ranges
- **Data Types**: Ensures data types match expectations
- **Logical Consistency**: Checks that data relationships make sense

### Check 4: Data Freshness
- **Season Data**: Validates that current season data is available
- **Recent Updates**: Checks that data appears to be recent
- **Data Timestamps**: Validates data freshness indicators

## Integration with Pipeline

The semantic verification tool is designed to be run before the main data pipeline:

```bash
# Step 1: Verify data quality
python verify_semantic_data.py --season 2024-25

# Step 2: Run pipeline (only if verification passes)
python master_data_pipeline.py --season 2024-25
```

## Error Handling

### If Verification Fails
1. **Check the detailed report**: `cat semantic_data_verification_report.md`
2. **Run with verbose output**: `python verify_semantic_data.py --season 2024-25 --verbose`
3. **Check API connectivity**: `python test_api_connection.py --season 2024-25`
4. **Review logs**: Check `semantic_data_verification.log`

### Common Issues
- **API Rate Limiting**: Wait and retry
- **Network Issues**: Check internet connection
- **Data Format Changes**: May require API client updates
- **Season Data Unavailable**: Verify season parameter

## Configuration

The tool uses the same configuration as the main pipeline:
- Season parameter: `--season 2024-25`
- Verbose output: `--verbose`
- Help: `--help`

## Best Practices

1. **Always run before pipeline**: Never skip semantic verification
2. **Check reports**: Review generated reports for detailed insights
3. **Monitor logs**: Watch for warning messages
4. **Validate regularly**: Run verification periodically during development
5. **Fix issues immediately**: Address any failures before proceeding

## Technical Details

### Dependencies
- `src.nba_stats.api.nba_stats_client`: NBA API client
- `logging`: Logging functionality
- `json`: JSON handling
- `time`: Timing functionality
- `typing`: Type hints

### File Outputs
- `semantic_data_verification_report.md`: Detailed validation report
- `semantic_data_verification.log`: Log file with detailed output

### Performance
- Typical runtime: 5-10 seconds
- API calls: 4-6 requests
- Memory usage: Minimal
- Network usage: Low

## Troubleshooting

### Tool Won't Start
```bash
# Check Python environment
python --version

# Check dependencies
pip list | grep -E "(requests|pydantic)"

# Check API client
python -c "from src.nba_stats.api.nba_stats_client import NBAStatsClient; print('OK')"
```

### Verification Fails
```bash
# Check API connectivity
curl -I https://stats.nba.com

# Test individual components
python -c "from src.nba_stats.api.nba_stats_client import NBAStatsClient; client = NBAStatsClient(); print(client.get_all_teams())"
```

### False Positives
- Review validation criteria
- Check for edge cases
- Update validation logic if needed

## Future Enhancements

- **Machine Learning Validation**: Use ML models to detect anomalous data patterns
- **Historical Comparison**: Compare current data with historical baselines
- **Cross-Validation**: Validate data against multiple sources
- **Automated Alerts**: Set up alerts for data quality issues
- **Dashboard Integration**: Create real-time data quality dashboard
