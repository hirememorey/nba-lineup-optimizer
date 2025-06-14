"""
This script executes the data verification and preparation steps for Phase 1
of the 'Algorithmic NBA Player Acquisition' project.
"""

import sqlite3
import pandas as pd
import logging
import sys
import os
from pathlib import Path

# Add the project root to the Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(PROJECT_ROOT)

from src.nba_stats.db.database import get_db_connection
from src.nba_stats.config.settings import DB_PATH, SEASON_ID

# --- New imports for clustering ---
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def verify_existing_data(conn: sqlite3.Connection):
    """
    Confirms that all necessary tables exist and contain data for the target season.
    """
    logging.info("--- Verifying Existing Data ---")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]

        if not tables:
            logging.warning("No tables found in the database.")
            return

        logging.info("Found tables:")
        for table in sorted(tables):
            try:
                count_query = f'SELECT COUNT(*) FROM "{table}"'
                count = pd.read_sql_query(count_query, conn).iloc[0, 0]
                logging.info(f"- {table}: {count} rows")
            except Exception as e:
                logging.error(f"Could not get row count for table {table}: {e}")
        
    except sqlite3.Error as e:
        logging.error(f"An error occurred while verifying tables: {e}")

def acquire_external_data(conn: sqlite3.Connection):
    """
    Acquires and integrates external datasets like DARKO ratings and player salaries.
    """
    logging.info("--- Acquiring External Data ---")
    
    # 1. Load DARKO Data
    try:
        darko_df = pd.read_csv(os.path.join(PROJECT_ROOT, 'data', 'darko_dpm_2024-25.csv'))
        logging.info(f"Loaded {len(darko_df)} records from DARKO CSV.")
        
        # Select and rename columns to match our schema
        darko_df = darko_df[['Player', 'O-DPM', 'D-DPM']].rename(columns={
            'Player': 'player_name',
            'O-DPM': 'o_darko',
            'D-DPM': 'd_darko'
        })
        
        # Get player IDs from the database
        players_df = pd.read_sql_query("SELECT player_id, player_name FROM Players", conn)
        
        # Merge DARKO data with player IDs
        merged_df = pd.merge(darko_df, players_df, on='player_name', how='inner')
        
        if len(merged_df) == 0:
            logging.warning("No matching players found between DARKO data and Players table.")
            return

        # Prepare data for insertion
        merged_df['season_id'] = SEASON_ID
        skill_data = merged_df[['player_id', 'season_id', 'o_darko', 'd_darko']]

        # Create PlayerSkills table
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS PlayerSkills (
            player_skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            season_id TEXT,
            o_darko REAL,
            d_darko REAL,
            FOREIGN KEY (player_id) REFERENCES Players (player_id)
        );
        """)
        logging.info("Created 'PlayerSkills' table.")

        # Insert data into PlayerSkills
        skill_data.to_sql('PlayerSkills', conn, if_exists='append', index=False)
        logging.info(f"Inserted {len(skill_data)} records into 'PlayerSkills' table.")

    except FileNotFoundError:
        logging.error("DARKO CSV file not found. Please ensure 'data/darko_dpm_2024-25.csv' exists.")
    except Exception as e:
        logging.error(f"An error occurred while acquiring DARKO data: {e}")

def acquire_salary_data(conn: sqlite3.Connection):
    """
    Acquires player salary data and integrates it into the database.
    """
    logging.info("--- Acquiring Player Salary Data ---")
    
    # 1. Load Salary Data
    try:
        salary_df = pd.read_csv(os.path.join(PROJECT_ROOT, 'data', 'player_salaries_2024-25.csv'))
        logging.info(f"Loaded {len(salary_df)} records from Salary CSV.")
        
        # 2. Rename columns for consistency
        salary_df.rename(columns={'Player': 'PlayerName'}, inplace=True)
        
        # 3. Create PlayerSalaries table
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS PlayerSalaries (
            PlayerName TEXT PRIMARY KEY,
            Salary INTEGER
        )
        """)
        logging.info("Created 'PlayerSalaries' table.")
        
        # 4. Insert data into the table
        salary_df.to_sql('PlayerSalaries', conn, if_exists='replace', index=False)
        
        logging.info(f"Successfully inserted {len(salary_df)} records into 'PlayerSalaries' table.")
        
    except FileNotFoundError:
        logging.error("Salary data file not found.")
    except Exception as e:
        logging.error(f"An error occurred during salary data acquisition: {e}")

