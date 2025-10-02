# Data Completeness Validation Report
Generated: 2025-10-01 15:58:42.200399

## Executive Summary
- Total tables: 43
- Tables with 2024-25 data: 23
- Available canonical metrics: 47/48

## Critical Tables Status
- PlayerSeasonRawStats: 21 rows ⚠️
- PlayerSeasonAdvancedStats: 21 rows ⚠️
- PlayerSeasonDriveStats: 0 rows ❌
- PlayerSeasonCatchAndShootStats: 569 rows ✅
- PlayerAnthroStats: 106 rows ✅
- PlayerSeasonDerivedShotStats: 0 rows ❌

## Canonical Metrics Availability
- ✅ FTPCT: 178 players (PlayerArchetypeFeatures)
- ✅ TSPCT: 178 players (PlayerArchetypeFeatures)
- ✅ THPAr: 178 players (PlayerArchetypeFeatures)
- ✅ FTr: 178 players (PlayerArchetypeFeatures)
- ✅ TRBPCT: 178 players (PlayerArchetypeFeatures)
- ✅ ASTPCT: 178 players (PlayerArchetypeFeatures)
- ✅ AVGDIST: 178 players (PlayerArchetypeFeatures)
- ✅ Zto3r: 178 players (PlayerArchetypeFeatures)
- ✅ THto10r: 178 players (PlayerArchetypeFeatures)
- ✅ TENto16r: 178 players (PlayerArchetypeFeatures)
- ✅ SIXTto3PTr: 178 players (PlayerArchetypeFeatures)
- ✅ HEIGHT: 178 players (PlayerArchetypeFeatures)
- ✅ WINGSPAN: 178 players (PlayerArchetypeFeatures)
- ✅ FRNTCTTCH: 178 players (PlayerArchetypeFeatures)
- ✅ TOP: 178 players (PlayerArchetypeFeatures)
- ✅ AVGSECPERTCH: 178 players (PlayerArchetypeFeatures)
- ✅ AVGDRIBPERTCH: 178 players (PlayerArchetypeFeatures)
- ✅ ELBWTCH: 178 players (PlayerArchetypeFeatures)
- ✅ POSTUPS: 178 players (PlayerArchetypeFeatures)
- ✅ PNTTOUCH: 178 players (PlayerArchetypeFeatures)
- ✅ DRIVES: 178 players (PlayerArchetypeFeatures)
- ✅ DRFGA: 178 players (PlayerArchetypeFeatures)
- ✅ DRPTSPCT: 178 players (PlayerArchetypeFeatures)
- ✅ DRPASSPCT: 178 players (PlayerArchetypeFeatures)
- ✅ DRASTPCT: 178 players (PlayerArchetypeFeatures)
- ✅ DRTOVPCT: 178 players (PlayerArchetypeFeatures)
- ✅ DRPFPCT: 178 players (PlayerArchetypeFeatures)
- ✅ DRIMFGPCT: 178 players (PlayerArchetypeFeatures)
- ✅ CSFGA: 178 players (PlayerArchetypeFeatures)
- ✅ CS3PA: 178 players (PlayerArchetypeFeatures)
- ✅ PASSESMADE: 178 players (PlayerArchetypeFeatures)
- ✅ SECAST: 178 players (PlayerArchetypeFeatures)
- ✅ POTAST: 178 players (PlayerArchetypeFeatures)
- ✅ PUFGA: 178 players (PlayerArchetypeFeatures)
- ✅ PU3PA: 178 players (PlayerArchetypeFeatures)
- ✅ PSTUPFGA: 178 players (PlayerArchetypeFeatures)
- ✅ PSTUPPTSPCT: 178 players (PlayerArchetypeFeatures)
- ✅ PSTUPPASSPCT: 178 players (PlayerArchetypeFeatures)
- ✅ PSTUPASTPCT: 178 players (PlayerArchetypeFeatures)
- ✅ PSTUPTOVPCT: 178 players (PlayerArchetypeFeatures)
- ✅ PNTTCHS: 178 players (PlayerArchetypeFeatures)
- ✅ PNTFGA: 178 players (PlayerArchetypeFeatures)
- ✅ PNTPTSPCT: 178 players (PlayerArchetypeFeatures)
- ✅ PNTPASSPCT: 178 players (PlayerArchetypeFeatures)
- ✅ PNTASTPCT: 178 players (PlayerArchetypeFeatures)
- ✅ PNTTVPCT: 178 players (PlayerArchetypeFeatures)
- ✅ AVGFGATTEMPTEDAGAINSTPERGAME: 178 players (PlayerArchetypeFeatures)

**Total Available: 47/48 metrics**

