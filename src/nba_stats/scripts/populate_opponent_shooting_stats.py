"""Script to populate PlayerSeasonOpponentShootingStats with league-wide opponent shooting data."""

import sqlite3
from .common_utils import get_db_connection, get_nba_stats_client, logger
import pandas as pd

def _transform_row_to_db_data(row_data: dict, season: str, team_id: int, games_played: int) -> dict:
    """Transforms a single row of API data into a dictionary for database insertion."""
    
    total_fga_against = sum(
        float(row_data.get(key, 0) or 0) for key in row_data if key.startswith('OPP_FGA_')
    )
    avg_fga_per_game = total_fga_against / float(games_played) if games_played and float(games_played) > 0 else 0

    player_id = row_data.get('PLAYER_ID')
    try:
        player_id = int(player_id)
    except (ValueError, TypeError):
        logger.warning(f"Could not parse player_id '{player_id}'. Skipping record.")
        return None

    return {
        "player_id": player_id,
        "season": season,
        "team_id": team_id,
        "avg_fg_attempted_against_per_game": avg_fga_per_game,
        "opp_fgm_lt_5ft": row_data.get('OPP_FGM_Less_Than_5_ft'),
        "opp_fga_lt_5ft": row_data.get('OPP_FGA_Less_Than_5_ft'),
        "opp_fg_pct_lt_5ft": row_data.get('OPP_FG_PCT_Less_Than_5_ft'),
        "opp_fgm_5_9ft": row_data.get('OPP_FGM_5_9_ft'),
        "opp_fga_5_9ft": row_data.get('OPP_FGA_5_9_ft'),
        "opp_fg_pct_5_9ft": row_data.get('OPP_FG_PCT_5_9_ft'),
        "opp_fgm_10_14ft": row_data.get('OPP_FGM_10_14_ft'),
        "opp_fga_10_14ft": row_data.get('OPP_FGA_10_14_ft'),
        "opp_fg_pct_10_14ft": row_data.get('OPP_FG_PCT_10_14_ft'),
        "opp_fgm_15_19ft": row_data.get('OPP_FGM_15_19_ft'),
        "opp_fga_15_19ft": row_data.get('OPP_FGA_15_19_ft'),
        "opp_fg_pct_15_19ft": row_data.get('OPP_FG_PCT_15_19_ft'),
        "opp_fgm_20_24ft": row_data.get('OPP_FGM_20_24_ft'),
        "opp_fga_20_24ft": row_data.get('OPP_FGA_20_24_ft'),
        "opp_fg_pct_20_24ft": row_data.get('OPP_FG_PCT_20_24_ft'),
        "opp_fgm_25_29ft": row_data.get('OPP_FGM_25_29_ft'),
        "opp_fga_25_29ft": row_data.get('OPP_FGA_25_29_ft'),
        "opp_fg_pct_25_29ft": row_data.get('OPP_FG_PCT_25_29_ft'),
    }

def populate_opponent_shooting_stats(season_to_load: str):
    """Fetches and stores league-wide opponent shooting stats for a given season."""
    logger.info(f"Starting opponent shooting stats fetch for season {season_to_load}")
    conn = get_db_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT player_id FROM Players")
        db_player_ids = {row[0] for row in cursor.fetchall()}
        
        cursor.execute("SELECT team_abbreviation, team_id FROM Teams")
        team_abbr_to_id = {row[0]: row[1] for row in cursor.fetchall()}

        # Fetch games played for all players
        cursor.execute("SELECT player_id, games_played FROM PlayerSeasonRawStats WHERE season = ?", (season_to_load,))
        player_games_played = {row[0]: row[1] for row in cursor.fetchall()}

        client = get_nba_stats_client()
        response = client.get_player_opponent_shooting_stats(season=season_to_load)

        if not response or 'resultSets' not in response:
            logger.warning("No opponent shooting data returned from API.")
            return

        result_sets = response['resultSets']
        headers = result_sets.get('headers')
        rows = result_sets.get('rowSet')

        if not headers or not rows:
            logger.warning("Opponent shooting dataset is empty.")
            return

        try:
            shot_zones = headers[0]['columnNames']
            all_column_names = headers[1]['columnNames']
            general_headers = all_column_names[:6]
            metric_headers = all_column_names[6:9]
            
            actual_headers = general_headers.copy()
            for zone in shot_zones:
                for metric in metric_headers:
                    zone_key = zone.replace(' ', '_').replace('.', '').replace('-', '_')
                    actual_headers.append(f"{metric}_{zone_key}")
        except (IndexError, KeyError) as e:
            logger.error(f"Could not extract column headers from API response: {e}", exc_info=True)
            return

        stats_to_insert = []
        for row in rows:
            row_data = dict(zip(actual_headers, row))
            
            try:
                player_id = int(row_data.get('PLAYER_ID'))
            except (ValueError, TypeError):
                logger.warning(f"Invalid PLAYER_ID '{row_data.get('PLAYER_ID')}' found in row. Skipping.")
                continue

            games_played = player_games_played.get(player_id)
            if games_played is None:
                logger.warning(f"Skipping player {player_id} due to missing GP data in PlayerSeasonRawStats.")
                continue

            team_abbr = row_data.get('TEAM_ABBREVIATION')
            if player_id in db_player_ids and team_abbr in team_abbr_to_id:
                team_id = team_abbr_to_id[team_abbr]
                db_data = _transform_row_to_db_data(row_data, season_to_load, team_id, games_played)
                if db_data:
                    stats_to_insert.append(db_data)
        
        if not stats_to_insert:
            logger.info("No new opponent shooting stats to insert.")
            return
            
        placeholders = ', '.join(['?'] * len(stats_to_insert[0]))
        columns = ', '.join(stats_to_insert[0].keys())
        sql = f"INSERT OR REPLACE INTO PlayerSeasonOpponentShootingStats ({columns}) VALUES ({placeholders})"
        
        cursor.executemany(sql, [tuple(d.values()) for d in stats_to_insert])
        conn.commit()
        logger.info(f"Successfully inserted/updated {cursor.rowcount} opponent shooting stat records.")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    import argparse
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from nba_stats.config import settings
    parser = argparse.ArgumentParser(description="Populate opponent shooting stats for a given season.")
    parser.add_argument("--season", type=str, default=settings.SEASON_ID, help="The season to populate data for (e.g., '2023-24').")
    args = parser.parse_args()
    
    populate_opponent_shooting_stats(season_to_load=args.season) 