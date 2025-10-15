"""
Fetches and stores lineup stats for a given season by aggregating multiple measure types.
"""
import sqlite3
from ..utils.common_utils import get_db_connection, get_nba_stats_client, logger, migrate_table
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
    lower = s2.lower()
    # Fix numeric-letter boundaries introduced by the above for all-caps tokens like 'PCT_FGA_2PT' -> 'pct_fga_2_pt'
    lower = re.sub(r'_(\d)_([a-z])', r'_\1\2', lower)
    return lower

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


def _backfill_scoring_shares(conn, client, season: str) -> int:
    """
    Fetch Scoring measure directly and update four scoring-share columns
    in PlayerLineupStats by GROUP_ID for the specified season.
    Returns number of rows updated.
    """
    target_cols = [
        'pct_fga_2pt', 'pct_fga_3pt', 'pct_pts_2pt_mr', 'pct_pts_3pt'
    ]
    try:
        data = client.get_lineup_stats(
            season=season,
            measure_type="Scoring"
        )
        if not data or "resultSets" not in data or not data["resultSets"]:
            logger.warning("No Scoring data returned for backfill.")
            return 0
        result_set = data["resultSets"][0]
        headers = [h for h in result_set["headers"] if not h.endswith("_RANK")]
        rows = result_set["rowSet"]
        snake_headers = [_to_snake_case(h) for h in headers]

        # Map header index for faster lookup
        idx = {h: i for i, h in enumerate(snake_headers)}
        missing_any = [h for h in target_cols if h not in idx]
        if missing_any:
            logger.warning(f"Scoring headers missing expected cols: {missing_any}")

        updates = []
        for row in rows:
            try:
                group_id = row[idx['group_id']]
            except KeyError:
                continue
            if not group_id:
                continue
            vals = {
                'pct_fga_2pt': row[idx['pct_fga_2pt']] if 'pct_fga_2pt' in idx else None,
                'pct_fga_3pt': row[idx['pct_fga_3pt']] if 'pct_fga_3pt' in idx else None,
                'pct_pts_2pt_mr': row[idx['pct_pts_2pt_mr']] if 'pct_pts_2pt_mr' in idx else None,
                'pct_pts_3pt': row[idx['pct_pts_3pt']] if 'pct_pts_3pt' in idx else None,
            }
            # Only update if at least one value is not None
            if any(v is not None for v in vals.values()):
                updates.append((
                    vals['pct_fga_2pt'],
                    vals['pct_fga_3pt'],
                    vals['pct_pts_2pt_mr'],
                    vals['pct_pts_3pt'],
                    season,
                    group_id
                ))

        if not updates:
            logger.info("No scoring share values available to backfill.")
            return 0

        cursor = conn.cursor()
        cursor.executemany(
            """
            UPDATE PlayerLineupStats
            SET
                pct_fga_2pt = COALESCE(?, pct_fga_2pt),
                pct_fga_3pt = COALESCE(?, pct_fga_3pt),
                pct_pts_2pt_mr = COALESCE(?, pct_pts_2pt_mr),
                pct_pts_3pt = COALESCE(?, pct_pts_3pt)
            WHERE season = ? AND group_id = ?
            """,
            updates
        )
        conn.commit()
        logger.info(f"Backfilled scoring shares for {cursor.rowcount} lineup rows.")
        return cursor.rowcount or 0
    except Exception as e:
        logger.error(f"Failed scoring share backfill: {e}", exc_info=True)
        return 0

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
        # Ensure required scoring-share columns exist before inserting
        migrate_table(conn, "PlayerLineupStats", {
            "pct_fga_2pt": "REAL",
            "pct_fga_3pt": "REAL",
            "pct_pts_2pt_mr": "REAL",
            "pct_pts_3pt": "REAL",
        })

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

        # Compute the union of keys across all records, intersected with actual table columns
        all_keys = set()
        for record in stats_to_insert:
            all_keys.update(record.keys())
        final_columns = [col for col in sorted(all_keys) if col in table_columns]

        # Log presence of advanced/percentage fields to confirm inclusion
        advanced_candidates = {
            'off_rating', 'def_rating', 'ts_pct', 'pace', 'efg_pct',
            'ast_pct', 'ast_to', 'oreb_pct', 'dreb_pct', 'reb_pct', 'tm_tov_pct',
            'pct_fga_2pt', 'pct_fga_3pt', 'pct_pts_2pt_mr', 'pct_pts_3pt', 'pct_pts_fb'
        }
        present_advanced = sorted([c for c in advanced_candidates if c in final_columns])
        missing_advanced = sorted([c for c in advanced_candidates if c not in final_columns])
        logger.info(f"Final insert will use {len(final_columns)} columns. Advanced present: {present_advanced}")
        if missing_advanced:
            logger.warning(f"Advanced lineup fields missing from final insert columns: {missing_advanced}")
        
        rows_for_db = []
        for stat_line in stats_to_insert:
            row = tuple(stat_line.get(col) for col in final_columns)
            rows_for_db.append(row)

        placeholders = ", ".join(["?"] * len(final_columns))
        sql = f"INSERT OR REPLACE INTO PlayerLineupStats ({', '.join(final_columns)}) VALUES ({placeholders})"
        
        cursor.executemany(sql, rows_for_db)
        conn.commit()
        logger.info(f"Successfully inserted/updated {cursor.rowcount} aggregated lineup stat entries.")

        # Backfill scoring share columns explicitly from Scoring measure
        # only if these columns were not included in the final insert set
        scoring_share_cols = {'pct_fga_2pt', 'pct_fga_3pt', 'pct_pts_2pt_mr', 'pct_pts_3pt'}
        missing_shares = [c for c in scoring_share_cols if c not in final_columns]
        if missing_shares:
            logger.info(f"Attempting scoring-share backfill for missing columns: {missing_shares}")
            _ = _backfill_scoring_shares(conn, client, season_to_load)
        else:
            logger.info("Scoring-share columns present in insert; backfill not needed.")

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