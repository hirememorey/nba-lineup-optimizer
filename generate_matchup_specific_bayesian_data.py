#!/usr/bin/env python3
"""
Generate Matchup-Specific Bayesian Training Data

This script prepares historical possession data for the enhanced Bayesian model with
matchup-specific parameters (36×16 architecture). Uses the new multi-season supercluster
model for consistent semantic definitions across all seasons.

This addresses the critical issue identified in the pre-mortem by using a semantically
stable supercluster model trained on pooled historical data.
"""

import os
import sqlite3
import json
import logging
from collections import defaultdict
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
DB_PATH = "src/nba_stats/db/nba_stats.db"
OUTPUT_CSV_PATH = "matchup_specific_bayesian_data.csv"
BATCH_SIZE = 50000

# Historical seasons to train on (excluding 2022-23 for validation)
TRAIN_SEASONS = ['2018-19', '2020-21', '2021-22']

# Model paths (from Phase 0)
SUPERCLUSTER_MODEL_PATH = "trained_models/multi_season_kmeans_model.joblib"
SUPERCLUSTER_SCALER_PATH = "trained_models/multi_season_robust_scaler.joblib"
ASSIGNMENT_MAP_PATH = "historical_lineup_features/multi_season_supercluster_assignments.json"

# Archetype CSV patterns
ARCHETYPE_CSV_PATTERNS = {
    '2018-19': 'player_archetypes_k8_2018-19.csv',
    '2020-21': 'player_archetypes_k8_2020-21.csv',
    '2021-22': 'player_archetypes_k8_2021-22.csv'
}

def _load_archetypes_for_season(season: str) -> dict:
    """Load archetype assignments from CSV, mapping IDs 1-8 to indices 0-7."""
    csv_path = ARCHETYPE_CSV_PATTERNS[season]
    if not os.path.exists(csv_path):
        logging.error(f"Archetypes CSV not found at {csv_path}")
        return {}

    df = pd.read_csv(csv_path)
    if not {'player_id','archetype_id'}.issubset(df.columns):
        logging.error("Archetypes CSV missing required columns: {'player_id','archetype_id'}")
        return {}

    # Map IDs 1-8 to indices 0-7 for internal use
    return pd.Series(df['archetype_id'].values - 1, index=df['player_id']).to_dict()

def _load_darko_for_season(season: str) -> dict:
    """Load DARKO ratings for a specific season."""
    ratings = {}
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(
            "SELECT player_id, offensive_darko, defensive_darko FROM PlayerSeasonSkill WHERE season=?",
            conn,
            params=(season,)
        )
        for _, r in df.iterrows():
            try:
                pid = int(r['player_id'])
            except Exception:
                continue
            ratings[pid] = {'o_darko': r['offensive_darko'], 'd_darko': r['defensive_darko']}
    except sqlite3.Error as e:
        logging.error(f"Error loading DARKO ratings for {season}: {e}")
    finally:
        if conn is not None:
            conn.close()
    return ratings

def _load_supercluster_models():
    """Load the multi-season supercluster model and scaler."""
    if not os.path.exists(SUPERCLUSTER_MODEL_PATH):
        raise FileNotFoundError(f"Supercluster model not found at {SUPERCLUSTER_MODEL_PATH}")

    if not os.path.exists(SUPERCLUSTER_SCALER_PATH):
        raise FileNotFoundError(f"Supercluster scaler not found at {SUPERCLUSTER_SCALER_PATH}")

    if not os.path.exists(ASSIGNMENT_MAP_PATH):
        raise FileNotFoundError(f"Assignment map not found at {ASSIGNMENT_MAP_PATH}")

    kmeans = joblib.load(SUPERCLUSTER_MODEL_PATH)
    scaler = joblib.load(SUPERCLUSTER_SCALER_PATH)

    with open(ASSIGNMENT_MAP_PATH, 'r') as f:
        assignment_map = json.load(f)

    logging.info(f"Loaded multi-season supercluster model (trained on {len(assignment_map['training_seasons'])} seasons)")
    logging.info(f"Model covers {assignment_map['num_lineup_combinations']} lineup combinations")

    return kmeans, scaler, assignment_map

