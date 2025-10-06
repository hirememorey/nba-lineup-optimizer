# Project Overview: Algorithmic NBA Player Acquisition

This document provides a comprehensive overview of the "Algorithmic NBA Player Acquisition" project, based on the foundational research paper by Brill, Hughes, and Waldbaum. The goal of this project is to create a sophisticated system for evaluating NBA player acquisitions that prioritizes team **fit** over individual skill alone.

## Core Concepts

The model is built on the premise that a player's value is deeply contextual. It depends not only on their talent but also on their specific role and how that role interacts with the roles of their teammates and opponents.

### 1. Player Archetypes 🎯 **k=8 SYSTEM TARGET**

**Current State**: The system currently uses k=3 archetypes (Big Men, Primary Ball Handlers, Role Players) but is transitioning to k=8 for richer analysis.

**Target k=8 Archetypes** (Ready for implementation):
  1. **Scoring Wings**
  2. **Non-Shooting, Defensive Minded Bigs**
  3. **Offensive Minded Bigs**
  4. **Versatile Frontcourt Players**
  5. **Offensive Juggernauts**
  6. **3&D Players**
  7. **Defensive Minded Guards**
  8. **Playmaking, Initiating Guards**

**Why k=8 is Essential**: The k=8 system captures the rich diversity of NBA playstyles needed for meaningful lineup comparison, player swapping analysis, and data-driven basketball intelligence.

### 2. Lineup Superclusters 🔄 **BEING REDESIGNED**

The current supercluster system is being redesigned as part of the transition to k=8 archetypes. The previous k=2 system will be replaced with a new methodology.

- **Current State**: Previous k=2 supercluster system (Balanced vs Specialized lineups) is being phased out
- **Next Phase**: New supercluster methodology will be developed alongside k=8 archetype implementation
- **Rationale**: The k=2 system was based on k=3 archetypes and needs to be redesigned for k=8

### 3. Bayesian Possession-Level Modeling ✅ **IMPLEMENTED**

The core analytical engine that estimates the value of different player combinations in specific matchups.

- **How it Works**: Uses Bayesian regression to model possession outcomes based on the interaction between offensive and defensive lineup superclusters and individual player skills (DARKO ratings).

- **Model Specification**:
  ```
  E[y_i] = β_0,m_i + Σ_a β^off_a,m_i * Z^off_ia - Σ_a β^def_a,m_i * Z^def_ia
  ```
  Where:
  - `y_i` is the expected net points for possession i
  - `m_i` is the matchup (offensive supercluster, defensive supercluster)
  - `a` is the archetype (k=8 system: Scoring Wings, Defensive Bigs, etc.)
  - `Z^off_ia` and `Z^def_ia` are aggregated skill ratings by archetype
  - `β` coefficients are estimated using MCMC sampling

- **Implementation Status**:
  - ✅ Data preparation pipeline completed
  - ✅ PyMC prototype model validated (excellent convergence)
  - ✅ Statistical scaling analysis completed
  - 🔄 Production Stan model ready for implementation

### 4. Player Acquisition and Lineup Valuation

The model estimates a player's impact based on their offensive and defensive skill (using the DARKO metric), but critically, it weights this skill based on the full context of the possession:
- The player's own **archetype**.
- The **supercluster** of their offensive lineup.
- The **supercluster** of the opposing defensive lineup.

This approach allows the model to capture nuanced interactions. For example, it can recognize that adding another "Playmaking, Initiating Guard" to a lineup already featuring a ball-dominant "Offensive Juggernaut" may yield diminishing returns.

### 4. Player Acquisition and Lineup Valuation

The ultimate goal is to provide actionable recommendations for player acquisition.

- **Lineup Value**: A lineup's overall value is calculated by simulating its performance (both on offense and defense) against a baseline of the previous season's playoff teams. This ensures that lineup construction is optimized for high-level competition.
- **Acquisition Tool**: The system can take a core of four players and search through a list of available free agents to find the fifth player who maximizes the new lineup's projected value, taking both skill and team fit into account.

This methodology provides a powerful, data-driven framework for roster construction that moves beyond simple player rankings and embraces the complex, interactive nature of basketball.

## Data Integrity and Reconciliation

The project includes a comprehensive data reconciliation system to ensure 100% coverage of player salary and skill data:

- **Enhanced Reconciliation Tool**: Interactive system that handles both name mapping and player creation
- **Fuzzy Matching**: Intelligent suggestions for resolving name discrepancies
- **NBA API Integration**: Automatic creation of missing players via official NBA data
- **Persistent Mapping**: Reusable mapping file for consistent data across seasons

For detailed instructions on achieving 100% data integrity, see `docs/data_reconciliation_guide.md`.
