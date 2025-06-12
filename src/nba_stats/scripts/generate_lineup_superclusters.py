"""
This script generates lineup superclusters based on weighted stats from archetype lineups.
"""
import sqlite3
import pandas as pd
import logging
from pathlib import Path
import sys
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from itertools import combinations
import re

# Configure logging FIRST
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.nba_stats.db.database import get_db_connection
from src.nba_stats.config.settings import SEASON_ID

def get_player_ids_from_group(group_name: str) -> list[int]:
    """Extracts player IDs from a lineup's group name string."""
    return sorted([int(p_id) for p_id in re.findall(r'\d+', group_name)])

def generate_archetype_lineups(conn: sqlite3.Connection) -> tuple[pd.DataFrame, list[str]]:
    """
    Generates weighted average stats for each unique archetype lineup.
    Returns a tuple of (DataFrame, feature_columns_list).
    """
    logging.info("--- Generating Archetype Lineups ---")
    
    # 1. Fetch lineup stats and player archetypes
    lineup_stats_df = pd.read_sql(f"SELECT * FROM PlayerLineupStats WHERE season = '{SEASON_ID}'", conn)
    player_archetypes_df = pd.read_sql(f"SELECT player_id, archetype_id FROM PlayerSeasonArchetypes WHERE season = '{SEASON_ID}'", conn)
    
    logging.info(f"Found {len(lineup_stats_df)} lineups in PlayerLineupStats for season {SEASON_ID}.")
    logging.info(f"Found {len(player_archetypes_df)} player archetypes in PlayerSeasonArchetypes for season {SEASON_ID}.")

    archetype_map = player_archetypes_df.set_index('player_id')['archetype_id'].to_dict()
    logging.info(f"Created archetype map with {len(archetype_map)} players.")

    # 2. Map player IDs to archetypes for each lineup
    archetype_lineups = []
    for _, row in lineup_stats_df.iterrows():
        player_ids = get_player_ids_from_group(row['group_id'])
        
        # Ensure all 5 players have a mapped archetype
        if len(player_ids) == 5 and all(pid in archetype_map for pid in player_ids):
            archetypes = sorted([archetype_map[pid] for pid in player_ids])
            archetype_lineup_id = '-'.join(map(str, archetypes))
            
            new_row = row.to_dict()
            new_row['archetype_lineup_id'] = archetype_lineup_id
            archetype_lineups.append(new_row)
            
    if not archetype_lineups:
        logging.warning("No valid archetype lineups could be generated. Halting process.")
        return pd.DataFrame(), []

    archetype_lineups_df = pd.DataFrame(archetype_lineups)
    
    # 3. Calculate weighted average stats
    feature_cols = [
        'fgm_pct_uast', 'fgm_pct_ast', 'three_fgm_pct_uast', 'three_fgm_pct_ast',
        'two_fgm_pct_uast', 'two_fgm_pct_ast', 'pct_pts_pitp', 'pct_pts_off_to',
        'pct_pts_ft', 'pct_pts_fbps', 'pct_pts_3pt', 'pct_pts_mr', 'pct_pts_2pt',
        'pct_fga_3pt', 'pct_fga_2pt', 'opp_tov_pct', 'opp_fta_rate', 'pace'
    ]

    def weighted_avg(group):
        weights = group['min']
        total_minutes = weights.sum()
        if total_minutes == 0:
            # Return a series with 0 for all feature columns
            return pd.Series({f'W{col.upper()}': 0.0 for col in feature_cols})
            
        weighted_features = {
            f'W{col.upper()}': (group[col] * weights).sum() / total_minutes
            for col in feature_cols if col in group.columns
        }
        weighted_features['total_minutes'] = total_minutes
        return pd.Series(weighted_features)

    # Note: include_groups=False silences a deprecation warning.
    weighted_stats_df = archetype_lineups_df.groupby('archetype_lineup_id').apply(weighted_avg, include_groups=False).reset_index()
    
    logging.info(f"Generated {len(weighted_stats_df)} unique archetype lineups with weighted stats.")
    return weighted_stats_df, feature_cols

def run_supercluster_clustering(conn: sqlite3.Connection, archetype_lineups_df: pd.DataFrame, feature_cols: list[str]):
    """
    Performs K-means clustering on archetype lineups and stores the results.
    """
    logging.info("--- Starting Lineup Supercluster Clustering ---")
    
    if archetype_lineups_df.empty:
        logging.warning("Archetype lineups DataFrame is empty. Skipping clustering.")
        return

    # Prepare features for clustering
    clustering_features = [f'W{col.upper()}' for col in feature_cols]
    # Ensure all features are actually in the dataframe before trying to scale them
    existing_features = [f for f in clustering_features if f in archetype_lineups_df.columns]
    features = archetype_lineups_df[existing_features]

    # Scale features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    
    # K-means clustering for superclusters (K'=6)
    kmeans = KMeans(n_clusters=6, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(scaled_features)
    
    archetype_lineups_df['supercluster_id'] = clusters

    # --- Store Superclusters and Archetype Lineups in Database ---
    cursor = conn.cursor()
    
    # 1. Populate LineupSuperclusters table
    supercluster_names = [
        "Three-Point Symphony", "Half-Court Individual Shot Creators", "Slashing Offenses",
        "All-Around with Midrange", "Chaos Instigators", "Up-Tempo Distributors"
    ]
    
    try:
        for i, name in enumerate(supercluster_names):
            cursor.execute("INSERT OR IGNORE INTO LineupSuperclusters (supercluster_id, supercluster_name) VALUES (?, ?)", (i, name))
        
        # 2. Populate/Update ArchetypeLineups table
        archetype_lineups_df['season'] = SEASON_ID
        
        db_df = archetype_lineups_df
        
        # Make sure all required columns are present
        db_cols = [
            'archetype_lineup_id', 'season', 'total_minutes', 'supercluster_id'
        ] + existing_features
        
        # Align DataFrame columns with DB schema, filling missing with None (or 0.0 for numeric)
        for col in db_cols:
            if col not in db_df.columns:
                # This case should ideally not happen if data processing is correct
                db_df[col] = 0.0
        
        db_df = db_df[db_cols]

        db_df.to_sql('ArchetypeLineups', conn, if_exists='replace', index=False)

        logging.info(f"Successfully stored {len(db_df)} archetype lineups with supercluster assignments.")

    except sqlite3.Error as e:
        logging.error(f"Database error during supercluster storage: {e}")
        conn.rollback()

def main():
    """Main function to generate lineup superclusters."""
    logging.info("--- Starting Lineup Supercluster Generation ---")
    conn = get_db_connection()
    if conn:
        try:
            # First, ensure lineup stats are populated
            # Note: In a real pipeline, you might run populate_lineup_stats.py here
            # For now, we assume it's been run.
            
            # Generate weighted archetype lineup stats
            archetype_lineups_df, feature_cols = generate_archetype_lineups(conn)
            
            # Run clustering on the generated stats
            run_supercluster_clustering(conn, archetype_lineups_df, feature_cols)
            
        finally:
            conn.close()
            logging.info("Database connection closed.")

if __name__ == "__main__":
    main() 