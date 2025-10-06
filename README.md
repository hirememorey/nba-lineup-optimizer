# NBA Lineup Optimizer

This project implements the methodology from the research paper "Algorithmic NBA Player Acquisition" by Brill, Hughes, and Waldbaum. It uses a data-driven approach to NBA player acquisition and lineup optimization, prioritizing team **fit** over individual skill alone.

**Vision**: A fan-friendly tool that helps NBA fans understand which players would fit best on their favorite teams, with real-world examples like why Russell Westbrook struggled with the Lakers but succeeded with the Clippers and Nuggets. The system will eventually expand to evaluate G-League players for finding hidden gems and role players.

The project has recently undergone a complete architectural redesign based on first-principles reasoning and is now production-ready with a solid foundation for fan-friendly enhancements.

## Current Status

**Date**: October 4, 2025  
**Status**: 🎯 **PHASE 1 READY** - Data-Driven Approach Implementation

The NBA Lineup Optimizer has completed its foundational infrastructure and is ready to implement a data-driven approach based on real possession data analysis. The system will discover basketball intelligence from actual NBA data rather than using arbitrary mathematical parameters.

### What's Working Now ✅
- **Fan-Friendly Dashboard**: Intuitive interface with team selection and player search
- **Basketball Language**: Uses positions (PG, SG, SF, PF, C) and roles instead of technical archetypes
- **Player Search**: Name-based search with instant fit analysis
- **Team Analysis**: Roster display with position balance and needs identification
- **Free Agent Recommendations**: Team-specific player recommendations with basketball explanations
- **Production Dashboard**: Web interface with authentication and data-driven models
- **Data Pipeline**: 651 players with complete archetype assignments and 574,357 possessions
- **Robust Infrastructure**: Complete data pipeline, validation framework, and production system

### Next Phase: Data-Driven Basketball Intelligence 🎯
- **Real Data Analysis**: Study our 574,357 possessions to discover actual basketball patterns
- **Calculate Real Performance Differences**: Find actual diminishing returns from data
- **Build Grounded Models**: Replace arbitrary penalties with real performance-based logic
- **Live System**: Use 2024-25 data for real-time relevance during the 2025-26 season

### Production System ✅
- **Production Dashboard**: Complete web application with authentication, user management, and monitoring
- **Admin Panel**: Administrative interface for user management, data export, and system monitoring
- **User Onboarding**: Interactive tutorial system and user analytics
- **Model Switching**: Seamless toggle between production and original models
- **Data Protection**: Encryption, audit logging, and secure data handling
- **Error Handling**: Comprehensive monitoring, alerting, and error recovery

### Data Pipeline ✅
- **Complete Data Coverage**: 651 players with 100% archetype coverage and fallback assignments
- **Possession Data**: 574,357 possessions with complete lineup data
- **Advanced Metrics**: 100% coverage for 48 canonical features
- **Robust Pipeline**: Reliable and resumable data collection system

### Model Performance ✅
- **Data-Driven Approach**: Ready to implement real basketball intelligence from possession data
- **Real Pattern Discovery**: Analyze 574,357 possessions to discover actual basketball patterns
- **Model Integration**: Unified interface ready for data-driven models

## Getting Started

### Prerequisites

*   Python 3.9+ (for production features)
*   Docker and Docker Compose (for containerized deployment)
*   Git

### Quick Start (Fan-Friendly Dashboard) 🏀

**For NBA fans who want to explore player-team fit:**

```bash
# Start the fan-friendly dashboard
python run_fan_dashboard.py

# Access at http://localhost:8501
```

**Features:**
- Select any of 30 NBA teams
- Search players by name
- Get basketball-intuitive fit explanations
- View free agent recommendations
- Analyze team roster balance

### Quick Start (Production Deployment)

#### Option 1: Docker Deployment (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-repo/nba-lineup-optimizer.git
cd nba-lineup-optimizer

# Deploy the complete production system
docker-compose up -d

