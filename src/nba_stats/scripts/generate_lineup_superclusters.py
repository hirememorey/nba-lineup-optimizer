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
    VALIDATED_FEATURES = [
        'W_PCT', 'PLUS_MINUS', 'OFF_RATING', 'DEF_RATING', 'TS_PCT',
        'AST_PCT', 'AST_TO', 'OREB_PCT', 'DREB_PCT', 'REB_PCT', 'TM_TOV_PCT',
        'EFG_PCT', 'PACE',
        'FGA_PG_frequency_2PT', 'FGA_PG_frequency_3PT',
        'PTS_frequency_2PT_MR', 'PTS_frequency_3PT', 'PTS_frequency_FBPS'
    ]
    features_df = input_df[VALIDATED_FEATURES].copy()
    print(f"Selected {len(features_df.columns)} validated features for clustering.")

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
