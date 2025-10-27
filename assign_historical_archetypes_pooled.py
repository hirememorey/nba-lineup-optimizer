"""
Assign archetypes using POOLED data across all historical seasons.

This is the CORRECT approach: pool all historical seasons together, create ONE
set of archetypes (K=8), then assign players to those stable archetypes.

Why this matters: Archetypes should be comparable across seasons. If LeBron
is an "Offensive Juggernaut" in 2018, he should be in the same archetype in 2021
unless his playing style fundamentally changed.
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


def load_all_historical_features(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Load archetype features from ALL historical seasons and pool them together.
    
    Args:
        conn: Database connection
        
    Returns:
        DataFrame with all historical player-season features (with season column)
    """
    all_features = []
    
    for season_display, season_table in HISTORICAL_SEASONS.items():
        table_name = f"PlayerArchetypeFeatures_{season_table}"
        
        try:
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql_query(query, conn)
            df['season'] = season_display  # Add season identifier
            all_features.append(df)
            logger.info(f"Loaded {len(df)} players from {table_name}")
        except Exception as e:
            logger.error(f"Error loading from {table_name}: {e}")
    
    if not all_features:
        return pd.DataFrame()
    
    # Combine all seasons
    combined = pd.concat(all_features, ignore_index=True)
    logger.info(f"Total player-season combinations: {len(combined)}")
    
    return combined


def assign_pooled_archetypes():
    """
    Pool all historical seasons, perform ONE clustering, then assign archetypes.
    This ensures archetype definitions are stable across seasons.
    """
    logger.info("=" * 80)
    logger.info("POOLED ARCHETYPE ASSIGNMENT")
    logger.info("Pooling all historical seasons for stable archetype definitions")
    logger.info("=" * 80)
    logger.info("")
    
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Load all historical features
        features_df = load_all_historical_features(conn)
        
        if features_df.empty:
            logger.error("No features loaded")
            return
        
        # Check for required features
        missing_features = [f for f in CANONICAL_48_FEATURES if f not in features_df.columns]
        if missing_features:
            logger.warning(f"Missing features: {missing_features}")
            available_features = [f for f in CANONICAL_48_FEATURES if f in features_df.columns]
        else:
            available_features = CANONICAL_48_FEATURES
        
        logger.info(f"Using {len(available_features)} features for clustering")
        
        # Prepare features for clustering
        X = features_df[available_features].copy()
        
        # Handle missing values
        X = X.fillna(0)
        X = X.replace([np.inf, -np.inf], 0)
        
        logger.info(f"Features prepared for {len(X)} player-season combinations")
        
        # Use RobustScaler (as determined from previous analysis)
        scaler = RobustScaler()
        X_scaled = scaler.fit_transform(X)
        
        logger.info("Features scaled")
        
        # Perform K-means clustering (K=8) on the ENTIRE pooled dataset
        kmeans = KMeans(n_clusters=8, random_state=42, n_init=10, max_iter=300)
        archetype_labels = kmeans.fit_predict(X_scaled)
        
        # Assign archetype IDs (1-indexed)
        features_df['archetype_id'] = [int(label) + 1 for label in archetype_labels]
        
        logger.info("Clustering complete. Archetype distribution:")
        for arch_id, count in sorted(features_df['archetype_id'].value_counts().items()):
            arch_name = ARCHETYPE_NAMES[arch_id - 1] if 1 <= arch_id <= 8 else "Unknown"
            logger.info(f"  Archetype {arch_id} ({arch_name}): {count} player-seasons")
        
        # Split by season and save to individual files
        for season_display, season_table in HISTORICAL_SEASONS.items():
            season_df = features_df[features_df['season'] == season_display].copy()
            
            # Save to CSV
            output_file = f"player_archetypes_k8_{season_display}.csv"
            output_df = season_df[['player_id', 'archetype_id']].copy()
            output_df.to_csv(output_file, index=False)
            logger.info(f"Saved {season_display} archetype assignments to {output_file}")
            
            # Update database
            cursor = conn.cursor()
            
            # Add archetype_id column if needed
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
                """, (int(row['archetype_id']), int(row['player_id'])))
            
            logger.info(f"Updated {len(output_df)} player archetypes in database for {season_display}")
        
        conn.commit()
        
        # Check archetype consistency across seasons
        logger.info("")
        logger.info("Checking archetype consistency across seasons...")
        for player_id in features_df['player_id'].unique():
            player_seasons = features_df[features_df['player_id'] == player_id]
            unique_archetypes = player_seasons['archetype_id'].unique()
            
            if len(unique_archetypes) > 1:
                seasons_str = ", ".join([f"{row['season']}: {row['archetype_id']}" for _, row in player_seasons.iterrows()])
                logger.warning(f"Player {player_id}: archetype changed across seasons ({seasons_str})")
        
    finally:
        conn.close()
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("✅ POOLED ARCHETYPE ASSIGNMENT COMPLETE")
    logger.info("All historical seasons now use STABLE, CONSISTENT archetype definitions")
    logger.info("=" * 80)


if __name__ == "__main__":
    assign_pooled_archetypes()

