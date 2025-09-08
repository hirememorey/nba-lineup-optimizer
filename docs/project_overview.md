# Project Overview: Algorithmic NBA Player Acquisition

This document provides a comprehensive overview of the "Algorithmic NBA Player Acquisition" project, based on the foundational research paper by Brill, Hughes, and Waldbaum. The goal of this project is to create a sophisticated system for evaluating NBA player acquisitions that prioritizes team **fit** over individual skill alone.

## Core Concepts

The model is built on the premise that a player's value is deeply contextual. It depends not only on their talent but also on their specific role and how that role interacts with the roles of their teammates and opponents.

### 1. Player Archetypes

To capture a player's on-court role, the system categorizes every player into one of **eight distinct archetypes**. These are not traditional positions (PG, SG) but are instead based on playstyle.

- **How it Works**: Players are clustered using a K-means algorithm on a rich dataset of 48 advanced statistics. These stats are chosen to describe *how* a player plays (e.g., drive frequency, shot distance, time of possession) rather than *how well* they play.

- **The 8 Archetypes**:
  1. Scoring Wings
  2. Non-Shooting, Defensive Minded Bigs
  3. Offensive Minded Bigs
  4. Versatile Frontcourt Players
  5. Offensive Juggernauts
  6. 3&D
  7. Defensive Minded Guards
  8. Playmaking, Initiating Guards

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
