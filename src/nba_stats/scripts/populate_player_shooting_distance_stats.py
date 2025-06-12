"""Fetch and store player shooting distance stats for a given season."""

import sqlite3
from .common_utils import get_db_connection, get_nba_stats_client, logger

def _parse_shot_distance_data(raw_data: dict) -> list:
    """Parses the complex nested structure of the shot distance API response."""
    if not raw_data or 'resultSets' not in raw_data:
        return []

    result_sets = raw_data['resultSets']
    result_data = result_sets[0] if isinstance(result_sets, list) else result_sets
    
    api_headers = result_data.get('headers', [])
    rows = result_data.get('rowSet', [])
    
    if not rows or not api_headers or len(api_headers) != 2:
        logger.error("Unexpected API header structure for shooting distance.")
        return []

    zone_header = api_headers[0]
    stats_header = api_headers[1]

    player_info_cols = [col.lower() for col in stats_header['columnNames'][:zone_header['columnsToSkip']]]
    zone_names = zone_header['columnNames']
    
    zone_stat_cols = []
    for zone in zone_names:
        sanitized_zone = zone.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
        zone_stat_cols.extend([f"{sanitized_zone}_fgm", f"{sanitized_zone}_fga", f"{sanitized_zone}_fg_pct"])

    final_headers = player_info_cols + zone_stat_cols
    
    parsed_data = []
    for row in rows:
        if len(row) == len(final_headers):
            parsed_data.append(dict(zip(final_headers, row)))
    return parsed_data

def populate_player_shooting_distance_stats(season: str):
    """Fetches and stores league-wide shooting distance stats."""
    logger.info(f"Fetching shooting distance stats for season: {season}")
    conn = get_db_connection()
    if conn is None:
        return

    try:
        client = get_nba_stats_client()
        raw_data = client.get_league_player_shot_locations(season=season)
        
        parsed_stats = _parse_shot_distance_data(raw_data)
        if not parsed_stats:
            logger.warning("No shooting distance data to process.")
            return

        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(PlayerSeasonShootingDistanceStats)")
        db_columns = {col[1] for col in cursor.fetchall()}

        stats_for_db = []
        for record in parsed_stats:
            db_record = {k: v for k, v in record.items() if k in db_columns}
            db_record['season'] = season
            if db_record.get('player_id'):
                stats_for_db.append(db_record)

        if not stats_for_db:
            logger.warning("No valid records to insert after schema mapping.")
            return

        columns = stats_for_db[0].keys()
        placeholders = ', '.join(['?'] * len(columns))
        sql = f"INSERT OR REPLACE INTO PlayerSeasonShootingDistanceStats ({', '.join(columns)}) VALUES ({placeholders})"
        
        cursor.executemany(sql, [tuple(d.values()) for d in stats_for_db])
        conn.commit()
        logger.info(f"Successfully stored {cursor.rowcount} shooting distance stat records.")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    import argparse
    from ..config import settings
    
    parser = argparse.ArgumentParser(description="Populate shooting distance stats for a season.")
    parser.add_argument("--season", type=str, default=settings.SEASON_ID, help="The season to fetch data for (e.g., '2023-24').")
    args = parser.parse_args()
    
    populate_player_shooting_distance_stats(season=args.season) 