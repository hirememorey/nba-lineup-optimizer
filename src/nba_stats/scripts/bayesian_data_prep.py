import os
import sqlite3
import json
import logging
from collections import defaultdict
import numpy as np
import pandas as pd

DB_PATH = "src/nba_stats/db/nba_stats.db"
ARCHETYPES_CSV = "player_archetypes_k8_2022_23.csv"
SUPERCLUSTER_MAP_PATH = "lineup_supercluster_results/supercluster_assignments.json"
OUTPUT_CSV_PATH = "production_bayesian_data.csv"
SAMPLE_CSV_PATH = "stratified_sample_10k.csv"
BATCH_SIZE = 50000

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _load_archetypes(csv_path: str) -> dict:
    if not os.path.exists(csv_path):
        logging.error(f"Archetypes CSV not found at {csv_path}")
        return {}
    df = pd.read_csv(csv_path)
    if not {'player_id','archetype_id'}.issubset(df.columns):
        logging.error("Archetypes CSV missing required columns: {'player_id','archetype_id'}")
        return {}
    return pd.Series(df['archetype_id'].values, index=df['player_id']).to_dict()

def _load_darko(db_path: str) -> dict:
    ratings = {}
    con = None
    try:
        con = sqlite3.connect(db_path)
        try:
            df = pd.read_sql_query("SELECT player_id, offensive_darko, defensive_darko FROM PlayerSeasonSkill WHERE season='2022-23'", con)
        except Exception:
            df = pd.read_sql_query("SELECT player_id, offensive_skill_rating AS offensive_darko, defensive_skill_rating AS defensive_darko FROM PlayerSkills WHERE skill_metric_source='DARKO'", con)
        for _, r in df.iterrows():
            try:
                pid = int(r['player_id'])
            except Exception:
                continue
            ratings[pid] = {'o_darko': r['offensive_darko'], 'd_darko': r['defensive_darko']}
    except sqlite3.Error as e:
        logging.error(f"Error loading DARKO ratings: {e}")
    finally:
        if con is not None:
            con.close()
    return ratings

def _load_supercluster_map(path: str) -> dict:
    if not os.path.exists(path):
        logging.warning(f"Supercluster map not found at {path}. Unknown lineups will default to 0.")
        return {}
    with open(path, 'r') as f:
        data = json.load(f)
    return data.get('lineup_assignments', {})

def _lineup_key(archetypes_list: list[int]) -> str:
    return "_".join(str(int(a)) for a in sorted(archetypes_list))

def _lookup_supercluster(archetypes_list: list[int], sc_map: dict) -> int:
    return int(sc_map.get(_lineup_key(archetypes_list), 0))

def _calc_outcome(description: str) -> int:
    if not isinstance(description, str):
        return 0
    t = description.lower()
    if '(3 pts)' in t: return 3
    if '(2 pts)' in t: return 2
    if 'free throw' in t and 'makes' in t: return 1
    if 'turnover' in t or 'miss' in t: return 0
    return 0

def prepare_bayesian_data():
    logging.info("--- Preparing Bayesian dataset ---")
    archetypes = _load_archetypes(ARCHETYPES_CSV)
    darko = _load_darko(DB_PATH)
    sc_map = _load_supercluster_map(SUPERCLUSTER_MAP_PATH)

    if not archetypes or not darko:
        logging.error("Missing archetypes or DARKO ratings. Aborting.")
        return

    rows = []
    con = None
    try:
        con = sqlite3.connect(DB_PATH)
        query = "SELECT * FROM Possessions WHERE offensive_team_id IS NOT NULL"
        for chunk in pd.read_sql_query(query, con, chunksize=BATCH_SIZE):
            # Coalesce description fields
            for c in ['home_description','visitor_description','neutral_description']:
                if c not in chunk.columns:
                    chunk[c] = ''
            chunk['description'] = chunk['home_description'].fillna('') + chunk['visitor_description'].fillna('') + chunk['neutral_description'].fillna('')

            for _, r in chunk.iterrows():
                try:
                    home = [int(r[f'home_player_{i}_id']) for i in range(1,6)]
                    away = [int(r[f'away_player_{i}_id']) for i in range(1,6)]
                except Exception:
                    continue
                if any(pd.isna(p) for p in home+away):
                    continue
                if not all(p in archetypes and p in darko for p in home+away):
                    continue
                off_team = r.get('offensive_team_id')
                p1_team = r.get('player1_team_id')
                off_players, def_players = (home, away) if p1_team == off_team else (away, home)
                off_arch = [int(archetypes[p]) for p in off_players]
                def_arch = [int(archetypes[p]) for p in def_players]
                off_sc = _lookup_supercluster(off_arch, sc_map)
                def_sc = _lookup_supercluster(def_arch, sc_map)
                z_off = defaultdict(float)
                z_def = defaultdict(float)
                for i,p in enumerate(off_players):
                    z_off[off_arch[i]] += float(darko[p]['o_darko'])
                for i,p in enumerate(def_players):
                    z_def[def_arch[i]] += float(darko[p]['d_darko'])
                outc = _calc_outcome(r.get('description'))
                rec = {'outcome': outc, 'matchup_id': f"{off_sc}_vs_{def_sc}"}
                for a in range(8):
                    rec[f'z_off_{a}'] = z_off.get(a, 0.0)
                    rec[f'z_def_{a}'] = z_def.get(a, 0.0)
                rows.append(rec)
    finally:
        if con is not None:
            con.close()

    if not rows:
        logging.error('No rows prepared; nothing to write.')
        return

    df = pd.DataFrame(rows)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    before = len(df)
    df.dropna(inplace=True)
    dropped = before - len(df)
    if dropped:
        logging.warning(f'Dropped {dropped} rows containing NaN/Inf')

    df.to_csv(OUTPUT_CSV_PATH, index=False)
    logging.info(f'Wrote full dataset to {OUTPUT_CSV_PATH} ({len(df)} rows)')
    if len(df) > 10000:
        df.sample(n=10000, random_state=42).to_csv(SAMPLE_CSV_PATH, index=False)
        logging.info(f'Wrote sample dataset to {SAMPLE_CSV_PATH} (10000 rows)')
    else:
        df.to_csv(SAMPLE_CSV_PATH, index=False)
        logging.warning('Full dataset < 10k; sample equals full output')

if __name__ == '__main__':
    prepare_bayesian_data()
