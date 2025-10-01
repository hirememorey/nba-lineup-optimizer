# NBA API Smoke Test Report
Generated on: 2025-10-01 13:17:18
Season: 2024-25
Duration: 34.99 seconds

## Summary
- Total tests: 25
- Passed: 23
- Failed: 2
- Success rate: 92.0%

## Warnings
These issues may cause problems but won't prevent the pipeline from running:
- Rapid requests success rate: Value 0.0 below minimum 80.0
- Invalid player ID handling: Exception - RetryError[<Future at 0x10629c550 state=finished raised EmptyResponseError>]

## Detailed Test Results
### Basic team request
- Status: ✓ PASS (CRITICAL)
- Duration: 0.00s

### Basic player request
- Status: ✓ PASS (CRITICAL)
- Duration: 0.01s

### League player stats (Base)
- Status: ✓ PASS (CRITICAL)
- Duration: 0.01s

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
- Status: ✓ PASS (CRITICAL)
- Duration: 0.13s

### Fetch metric: TSPCT
- Status: ✓ PASS (CRITICAL)
- Duration: 0.21s

### Fetch metric: THPAr
- Status: ✓ PASS (CRITICAL)
- Duration: 0.16s

### Fetch metric: FTr
- Status: ✓ PASS (CRITICAL)
- Duration: 0.26s

### Fetch metric: TRBPCT
- Status: ✓ PASS (CRITICAL)
- Duration: 0.23s

### Rapid requests success rate
- Status: ✗ FAIL
- Duration: 0.00s
- Error: Value 0.0 below minimum 80.0

### Invalid player ID handling
- Status: ✗ FAIL
- Duration: 27.80s
- Error: Exception: RetryError[<Future at 0x10629c550 state=finished raised EmptyResponseError>]

## Recommendations
⚠️ **PROCEED WITH CAUTION**
Some non-critical issues detected. The pipeline may run but with reduced functionality.
Consider addressing warnings before running the full pipeline.