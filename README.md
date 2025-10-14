# NBA Lineup Optimizer

This project implements the methodology from the research paper "Algorithmic NBA Player Acquisition" by Brill, Hughes, and Waldbaum. It uses a data-driven approach to NBA player acquisition and lineup optimization, prioritizing team **fit** over individual skill alone.

**Vision**: A fan-friendly tool that helps NBA fans understand which players would fit best on their favorite teams.

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

**Date**: October 10, 2025
**Status**: ✅ **BAYESIAN DATA PREP COMPLETE; READY TO TRAIN** — Superclusters regenerated using the full 18 validated features (no fallback).

We completed hardened Bayesian data preparation and produced training files:
- `production_bayesian_data.csv` (627,969 rows)
- `stratified_sample_10k.csv`
- Supercluster artifacts (`robust_scaler.joblib`, `kmeans_model.joblib`, CSV) regenerated. Four lineup Scoring share fields are now included via ingestion mapping fix: `pct_fga_2pt`, `pct_fga_3pt`, `pct_pts_2pt_mr`, `pct_pts_3pt` (coverage ~2,000/4,968 rows in 2022‑23, yielding 21 complete rows for validated clustering).

**Next Phase**: Train the Bayesian Stan model and validate against the paper’s examples. See **[`CURRENT_STATUS.md`](./CURRENT_STATUS.md)** for details and next steps.