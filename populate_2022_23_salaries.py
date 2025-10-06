#!/usr/bin/env python3
"""
Script to populate 2022-23 salary data from Kaggle CSV into the NBA Lineup Optimizer database.
This integrates the salary data needed for Phase 1 ground truth validation.
"""

import sqlite3
import csv
import os
import sys
import unicodedata
from typing import Dict, Tuple


# Database and CSV paths
DB_PATH = os.path.join(os.path.dirname(__file__), 'src', 'nba_stats', 'db', 'nba_stats.db')
CSV_PATH = os.path.join(os.path.dirname(__file__), 'data', 'nba_salaries_2022-23.csv')
SEASON_ID = "2022-23"

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
    """Parses the Kaggle CSV of 2022-23 player salaries and inserts them into the database."""
    print(f"Starting 2022-23 salary population from Kaggle CSV...")

    if not os.path.exists(CSV_PATH):
        print(f"Error: Salary CSV file not found at {CSV_PATH}", file=sys.stderr)
        return

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

        print(f"Found {len(player_name_map)} players in database")

        # 2. Make the script idempotent: Delete existing entries for the season
        print(f"Deleting existing salary records for season {SEASON_ID} to prevent duplicates...")
        cursor.execute("DELETE FROM PlayerSalaries WHERE season_id = ?", (SEASON_ID,))

        # 3. Read the CSV and prepare data for insertion
        salaries_to_insert: list[Tuple[int, str, float]] = []
        unmatched_names: list[str] = []
        matched_count = 0

        with open(CSV_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            total_rows = 0

            for row in reader:
                total_rows += 1
                player_name_csv = row.get('Player Name')
                salary_str = row.get('Salary')

                if not player_name_csv or not salary_str:
                    continue

                normalized_name = normalize_name(player_name_csv)
                player_id = player_name_map.get(normalized_name)

                if player_id:
                    try:
                        salary = float(salary_str)
                        salaries_to_insert.append((player_id, SEASON_ID, salary))
                        matched_count += 1
                    except (ValueError, TypeError):
                        print(f"Warning: Could not parse salary for {player_name_csv}: '{salary_str}'", file=sys.stderr)
                else:
                    unmatched_names.append(player_name_csv)

        print(f"Processed {total_rows} total rows from CSV")
        print(f"Found {matched_count} matching players for salary insertion")

        # 4. Perform bulk insert
        if salaries_to_insert:
            print(f"Inserting {len(salaries_to_insert)} salary records into database...")
            cursor.executemany(
                "INSERT INTO PlayerSalaries (player_id, season_id, salary) VALUES (?, ?, ?)",
                salaries_to_insert
            )
            conn.commit()
            print("✅ Successfully inserted salary data.")
        else:
            print("❌ No salary data was inserted.")

        if unmatched_names:
            print(f"\n⚠️  Could not find a match for {len(unmatched_names)} players in the database.")
            print(f"Sample unmatched names: {unmatched_names[:10]}...")
            print(f"Total unmatched: {len(unmatched_names)}")

        # 5. Summary
        print("\n📊 Integration Summary:")
        print(f"   • CSV rows processed: {total_rows}")
        print(f"   • Players matched: {matched_count}")
        print(f"   • Players unmatched: {len(unmatched_names)}")
        print(f"   • Match rate: {matched_count/total_rows*100:.1f}%" if total_rows > 0 else "   • Match rate: 0%")

        # 6. Verify insertion
        cursor.execute("SELECT COUNT(*) FROM PlayerSalaries WHERE season_id = ?", (SEASON_ID,))
        inserted_count = cursor.fetchone()[0]
        print(f"   • Records in DB for {SEASON_ID}: {inserted_count}")

    except sqlite3.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
    finally:
        if 'conn' in locals() and conn:
            conn.close()


if __name__ == "__main__":
    populate_salaries_from_csv()
