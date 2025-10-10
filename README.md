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
**Status**: 🚀 **BAYESIAN MODEL IMPLEMENTATION** - Core Data Pipeline Repaired. Test Harness Built.

A critical, silent bug in the core data pipeline has been fixed, and the `PlayerLineupStats` table is now correctly populated. We have pivoted to a test-driven approach for the final modeling phase to ensure data integrity.

**Next Phase**: The immediate priority is to use the newly built integration test harness to drive the implementation of the lineup supercluster and Bayesian data preparation scripts. For a detailed breakdown, please see **[`CURRENT_STATUS.md`](./CURRENT_STATUS.md)**. 