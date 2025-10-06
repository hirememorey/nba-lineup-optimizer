#!/usr/bin/env python3
"""
Populate 2022-23 season data into the database using the pipeline results.
"""

import json
import sqlite3
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_pipeline_data():
    """Load the 2022-23 pipeline data."""
    with open('pipeline_results.json', 'r') as f:
        return json.load(f)

def create_2022_23_tables(conn):
    """Create tables for 2022-23 data if they don't exist."""
    cursor = conn.cursor()
    
    # Create PlayerSeasonRawStats table for 2022-23
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PlayerSeasonRawStats_2022_23 (
            player_id INTEGER,
            season TEXT,
            team_id INTEGER,
            points REAL,
            field_goals_made REAL,
            field_goals_attempted REAL,
            assists REAL,
            total_rebounds REAL,
            steals REAL,
            blocks REAL,
            turnovers REAL,
            minutes_played REAL,
            PRIMARY KEY (player_id, season)
        )
    """)
    
    # Create PlayerSeasonAdvancedStats table for 2022-23
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PlayerSeasonAdvancedStats_2022_23 (
            player_id INTEGER,
            season TEXT,
            team_id INTEGER,
            offensive_rating REAL,
            defensive_rating REAL,
            net_rating REAL,
            usage_percentage REAL,
            true_shooting_percentage REAL,
            effective_field_goal_percentage REAL,
            PRIMARY KEY (player_id, season)
        )
    """)
    
    # Create PlayerArchetypeFeatures table for 2022-23
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PlayerArchetypeFeatures_2022_23 (
            player_id INTEGER,
            season TEXT,
            team_id INTEGER,
            FTPCT REAL,
            TSPCT REAL,
            THPAr REAL,
            FTr REAL,
            TRBPCT REAL,
            ASTPCT REAL,
            FRNTCTTCH REAL,
            TOP REAL,
            AVGSECPERTCH REAL,
            AVGDRIBPERTCH REAL,
            ELBWTCH REAL,
            POSTUPS REAL,
            PNTTOUCH REAL,
            DRIVES REAL,
            DRFGA REAL,
            DRPTSPCT REAL,
            DRPASSPCT REAL,
            DRASTPCT REAL,
            DRTOVPCT REAL,
            DRPFPCT REAL,
            DRIMFGPCT REAL,
            CSFGA REAL,
            CS3PA REAL,
            PASSESMADE REAL,
            SECAST REAL,
            POTAST REAL,
            PUFGA REAL,
            PU3PA REAL,
            PSTUPFGA REAL,
            PSTUPPTSPCT REAL,
            PSTUPPASSPCT REAL,
            PSTUPASTPCT REAL,
            PSTUPTOVPCT REAL,
            PNTTCHS REAL,
            PNTFGA REAL,
            PNTPTSPCT REAL,
            PNTPASSPCT REAL,
            PNTASTPCT REAL,
            PNTTVPCT REAL,
            AVGFGATTEMPTEDAGAINSTPERGAME REAL,
            PRIMARY KEY (player_id, season)
        )
    """)
    
    conn.commit()
    logger.info("Created 2022-23 tables")

def populate_archetype_features(conn, pipeline_data):
    """Populate the PlayerArchetypeFeatures table with 2022-23 data."""
    cursor = conn.cursor()
    
    # Get all unique player IDs from the pipeline data
    all_player_ids = set()
    for metric_data in pipeline_data.values():
        if isinstance(metric_data, dict):
            all_player_ids.update(metric_data.keys())
    
    logger.info(f"Found {len(all_player_ids)} unique players in 2022-23 data")
    
    # Prepare the data for insertion
    archetype_data = []
    
    for player_id in all_player_ids:
        player_data = {
            'player_id': int(player_id),
            'season': '2022-23',
            'team_id': 0  # We'll need to get this from another source
        }
        
        # Add all available metrics
        for metric, metric_data in pipeline_data.items():
            if isinstance(metric_data, dict) and player_id in metric_data:
                player_data[metric] = metric_data[player_id]
            else:
                player_data[metric] = None
        
        archetype_data.append(player_data)
    
    # Insert the data
    if archetype_data:
        # Get the column names
        columns = list(archetype_data[0].keys())
        placeholders = ', '.join(['?' for _ in columns])
        column_names = ', '.join(columns)
        
        # Insert data
        insert_sql = f"""
            INSERT OR REPLACE INTO PlayerArchetypeFeatures_2022_23 
            ({column_names}) VALUES ({placeholders})
        """
        
        for player_data in archetype_data:
            values = [player_data.get(col) for col in columns]
            cursor.execute(insert_sql, values)
        
        conn.commit()
        logger.info(f"Inserted {len(archetype_data)} players into PlayerArchetypeFeatures_2022_23")
    
    return len(archetype_data)

def validate_data(conn):
    """Validate the populated data."""
    cursor = conn.cursor()
    
    # Check player count
    cursor.execute("SELECT COUNT(*) FROM PlayerArchetypeFeatures_2022_23")
    player_count = cursor.fetchone()[0]
    logger.info(f"Total players in 2022-23 data: {player_count}")
    
    # Check data completeness
    cursor.execute("""
        SELECT 
            COUNT(*) as total_players,
            COUNT(FTPCT) as ftpct_count,
            COUNT(TSPCT) as tspct_count,
            COUNT(DRIVES) as drives_count
        FROM PlayerArchetypeFeatures_2022_23
    """)
    
    stats = cursor.fetchone()
    logger.info(f"Data completeness - Total: {stats[0]}, FTPCT: {stats[1]}, TSPCT: {stats[2]}, DRIVES: {stats[3]}")
    
    # Check for some well-known players
    well_known_players = [2544, 201142, 201935, 201939, 201144]  # LeBron, Curry, Durant, etc.
    for player_id in well_known_players:
        cursor.execute("SELECT player_id FROM PlayerArchetypeFeatures_2022_23 WHERE player_id = ?", (player_id,))
        if cursor.fetchone():
            logger.info(f"✅ Found player {player_id} in 2022-23 data")
        else:
            logger.warning(f"❌ Player {player_id} not found in 2022-23 data")

def main():
    """Main function to populate 2022-23 data."""
    logger.info("Starting 2022-23 data population...")
    
    # Load pipeline data
    pipeline_data = load_pipeline_data()
    logger.info(f"Loaded pipeline data with {len(pipeline_data)} metrics")
    
    # Connect to database
    db_path = Path("src/nba_stats/db/nba_stats.db")
    if not db_path.exists():
        logger.error(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    
    try:
        # Create tables
        create_2022_23_tables(conn)
        
        # Populate archetype features
        player_count = populate_archetype_features(conn, pipeline_data)
        
        # Validate data
        validate_data(conn)
        
        logger.info(f"✅ Successfully populated 2022-23 data with {player_count} players")
        
    except Exception as e:
        logger.error(f"Error populating 2022-23 data: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
