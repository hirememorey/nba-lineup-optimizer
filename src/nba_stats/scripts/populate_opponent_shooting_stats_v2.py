"""Script to populate PlayerSeasonOpponentShootingStats with league-wide opponent shooting data.

This is a corrected version that handles the actual API response structure from
leaguedashplayershotlocations with MeasureType=Opponent.
"""

import sqlite3
from .common_utils import get_db_connection, get_nba_stats_client, logger
from typing import Dict, List, Optional, Tuple


def _create_distance_mapping(shot_categories: List[str]) -> Dict[str, str]:
    """Create mapping from API distance names to database suffixes."""
    distance_mapping = {
        "Less Than 5 ft.": "lt_5ft",
        "5-9 ft.": "5_9ft", 
        "10-14 ft.": "10_14ft",
        "15-19 ft.": "15_19ft",
        "20-24 ft.": "20_24ft",
        "25-29 ft.": "25_29ft",
        "30-34 ft.": "30_34ft",
        "35-39 ft.": "35_39ft",
        "40+ ft.": "40_plus_ft"
    }
    
    # Create mapping for the actual categories returned by API
    api_to_db = {}
    for category in shot_categories:
        if category in distance_mapping:
            api_to_db[category] = distance_mapping[category]
        else:
            # Handle any unexpected categories
            logger.warning(f"Unknown shot category: {category}")
            # Create a safe suffix by replacing spaces and special chars
            safe_suffix = category.lower().replace(" ", "_").replace(".", "").replace("-", "_").replace("+", "_plus")
            api_to_db[category] = safe_suffix
    
    return api_to_db


def _parse_api_response(response: Dict) -> Tuple[List[str], List[List]]:
    """Parse the API response and return column names and data rows."""
    if not response or 'resultSets' not in response:
        raise ValueError("Invalid response: missing resultSets")
    
    result_sets = response['resultSets']
    
    # Handle the new structure where resultSets is a dict, not array
    if not isinstance(result_sets, dict):
        raise ValueError("Expected resultSets to be a dict")
    
    if 'headers' not in result_sets or 'rowSet' not in result_sets:
        raise ValueError("Missing headers or rowSet in resultSets")
    
    headers = result_sets['headers']
    row_set = result_sets['rowSet']
    
    if not isinstance(headers, list) or len(headers) < 2:
        raise ValueError("Expected headers to be a list with at least 2 elements")
    
    # Extract shot categories and column names
    shot_categories = headers[0].get('columnNames', [])
    column_names = headers[1].get('columnNames', [])
    
    if not shot_categories or not column_names:
        raise ValueError("Missing shot categories or column names")
    
    logger.info(f"Found {len(shot_categories)} shot categories and {len(column_names)} columns")
    logger.info(f"Shot categories: {shot_categories}")
    
    return column_names, row_set


