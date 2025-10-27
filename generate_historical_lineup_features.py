#!/usr/bin/env python3
"""
Generate Historical Lineup Features for Multi-Season Supercluster Training

This script extracts lineup features from historical possession data (2018-19, 2020-21, 2021-22)
and prepares them for training a semantically stable supercluster model.

This addresses the critical issue identified in the pre-mortem: the current supercluster model
was trained on 2022-23 data only, creating semantic drift when applied to historical seasons.
"""

import sqlite3
import pandas as pd
import numpy as np
import json
import logging
from collections import defaultdict, Counter
import os
from pathlib import Path

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Historical training seasons
TRAIN_SEASONS = ['2018-19', '2020-21', '2021-22']
DB_PATH = "src/nba_stats/db/nba_stats.db"

def _load_archetypes_for_season(season: str) -> dict:
    """Load archetype assignments for a season, mapping IDs 1-8 to indices 0-7."""
    csv_patterns = {
        '2018-19': 'player_archetypes_k8_2018-19.csv',
        '2020-21': 'player_archetypes_k8_2020-21.csv',
        '2021-22': 'player_archetypes_k8_2021-22.csv'
    }

    csv_path = csv_patterns[season]
    if not os.path.exists(csv_path):
        logging.error(f"Archetype CSV not found: {csv_path}")
        return {}

    df = pd.read_csv(csv_path)
    # Map IDs 1-8 to indices 0-7 for internal use
    return pd.Series(df['archetype_id'].values - 1, index=df['player_id']).to_dict()

def _extract_lineup_from_possession(row) -> tuple:
    """Extract home and away lineups from a possession row."""
    try:
        home_players = [row[f'home_player_{i}_id'] for i in range(1, 6)]
        away_players = [row[f'away_player_{i}_id'] for i in range(1, 6)]

        # Check if all players are present
        if any(p is None for p in home_players + away_players):
            return None, None

        # Determine which team is on offense
        offensive_team = row.get('offensive_team_id')
        player1_team = row.get('player1_team_id')


        # If we have offensive team info, use it (handle NaN values)
        if (pd.notna(offensive_team) and pd.notna(player1_team) and
            offensive_team != '' and player1_team != ''):
            # Convert to same type for comparison (float vs int)
            if float(player1_team) == float(offensive_team):
                offensive_players, defensive_players = home_players, away_players
            else:
                offensive_players, defensive_players = away_players, home_players
        else:
            # If missing offensive team info, try to infer from score or other indicators
            # For now, use a simple heuristic: if there's a score change, determine based on that
            # But this is complex, so let's just skip these possessions for now
            return None, None

        return offensive_players, defensive_players

    except Exception as e:
        logging.debug(f"Error extracting lineup: {e}")
        return None, None

def _calculate_lineup_outcome(description: str) -> dict:
    """Calculate outcome points and shot type from play description."""
    if not isinstance(description, str):
        return {'points': 0, 'is_2pt': False, 'is_3pt': False, 'is_ft': False}

    desc_lower = description.lower()
    points = 0
    is_2pt = False
    is_3pt = False
    is_ft = False

    # 3-point shots
    if '(3pt)' in desc_lower or 'three' in desc_lower:
        points = 3
        is_3pt = True
    # 2-point shots
    elif '(2pt)' in desc_lower or ('shot' in desc_lower and '3' not in desc_lower):
        points = 2
        is_2pt = True
    # Free throws
    elif 'free throw' in desc_lower and 'miss' not in desc_lower:
        points = 1
        is_ft = True
    # Turnovers or misses = 0 points
    elif 'turnover' in desc_lower or 'miss' in desc_lower:
        points = 0

    return {
        'points': points,
        'is_2pt': is_2pt,
        'is_3pt': is_3pt,
        'is_ft': is_ft
    }

