# Golden Cohort Validation Guide

## Overview

The Golden Cohort Validation is a critical data integrity tool that performs deep, surgical checks on a predefined group of players to identify subtle data corruption issues that macro-level validation might miss. This tool was created as a direct response to our pre-mortem analysis, which identified the risk of silent data corruption.

## Purpose

The Golden Cohort Validation addresses the critical failure mode where:
- Data appears structurally valid but is semantically incorrect
- Cross-table consistency issues exist that aren't caught by broad validation
- Season-specific data corruption affects specific player subsets
- Silent failures in data population scripts go undetected

## Golden Cohort Players

The validation focuses on 5 carefully selected players representing different edge cases:

1. **LeBron James (ID: 2544)** - Superstar player
2. **Victor Wembanyama (ID: 1630173)** - Rookie player  
3. **James Harden (ID: 201935)** - Player traded mid-season
4. **Luka Dončić (ID: 201142)** - International player
5. **Danny Green (ID: 201980)** - Journeyman role-player

## Validation Checks

### 1. Player Existence
- Verifies all Golden Cohort players exist in the database
- Confirms player names match expectations
- Validates player IDs are correct

### 2. Season Consistency
- Checks that all tables for a player have consistent season data
- Identifies cases where some tables have 2024-25 data while others have different seasons
- Prevents cross-season data contamination

### 3. Data Completeness
- Measures table coverage for each player across 14 critical tables
- Ensures adequate data coverage (≥80% threshold)
- Identifies players with missing data in key tables

### 4. Value Reasonableness
- Validates that statistical values are within reasonable ranges
- Checks percentage metrics (0-1 range)
- Identifies impossible or suspicious values

### 5. Cross-Table Consistency
- Verifies relationships between related tables
- Ensures basic stats and advanced stats are consistent
- Detects data integrity issues across table boundaries

## Usage

### Basic Usage
```bash
python validate_golden_cohort.py
```

### Understanding Results

The script generates two outputs:

1. **Console Output**: Real-time validation progress and results
2. **JSON Report**: `golden_cohort_validation_results.json` with detailed findings

### Expected Results

**✅ PASS**: All checks pass, data integrity verified
**⚠️ WARNING**: Some issues detected but not critical
**❌ FAIL**: Critical data integrity issues detected

## Current Status

As of October 1, 2025, the Golden Cohort Validation shows:

- **Player Existence**: ✅ All 5 players found
- **Season Consistency**: ✅ All players have consistent 2024-25 data
- **Data Completeness**: ⚠️ Inadequate coverage (14.3%) - core tables empty
- **Value Reasonableness**: ⚠️ Cannot access core statistics tables
- **Cross-Table Consistency**: ✅ No inconsistencies detected

## Interpretation

The current "inadequate coverage" result indicates that:
- Specialized tracking tables are populated (PlayerSeasonCatchAndShootStats, etc.)
- Core statistics tables are empty (PlayerSeasonRawStats, PlayerSeasonAdvancedStats)
- This is expected given the current implementation status

## Next Steps

1. **Populate Core Tables**: Run individual population scripts for core statistics
2. **Re-run Validation**: Execute Golden Cohort validation after core table population
3. **Address Issues**: Fix any data integrity issues identified by the validation

## Integration with Pipeline

The Golden Cohort Validation should be run:
- After major data population operations
- Before proceeding to analysis phase
- As part of regular data quality monitoring
- When investigating data integrity issues

## Files

- `validate_golden_cohort.py` - Main validation script
- `golden_cohort_validation_results.json` - Detailed validation results
- `golden_cohort_validation.log` - Validation log file

## Technical Details

The validation script performs SQL queries across multiple tables to check:
- Data existence and completeness
- Value ranges and reasonableness
- Cross-table relationships
- Season consistency
- Data integrity patterns

This provides a comprehensive view of data quality that complements the broader validation tools in the system.
