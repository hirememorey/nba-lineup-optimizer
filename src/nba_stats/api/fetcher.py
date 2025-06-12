"""Data fetcher for NBA stats application."""

import logging
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..config.settings import MAX_WORKERS, SEASON_ID, MIN_MINUTES_THRESHOLD
from .client import NBAStatsClient
from .sample_data import SAMPLE_PLAYERS
from ..models.player import Player
from ..db.connection import DatabaseConnection

class NBAStatsFetcher:
    """Fetches and processes NBA player statistics."""
    
    def __init__(self, use_sample_data: bool = True):
        """Initialize the NBA stats fetcher.
        
        Args:
            use_sample_data: Whether to use sample data instead of making API calls
        """
        self.api_client = NBAStatsClient()
        self.db = DatabaseConnection()
        self.use_sample_data = use_sample_data
    
    def fetch_player_data(
        self,
        player_id: int,
        player_name: str,
        team_id: int,
        season: str = SEASON_ID
    ) -> Optional[Player]:
        """Fetch all available data for a player.
        
        Args:
            player_id: NBA player ID
            player_name: Player's name
            team_id: Team ID
            season: Season ID (e.g., "2024-25")
            
        Returns:
            Optional[Player]: Player object with all available stats or None if fetch fails
        """
        try:
            if self.use_sample_data:
                # Use sample data
                for player_data in SAMPLE_PLAYERS:
                    if player_data["player_id"] == player_id:
                        return Player.from_dict(player_data)
                return None
            
            # Initialize player with basic info
            player_data = {
                "player_id": player_id,
                "player_name": player_name,
                "team_id": team_id,
                "season_id": season
            }
            
            # Fetch basic stats
            basic_stats = self.api_client.get_player_stats(player_id, season)
            if basic_stats:
                self._process_basic_stats(basic_stats, player_data)
            
            # Fetch advanced stats
            advanced_stats = self.api_client.get_player_advanced_stats(player_id, season)
            if advanced_stats:
                self._process_advanced_stats(advanced_stats, player_data)
            
            # Fetch tracking stats
            tracking_stats = self.api_client.get_player_tracking_stats(player_id, season)
            if tracking_stats:
                self._process_tracking_stats(tracking_stats, player_data)
            
            # Fetch shooting splits
            shooting_splits = self.api_client.get_player_shooting_splits(player_id, season)
            if shooting_splits:
                self._process_shooting_splits(shooting_splits, player_data)
            
            return Player.from_dict(player_data)
            
        except Exception as e:
            logging.error(f"Error fetching data for player {player_name} (ID: {player_id}): {e}")
            return None
    
    def fetch_all_players(self, season: str = SEASON_ID) -> List[Player]:
        """Fetch data for all players in the specified season.
        
        Args:
            season: Season ID (e.g., "2024-25")
            
        Returns:
            List[Player]: List of Player objects with their statistics
        """
        players = []
        
        try:
            if self.use_sample_data:
                # Use sample data
                for player_data in SAMPLE_PLAYERS:
                    player = Player.from_dict(player_data)
                    players.append(player)
                    logging.info(f"Successfully loaded sample data for {player.player_name} (ID: {player.player_id})")
                return players
            
            # Fetch all players from NBA Stats API
            logging.info("Fetching players from NBA Stats API")
            response = self.api_client.make_request(
                "/leaguedashplayerstats",
                {
                    "Season": season,
                    "SeasonType": "Regular Season",
                    "LeagueID": "00",
                    "PerMode": "PerGame",
                    "MinMinutes": MIN_MINUTES_THRESHOLD
                }
            )
            
            if not response or "resultSets" not in response:
                logging.error("Failed to fetch players from NBA Stats API")
                return players
            
            # Process player data
            headers = response["resultSets"][0].get("headers", [])
            rows = response["resultSets"][0].get("rowSet", [])
            
            if not headers or not rows:
                logging.error("No player data found in API response")
                return players
            
            # Map column indices
            try:
                player_id_idx = headers.index("PLAYER_ID")
                player_name_idx = headers.index("PLAYER_NAME")
                team_id_idx = headers.index("TEAM_ID")
                minutes_idx = headers.index("MIN")
            except ValueError as e:
                logging.error(f"Required column not found in API response: {e}")
                return players
            
            # Process players in parallel
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                future_to_player = {
                    executor.submit(
                        self.fetch_player_data,
                        row[player_id_idx],
                        row[player_name_idx],
                        row[team_id_idx],
                        season
                    ): (row[player_id_idx], row[player_name_idx])
                    for row in rows
                    if row[minutes_idx] >= MIN_MINUTES_THRESHOLD
                }
                
                for future in as_completed(future_to_player):
                    player_id, player_name = future_to_player[future]
                    try:
                        player = future.result()
                        if player:
                            players.append(player)
                            logging.info(f"Successfully fetched data for {player_name} (ID: {player_id})")
                    except Exception as e:
                        logging.error(f"Error processing player {player_name} (ID: {player_id}): {e}")
            
        except Exception as e:
            logging.error(f"Error fetching all players: {e}")
        
        return players
    
    def _process_basic_stats(self, stats: Dict[str, Any], player_data: Dict[str, Any]) -> None:
        """Process basic player statistics.
        
        Args:
            stats: Raw statistics data from API
            player_data: Dictionary to update with processed stats
        """
        if "resultSets" in stats and stats["resultSets"]:
            headers = stats["resultSets"][0].get("headers", [])
            row_set = stats["resultSets"][0].get("rowSet", [])
            
            if headers and row_set and row_set[0]:
                stats_dict = dict(zip(headers, row_set[0]))
                
                # Map API fields to our model fields
                field_mapping = {
                    "MIN": "minutes_played",
                    "FG_PCT": "field_goal_percentage",
                    "FG3_PCT": "three_point_percentage",
                    "FT_PCT": "free_throw_percentage",
                    "REB": "rebounds",
                    "AST": "assists",
                    "STL": "steals",
                    "BLK": "blocks",
                    "PTS": "points",
                    "PLUS_MINUS": "plus_minus"
                }
                
                for api_field, model_field in field_mapping.items():
                    if api_field in stats_dict:
                        player_data[model_field] = stats_dict[api_field]
    
    def _process_advanced_stats(self, stats: Dict[str, Any], player_data: Dict[str, Any]) -> None:
        """Process advanced player statistics.
        
        Args:
            stats: Raw statistics data from API
            player_data: Dictionary to update with processed stats
        """
        if "resultSets" in stats and stats["resultSets"]:
            headers = stats["resultSets"][0].get("headers", [])
            row_set = stats["resultSets"][0].get("rowSet", [])
            
            if headers and row_set and row_set[0]:
                stats_dict = dict(zip(headers, row_set[0]))
                
                # Map API fields to our model fields
                field_mapping = {
                    "USG_PCT": "usage_rate",
                    "PER": "player_efficiency_rating",
                    "TS_PCT": "true_shooting_percentage",
                    "WS": "win_shares",
                    "BPM": "box_plus_minus",
                    "VORP": "value_over_replacement"
                }
                
                for api_field, model_field in field_mapping.items():
                    if api_field in stats_dict:
                        player_data[model_field] = stats_dict[api_field]
    
    def _process_tracking_stats(self, stats: Dict[str, Any], player_data: Dict[str, Any]) -> None:
        """Process player tracking statistics.
        
        Args:
            stats: Raw statistics data from API
            player_data: Dictionary to update with processed stats
        """
        if "resultSets" in stats and stats["resultSets"]:
            headers = stats["resultSets"][0].get("headers", [])
            row_set = stats["resultSets"][0].get("rowSet", [])
            
            if headers and row_set and row_set[0]:
                stats_dict = dict(zip(headers, row_set[0]))
                
                # Map API fields to our model fields
                field_mapping = {
                    "AVG_SPEED": "average_speed",
                    "DIST_MILES": "distance_covered",
                    "AVG_SPEED_OFF": "average_speed_offense",
                    "AVG_SPEED_DEF": "average_speed_defense"
                }
                
                for api_field, model_field in field_mapping.items():
                    if api_field in stats_dict:
                        player_data[model_field] = stats_dict[api_field]
    
    def _process_shooting_splits(self, stats: Dict[str, Any], player_data: Dict[str, Any]) -> None:
        """Process player shooting splits by distance.
        
        Args:
            stats: Raw statistics data from API
            player_data: Dictionary to update with processed stats
        """
        if "resultSets" in stats and stats["resultSets"]:
            for result_set in stats["resultSets"]:
                headers = result_set.get("headers", [])
                row_set = result_set.get("rowSet", [])
                
                if headers and row_set:
                    for row in row_set:
                        stats_dict = dict(zip(headers, row))
                        
                        # Process shot distance data
                        if "GROUP_VALUE" in stats_dict:
                            distance = stats_dict["GROUP_VALUE"]
                            fga = stats_dict.get("FGA", 0)
                            fgm = stats_dict.get("FGM", 0)
                            
                            if "Less Than 5 ft." in distance:
                                player_data["shot_attempts_0_3"] = fga
                                player_data["shot_makes_0_3"] = fgm
                            elif "5-9 ft." in distance:
                                player_data["shot_attempts_3_10"] = fga
                                player_data["shot_makes_3_10"] = fgm
                            elif "10-14 ft." in distance or "15-19 ft." in distance:
                                player_data["shot_attempts_10_16"] = fga
                                player_data["shot_makes_10_16"] = fgm
                            elif "20-24 ft." in distance:
                                player_data["shot_attempts_16_3pt"] = fga
                                player_data["shot_makes_16_3pt"] = fgm
                            elif "25-29 ft." in distance:
                                player_data["shot_attempts_3pt"] = fga
                                player_data["shot_makes_3pt"] = fgm 