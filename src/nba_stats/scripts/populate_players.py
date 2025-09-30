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
    # logger.info("--- STEP 0a: Ensuring database tables exist... ---")
    # init_database()
    # logger.info("--- STEP 0a complete. ---")
    
    conn = get_db_connection()
    if not conn:
        return

    # STEP 0b: Run Migrations
    # logger.info("--- STEP 0b: Running database migrations... ---")
    # run_migrations(conn)
    # logger.info("--- STEP 0b complete. ---")

    # Step 1: Populate Teams
    # run_step(1, "Populate Teams", populate_teams, season, "Teams", "team_id")

    # Step 2: Populate Players
    players_step_config = get_step_from_config(POPULATION_CONFIG, 2)
    if players_step_config and players_step_config.get("module"):
        run_step(players_step_config, season, conn, force_run=force_run_all)
    else:
        logger.error("Could not find or load configuration for step 2: Populate Players.")
    # run_step(2, "Populate Players", populate_players, season, "Players", "player_id")

    # Step 3: Populate Player Wingspan
    # wingspan_step_config = get_step_from_config(POPULATION_CONFIG, 3)
    # if wingspan_step_config and wingspan_step_config.get("module"):
    #     run_step(wingspan_step_config, season, conn)
    # else:
    #     logger.error("Could not find or load configuration for step 3: Populate Player Wingspan.")
    
    # Step 4: Populate Games
    # run_step(4, "Populate Games", populate_games, season, "Games", "game_id")

    # Step 5: Populate PlayerSeasonRawStats
    # run_step(5, "Populate PlayerSeasonRawStats", populate_player_season_stats, season, "PlayerSeasonRawStats", "player_id")

    # Step 6: Populate PlayerSeasonDriveStats
    # run_step(6, "Populate PlayerSeasonDriveStats", populate_player_drive_stats, season, "PlayerSeasonDriveStats", "player_id")

    # Step 7: Populate PlayerSeasonHustleStats
    # run_step(7, "Populate PlayerSeasonHustleStats", populate_player_hustle_stats, season, "PlayerSeasonHustleStats", "player_id")

    # Step 8: Populate PlayerSeasonOpponentShootingStats
    # run_step(8, "Populate PlayerSeasonOpponentShootingStats", populate_opponent_shooting_stats, season, "PlayerSeasonOpponentShootingStats", "player_id")

    # Step 9: Populate PlayerSeasonPassingStats
    # run_step(9, "Populate PlayerSeasonPassingStats", populate_player_passing_stats, season, "PlayerSeasonPassingStats", "player_id")

    # Step 10: Populate PlayerSeasonReboundingStats
    # run_step(10, "Populate PlayerSeasonReboundingStats", populate_player_rebounding_stats, season, "PlayerSeasonReboundingStats", "player_id")

    # Step 11: Populate PlayerSeasonTrackingTouchesStats
    # run_step(11, "Populate PlayerSeasonTrackingTouchesStats", populate_player_tracking_touches_stats, season, "PlayerSeasonTrackingTouchesStats", "player_id")

    # Step 12: Populate PlayerSeasonCatchAndShootStats
    # run_step(12, "Populate PlayerSeasonCatchAndShootStats", populate_player_catch_shoot_stats, season, "PlayerSeasonCatchAndShootStats", "player_id")

    # Step 13: Populate PlayerSeasonPullUpStats
    # run_step(13, "Populate PlayerSeasonPullUpStats", populate_player_pull_up_stats, season, "PlayerSeasonPullUpStats", "player_id")
    
    # Step 14: Populate PlayerSeasonPostUpStats
    # run_step(14, "Populate PlayerSeasonPostUpStats", populate_player_post_up_stats, season, "PlayerSeasonPostUpStats", "player_id")

    # Step 15: Populate PlayerSeasonPaintTouchStats
    # run_step(15, "Populate PlayerSeasonPaintTouchStats", populate_player_paint_touch_stats, season, "PlayerSeasonPaintTouchStats", "player_id")

    # Step 16: Populate PlayerSeasonElbowTouchStats
    # run_step(16, "Populate PlayerSeasonElbowTouchStats", populate_player_elbow_touch_stats, season, "PlayerSeasonElbowTouchStats", "player_id")

    # Step 17: Populate PlayerLineupStats
    # run_step(17, "Populate PlayerLineupStats", populate_lineup_stats, season, "PlayerLineupStats", "lineup_id")

    # Step 18: Populate PlayerShotChart
    # run_step(18, "Populate PlayerShotChart", populate_player_shot_charts, season, "PlayerShotChart", "player_id")

    # Step 19: Populate Player Skills
    # run_step(19, "Populate Player Skills", POPULATION_CONFIG.get('populate_player_skill'), season, 'PlayerSeasonSkill', 'player_id')
    
    # Step 20: Populate Possessions
    # run_step(20, "Populate Possessions", populate_possessions, season, "Possessions", "game_id")

    # Final Verification
    # logger.info("--- FINAL VERIFICATION ---")
    # with get_db_connection() as conn:
    #     for table in ["Teams", "Players", "Possessions"]:
    #         count = pd.read_sql(f"SELECT COUNT(*) FROM {table}", conn).iloc[0, 0]
    #         logger.info(f"Verification: {table} contains {count} total records.")
    
    logger.info(f"Orchestration complete for season: {season}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NBA Stats Data Population Orchestrator")
    parser.add_argument("--season", type=str, default=settings.SEASON_ID, help="The season to populate data for (e.g., '2023-24').")
    parser.add_argument("--force-run-all", action="store_true", help="Force all population scripts to run, even if data exists.")
    args = parser.parse_args()

    main(season=args.season, force_run_all=args.force_run_all)