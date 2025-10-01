# NBA API Smoke Test Report
Generated on: 2025-10-01 12:13:52
Season: 2024-25
Duration: 62.68 seconds

## Summary
- Total tests: 25
- Passed: 17
- Failed: 8
- Success rate: 68.0%

## Critical Failures
These failures will prevent the data pipeline from running successfully:
- Basic team request: Invalid response format
- Basic player request: Invalid response format
- League player stats (Base): Invalid response format
- Fetch metric: FTPCT: No data returned
- Fetch metric: FTr: No data returned

## Warnings
These issues may cause problems but won't prevent the pipeline from running:
- League shot locations: Exception - RetryError[<Future at 0x104b35a70 state=finished raised EmptyResponseError>]
- Rapid requests success rate: Value 0.0 below minimum 80.0
- Invalid player ID handling: Exception - RetryError[<Future at 0x1075b8150 state=finished raised EmptyResponseError>]

## Detailed Test Results
### Basic team request
- Status: ✗ FAIL (CRITICAL)
- Duration: 0.00s
- Error: Invalid response format

### Basic player request
- Status: ✗ FAIL (CRITICAL)
- Duration: 0.01s
- Error: Invalid response format

### League player stats (Base)
- Status: ✗ FAIL (CRITICAL)
- Duration: 0.01s
- Error: Invalid response format

### League player stats (Advanced)
- Status: ✓ PASS (CRITICAL)
- Duration: 0.00s

### League hustle stats
- Status: ✓ PASS
- Duration: 0.00s

### League shot locations
- Status: ✗ FAIL
- Duration: 27.88s
- Error: Exception: RetryError[<Future at 0x104b35a70 state=finished raised EmptyResponseError>]

### League tracking stats (Drives)
- Status: ✓ PASS
- Duration: 0.00s

### LeBron James basic stats
- Status: ✓ PASS (CRITICAL)
- Duration: 0.00s

### LeBron James advanced stats
- Status: ✓ PASS (CRITICAL)
- Duration: 0.00s

### LeBron James player info
- Status: ✓ PASS
- Duration: 0.00s

### James Harden basic stats
- Status: ✓ PASS (CRITICAL)
- Duration: 0.00s

### James Harden advanced stats
- Status: ✓ PASS (CRITICAL)
- Duration: 0.00s

### James Harden player info
- Status: ✓ PASS
- Duration: 0.00s

### Victor Wembanyama basic stats
- Status: ✓ PASS (CRITICAL)
- Duration: 0.00s

### Victor Wembanyama advanced stats
- Status: ✓ PASS (CRITICAL)
- Duration: 0.00s

### Victor Wembanyama player info
- Status: ✓ PASS
- Duration: 0.00s

### Available metrics count
- Status: ✓ PASS (CRITICAL)
- Duration: 0.00s

### Missing metrics count
- Status: ✓ PASS
- Duration: 0.00s

### Fetch metric: FTPCT
- Status: ✗ FAIL (CRITICAL)
- Duration: 0.22s
- Error: No data returned

### Fetch metric: TSPCT
- Status: ✓ PASS (CRITICAL)
- Duration: 0.19s

### Fetch metric: THPAr
- Status: ✓ PASS (CRITICAL)
- Duration: 0.28s

### Fetch metric: FTr
- Status: ✗ FAIL (CRITICAL)
- Duration: 0.15s
- Error: No data returned

### Fetch metric: TRBPCT
- Status: ✓ PASS (CRITICAL)
- Duration: 0.32s

### Rapid requests success rate
- Status: ✗ FAIL
- Duration: 0.00s
- Error: Value 0.0 below minimum 80.0

### Invalid player ID handling
- Status: ✗ FAIL
- Duration: 27.46s
- Error: Exception: RetryError[<Future at 0x1075b8150 state=finished raised EmptyResponseError>]

## Recommendations
❌ **DO NOT RUN THE DATA PIPELINE**
Critical failures detected. Please:
1. Check your internet connection
2. Verify the NBA API is accessible
3. Check if the season parameter is correct
4. Review the error messages above