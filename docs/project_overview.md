# Project Overview: Algorithmic NBA Player Acquisition

This document provides a comprehensive overview of the "Algorithmic NBA Player Acquisition" project, based on the foundational research paper by Brill, Hughes, and Waldbaum. The goal of this project is to create a sophisticated system for evaluating NBA player acquisitions that prioritizes team **fit** over individual skill alone.

## Core Concepts

The model is built on the premise that a player's value is deeply contextual. It depends not only on their talent but also on their specific role and how that role interacts with the roles of their teammates and opponents.

### 1. Player Archetypes ✅ **IMPLEMENTED**

To capture a player's on-court role, the system categorizes every player into one of **three distinct archetypes** based on rigorous data analysis. These are not traditional positions (PG, SG) but are instead based on playstyle, determined using PCA-based feature engineering and multi-metric clustering evaluation.

- **How it Works**: Players are clustered using K-means algorithm on PCA-transformed features derived from 48 advanced statistics. The analysis revealed that k=3 with PCA (80% variance) provides optimal basketball-meaningful separation.

- **The 3 Implemented Archetypes**:
  1. **Big Men** (51 players, 18.7%): High height, wingspan, frontcourt presence, paint touches
     - *Examples*: Jonas Valančiūnas, Anthony Davis, Rudy Gobert, Giannis Antetokounmpo
  2. **Primary Ball Handlers** (86 players, 31.5%): High usage, driving ability, playmaking skills
     - *Examples*: LeBron James, Stephen Curry, Kevin Durant, James Harden
  3. **Role Players** (136 players, 49.8%): Balanced contributors, catch-and-shoot ability, defensive presence
     - *Examples*: Al Horford, Brook Lopez, Nicolas Batum, Jrue Holiday

### 2. Lineup Superclusters

Just as individual players have archetypes, five-player lineups have collective strategies. The model identifies **six "superclusters"** to represent the tactical style of a lineup.

- **How it Works**: Using K-means clustering on lineup-level statistics, the model groups lineups based on their shared strategic characteristics (e.g., pace, three-point attempt rate, shot creation style).

- **The 6 Superclusters**:
  1. Three-Point Symphony
  2. Half-Court Individual Shot Creators
  3. Slashing Offenses
  4. All-Around with Midrange
  5. Chaos Instigators
  6. Up-Tempo Distributors

### 3. Bayesian Possession-level Modeling

The core of the analysis is a Bayesian regression model that predicts the outcome (in expected net points) of a single NBA possession.

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