def verify_archetype_features(conn: sqlite3.Connection):
    """
    Verifies that all 48 player archetype features are present in the database.
    """
    logging.info("--- Verifying Archetype Features ---")

    # This map translates the paper's conceptual features to our actual DB columns.
    FEATURE_MAP = {
        # Paper Name: DB Column Name
        # Basic
        "GP": "games_played",
        "MIN": "minutes_played",
        # Shooting
        "FGA": "field_goals_attempted",
        "FG_PCT": "field_goal_percentage",
        "FG3A": "three_pointers_attempted",
        "FG3_PCT": "three_point_percentage",
        "FTA": "free_throws_attempted",
        "FT_PCT": "free_throw_percentage",
        "EFG_PCT": "effective_field_goal_percentage",
        "TS_PCT": "true_shooting_percentage",
        # Shooting by Location (Approximated)
        "FG_PCT_0_3": "restricted_area_fg_pct",
        "FG_PCT_3_10": "in_the_paint_non_ra_fg_pct",
        "FG_PCT_10_16": "mid_range_fg_pct", # Approximation
        "FG_PCT_16_3P": "mid_range_fg_pct", # Approximation
        "PCT_AST_2PM": "pct_ast_2pm",
        "PCT_AST_3PM": "pct_ast_3pm",
        # Defense
        "DREB": "defensive_rebounds",
        "STL": "steals",
        "BLK": "blocks",
        "D_DPM": "D_DPM", 
        # Passing
        "AST": "assists",
        "TOV": "turnovers",
        # Athleticism/Physical
        "HEIGHT": "height",
        "WINGSPAN": "wingspan",
        "AVG_SHOT_DIST": "avg_shot_distance",
        # Advanced
        "USG_PCT": "usage_percentage",
        "PIE": "pie",
        "AST_RATIO": "assist_ratio",
        "AST_TO_TOV": "assist_to_turnover_ratio",
        "REB_PCT": "rebound_percentage",
        "DREB_PCT": "defensive_rebound_percentage",
        "OREB_PCT": "offensive_rebound_percentage",
        "PACE": "pace",
        "POSS": "possessions"
    }

    # Features we know are missing (e.g., from Synergy)
    MISSING_PLAY_TYPES = {
        "PCT_ISO", "PCT_TRANSITION", "PCT_PRB", "PCT_PRR", "PCT_POST_UP",
        "PCT_SPOT_UP", "PCT_HND_OFF", "PCT_CUT", "PCT_OFF_SCREEN", "PCT_PUTBACKS"
    }
    
    REQUIRED_COUNT = 48

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        db_columns = set()
        for table_tuple in tables:
            table_name = table_tuple[0]
            if "Player" in table_name or "player" in table_name:
                try:
                    cursor.execute(f"PRAGMA table_info('{table_name}')")
                    columns = [info[1].lower() for info in cursor.fetchall()] # Use lowercase for case-insensitive matching
                    db_columns.update(columns)
                except sqlite3.OperationalError as e:
                    logging.warning(f"Could not read schema for table {table_name}: {e}")

        found_features = set()
        missing_features = set()

        for paper_name, db_name in FEATURE_MAP.items():
            if db_name.lower() in db_columns:
                found_features.add(paper_name)
            else:
                missing_features.add(f"{paper_name} (expected: {db_name})")
        
        # Account for known missing play types
        total_found = len(found_features)
        logging.info(f"Found {total_found} of the mappable features.")
        logging.warning(f"Known missing play-type features (require Synergy data): {len(MISSING_PLAY_TYPES)}")
        logging.info(f"Total features accounted for: {total_found + len(MISSING_PLAY_TYPES)}/{REQUIRED_COUNT}")

        if missing_features:
            logging.warning(f"MISSING or MISNAMED features: {sorted(list(missing_features))}")
        
        if not missing_features:
            logging.info("All mappable archetype features are present.")

    except Exception as e:
        logging.error(f"An error occurred during feature verification: {e}")

