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
**Status**: 🚀 **SUPERCLUSTER PIPELINE VALIDATED & BUILT** - Data Foundation Rebuilt.

A critical data quality disaster in the `PlayerLineupStats` table has been identified and fixed through a rigorous, "profile-first" data archaeology approach. The project now has a robust, validated pipeline for generating lineup superclusters.

**Next Phase**: The immediate priority is to train the Bayesian model using the high-integrity data produced by the new pipeline. For a detailed breakdown, please see **[`CURRENT_STATUS.md`](./CURRENT_STATUS.md)**. 