def _transform_row_to_db_data(
    row_data: List, 
    column_names: List[str],
    season: str, 
    team_id: int, 
    games_played: int,
    distance_mapping: Dict[str, str]
) -> Optional[Dict]:
    """Transform a single row of API data into database format."""
    
    # Create row dict from column names and values
    row_dict = dict(zip(column_names, row_data))
    
    # Extract basic info
    player_id = row_dict.get('PLAYER_ID')
    if not player_id:
        logger.warning("Missing PLAYER_ID in row data")
        return None
    
    try:
        player_id = int(player_id)
    except (ValueError, TypeError):
        logger.warning(f"Invalid PLAYER_ID '{player_id}'. Skipping record.")
        return None
    
    # Calculate total FGA for avg_fg_attempted_against_per_game
    # The shot data starts at index 6 and comes in groups of 3 (FGM, FGA, FG_PCT)
    total_fga = 0
    for i in range(6, len(row_data), 3):  # Every 3rd element starting from index 6
        if i + 1 < len(row_data):  # FGA is at index i+1
            try:
                fga_value = float(row_data[i + 1])
                total_fga += fga_value
            except (ValueError, TypeError):
                pass
    
    avg_fga_per_game = total_fga / float(games_played) if games_played and float(games_played) > 0 else 0
    
    # Build the database record
    db_data = {
        "player_id": player_id,
        "season": season,
        "team_id": team_id,
        "player_name_api": row_dict.get('PLAYER_NAME'),
        "team_code_api": row_dict.get('TEAM_ABBREVIATION'),
        "age_api": row_dict.get('AGE'),
        "games_played": games_played,
        "avg_fg_attempted_against_per_game": avg_fga_per_game,
    }
    
    # Add shot data for each distance range
    # The data comes in groups of 3: FGM, FGA, FG_PCT for each distance
    shot_categories = list(distance_mapping.keys())
    for distance_index, api_distance in enumerate(shot_categories):
        db_suffix = distance_mapping[api_distance]
        
        # Calculate the base index for this distance
        # 6 basic info columns + (distance_index * 3) for shot data
        base_index = 6 + (distance_index * 3)
        
        if base_index + 2 < len(row_data):
            # FGM, FGA, FG_PCT are at base_index, base_index+1, base_index+2
            fgm_value = row_data[base_index] if row_data[base_index] is not None else 0
            fga_value = row_data[base_index + 1] if row_data[base_index + 1] is not None else 0
            fg_pct_value = row_data[base_index + 2] if row_data[base_index + 2] is not None else 0
            
            db_data[f"opp_fgm_{db_suffix}"] = fgm_value
            db_data[f"opp_fga_{db_suffix}"] = fga_value
            db_data[f"opp_fg_pct_{db_suffix}"] = fg_pct_value
        else:
            # Not enough data for this distance
            db_data[f"opp_fgm_{db_suffix}"] = 0
            db_data[f"opp_fga_{db_suffix}"] = 0
            db_data[f"opp_fg_pct_{db_suffix}"] = 0
    
    return db_data




def populate_opponent_shooting_stats(season_to_load: str):
    """Fetches and stores league-wide opponent shooting stats for a given season."""
    logger.info(f"Starting opponent shooting stats fetch for season {season_to_load}")
    
    conn = get_db_connection()
    if conn is None:
        return
    
    try:
        cursor = conn.cursor()
        
        # Get team mapping
        cursor.execute("SELECT team_abbreviation, team_id FROM Teams")
        team_abbr_to_id = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get games played for all players
        cursor.execute("SELECT player_id, games_played FROM PlayerSeasonRawStats WHERE season = ?", (season_to_load,))
        player_games_played = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Fetch data from API
        client = get_nba_stats_client()
        response = client.get_player_opponent_shooting_stats(season=season_to_load)
        
        if not response:
            logger.warning("No response from API")
            return
        
        # Parse the API response
        try:
            column_names, row_set = _parse_api_response(response)
        except Exception as e:
            logger.error(f"Failed to parse API response: {e}")
            return
        
        # Create distance mapping
        shot_categories = response['resultSets']['headers'][0]['columnNames']
        distance_mapping = _create_distance_mapping(shot_categories)
        
        # Process each row
        stats_to_insert = []
        for row in row_set:
            # Get basic info from row
            if len(row) < 6:
                logger.warning("Row too short, skipping")
                continue
                
            player_id = row[0]  # PLAYER_ID
            team_abbr = row[3]  # TEAM_ABBREVIATION
            
            if not player_id:
                continue
                
            try:
                player_id = int(player_id)
            except (ValueError, TypeError):
                continue
            
            # Get team info
            if not team_abbr or team_abbr not in team_abbr_to_id:
                logger.warning(f"Unknown team abbreviation: {team_abbr}")
                continue
            
            team_id = team_abbr_to_id[team_abbr]
            
            # Get games played
            games_played = player_games_played.get(player_id)
            if games_played is None:
                logger.warning(f"No games played data for player {player_id}")
                continue
            
            # Transform row data
            db_data = _transform_row_to_db_data(row, column_names, season_to_load, team_id, games_played, distance_mapping)
            if db_data:
                stats_to_insert.append(db_data)
        
        if not stats_to_insert:
            logger.info("No opponent shooting stats to insert.")
            return
        
        # Insert data
        columns = ', '.join(stats_to_insert[0].keys())
        placeholders = ', '.join(['?'] * len(stats_to_insert[0]))
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
    parser.add_argument("--season", type=str, default=settings.SEASON_ID, help="The season to populate data for (e.g., '2024-25').")
    args = parser.parse_args()
    
    populate_opponent_shooting_stats(season_to_load=args.season)
