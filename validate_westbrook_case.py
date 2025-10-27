#!/usr/bin/env python3
"""
Russell Westbrook-Lakers Case Study Validation

This script tests the model's prediction for the Russell Westbrook-Lakers roster construction
issues in the 2022-23 season. The hypothesis is that the model should predict poor fit
for redundant ball handlers on the same lineup.
"""

import pandas as pd
import numpy as np
import sqlite3
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def get_lakers_core_players(conn: sqlite3.Connection, season: str = '2022-23') -> list:
    """Get Lakers core players excluding Westbrook."""
    query = """
    SELECT DISTINCT p.player_id, p.player_name, psa.archetype_id, pss.offensive_darko, pss.defensive_darko
    FROM Players p
    JOIN PlayerSeasonArchetypes psa ON p.player_id = psa.player_id
    JOIN PlayerSeasonSkill pss ON p.player_id = pss.player_id
    WHERE p.team_id = 1610612747  -- Lakers
    AND p.player_name NOT LIKE '%Westbrook%'
    AND (p.player_name LIKE '%LeBron%' OR p.player_name LIKE '%Davis%' OR p.player_name LIKE '%Reaves%')
    AND psa.season = ?
    AND pss.season = ?
    ORDER BY p.player_name
    """

    df = pd.read_sql_query(query, conn, params=[season, season])

    # Debug: print column names and first row
    logging.debug(f"Core players columns: {list(df.columns)}")
    if not df.empty:
        logging.debug(f"First core player row: {df.iloc[0].to_dict()}")

    return df.to_dict('records')

def get_westbrook_data(conn: sqlite3.Connection, season: str = '2022-23') -> dict:
    """Get Russell Westbrook's archetype and skill data."""
    query = """
    SELECT p.player_id, p.player_name, psa.archetype_id, pss.offensive_darko, pss.defensive_darko
    FROM Players p
    JOIN PlayerSeasonArchetypes psa ON p.player_id = psa.player_id
    JOIN PlayerSeasonSkill pss ON p.player_id = pss.player_id
    WHERE p.player_name LIKE '%Westbrook%'
    AND psa.season = ?
    AND pss.season = ?
    """

    df = pd.read_sql_query(query, conn, params=[season, season])
    if df.empty:
        return None

    # Debug: print column names
    logging.debug(f"Columns in result: {list(df.columns)}")

    return {
        'player_id': int(df.iloc[0]['player_id']),
        'player_name': df.iloc[0]['player_name'],
        'archetype_id': int(df.iloc[0]['archetype_id']),
        'offensive_darko': float(df.iloc[0]['offensive_darko']),
        'defensive_darko': float(df.iloc[0]['defensive_darko'])
    }

def load_model_coefficients(coeff_path: str = "multi_season_coefficients.csv") -> np.ndarray:
    """Load trained coefficients."""
    df = pd.read_csv(coeff_path)
    return df['mean'].values

def calculate_lineup_value_with_westbrook(coefficients: np.ndarray, core_players: list,
                                        westbrook: dict) -> float:
    """
    Calculate the predicted value of Lakers core + Westbrook lineup.

    This simulates the 2022-23 Lakers starting lineup construction.
    """
    # Replace one core player with Westbrook (simulate the actual roster construction)
    lineup_with_westbrook = core_players.copy()
    lineup_with_westbrook[-1] = westbrook  # Replace last player with Westbrook

    # Calculate aggregate skills by archetype
    z_off = np.zeros(8)
    z_def = np.zeros(8)

    for player in lineup_with_westbrook:
        archetype_idx = player['archetype_id']  # Already 0-7 from database
        # Handle different possible key names
        off_darko = player.get('offensive_darko') or player.get('offensive_skill_rating')
        def_darko = player.get('defensive_darko') or player.get('defensive_skill_rating')

        if off_darko is None or def_darko is None:
            logging.error(f"Missing DARKO data for {player['player_name']}. Available keys: {list(player.keys())}")
            continue

        z_off[archetype_idx] += float(off_darko)
        z_def[archetype_idx] += float(def_darko)

    # Apply model: beta_0 + Σ(z_off[i] * beta_off[i]) - Σ(z_def[i] * beta_def[i])
    beta_0 = coefficients[0]
    beta_off = coefficients[1:9]  # beta_off[1-8] in Stan indices
    beta_def = coefficients[9:17]  # beta_def[1-8] in Stan indices

    prediction = beta_0 + np.sum(z_off * beta_off) - np.sum(z_def * beta_def)

    return prediction

