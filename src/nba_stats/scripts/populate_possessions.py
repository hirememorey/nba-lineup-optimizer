"""
Fetches and stores play-by-play data for all games in a given season, including full lineups for each event.
"""
import sqlite3
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from nba_api.stats.endpoints import playbyplayv2, boxscoretraditionalv2
from .common_utils import get_db_connection, get_nba_stats_client, logger, settings
import time
import random

# Add a retry decorator
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError

# Add progress bar support
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    logger.warning("tqdm not available. Progress bars will be disabled.")


def _get_lineups_from_pbp(pbp_df: pd.DataFrame, home_team_id: int, away_team_id: int) -> tuple[set[int], set[int]]:
    """
    Infers the starting lineups by identifying the first 5 unique players for each team from the play-by-play data.
    """
    # Ensure events are processed in the order they happened
    first_period_events = pbp_df[pbp_df['PERIOD'] == 1].sort_values(by='EVENTNUM')

    # Create a comprehensive map of player IDs to their team IDs from the entire game's data,
    # as first-period data might be sparse.
    player_to_team_map = {}
    for _, row in pbp_df.iterrows():
        for i in range(1, 4):
            player_id = row[f'PLAYER{i}_ID']
            team_id = row[f'PLAYER{i}_TEAM_ID']
            if pd.notna(player_id) and pd.notna(team_id) and player_id not in player_to_team_map:
                player_to_team_map[int(player_id)] = int(team_id)

    home_players = set()
    away_players = set()

    # Iterate through the first period chronologically to find the first 5 unique players for each team
    for _, row in first_period_events.iterrows():
        for i in range(1, 4):
            player_id = row[f'PLAYER{i}_ID']
            if pd.notna(player_id):
                player_id = int(player_id)
                team_id = player_to_team_map.get(player_id)
                
                if team_id == home_team_id and len(home_players) < 5:
                    home_players.add(player_id)
                elif team_id == away_team_id and len(away_players) < 5:
                    away_players.add(player_id)
        
        # Once we have 5 players for both teams, we have the starting lineups.
        if len(home_players) == 5 and len(away_players) == 5:
            break

    # Final contract enforcement: if we couldn't find exactly 5, fail safely.
    if len(home_players) != 5 or len(away_players) != 5:
        logger.warning(f"Could not reliably determine 5 starters for each team from PBP. Found: Home={len(home_players)}, Away={len(away_players)}. Game will be skipped.")
        return set(), set()

    return home_players, away_players


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def _fetch_pbp_for_game(game_id: str, home_team_id: int, away_team_id: int) -> pd.DataFrame:
    """Fetches play-by-play data for a single game and enriches it with lineup information."""
    logger.info(f"Fetching play-by-play for game_id: {game_id}")
    try:
        # Increase the timeout to 120 seconds for the API call to handle slow responses
        pbp = playbyplayv2.PlayByPlayV2(game_id=game_id, timeout=120)
        pbp_df = pbp.get_data_frames()[0]

        if pbp_df.empty:
            logger.warning(f"PlayByPlay data for game {game_id} is empty. Skipping.")
            return pd.DataFrame()
            
        # Infer lineups directly from Play-by-play data
        home_players, away_players = _get_lineups_from_pbp(pbp_df, home_team_id, away_team_id)

        if not home_players or not away_players:
            logger.warning(f"Could not determine lineups for game {game_id} from PBP data. Skipping.")
            return pd.DataFrame()

        enriched_rows = []
        
        for _, row in pbp_df.iterrows():
            # Determine offensive team. Simplified logic, may need refinement.
            # Assumes the team of PLAYER1_ID is the offensive team.
            offensive_team_id = row.get('PLAYER1_TEAM_ID')
            if pd.isna(offensive_team_id) and row['HOMEDESCRIPTION'] is not None:
                 offensive_team_id = home_team_id
            elif pd.isna(offensive_team_id) and row['VISITORDESCRIPTION'] is not None:
                offensive_team_id = away_team_id

            defensive_team_id = home_team_id if offensive_team_id != home_team_id else away_team_id

            row_data = row.to_dict()
            row_data['home_player_1_id'], row_data['home_player_2_id'], row_data['home_player_3_id'], row_data['home_player_4_id'], row_data['home_player_5_id'] = sorted(list(home_players))
            row_data['away_player_1_id'], row_data['away_player_2_id'], row_data['away_player_3_id'], row_data['away_player_4_id'], row_data['away_player_5_id'] = sorted(list(away_players))
            row_data['offensive_team_id'] = offensive_team_id
            row_data['defensive_team_id'] = defensive_team_id

            enriched_rows.append(row_data)

            # Handle substitutions
            if row['EVENTMSGTYPE'] == 8: # 8 is substitution
                player_out_id = row['PLAYER1_ID']
                player_in_id = row['PLAYER2_ID']
                
                # --- START FIX V2: Defend against anomalous substitution data ---
                sub_team_id = row['PLAYER1_TEAM_ID']

                if sub_team_id == home_team_id:
                    # ANOMALY CHECK: If the player subbing in is already on the court,
                    # do nothing to prevent corrupting the player set to 4 members.
                    if player_in_id in home_players:
                        logger.warning(f"ANOMALY in Game {row['GAME_ID']} Event {row['EVENTNUM']}: Player {player_in_id} subbing in is already on court. Skipping substitution to maintain state integrity.")
                    elif player_out_id in home_players:
                        home_players.remove(player_out_id)
                        home_players.add(player_in_id)
                
                elif sub_team_id == away_team_id:
                    # ANOMALY CHECK: If the player subbing in is already on the court,
                    # do nothing to prevent corrupting the player set to 4 members.
                    if player_in_id in away_players:
                        logger.warning(f"ANOMALY in Game {row['GAME_ID']} Event {row['EVENTNUM']}: Player {player_in_id} subbing in is already on court. Skipping substitution to maintain state integrity.")
                    elif player_out_id in away_players:
                        away_players.remove(player_out_id)
                        away_players.add(player_in_id)
                # --- END FIX V2 ---

        return pd.DataFrame(enriched_rows)

    except Exception as e:
        logger.error(f"Error processing PBP for game {game_id}: {e}", exc_info=False) # exc_info=False to avoid noisy tracebacks on retry
        raise # Reraise the exception to trigger the retry mechanism


