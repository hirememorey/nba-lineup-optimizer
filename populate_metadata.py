import sqlite3
import sys
from nba_api.stats.static import teams, players

DB_FILE = "nba_lineup_data.db"
SEASON_ID = "2024-25" # Assuming this is the target season

def populate_base_metadata():
    """Populates Seasons, Teams, and Players tables in the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 1. Populate Seasons
        # Using INSERT OR IGNORE to avoid error if the season already exists
        print(f"Inserting season: {SEASON_ID}")
        cursor.execute("INSERT OR IGNORE INTO Seasons (season_id) VALUES (?)", (SEASON_ID,))

        # 2. Populate Teams
        print("Fetching team data from nba_api...")
        nba_teams = teams.get_teams()
        if not nba_teams:
            print("Error: Could not fetch team data.", file=sys.stderr)
            return # Or raise an exception

        print(f"Inserting {len(nba_teams)} teams...")
        teams_data = [(team['id'], team['full_name'], team['abbreviation']) for team in nba_teams]
        # Using INSERT OR IGNORE to handle potential duplicates gracefully
        cursor.executemany("INSERT OR IGNORE INTO Teams (team_id, team_name, team_abbreviation) VALUES (?, ?, ?)", teams_data)

        # 3. Populate Players
        print("Fetching player data from nba_api...")
        nba_players = players.get_players()
        if not nba_players:
            print("Error: Could not fetch player data.", file=sys.stderr)
            return # Or raise an exception

        print(f"Inserting {len(nba_players)} players...")
        # Filter for active players if needed, though storing all might be fine
        # players_data = [(player['id'], player['full_name']) for player in nba_players if player['is_active']]
        players_data = [(player['id'], player['full_name']) for player in nba_players]
        # Using INSERT OR IGNORE
        cursor.executemany("INSERT OR IGNORE INTO Players (player_id, player_name) VALUES (?, ?)", players_data)

        conn.commit()
        print("Metadata populated successfully.")

    except sqlite3.Error as e:
        print(f"Database error occurred: {e}", file=sys.stderr)
        if conn:
            conn.rollback() # Roll back changes on error
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    populate_base_metadata() 