# Check logs
docker-compose logs -f

# Access dashboard at http://localhost:8502
```

#### Option 2: Direct Python Deployment

```bash
# Clone and setup
git clone https://github.com/your-repo/nba-lineup-optimizer.git
cd nba-lineup-optimizer

# Install dependencies
pip install -r requirements.txt
pip install -r requirements_streamlit.txt

# Run production system
python run_production.py
```

### Default Credentials

- **Admin**: `admin` / `admin123`
- **User**: `user` / `user123`

⚠️ **Change these passwords in production!**

### Production Features

The production system includes:

- **🔐 Authentication**: Multi-user system with role-based access
- **📊 User Analytics**: Track user behavior and feature usage
- **🛡️ Data Protection**: Encryption and comprehensive audit logging
- **📈 Monitoring**: Real-time system health and performance metrics
- **👥 User Management**: Admin panel for user and system management
- **📚 Onboarding**: Interactive tutorial and user guidance
- **🔄 Model Switching**: Seamless toggle between production and original models

### Data Pipeline Setup

Before using the production system, ensure the data pipeline is complete:

```bash
# Verify database status
python verify_database_sanity.py

# Expected output: "🎉 ALL CRITICAL VERIFICATIONS PASSED"

# Generate model coefficients (if not already done)
python run_production_model.py
```

### Development Mode

For development and testing:

```bash
# Set environment to development
export ENVIRONMENT=development
export ENABLE_AUTH=false

# Run production dashboard
python production_dashboard.py
```

### Using Data-Driven Models in Code

```python
from data_analysis.data_driven_model_evaluator import DataDrivenModelEvaluator

# Create data-driven evaluator
evaluator = DataDrivenModelEvaluator("src/nba_stats/db/nba_stats.db")

# Evaluate lineup using real possession data
result = evaluator.evaluate_lineup([2544, 101108, 201142, 201143, 201144])
print(f"Predicted outcome: {result.predicted_outcome}")
print(f"Confidence: {result.confidence}")
print(f"Breakdown: {result.breakdown}")
```

## Roadmap

### **🎯 Phase 1: Data-Driven Model Implementation (CURRENT PRIORITY)**

**Status**: 🚀 **READY TO IMPLEMENT** - Data-Driven Approach

**Implementation Plan**: Build basketball intelligence from real possession data analysis:

- [ ] **PRIORITY 1**: Analyze 574,357 possessions to discover real basketball patterns
- [ ] **PRIORITY 2**: Calculate actual performance differences from data
- [ ] **PRIORITY 3**: Build grounded models based on real basketball insights
- [ ] **PRIORITY 4**: Implement k=8 archetype system for richer lineup analysis
- [ ] **PRIORITY 5**: Validate against current NBA examples with data-driven approach

### **Phase 2: Enhanced Fan Interface (After data-driven models)**
- Starting lineup display with real performance metrics
- Player swapping interface with real-time impact analysis
- Side-by-side lineup comparison functionality
- Real-time updates as 2025-26 season progresses

### **Phase 3: Advanced Features (Future)**
- G-League player integration for finding hidden gems
- Historical analysis and case studies
- Team-specific strategy recommendations
- Advanced analytics dashboard

## Documentation

### **Current Status & Quick Start**
- **`CURRENT_STATUS.md`**: Detailed current status and technical implementation details
- **`QUICK_START_GUIDE.md`**: Step-by-step instructions for getting started
- **`FAN_FRIENDLY_README.md`**: Guide for the fan-friendly dashboard

### **Technical Documentation**
- **`docs/project_overview.md`**: Core concepts from the source research paper
- **`docs/architecture.md`**: System design principles and architectural decisions
- **`docs/data_dictionary.md`**: Complete database schema reference
- **`DATA_DRIVEN_APPROACH.md`**: Data-driven basketball intelligence implementation guide

### **Implementation History**
- **`docs/archive/`**: Archived implementation documents and historical analysis 