def _collect_possession_data_for_season(season: str, archetypes: dict) -> dict:
    """Collect possession data for a single season."""
    logging.info(f"Processing {season}...")

    conn = sqlite3.connect(DB_PATH)
    lineup_stats = defaultdict(lambda: {
        'possessions': 0,
        'points': 0,
        'fga_2pt': 0,
        'fga_3pt': 0,
        'fga_total': 0,
        'fgm_2pt': 0,
        'fgm_3pt': 0,
        'ftm': 0,
        'fta': 0,
        'pts_2pt': 0,
        'pts_3pt': 0,
        'pts_ft': 0,
        'pts_paint': 0,
        'pts_fastbreak': 0,
        'pts_off_turnover': 0,
        'ast': 0,
        'tov': 0,
        'minutes': 0.0
    })

    try:
        # Use pandas to read the data as DataFrame for easier column access
        query = """
            SELECT p.*, g.season
            FROM Possessions p
            JOIN Games g ON p.game_id = g.game_id
            WHERE g.season = ?
            AND p.home_player_1_id IS NOT NULL
            AND p.away_player_1_id IS NOT NULL
        """

        # Read all data at once for simplicity (limit for debugging)
        df = pd.read_sql_query(query, conn, params=(season,))
        logging.info(f"  Loaded {len(df)} rows from database")

        processed = 0
        skipped_lineup = 0
        skipped_archetype = 0

        for idx, row in df.iterrows():
            processed += 1

            # Debug: log first few rows to see what's in the data
            if idx < 3:
                logging.debug(f"Row {idx}: offensive_team={row.get('offensive_team_id')}, player1_team={row.get('player1_team_id')}")
                logging.debug(f"  Home players: {[row.get(f'home_player_{i}_id') for i in range(1, 6)]}")
                logging.debug(f"  Away players: {[row.get(f'away_player_{i}_id') for i in range(1, 6)]}")

            # Extract lineups
            off_players, def_players = _extract_lineup_from_possession(row)
            if off_players is None:
                skipped_lineup += 1
                if idx < 3:
                    logging.debug(f"  Failed lineup extraction for row {idx}")
                continue

            # Check if all players have archetypes (relaxed for debugging)
            all_players = off_players + def_players
            players_with_archetypes = [p for p in all_players if p in archetypes]

            # For now, require at least 6 out of 10 players to have archetypes (very lenient for Phase 0)
            if len(players_with_archetypes) < 6:
                skipped_archetype += 1
                continue

            # Get archetypes (handle missing ones)
            off_archetypes = [archetypes.get(p, 0) for p in off_players]  # Default to archetype 0
            def_archetypes = [archetypes.get(p, 0) for p in def_players]  # Default to archetype 0

            # Create lineup key (archetypes 0-7 for internal use)
            lineup_key = "_".join(map(str, sorted(off_archetypes)))

            # Calculate outcome
            description = (row['home_description'] or '') + (row['visitor_description'] or '') + (row['neutral_description'] or '')
            outcome = _calculate_lineup_outcome(description)

            # Update lineup stats
            stats = lineup_stats[lineup_key]
            stats['possessions'] += 1
            stats['points'] += outcome['points']

            if outcome['is_2pt']:
                stats['fga_2pt'] += 1
                stats['fga_total'] += 1
                if outcome['points'] > 0:
                    stats['fgm_2pt'] += 1
                    stats['pts_2pt'] += outcome['points']
            elif outcome['is_3pt']:
                stats['fga_3pt'] += 1
                stats['fga_total'] += 1
                if outcome['points'] > 0:
                    stats['fgm_3pt'] += 1
                    stats['pts_3pt'] += outcome['points']

            # Estimate minutes (rough approximation)
            stats['minutes'] += 0.5  # Approximate 30 seconds per possession

        logging.info(f"  Processed {processed:,} possessions for {len(lineup_stats)} unique lineups")
        logging.info(f"  Skipped - lineup extraction: {skipped_lineup:,}")
        logging.info(f"  Skipped - archetype coverage: {skipped_archetype:,}")

    finally:
        conn.close()

    return dict(lineup_stats)

def _calculate_derived_features(stats: dict) -> dict:
    """Calculate derived features needed for clustering."""
    possessions = stats['possessions']
    if possessions == 0:
        return {k: 0.0 for k in [
            'w_pct', 'plus_minus', 'off_rating', 'pace', 'ast_pct', 'ast_to',
            'pct_fga_2pt', 'pct_fga_3pt', 'pct_pts_2pt', 'pct_pts_2pt_mr',
            'pct_pts_3pt', 'pct_pts_ft', 'pct_pts_off_tov', 'pct_pts_paint'
        ]}

    # Basic metrics
    w_pct = 1.0 if stats['points'] > 0 else 0.0  # Simplified win percentage
    plus_minus = stats['points'] - 0  # Simplified (no defensive points)
    off_rating = (stats['points'] / possessions) * 100 if possessions > 0 else 0
    pace = 100.0  # Default pace per 100 possessions

    # Assist and turnover rates
    ast_pct = (stats['ast'] / max(stats['fga_total'], 1)) * 100
    ast_to = stats['ast'] / max(stats['tov'], 1) if stats['tov'] > 0 else stats['ast']

    # Shot distribution percentages
    total_fga = stats['fga_2pt'] + stats['fga_3pt']
    pct_fga_2pt = (stats['fga_2pt'] / max(total_fga, 1)) * 100
    pct_fga_3pt = (stats['fga_3pt'] / max(total_fga, 1)) * 100

    # Points distribution percentages
    total_points = stats['pts_2pt'] + stats['pts_3pt'] + stats['pts_ft']
    pct_pts_2pt = (stats['pts_2pt'] / max(total_points, 1)) * 100
    pct_pts_2pt_mr = pct_pts_2pt * 0.3  # Estimate mid-range as portion of 2pt
    pct_pts_3pt = (stats['pts_3pt'] / max(total_points, 1)) * 100
    pct_pts_ft = (stats['pts_ft'] / max(total_points, 1)) * 100

    # Other point source percentages (estimates)
    pct_pts_off_tov = 0.0  # Not calculable from possession data
    pct_pts_paint = pct_pts_2pt * 0.8  # Estimate paint as portion of 2pt

    return {
        'w_pct': w_pct,
        'plus_minus': plus_minus,
        'off_rating': off_rating,
        'pace': pace,
        'ast_pct': ast_pct,
        'ast_to': ast_to,
        'pct_fga_2pt': pct_fga_2pt,
        'pct_fga_3pt': pct_fga_3pt,
        'pct_pts_2pt': pct_pts_2pt,
        'pct_pts_2pt_mr': pct_pts_2pt_mr,
        'pct_pts_3pt': pct_pts_3pt,
        'pct_pts_ft': pct_pts_ft,
        'pct_pts_off_tov': pct_pts_off_tov,
        'pct_pts_paint': pct_pts_paint
    }

