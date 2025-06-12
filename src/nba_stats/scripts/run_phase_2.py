"""
This script executes the feature engineering and clustering steps for Phase 2
of the 'Algorithmic NBA Player Acquisition' project.
"""

import sqlite3
import pandas as pd
import logging
import sys
import os

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Add the project root to the Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(PROJECT_ROOT)

from src.nba_stats.db.database import get_db_connection
from src.nba_stats.config.settings import SEASON_ID, MIN_MINUTES_THRESHOLD

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_player_archetype_features(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Fetches and combines all necessary player features for clustering from the database.
    
    Args:
        conn: SQLite database connection object.
        
    Returns:
        A pandas DataFrame containing the combined features for all players.
    """
    logging.info("--- Fetching Player Features for Archetype Clustering ---")

    query = f"""
    SELECT
        *
    FROM
        PlayerArchetypeFeatures
    WHERE
        season = '{SEASON_ID}'
    """
    
    features_df = pd.read_sql(query, conn)
    logging.info(f"Found features for {len(features_df)} players.")
    
    return features_df

def run_archetype_clustering(conn: sqlite3.Connection, features_df: pd.DataFrame):
    """
    Performs K-means clustering and stores the resulting archetypes in the database.
    """
    logging.info("--- Starting Player Archetype Clustering ---")
    
    if 'player_id' not in features_df.columns or 'season' not in features_df.columns:
        logging.error("The features DataFrame must contain 'player_id' and 'season' columns.")
        return

    player_ids = features_df['player_id']
    season = features_df['season'].iloc[0]
    
    # Impute missing values with the median of the column (as a fallback)
    for col in features_df.columns:
        if features_df[col].isnull().any():
            median_val = features_df[col].median()
            if pd.isna(median_val):
                logging.warning(f"Median for '{col}' is NaN. Filling with 0 instead.")
                features_df[col] = features_df[col].fillna(0)
            else:
                logging.info(f"Imputed missing values in '{col}' with median value {median_val:.2f}")
                features_df[col] = features_df[col].fillna(median_val)

    # Drop non-feature columns
    feature_cols = features_df.drop(columns=['player_id', 'season'])

    # Scale features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(feature_cols)
    
    # K-means clustering
    kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(scaled_features)
    
    # --- Store Archetypes in Database ---
    cursor = conn.cursor()

    # 1. Populate Archetypes table
    archetype_names = [
        "Scoring Wings", "Non-Shooting, Defensive Minded Bigs", "Offensive Minded Bigs",
        "Versatile Frontcourt Players", "Offensive Juggernauts", "3&D",
        "Defensive Minded Guards", "Playmaking, Initiating Guards"
    ]
    
    try:
        for i, name in enumerate(archetype_names):
            cursor.execute("INSERT OR IGNORE INTO Archetypes (archetype_id, archetype_name) VALUES (?, ?)", (i, name))
        
        # 2. Populate PlayerSeasonArchetypes table
        player_archetypes = []
        for player_id, cluster_id in zip(player_ids, clusters):
            player_archetypes.append((player_id, season, cluster_id))

        cursor.executemany("""
            INSERT OR REPLACE INTO PlayerSeasonArchetypes (player_id, season, archetype_id)
            VALUES (?, ?, ?)
        """, player_archetypes)

        conn.commit()
        logging.info(f"Successfully clustered and stored archetypes for {len(player_archetypes)} players.")

    except sqlite3.Error as e:
        logging.error(f"Database error during archetype storage: {e}")
        conn.rollback()

def main():
    """Main function to execute Phase 2."""
    logging.info("--- Starting Phase 2: Feature Engineering & Clustering ---")
    
    conn = get_db_connection()
    if conn:
        try:
            player_features = get_player_archetype_features(conn)
            if not player_features.empty:
                run_archetype_clustering(conn, player_features)
            else:
                logging.warning("No player features found, a common cause for this is not running Phase 1, skipping clustering.")
        finally:
            conn.close()
            logging.info("Database connection closed.")

if __name__ == "__main__":
    main() 