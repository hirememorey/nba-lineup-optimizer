"""Script to populate the PlayerSeasonRawStats and PlayerSeasonAdvancedStats tables."""

# Standard libs
import sqlite3
import time
import random
from typing import Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure project root is on sys.path so that relative imports work
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Local imports (after path fix)
from nba_stats.utils.common_utils import get_db_connection, get_nba_stats_client, logger

def _insert_stats(conn: sqlite3.Connection, player_id: int, season: str, team_id: int, stats: Dict):
    """Inserts both raw and advanced stats for a player for a given season."""
    # This can be expanded or split if schemas diverge significantly
    try:
        raw_cursor = conn.cursor()
        raw_cursor.execute("""
            INSERT OR REPLACE INTO PlayerSeasonRawStats (
                player_id, season, team_id, games_played, minutes_played, field_goal_percentage,
                three_point_percentage, free_throw_percentage,
                field_goals_made, field_goals_attempted,
                three_pointers_made, three_pointers_attempted,
                free_throws_made, free_throws_attempted,
                offensive_rebounds, defensive_rebounds, total_rebounds,
                assists, steals, blocks, turnovers, personal_fouls,
                points, plus_minus
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            player_id, season, team_id,
            stats.get('GP'),
            stats.get('MIN'),
            stats.get('FG_PCT'),
            stats.get('FG3_PCT'),
            stats.get('FT_PCT'),
            stats.get('FGM'), stats.get('FGA'),
            stats.get('FG3M'), stats.get('FG3A'),
            stats.get('FTM'), stats.get('FTA'),
            stats.get('OREB'), stats.get('DREB'), stats.get('REB'),
            stats.get('AST'), stats.get('STL'), stats.get('BLK'),
            stats.get('TOV'), stats.get('PF'),
            stats.get('PTS'), stats.get('PLUS_MINUS')
        ))

        adv_cursor = conn.cursor()
        adv_cursor.execute("""
            INSERT OR REPLACE INTO PlayerSeasonAdvancedStats (
                player_id, season, team_id, offensive_rating, defensive_rating, net_rating,
                assist_percentage, offensive_rebound_percentage, defensive_rebound_percentage,
                rebound_percentage, turnover_percentage, effective_field_goal_percentage,
                true_shooting_percentage, usage_percentage, pace, pie
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            player_id, season, team_id, stats.get('OFF_RATING'), stats.get('DEF_RATING'),
            stats.get('NET_RATING'), stats.get('AST_PCT'), stats.get('OREB_PCT'),
            stats.get('DREB_PCT'), stats.get('REB_PCT'), stats.get('TM_TOV_PCT'),
            stats.get('E_FG_PCT'), stats.get('TS_PCT'), stats.get('USG_PCT'),
            stats.get('PACE'), stats.get('PIE')
        ))
    except sqlite3.Error as e:
        logger.error(f"DB error for player {player_id} in season {season}: {e}")

def _fetch_player_stats_task(player_info: Tuple[int, str], season: str) -> Dict:
    """Task to fetch all stats for a single player, designed for concurrent execution."""
    player_id, player_name = player_info
    client = get_nba_stats_client()
    
    logger.info(f"Fetching stats for {player_name} (ID: {player_id}), Season: {season}")
    
    try:
        time.sleep(random.uniform(0.5, 1.5))
        
        # Consolidate API calls
        player_info = client.get_player_info(player_id)
        
        # Fetch both base and advanced stats and merge them
        base_stats_raw = client.get_player_stats(player_id, season, per_mode="Totals", measure_type="Base")
        advanced_stats_raw = client.get_player_stats(player_id, season, per_mode="Totals", measure_type="Advanced")

        if not player_info or not base_stats_raw or not advanced_stats_raw:
            logger.warning(f"Could not retrieve full stats for player {player_id}")
            return {}

        team_id = player_info.get('TEAM_ID')
        
        # Helper to extract the primary rowSet from a raw API response
        def _extract_row_set(raw_data: Dict) -> Dict:
            if not raw_data or 'resultSets' not in raw_data:
                return {}
            
            for result_set in raw_data.get('resultSets', []):
                if result_set.get('name') == 'OverallPlayerDashboard' and result_set.get('rowSet'):
                    headers = [h.upper() for h in result_set['headers']] # Normalize headers to upper
                    row = result_set['rowSet'][0]
                    return dict(zip(headers, row))
            return {}

        # Extract and merge base and advanced stats
        base_stats = _extract_row_set(base_stats_raw)
        advanced_stats = _extract_row_set(advanced_stats_raw)
        
        if not base_stats or not advanced_stats:
            logger.warning(f"Could not find 'OverallPlayerDashboard' in raw stats for player {player_id}")
            return {}

        all_stats = {
            'player_id': player_id,
            'season': season,
            'team_id': team_id
        }
        
        all_stats.update(base_stats)
        
        # Only add keys from advanced_stats that are not already in all_stats
        # This prevents overwriting 'MIN' (total minutes) from base_stats
        # with 'MIN' (average minutes) from advanced_stats.
        for key, value in advanced_stats.items():
            if key not in all_stats:
                all_stats[key] = value
            
        return all_stats

    except Exception as e:
        logger.error(f"Exception in thread for player {player_name} (ID: {player_id}): {e}")
        return {}

