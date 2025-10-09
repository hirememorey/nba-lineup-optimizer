import logging
import pandas as pd
import sqlite3
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = "src/nba_stats/db/nba_stats.db"
OUTPUT_CSV_PATH = "player_archetypes_k8_2022_23.csv"

def fetch_player_features():
    """Fetches player features from the database."""
    logger.info(f"Connecting to database at {DB_PATH}...")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            query = "SELECT * FROM PlayerArchetypeFeatures_2022_23"
            df = pd.read_sql_query(query, conn)
            logger.info(f"Successfully fetched {len(df)} records from PlayerArchetypeFeatures_2022_23.")
            return df
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise

def preprocess_features(df):
    """Preprocesses the feature data for clustering."""
    logger.info("Preprocessing features...")
    
    # Separate identifiers and features
    player_ids = df['player_id']
    features = df.drop(columns=['player_id', 'season', 'team_id'])
    
    # Handle missing values by filling with the mean
    # The paper doesn't specify a method, so mean imputation is a reasonable default.
    for column in features.columns:
        if features[column].isnull().any():
            mean_value = features[column].mean()
            features[column].fillna(mean_value, inplace=True)
            logger.warning(f"Filled {features[column].isnull().sum()} missing values in '{column}' with mean ({mean_value:.2f}).")

    # Scale the features
    # K-means is sensitive to feature scaling, so this is a critical step.
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    logger.info("Features scaled successfully using StandardScaler.")
    
    return player_ids, scaled_features, features.columns

def perform_clustering(scaled_features, n_clusters=8):
    """Performs k-means clustering."""
    logger.info(f"Performing K-means clustering with n_clusters={n_clusters}...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(scaled_features)
    logger.info("Clustering complete.")
    return clusters

def save_archetypes(player_ids, clusters):
    """Saves the player archetypes to a CSV file."""
    results_df = pd.DataFrame({
        'player_id': player_ids,
        'archetype_id': clusters
    })
    
    results_df.to_csv(OUTPUT_CSV_PATH, index=False)
    logger.info(f"Archetype results saved to {OUTPUT_CSV_PATH}")
    return results_df

def main():
    """Main function to create and save player archetypes."""
    logger.info("Starting archetype generation process...")
    try:
        features_df = fetch_player_features()
        player_ids, scaled_features, feature_columns = preprocess_features(features_df)
        clusters = perform_clustering(scaled_features)
        save_archetypes(player_ids, clusters)
        logger.info("✅ Archetype generation process completed successfully.")
    except Exception as e:
        logger.error(f"An error occurred during archetype generation: {e}")
        raise

if __name__ == "__main__":
    main()
