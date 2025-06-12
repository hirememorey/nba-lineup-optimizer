import sqlite3
import os

def main():
    """Connects to the database and prints the row count for each table."""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'nba_stats.db')
    print(f"Connecting to database at: {db_path}")

    if not os.path.exists(db_path):
        print("Database file not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in the database.")
            return

        print("\\n--- Table Row Counts ---")
        for table_name_tuple in tables:
            table_name = table_name_tuple[0]
            if table_name == 'sqlite_sequence': # Skip internal tables
                continue
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"- {table_name}: {count} rows")
        print("------------------------\\n")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main() 