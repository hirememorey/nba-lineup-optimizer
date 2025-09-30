# API Debugging Methodology: The "Isolate with curl First" Principle

**Date**: September 30, 2025  
**Status**: ✅ **CRITICAL METHODOLOGY**

## Overview

This document establishes the definitive methodology for debugging NBA API issues, based on hard-won lessons from multiple failed attempts. The core principle is: **When an API call fails, isolate the external dependency before debugging your own code.**

## The Problem

The NBA Stats API (`stats.nba.com`) is an **unofficial, private API** designed for the NBA's own website. It has several dangerous characteristics:

1. **Silent Timeouts**: The API can hang indefinitely on requests it deems "illogical" without returning an error
2. **Unpredictable Behavior**: What works today might not work tomorrow
3. **No Documentation**: Parameters, headers, and endpoints can change without notice
4. **Rate Limiting**: Excessive requests can result in IP blocking

## The Solution: The "Isolate with curl First" Methodology

### Core Principle

**Never debug your Python code when an API call fails. Always isolate the external dependency first using raw HTTP requests.**

### The Workflow

#### Step 1: Assume Your Client is Correct
Start by attempting the request through your `NBAStatsClient` or `nba_api` package.

```python
# Example: This is your first attempt
client = NBAStatsClient()
response = client.get_player_stats(player_id=2544, season="2024-25")
```

#### Step 2: When It Fails, Isolate with curl
If the request fails (especially with a timeout), immediately construct the equivalent raw `curl` command.

**Critical**: Use your browser's Developer Tools to capture the exact request made by the official NBA website.

1. Go to `stats.nba.com`
2. Navigate to the page that shows the data you need
3. Open Developer Tools (F12)
4. Go to the Network tab
5. Refresh the page
6. Find the relevant API call
7. Right-click → Copy as cURL

#### Step 3: Test with curl
Execute the `curl` command to verify the API works in isolation.

```bash
curl 'https://stats.nba.com/stats/playerdashboardbygeneralsplits?MeasureType=Base&PerMode=PerGame&PlayerID=2544&Season=2024-25&SeasonType=Regular+Season&LeagueID=00' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'x-nba-stats-token: true' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' \
  -H 'x-nba-stats-origin: stats' \
  -H 'Referer: https://www.nba.com/' \
  --compressed
```

#### Step 4: Iterate Until You Find Ground Truth
If the `curl` command fails, modify parameters until it works:

- Try different seasons (`2023-24` vs `2024-25`)
- Try different player IDs (active vs retired players)
- Try different measure types (`Base` vs `Advanced`)
- Check if the endpoint URL has changed

#### Step 5: Inform Your Python Code
Once you have a working `curl` command, update your Python code to match the working parameters.

## Common Failure Patterns

### Pattern 1: Silent Timeout on "Illogical" Requests
**Symptom**: Request hangs indefinitely (60+ seconds)
**Cause**: API deems the request illogical (e.g., requesting 2024-25 data for a retired player)
**Solution**: Use `curl` to test with different parameters until you find what the API accepts

### Pattern 2: Season Parameter Issues
**Symptom**: Request works for `2023-24` but fails for `2024-25`
**Cause**: The API might not have data for the most recent season under that exact identifier
**Solution**: Test different season formats (`2024-25`, `2024-25`, `2024-25 Regular Season`)

### Pattern 3: Header Requirements
**Symptom**: Request fails with authentication errors
**Cause**: Missing required headers that the NBA website includes
**Solution**: Copy headers exactly from the browser's network tab

## Why This Methodology Works

### 1. Eliminates Variables
By using `curl`, you remove your Python code, your HTTP client library, and your application logic from the equation. You're testing the API in its purest form.

### 2. Provides Ground Truth
A working `curl` command is the absolute truth about what the API accepts. There's no higher authority.

### 3. Saves Time
Instead of debugging complex Python code, you can quickly test different parameters with simple `curl` commands.

### 4. Prevents False Assumptions
It's easy to assume the problem is in your code when it's actually in the API's behavior.

## Anti-Patterns to Avoid

### ❌ Don't: Debug Python Code First
```python
# DON'T DO THIS
# If this fails, don't immediately start debugging the Python code
response = client.get_player_stats(player_id=2544, season="2024-25")
```

### ❌ Don't: Increase Timeouts as First Fix
```python
# DON'T DO THIS
# Increasing timeouts doesn't fix the root cause
response = requests.get(url, timeout=300)  # This just makes it hang longer
```

### ❌ Don't: Assume the API is Stable
```python
# DON'T DO THIS
# The API can change without notice
# Always verify with curl first
```

## Tools and Commands

### Essential curl Command Template
```bash
curl 'https://stats.nba.com/stats/ENDPOINT?PARAMS' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'x-nba-stats-token: true' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' \
  -H 'x-nba-stats-origin: stats' \
  -H 'Referer: https://www.nba.com/' \
  --compressed
```

### Browser Developer Tools
1. **Chrome/Edge**: F12 → Network tab
2. **Firefox**: F12 → Network tab
3. **Safari**: Develop menu → Show Web Inspector → Network tab

### Testing Different Scenarios
```bash
# Test with different seasons
curl '...Season=2023-24...'
curl '...Season=2024-25...'

# Test with different players
curl '...PlayerID=2544...'  # LeBron James (active)
curl '...PlayerID=893...'   # Michael Jordan (retired)

# Test with different measure types
curl '...MeasureType=Base...'
curl '...MeasureType=Advanced...'
```

## Integration with Project Workflow

### Before Implementing New API Calls
1. Use `curl` to verify the endpoint works
2. Capture the working parameters
3. Implement in Python using those exact parameters

### When Existing Code Breaks
1. Use `curl` to test the same endpoint
2. Compare working `curl` with your Python code
3. Update Python code to match working `curl`

### During Data Population
1. If a script hangs, immediately test the failing endpoint with `curl`
2. Don't waste time debugging Python until you know the API works

## Examples

### Example 1: Season Parameter Issue
**Problem**: `get_player_stats(2544, "2024-25")` hangs
**Solution**: 
```bash
# Test with 2023-24 first
curl '...Season=2023-24...'  # Works!

# Test with 2024-25
curl '...Season=2024-25...'  # Hangs!

# Conclusion: API doesn't support 2024-25 yet
```

### Example 2: Header Issue
**Problem**: Request returns 401 Unauthorized
**Solution**:
```bash
# Copy exact headers from browser
curl '...' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'x-nba-stats-token: true' \
  -H 'x-nba-stats-origin: stats' \
  # ... other headers from browser
```

## Conclusion

The "isolate with curl first" methodology is not just a debugging technique—it's a fundamental principle for working with unreliable external APIs. By following this workflow, you can:

1. **Save hours of debugging time**
2. **Avoid false assumptions about your code**
3. **Get definitive answers about API behavior**
4. **Build more reliable data pipelines**

**Remember**: When in doubt, curl it out. The API doesn't lie, but your assumptions might.
