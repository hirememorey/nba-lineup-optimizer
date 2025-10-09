import logging
import sqlite3
import pandas as pd
from nba_api.stats.endpoints import leaguegamelog
from tenacity import retry, stop_after_attempt, wait_exponential
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = "src/nba_stats/db/nba_stats.db"

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_games_for_season(season: str):
    """Fetches all game logs for a given season using the NBA API."""
    logger.info(f"Fetching game logs for season: {season}...")
    try:
        # SeasonType can be 'Regular Season' or 'Playoffs'
        regular_season_games = leaguegamelog.LeagueGameLog(season=season, season_type_all_star="Regular Season").get_data_frames()[0]
        playoff_games = leaguegamelog.LeagueGameLog(season=season, season_type_all_star="Playoffs").get_data_frames()[0]
        
        all_games = pd.concat([regular_season_games, playoff_games], ignore_index=True)
        
        if all_games.empty:
            logger.warning(f"No games found for season {season}.")
            return pd.DataFrame()
            
        logger.info(f"Successfully fetched {len(all_games)} game log entries for season {season}.")
        return all_games
        
    except Exception as e:
        logger.error(f"Error fetching game logs for season {season}: {e}")
        raise

def transform_game_data(games_df: pd.DataFrame, season: str):
    """Transforms the raw game log data to match the Games table schema."""
    if games_df.empty:
        return pd.DataFrame()
        
    logger.info("Transforming game data...")
    # Get unique games
    unique_games = games_df[['GAME_ID', 'GAME_DATE', 'MATCHUP']].drop_duplicates()
    
    games_to_insert = []
    for _, row in unique_games.iterrows():
        game_id = row['GAME_ID']
        game_date = row['GAME_DATE']
        matchup = row['MATCHUP']
        
        # Extract team IDs
        team_abbr = matchup.split(' vs. ')
        if len(team_abbr) != 2:
            team_abbr = matchup.split(' @ ')
        
        home_team_abbr = team_abbr[1]
        away_team_abbr = team_abbr[0]
        
        home_team_id = games_df[games_df['TEAM_ABBREVIATION'] == home_team_abbr]['TEAM_ID'].iloc[0]
        away_team_id = games_df[games_df['TEAM_ABBREVIATION'] == away_team_abbr]['TEAM_ID'].iloc[0]

        # Determine season type
        game_info = games_df[games_df['GAME_ID'] == game_id].iloc[0]
        is_playoff_game = 'Playoffs' in games_df[games_df['GAME_ID'] == game_id]['SEASON_ID'].astype(str).unique()[0]

        games_to_insert.append({
            'game_id': game_id,
            'game_date': game_date,
            'home_team_id': home_team_id,
            'away_team_id': away_team_id,
            'home_team_score': None, # Scores are not in this endpoint, can be populated later
            'away_team_score': None,
            'season': season,
            'season_type': 'Playoffs' if is_playoff_game else 'Regular Season',
            'season_id': game_info['SEASON_ID']
        })
        
    transformed_df = pd.DataFrame(games_to_insert)
    logger.info(f"Transformed {len(transformed_df)} unique games.")
    return transformed_df

def populate_games_table(df: pd.DataFrame):
    """Populates the Games table in the database."""
    if df.empty:
        logger.info("No game data to populate.")
        return
        
    logger.info(f"Connecting to database at {DB_PATH} to populate Games table...")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Use INSERT OR IGNORE to avoid errors on duplicate game_ids
            cols = ', '.join(df.columns)
            placeholders = ', '.join(['?'] * len(df.columns))
            sql = f"INSERT OR IGNORE INTO Games ({cols}) VALUES ({placeholders})"
            
            cursor.executemany(sql, df.to_records(index=False).tolist())
            conn.commit()
            
            logger.info(f"Successfully inserted/ignored {len(df)} games into the Games table. Affected rows: {cursor.rowcount}")

    except sqlite3.Error as e:
        logger.error(f"Database error during population: {e}")
        raise

def main(season: str):
    """Main function to fetch and populate games for a season."""
    logger.info(f"--- Starting Games population for season: {season} ---")
    try:
        raw_games_df = fetch_games_for_season(season)
        transformed_df = transform_game_data(raw_games_df, season)
        populate_games_table(transformed_df)
        logger.info(f"--- Successfully finished Games population for season: {season} ---")
    except Exception as e:
        logger.error(f"A failure occurred during the game population process: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate the Games table for a specific season.")
    parser.add_argument("--season", type=str, required=True, help="The season to populate, e.g., '2022-23'.")
    args = parser.parse_args()
    
    main(args.season)

