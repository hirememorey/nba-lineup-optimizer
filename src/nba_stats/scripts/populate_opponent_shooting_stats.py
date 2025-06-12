"""Script to populate PlayerSeasonOpponentShootingStats with league-wide opponent shooting data."""

import sqlite3
from .common_utils import get_db_connection, get_nba_stats_client, logger

def _transform_row_to_db_data(row_data: dict, season: str, team_id: int) -> dict:
    """Transforms a single row of API data into a dictionary for database insertion."""
    # This calculation was part of the original script and is preserved here.
    total_fga_against = sum(
        row_data.get(f'OPP_FGA_{dist}', 0) or 0
        for dist in ['LT_05', '05_09', '10_14', '15_19', '20_24', '25_29']
    )
    games_played = row_data.get('GP')
    avg_fga_per_game = total_fga_against / games_played if games_played else 0

    return {
        "player_id": row_data.get('PLAYER_ID'),
        "season": season,
        "team_id": team_id,
        "avg_fg_attempted_against_per_game": avg_fga_per_game,
        "opp_fgm_lt_5ft": row_data.get('OPP_FGM_LT_05'),
        "opp_fga_lt_5ft": row_data.get('OPP_FGA_LT_05'),
        "opp_fg_pct_lt_5ft": row_data.get('OPP_FG_PCT_LT_05'),
        "opp_fgm_5_9ft": row_data.get('OPP_FGM_05_09'),
        "opp_fga_5_9ft": row_data.get('OPP_FGA_05_09'),
        "opp_fg_pct_5_9ft": row_data.get('OPP_FG_PCT_05_09'),
        "opp_fgm_10_14ft": row_data.get('OPP_FGM_10_14'),
        "opp_fga_10_14ft": row_data.get('OPP_FGA_10_14'),
        "opp_fg_pct_10_14ft": row_data.get('OPP_FG_PCT_10_14'),
        "opp_fgm_15_19ft": row_data.get('OPP_FGM_15_19'),
        "opp_fga_15_19ft": row_data.get('OPP_FGA_15_19'),
        "opp_fg_pct_15_19ft": row_data.get('OPP_FG_PCT_15_19'),
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

        client = get_nba_stats_client()
        response = client.get_player_opponent_shooting_stats(season=season_to_load)

        if not response or 'resultSets' not in response:
            logger.warning("No opponent shooting data returned from API.")
            return

        result_sets = response['resultSets']
        
        # Ensure result_sets is a dictionary and contains the necessary keys
        if not isinstance(result_sets, dict) or 'headers' not in result_sets or 'rowSet' not in result_sets:
            logger.warning("API response is not in the expected format.")
            return
            
        headers = result_sets.get('headers')
        rows = result_sets.get('rowSet')

        if not headers or not rows:
            logger.warning("Opponent shooting dataset is empty.")
            return

        # Extract the actual column headers from the nested structure
        try:
            actual_headers = headers[1]['columnNames']
        except (IndexError, KeyError) as e:
            logger.error(f"Could not extract column headers from API response: {e}", exc_info=True)
            return

        stats_to_insert = []
        for row in rows:
            row_data = dict(zip(actual_headers, row))
            player_id = row_data.get('PLAYER_ID')
            team_abbr = row_data.get('TEAM_ABBREVIATION')
            
            if player_id in db_player_ids and team_abbr in team_abbr_to_id:
                team_id = team_abbr_to_id[team_abbr]
                db_data = _transform_row_to_db_data(row_data, season_to_load, team_id)
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
    from ..config import settings
    parser = argparse.ArgumentParser(description="Populate opponent shooting stats for a given season.")
    parser.add_argument("--season", type=str, default=settings.SEASON_ID, help="The season to populate data for (e.g., '2023-24').")
    args = parser.parse_args()
    
    populate_opponent_shooting_stats(season_to_load=args.season)