def _extract_lineup_features(archetypes_list: list, season: str) -> dict:
    """Extract lineup features for clustering (must match the 14 features used in multi-season model)."""
    # The multi-season model was trained on these exact 14 features:
    # ['w_pct', 'plus_minus', 'off_rating', 'pace', 'ast_pct', 'ast_to',
    #  'pct_fga_2pt', 'pct_fga_3pt', 'pct_pts_2pt', 'pct_pts_2pt_mr',
    #  'pct_pts_3pt', 'pct_pts_ft', 'pct_pts_off_tov', 'pct_pts_paint']

    # For the prototype, we'll create reasonable estimates based on archetype composition
    # In production, these would be calculated from actual lineup performance data

    # Count archetypes by type
    archetype_counts = defaultdict(int)
    for arch in archetypes_list:
        if arch in [0, 1, 2]:  # Scoring/Offensive archetypes
            archetype_counts['offensive'] += 1
        elif arch in [3, 4, 5]:  # Balanced/Versatile archetypes
            archetype_counts['balanced'] += 1
        else:  # Defensive archetypes
            archetype_counts['defensive'] += 1

    total_players = len(archetypes_list)

    # Estimate features based on archetype composition (simplified approach)
    features = {
        'w_pct': 0.5,  # Neutral estimate
        'plus_minus': 0.0,  # Neutral estimate
        'off_rating': 100.0,  # League average
        'pace': 100.0,  # League average
        'ast_pct': min(archetype_counts['balanced'] / total_players * 50, 50),  # Assist percentage
        'ast_to': max(archetype_counts['balanced'] / max(archetype_counts['offensive'], 1) * 2, 1),  # Assist-to-turnover

        # Shot distribution (based on archetype types)
        'pct_fga_2pt': 60 + (archetype_counts['offensive'] * 10),  # Offensive players take more 2pt shots
        'pct_fga_3pt': 40 - (archetype_counts['offensive'] * 10),  # Offensive players take more 3pt shots

        # Points distribution (based on archetype types)
        'pct_pts_2pt': 50 + (archetype_counts['offensive'] * 15),
        'pct_pts_2pt_mr': 15,  # Estimate mid-range as portion of 2pt
        'pct_pts_3pt': 30 + (archetype_counts['offensive'] * 10),
        'pct_pts_ft': 20,  # League average
        'pct_pts_off_tov': 5,  # League average
        'pct_pts_paint': 40 + (archetype_counts['offensive'] * 10)  # Offensive players score more in paint
    }

    return features

def _get_supercluster_from_features(features: dict, kmeans, scaler) -> int:
    """Get supercluster assignment from lineup features."""
    try:
        # Convert features to array in the exact order expected by the multi-season model
        feature_order = ['w_pct', 'plus_minus', 'off_rating', 'pace', 'ast_pct', 'ast_to',
                        'pct_fga_2pt', 'pct_fga_3pt', 'pct_pts_2pt', 'pct_pts_2pt_mr',
                        'pct_pts_3pt', 'pct_pts_ft', 'pct_pts_off_tov', 'pct_pts_paint']

        feature_array = np.array([[features[f] for f in feature_order]])

        # Scale features using the multi-season scaler
        scaled_features = scaler.transform(feature_array)

        # Get cluster assignment
        cluster = kmeans.predict(scaled_features)[0]

        return cluster

    except Exception as e:
        logging.warning(f"Error getting supercluster: {e}")
        return 0  # Default to supercluster 0

def _calculate_matchup_id(off_supercluster: int, def_supercluster: int) -> int:
    """Calculate matchup_id (0-35) from offensive and defensive superclusters."""
    # 6 offensive superclusters × 6 defensive superclusters = 36 possible matchups
    # Use 0-based indexing: matchup_id = off_sc * 6 + def_sc
    matchup_id = off_supercluster * 6 + def_supercluster
    return matchup_id