## Detailed Table Analysis
### ArchetypeLineups
- Total rows: 88
- 2024-25 rows: 88
- Columns: 12
- Null rates (first 5 columns):
  - archetype_lineup_id: 0.0%
  - season: 0.0%
  - total_minutes: 0.0%
  - supercluster_id: 0.0%
  - WPCT_PTS_FT: 0.0%

### Archetypes
- Total rows: 8
- 2024-25 rows: 8
- Columns: 2

### Games
- Total rows: 1230
- 2024-25 rows: 1230
- Columns: 11
- Null rates (first 5 columns):
  - game_id: 0.0%
  - game_date: 0.0%
  - home_team_id: 0.0%
  - away_team_id: 0.0%
  - home_team_score: 100.0%

### LineupSuperclusters
- Total rows: 6
- 2024-25 rows: 6
- Columns: 2

### PlayerAnthroStats
- Total rows: 106
- 2024-25 rows: 106
- Columns: 10

### PlayerArchetypeFeatures
- Total rows: 178
- 2024-25 rows: 178
- Columns: 49
- Null rates (first 5 columns):
  - player_id: 0.0%
  - FTPCT: 0.0%
  - TSPCT: 0.0%
  - THPAr: 0.0%
  - FTr: 0.0%

### PlayerLineupStats
- Total rows: 2000
- 2024-25 rows: 2000
- Columns: 80
- Null rates (first 5 columns):
  - group_id: 0.0%
  - group_name: 0.0%
  - team_id: 0.0%
  - season: 0.0%
  - gp: 0.0%

### PlayerSalaries
- Total rows: 468
- 2024-25 rows: 468
- Columns: 4

### PlayerSalaries_old
- Total rows: 513
- 2024-25 rows: 513
- Columns: 2

### PlayerSeasonAdvancedStats
- Total rows: 21
- 2024-25 rows: 21
- Columns: 27
- Null rates (first 5 columns):
  - player_id: 0.0%
  - season: 0.0%
  - team_id: 0.0%
  - age: 100.0%
  - games_played: 100.0%

### PlayerSeasonArchetypes
- Total rows: 356
- 2024-25 rows: 356
- Columns: 3
- Null rates (first 5 columns):
  - player_id: 0.0%
  - season: 0.0%
  - archetype_id: 0.0%

### PlayerSeasonCatchAndShootStats
- Total rows: 569
- 2024-25 rows: 569
- Columns: 17
- Null rates (first 5 columns):
  - player_id: 0.0%
  - season: 0.0%
  - team_id: 0.0%
  - games_played: 0.0%
  - wins: 0.0%

### PlayerSeasonRawStats
- Total rows: 21
- 2024-25 rows: 21
- Columns: 28
- Null rates (first 5 columns):
  - player_id: 0.0%
  - season: 0.0%
  - team_id: 0.0%
  - games_played: 0.0%
  - games_started: 100.0%

### PlayerSeasonShootingZoneStats
- Total rows: 569
- 2024-25 rows: 569
- Columns: 31
- Null rates (first 5 columns):
  - player_id: 0.0%
  - player_name: 0.0%
  - team_id: 0.0%
  - team_abbreviation: 0.0%
  - age: 0.0%

### PlayerSeasonSkill
- Total rows: 534
- 2024-25 rows: 534
- Columns: 15
- Null rates (first 5 columns):
  - player_id: 0.0%
  - season: 0.0%
  - player_name: 0.0%
  - team_abbreviation: 0.0%
  - offensive_darko: 0.0%

### PlayerShotChart
- Total rows: 37891
- 2024-25 rows: 37891
- Columns: 17
- Null rates (first 5 columns):
  - shot_id: 0.0%
  - player_id: 0.0%
  - team_id: 0.0%
  - game_id: 0.0%
  - season: 0.0%

### PlayerShotMetrics
- Total rows: 84
- 2024-25 rows: 84
- Columns: 9
- Null rates (first 5 columns):
  - player_id: 0.0%
  - season: 0.0%
  - avgdist: 0.0%
  - zto3r: 0.0%
  - thto10r: 0.0%

### PlayerSkills
- Total rows: 521
- 2024-25 rows: 521
- Columns: 6

### PlayerSkills_old
- Total rows: 2521
- 2024-25 rows: 2521
- Columns: 5

### Players
- Total rows: 5025
- 2024-25 rows: 5025
- Columns: 16

### Possessions
- Total rows: 574357
- 2024-25 rows: 574357
- Columns: 47

### Teams
- Total rows: 30
- 2024-25 rows: 30
- Columns: 10

### sqlite_sequence
- Total rows: 4
- 2024-25 rows: 4
- Columns: 2

## Recommendations
✅ **GOOD**: Sufficient metrics available for analysis