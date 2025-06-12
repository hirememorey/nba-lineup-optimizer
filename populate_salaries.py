import sqlite3
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import sys
import re
# New import for fuzzy matching
from thefuzz import process
# New import for unicode normalization
import unicodedata

DB_FILE = "nba_lineup_data.db"
SEASON_ID = "2024-25"
SALARY_SOURCE = "HoopsHype"
# URL for HoopsHype NBA Player Salaries for the 2024-25 season
# Verify this URL is correct and points to the right season's data
HOOPSHYPE_URL = "https://hoopshype.com/salaries/players/"
# Fuzzy matching threshold (adjust as needed, 0-100)
FUZZY_MATCH_THRESHOLD = 90

def normalize_name(name):
    """Normalizes a name by lowercasing, removing accents (NFKD), and stripping whitespace."""
    if not isinstance(name, str):
        return ""
    # NFKD decomposes characters (e.g., 'é' -> 'e' + combining accent)
    # Encoding to ascii with 'ignore' removes the combining accents
    # Decoding back to utf-8 and lowercasing
    normalized = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')
    return normalized.lower().strip()

def get_player_name_id_map(cursor):
    """Fetches mappings from normalized player name to player_id from the database."""
    cursor.execute("SELECT player_name, player_id FROM Players")
    results = cursor.fetchall()
    # Map from normalized name to ID
    normalized_player_map = {normalize_name(name): player_id for name, player_id in results}
    # List of normalized names for fuzzy matching
    db_player_names_normalized = list(normalized_player_map.keys())
    # Keep original names for potential logging/debugging if needed (optional)
    # original_names_map = {player_id: name for name, player_id in results}
    return normalized_player_map, db_player_names_normalized

def parse_salary(salary_str):
    """Converts a salary string (e.g., '$50,000,000') to a float."""
    if not isinstance(salary_str, str):
        return None
    # Remove $, commas, and whitespace
    cleaned = re.sub(r'[\$,\s]', '', salary_str)
    try:
        return float(cleaned)
    except ValueError:
        return None # Handle cases where conversion fails

def populate_salaries():
    """Scrapes HoopsHype for player salaries and inserts them into the database, using normalization and fuzzy matching."""
    print(f"Starting salary population from {SALARY_SOURCE} for {SEASON_ID} (with Unicode normalization)...")
    conn = None
    try:
        # --- Fetch Player Name to ID mapping from DB ---
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # Get the normalized maps and list needed
        normalized_player_map, db_player_names_normalized = get_player_name_id_map(cursor)
        if not normalized_player_map:
            print("Error: Could not fetch player map from database.", file=sys.stderr)
            return
        print(f"Fetched {len(normalized_player_map)} normalized player names from database for matching.")

        # --- Scrape HoopsHype ---
        print(f"Fetching data from {HOOPSHYPE_URL}...")
        headers = {'User-Agent': 'Mozilla/5.0'} # Be a polite scraper
        response = requests.get(HOOPSHYPE_URL, headers=headers)
        response.raise_for_status() # Raise an exception for bad status codes
        time.sleep(1) # Wait a second before processing

        # Using pandas.read_html
        try:
            import io
            salary_tables = pd.read_html(io.StringIO(response.text), attrs = {'class': 'hh-salaries-ranking-table'})
            if not salary_tables:
                 raise ValueError("Could not find the salary table using pandas.read_html. Check table class/structure.")
            df = salary_tables[0]
            print(f"Successfully parsed table using pandas.read_html. Found {len(df)} rows.")
        except ValueError as e:
             print(f"pandas.read_html failed: {e}. Manual parsing might be needed or table structure changed.", file=sys.stderr)
             return

        # --- Process and Prepare Data ---
        salaries_to_insert = []
        exact_match_count = 0
        fuzzy_match_count = 0
        unmatched_names = [] # Store original scraped names for reporting
        skipped_salary_parse = 0

        # Adjust column names based on the actual table structure
        player_col_name = 'Player'
        salary_col_name = df.columns[2] # Still assuming 3rd column, VERIFY
        print(f"Using Player column: '{player_col_name}', Salary column: '{salary_col_name}'")

        if player_col_name not in df.columns or salary_col_name not in df.columns:
            print(f"Error: Expected columns '{player_col_name}' or '{salary_col_name}' not found in table.", file=sys.stderr)
            print(f"Available columns: {df.columns.tolist()}", file=sys.stderr)
            return

        for index, row in df.iterrows():
            player_name_scraped = str(row[player_col_name]) # Keep original for reporting
            salary_str = row[salary_col_name]

            if pd.isna(player_name_scraped) or player_name_scraped == "" or pd.isna(salary_str):
                continue # Skip rows with missing data

            # Normalize the scraped name for matching
            name_scraped_normalized = normalize_name(player_name_scraped)
            salary = parse_salary(str(salary_str))

            if salary is None:
                skipped_salary_parse += 1
                continue

            player_id = None
            matched_how = None

            # 1. Try exact match on normalized names
            if name_scraped_normalized in normalized_player_map:
                player_id = normalized_player_map[name_scraped_normalized]
                exact_match_count += 1
                matched_how = "Exact (Normalized)"
            else:
                # 2. Try fuzzy match on normalized names if exact failed
                best_match = process.extractOne(name_scraped_normalized, db_player_names_normalized)
                if best_match and best_match[1] >= FUZZY_MATCH_THRESHOLD:
                    matched_db_name_normalized = best_match[0]
                    player_id = normalized_player_map.get(matched_db_name_normalized)
                    if player_id:
                        # print(f"Fuzzy match: '{player_name_scraped}' (Normalized: '{name_scraped_normalized}') -> '{matched_db_name_normalized}' (Score: {best_match[1]})")
                        fuzzy_match_count += 1
                        matched_how = "Fuzzy (Normalized)"
                    else:
                         print(f"Warning: Fuzzy match found ('{matched_db_name_normalized}') but failed to get ID.", file=sys.stderr)

            # If a match was found
            if player_id:
                salaries_to_insert.append((player_id, SEASON_ID, salary, SALARY_SOURCE))
            else:
                # Still no match
                unmatched_names.append(player_name_scraped) # Store original name

        print(f"--- Match Summary ---")
        print(f"Total rows processed: {len(df)}")
        print(f"Skipped (unparsable salary): {skipped_salary_parse}")
        print(f"Exact matches (normalized): {exact_match_count}")
        print(f"Fuzzy matches (normalized, Score >= {FUZZY_MATCH_THRESHOLD}): {fuzzy_match_count}")
        total_matched = exact_match_count + fuzzy_match_count
        print(f"Total matches: {total_matched}")
        print(f"Remaining unmatched: {len(unmatched_names)}")
        if unmatched_names:
            print(f"Unmatched examples: {unmatched_names[:10]}...")

        # --- Insert into Database ---
        if salaries_to_insert:
            print(f"Inserting/updating {len(salaries_to_insert)} salary records into database...")
            cursor.executemany("INSERT OR IGNORE INTO PlayerSalaries (player_id, season_id, salary, salary_source) VALUES (?, ?, ?, ?)", salaries_to_insert)
            conn.commit()
            print("Salaries inserted/updated successfully.")
        else:
            print("No new salary data to insert.")

    except requests.exceptions.RequestException as e:
        print(f"HTTP Error fetching URL: {e}", file=sys.stderr)
    except (ValueError, IndexError, AttributeError) as e:
        print(f"Error parsing HTML or DataFrame: {e}", file=sys.stderr)
    except sqlite3.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    populate_salaries() 