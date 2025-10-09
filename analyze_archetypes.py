import pandas as pd
import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = "src/nba_stats/db/nba_stats.db"
ARCHETYPES_CSV_PATH = "player_archetypes_k8_2022_23.csv"

def load_data():
    """Loads all necessary data from the database and CSV files."""
    logger.info("Loading data for analysis...")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Load player names
            players_df = pd.read_sql_query("SELECT player_id, player_name FROM Players", conn)
            logger.info(f"Loaded {len(players_df)} player names.")
            
            # Load feature data
            features_df = pd.read_sql_query("SELECT * FROM PlayerArchetypeFeatures_2022_23", conn)
            logger.info(f"Loaded {len(features_df)} records from PlayerArchetypeFeatures_2022_23.")

        # Load archetype assignments
        archetypes_df = pd.read_csv(ARCHETYPES_CSV_PATH)
        logger.info(f"Loaded {len(archetypes_df)} archetype assignments from CSV.")
        
        return players_df, features_df, archetypes_df

    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise

def merge_data(players_df, features_df, archetypes_df):
    """Merges all data sources into a single DataFrame."""
    logger.info("Merging data sources...")
    # Merge archetypes with player names
    merged_df = pd.merge(archetypes_df, players_df, on='player_id')
    # Merge with features
    full_df = pd.merge(merged_df, features_df, on='player_id')
    logger.info("Data merged successfully.")
    return full_df

def analyze_archetypes(df):
    """Analyzes and prints a summary for each archetype."""
    logger.info("Analyzing archetypes...")
    
    feature_columns = df.drop(columns=['player_id', 'player_name', 'archetype_id', 'season', 'team_id']).columns
    
    # Calculate global means and std deviations for Z-score calculation
    global_means = df[feature_columns].mean()
    global_stds = df[feature_columns].std()

    # Get a list of well-known players to highlight if they appear
    # Sourced from the validation script in the project
    well_known_players = {
        2544: "LeBron James", 201142: "Stephen Curry", 201935: "Kevin Durant",
        201939: "James Harden", 201144: "Russell Westbrook", 1628369: "Jayson Tatum",
        203999: "Nikola Jokic", 203507: "Giannis Antetokounmpo", 1629029: "Luka Doncic",
        203954: "Joel Embiid", 101108: "Chris Paul", 1628386: "De'Aaron Fox"
    }
    
    for archetype_id in sorted(df['archetype_id'].unique()):
        archetype_df = df[df['archetype_id'] == archetype_id]
        
        print("\n" + "="*50)
        print(f"ARCHETYPE {archetype_id} ANALYSIS")
        print("="*50)
        print(f"Total Players: {len(archetype_df)}")
        
        # Highlight well-known players in this archetype
        known_players_in_archetype = [
            p_name for p_id, p_name in well_known_players.items() 
            if p_id in archetype_df['player_id'].values
        ]
        if known_players_in_archetype:
            print(f"Prominent Players: {', '.join(known_players_in_archetype)}")
        else:
            # Show a sample of other players if no well-known ones are found
            sample_players = archetype_df['player_name'].head(5).tolist()
            print(f"Sample Players: {', '.join(sample_players)}")

        print("\n--- Defining Statistical Profile ---")
        
        # Calculate Z-scores for the archetype's mean stats
        archetype_means = archetype_df[feature_columns].mean()
        z_scores = (archetype_means - global_means) / global_stds
        
        print("Top 5 Positive Characteristics (Higher than average):")
        for feature, z_score in z_scores.nlargest(5).items():
            print(f"  - {feature}: {archetype_means[feature]:.2f} (Z-score: {z_score:+.2f})")
            
        print("\nTop 5 Negative Characteristics (Lower than average):")
        for feature, z_score in z_scores.nsmallest(5).items():
            print(f"  - {feature}: {archetype_means[feature]:.2f} (Z-score: {z_score:+.2f})")

def main():
    """Main function to run the archetype analysis."""
    try:
        players_df, features_df, archetypes_df = load_data()
        full_df = merge_data(players_df, features_df, archetypes_df)
        analyze_archetypes(full_df)
    except Exception as e:
        logger.error(f"An error occurred during analysis: {e}")
        raise

if __name__ == "__main__":
    main()

