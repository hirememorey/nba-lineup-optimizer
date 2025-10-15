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
**Status**: ✅ **VALIDATION COMPLETE; MODEL VALIDATED** — All three case studies (Lakers, Pacers, Suns) now pass validation. The model is working correctly and ready for production use.

**Validation Results**: All three case studies now pass validation consistently:
- **Lakers**: ✅ PASS (5/5 preferred, 100%) - Model recommends "Playmaking, Initiating Guards"
- **Pacers**: ✅ PASS (4/5 preferred, 80%) - Model recommends defensive players
- **Suns**: ✅ PASS (5/5 preferred, 100%) - Model recommends "Offensive Minded Bigs"

**Next Phase**: Production deployment and user interface development.
See **[`CURRENT_STATUS.md`](./CURRENT_STATUS.md)** for latest results and **[`NEXT_STEPS_FOR_DEVELOPER.md`](./NEXT_STEPS_FOR_DEVELOPER.md)** for hand-off tasks.