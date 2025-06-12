"""Data fetcher for NBA stats application."""

import logging
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from queue import Queue, Empty
from threading import Thread, Event, Lock
from .nba_stats_client import NBAStatsClient
from ..db.connection import DatabaseConnection
import threading

class NBAStatsFetcher:
    """Fetches and processes NBA statistics data."""
    
    def __init__(self, db_path: str):
        """Initialize the NBA stats fetcher.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.client = NBAStatsClient()
        self.db_queue = Queue()
        self.stop_event = Event()
        self.db_lock = Lock()
        self.writer_thread = None
        self.stop_writer = False
        self.logger = logging.getLogger(__name__)
    
    def get_db_connection(self) -> sqlite3.Connection:
        """Create a new database connection for the current thread."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def format_nba_stats_date(self, dt_str: str) -> str:
        """Convert 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS' to 'MM/DD/YYYY' for stats.nba.com."""
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
            try:
                d = datetime.strptime(dt_str, fmt)
                return d.strftime("%m/%d/%Y")
            except ValueError:
                pass
        raise ValueError(f"No valid date format found for '{dt_str}'")
    
    def process_result_set(self, result_set: Dict[str, Any], table_name: str, game_id: str, team_id: int, measure_type: str, season: str) -> None:
        """Process a result set from the NBA Stats API.
        
        Args:
            result_set: Result set from the API
            table_name: Name of the table to insert into
            game_id: Game ID
            team_id: Team ID
            measure_type: Type of statistics ("Base" or "Advanced")
            season: Season ID (e.g., "2023-24")
        """
        if not result_set or 'headers' not in result_set or 'rowSet' not in result_set:
            logging.error("Invalid result set format")
            return
            
        headers = result_set['headers']
        rows = result_set['rowSet']
        
        if not headers or not rows:
            logging.error("Empty result set")
            return
            
        # Map API column names to database column names
        column_mapping = {
            'GROUP_SET': 'group_set',
            'GROUP_VALUE': 'group_value',
            'GP': 'GP',
            'W': 'W',
            'L': 'L',
            'W_PCT': 'W_PCT',
            'MIN': 'MIN',
            'FGM': 'FGM',
            'FGA': 'FGA',
            'FG_PCT': 'FG_PCT',
            'FG3M': 'FG3M',
            'FG3A': 'FG3A',
            'FG3_PCT': 'FG3_PCT',
            'FTM': 'FTM',
            'FTA': 'FTA',
            'FT_PCT': 'FT_PCT',
            'OREB': 'OREB',
            'DREB': 'DREB',
            'REB': 'REB',
            'AST': 'AST',
            'TOV': 'TOV',
            'STL': 'STL',
            'BLK': 'BLK',
            'BLKA': 'BLKA',
            'PF': 'PF',
            'PFD': 'PFD',
            'PTS': 'PTS',
            'PLUS_MINUS': 'PLUS_MINUS',
            'GP_RANK': 'GP_RANK',
            'W_RANK': 'W_RANK',
            'L_RANK': 'L_RANK',
            'W_PCT_RANK': 'W_PCT_RANK',
            'MIN_RANK': 'MIN_RANK',
            'FGM_RANK': 'FGM_RANK',
            'FGA_RANK': 'FGA_RANK',
            'FG_PCT_RANK': 'FG_PCT_RANK',
            'FG3M_RANK': 'FG3M_RANK',
            'FG3A_RANK': 'FG3A_RANK',
            'FG3_PCT_RANK': 'FG3_PCT_RANK',
            'FTM_RANK': 'FTM_RANK',
            'FTA_RANK': 'FTA_RANK',
            'FT_PCT_RANK': 'FT_PCT_RANK',
            'OREB_RANK': 'OREB_RANK',
            'DREB_RANK': 'DREB_RANK',
            'REB_RANK': 'REB_RANK',
            'AST_RANK': 'AST_RANK',
            'TOV_RANK': 'TOV_RANK',
            'STL_RANK': 'STL_RANK',
            'BLK_RANK': 'BLK_RANK',
            'BLKA_RANK': 'BLKA_RANK',
            'PF_RANK': 'PF_RANK',
            'PFD_RANK': 'PFD_RANK',
            'PTS_RANK': 'PTS_RANK',
            'PLUS_MINUS_RANK': 'PLUS_MINUS_RANK',
            'E_OFF_RATING': 'E_OFF_RATING',
            'OFF_RATING_RANK': 'OFF_RATING_RANK',
            'E_DEF_RATING': 'E_DEF_RATING',
            'DEF_RATING_RANK': 'DEF_RATING_RANK',
            'E_NET_RATING': 'E_NET_RATING',
            'NET_RATING_RANK': 'NET_RATING_RANK',
            'AST_PCT': 'AST_PCT',
            'AST_PCT_RANK': 'AST_PCT_RANK',
            'AST_TO_TOV': 'AST_TO_TOV',
            'AST_TO_TOV_RANK': 'AST_TO_TOV_RANK',
            'AST_RATIO': 'AST_RATIO',
            'AST_RATIO_RANK': 'AST_RATIO_RANK',
            'OREB_PCT': 'OREB_PCT',
            'OREB_PCT_RANK': 'OREB_PCT_RANK',
            'DREB_PCT': 'DREB_PCT',
            'DREB_PCT_RANK': 'DREB_PCT_RANK',
            'REB_PCT': 'REB_PCT',
            'REB_PCT_RANK': 'REB_PCT_RANK',
            'TOV_PCT': 'TOV_PCT',
            'TOV_PCT_RANK': 'TOV_PCT_RANK',
            'EFG_PCT': 'EFG_PCT',
            'EFG_PCT_RANK': 'EFG_PCT_RANK',
            'TS_PCT': 'TS_PCT',
            'TS_PCT_RANK': 'TS_PCT_RANK',
            'PACE': 'PACE',
            'PACE_RANK': 'PACE_RANK',
            'PIE': 'PIE',
            'PIE_RANK': 'PIE_RANK'
        }
        
        # Create records for each row
        for row in rows:
            record = {
                'game_id': game_id,
                'team_id': team_id,
                'season': season,
                'measure_type': measure_type,
                'group_set': result_set.get('name', ''),
                'group_value': row[headers.index('GROUP_VALUE')] if 'GROUP_VALUE' in headers else ''
            }
            
            # Add all available metrics
            for api_col, db_col in column_mapping.items():
                if api_col in headers:
                    record[db_col] = row[headers.index(api_col)]
            
            # Queue the record for database insertion
            self.db_queue.put((table_name, record))

    def process_player_tracking_result_set(
        self,
        result_set: Dict[str, Any],
        table_name: str,
        season: str,
        measure_type: str,
        per_mode: str
    ) -> None:
        """Process a player tracking result set from the NBA Stats API.

        Args:
            result_set: Result set from the API (containing 'resultSets')
            table_name: Base name of the table to insert into (e.g., 'player_tracking')
            season: Season ID (e.g., "2023-24")
            measure_type: The specific tracking measure (e.g., "Driving", "Passing")
            per_mode: Per mode used for fetching ("PerGame" or "Totals")
        """
        if not result_set or 'resultSets' not in result_set:
            logging.warning(f"Invalid or empty player tracking result set for {measure_type} {season}")
            return

        # The actual data is usually in the first dictionary within 'resultSets'
        data_container = result_set['resultSets']
        if not isinstance(data_container, list) or not data_container:
            logging.warning(f"resultSets is not a list or is empty for {measure_type} {season}")
            return
        
        actual_result_set = data_container[0] # Assuming the first result set is the one we want

        if 'headers' not in actual_result_set or 'rowSet' not in actual_result_set:
            logging.warning(f"Missing 'headers' or 'rowSet' in player tracking data for {measure_type} {season}")
            return

        headers = actual_result_set['headers']
        rows = actual_result_set['rowSet']

        logging.info(f"Raw headers for {measure_type}: {headers}") # Log raw headers

        if not headers or not rows:
            logging.warning(f"Empty headers or rowSet for {measure_type} {season}")
            return
            
        # Generic column mapping - convert to lowercase and replace spaces with underscores
        # We'll add specific mappings if needed, but this covers most cases
        column_mapping = {header: header.lower().replace(' ', '_').replace('-', '_').replace('%', '_pct') for header in headers}
        
        # Ensure essential columns are present if possible
        player_id_col = 'PLAYER_ID' # Standard NBA stats API player ID column
        if player_id_col not in headers:
            logging.error(f"'{player_id_col}' not found in headers for {measure_type}. Cannot process.")
            return

        # Determine the specific table name
        specific_table_name = f"{table_name}_{measure_type.lower().replace(' ', '_')}"

        logging.info(f"Processing {len(rows)} rows for {specific_table_name} ({season} {per_mode})")

        # Create records for each row
        for row in rows:
            record = {
                'season': season,
                'per_mode': per_mode,
                'measure_type': measure_type
                # Player ID will be added from the mapping
            }
            
            # Add all available metrics using the mapping
            for api_col, db_col in column_mapping.items():
                try:
                    record[db_col] = row[headers.index(api_col)]
                except IndexError:
                    logging.warning(f"IndexError for column {api_col} in {measure_type} data.")
                    record[db_col] = None # Or some other default value
                except Exception as e:
                    logging.error(f"Error processing column {api_col}: {e}")
                    record[db_col] = None

            # Rename PLAYER_ID to player_id for consistency if it exists
            if 'player_id' in record and player_id_col != 'player_id':
                record['player_id'] = record.pop('player_id')

            # Queue the record for database insertion
            self.db_queue.put((specific_table_name, record))

    def database_writer_thread(self) -> None:
        """Database writer thread that processes records from the queue."""
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            batch = []
            last_table = None
            
            while not self.stop_event.is_set():
                try:
                    # Get next record from queue with timeout
                    item = self.db_queue.get(timeout=1.0)
                    if item is None:  # Sentinel value to stop the thread
                        break
                        
                    table_name, record = item
                    
                    # If we have a batch and the table changes, insert the current batch
                    if last_table and last_table != table_name and batch:
                        self._insert_batch(cursor, last_table, batch)
                        batch = []
                    
                    batch.append(record)
                    last_table = table_name
                    
                    # Insert batch if it reaches the size limit
                    if len(batch) >= 100:
                        self._insert_batch(cursor, table_name, batch)
                        batch = []
                        
                    # Commit every 1000 records
                    if len(batch) % 1000 == 0:
                        conn.commit()
                        
                except Empty:
                    # Insert any remaining records in the batch
                    if batch and last_table:
                        self._insert_batch(cursor, last_table, batch)
                        batch = []
                        conn.commit()
                        
                except Exception as e:
                    logging.error(f"Error in database writer thread: {str(e)}")
                    if batch:
                        batch = []
            
            # Insert any remaining records
            if batch and last_table:
                self._insert_batch(cursor, last_table, batch)
                conn.commit()
                
        except Exception as e:
            logging.error(f"Database writer thread error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
                
    def _insert_batch(self, cursor: sqlite3.Cursor, table_name: str, records: List[Dict[str, Any]]) -> None:
        """Insert a batch of records into the database.
        
        Args:
            cursor: Database cursor
            table_name: Name of the table to insert into
            records: List of records to insert
        """
        if not records:
            return
            
        try:
            # Get column names from the first record
            columns = list(records[0].keys())
            placeholders = ','.join(['?' for _ in columns])
            column_str = ','.join(columns)
            
            # Create the INSERT OR REPLACE statement
            sql = f"""
            INSERT OR REPLACE INTO {table_name}
            ({column_str})
            VALUES ({placeholders})
            """
            
            # Convert records to tuples in the same order as columns
            values = [tuple(record.get(col) for col in columns) for record in records]
            
            # Execute the batch insert
            cursor.executemany(sql, values)
            
        except Exception as e:
            logging.error(f"Error inserting batch: {str(e)}")
            raise

    def fetch_team_dashboard_data(self, team_id: int, measure_type: str = "Base", game_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch team dashboard data for all group sets.
        
        Args:
            team_id: NBA team ID
            measure_type: Type of stats to fetch ("Base" or "Advanced")
            game_id: Optional game ID to filter by
            
        Returns:
            Dictionary containing team dashboard data for all group sets
        """
        try:
            group_sets = [
                "Overall",
                "Location",
                "WinsLosses",
                "Month",
                "PrePostAllStar",
                "DaysRest"
            ]
            
            all_data = {
                "resultSets": []
            }
            
            for group_set in group_sets:
                try:
                    data = self.client.get_team_dashboard(
                        team_id=team_id,
                        measure_type=measure_type,
                        group_set=group_set,
                        game_id=game_id
                    )
                    
                    if data and "resultSets" in data:
                        all_data["resultSets"].extend(data["resultSets"])
                        
                except Exception as e:
                    logging.error(f"Error fetching {group_set} dashboard for team {team_id}: {str(e)}")
                    continue
                    
            return all_data
            
        except Exception as e:
            logging.error(f"Error fetching team dashboard data: {str(e)}")
            raise

    def fetch_unprocessed_games(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch list of unprocessed games.
        
        Args:
            limit: Maximum number of games to return
            
        Returns:
            List of unprocessed games with game_id, home_team_id, and away_team_id
        """
        conn = self.get_db_connection()
        try:
            cursor = conn.cursor()
            
            # Get games that haven't been processed
            query = """
                SELECT g.game_id, g.home_team_id, g.away_team_id
                FROM games g
                LEFT JOIN overall_team_dashboard otd 
                    ON g.game_id = otd.game_id 
                WHERE otd.game_id IS NULL
            """
            
            if limit:
                query += f" LIMIT {limit}"
                
            cursor.execute(query)
            games = [
                {
                    'game_id': row[0],
                    'home_team_id': row[1],
                    'away_team_id': row[2]
                }
                for row in cursor.fetchall()
            ]
            
            return games
            
        except Exception as e:
            logging.error(f"Error fetching unprocessed games: {str(e)}")
            raise
        finally:
            conn.close()
    
    def fetch_player_tracking_stats(
        self,
        season: str,
        per_mode: str = "PerGame",
        season_type: str = "Regular Season"
    ) -> None:
        """Fetch various player tracking stats for a given season.

        Fetches: Driving, Passing, Touches (Elbow, Post, Paint), Catch & Shoot, Pull Up Shots.

        Args:
            season: Season in YYYY-YY format (e.g., "2023-24")
            per_mode: Mode for stats ("PerGame", "Totals")
            season_type: Type of season ("Regular Season", "Playoffs", etc.)
        """
        tracking_types = [
            "SpeedDistance", 
            "Driving", 
            # "Passing", 
            # "ElbowTouch",
            # "PostTouch",
            # "PaintTouch",
            # "CatchShoot",
            # "PullUpShot",
        ]
        
        base_table_name = "player_tracking"

        # Ensure writer thread is running if called independently
        if self.writer_thread is None or not self.writer_thread.is_alive():
             logging.info("Starting DB writer thread for player tracking fetch.")
             self.stop_event.clear() # Ensure stop event is clear
             self.db_writer_thread = threading.Thread(target=self.database_writer_thread)
             self.db_writer_thread.start()
             started_thread_locally = True
        else:
             started_thread_locally = False

        try:
            for measure_type in tracking_types:
                try:
                    logging.info(f"Fetching player tracking data: {measure_type} for {season} ({per_mode})")
                    data = self.client.get_league_player_tracking_stats(
                        season=season,
                        per_mode=per_mode,
                        pt_measure_type=measure_type,
                        season_type=season_type
                    )

                    if data:
                        self.process_player_tracking_result_set(
                            result_set=data,
                            table_name=base_table_name,
                            season=season,
                            measure_type=measure_type,
                            per_mode=per_mode
                        )
                    else:
                        logging.warning(f"No data returned for {measure_type} - {season} - {per_mode}")
                        
                except Exception as e:
                    logging.error(f"Error fetching/processing {measure_type} for season {season}: {str(e)}")
                    continue # Continue to next tracking type

        finally:
            # If this function started the thread, it should also stop it.
            if started_thread_locally:
                logging.info("Signaling DB writer thread to stop after player tracking fetch.")
                self.db_queue.put(None)
                if self.db_writer_thread:
                    self.db_writer_thread.join()
                logging.info("DB writer thread stopped after player tracking fetch.")

    def fetch_all_data(self, measure_type: str = "Base", limit: int = 100) -> None:
        """Fetch all data for unprocessed games.
        
        Args:
            measure_type: Type of stats to fetch ("Base" or "Advanced")
            limit: Maximum number of games to process
        """
        try:
            # Start database writer thread
            self.db_writer_thread = threading.Thread(target=self.database_writer_thread)
            self.db_writer_thread.start()
            
            # Get unprocessed games
            games = self.fetch_unprocessed_games(limit=limit)
            if not games:
                logging.info("No unprocessed games found")
                return
                
            logging.info(f"Processing {len(games)} games")
            
            for game in games:
                game_id = game['game_id']
                home_team_id = game['home_team_id']
                away_team_id = game['away_team_id']
                
                # Extract season from game_id
                season = f"20{game_id[1:3]}-{str(int(game_id[1:3]) + 1).zfill(2)}"
                
                # Fetch data for both teams
                for team_id in [home_team_id, away_team_id]:
                    try:
                        # Fetch team dashboard data
                        data = self.fetch_team_dashboard_data(
                            team_id=team_id,
                            measure_type=measure_type,
                            game_id=game_id
                        )
                        
                        if data:
                            # Process each result set
                            for result_set in data.get('resultSets', []):
                                if result_set.get('name') == 'OverallTeamDashboard':
                                    self.process_result_set(result_set, 'overall_team_dashboard', game_id, team_id, measure_type, season)
                                elif result_set.get('name') == 'LocationTeamDashboard':
                                    self.process_result_set(result_set, 'location_team_dashboard', game_id, team_id, measure_type, season)
                                elif result_set.get('name') == 'WinsLossesTeamDashboard':
                                    self.process_result_set(result_set, 'wins_losses_team_dashboard', game_id, team_id, measure_type, season)
                                elif result_set.get('name') == 'MonthTeamDashboard':
                                    self.process_result_set(result_set, 'month_team_dashboard', game_id, team_id, measure_type, season)
                                elif result_set.get('name') == 'PrePostAllStarTeamDashboard':
                                    self.process_result_set(result_set, 'pre_postallstar_team_dashboard', game_id, team_id, measure_type, season)
                                elif result_set.get('name') == 'DaysRestTeamDashboard':
                                    self.process_result_set(result_set, 'days_rest_team_dashboard', game_id, team_id, measure_type, season)
                                    
                    except Exception as e:
                        logging.error(f"Error processing team {team_id} for game {game_id}: {str(e)}")
                        continue
                        
        except Exception as e:
            logging.error(f"Error during data fetch: {str(e)}")
            raise
        finally:
            # Signal database writer thread to stop
            self.db_queue.put(None)
            if self.db_writer_thread:
                self.db_writer_thread.join() 