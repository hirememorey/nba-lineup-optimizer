import sqlite3
import pandas as pd
import logging
from typing import List, Dict, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Assuming the script is run from the root of the project
DB_PATH = "src/nba_stats/db/nba_stats.db"

class DatabaseVerifier:
    """
    Connects to the NBA stats database and performs a series of checks to
    verify data integrity and readiness for the analysis phase.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.failed_checks = 0

    def connect(self):
        """Establish a connection to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            logging.info(f"Successfully connected to the database at {self.db_path}.")
        except sqlite3.Error as e:
            logging.error(f"Failed to connect to the database: {e}")
            raise

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed.")

    def _run_check(self, check_function, *args, **kwargs):
        """Wrapper to run a check function and handle exceptions."""
        try:
            check_function(*args, **kwargs)
        except AssertionError as e:
            logging.error(f"FAILED: {e}")
            self.failed_checks += 1
        except Exception as e:
            logging.error(f"An unexpected error occurred during check: {e}")
            self.failed_checks += 1
            
    def get_table_schema(self, table_name: str) -> Dict[str, str]:
        """Retrieve the schema for a given table."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            if not columns:
                 raise ValueError(f"Table '{table_name}' not found or has no columns.")
            return {col['name']: col['type'] for col in columns}
        except Exception as e:
            logging.error(f"Could not get schema for table {table_name}: {e}")
            return {}

    def verify_table_schemas(self):
        """
        Phase 1: Ground Truth - Verify the schema of critical tables.
        The schema is the law.
        """
        logging.info("--- Phase 1: Verifying Table Schemas (Ground Truth) ---")
        
        # Check 1: Games table schema
        games_schema = self.get_table_schema("Games")
        assert 'season_id' in games_schema, "Games table MUST have a 'season_id' column."
        logging.info("PASSED: `Games` table has a `season_id` column.")

        # Check 2: PlayerSalaries table schema
        salaries_schema = self.get_table_schema("PlayerSalaries")
        assert 'player_id' in salaries_schema, "PlayerSalaries table MUST have a 'player_id' column."
        assert 'season_id' in salaries_schema, "PlayerSalaries table MUST have a 'season_id' column."
        logging.info("PASSED: `PlayerSalaries` table has `player_id` and `season_id` columns.")

        # Check 3: PlayerSkills table schema
        skills_schema = self.get_table_schema("PlayerSkills")
        assert 'player_id' in skills_schema, "PlayerSkills table MUST have a 'player_id' column."
        assert 'season_id' in skills_schema, "PlayerSkills table MUST have a 'season_id' column."
        logging.info("PASSED: `PlayerSkills` table has `player_id` and `season_id` columns.")

    def verify_data_content(self):
        """
        Phase 2: Content Verification - Check row counts and data integrity.
        This runs only if the schema verification is successful.
        """
        logging.info("\n--- Phase 2: Verifying Data Content ---")

        cursor = self.conn.cursor()

        # Check 1: Team count
        cursor.execute("SELECT COUNT(*) FROM Teams;")
        team_count = cursor.fetchone()[0]
        assert team_count == 30, f"Expected 30 teams, but found {team_count}."
        logging.info(f"PASSED: Found {team_count} teams, as expected.")

        # Check 2: Game count for the 2024-25 season
        cursor.execute("SELECT COUNT(*) FROM Games WHERE season_id = '2024-25';")
        game_count = cursor.fetchone()[0]
        assert game_count == 1230, f"Expected 1230 games for '2024-25' season, but found {game_count}."
        logging.info(f"PASSED: Found {game_count} games for the 2024-25 season, as expected.")
        
        # Check 3: PlayerSalaries are all for the correct season
        cursor.execute("SELECT COUNT(*) FROM PlayerSalaries WHERE season_id != '2024-25';")
        bad_salary_seasons = cursor.fetchone()[0]
        assert bad_salary_seasons == 0, f"Found {bad_salary_seasons} records in PlayerSalaries not for the '2024-25' season."
        logging.info("PASSED: All `PlayerSalaries` records are for the '2024-25' season.")

        # Check 4: PlayerSkills are all for the correct season
        cursor.execute("SELECT COUNT(*) FROM PlayerSkills WHERE season_id != '2024-25';")
        bad_skill_seasons = cursor.fetchone()[0]
        assert bad_skill_seasons == 0, f"Found {bad_skill_seasons} records in PlayerSkills not for the '2024-25' season."
        logging.info("PASSED: All `PlayerSkills` records are for the '2024-25' season.")

        # Check 5: Foreign key integrity for PlayerSalaries
        cursor.execute("""
            SELECT COUNT(*) FROM PlayerSalaries ps
            LEFT JOIN Players p ON ps.player_id = p.player_id
            WHERE p.player_id IS NULL;
        """)
        orphaned_salaries = cursor.fetchone()[0]
        assert orphaned_salaries == 0, f"Found {orphaned_salaries} orphaned records in PlayerSalaries."
        logging.info("PASSED: No orphaned records found in `PlayerSalaries`.")

    def run_all_checks(self):
        """Run all verification checks in sequence."""
        self.connect()
        if not self.conn:
            return

        self._run_check(self.verify_table_schemas)
        
        # Only proceed to content checks if schema is okay
        if self.failed_checks == 0:
            self._run_check(self.verify_data_content)
        else:
            logging.warning("Skipping content verification due to schema validation failures.")
        
        self.close()

        if self.failed_checks > 0:
            logging.error(f"\nVerification finished with {self.failed_checks} failed check(s).")
        else:
            logging.info("\nVerification finished successfully. All checks passed!")


if __name__ == "__main__":
    verifier = DatabaseVerifier(DB_PATH)
    verifier.run_all_checks() 