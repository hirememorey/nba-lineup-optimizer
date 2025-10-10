import pandas as pd
import sqlite3
import os
from sklearn.preprocessing import RobustScaler
from sklearn.cluster import KMeans
import joblib

# Add the project root to the python path so we can import modules from src
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

def get_db_connection(db_path):
    """Establishes a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def generate_lineup_superclusters(input_df=None, db_path=None, table_name='PlayerLineupStats', output_path='lineup_supercluster_results/lineup_features_with_superclusters.csv', scaler_path='trained_models/robust_scaler.joblib', kmeans_path='trained_models/kmeans_model.joblib'):
    """
    This function generates lineup superclusters based on player lineup stats.
    It performs the following steps:
    1. Loads lineup data from a database or a provided DataFrame.
    2. Selects a predefined set of 18 validated, non-null features.
    3. Applies RobustScaler to handle outliers in the feature set.
    4. Performs K-Means clustering (k=6) to identify lineup superclusters.
    5. Saves the results, including the original data and the new supercluster_id, to a CSV.
    6. Saves the trained scaler and KMeans model for future use.
    """
    if input_df is None:
        if db_path is None:
            raise ValueError("Either input_df or db_path must be provided.")
        print(f"Loading data from table '{table_name}' in database at {db_path}...")
        conn = get_db_connection(db_path)
        try:
            input_df = pd.read_sql_query(f'SELECT * FROM {table_name}', conn)
            print(f"Successfully loaded {len(input_df)} rows.")
        finally:
            conn.close()

    # --- Feature Selection ---
    # Use actual column names from PlayerLineupStats
    VALIDATED_FEATURES = [
        'w_pct', 'plus_minus', 'off_rating', 'def_rating', 'ts_pct',
        'ast_pct', 'ast_to', 'oreb_pct', 'dreb_pct', 'reb_pct', 'tm_tov_pct',
        'efg_pct', 'pace',
        'pct_fga_2pt', 'pct_fga_3pt',
        'pct_pts_2pt_mr', 'pct_pts_3pt', 'pct_pts_fb'
    ]
    # Attempt to use predefined validated features; if unusable, fall back to auto-selected features
    base_features = VALIDATED_FEATURES
    usable_cols = [c for c in base_features if c in input_df.columns]
    features_df = input_df[usable_cols].copy()
    print(f"Selected {len(features_df.columns)} validated features for clustering.")
    # Drop rows with any NaNs in selected features to satisfy scaler/KMeans
    before = len(features_df)
    mask_complete = features_df.notna().all(axis=1) if len(features_df.columns) > 0 else pd.Series([False]*len(input_df), index=input_df.index)
    features_df = features_df[mask_complete]
    if len(features_df) == 0 or len(features_df.columns) == 0:
        print("Validated feature set unusable (no complete rows/cols). Falling back to auto-selected features...")
        # Auto-select up to 18 high-coverage numeric columns with variance
        exclude_keywords = [
            'id', 'name', 'season', 'created_at', 'updated_at'
        ]
        numeric_cols = [c for c in input_df.columns if pd.api.types.is_numeric_dtype(input_df[c])]
        candidate_cols = []
        for c in numeric_cols:
            lc = c.lower()
            if any(k in lc for k in exclude_keywords):
                continue
            s = input_df[c]
            if s.notna().all() and s.nunique(dropna=True) > 1:
                candidate_cols.append(c)
        # Prefer percentage/ratio-like columns if present, else take any
        prioritized = [c for c in candidate_cols if any(tok in c.lower() for tok in ['pct','rate','ratio','plus_minus','w_pct'])]
        rest = [c for c in candidate_cols if c not in prioritized]
        auto_cols = (prioritized + rest)[:18]
        if not auto_cols:
            raise ValueError("No usable numeric features found for clustering.")
        print(f"Auto-selected {len(auto_cols)} features: {auto_cols}")
        features_df = input_df[auto_cols].copy()
        mask_complete = features_df.notna().all(axis=1)
        features_df = features_df[mask_complete]
        input_df = input_df.loc[features_df.index]
    else:
        dropped = before - int(mask_complete.sum())
        if dropped > 0:
            print(f"Dropping {dropped} rows with missing feature values before scaling/clustering")
        input_df = input_df.loc[features_df.index]

    # --- Feature Scaling ---
    print("Applying RobustScaler to handle outliers...")
    scaler = RobustScaler()
    scaled_features = scaler.fit_transform(features_df)
    
    # Save the scaler
    os.makedirs(os.path.dirname(scaler_path), exist_ok=True)
    joblib.dump(scaler, scaler_path)
    print(f"Scaler saved to {scaler_path}")

    # --- K-Means Clustering ---
    print("Performing K-Means clustering (k=6)...")
    kmeans = KMeans(n_clusters=6, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(scaled_features)
    
    # Save the model
    os.makedirs(os.path.dirname(kmeans_path), exist_ok=True)
    joblib.dump(kmeans, kmeans_path)
    print(f"KMeans model saved to {kmeans_path}")

    # --- Assign Clusters and Save Results ---
    output_df = input_df.copy()
    output_df['supercluster_id'] = clusters
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    output_df.to_csv(output_path, index=False)
    print(f"Clustering complete. Results saved to {output_path}")
    
    return output_df

if __name__ == '__main__':
    # This allows the script to be run from the command line
    # The database is located in ../db/nba_stats.db relative to the script path
    
    # Correctly determine the project root and database path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    db_path = os.path.join(project_root, 'src', 'nba_stats', 'db', 'nba_stats.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        print("Please ensure the database exists and the path is correct.")
    else:
        generate_lineup_superclusters(db_path=db_path)