def prepare_matchup_specific_bayesian_data():
    """Generate matchup-specific Bayesian training data."""
    logging.info("="*80)
    logging.info("PREPARING MATCHUP-SPECIFIC BAYESIAN DATASET")
    logging.info("="*80)

    # Load models and mappings
    try:
        kmeans, scaler, assignment_map = _load_supercluster_models()
    except FileNotFoundError as e:
        logging.error(f"Required model files not found: {e}")
        logging.error("Please run train_multi_season_supercluster_model.py first")
        return

    # Load all mappings
    archetype_maps = {}
    darko_maps = {}

    for season in TRAIN_SEASONS:
        logging.info(f"Loading mappings for {season}...")

        # Load archetypes
        arch_map = _load_archetypes_for_season(season)
        if arch_map:
            archetype_maps[season] = arch_map
            logging.info(f"  Loaded {len(arch_map)} archetype assignments")
        else:
            logging.error(f"  Failed to load archetypes for {season}")
            return

        # Load DARKO
        darko_map = _load_darko_for_season(season)
        if darko_map:
            darko_maps[season] = darko_map
            logging.info(f"  Loaded {len(darko_map)} DARKO ratings")
        else:
            logging.error(f"  Failed to load DARKO for {season}")
            return

    rows = []
    conn = None

    try:
        conn = sqlite3.connect(DB_PATH)

        # Process each training season
        for season in TRAIN_SEASONS:
            logging.info(f"\nProcessing {season}...")
            archetypes = archetype_maps[season]
            darko = darko_maps[season]

            # Query possessions for this season (limit for prototype)
            query = """
                SELECT p.*, g.season
                FROM Possessions p
                JOIN Games g ON p.game_id = g.game_id
                WHERE g.season = ?
                AND p.home_player_1_id IS NOT NULL
                AND p.away_player_1_id IS NOT NULL
                AND p.offensive_team_id IS NOT NULL
                AND p.offensive_team_id != ''
                LIMIT 10000  -- Limit for prototype testing
            """

            df = pd.read_sql_query(query, conn, params=(season,))
            logging.info(f"  Loaded {len(df)} possessions")

            season_rows = 0

            for idx, row in df.iterrows():
                try:
                    # Extract player IDs
                    home_players = [row[f'home_player_{i}_id'] for i in range(1, 6)]
                    away_players = [row[f'away_player_{i}_id'] for i in range(1, 6)]

                    # Skip if any players are NULL
                    if any(pd.isna(p) for p in home_players + away_players):
                        continue

                    # Check if all players have both archetype AND DARKO
                    all_players = home_players + away_players
                    if not all(p in archetypes and p in darko for p in all_players):
                        continue

                    # Determine offensive/defensive players
                    offensive_team = row.get('offensive_team_id')
                    player1_team = row.get('player1_team_id')

                    if pd.isna(offensive_team) or pd.isna(player1_team):
                        continue

                    # Convert to same type for comparison
                    if float(player1_team) == float(offensive_team):
                        off_players, def_players = home_players, away_players
                    else:
                        off_players, def_players = away_players, home_players

                    # Get archetypes (now 0-7 after fix)
                    off_archetypes = [int(archetypes[p]) for p in off_players]
                    def_archetypes = [int(archetypes[p]) for p in def_players]

                    # Get lineup features for supercluster assignment
                    off_features = _extract_lineup_features(off_archetypes, season)
                    def_features = _extract_lineup_features(def_archetypes, season)

                    # Get superclusters using the multi-season model
                    off_sc = _get_supercluster_from_features(off_features, kmeans, scaler)
                    def_sc = _get_supercluster_from_features(def_features, kmeans, scaler)

                    # Calculate matchup_id (0-35)
                    matchup_id = _calculate_matchup_id(off_sc, def_sc)

                    # Aggregate Z-matrices (indices are now 0-7)
                    z_off = defaultdict(float)
                    z_def = defaultdict(float)
                    for i, p in enumerate(off_players):
                        z_off[off_archetypes[i]] += float(darko[p]['o_darko'])
                    for i, p in enumerate(def_players):
                        z_def[def_archetypes[i]] += float(darko[p]['d_darko'])

                    # Calculate outcome (simplified for prototype)
                    outcome = 0  # Placeholder - would calculate from play description

                    # Create record
                    rec = {
                        'outcome': outcome,
                        'matchup_id': matchup_id,
                        'off_supercluster': off_sc,
                        'def_supercluster': def_sc,
                        'season': season
                    }

                    # Write Z-matrices (indices 0-7)
                    for a in range(8):
                        rec[f'z_off_{a}'] = z_off.get(a, 0.0)
                        rec[f'z_def_{a}'] = z_def.get(a, 0.0)

                    rows.append(rec)
                    season_rows += 1

                    # Log progress
                    if season_rows % 1000 == 0:
                        logging.info(f"  Processed {season_rows:,} possessions...")

                except Exception as e:
                    logging.debug(f"Error processing possession {idx}: {e}")
                    continue

            logging.info(f"  Generated {season_rows:,} training-ready possessions for {season}")

    finally:
        if conn is not None:
            conn.close()

    if not rows:
        logging.error('No rows prepared; nothing to write.')
        return

    # Create DataFrame
    df = pd.DataFrame(rows)

    # Clean data
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    before = len(df)
    df.dropna(inplace=True)
    dropped = before - len(df)
    if dropped:
        logging.warning(f'Dropped {dropped} rows containing NaN/Inf')

    # Validate matchup diversity
    unique_matchups = df['matchup_id'].nunique()
    logging.info(f"\nMatchup diversity: {unique_matchups} unique matchups (expected: 36)")

    if unique_matchups < 10:
        logging.warning("Low matchup diversity - may indicate issues with supercluster assignment")

    # Write output
    df.to_csv(OUTPUT_CSV_PATH, index=False)
    logging.info(f"\n✅ Wrote matchup-specific dataset to {OUTPUT_CSV_PATH} ({len(df):,} rows)")

    # Generate summary
    logging.info(f"\nDataset Summary:")
    logging.info(f"  Total possessions: {len(df):,}")
    for season in TRAIN_SEASONS:
        season_count = len(df[df['season'] == season])
        if season_count > 0:
            pct = (season_count / len(df)) * 100
            logging.info(f"  {season}: {season_count:,} ({pct:.1f}%)")

    # Check archetype coverage
    logging.info(f"\nArchetype Coverage:")
    for a in range(8):
        off_nonzero = (df[f'z_off_{a}'] != 0).sum()
        def_nonzero = (df[f'z_def_{a}'] != 0).sum()
        if off_nonzero > 0 or def_nonzero > 0:
            logging.info(f"  Archetype {a}: Off={off_nonzero:,}, Def={def_nonzero:,}")

    # Check matchup distribution
    logging.info(f"\nMatchup Distribution:")
    matchup_counts = df['matchup_id'].value_counts().sort_index()
    for matchup_id in range(36):
        count = matchup_counts.get(matchup_id, 0)
        if count > 0:
            logging.info(f"  Matchup {matchup_id}: {count} possessions")

if __name__ == '__main__':
    prepare_matchup_specific_bayesian_data()