def populate_player_season_stats(season_to_load: str, player_ids: list[int] | None = None):
    """
    Fetches and stores basic and advanced season stats for all players using parallel requests.
    If player_ids is provided, only fetches for those players.
    """
    logger.info(f"Starting player season stats fetch for season {season_to_load}.")
    conn = get_db_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()
        if player_ids:
            # Create a string of placeholders for the query
            placeholders = ','.join('?' for _ in player_ids)
            query = f"""
                SELECT DISTINCT p.player_id, p.player_name
                FROM Players p
                WHERE p.player_id IN ({placeholders})
            """
            cursor.execute(query, player_ids)
            players_to_process = cursor.fetchall()
        else:
            # Get all players for the specific season directly from the API
            # This is the CORRECT approach - use leaguedashplayerstats which includes minutes data
            logger.info(f"Fetching all players for season {season_to_load} from NBA Stats API")

            client = get_nba_stats_client()
            all_players_raw = client.get_league_player_base_stats(season=season_to_load)

            if not all_players_raw or 'resultSets' not in all_players_raw or not all_players_raw['resultSets']:
                logger.error(f"No player data found for season {season_to_load}")
                return

            player_data = all_players_raw['resultSets'][0]
            headers = [header.upper() for header in player_data['headers']]
            player_rows = player_data['rowSet']

            # Convert API response to the format expected by the rest of the script
            # Note: API returns minutes per game, need to multiply by games played for total minutes
            players_to_process = []
            gp_idx = headers.index('GP')  # Games played index

            for player_row in player_rows:
                player_dict = dict(zip(headers, player_row))
                # Only include players who meet the minimum minutes threshold
                # Using the same low threshold as the current archetype analysis (15+ minutes)
                try:
                    gp = float(player_row[gp_idx]) if player_row[gp_idx] else 0
                    min_per_game = float(player_row[headers.index('MIN')]) if player_row[headers.index('MIN')] else 0
                    total_minutes = gp * min_per_game

                    if total_minutes >= 15:  # Using the same threshold as current archetype analysis
                        players_to_process.append((player_dict['PLAYER_ID'], player_dict['PLAYER_NAME']))
                except (ValueError, IndexError):
                    # If we can't get minutes data, include the player anyway
                    # This matches the original paper's approach
                    players_to_process.append((player_dict['PLAYER_ID'], player_dict['PLAYER_NAME']))

            logger.info(f"API returned {len(player_rows)} total players, {len(players_to_process)} meet 15+ total minutes threshold for season {season_to_load}")

        if not players_to_process:
            logger.warning("No players found in DB to process for season stats.")
            return

        logger.info(f"Processing {len(players_to_process)} players for season {season_to_load}.")
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_player = {executor.submit(_fetch_player_stats_task, player, season_to_load): player for player in players_to_process}
            
            processed_count = 0
            for future in as_completed(future_to_player):
                stats = future.result()
                if stats and stats.get('team_id'):
                    _insert_stats(conn, stats['player_id'], stats['season'], stats['team_id'], stats)
                    processed_count += 1
                else:
                    player_name = future_to_player[future][1]
                    logger.warning(f"Skipping stats for {player_name} due to missing data from API.")
            
            conn.commit()
            logger.info(f"Finished processing. Stored stats for {processed_count} players.")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Populate player season stats for a specific NBA season.")
    parser.add_argument("--season", type=str, default="2024-25", help="The season to populate stats for, e.g., '2024-25'.")
    parser.add_argument("--players", type=int, nargs='*', help="Optional list of player IDs to process.")
    args = parser.parse_args()
    
    populate_player_season_stats(season_to_load=args.season, player_ids=args.players) 