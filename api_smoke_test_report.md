# NBA API Smoke Test Report
Generated on: 2025-10-01 12:53:30
Season: 2024-25
Duration: 28.54 seconds

## Summary
- Total tests: 25
- Passed: 21
- Failed: 4
- Success rate: 84.0%

## Critical Failures
These failures will prevent the data pipeline from running successfully:
- Fetch metric: FTPCT: No data returned
- Fetch metric: FTr: No data returned

## Warnings
These issues may cause problems but won't prevent the pipeline from running:
- Rapid requests success rate: Value 0.0 below minimum 80.0
- Invalid player ID handling: Exception - RetryError[<Future at 0x105115350 state=finished raised EmptyResponseError>]

## Detailed Test Results
### Basic team request
- Status: ✓ PASS (CRITICAL)
- Duration: 0.00s

### Basic player request
- Status: ✓ PASS (CRITICAL)
- Duration: 0.01s

### League player stats (Base)
- Status: ✓ PASS (CRITICAL)
- Duration: 0.00s

### League player stats (Advanced)
- Status: ✓ PASS (CRITICAL)
- Duration: 0.00s

### League hustle stats
- Status: ✓ PASS
- Duration: 0.00s

### League shot locations
- Status: ✓ PASS
- Duration: 0.00s

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
- Duration: 0.17s
- Error: No data returned

### Fetch metric: TSPCT
- Status: ✓ PASS (CRITICAL)
- Duration: 0.18s

### Fetch metric: THPAr
- Status: ✓ PASS (CRITICAL)
- Duration: 0.14s

### Fetch metric: FTr
- Status: ✗ FAIL (CRITICAL)
- Duration: 0.13s
- Error: No data returned

### Fetch metric: TRBPCT
- Status: ✓ PASS (CRITICAL)
- Duration: 0.23s

### Rapid requests success rate
- Status: ✗ FAIL
- Duration: 0.00s
- Error: Value 0.0 below minimum 80.0

### Invalid player ID handling
- Status: ✗ FAIL
- Duration: 21.55s
- Error: Exception: RetryError[<Future at 0x105115350 state=finished raised EmptyResponseError>]

## Recommendations
❌ **DO NOT RUN THE DATA PIPELINE**
Critical failures detected. Please:
1. Check your internet connection
2. Verify the NBA API is accessible
3. Check if the season parameter is correct
4. Review the error messages above