def populate_possessions(season_to_load: str) -> None:
    """
    Fetches play-by-play data for each game in a season and populates the Possessions table.
    """
    logger.info(f"Starting to populate Possessions data for the {season_to_load} season.")
    conn = get_db_connection()
    if not conn:
        return

    try:
        games_df = pd.read_sql_query(f"SELECT game_id, home_team_id, away_team_id FROM Games WHERE season = '{season_to_load}'", conn)
        logger.info(f"Found {len(games_df)} games for season {season_to_load}.")

        # --- ARCHITECTURAL CHANGE FOR RESUMPTION ---
        # 1. Get games already processed to make the script resumable
        try:
            processed_games_df = pd.read_sql_query("SELECT DISTINCT game_id FROM Possessions", conn)
            processed_games_ids = set(processed_games_df['game_id'])
            logger.info(f"Found {len(processed_games_ids)} games already processed in the Possessions table.")
        except pd.io.sql.DatabaseError: # Possessions table might not exist yet
            processed_games_ids = set()
            logger.info("Possessions table does not exist yet. Starting fresh.")

        # 2. Determine which games to process
        all_game_ids = set(games_df['game_id'])
        games_to_process_ids = all_game_ids - processed_games_ids
        
        if not games_to_process_ids:
            logger.info("All games for this season have already been processed. Exiting.")
            return

        games_to_process_df = games_df[games_df['game_id'].isin(games_to_process_ids)]
        logger.info(f"Processing {len(games_to_process_df)} new games.")

        # --- REMOVED OLD ALL-OR-NOTHING LOGIC ---
        # The logic to clear existing data is no longer needed with the resumable approach.

        # Note: Running this without ThreadPoolExecutor for now to avoid rate-limiting issues with the API
        # Add progress bar if tqdm is available
        if TQDM_AVAILABLE:
            game_iterator = tqdm(games_to_process_df.iterrows(), 
                               total=len(games_to_process_df),
                               desc="Processing games",
                               unit="game")
        else:
            game_iterator = games_to_process_df.iterrows()
            
        for index, game in game_iterator:
            try:
                pbp_df = _fetch_pbp_for_game(game['game_id'], game['home_team_id'], game['away_team_id'])
                if pbp_df.empty:
                    logger.warning(f"No data returned for game {game['game_id']}. Skipping.")
                    continue
                
                # --- START FINAL FIX V3: Deduplicate source data ---
                # The API can occasionally return duplicate events. We must remove them before insertion.
                pbp_df.drop_duplicates(subset=['GAME_ID', 'EVENTNUM'], keep='first', inplace=True)
                # --- END FINAL FIX V3 ---

                # Rename columns
                column_mapping = {
                    'GAME_ID': 'game_id', 'EVENTNUM': 'event_num', 'EVENTMSGTYPE': 'event_type',
                    'EVENTMSGACTIONTYPE': 'event_action_type', 'PERIOD': 'period', 'WCTIMESTRING': 'wc_time_string',
                    'PCTIMESTRING': 'pc_time_string', 'HOMEDESCRIPTION': 'home_description',
                    'NEUTRALDESCRIPTION': 'neutral_description', 'VISITORDESCRIPTION': 'visitor_description',
                    'SCORE': 'score', 'SCOREMARGIN': 'score_margin', 'PERSON1TYPE': 'person1_type',
                    'PLAYER1_ID': 'player1_id', 'PLAYER1_NAME': 'player1_name', 'PLAYER1_TEAM_ID': 'player1_team_id',
                    'PLAYER2_ID': 'player2_id', 'PLAYER2_NAME': 'player2_name', 'PLAYER2_TEAM_ID': 'player2_team_id',
                    'PLAYER3_ID': 'player3_id', 'PLAYER3_NAME': 'player3_name', 'PLAYER3_TEAM_ID': 'player3_team_id',
                }
                pbp_df.rename(columns=column_mapping, inplace=True)
                
                # Get schema and filter DataFrame
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(Possessions)")
                table_columns = {info[1] for info in cursor.fetchall()}
                df_to_insert = pbp_df[[col for col in pbp_df.columns if col in table_columns]]
                
                # --- START FINAL FIX V2: Manual INSERT ---
                cursor = conn.cursor()
                try:
                    cursor.execute("BEGIN")
                    # 1. Clean up any partial data from a previous failed run for this game
                    cursor.execute("DELETE FROM Possessions WHERE game_id = ?", (game['game_id'],))
                    
                    # 2. Insert the new, complete data using executemany for true atomicity
                    cols = ', '.join(df_to_insert.columns)
                    placeholders = ', '.join(['?'] * len(df_to_insert.columns))
                    sql = f"INSERT INTO Possessions ({cols}) VALUES ({placeholders})"
                    cursor.executemany(sql, df_to_insert.to_records(index=False).tolist())
                    
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise # Reraise the exception to be handled by the outer loop
                # --- END FINAL FIX V2 ---
                
                logger.info(f"Successfully inserted {len(df_to_insert)} plays for game {game['game_id']}.")

            except RetryError as e:
                logger.error(f"Failed to fetch PBP for game {game['game_id']} after multiple retries: {e}")
            time.sleep(random.uniform(0.6, 1.0)) # Be respectful of the API
        
        logger.info("Finished processing all new games for the season.")
        
    except Exception as e:
        logger.error(f"An unexpected error occurred during possession population: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    import argparse
    from ..config import settings

    parser = argparse.ArgumentParser(description="Populate possessions data for a given season.")
    parser.add_argument("--season", type=str, default=settings.SEASON_ID, help="The season to populate data for (e.g., '2023-24').")
    args = parser.parse_args()
    
    populate_possessions(season_to_load=args.season) 