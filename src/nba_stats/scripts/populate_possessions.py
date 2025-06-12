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

def _get_starters(game_id: str):
    """Fetches the starting lineups for a given game."""
    try:
        boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
        starters = boxscore.get_data_frames()[0]
        starters = starters[starters['START_POSITION'].notna()]
        home_starters = starters[starters['TEAM_ID'] == boxscore.game_summary.get_data_frames()[0]['HOME_TEAM_ID'].iloc[0]]['PLAYER_ID'].tolist()
        away_starters = starters[starters['TEAM_ID'] == boxscore.game_summary.get_data_frames()[0]['VISITOR_TEAM_ID'].iloc[0]]['PLAYER_ID'].tolist()
        return home_starters, away_starters
    except Exception as e:
        logger.error(f"Error fetching starters for game {game_id}: {e}", exc_info=True)
        return [], []

def _fetch_pbp_for_game(game_id: str) -> pd.DataFrame:
    """Fetches play-by-play data for a single game and enriches it with lineup information."""
    logger.info(f"Fetching play-by-play for game_id: {game_id}")
    try:
        pbp = playbyplayv2.PlayByPlayV2(game_id=game_id)
        pbp_df = pbp.get_data_frames()[0]

        home_starters, away_starters = _get_starters(game_id)
        if not home_starters or not away_starters:
            logger.warning(f"Could not determine starters for game {game_id}. Skipping.")
            return pd.DataFrame()

        home_players = set(home_starters)
        away_players = set(away_starters)
        
        enriched_rows = []
        
        for _, row in pbp_df.iterrows():
            # Determine offensive team. Simplified logic, may need refinement.
            # Assumes the team of PLAYER1_ID is the offensive team.
            offensive_team_id = row.get('PLAYER1_TEAM_ID')
            if pd.isna(offensive_team_id) and row['HOMEDESCRIPTION'] is not None:
                 offensive_team_id = pbp.game_summary.get_data_frames()[0]['HOME_TEAM_ID'].iloc[0]
            elif pd.isna(offensive_team_id) and row['VISITORDESCRIPTION'] is not None:
                offensive_team_id = pbp.game_summary.get_data_frames()[0]['VISITOR_TEAM_ID'].iloc[0]

            home_team_id = pbp.game_summary.get_data_frames()[0]['HOME_TEAM_ID'].iloc[0]
            defensive_team_id = home_team_id if offensive_team_id != home_team_id else pbp.game_summary.get_data_frames()[0]['VISITOR_TEAM_ID'].iloc[0]

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
                
                if player_out_id in home_players:
                    home_players.remove(player_out_id)
                    home_players.add(player_in_id)
                elif player_out_id in away_players:
                    away_players.remove(player_out_id)
                    away_players.add(player_in_id)

        return pd.DataFrame(enriched_rows)

    except Exception as e:
        logger.error(f"Error processing PBP for game {game_id}: {e}", exc_info=True)
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
        # Note: Running this without ThreadPoolExecutor for now to avoid rate-limiting issues with the API
        for game_id in game_ids:
            pbp_df = _fetch_pbp_for_game(game_id)
            if not pbp_df.empty:
                all_plays_df = pd.concat([all_plays_df, pbp_df], ignore_index=True)
            time.sleep(random.uniform(0.6, 1.0)) # Be respectful of the API
        
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
    import argparse
    from ..config import settings

    parser = argparse.ArgumentParser(description="Populate possessions data for a given season.")
    parser.add_argument("--season", type=str, default=settings.SEASON_ID, help="The season to populate data for (e.g., '2023-24').")
    args = parser.parse_args()
    
    populate_possessions(season_to_load=args.season) 