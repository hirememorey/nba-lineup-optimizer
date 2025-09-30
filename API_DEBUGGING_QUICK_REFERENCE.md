# API Debugging Quick Reference

**When an NBA API call fails, follow this workflow:**

## 1. Don't Debug Python Code First
❌ **Wrong**: Start debugging your `NBAStatsClient` or `nba_api` code
✅ **Right**: Test the API with `curl` first

## 2. Get the Raw Request
1. Go to `stats.nba.com`
2. Navigate to the data you need
3. Open Developer Tools (F12) → Network tab
4. Refresh the page
5. Find the API call → Right-click → Copy as cURL

## 3. Test with curl
```bash
curl 'https://stats.nba.com/stats/ENDPOINT?PARAMS' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'x-nba-stats-token: true' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' \
  -H 'x-nba-stats-origin: stats' \
  -H 'Referer: https://www.nba.com/' \
  --compressed
```

## 4. If curl Fails, Try These Fixes
- **Different season**: `2023-24` vs `2024-25`
- **Different player**: Active vs retired player
- **Different measure type**: `Base` vs `Advanced`
- **Check headers**: Copy exactly from browser

## 5. Once curl Works, Update Python
Use the working `curl` parameters in your Python code.

## Common Issues
- **Silent timeout**: API hangs on "illogical" requests
- **Season issues**: API might not support latest season
- **Header issues**: Missing required headers
- **Rate limiting**: Too many requests too fast

## Remember
**The API doesn't lie, but your assumptions might.**

For detailed methodology: `docs/api_debugging_methodology.md`
