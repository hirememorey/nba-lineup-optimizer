import sqlite3
import csv
import os
import sys
import unicodedata
from typing import Dict, Tuple


# Correct database path, relative to the project root
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'nba_stats.db')
CSV_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'player_salaries_2024-25.csv')
SEASON_ID = "2024-25"

def normalize_name(name: str) -> str:
    """Normalizes a name by lowercasing, removing accents, and stripping whitespace."""
    if not isinstance(name, str):
        return ""
    normalized = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')
    return normalized.lower().strip()


def get_player_name_id_map(cursor: sqlite3.Cursor) -> Dict[str, int]:
    """Fetches a mapping from normalized player name to player_id from the database."""
    cursor.execute("SELECT player_name, player_id FROM Players")
    return {normalize_name(name): player_id for name, player_id in cursor.fetchall()}


def populate_salaries_from_csv():
    """Parses a CSV of player salaries and inserts them into the database."""
    print(f"Starting salary population from CSV for season {SEASON_ID}...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 1. Get player name to ID mapping
        player_name_map = get_player_name_id_map(cursor)
        if not player_name_map:
            print("Error: Could not fetch player map from the database. Please populate players first.", file=sys.stderr)
            return

        # 2. Make the script idempotent: Delete existing entries for the season
        print(f"Deleting existing salary records for season {SEASON_ID} to prevent duplicates...")
        cursor.execute("DELETE FROM PlayerSalaries WHERE season_id = ?", (SEASON_ID,))
        
        # 3. Read the CSV and prepare data for insertion
        salaries_to_insert: list[Tuple[int, str, float]] = []
        unmatched_names: list[str] = []

        with open(CSV_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                player_name_csv = row.get('Player')
                salary_str = row.get('Salary')

                if not player_name_csv or not salary_str:
                    continue

                normalized_name = normalize_name(player_name_csv)
                player_id = player_name_map.get(normalized_name)

                if player_id:
                    try:
                        salary = float(salary_str)
                        salaries_to_insert.append((player_id, SEASON_ID, salary))
                    except (ValueError, TypeError):
                        print(f"Warning: Could not parse salary for {player_name_csv}: '{salary_str}'", file=sys.stderr)
                else:
                    unmatched_names.append(player_name_csv)

        # 4. Perform bulk insert
        if salaries_to_insert:
            print(f"Found {len(salaries_to_insert)} matching players. Inserting into database...")
            cursor.executemany(
                "INSERT INTO PlayerSalaries (player_id, season_id, salary) VALUES (?, ?, ?)",
                salaries_to_insert
            )
            conn.commit()
            print("Successfully inserted salary data.")
        else:
            print("No new salary data was inserted.")

        if unmatched_names:
            print(f"\nWarning: Could not find a match for {len(unmatched_names)} players in the database.")
            print(f"Unmatched examples: {unmatched_names[:10]}...")

    except sqlite3.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
    except FileNotFoundError:
        print(f"Error: Salary CSV file not found at {CSV_PATH}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    # This allows the script to be run with `python -m nba_stats.scripts.populate_salaries`
    populate_salaries_from_csv()
