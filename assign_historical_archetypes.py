"""
Assign archetypes to historical seasons (2018-19, 2020-21, 2021-22).

This script performs K-means clustering on the archetype features for each historical season
and assigns archetype IDs to players. This is a critical step before multi-season Bayesian
model training.
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from sklearn.cluster import KMeans
from sklearn.preprocessing import RobustScaler

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database path
DB_PATH = "src/nba_stats/db/nba_stats.db"

# Historical seasons to process
HISTORICAL_SEASONS = {
    "2018-19": "2018_19",
    "2020-21": "2020_21", 
    "2021-22": "2021_22"
}

# The 48 canonical archetype features from the paper
CANONICAL_48_FEATURES = [
    'FTPCT', 'TSPCT', 'THPAr', 'FTr', 'TRBPCT', 'ASTPCT', 'AVGDIST', 'Zto3r',
    'THto10r', 'TENto16r', 'SIXTto3PTr', 'HEIGHT', 'WINGSPAN', 'FRNTCTTCH',
    'TOP', 'AVGSECPERTCH', 'AVGDRIBPERTCH', 'ELBWTCH', 'POSTUPS', 'PNTTOUCH',
    'DRIVES', 'DRFGA', 'DRPTSPCT', 'DRPASSPCT', 'DRASTPCT', 'DRTOVPCT',
    'DRPFPCT', 'DRIMFGPCT', 'CSFGA', 'CS3PA', 'PASSESMADE', 'SECAST',
    'POTAST', 'PUFGA', 'PU3PA', 'PSTUPFGA', 'PSTUPPTSPCT', 'PSTUPPASSPCT',
    'PSTUPASTPCT', 'PSTUPTOVPCT', 'PNTTCHS', 'PNTFGA', 'PNTPTSPCT',
    'PNTPASSPCT', 'PNTASTPCT', 'PNTTVPCT', 'AVGFGATTEMPTEDAGAINSTPERGAME'
]

# Archetype names (from the paper)
ARCHETYPE_NAMES = [
    "Scoring Wings",
    "Non-Shooting, Defensive Minded Bigs",
    "Offensive Minded Bigs",
    "Versatile Frontcourt Players",
    "Offensive Juggernauts",
    "3&D",
    "Defensive Minded Guards",
    "Playmaking, Initiating Guards"
]


def load_archetype_features(conn: sqlite3.Connection, season: str) -> pd.DataFrame:
    """
    Load archetype features for a specific historical season.
    
    Args:
        conn: Database connection
        season: Season string (e.g., "2018_19")
        
    Returns:
        DataFrame with player features
    """
    table_name = f"PlayerArchetypeFeatures_{season}"
    
    try:
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql_query(query, conn)
        logger.info(f"Loaded {len(df)} players from {table_name}")
        return df
    except Exception as e:
        logger.error(f"Error loading from {table_name}: {e}")
        return pd.DataFrame()


def assign_archetypes_for_season(season_display: str, season_table: str):
    """
    Assign archetypes to players for a specific historical season.
    
    Args:
        season_display: Display name (e.g., "2018-19")
        season_table: Table suffix (e.g., "2018_19")
    """
    logger.info(f"Processing season: {season_display}")
    
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Load archetype features
        features_df = load_archetype_features(conn, season_table)
        
        if features_df.empty:
            logger.error(f"No data found for {season_display}")
            return
        
        # Check for required features
        missing_features = [f for f in CANONICAL_48_FEATURES if f not in features_df.columns]
        if missing_features:
            logger.warning(f"Missing features for {season_display}: {missing_features}")
            # Use only available features
            available_features = [f for f in CANONICAL_48_FEATURES if f in features_df.columns]
        else:
            available_features = CANONICAL_48_FEATURES
        
        logger.info(f"Using {len(available_features)} features for clustering")
        
        # Prepare features for clustering
        X = features_df[available_features].copy()
        
        # Handle missing values - fill with 0 (already done in feature generation)
        X = X.fillna(0)
        
        # Replace inf values
        X = X.replace([np.inf, -np.inf], 0)
        
        # Use RobustScaler (as determined from previous analysis)
        scaler = RobustScaler()
        X_scaled = scaler.fit_transform(X)
        
        logger.info(f"Scaled features for {len(X)} players")
        
        # Perform K-means clustering (K=8)
        kmeans = KMeans(n_clusters=8, random_state=42, n_init=10, max_iter=300)
        archetype_labels = kmeans.fit_predict(X_scaled)
        
        # Assign archetype IDs (convert from 0-indexed to 1-indexed for consistency)
        features_df['archetype_id'] = [int(label) + 1 for label in archetype_labels]
        
        logger.info(f"Clustering complete. Archetype distribution:")
        for arch_id, count in sorted(features_df['archetype_id'].value_counts().items()):
            arch_name = ARCHETYPE_NAMES[arch_id - 1] if 1 <= arch_id <= 8 else "Unknown"
            logger.info(f"  Archetype {arch_id} ({arch_name}): {count} players")
        
        # Save results to CSV
        output_file = f"player_archetypes_k8_{season_display}.csv"
        output_df = features_df[['player_id', 'archetype_id']].copy()
        output_df.to_csv(output_file, index=False)
        logger.info(f"Archetype assignments saved to {output_file}")
        
        # Also save to database (update the features table)
        cursor = conn.cursor()
        
        # Create a new column for archetype_id if it doesn't exist
        cursor.execute(f"PRAGMA table_info(PlayerArchetypeFeatures_{season_table})")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'archetype_id' not in columns:
            cursor.execute(f"ALTER TABLE PlayerArchetypeFeatures_{season_table} ADD COLUMN archetype_id INTEGER")
            logger.info(f"Added archetype_id column to PlayerArchetypeFeatures_{season_table}")
        
        # Update archetype assignments
        for _, row in output_df.iterrows():
            cursor.execute(f"""
                UPDATE PlayerArchetypeFeatures_{season_table}
                SET archetype_id = ?
                WHERE player_id = ?
            """, (row['archetype_id'], row['player_id']))
        
        conn.commit()
        logger.info(f"Updated archetype assignments in database for {len(output_df)} players")
        
    finally:
        conn.close()


def main():
    """Main function to assign archetypes to all historical seasons."""
    logger.info("=" * 80)
    logger.info("ASSIGNING ARCHETYPES TO HISTORICAL SEASONS")
    logger.info("=" * 80)
    logger.info("")
    
    for season_display, season_table in HISTORICAL_SEASONS.items():
        assign_archetypes_for_season(season_display, season_table)
        logger.info("")
    
    logger.info("=" * 80)
    logger.info("✅ ARCHETYPE ASSIGNMENT COMPLETE")
    logger.info("Historical seasons are now ready for multi-season Bayesian model training!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

