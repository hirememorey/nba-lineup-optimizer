"""
This script populates the PlayerSeasonSkill table with data from a manually downloaded CSV file.
"""
import sqlite3
import csv
import os
import sys
import unicodedata
from typing import Dict, Tuple

# Correct database path, relative to the project root
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'nba_stats.db')
CSV_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'darko_dpm_2024-25.csv')
MAPPING_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'mappings', 'player_name_map.csv')
SEASON_ID = "2024-25"
SKILL_METRIC_SOURCE = "DARKO"

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


def load_name_mapping() -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    try:
        if os.path.exists(MAPPING_PATH):
            with open(MAPPING_PATH, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    csv_name = row.get('csv_name', '').strip()
                    db_name = row.get('db_name', '').strip()
                    if csv_name and db_name:
                        mapping[normalize_name(csv_name)] = db_name
    except Exception as e:
        print(f"Warning: failed to load name mapping: {e}", file=sys.stderr)
    return mapping

def populate_player_skill_from_csv():
    """Parses a CSV of player DARKO ratings and inserts them into the database."""
    print(f"Starting player skill population from CSV for season {SEASON_ID}...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys = ON;")
        except sqlite3.Error:
            pass

        # 1. Get player name to ID mapping
        player_name_map = get_player_name_id_map(cursor)
        if not player_name_map:
            print("Error: Could not fetch player map from the database. Please populate players first.", file=sys.stderr)
            return

        # 2. Make the script idempotent: Delete existing entries for the season
        print(f"Deleting existing player skill records for season {SEASON_ID} to prevent duplicates...")
        cursor.execute("DELETE FROM PlayerSkills WHERE season_id = ? AND skill_metric_source = ?", (SEASON_ID, SKILL_METRIC_SOURCE))
        
        # 3. Read the CSV and prepare data for insertion
        skills_to_insert: list[Tuple[int, str, float, float, str]] = []
        unmatched_names: list[str] = []

        name_mapping = load_name_mapping()

        with open(CSV_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                player_name_csv = row.get('Player')
                offensive_skill_str = row.get('O-DPM')
                defensive_skill_str = row.get('D-DPM')

                if not all([player_name_csv, offensive_skill_str, defensive_skill_str]):
                    continue

                mapped_name = name_mapping.get(normalize_name(player_name_csv), player_name_csv)
                normalized_name = normalize_name(mapped_name)
                player_id = player_name_map.get(normalized_name)

                if player_id:
                    try:
                        offensive_skill = float(offensive_skill_str)
                        defensive_skill = float(defensive_skill_str)
                        skills_to_insert.append((player_id, SEASON_ID, offensive_skill, defensive_skill, SKILL_METRIC_SOURCE))
                    except (ValueError, TypeError):
                        print(f"Warning: Could not parse skill ratings for {player_name_csv}", file=sys.stderr)
                else:
                    unmatched_names.append(player_name_csv)

        # 4. Perform bulk insert
        if skills_to_insert:
            print(f"Found {len(skills_to_insert)} matching players. Inserting into database...")
            cursor.executemany(
                """INSERT INTO PlayerSkills 
                   (player_id, season_id, offensive_skill_rating, defensive_skill_rating, skill_metric_source) 
                   VALUES (?, ?, ?, ?, ?)""",
                skills_to_insert
            )
            conn.commit()
            print("Successfully inserted player skill data.")
        else:
            print("No new player skill data was inserted.")

        if unmatched_names:
            print(f"\nWarning: Could not find a match for {len(unmatched_names)} players in the database.")
            print(f"Unmatched examples: {unmatched_names[:10]}...")

    except sqlite3.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
    except FileNotFoundError:
        print(f"Error: DARKO CSV file not found at {CSV_PATH}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    populate_player_skill_from_csv() 