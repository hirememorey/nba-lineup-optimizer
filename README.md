# NBA Lineup Optimizer

This project implements the methodology from the research paper "Algorithmic NBA Player Acquisition" by Brill, Hughes, and Waldbaum. It uses a data-driven approach to NBA player acquisition and lineup optimization, prioritizing team **fit** over individual skill alone.

**Vision**: A fan-friendly tool that helps NBA fans understand which players would fit best on their favorite teams, with the ultimate goal of evolving into a predictive engine for General Managers to make data-driven roster decisions.

---

## Documentation Guide

This project's documentation is curated to provide a clear path for any contributor.

*   **To understand the current work and next steps:**
    *   **[`CURRENT_STATUS.md`](./CURRENT_STATUS.md)**: The "Captain's Log" with detailed, up-to-the-minute status.

*   **To run the software:**
    *   **[`docs/GUIDE.md`](./docs/GUIDE.md)**: The complete "how-to" manual for fans, developers, and administrators.

*   **To understand the project's design and principles:**
    *   **[`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md)**: The "Blueprint" explaining our guiding principles, system architecture, and core concepts.

*   **For historical context and past research:**
    *   **[`docs/archive/`](./docs/archive/)**: An archive of superseded documents.

---

## Current Status (High-Level)

**Date**: October 27, 2025
**Status**: ✅ **PHASE 2 MULTI-SEASON MODEL TRAINING COMPLETE** — Successfully trained Bayesian model on 103,047 multi-season possessions with 36 unique matchups. Archetype index bug fixed, supercluster system regenerated. Ready for Phase 3 predictive validation.

**Major Achievement**: ✅ **1,770,051 POSSESSIONS ACROSS 3,794 GAMES** — Complete historical dataset ready for multi-season Bayesian model training!
- **2018-19**: 1,312/1,312 games (621,523 possessions) ✅ 100% Complete
- **2020-21**: 1,165/1,165 games (538,444 possessions) ✅ 100% Complete
- **2021-22**: 1,317/1,317 games (610,084 possessions) ✅ 100% Complete

**Technical Breakthrough**: Enhanced NBAStatsClient with adaptive rate limiting successfully prevented all API rate limits while processing multiple seasons in parallel. Zero manual intervention required!

**Next Phase**: Phase 3 predictive validation against 2022-23 outcomes using the trained multi-season model. Ready to test Russell Westbrook-Lakers case study and assess predictive accuracy.

**Predictive Vision**: The ultimate goal is to build a model that can predict the Russell Westbrook-Lakers failure *before* the 2022-23 season begins, transforming this from a historical analysis project into a true GM decision-making tool.

**Phase 2 Status**: ✅ **COMPLETED**. Multi-season Bayesian model successfully trained with excellent convergence (R-hat < 1.01). All critical bugs resolved, 36 unique matchups operational.

See **[`CURRENT_STATUS.md`](./CURRENT_STATUS.md)** for latest results, **[`NEXT_STEPS_FOR_DEVELOPER.md`](./NEXT_STEPS_FOR_DEVELOPER.md)** for hand-off tasks, and the **Predictive Vision & Evolution Strategy** section in **[`CURRENT_STATUS.md`](./CURRENT_STATUS.md)** for the detailed predictive modeling implementation plan.

---

## Recent Achievement (2025-10-27)

- ✅ **PHASE 2 MULTI-SEASON MODEL TRAINING COMPLETE**: Successfully trained Bayesian model on **103,047 possessions** across three historical seasons
  - **2018-19**: 34,978 possessions (33.9%) ✅ Model trained
  - **2020-21**: 20,251 possessions (19.7%) ✅ Model trained
  - **2021-22**: 47,818 possessions (46.4%) ✅ Model trained
- ✅ **Enhanced Rate Limiting Breakthrough**: NBAStatsClient with adaptive rate limiting successfully prevented all API rate limits while processing multiple seasons in parallel
- ✅ **Technical Innovation**: Zero manual intervention required - complete automation from start to finish
- ✅ **Data Quality Excellence**: 15,000+ substitution anomalies handled gracefully across all games
- ✅ **Cache System Optimized**: 93+ MB API response cache built with maximum efficiency
- ✅ **Archetype Index Bug Fixed**: Critical mapping issue resolved (1-8 IDs → 0-7 indices)
- ✅ **Supercluster System Regenerated**: 36 unique matchups operational (6×6 system)
- ✅ **Model Convergence**: R-hat < 1.01, 0 divergent transitions, 18 parameters learned
- 2022-23 DARKO ratings available in `PlayerSeasonSkill` (549 rows) for validation
- Multi-season Z-matrix available in `multi_season_bayesian_data.csv` with all 8 archetypes active

**⚠️ Data Quality Issues Identified (2025-10-27)**:
- **Drive Statistics**: All players have identical values across historical seasons (NBA API limitation)
- **Other Tracking Stats**: Show proper variation (touch stats, paint touches, etc.)
- **Impact**: 47/48 canonical metrics available, but only ~36-40 have real variation
- **Status**: Archetype clustering functional but with reduced discriminatory power
- **Current Phase**: Phase 3 predictive validation with documented data quality limitations

### Quick verification (final completion status)

```bash
# Verify complete historical data collection
python3 -c "
import sqlite3
conn = sqlite3.connect('src/nba_stats/db/nba_stats.db')
cursor = conn.cursor()
print('=== FINAL MULTI-SEASON COMPLETION STATUS ===')
print()

seasons = ['2018-19', '2020-21', '2021-22']
total_possessions = 0

for season in seasons:
    cursor.execute('''
        SELECT COUNT(DISTINCT p.game_id) as games, COUNT(p.game_id) as possessions
        FROM Possessions p
        JOIN Games g ON p.game_id = g.game_id
        WHERE g.season = ?
    ''', (season,))
    result = cursor.fetchone()
    total_games = cursor.execute('SELECT COUNT(*) FROM Games WHERE season = ?', (season,)).fetchone()[0]
    if result:
        games, possessions = result
        total_possessions += possessions
        status = '✅' if games == total_games else '❌'
        print(f'{status} {season}: {games}/{total_games} ({games/total_games*100:.1f}%) - {possessions:,} possessions')

print(f'\\n🎉 TOTAL: {total_possessions:,} possessions ready for Bayesian model training!')
conn.close()
"
```

### Quick run (smoke test)

```bash
python3 train_bayesian_model.py \
  --data stratified_sample_10k.csv \
  --stan bayesian_model_k8.stan \
  --draws 100 --tune 100 --chains 1 \
  --coefficients model_coefficients_sample.csv
```

For a full run, switch to `--data production_bayesian_data.csv` and increase `--draws`, `--tune`, and `--chains`.