# Essential Documentation for New Developers

**Last Updated**: October 6, 2025

## Quick Start Path for New Developers

### 1. **Start Here** - Project Overview
- **[README.md](README.md)** - Main project overview, current status, and quick start
- **[CURRENT_STATUS.md](CURRENT_STATUS.md)** - Detailed current state and next steps

### 2. **Understand the Vision** - Core Concepts  
- **[GROUND_TRUTH_VALIDATION_RESULTS.md](GROUND_TRUTH_VALIDATION_RESULTS.md)** - **CRITICAL**: Ground truth validation results and methodology
- **[DATA_DRIVEN_APPROACH.md](DATA_DRIVEN_APPROACH.md)** - Ground truth validation implementation plan
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

### **Current State** (January 3, 2025)
- ✅ **Phase 1 Complete**: Fan-friendly interface, production system, data pipeline, DARKO integration, salary data
- ✅ **Ground Truth Validation Complete**: Core basketball principles validated, custom 2022-23 evaluator built
- 🎯 **NEW APPROACH**: Case Study Archive validation strategy based on post-mortem analysis
- 📊 **Data Ready**: 534 players with complete 2022-23 data, 549 DARKO ratings, 459 salary records
- 🎯 **Next Phase**: Implement Case Study Archive with betting market analysis (2017-2025)

### **Critical Understanding**
- **NEW: Case Study Archive Approach**: Basketball-first validation using historical data (2017-2025)
- **Post-Mortem Insights**: Basketball is unpredictable - focus on patterns, not predictions
- **Betting Market Analysis**: Use betting market movements as primary indicator of expectations
- **Glass Box Advisor**: Separate quantitative analysis from qualitative risk flags
- **Pattern Recognition**: Look for correlations across historical cases, not single causes

### **Next Steps**
1. Read **[CASE_STUDY_ARCHIVE_IMPLEMENTATION.md](CASE_STUDY_ARCHIVE_IMPLEMENTATION.md)** for the new basketball-first approach
2. Review **[CURRENT_STATUS.md](CURRENT_STATUS.md)** for updated project status and post-mortem insights
3. Start with Phase 1: Historical database construction (2017-2025 cases)
4. Implement betting market analysis for Hype Score calculation
5. Build pattern recognition engine for correlation analysis

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
