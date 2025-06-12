"""
Fetches and stores play-by-play data for all games in a given season.
"""
import sqlite3
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from .common_utils import get_db_connection, get_nba_stats_client, logger, settings
import time
import random

def _fetch_pbp_for_game(game_id: str) -> pd.DataFrame:
    """Fetches play-by-play data for a single game and returns a DataFrame."""
    logger.info(f"Fetching play-by-play for game_id: {game_id}")
    client = get_nba_stats_client()
    try:
        pbp_data = client.get_play_by_play(game_id)
        if pbp_data and "resultSets" in pbp_data and pbp_data["resultSets"]:
            result_set = pbp_data["resultSets"][0]
            headers = result_set["headers"]
            rows = result_set["rowSet"]
            if rows:
                return pd.DataFrame(rows, columns=headers)
    except Exception as e:
        logger.error(f"Error fetching PBP for game {game_id}: {e}", exc_info=True)
    return pd.DataFrame()

def populate_possessions(season_to_load: str) -> None:
    """
    Fetches play-by-play data for each game in a season and populates the Possessions table.
    """
    logger.info(f"Starting to populate Possessions data for the {season_to_load} season.")
    conn = get_db_connection()
    if not conn:
        return

    try:
        games_df = pd.read_sql_query(f"SELECT game_id FROM Games WHERE season = '{season_to_load}'", conn)
        game_ids = games_df['game_id'].tolist()
        logger.info(f"Found {len(game_ids)} games for season {season_to_load}.")

        if game_ids:
            # Clear existing data for this season's games to prevent duplicates
            game_ids_placeholder = ','.join('?' for _ in game_ids)
            delete_query = f"DELETE FROM Possessions WHERE game_id IN ({game_ids_placeholder})"
            cursor = conn.cursor()
            cursor.execute(delete_query, game_ids)
            conn.commit()
            logger.info(f"Cleared existing possession data for {cursor.rowcount} games for season {season_to_load}.")

        all_plays_df = pd.DataFrame()
        with ThreadPoolExecutor(max_workers=settings.MAX_WORKERS) as executor:
            future_to_game = {executor.submit(_fetch_pbp_for_game, game_id): game_id for game_id in game_ids}
            for future in as_completed(future_to_game):
                pbp_df = future.result()
                if not pbp_df.empty:
                    all_plays_df = pd.concat([all_plays_df, pbp_df], ignore_index=True)
                time.sleep(random.uniform(0.1, 0.3)) # Small delay between processing results
        
        if all_plays_df.empty:
            logger.warning("No play-by-play data was successfully fetched for any game.")
            return

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
        all_plays_df.rename(columns=column_mapping, inplace=True)
        
        # Remove duplicates before inserting
        original_rows = len(all_plays_df)
        all_plays_df.drop_duplicates(subset=['game_id', 'event_num'], keep='first', inplace=True)
        new_rows = len(all_plays_df)
        if original_rows > new_rows:
            logger.warning(f"Removed {original_rows - new_rows} duplicate plays from fetched data.")

        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(Possessions)")
        table_columns = {info[1] for info in cursor.fetchall()}
        
        df_to_insert = all_plays_df[[col for col in all_plays_df.columns if col in table_columns]]
        
        df_to_insert.to_sql('Possessions', conn, if_exists='append', index=False)
        logger.info(f"Successfully inserted {len(df_to_insert)} total plays for the season.")

    except Exception as e:
        logger.error(f"An unexpected error occurred during possession population: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    from ..config import settings
    populate_possessions(season_to_load=settings.SEASON_ID) 