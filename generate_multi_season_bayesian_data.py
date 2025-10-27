#!/usr/bin/env python3
"""
Generate Multi-Season Bayesian Training Data

This script prepares historical possession data (2018-19, 2020-21, 2021-22) 
for multi-season Bayesian model training. Excludes 2022-23 as validation holdout.

CRITICAL FIX: Archetype IDs are 1-8 in CSVs but must be mapped to indices 0-7.
"""

import os
import sqlite3
import json
import logging
from collections import defaultdict
import numpy as np
import pandas as pd

DB_PATH = "src/nba_stats/db/nba_stats.db"
SUPERCLUSTER_MAP_PATH = "lineup_supercluster_results/supercluster_assignments_v2.json"
OUTPUT_CSV_PATH = "multi_season_bayesian_data.csv"
BATCH_SIZE = 50000

# Historical seasons to train on (excluding 2022-23 for validation)
TRAIN_SEASONS = ['2018-19', '2020-21', '2021-22']
ARCHETYPE_CSV_PATTERNS = {
    '2018-19': 'player_archetypes_k8_2018-19.csv',
    '2020-21': 'player_archetypes_k8_2020-21.csv',
    '2021-22': 'player_archetypes_k8_2021-22.csv'
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _load_archetypes_for_season(csv_path: str) -> dict:
    """Load archetype assignments from CSV, FIXED to map IDs 1-8 to indices 0-7."""
    if not os.path.exists(csv_path):
        logging.error(f"Archetypes CSV not found at {csv_path}")
        return {}
    df = pd.read_csv(csv_path)
    if not {'player_id','archetype_id'}.issubset(df.columns):
        logging.error("Archetypes CSV missing required columns: {'player_id','archetype_id'}")
        return {}
    
    # CRITICAL FIX: Subtract 1 from archetype IDs (1-8) to get indices (0-7)
    return pd.Series(df['archetype_id'].values - 1, index=df['player_id']).to_dict()

def _load_darko_for_season(db_path: str, season: str) -> dict:
    """Load DARKO ratings for a specific season."""
    ratings = {}
    con = None
    try:
        con = sqlite3.connect(db_path)
        df = pd.read_sql_query(
            "SELECT player_id, offensive_darko, defensive_darko FROM PlayerSeasonSkill WHERE season=?",
            con,
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
        if con is not None:
            con.close()
    return ratings

def _load_all_mappings():
    """Load archetype and DARKO mappings for all training seasons."""
    archetype_maps = {}
    darko_maps = {}
    
    for season in TRAIN_SEASONS:
        logging.info(f"Loading mappings for {season}...")
        
        # Load archetypes
        csv_path = ARCHETYPE_CSV_PATTERNS[season]
        arch_map = _load_archetypes_for_season(csv_path)
        if arch_map:
            archetype_maps[season] = arch_map
            logging.info(f"  Loaded {len(arch_map)} archetype assignments")
        else:
            logging.error(f"  Failed to load archetypes for {season}")
            return None, None
        
        # Load DARKO
        darko_map = _load_darko_for_season(DB_PATH, season)
        if darko_map:
            darko_maps[season] = darko_map
            logging.info(f"  Loaded {len(darko_map)} DARKO ratings")
        else:
            logging.error(f"  Failed to load DARKO for {season}")
            return None, None
    
    return archetype_maps, darko_maps

def _load_supercluster_map(path: str) -> dict:
    """Load supercluster assignments."""
    if not os.path.exists(path):
        logging.warning(f"Supercluster map not found at {path}. Unknown lineups will default to 0.")
        return {}
    with open(path, 'r') as f:
        data = json.load(f)
    return data.get('lineup_assignments', {})

def _lineup_key(archetypes_list: list[int]) -> str:
    """Create lineup key from archetype IDs (now 0-7 after fix)."""
    # Archetypes are 0-7 internally, but supercluster map uses 1-8
    # Convert to 1-8 range for lookup
    archetypes_1_to_8 = [a + 1 for a in archetypes_list]
    return "_".join(str(a) for a in sorted(archetypes_1_to_8))

def _lookup_supercluster(archetypes_list: list[int], sc_map: dict) -> int:
    """Lookup supercluster for archetype lineup."""
    return int(sc_map.get(_lineup_key(archetypes_list), 0))

def _calc_outcome(description: str) -> int:
    """Calculate possession outcome (points scored)."""
    if not isinstance(description, str):
        return 0
    t = description.lower()
    if '(3 pts)' in t: return 3
    if '(2 pts)' in t: return 2
    if 'free throw' in t and 'miss' not in t: return 1
    if 'turnover' in t or 'miss' in t: return 0
    return 0

def prepare_multi_season_bayesian_data():
    """Generate multi-season Bayesian training data."""
    logging.info("="*80)
    logging.info("PREPARING MULTI-SEASON BAYESIAN DATASET")
    logging.info("="*80)
    
    # Load all mappings
    archetype_maps, darko_maps = _load_all_mappings()
    if not archetype_maps or not darko_maps:
        logging.error("Failed to load required mappings. Aborting.")
        return
    
    # Load supercluster map
    sc_map = _load_supercluster_map(SUPERCLUSTER_MAP_PATH)
    logging.info(f"Loaded supercluster map with {len(sc_map)} lineup assignments")
    
    rows = []
    con = None
    
    try:
        con = sqlite3.connect(DB_PATH)
        
        # Process each training season
        for season in TRAIN_SEASONS:
            logging.info(f"\nProcessing {season}...")
            archetypes = archetype_maps[season]
            darko = darko_maps[season]
            
            # Query possessions for this season
            query = """
                SELECT p.*, g.season
                FROM Possessions p
                JOIN Games g ON p.game_id = g.game_id
                WHERE g.season = ? AND p.offensive_team_id IS NOT NULL
            """
            
            season_rows = 0
            
            for chunk in pd.read_sql_query(query, con, params=(season,), chunksize=BATCH_SIZE):
                # Coalesce description fields
                for c in ['home_description','visitor_description','neutral_description']:
                    if c not in chunk.columns:
                        chunk[c] = ''
                chunk['description'] = chunk['home_description'].fillna('') + chunk['visitor_description'].fillna('') + chunk['neutral_description'].fillna('')
                
                for _, r in chunk.iterrows():
                    try:
                        # Extract player IDs
                        home = [int(r[f'home_player_{i}_id']) for i in range(1,6)]
                        away = [int(r[f'away_player_{i}_id']) for i in range(1,6)]
                    except Exception:
                        continue
                    
                    # Skip if any players are NULL
                    if any(pd.isna(p) for p in home+away):
                        continue
                    
                    # CRITICAL: Check if all players have both archetype AND DARKO
                    if not all(p in archetypes and p in darko for p in home+away):
                        continue
                    
                    # Determine offensive/defensive players
                    off_team = r.get('offensive_team_id')
                    p1_team = r.get('player1_team_id')
                    off_players, def_players = (home, away) if p1_team == off_team else (away, home)
                    
                    # Get archetypes (now 0-7 after fix)
                    off_arch = [int(archetypes[p]) for p in off_players]
                    def_arch = [int(archetypes[p]) for p in def_players]
                    
                    # Get superclusters
                    off_sc = _lookup_supercluster(off_arch, sc_map)
                    def_sc = _lookup_supercluster(def_arch, sc_map)
                    
                    # Aggregate Z-matrices (indices are now 0-7)
                    z_off = defaultdict(float)
                    z_def = defaultdict(float)
                    for i, p in enumerate(off_players):
                        z_off[off_arch[i]] += float(darko[p]['o_darko'])
                    for i, p in enumerate(def_players):
                        z_def[def_arch[i]] += float(darko[p]['d_darko'])
                    
                    # Calculate outcome
                    outc = _calc_outcome(r.get('description'))
                    
                    # Create record
                    rec = {'outcome': outc, 'matchup_id': f"{off_sc}_vs_{def_sc}", 'season': season}
                    
                    # Write Z-matrices (indices 0-7)
                    for a in range(8):
                        rec[f'z_off_{a}'] = z_off.get(a, 0.0)
                        rec[f'z_def_{a}'] = z_def.get(a, 0.0)
                    
                    rows.append(rec)
                    season_rows += 1
            
            logging.info(f"  Generated {season_rows:,} training-ready possessions for {season}")
        
    finally:
        if con is not None:
            con.close()
    
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
    
    # Write output
    df.to_csv(OUTPUT_CSV_PATH, index=False)
    logging.info(f"\n✅ Wrote full dataset to {OUTPUT_CSV_PATH} ({len(df):,} rows)")
    
    # Generate summary
    logging.info(f"\nDataset Summary:")
    logging.info(f"  Total possessions: {len(df):,}")
    for season in TRAIN_SEASONS:
        season_count = len(df[df['season'] == season])
        pct = (season_count / len(df)) * 100
        logging.info(f"  {season}: {season_count:,} ({pct:.1f}%)")
    
    # Check archetype coverage
    logging.info(f"\nArchetype Coverage:")
    for a in range(8):
        off_nonzero = (df[f'z_off_{a}'] != 0).sum()
        def_nonzero = (df[f'z_def_{a}'] != 0).sum()
        logging.info(f"  Archetype {a}: Off={off_nonzero:,}, Def={def_nonzero:,}")
    
    # Check matchup diversity
    unique_matchups = df['matchup_id'].nunique()
    logging.info(f"\nMatchup Diversity:")
    logging.info(f"  Unique matchups: {unique_matchups}")

if __name__ == '__main__':
    prepare_multi_season_bayesian_data()