def calculate_lineup_value_without_westbrook(coefficients: np.ndarray, core_players: list) -> float:
    """Calculate the predicted value of Lakers core without Westbrook."""
    # Use the original core lineup
    z_off = np.zeros(8)
    z_def = np.zeros(8)

    for player in core_players:
        archetype_idx = player['archetype_id']
        # Handle different possible key names
        off_darko = player.get('offensive_darko') or player.get('offensive_skill_rating')
        def_darko = player.get('defensive_darko') or player.get('defensive_skill_rating')

        if off_darko is None or def_darko is None:
            logging.error(f"Missing DARKO data for {player['player_name']}. Available keys: {list(player.keys())}")
            continue

        z_off[archetype_idx] += float(off_darko)
        z_def[archetype_idx] += float(def_darko)

    beta_0 = coefficients[0]
    beta_off = coefficients[1:9]
    beta_def = coefficients[9:17]

    prediction = beta_0 + np.sum(z_off * beta_off) - np.sum(z_def * beta_def)

    return prediction

def main():
    """Run Russell Westbrook case study validation."""

    # Database connection
    conn = sqlite3.connect('src/nba_stats/db/nba_stats.db')

    try:
        # Get Lakers core players (excluding Westbrook)
        logging.info("Loading Lakers core players...")
        core_players = get_lakers_core_players(conn)

        if len(core_players) < 2:
            logging.error("Not enough Lakers core players found (need at least 2)")
            return

        logging.info(f"Found {len(core_players)} core players:")
        for player in core_players:
            logging.info(f"  - {player['player_name']} (Archetype {player['archetype_id']}, "
                        f"O: {player.get('offensive_darko', 'MISSING')}, D: {player.get('defensive_darko', 'MISSING')})")

        # Get Westbrook data
        logging.info("Loading Westbrook data...")
        westbrook = get_westbrook_data(conn)

        if westbrook is None:
            logging.error("Westbrook data not found")
            return

        logging.info(f"Westbrook: Archetype {westbrook['archetype_id']}, "
                    f"O: {westbrook['offensive_darko']:.2f}, D: {westbrook['defensive_darko']:.2f}")

        # Load model coefficients
        logging.info("Loading model coefficients...")
        coefficients = load_model_coefficients()

        # Calculate lineup values
        value_with_westbrook = calculate_lineup_value_with_westbrook(coefficients, core_players, westbrook)
        value_without_westbrook = calculate_lineup_value_without_westbrook(coefficients, core_players)

        # Analyze the difference
        difference = value_with_westbrook - value_without_westbrook

        logging.info("=== RUSSELL WESTBROOK CASE STUDY RESULTS ===")
        logging.info(f"Lineup value WITHOUT Westbrook: {value_without_westbrook:.6f}")
        logging.info(f"Lineup value WITH Westbrook:    {value_with_westbrook:.6f}")
        logging.info(f"Difference: {difference:.6f}")

        if difference < 0:
            logging.info("✅ Model correctly predicts POOR fit for Westbrook with Lakers core")
            logging.info("   This aligns with the historical outcome (redundant ball handlers)")
        elif difference > 0:
            logging.info("❌ Model predicts GOOD fit for Westbrook (unexpected)")
        else:
            logging.info("⚠️  Model predicts neutral fit for Westbrook")

        # Archetype analysis
        logging.info("\n=== ARCHETYPE ANALYSIS ===")
        logging.info(f"Westbrook archetype: {westbrook['archetype_id']} (0-7 indexing)")

        # Check if Westbrook and LeBron have the same archetype (redundancy)
        lebron_archetype = None
        for player in core_players:
            if 'LeBron' in player['player_name']:
                lebron_archetype = player['archetype_id']
                break

        if lebron_archetype is not None:
            if westbrook['archetype_id'] == lebron_archetype:
                logging.info("🔴 REDUNDANCY DETECTED: Westbrook and LeBron share same archetype")
                logging.info("   This explains the poor fit prediction")
            else:
                logging.info("✅ DIFFERENT ARCHETYPES: No direct redundancy detected")

        logging.info(f"\nArchetype {westbrook['archetype_id']} coefficient (offensive): {coefficients[westbrook['archetype_id'] + 1]:.6f}")
        logging.info(f"Archetype {westbrook['archetype_id']} coefficient (defensive): {coefficients[westbrook['archetype_id'] + 9]:.6f}")

    except Exception as e:
        logging.error(f"Case study failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