def _create_features_dataframe(all_lineup_stats: dict) -> pd.DataFrame:
    """Create feature dataframe from lineup statistics."""
    rows = []

    for lineup_key, stats in all_lineup_stats.items():
        base_features = {
            'lineup_key': lineup_key,
            'archetype_lineup': lineup_key,
            'possessions': stats['possessions'],
            'minutes': stats['minutes'],
            'points': stats['points'],
            'fga_2pt': stats['fga_2pt'],
            'fga_3pt': stats['fga_3pt'],
            'fgm_2pt': stats['fgm_2pt'],
            'fgm_3pt': stats['fgm_3pt'],
            'ftm': stats['ftm'],
            'fta': stats['fta'],
            'pts_2pt': stats['pts_2pt'],
            'pts_3pt': stats['pts_3pt'],
            'pts_ft': stats['pts_ft'],
            'ast': stats['ast'],
            'tov': stats['tov']
        }

        derived_features = _calculate_derived_features(stats)

        rows.append({**base_features, **derived_features})

    return pd.DataFrame(rows)

def main():
    """Main execution function."""
    logging.info("="*80)
    logging.info("GENERATING HISTORICAL LINEUP FEATURES FOR MULTI-SEASON SUPERCLUSTER MODEL")
    logging.info("="*80)

    # Load archetypes for all seasons
    archetype_maps = {}
    for season in TRAIN_SEASONS:
        archetypes = _load_archetypes_for_season(season)
        if archetypes:
            archetype_maps[season] = archetypes
            logging.info(f"Loaded {len(archetypes)} archetype assignments for {season}")
        else:
            logging.error(f"Failed to load archetypes for {season}")
            return

    # Collect lineup statistics for all seasons
    all_lineup_stats = {}

    for season in TRAIN_SEASONS:
        season_stats = _collect_possession_data_for_season(season, archetype_maps[season])
        all_lineup_stats.update(season_stats)
        logging.info(f"Season {season}: {len(season_stats)} unique lineups")

    logging.info(f"\nTotal unique lineups across all seasons: {len(all_lineup_stats)}")

    # Create features dataframe
    features_df = _create_features_dataframe(all_lineup_stats)

    # Filter for lineups with sufficient possessions (similar to original paper's approach)
    min_possessions = 10  # Require at least 10 possessions for reliable statistics
    features_df = features_df[features_df['possessions'] >= min_possessions]

    logging.info(f"After filtering (≥{min_possessions} possessions): {len(features_df)} lineups")

    # Select features for clustering (similar to original approach)
    clustering_features = [
        'w_pct', 'plus_minus', 'off_rating', 'pace',
        'ast_pct', 'ast_to',
        'pct_fga_2pt', 'pct_fga_3pt',
        'pct_pts_2pt', 'pct_pts_2pt_mr', 'pct_pts_3pt',
        'pct_pts_ft', 'pct_pts_off_tov', 'pct_pts_paint'
    ]

    available_features = [f for f in clustering_features if f in features_df.columns]
    logging.info(f"Using {len(available_features)} features for clustering: {available_features}")

    # Handle missing values
    features_df = features_df.dropna(subset=available_features)

    if len(features_df) == 0:
        logging.error("No valid lineup features after filtering")
        return

    # Save the features for later use
    output_dir = "historical_lineup_features"
    Path(output_dir).mkdir(exist_ok=True)

    features_df.to_csv(f"{output_dir}/historical_lineup_features.csv", index=False)
    logging.info(f"Saved {len(features_df)} lineup features to {output_dir}/historical_lineup_features.csv")

    # Save summary statistics
    summary = {
        'total_lineups': int(len(features_df)),
        'total_possessions': int(features_df['possessions'].sum()),
        'avg_possessions_per_lineup': float(features_df['possessions'].mean()),
        'features_used': available_features,
        'seasons': TRAIN_SEASONS
    }

    with open(f"{output_dir}/features_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)

    logging.info("\nFeature Summary:")
    logging.info(f"  Total lineups: {summary['total_lineups']:,}")
    logging.info(f"  Total possessions: {summary['total_possessions']:,}")
    logging.info(f"  Average possessions per lineup: {summary['avg_possessions_per_lineup']:.1f}")
    logging.info(f"  Features used: {len(summary['features_used'])}")

    logging.info("\n✅ Historical lineup features generated successfully!")
    logging.info("Next step: Train K-Means model on these pooled features")

if __name__ == '__main__':
    main()
