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
**Status**: ✅ **PHASE 1.4 PLAYER STATS COMPLETE; POSSESSIONS PENDING** — Historical player statistics collection complete for all three target seasons using corrected methodology (1,281 players total). All seasons now have complete, consistent datasets with realistic team distributions.

**Recent Achievement**: Successfully corrected data collection methodology and collected comprehensive player statistics:
- **2018-19**: 395 players with complete stats (was 254, +55% improvement)
- **2020-21**: 424 players with complete stats (was 423, complete dataset)
- **2021-22**: 462 players with complete stats (maintained quality)
- **Team Distribution**: All seasons now have realistic 8-22 players per team (was 4-15 for 2018-19)

**Next Phase**: Generate archetype features and collect play-by-play possession data to enable multi-season Bayesian model training.

**Predictive Vision**: The ultimate goal is to build a model that can predict the Russell Westbrook-Lakers failure *before* the 2022-23 season begins, transforming this from a historical analysis project into a true GM decision-making tool.

See **[`CURRENT_STATUS.md`](./CURRENT_STATUS.md)** for latest results, **[`NEXT_STEPS_FOR_DEVELOPER.md`](./NEXT_STEPS_FOR_DEVELOPER.md)** for hand-off tasks, and the **Predictive Vision & Evolution Strategy** section in **[`CURRENT_STATUS.md`](./CURRENT_STATUS.md)** for the detailed predictive modeling implementation plan.

---

## Recent verification (2025-10-23)

- ✅ **Historical Player Stats Collection Corrected**: 1,281 players across 2018-19 (395), 2020-21 (424), and 2021-22 (462) seasons using proper API-based methodology
- ✅ **Critical Bug Fixed**: Replaced flawed "reference season" logic with direct API calls using 15-minute threshold (matching original paper approach)
- ✅ **Data Quality Improved**: All seasons now have realistic team distributions (8-22 players per team vs previous 4-15 range) and consistent methodology
- ✅ **Complete Coverage**: All 30 NBA teams represented in each season with proper roster sizes
- 2022-23 DARKO ratings are present in `PlayerSeasonSkill` (549 rows).
- `production_bayesian_data.csv` and `stratified_sample_10k.csv` include the required Z-matrix columns (`z_off_*`, `z_def_*`) aggregated by archetype.
- A Stan smoke test on the 10k sample completed end-to-end and produced outputs in `stan_model_results/`, `model_coefficients_sample.csv`, and `stan_model_report.txt`.

### Quick run (smoke test)

```bash
python3 train_bayesian_model.py \
  --data stratified_sample_10k.csv \
  --stan bayesian_model_k8.stan \
  --draws 100 --tune 100 --chains 1 \
  --coefficients model_coefficients_sample.csv
```

For a full run, switch to `--data production_bayesian_data.csv` and increase `--draws`, `--tune`, and `--chains`.