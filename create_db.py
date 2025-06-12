import sqlite3
import os

DB_FILE = "nba_lineup_data.db"
SCHEMA_FILE = "schema.sql"

def create_database():
    """Creates the SQLite database and tables based on the schema file."""
    # Check if the database file already exists
    if os.path.exists(DB_FILE):
        print(f"Database file '{DB_FILE}' already exists.")
        # Optional: Ask user if they want to overwrite or exit
        # response = input("Overwrite? (y/N): ")
        # if response.lower() != 'y':
        #     print("Exiting without creating tables.")
        #     return
        # os.remove(DB_FILE)
        # print("Existing database file removed.")
        print("Assuming schema is already applied. If not, delete the file and rerun.")
        return

    # Check if schema file exists
    if not os.path.exists(SCHEMA_FILE):
        print(f"Error: Schema file '{SCHEMA_FILE}' not found.")
        return

    conn = None
    try:
        # Read the SQL schema
        with open(SCHEMA_FILE, 'r') as f:
            sql_script = f.read()

        # Connect to the database (this will create the file if it doesn't exist)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Execute the SQL script to create tables
        cursor.executescript(sql_script)
        print(f"Database '{DB_FILE}' created and schema applied successfully.")

        # Commit changes and close the connection
        conn.commit()

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        # Optional: Clean up db file if creation failed partially
        if os.path.exists(DB_FILE):
             if conn: conn.close() # Ensure connection is closed before removing
             os.remove(DB_FILE)
             print(f"Removed partially created database file '{DB_FILE}'.")
    except IOError as e:
        print(f"Error reading schema file '{SCHEMA_FILE}': {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_database() 