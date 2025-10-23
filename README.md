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

**Date**: October 23, 2025
**Status**: ✅ **PHASE 1.4.4 ARCHETYPES COMPLETE; POSSESSIONS 45.9% DONE** — Historical archetype features generation complete for all three target seasons (717 players). Possessions collection 45.9% complete for 2018-19 season using robust, resumable pipeline.

**Recent Achievement**: Successfully generated historical archetype features and started possessions collection:
- **Archetype Features**: 717 players across 2018-19 (234), 2020-21 (229), 2021-22 (254) seasons
- **Possessions Collection**: 45.9% complete for 2018-19 (602/1,312 games = 286,012 possessions)
- **Script Enhancement**: Modified archetype generation to create season-specific tables
- **Cache System**: Built 93 MB API response cache for efficient data collection
- **Team Distribution**: All seasons now have realistic 8-22 players per team (was 4-15 for 2018-19)

**Next Phase**: Complete possessions collection for all historical seasons and integrate multi-season data for Bayesian model training.

**Predictive Vision**: The ultimate goal is to build a model that can predict the Russell Westbrook-Lakers failure *before* the 2022-23 season begins, transforming this from a historical analysis project into a true GM decision-making tool.

See **[`CURRENT_STATUS.md`](./CURRENT_STATUS.md)** for latest results, **[`NEXT_STEPS_FOR_DEVELOPER.md`](./NEXT_STEPS_FOR_DEVELOPER.md)** for hand-off tasks, and the **Predictive Vision & Evolution Strategy** section in **[`CURRENT_STATUS.md`](./CURRENT_STATUS.md)** for the detailed predictive modeling implementation plan.

---

## Recent verification (2025-10-23)

- ✅ **Historical Archetype Features Generated**: 717 players across 2018-19 (234), 2020-21 (229), and 2021-22 (254) seasons using season-specific tables
- ✅ **Script Enhancement**: Modified `generate_archetype_features.py` to handle historical data with proper missing value imputation
- ✅ **Possessions Collection Started**: 45.9% complete for 2018-19 season (602/1,312 games = 286,012 possessions)
- ✅ **Cache System Operational**: 93 MB API response cache built (9,726 files) for efficient data collection
- ✅ **Data Quality Maintained**: All generated data passes validation checks and consistency requirements
- 2022-23 DARKO ratings are present in `PlayerSeasonSkill` (549 rows).
- `production_bayesian_data.csv` and `stratified_sample_10k.csv` include the required Z-matrix columns (`z_off_*`, `z_def_*`) aggregated by archetype.
- A Stan smoke test on the 10k sample completed end-to-end and produced outputs in `stan_model_results/`, `model_coefficients_sample.csv`, and `stan_model_report.txt`.

### Quick verification (current progress)

```bash
# Check historical possessions collection progress
python3 -c "
import sqlite3
conn = sqlite3.connect('src/nba_stats/db/nba_stats.db')
cursor = conn.cursor()
print('=== CURRENT POSSESSIONS PROGRESS ===')
cursor.execute('''
    SELECT g.season, COUNT(DISTINCT p.game_id) as games, COUNT(p.game_id) as possessions
    FROM Possessions p
    JOIN Games g ON p.game_id = g.game_id
    WHERE g.season IN (\"2018-19\", \"2020-21\", \"2021-22\")
    GROUP BY g.season
    ORDER BY g.season
''')
for season, games, possessions in cursor.fetchall():
    print(f'{season}: {games} games, {possessions:,} possessions')
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