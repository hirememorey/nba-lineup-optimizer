# Metric Investigation Summary - October 1, 2025

This document summarizes the findings from the investigation into the seven missing canonical metrics required for the player archetype analysis. The investigation followed a `curl`-first, manual validation approach, prioritizing ground truth and minimizing unnecessary automation.

## Summary of Findings

| Metric      | Status        | Source                                                                      | Notes                                                                                                                                                                                                                                                             |
| :---------- | :------------ | :-------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AVGDIST`   | **Derivable** | `shotchartdetail` API endpoint                                              | The endpoint returns a `SHOT_DISTANCE` field for every shot. This metric can be calculated by averaging this value across all shots for a player in a season.                                                                                                         |
| `Zto3r`     | **Derivable** | `shotchartdetail` API endpoint                                              | The endpoint returns a `SHOT_ZONE_RANGE` field (e.g., "Less than 8 ft.", "8-16 ft."). The required metric can be calculated by creating a frequency distribution of shots falling into the "0-3 ft" range. A validation step against a public source is required. |
| `THto10r`   | **Derivable** | `shotchartdetail` API endpoint                                              | Derivable from the `SHOT_ZONE_RANGE` field by calculating the frequency of shots in the "3-10 ft" range.                                                                                                                                                     |
| `TENto16r`  | **Derivable** | `shotchartdetail` API endpoint                                              | Derivable from the `SHOT_ZONE_RANGE` field by calculating the frequency of shots in the "10-16 ft" range.                                                                                                                                                    |
| `SIXTto3PTr`| **Derivable** | `shotchartdetail` API endpoint                                              | Derivable from the `SHOT_ZONE_RANGE` field by calculating the frequency of shots in the "16-24 ft" range.                                                                                                                                                    |
| `HEIGHT`    | **Found**     | `commonplayerinfo` API endpoint                                             | The endpoint returns a `HEIGHT` field with a string value (e.g., "6-9"). This can be parsed and stored.                                                                                                                                                     |
| `WINGSPAN`  | **Unavailable** | Not found in any investigated API endpoint (`shotchartdetail`, `commonplayerinfo`). | This metric is not available via the NBA Stats API. Sourcing it will require integrating an external dataset, likely from NBA Draft Combine records.                                                                                                                 |

### Critical Technical Requirement: Request Headers

The investigation definitively concluded that the NBA Stats API now enforces a strict header validation policy. **Successful requests require the full, modern, browser-generated set of headers.** Attempts to use a minimal or incomplete set of headers result in timeouts or failed requests. All future API calls must use this comprehensive header set for reliability.

## Proposed Implementation Plan

Based on these findings, the following implementation is recommended:

1.  **Update the Core API Client (`src/nba_stats/api/nba_stats_client.py`):**
    *   Create a new, private method that returns the full, validated dictionary of required headers.
    *   Update the existing methods (`get`, `post`) within the client to use these new headers for all outgoing requests. This is a necessary global change to ensure all API calls are compliant.

2.  **Create a New Metric Derivation Script (`src/nba_stats/scripts/populate_player_shot_metrics.py`):**
    *   This script will be responsible for fetching the detailed shot chart data for all players for a given season using a new method in the API client.
    *   It will calculate the five derivable metrics (`AVGDIST`, `Zto3r`, etc.).
    *   **Crucially, it must include a validation step:** For a small, static set of well-known players, it will compare its calculated values against the publicly available data on a site like Basketball-Reference.com to ensure methodological correctness.
    *   The script will then save these derived metrics to a new table in the database (e.g., `PlayerSeasonDerivedShotStats`).

3.  **Enhance the Player Population Script:**
    *   The existing script that populates the core player data (`populate_players.py` or similar) will be modified.
    *   It will now also call the `commonplayerinfo` endpoint to fetch and store the `HEIGHT` for each player in the appropriate table.

4.  **Defer `WINGSPAN` Integration:**
    *   The effort required to find, validate, and integrate an external dataset for `WINGSPAN` is non-trivial. It involves a separate ingestion pipeline and a new name reconciliation process.
    *   It is recommended to **defer** this task and proceed with the 47 out of 48 canonical metrics that are now attainable. The model can be successfully built with this slightly reduced feature set, and `WINGSPAN` can be added in a future iteration if deemed critical.

This plan surgically addresses the missing metrics, ensures data quality through validation, and makes a pragmatic decision to defer the highest-effort task, allowing the project to move forward efficiently.
