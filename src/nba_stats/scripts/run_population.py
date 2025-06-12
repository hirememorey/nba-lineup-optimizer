"""Orchestration script to populate NBA stats database by calling individual population modules."""

import sqlite3
import time
import logging
import sys
import argparse
import json
import importlib
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Set up basic logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from .common_utils import get_db_connection, logger # Assuming logger and get_db_connection are in common_utils
from ..db.init_db import init_database
from ..config import settings
from ..scripts.migrate_db import run_migrations

def load_population_config() -> List[Dict]:
    """Loads the population config from the JSON file and resolves the module functions."""
    config_path = Path(__file__).parent.parent / "config" / "population_config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)

    for step in config:
        if "module_name" in step and "function_name" in step:
            try:
                module = importlib.import_module(step["module_name"], package='src.nba_stats.scripts')
                step["module"] = getattr(module, step["function_name"])
            except (ImportError, AttributeError) as e:
                logger.error(f"Could not import function {step['function_name']} from {step['module_name']}: {e}")
                # Decide how to handle this - skip step, raise error, etc.
                # For now, let's just set module to None and it will fail later
                step["module"] = None
    return config


POPULATION_CONFIG = load_population_config()


def should_skip_step(
    conn: sqlite3.Connection,
    season: str,
    check_season_data: bool,
    table_name: str,
    column_name: Optional[str] = None,
    row_threshold: int = 100,
    special_check: bool = False,
) -> bool:
    """
    Determines if a population step should be skipped.
    """
    cursor = conn.cursor()

    if special_check and table_name == "Players":
        # Special check for Player Wingspan: run if many players are missing wingspan.
        try:
            cursor.execute("SELECT COUNT(*) FROM Players WHERE wingspan IS NULL OR wingspan = 0.0 OR wingspan = ''")
            missing_count = cursor.fetchone()[0]
            
            wingspan_threshold = 50 # Arbitrary threshold
            if missing_count > wingspan_threshold:
                logger.info(f"{missing_count} players missing wingspan data. Proceeding with population.")
                return False # Do not skip
            else:
                logger.info(f"Only {missing_count} players missing wingspan. Skipping population step.")
                return True # Skip
        except sqlite3.OperationalError as e:
            logger.error(f"Could not perform wingspan check due to a database error: {e}")
            return True # Skip on error to be safe

    if check_season_data:
        # If a column name is provided, check if it's populated for the given season
        if column_name:
            try:
                # Check if column exists first
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [info[1] for info in cursor.fetchall()]
                if column_name not in columns:
                    logger.warning(
                        f"Column '{column_name}' not found in '{table_name}'. Proceeding with population."
                    )
                    return False

                # Check for non-null values in the specified column for the season
                cursor.execute(
                    f"SELECT COUNT(*) FROM {table_name} WHERE season = ? AND {column_name} IS NOT NULL",
                    (season,),
                )
            except sqlite3.OperationalError:
                # This can happen if 'season' column doesn't exist. Fallback to general check.
                cursor.execute(
                    f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} IS NOT NULL"
                )

        else:
            # Check for any data in the table for the given season
            try:
                cursor.execute(
                    f"SELECT COUNT(*) FROM {table_name} WHERE season = ?", (season,)
                )
            except sqlite3.OperationalError:
                # Fallback for tables without a 'season' column
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")

        count = cursor.fetchone()[0]
        if count > row_threshold:
            # This is a bit of a messy way to generate the message, but it works
            log_msg = f"Table '{table_name}' "
            if (
                column_name
                and "season" in cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
            ):  # Check if season was in the select
                log_msg += f"already has {count} records with '{column_name}' populated for season {season}."
            elif column_name:
                log_msg += f"already has {count} records with '{column_name}' populated."
            elif "season" in [
                col[1]
                for col in cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
            ]:
                log_msg += f"already has {count} records for season {season}."
            else:
                log_msg += f"has {count} records."

            log_msg += " Skipping population."
            logger.info(log_msg)
            return True

    else:
        # For steps that don't need season-specific checks (like 'Teams'),
        # just check if the table has a minimum number of records.
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        if count > row_threshold:
            logger.info(
                f"Table '{table_name}' has {count} records. Skipping population."
            )
            return True

    return False

