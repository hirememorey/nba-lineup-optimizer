# Data Reality Report
**Generated:** October 2, 2025  
**Purpose:** Ground truth documentation of actual database schema and data structure

## Executive Summary

This report documents the actual state of the database schema and data, based on empirical investigation rather than documentation assumptions. This is the definitive reference for any developer working on the possession-level modeling system.

## Key Findings

### ✅ **Critical Data Available**
- **Possessions with Lineup Data:** 574,357 records with complete 10-player lineup information
- **Player Archetypes:** 270 players with archetype assignments for 2024-25 season
- **Player Skills (DARKO):** 534 players with skill ratings for 2024-25 season

### ⚠️ **Schema Discrepancies Identified**
The actual database schema differs significantly from documentation expectations:

1. **PlayerSeasonSkill Table Structure:**
   - **Expected:** `offensive_rating`, `defensive_rating` columns
   - **Actual:** `offensive_darko`, `defensive_darko` columns
   - **Impact:** All skill-related queries must use the actual column names

2. **Possession Data Structure:**
   - **Event Types:** Numeric codes (1, 2, 3, 4, 5) not text strings
   - **Lineup Fields:** Present as `home_player_1_id` through `home_player_5_id` and `away_player_1_id` through `away_player_5_id`
   - **Team Context:** `offensive_team_id` and `defensive_team_id` fields available

## Detailed Schema Analysis

### Core Tables for Modeling

#### 1. PlayerSeasonSkill
```sql
-- Actual columns (from PRAGMA table_info)
player_id INTEGER PRIMARY KEY
season TEXT NOT NULL
offensive_darko REAL
defensive_darko REAL
darko REAL
offensive_epm REAL
defensive_epm REAL
epm REAL
offensive_raptor REAL
defensive_raptor REAL
raptor REAL
```

**Key Insight:** Multiple skill metrics available (DARKO, EPM, RAPTOR), not just DARKO as assumed.

#### 2. PlayerSeasonArchetypes
```sql
-- Actual columns
player_id INTEGER
season TEXT
archetype_id INTEGER
```

**Key Insight:** Archetype assignments are stored as integer IDs, not text names. Need to join with `Archetypes` table for names.

#### 3. Possessions
```sql
-- Key columns for lineup reconstruction
game_id TEXT
event_num INTEGER
event_type TEXT
home_player_1_id INTEGER
home_player_2_id INTEGER
home_player_3_id INTEGER
home_player_4_id INTEGER
home_player_5_id INTEGER
away_player_1_id INTEGER
away_player_2_id INTEGER
away_player_3_id INTEGER
away_player_4_id INTEGER
away_player_5_id INTEGER
offensive_team_id INTEGER
defensive_team_id INTEGER
```

**Key Insight:** Complete 10-player lineup data is available for 574,357 possessions.

### Supporting Tables

#### 4. Archetypes
```sql
archetype_id INTEGER PRIMARY KEY
archetype_name TEXT NOT NULL UNIQUE
```

#### 5. Games
```sql
game_id TEXT PRIMARY KEY
game_date TEXT NOT NULL
home_team_id INTEGER NOT NULL
away_team_id INTEGER NOT NULL
season TEXT NOT NULL
```

## Data Quality Assessment

### ✅ **High Quality Data**
- **Possession Coverage:** 574,357 possessions with complete lineup data
- **Player Coverage:** 270 players with archetype assignments
- **Skill Data:** 534 players with DARKO ratings
- **Schema Consistency:** All foreign key relationships intact

### ⚠️ **Potential Issues**
- **Event Type Encoding:** Numeric codes need mapping to meaningful categories
- **Missing Outcome Data:** No direct possession outcome field (points scored)
- **Team Context:** Need to verify `offensive_team_id`/`defensive_team_id` accuracy

## Critical Implementation Notes

### 1. Column Name Mapping Required
All code must use actual column names:
- `offensive_darko` not `offensive_rating`
- `defensive_darko` not `defensive_rating`
- `archetype_id` not `archetype_name`

### 2. Data Joins Required
- Player archetypes: `PlayerSeasonArchetypes` → `Archetypes`
- Player skills: `PlayerSeasonSkill` (multiple metrics available)
- Game context: `Possessions` → `Games`

### 3. Possession Outcome Calculation
No direct outcome field exists. Must calculate from:
- Event sequences within possessions
- Score changes
- Event types (shot made/missed, turnover, etc.)

## Recommendations

### Immediate Actions
1. **Create Column Mapping Module:** `db_mapping.py` with actual column names
2. **Build Possession Outcome Calculator:** Logic to determine points scored per possession
3. **Validate Team Context:** Verify `offensive_team_id`/`defensive_team_id` accuracy

### Schema Validation Requirements
Any future code must validate against these actual column names and data structures. The schema is stable and well-structured, but different from documentation expectations.

## Files Generated
- `actual_schema.txt` - Complete database schema
- `skill_table_info.txt` - PlayerSeasonSkill table structure
- `possession_sample.txt` - Sample possession data
- `archetype_sample.txt` - Sample archetype assignments

## Next Steps
1. Create `schema_expectations.yml` based on these findings
2. Build `LiveSchemaValidator` to enforce these expectations
3. Implement column mapping in `db_mapping.py`
4. Develop possession outcome calculation logic

---

**This report represents the ground truth of the database. All implementation must be based on these actual findings, not documentation assumptions.**

