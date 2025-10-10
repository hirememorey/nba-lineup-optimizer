"""
Fetches and stores lineup stats for a given season by aggregating multiple measure types.
"""
import sqlite3
from .common_utils import get_db_connection, get_nba_stats_client, logger, settings
import time
import random
import re

def _to_snake_case(name: str) -> str:
    """Converts a string from CamelCase or SCREAMING_SNAKE_CASE to snake_case."""
    if not name:
        return ""
    # This handles cases like 'PlayerID' -> 'player_id' and 'GROUP_ID' -> 'group_id'
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    # This handles cases like 'W_PCT' -> 'w_pct' by replacing the underscore
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower()

def _schema_reconnaissance(client, season: str):
    """
    A temporary function to perform schema reconnaissance on all measure types.
    It fetches the first page of data for each measure type and prints the headers.
    This helps identify any inconsistencies in the API response schemas upfront.
    """
    logger.info("--- Starting Schema Reconnaissance ---")
    measure_types = ["Base", "Advanced", "Misc", "Four Factors", "Scoring"]
    
    for measure in measure_types:
        logger.info(f"Fetching headers for {measure} lineup stats...")
        try:
            # Fetching data without date filters as per previous findings
            data = client.get_lineup_stats(
                season=season, 
                measure_type=measure
            )
            
            if not data or "resultSets" not in data or not data["resultSets"]:
                logger.warning(f"No data returned for measure type: {measure}")
                continue

            result_set = data["resultSets"][0]
            headers = result_set["headers"]
            logger.info(f"Headers for '{measure}': {headers}")

        except Exception as e:
            logger.error(f"Error fetching headers for {measure}: {e}", exc_info=True)
    logger.info("--- Schema Reconnaissance Complete ---")


def _fetch_and_aggregate_lineup_stats(client, season: str) -> dict:
    """Fetches all lineup stat types and aggregates them by lineup group ID."""
    aggregated_stats = {}
    measure_types = ["Base", "Advanced", "Misc", "Four Factors", "Scoring"]

    try:
        start_year = int(season.split('-')[0])
        date_from = f"10/01/{start_year}"
        date_to = f"04/30/{start_year + 1}"
    except (ValueError, IndexError):
        logger.error(f"Invalid season format: {season}. Expected format 'YYYY-YY'.")
        return {}

    for measure in measure_types:
        logger.info(f"Fetching {measure} lineup stats for {season} season.")
        try:
            # The API call was failing with date parameters. Removing them as a fix.
            data = client.get_lineup_stats(
                season=season, 
                measure_type=measure
            )

            if measure == "Base":
                logger.info(f"Received data for Base measure type: {data}")
                
            if not data or "resultSets" not in data or not data["resultSets"]:
                logger.warning(f"No data for measure type: {measure}")
                continue

            result_set = data["resultSets"][0]
            headers = [h for h in result_set["headers"] if not h.endswith("_RANK")]
            rows = result_set["rowSet"]

            snake_case_headers = [_to_snake_case(h) for h in headers]
            for row in rows:
                row_dict = dict(zip(snake_case_headers, row))
                group_id = row_dict.get('group_id')
                if group_id:
                    if group_id not in aggregated_stats:
                        aggregated_stats[group_id] = {'season': season}
                    aggregated_stats[group_id].update(row_dict)
            
            time.sleep(random.uniform(settings.MIN_SLEEP, settings.MAX_SLEEP))

        except Exception as e:
            logger.error(f"Error processing {measure} lineup stats: {e}", exc_info=True)
            
    return aggregated_stats

def populate_lineup_stats(season_to_load: str):
    """Orchestrates fetching, aggregating, and storing of lineup stats."""
    logger.info(f"Starting lineup stats population for the {season_to_load} season.")
    conn = get_db_connection()
    if conn is None:
        return

    try:
        client = get_nba_stats_client()
        aggregated_stats = _fetch_and_aggregate_lineup_stats(client, season_to_load)

        if not aggregated_stats:
            logger.info("No aggregated lineup stats to insert.")
            return

        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(PlayerLineupStats)")
        table_columns = {info[1] for info in cursor.fetchall()}

        # Flatten the aggregated data into a list of dictionaries for insertion
        stats_to_insert = [stats for stats in aggregated_stats.values()]

        # Use the columns from the first record as the standard for this batch
        final_columns = [col for col in sorted(stats_to_insert[0].keys()) if col in table_columns]
        
        rows_for_db = []
        for stat_line in stats_to_insert:
            row = tuple(stat_line.get(col) for col in final_columns)
            rows_for_db.append(row)

        placeholders = ", ".join(["?"] * len(final_columns))
        sql = f"INSERT OR REPLACE INTO PlayerLineupStats ({', '.join(final_columns)}) VALUES ({placeholders})"
        
        cursor.executemany(sql, rows_for_db)
        conn.commit()
        logger.info(f"Successfully inserted/updated {cursor.rowcount} aggregated lineup stat entries.")

    except Exception as e:
        logger.error(f"Failed during lineup stats database operation: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    import argparse
    from ..config import settings

    parser = argparse.ArgumentParser(description="Populate lineup stats for a given season.")
    parser.add_argument("--season", type=str, default=settings.SEASON_ID, help="The season to populate data for (e.g., '2023-24').")
    parser.add_argument("--recon", action="store_true", help="Run schema reconnaissance and exit.")
    args = parser.parse_args()
    
    if args.recon:
        client = get_nba_stats_client()
        _schema_reconnaissance(client, season=args.season)
    else:
        populate_lineup_stats(season_to_load=args.season) 