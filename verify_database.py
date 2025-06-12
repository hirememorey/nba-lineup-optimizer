import sqlite3
import pandas as pd
from tabulate import tabulate

DB_FILE = "nba_lineup_data.db"

def get_db_connection():
    """Creates and returns a database connection."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def verify_database():
    """Verifies database structure and data completeness."""
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        
        # 1. Check table structure
        print("\n=== Database Structure ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Found {len(tables)} tables:")
        for table in tables:
            table_name = table['name']
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print(f"\n{table_name} ({len(columns)} columns):")
            print(tabulate(columns, headers=['cid', 'name', 'type', 'notnull', 'dflt_value', 'pk']))

        # 2. Count records in each table
        print("\n=== Record Counts ===")
        for table in tables:
            table_name = table['name']
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            count = cursor.fetchone()['count']
            print(f"{table_name}: {count} records")

        # 3. Check Teams table completeness
        print("\n=== Teams Table Verification ===")
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT team_id) as unique_ids,
                   COUNT(DISTINCT team_abbreviation) as unique_abbrs
            FROM Teams
        """)
        team_stats = cursor.fetchone()
        print(f"Total teams: {team_stats['total']}")
        print(f"Unique team IDs: {team_stats['unique_ids']}")
        print(f"Unique team abbreviations: {team_stats['unique_abbrs']}")

        # 4. Check PlayerSeasonRawStats completeness
        print("\n=== Player Stats Verification ===")
        cursor.execute("""
            SELECT 
                COUNT(*) as total_players,
                COUNT(DISTINCT player_id) as unique_players,
                COUNT(CASE WHEN minutes_played >= 1000 THEN 1 END) as players_1000_min,
                COUNT(CASE WHEN FTPCT IS NOT NULL THEN 1 END) as players_with_ftpct,
                COUNT(CASE WHEN TSPCT IS NOT NULL THEN 1 END) as players_with_tspct,
                COUNT(CASE WHEN AVGFGATTEMPTEDAGAINSTPERGAME IS NOT NULL THEN 1 END) as players_with_defense
            FROM PlayerSeasonRawStats
        """)
        stats = cursor.fetchone()
        print(f"Total player records: {stats['total_players']}")
        print(f"Unique players: {stats['unique_players']}")
        print(f"Players with 1000+ minutes: {stats['players_1000_min']}")
        print(f"Players with free throw %: {stats['players_with_ftpct']}")
        print(f"Players with true shooting %: {stats['players_with_tspct']}")
        print(f"Players with defensive stats: {stats['players_with_defense']}")

        # 5. Sample some player data
        print("\n=== Sample Player Data ===")
        cursor.execute("""
            SELECT p.player_id, p.minutes_played, p.FTPCT, p.TSPCT, p.AVGFGATTEMPTEDAGAINSTPERGAME,
                   t.team_abbreviation
            FROM PlayerSeasonRawStats p
            JOIN Teams t ON p.team_id = t.team_id
            WHERE p.minutes_played >= 1000
            ORDER BY p.minutes_played DESC
            LIMIT 5
        """)
        sample_players = cursor.fetchall()
        print("\nTop 5 players by minutes played:")
        print(tabulate(sample_players, headers='keys', tablefmt='grid'))

        # 6. Check for any missing critical data
        print("\n=== Missing Data Check ===")
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM PlayerSeasonRawStats
            WHERE minutes_played IS NULL 
               OR FTPCT IS NULL 
               OR TSPCT IS NULL 
               OR AVGFGATTEMPTEDAGAINSTPERGAME IS NULL
        """)
        missing_data = cursor.fetchone()['count']
        print(f"Players with missing critical stats: {missing_data}")

    except sqlite3.Error as e:
        print(f"Database error during verification: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    verify_database() 