def cluster_player_archetypes(conn: sqlite3.Connection, season_id: str):
    """
    Performs K-means clustering on player archetype features to assign archetypes.
    """
    logging.info("--- Clustering Player Archetypes ---")
    
    try:
        # 1. Load data from PlayerArchetypeFeatures
        features_df = pd.read_sql_query(f"SELECT * FROM PlayerArchetypeFeatures WHERE season = '{season_id}'", conn)
        
        if features_df.empty:
            logging.error(f"No feature data found for season {season_id}. Aborting clustering.")
            return

        logging.info(f"Loaded {len(features_df)} players for clustering.")
        
        # 2. Define the 48 features for clustering
        feature_columns = [
            'FTPCT', 'TSPCT', 'THPAr', 'FTr', 'TRBPCT', 'ASTPCT', 'AVGDIST', 'Zto3r',
            'THto10r', 'TENto16r', 'SIXTto3PTr', 'HEIGHT', 'WINGSPAN', 'FRNTCTTCH',
            'TOP', 'AVGSECPERTCH', 'AVGDRIBPERTCH', 'ELBWTCH', 'POSTUPS', 'PNTTOUCH',
            'DRIVES', 'DRFGA', 'DRPTSPCT', 'DRPASSPCT', 'DRASTPCT', 'DRTOVPCT',
            'DRPFPCT', 'DRIMFGPCT', 'CSFGA', 'CS3PA', 'PASSESMADE', 'SECAST',
            'POTAST', 'PUFGA', 'PU3PA', 'PSTUPFGA', 'PSTUPPTSPCT', 'PSTUPPASSPCT',
            'PSTUPASTPCT', 'PSTUPTOVPCT', 'PNTTCHS', 'PNTFGA', 'PNTPTSPCT',
            'PNTPASSPCT', 'PNTASTPCT', 'PNTTVPCT', 'AVGFGATTEMPTEDAGAINSTPERGAME'
        ]

        # Check if all feature columns exist in the DataFrame
        missing_cols = [col for col in feature_columns if col not in features_df.columns]
        if missing_cols:
            logging.error(f"The following required feature columns are missing from 'PlayerArchetypeFeatures': {missing_cols}")
            return
            
        # 3. Prepare data for clustering
        X = features_df[feature_columns].copy()
        X.fillna(0, inplace=True) # Ensure no NaN values are passed to the scaler

        # 4. Standardize the features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        logging.info("Standardized feature data.")

        # 5. Determine K using the Elbow Method and create plot
        sse = []
        k_range = range(1, 16)
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto')
            kmeans.fit(X_scaled)
            sse.append(kmeans.inertia_)

        # Plotting the elbow curve
        plt.figure(figsize=(10, 6))
        plt.plot(k_range, sse, marker='o')
        plt.title('Elbow Method for Optimal K')
        plt.xlabel('Number of Clusters (K)')
        plt.ylabel('Sum of Squared Errors (SSE)')
        plt.xticks(k_range)
        plt.grid(True)
        
        # Save the plot
        plot_dir = Path(PROJECT_ROOT) / "src" / "nba_stats" / "data" / "plots"
        plot_dir.mkdir(parents=True, exist_ok=True)
        plot_path = plot_dir / "archetype_elbow_plot.png"
        plt.savefig(plot_path)
        logging.info(f"Saved elbow plot to {plot_path}")
        plt.close()

        # 6. Perform K-means clustering with K=8
        K = 8
        kmeans = KMeans(n_clusters=K, random_state=42, n_init='auto')
        kmeans.fit(X_scaled)
        logging.info(f"Performed K-means clustering with K={K}.")

        # 7. Save the results to the database
        results_df = features_df[['player_id', 'season']].copy()
        results_df['archetype_id'] = kmeans.labels_ # Labels are 0-indexed

        # Create and populate the new table
        results_df.to_sql('PlayerSeasonArchetypes', conn, if_exists='replace', index=False)
        
        logging.info(f"Successfully saved {len(results_df)} player archetype assignments to 'PlayerSeasonArchetypes' table.")

    except Exception as e:
        logging.error(f"An error occurred during player archetype clustering: {e}", exc_info=True)

def main():
    """
    Main function to run Phase 1 steps.
    """
    logging.info("--- Starting Phase 1: Data Verification and Preparation ---")
    
    conn = None
    try:
        conn = get_db_connection()
        verify_existing_data(conn)
        acquire_external_data(conn)
        acquire_salary_data(conn)
        verify_archetype_features(conn)
        cluster_player_archetypes(conn, SEASON_ID)
        
    except sqlite3.Error as e:
        logging.error(f"A database error occurred: {e}")
    finally:
        if conn:
            conn.close()
        logging.info("--- Phase 1 Finished ---")

if __name__ == "__main__":
    main() 