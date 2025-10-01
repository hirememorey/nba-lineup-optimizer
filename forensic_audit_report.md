# NBA Data Pipeline Forensic Audit Report

**Generated:** 2025-10-01 13:08:00

## Summary

- Total Tests: 9
- PASS: 6
- FAIL: 1
- WARN: 2

## Detailed Results

### Phase 1 - Python Version
**Status:** PASS
**Message:** Python 3.13.1 is compatible

### Phase 1 - Dependencies
**Status:** FAIL
**Message:** Missing packages: tenacity

### Phase 1 - Database primary
**Status:** PASS
**Message:** Connected successfully, 43 tables found

### Phase 1 - Database secondary
**Status:** PASS
**Message:** Connected successfully, 8 tables found

### Phase 1 - Database tertiary
**Status:** PASS
**Message:** Connected successfully, 14 tables found

### Phase 1 - Schema Audit
**Status:** PASS
**Message:** All expected tables present (43 total tables)

### Phase 2 - Cache System
**Status:** WARN
**Message:** No cache files found

### Phase 2 - API Smoke Test
**Status:** WARN
**Message:** API success rate: 84.0% (below 90% threshold)

### Phase 2 - Semantic Verification
**Status:** PASS
**Message:** Semantic verification: 100.0%