def run_population_module(module: Any, step_config: Dict[str, Any], season: str):
    """
    Runs the specified population module function.
    Now assumes a standardized function signature.
    """
    function_name = step_config.get("function_name")
    takes_season_arg = step_config.get("takes_season_arg", False)
    
    try:
        if takes_season_arg:
            module(season_to_load=season)
        else:
            module()
    except Exception as e:
        logger.error(f"Error in {step_config.get('description')} for season {season}: {e}", exc_info=True)

def get_step_from_config(steps: List[Dict[str, Any]], step_num: int) -> Optional[Dict[str, Any]]:
    for step in steps:
        if step.get("step_num") == step_num:
            return step
    return None

def run_step(step_config: Dict, season: str, conn: sqlite3.Connection, force_run: bool = False):
    """Run a single population step."""
    description = step_config["description"]
    step_num = step_config["step_num"]
    module = step_config["module"]
    table_name = step_config.get("table_name")

    if step_config.get("special_logic"):
        logger.info(f"--- STEP {step_num}: {description} ---")
        # Directly invoke module with special handling, assuming it takes season_to_load
        module(season_to_load=season)
        logger.info(f"--- STEP {step_num} complete. ---")
        return

    if not force_run and table_name:
        should_skip = should_skip_step(
            conn,
            season,
            step_config.get("check_season_data", True),
            table_name,
            step_config.get("column_name"),
            step_config.get("row_threshold", 100),
            special_check=step_config.get("special_check", False),
        )
        if should_skip:
            logger.info(f"--- STEP {step_num} complete (skipped). ---")
            return

    # Execute the population module
    try:
        logger.info(f"--- STEP {step_num}: {description} ---")
        run_population_module(module, step_config, season)
    except Exception as e:
        logger.error(f"Error in {description} for season {season}: {e}", exc_info=True)
    finally:
        logger.info(f"--- STEP {step_num} complete. ---")

def main(season: str, force_run_all: bool = False):
    """
    Main orchestrator for populating all NBA stats data.
    """
    logger.info(f"Starting NBA stats population orchestrator for season: {season}")

    # STEP 0a: DB Initialization
    logger.info("--- STEP 0a: Ensuring database tables exist... ---")
    init_database()
    logger.info("--- STEP 0a complete. ---")
    
    conn = get_db_connection()
    if not conn:
        return

    # STEP 0b: Run Migrations
    logger.info("--- STEP 0b: Running database migrations... ---")
    run_migrations(conn)
    logger.info("--- STEP 0b complete. ---")

    for step_config in POPULATION_CONFIG:
        # Check if module was loaded successfully
        if step_config.get("module") is None:
            logger.error(f"Skipping step '{step_config.get('name')}' due to module loading error.")
            continue
        run_step(step_config, season, conn, force_run=force_run_all)

    # Final verification step
    verify_data_population(season)
    
    conn.close()
    logger.info(f"Orchestration complete for season: {season}")

def verify_data_population(season: str):
    conn_verify = get_db_connection()
    if conn_verify:
        try:
            cursor = conn_verify.cursor()
            tables_to_check = [
                "Teams", "Players", "PlayerSeasonRawStats", "PlayerSeasonAdvancedStats",
                "PlayerSeasonDriveStats", "PlayerSeasonHustleStats", "PlayerSeasonTrackingTouchesStats",
                "PlayerSeasonOpponentShootingStats", "PlayerSeasonShootingDistanceStats",
                "PlayerSeasonPassingStats", "PlayerSeasonCatchAndShootStats", "PlayerSeasonPullUpStats",
                "PlayerLineupStats", "PlayerSeasonReboundingStats", "PlayerSeasonPostUpStats",
                "PlayerSeasonPaintTouchStats", "PlayerSeasonElbowTouchStats", "PlayerShotChart", "PlayerSeasonSkill", "Possessions"
            ]
            for table_name in tables_to_check:
                if "Players" in table_name or "Teams" in table_name or "Possessions" in table_name:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    logger.info(f"Verification: {table_name} contains {count} total records.")
        except sqlite3.Error as e:
            logger.error(f"Error during data verification: {e}")
        finally:
            conn_verify.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NBA Stats Data Population Orchestrator")
    parser.add_argument("--season", type=str, default=settings.SEASON_ID, help="The season to populate data for (e.g., '2023-24').")
    parser.add_argument("--force-run-all", action="store_true", help="Force all population scripts to run, even if data exists.")
    args = parser.parse_args()

    main(season=args.season, force_run_all=args.force_run_all)