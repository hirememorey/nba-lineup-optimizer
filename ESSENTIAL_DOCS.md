# Essential Documentation for New Developers

**Last Updated**: October 6, 2025

## Quick Start Path for New Developers

### 1. **Start Here** - Project Overview
- **[README.md](README.md)** - Main project overview, current status, and quick start
- **[CURRENT_STATUS.md](CURRENT_STATUS.md)** - Detailed current state and next steps

### 2. **Understand the Vision** - Core Concepts  
- **[DATA_DRIVEN_APPROACH.md](DATA_DRIVEN_APPROACH.md)** - **CRITICAL**: Ground truth validation implementation plan
- **[source_paper.md](source_paper.md)** - Original research paper by Brill, Hughes, and Waldbaum
- **[docs/project_overview.md](docs/project_overview.md)** - Core concepts and methodology

### 3. **Get Running** - Implementation
- **[QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)** - Step-by-step setup instructions
- **[FAN_FRIENDLY_README.md](FAN_FRIENDLY_README.md)** - Fan dashboard guide
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide

### 4. **Technical Reference** - System Details
- **[docs/architecture.md](docs/architecture.md)** - System design principles
- **[docs/data_dictionary.md](docs/data_dictionary.md)** - Database schema reference
- **[docs/production_features.md](docs/production_features.md)** - Production system features

### 5. **Methodology** - Technical Implementation
- **[docs/methodology/](docs/methodology/)** - Detailed methodology documentation
- **[docs/troubleshooting_data_quality.md](docs/troubleshooting_data_quality.md)** - Data quality troubleshooting

## Key Points for New Developers

### **Current State** (October 6, 2025)
- ✅ **Phase 1 Complete**: Fan-friendly interface, production system, data pipeline, DARKO integration, salary data
- 🎯 **Next Phase**: Implement k=8 archetype clustering and reproduce original paper
- 📊 **Data Ready**: 574,357 possessions (2024-25), 651 players, 100% coverage, 549 DARKO ratings (2022-23), 459 salary records (2022-23)

### **Critical Understanding**
- **Validation-First Approach**: Reproduce original paper with 2022-23 data to validate implementation
- **Ground Truth Validation**: Only way to know our implementation is correct
- **k=8 Archetype System**: Implement proven 8-archetype approach
- **Scale After Validation**: Apply validated methodology to current data

### **Next Steps**
1. Read **[DARKO_DATA_INTEGRATION_SUMMARY.md](DARKO_DATA_INTEGRATION_SUMMARY.md)** for DARKO integration details
2. Implement k=8 archetype clustering exactly as described in the original paper
3. Reproduce the Bayesian model with 2022-23 data
4. Validate against Lakers, Pacers, and Suns examples from paper

## Files Removed (Outdated)
- `IMPLEMENTATION_GUIDE.md` - Redundant with DATA_DRIVEN_APPROACH.md
- `VALIDATION_TOOLS_GUIDE.md` - Referenced old approach
- `DOCUMENTATION.md` - Redundant index file
- `docs/index.md` - Redundant index file
- `CRITICAL_DATA_MIGRATION_PLAN.md` - Contradicted data-driven approach
- `docs/stan_scaling_issues.md` - Referenced old model approach
- `docs/archive/` - Entire directory of outdated files

---

**Total Documentation**: 18 essential markdown files (down from 40+)
**Focus**: Data-driven basketball intelligence implementation
**Status**: Ready for new developer onboarding
