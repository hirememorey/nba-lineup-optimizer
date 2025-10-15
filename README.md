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

**Date**: October 15, 2025
**Status**: ✅ **MODEL TRAINED; READY FOR PAPER VALIDATION** — Training completed with strong convergence. Coefficients saved to `model_coefficients.csv` and a summary report is available in `stan_model_report.txt`.

**Next Phase**: Implement the paper-case validator (Lakers, Pacers, Suns) using `model_coefficients.csv`. See **[`CURRENT_STATUS.md`](./CURRENT_STATUS.md)** for artifacts and **[`NEXT_STEPS_FOR_DEVELOPER.md`](./NEXT_STEPS_FOR_DEVELOPER.md)** for the exact steps/CLI.