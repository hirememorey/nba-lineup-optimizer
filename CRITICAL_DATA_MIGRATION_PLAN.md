# Critical Data Migration Plan: 2024-25 → 2022-23

**Date**: October 4, 2025  
**Status**: 🚨 **CRITICAL BLOCKER** - Must be completed before any validation

## Executive Summary

We have discovered a **critical temporal mismatch** that makes our current validation plan impossible. We currently have 2024-25 season data, but the original research paper used 2022-23 data. This means we cannot validate our model against the paper's examples until we populate our database with 2022-23 data.

## The Problem

### Current State
- **Database**: Contains 2024-25 season data throughout
- **Player Statistics**: All from 2024-25 season
- **Player Salaries**: All from 2024-25 season  
- **Player Skills (DARKO)**: All from 2024-25 season
- **Archetypes**: Generated using 2024-25 player performances
- **Superclusters**: Generated using 2024-25 lineup data

### Original Paper Context
- **Season**: 2022-23 NBA season
- **Examples**: Lakers, Pacers, Suns analysis based on 2022-23 rosters and player performances
- **Player Context**: LeBron, AD, Westbrook, etc. in their 2022-23 roles and effectiveness
- **Team Systems**: 2022-23 team strategies and lineup compositions

### Why This Matters
1. **Player Evolution**: LeBron's role in 2022-23 Lakers vs 2024-25 Lakers is completely different
2. **Team Systems**: Lakers' system pre-trade deadline 2022-23 vs current 2024-25 system
3. **Validation Accuracy**: We can only validate against the same temporal context the paper used
4. **Reproducibility**: Other researchers need to be able to reproduce the paper's results

## Migration Plan

### Phase 1: Backup and Preparation (1-2 days)
- [ ] **Backup Current Data**: Create full backup of 2024-25 database
- [ ] **Document Current State**: Record all current data coverage and quality metrics
- [ ] **Prepare Migration Scripts**: Modify data pipeline scripts for 2022-23 season
- [ ] **Test Migration Process**: Run migration on test database first

### Phase 2: Data Population (3-5 days)
- [ ] **Player Statistics**: Fetch all 2022-23 player statistics from NBA API
- [ ] **Player Salaries**: Get 2022-23 salary data from HoopsHype
- [ ] **Player Skills**: Obtain 2022-23 DARKO ratings
- [ ] **Possession Data**: Fetch 2022-23 play-by-play data
- [ ] **Team Rosters**: Get 2022-23 team rosters and lineups

### Phase 3: Model Regeneration (2-3 days)
- [ ] **Player Archetypes**: Regenerate using 2022-23 data
- [ ] **Lineup Superclusters**: Regenerate using 2022-23 lineup data
- [ ] **Bayesian Model**: Retrain model coefficients using 2022-23 data
- [ ] **Validation**: Test model against paper's examples

### Phase 4: Validation (2-3 days)
- [ ] **Lakers Example**: Test 3&D players fit better with LeBron (2022-23 context)
- [ ] **Pacers Example**: Test defensive needs over positional needs (2022-23 context)
- [ ] **Suns Example**: Test defensive bigs fit better with offensive juggernauts (2022-23 context)
- [ ] **Document Results**: Record validation outcomes and any limitations

## Technical Implementation

### Data Pipeline Modifications
1. **Season Parameter**: Update all scripts to accept season parameter
2. **API Calls**: Modify NBA API calls to fetch 2022-23 data
3. **Database Schema**: Ensure schema supports multiple seasons
4. **Data Validation**: Add season-specific validation checks

### Key Files to Modify
- `src/nba_stats/scripts/populate_players.py`
- `src/nba_stats/scripts/populate_player_anthro.py`
- `src/nba_stats/scripts/populate_player_stats.py`
- `src/nba_stats/scripts/populate_salaries.py`
- `src/nba_stats/scripts/populate_shot_metrics.py`
- All archetype generation scripts
- All supercluster generation scripts

### Database Changes
- Add season_id columns where needed
- Update foreign key constraints
- Add season-specific indexes
- Ensure data isolation between seasons

## Success Criteria

### Data Quality
- [ ] 100% coverage of 2022-23 player statistics
- [ ] All major NBA players have 2022-23 archetype assignments
- [ ] Complete 2022-23 possession data
- [ ] Valid 2022-23 lineup superclusters

### Model Validation
- [ ] Model reproduces paper's Lakers example results
- [ ] Model reproduces paper's Pacers example results  
- [ ] Model reproduces paper's Suns example results
- [ ] All validation tests pass with 2022-23 data

### Documentation
- [ ] Updated documentation reflects 2022-23 data context
- [ ] Migration process documented for future use
- [ ] Validation results documented and shared

## Risk Mitigation

### Data Availability
- **Risk**: 2022-23 data may not be available or complete
- **Mitigation**: Verify data availability before starting migration
- **Fallback**: Use 2023-24 data if 2022-23 is incomplete

### Performance Impact
- **Risk**: Migration may take significant time
- **Mitigation**: Run migration in parallel where possible
- **Monitoring**: Track progress and estimate completion time

### Data Quality
- **Risk**: 2022-23 data quality may be different
- **Mitigation**: Apply same validation checks as current data
- **Fallback**: Use data imputation strategies if needed

## Timeline

**Total Estimated Time**: 1-2 weeks
- **Week 1**: Data migration and population
- **Week 2**: Model regeneration and validation

**Critical Path**: Data population → Model regeneration → Validation

## Next Steps

1. **Immediate**: Start Phase 1 (backup and preparation)
2. **This Week**: Complete data migration
3. **Next Week**: Complete model regeneration and validation
4. **After Validation**: Proceed with k=8 archetype implementation (if validation passes)

## Conclusion

This temporal mismatch is a critical blocker that must be resolved before any meaningful validation can occur. The migration to 2022-23 data is not optional - it's essential for the project's success. Without this migration, we cannot validate our model against the original paper's examples, making the entire validation phase meaningless.

**The critical insight**: Statistical convergence does not equal semantic validity, and temporal context is essential for meaningful validation.
