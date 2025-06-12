"""NBA Stats API client for making direct HTTP requests."""

import time
import random
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class NBAStatsClient:
    """Client for making requests to the NBA Stats API."""
    
    def __init__(self):
        """Initialize the NBA Stats API client."""
        self.base_url = "https://stats.nba.com/stats"
        self.session = requests.Session()
        
        # Configure retry strategy with exponential backoff and jitter
        retry_strategy = Retry(
            total=10,  # Increased number of retries
            backoff_factor=2,  # Increased backoff factor
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            respect_retry_after_header=True
        )
        
        # Create an adapter with the retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Host': 'stats.nba.com',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.nba.com/',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'x-nba-stats-origin': 'stats',
            'x-nba-stats-token': 'true',
            'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
        })
        
        # Rate limiting parameters
        self.requests_per_minute = 100
        self.request_interval = 60.0 / self.requests_per_minute
        self.last_request_time = 0.0
        self.min_request_interval = 5.0  # Minimum time between requests in seconds
    
    def _setup_session(self):
        """Set up the session with required headers and retry strategy."""
        self.session.headers.update(self.session.headers)
    
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits by waiting between requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        # Add a random jitter to the request interval
        time.sleep(random.uniform(0.5, 1.5))
        
        self.last_request_time = time.time()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API request with random user agent."""
        headers = self.session.headers.copy()
        headers["User-Agent"] = random.choice([
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ])
        return headers
    
    def _handle_rate_limit(self, response: requests.Response) -> None:
        """Handle rate limiting by waiting for the specified time."""
        if response.status_code == 429:  # Too Many Requests
            retry_after = int(response.headers.get("Retry-After", 30))
            logging.warning(f"Rate limited. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
    
    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff time."""
        base_delay = 2
        max_delay = 30
        backoff = min(base_delay * (2 ** attempt), max_delay)
        return backoff + random.uniform(0, 1)
    
    def make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make a request to the NBA Stats API with retry logic and error handling.
        
        Args:
            endpoint: The API endpoint to call
            params: Optional query parameters
            
        Returns:
            Dict containing the API response or None if the request failed
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            self._wait_for_rate_limit()
            
            # Ensure params is a dictionary
            if params is None:
                params = {}
            
            # Add required parameters if not present
            if 'LeagueID' not in params:
                params['LeagueID'] = '00'
            
            logger.info(f"Making request to {url} with params: {params}")
            response = self.session.get(
                url,
                params=params,
                timeout=30,
                allow_redirects=True
            )
            
            logger.info(f"Received response with status code: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to make request to {endpoint} after multiple retries: {e}")
            return None
    
    def get_teams(self) -> List[Dict[str, Any]]:
        """Get list of all NBA teams.
        
        Returns:
            List of team dictionaries containing team information
        """
        endpoint = "leaguedashteamstats"
        params = {
            "LastNGames": 0,
            "LeagueID": "00",
            "MeasureType": "Base",
            "Month": 0,
            "OpponentTeamID": 0,
            "PaceAdjust": "N",
            "PerMode": "PerGame",
            "Period": 0,
            "PlusMinus": "N",
            "Rank": "N",
            "Season": "2023-24",
            "SeasonType": "Regular Season",
            "TeamID": 0
        }
        
        response = self.make_request(endpoint, params)
        
        teams = []
        for row in response["resultSets"][0]["rowSet"]:
            teams.append({
                "teamId": row[0],
                "teamName": row[1],
                "teamAbbreviation": row[4]
            })
        
        return teams
    
    def get_schedule(self, season: str) -> List[Dict[str, Any]]:
        """Get the NBA schedule for a given season.
        
        Args:
            season: Season in YYYY-YY format (e.g., "2023-24")
            
        Returns:
            List of game dictionaries containing schedule information
        """
        endpoint = "leaguegamelog"
        params = {
            "Counter": 0,
            "DateFrom": "",
            "DateTo": "",
            "Direction": "DESC",
            "LeagueID": "00",
            "PlayerOrTeam": "T",
            "Season": season,
            "SeasonType": "Regular Season",
            "Sorter": "DATE"
        }
        
        response = self.make_request(endpoint, params)
        
        games = []
        for row in response["resultSets"][0]["rowSet"]:
            games.append({
                "gameId": row[4],
                "teamId": row[1],
                "seasonStartDate": f"{season[:4]}-10-01",  # NBA season typically starts in October
                "gameDate": row[5],
                "season": season
            })
        
        return games
    
    def get_team_dashboard(
        self,
        team_id: int,
        measure_type: str,
        group_set: str,
        game_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch team dashboard data.
        
        Args:
            team_id: NBA team ID
            measure_type: Type of statistics ("Base" or "Advanced")
            group_set: Group set for the dashboard ("Overall", "Location", etc.)
            game_id: Optional game ID to filter by
            
        Returns:
            Dictionary containing team dashboard data
        """
        try:
            # Extract season from game_id if provided
            season = None
            if game_id:
                season = f"20{game_id[1:3]}-{str(int(game_id[1:3]) + 1).zfill(2)}"
            else:
                # Default to current season if no game_id provided
                season = "2023-24"  # TODO: Make this configurable
            
            endpoint = "teamdashboardbygeneralsplits"
            params = {
                'TeamID': team_id,
                'Season': season,
                'SeasonType': 'Regular Season',
                'MeasureType': measure_type,
                'PerMode': 'PerGame',
                'PlusMinus': 'N',
                'PaceAdjust': 'N',
                'Rank': 'N',
                'Outcome': '',
                'Location': '',
                'Month': '0',
                'SeasonSegment': '',
                'DateFrom': '',
                'DateTo': '',
                'OpponentTeamID': '0',
                'VsConference': '',
                'VsDivision': '',
                'GameSegment': '',
                'Period': '0',
                'LastNGames': '0'
            }
            
            # Add game_id filter if provided
            if game_id:
                params['GameID'] = game_id
            
            response = self.make_request(endpoint, params)
            
            if not response or 'resultSets' not in response:
                logger.error(f"Invalid response format for team {team_id}")
                return {'resultSets': []}
            
            # Find the result set for the requested group_set
            result_sets = response['resultSets']
            target_set = None
            
            # Map group_set to result set name
            group_set_mapping = {
                'Overall': 'OverallTeamDashboard',
                'Location': 'LocationTeamDashboard',
                'WinsLosses': 'WinsLossesTeamDashboard',
                'Month': 'MonthTeamDashboard',
                'PrePostAllStar': 'PrePostAllStarTeamDashboard',
                'DaysRest': 'DaysRestTeamDashboard'
            }
            
            target_name = group_set_mapping.get(group_set)
            if not target_name:
                logger.error(f"Invalid group_set: {group_set}")
                return {'resultSets': []}
            
            for rs in result_sets:
                if rs.get('name') == target_name:
                    target_set = rs
                    break
            
            if not target_set:
                logger.error(f"Could not find result set for group_set {group_set}")
                return {'resultSets': []}
            
            # Add group_set to each row
            if 'rowSet' in target_set:
                for row in target_set['rowSet']:
                    row.append(group_set)
                if 'headers' in target_set:
                    target_set['headers'].append('GROUP_SET')
            
            return {'resultSets': [target_set]}
            
        except Exception as e:
            logger.error(f"Error fetching team dashboard data: {str(e)}")
            return {'resultSets': []}
    
    def get_player_stats(
        self,
        player_id: int,
        season: str,
        season_type: str = "Regular Season",
        per_mode: str = "PerGame"
    ) -> Optional[Dict[str, Any]]:
        """
        Get player statistics for a given season.
        
        Args:
            player_id: The NBA player ID
            season: The NBA season in YYYY-YY format
            
        Returns:
            Dict containing player statistics or None if the request failed
        """
        endpoint = "/playerdashboardbygeneralsplits"
        params = {
            "PlayerID": str(player_id),
            "Season": season,
            "SeasonType": season_type,
            "MeasureType": "Base",
            "PerMode": per_mode,
            "LeagueID": "00",
            "LastNGames": "0",
            "Month": "0",
            "OpponentTeamID": "0",
            "PaceAdjust": "N",
            "Period": "0",
            "PlusMinus": "N",
            "Rank": "N",
            "SeasonSegment": "",
            "DateFrom": "",
            "DateTo": "",
            "GameSegment": "",
            "Outcome": "",
            "Location": "",
            "VsConference": "",
            "VsDivision": ""
        }
        return self.make_request(endpoint, params)
    
    def get_player_advanced_stats(
        self,
        player_id: int,
        season: str,
        season_type: str = "Regular Season",
        per_mode: str = "PerGame"
    ) -> Optional[Dict[str, Any]]:
        """Get player advanced statistics.
        
        Args:
            player_id: NBA player ID
            season: Season ID (e.g., "2024-25")
            season_type: Type of season (Regular Season, Playoffs, etc.)
            per_mode: "PerGame", "Totals", or "Per100Possessions"
            
        Returns:
            Optional[Dict[str, Any]]: Player advanced statistics or None if request fails
        """
        endpoint = "/playerdashboardbygeneralsplits"
        params = {
            "PlayerID": player_id,
            "Season": season,
            "SeasonType": season_type,
            "LeagueID": "00",
            "PerMode": per_mode,
            "MeasureType": "Advanced",
            "LastNGames": "0",
            "Month": "0",
            "OpponentTeamID": "0",
            "PaceAdjust": "N",
            "Period": "0",
            "PlusMinus": "N",
            "Rank": "N",
            "SeasonSegment": "",
            "DateFrom": "",
            "DateTo": "",
            "GameSegment": "",
            "Outcome": "",
            "Location": "",
            "VsConference": "",
            "VsDivision": ""
        }
        
        return self.make_request(endpoint, params)
    
    def get_player_tracking_stats(
        self,
        player_id: int,
        season: str,
        season_type: str = "Regular Season",
        per_mode: str = "PerGame"
    ) -> Optional[Dict[str, Any]]:
        """Get player tracking statistics.
        
        Args:
            player_id: NBA player ID
            season: Season ID (e.g., "2024-25")
            season_type: Type of season (Regular Season, Playoffs, etc.)
            per_mode: "PerGame", "Totals", or "Per100Possessions"
            
        Returns:
            Optional[Dict[str, Any]]: Player tracking statistics or None if request fails
        """
        endpoint = "playerdashptshots"
        params = {
            "PlayerID": player_id,
            "Season": season,
            "SeasonType": season_type,
            "LeagueID": "00",
            "PerMode": per_mode
        }
        
        return self.make_request(endpoint, params)
    
    def get_player_shooting_splits(
        self,
        player_id: int,
        season: str,
        season_type: str = "Regular Season",
        per_mode: str = "PerGame"
    ) -> Optional[Dict[str, Any]]:
        """Get player shooting splits by distance.
        
        Args:
            player_id: NBA player ID
            season: Season ID (e.g., "2024-25")
            season_type: Type of season (Regular Season, Playoffs, etc.)
            per_mode: "PerGame", "Totals", or "Per100Possessions"
            
        Returns:
            Optional[Dict[str, Any]]: Player shooting splits or None if request fails
        """
        endpoint = "playerdashptshots"
        params = {
            "PlayerID": player_id,
            "Season": season,
            "SeasonType": season_type,
            "LeagueID": "00",
            "PerMode": per_mode
        }
        
        return self.make_request(endpoint, params)
    
    def get_all_teams(self) -> List[Dict[str, Any]]:
        """
        Fetch all NBA teams data.
        
        Returns:
            List[Dict[str, Any]]: List of team data dictionaries
        """
        endpoint = "leaguedashteamstats"
        params = {
            "MeasureType": "Base",
            "PerMode": "PerGame",
            "PlusMinus": "N",
            "PaceAdjust": "N",
            "Rank": "N",
            "Season": "2023-24",
            "SeasonType": "Regular Season",
            "LastNGames": 0,
            "Month": 0,
            "OpponentTeamID": 0,
            "Period": 0,
            "SeasonSegment": "",
            "Conference": "",
            "Division": "",
            "GameSegment": "",
            "DateFrom": "",
            "DateTo": "",
            "Location": "",
            "Outcome": "",
            "PORound": 0,
            "TeamID": 0,
            "VsConference": "",
            "VsDivision": ""
        }
        
        response = self.make_request(endpoint, params)
        if not response or "resultSets" not in response:
            logger.error("No response or resultSets from API")
            return []
            
        result_set = response["resultSets"][0]
        if not result_set or "rowSet" not in result_set:
            logger.error("No result_set or rowSet in API response")
            return []
            
        headers = result_set["headers"]
        logger.info(f"API Headers: {headers}")
        
        teams = []
        for row in result_set["rowSet"]:
            team = dict(zip(headers, row))
            logger.info(f"Team data: {team}")
            try:
                team_id = team["TEAM_ID"]
                teams.append({
                    "team_id": team_id,
                    "team_name": team["TEAM_NAME"],
                    "team_abbreviation": team["TEAM_NAME"][:3].upper(),  # Use first 3 letters of team name
                    "city": " ".join(team["TEAM_NAME"].split()[:-1]),  # Everything before the last word
                    "conference": self._get_team_conference(team_id),
                    "division": self._get_team_division(team_id)
                })
            except KeyError as e:
                logger.error(f"Missing key in team data: {e}")
                logger.error(f"Available keys: {list(team.keys())}")
                raise
        
        return teams
    
    def get_players_with_stats(self, season: str) -> List[Dict[str, Any]]:
        """Get list of all NBA players with their stats for a given season.
        
        Args:
            season: Season in YYYY-YY format (e.g., "2023-24")
            
        Returns:
            List of player dictionaries containing player information and stats
        """
        endpoint = "leaguedashplayerstats"
        params = {
            "LastNGames": 0,
            "LeagueID": "00",
            "MeasureType": "Base",
            "Month": 0,
            "OpponentTeamID": 0,
            "PaceAdjust": "N",
            "PerMode": "PerGame",
            "Period": 0,
            "PlusMinus": "N",
            "Rank": "N",
            "Season": season,
            "SeasonType": "Regular Season",
            "TeamID": 0
        }
        
        response = self.make_request(endpoint, params)
        
        players = []
        if not response or 'resultSets' not in response:
            return players
            
        result_set = response['resultSets'][0]
        headers = result_set.get('headers', [])
        rows = result_set.get('rowSet', [])
        
        for row in rows:
            player_dict = dict(zip(headers, row))
            players.append({
                'playerId': player_dict.get('PLAYER_ID'),
                'playerName': player_dict.get('PLAYER_NAME'),
                'teamId': player_dict.get('TEAM_ID'),
                'position': player_dict.get('POSITION'),
                'stats': {
                    'gamesPlayed': player_dict.get('GP'),
                    'gamesStarted': player_dict.get('GS', 0),
                    'minutes': player_dict.get('MIN'),
                    'fgm': player_dict.get('FGM'),
                    'fga': player_dict.get('FGA'),
                    'fgPct': player_dict.get('FG_PCT'),
                    'fg3m': player_dict.get('FG3M'),
                    'fg3a': player_dict.get('FG3A'),
                    'fg3Pct': player_dict.get('FG3_PCT'),
                    'ftm': player_dict.get('FTM'),
                    'fta': player_dict.get('FTA'),
                    'ftPct': player_dict.get('FT_PCT'),
                    'oreb': player_dict.get('OREB'),
                    'dreb': player_dict.get('DREB'),
                    'reb': player_dict.get('REB'),
                    'ast': player_dict.get('AST'),
                    'stl': player_dict.get('STL'),
                    'blk': player_dict.get('BLK'),
                    'tov': player_dict.get('TOV'),
                    'pf': player_dict.get('PF'),
                    'pts': player_dict.get('PTS'),
                    'plusMinus': player_dict.get('PLUS_MINUS')
                }
            })
        
        # Get additional player info
        for player in players:
            try:
                player_info = self.get_player_info(player['playerId'])
                if player_info:
                    player.update({
                        'birthDate': player_info.get('BIRTHDATE'),
                        'country': player_info.get('COUNTRY'),
                        'height': player_info.get('HEIGHT'),
                        'weight': player_info.get('WEIGHT'),
                        'jerseyNumber': player_info.get('JERSEY')
                    })
            except Exception as e:
                logger.warning(f"Could not fetch additional info for player {player['playerName']}: {e}")
        
        return players
    
    def get_player_info(self, player_id: int) -> Dict[str, Any]:
        """Get detailed information for a specific player.
        
        Args:
            player_id: NBA player ID
            
        Returns:
            Dictionary containing player information
        """
        endpoint = "commonplayerinfo"
        params = {
            "PlayerID": player_id,
            "LeagueID": "00"
        }
        
        response = self.make_request(endpoint, params)
        
        if not response or 'resultSets' not in response:
            return {}
            
        result_set = response['resultSets'][0]
        if not result_set or 'rowSet' not in result_set or not result_set['rowSet']:
            return {}
            
        headers = result_set['headers']
        row = result_set['rowSet'][0]
        
        return dict(zip(headers, row))
    
    def get_team_info(self) -> Dict[str, Any]:
        """Get team information."""
        params = {
            "LeagueID": "00",
            "Season": "2023-24",
            "SeasonType": "Regular Season",
            "MeasureType": "Base",
            "PerMode": "PerGame",
            "PlusMinus": "N",
            "PaceAdjust": "N",
            "Rank": "N",
            "LastNGames": 0,
            "TeamID": 0,
            "Location": "",
            "Outcome": "",
            "SeasonSegment": "",
            "DateFrom": "",
            "DateTo": "",
            "OpponentTeamID": 0,
            "VsConference": "",
            "VsDivision": "",
            "GameSegment": "",
            "Period": 0,
            "ShotClockRange": ""
        }
        
        return self.make_request("teamdashboardbygeneralsplits", params)
        
    def _get_team_conference(self, team_id):
        """Returns the conference for a given team ID."""
        # Conference mapping based on 2023-24 season
        eastern_conference = {1610612737, 1610612738, 1610612751, 1610612766, 1610612748,
                            1610612752, 1610612765, 1610612754, 1610612749, 1610612755,
                            1610612739, 1610612753, 1610612764, 1610612761, 1610612741}
        return 'Eastern' if team_id in eastern_conference else 'Western'
        
    def _get_team_division(self, team_id):
        """Returns the division for a given team ID."""
        # Division mapping based on 2023-24 season
        division_map = {
            # Atlantic
            1610612738: 'Atlantic',  # Celtics
            1610612751: 'Atlantic',  # Nets
            1610612752: 'Atlantic',  # Knicks
            1610612755: 'Atlantic',  # 76ers
            1610612761: 'Atlantic',  # Raptors
            # Central
            1610612741: 'Central',   # Bulls
            1610612739: 'Central',   # Cavaliers
            1610612765: 'Central',   # Pistons
            1610612754: 'Central',   # Pacers
            1610612749: 'Central',   # Bucks
            # Southeast
            1610612737: 'Southeast',  # Hawks
            1610612766: 'Southeast',  # Hornets
            1610612748: 'Southeast',  # Heat
            1610612753: 'Southeast',  # Magic
            1610612764: 'Southeast',  # Wizards
            # Northwest
            1610612743: 'Northwest',  # Nuggets
            1610612750: 'Northwest',  # Timberwolves
            1610612760: 'Northwest',  # Thunder
            1610612757: 'Northwest',  # Trail Blazers
            1610612762: 'Northwest',  # Jazz
            # Pacific
            1610612744: 'Pacific',    # Warriors
            1610612746: 'Pacific',    # Clippers
            1610612747: 'Pacific',    # Lakers
            1610612756: 'Pacific',    # Suns
            1610612758: 'Pacific',    # Kings
            # Southwest
            1610612742: 'Southwest',  # Mavericks
            1610612745: 'Southwest',  # Rockets
            1610612763: 'Southwest',  # Grizzlies
            1610612740: 'Southwest',  # Pelicans
            1610612759: 'Southwest',  # Spurs
        }
        return division_map.get(team_id, 'Unknown')
    
    def get_all_players(self, season: str, is_only_current_season: str = "1") -> Optional[Dict[str, Any]]:
        """
        Get all players for a given season.
        
        Args:
            season: The NBA season in YYYY-YY format (e.g., "2024-25")
            is_only_current_season: Flag to get only current season players ("1" for yes, "0" for no)
            
        Returns:
            Dict containing player data or None if the request failed
        """
        endpoint = "commonallplayers"
        params = {
            "LeagueID": "00",
            "Season": season,
            "IsOnlyCurrentSeason": is_only_current_season
        }
        return self.make_request(endpoint, params)
    
    def get_league_player_tracking_stats(
        self,
        season: str,
        per_mode: str = "PerGame",
        player_or_team: str = "Player",
        pt_measure_type: str = "SpeedDistance", # Example, will be changed in fetcher
        season_type: str = "Regular Season",
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Fetch league-wide player tracking statistics.

        Args:
            season: Season in YYYY-YY format (e.g., "2023-24")
            per_mode: Mode for stats ("PerGame", "Totals")
            player_or_team: Fetch stats for "Player" or "Team"
            pt_measure_type: Tracking measure type (e.g., "SpeedDistance", "Rebounding", 
                               "Possessions", "CatchShoot", "PullUpShot", "Defense", 
                               "Driving", "ElbowTouch", "PostTouch", "PaintTouch", "Passing")
            season_type: Type of season ("Regular Season", "Playoffs", etc.)
            **kwargs: Additional parameters for the endpoint

        Returns:
            Dictionary containing the API response or None if failed.
        """
        endpoint = "/leaguedashptstats"
        params = {
            "College": "",
            "Conference": "",
            "Country": "",
            "DateFrom": "", # Explicitly empty
            "DateTo": "", # Explicitly empty
            "Division": "",
            "DraftPick": "",
            "DraftYear": "",
            "GameScope": "",
            "Height": "",
            "LastNGames": 0,
            "LeagueID": "00", # Already default but good to be explicit
            "Location": "",
            "Month": 0,
            "OpponentTeamID": 0,
            "Outcome": "",
            "PORound": 0, # Often required, setting to 0 for all regular season games
            "PerMode": per_mode,
            "PlayerExperience": "",
            "PlayerOrTeam": player_or_team,
            "PlayerPosition": "",
            "PtMeasureType": pt_measure_type,
            "Season": season,
            "SeasonSegment": "", # Explicitly empty
            "SeasonType": season_type, # Explicitly set
            "StarterBench": "",
            "TeamID": 0,
            "VsConference": "",
            "VsDivision": "",
            "Weight": "",
            **kwargs
        }
        
        # Filter out parameters with empty string values, as stats.nba.com can be sensitive to them
        final_params = {k: v for k, v in params.items() if v != ""}
        
        logger.info(f"Fetching league player tracking stats: Season={season}, Type={pt_measure_type}, Mode={per_mode}, PlayerOrTeam={player_or_team}")
        # Use final_params for the request
        return self.make_request(endpoint, final_params)

    def get_shot_chart_detail(
        self,
        player_id: int,
        team_id: int, # Team ID is required for shotchartdetail
        season: str,
        season_type: str = "Regular Season",
        context_measure: str = "FGA" # Can be FGA, PTS, etc.
    ) -> Optional[Dict[str, Any]]:
        """
        Get shot chart details for a player.

        Args:
            player_id: NBA player ID
            team_id: NBA team ID for the player during the season/game
            season: Season ID (e.g., "2023-24")
            season_type: Type of season ("Regular Season", "Playoffs")
            context_measure: The measure for the shot chart (FGA, FG_PCT, etc.)

        Returns:
            Optional[Dict[str, Any]]: Shot chart data or None if request fails
        """
        endpoint = "/shotchartdetail"
        params = {
            "PlayerID": player_id,
            "TeamID": team_id,
            "Season": season,
            "SeasonType": season_type,
            "LeagueID": "00",
            "ContextMeasure": context_measure,
            "DateFrom": "",
            "DateTo": "",
            "GameID": "",
            "GameSegment": "",
            "LastNGames": 0,
            "Location": "",
            "Month": 0,
            "OpponentTeamID": 0,
            "Outcome": "",
            "Period": 0,
            "PlayerPosition": "",
            "Position": "", # Note: PlayerPosition vs Position, API might use one or the other or both
            "RookieYear": "",
            "SeasonSegment": "",
            "VsConference": "",
            "VsDivision": ""
        }
        # Clean out empty string params as stats.nba.com can be sensitive
        final_params = {k: v for k, v in params.items() if v != ""}
        return self.make_request(endpoint, final_params)

    def get_player_pass_stats(
        self,
        player_id: int,
        season: str,
        per_mode: str = "PerGame", # Or "Totals"
        season_type: str = "Regular Season"
    ) -> Optional[Dict[str, Any]]:
        """Fetch player passing and ball-handling stats (touches, time of possession, etc.)."""
        endpoint = "/playerdashptpass"
        params = {
            "PlayerID": player_id,
            "Season": season,
            "PerMode": per_mode,
            "SeasonType": season_type,
            "LeagueID": "00",
            "DateFrom": "",
            "DateTo": "",
            "GameSegment": "",
            "LastNGames": 0,
            "Location": "",
            "Month": 0,
            "OpponentTeamID": 0,
            "Outcome": "",
            "Period": 0,
            "SeasonSegment": "",
            "VsConference": "",
            "VsDivision": "",
            "TeamID": 0 # Often 0 for player-specific, but API might require it if player played for multiple teams
        }
        final_params = {k: v for k, v in params.items() if v != ""}
        return self.make_request(endpoint, final_params)

    def get_player_elbow_touch_stats(
        self,
        player_id: int,
        season: str,
        per_mode: str = "PerGame",
        season_type: str = "Regular Season"
    ) -> Optional[Dict[str, Any]]:
        """Fetch player elbow touch stats."""
        endpoint = "/playerdashptelbowtouch" # Placeholder, verify actual endpoint
        # Parameters for these tracking dashboards are often very similar
        params = {
            "PlayerID": player_id,
            "Season": season,
            "PerMode": per_mode,
            "SeasonType": season_type,
            "LeagueID": "00",
            "DateFrom": "",
            "DateTo": "",
            "GameSegment": "",
            "LastNGames": 0,
            "Location": "",
            "Month": 0,
            "OpponentTeamID": 0,
            "Outcome": "",
            "Period": 0,
            "SeasonSegment": "",
            "VsConference": "",
            "VsDivision": "",
            "TeamID": 0
        }
        final_params = {k: v for k, v in params.items() if v != ""}
        return self.make_request(endpoint, final_params)

    def get_player_post_touch_stats(
        self,
        player_id: int,
        season: str,
        per_mode: str = "PerGame",
        season_type: str = "Regular Season"
    ) -> Optional[Dict[str, Any]]:
        """Fetch player post touch stats."""
        endpoint = "/playerdashptposttouch" # Placeholder, verify actual endpoint
        params = {
            "PlayerID": player_id,
            "Season": season,
            "PerMode": per_mode,
            "SeasonType": season_type,
            "LeagueID": "00",
            "DateFrom": "",
            "DateTo": "",
            "GameSegment": "",
            "LastNGames": 0,
            "Location": "",
            "Month": 0,
            "OpponentTeamID": 0,
            "Outcome": "",
            "Period": 0,
            "SeasonSegment": "",
            "VsConference": "",
            "VsDivision": "",
            "TeamID": 0
        }
        final_params = {k: v for k, v in params.items() if v != ""}
        return self.make_request(endpoint, final_params)

    def get_player_paint_touch_stats(
        self,
        player_id: int,
        season: str,
        per_mode: str = "PerGame",
        season_type: str = "Regular Season"
    ) -> Optional[Dict[str, Any]]:
        """Fetch player paint touch stats."""
        endpoint = "/playerdashptpainttouch" # Placeholder, verify actual endpoint
        params = {
            "PlayerID": player_id,
            "Season": season,
            "PerMode": per_mode,
            "SeasonType": season_type,
            "LeagueID": "00",
            "DateFrom": "",
            "DateTo": "",
            "GameSegment": "",
            "LastNGames": 0,
            "Location": "",
            "Month": 0,
            "OpponentTeamID": 0,
            "Outcome": "",
            "Period": 0,
            "SeasonSegment": "",
            "VsConference": "",
            "VsDivision": "",
            "TeamID": 0
        }
        final_params = {k: v for k, v in params.items() if v != ""}
        return self.make_request(endpoint, final_params)

    def get_player_drive_stats(
        self,
        player_id: int,
        season: str,
        per_mode: str = "PerGame",
        season_type: str = "Regular Season"
    ) -> Optional[Dict[str, Any]]:
        """Fetch player drive stats using the leaguedashptstats endpoint."""
        endpoint = "/leaguedashptstats" 
        params = {
            "PlayerID": player_id,
            "Season": season,
            "PerMode": per_mode,
            "SeasonType": season_type,
            "LeagueID": "00",
            "PlayerOrTeam": "Player", # Specify we want Player stats
            "PtMeasureType": "Drives", # Specify the tracking measure type
            "DateFrom": "",
            "DateTo": "",
            "GameScope": "",
            "LastNGames": 0,
            "Location": "",
            "Month": 0,
            "OpponentTeamID": 0,
            "Outcome": "",
            "TeamID": 0, # Should be 0 when PlayerID is specified for a specific player
            "VsConference": "",
            "VsDivision": "",
            "Conference": "",
            "Division": "",
            "GameSegment": "",
            "Period": 0,
            "ShotClockRange": "",
            "PlayerExperience": "",
            "PlayerPosition": "",
            "StarterBench": "",
            "DraftYear": "",
            "DraftPick": "",
            "College": "",
            "Country": "",
            "Height": "",
            "Weight": ""
        }
        final_params = {k: v for k, v in params.items() if v != ""}
        return self.make_request(endpoint, final_params)

    def get_player_catch_shoot_stats(
        self,
        player_id: int,
        season: str,
        per_mode: str = "PerGame",
        season_type: str = "Regular Season"
    ) -> Optional[Dict[str, Any]]:
        """Fetch player catch and shoot stats."""
        endpoint = "/playerdashptcatchshoot" # Placeholder, verify actual endpoint
        params = {
            "PlayerID": player_id,
            "Season": season,
            "PerMode": per_mode,
            "SeasonType": season_type,
            "LeagueID": "00",
            "DateFrom": "",
            "DateTo": "",
            "GameSegment": "",
            "LastNGames": 0,
            "Location": "",
            "Month": 0,
            "OpponentTeamID": 0,
            "Outcome": "",
            "Period": 0,
            "SeasonSegment": "",
            "VsConference": "",
            "VsDivision": "",
            "TeamID": 0
        }
        final_params = {k: v for k, v in params.items() if v != ""}
        return self.make_request(endpoint, final_params)

    def get_player_pull_up_stats(
        self,
        player_id: int,
        season: str,
        per_mode: str = "PerGame",
        season_type: str = "Regular Season"
    ) -> Optional[Dict[str, Any]]:
        """Fetch player pull up shot stats."""
        endpoint = "/playerdashptpullup" # Placeholder, verify actual endpoint
        params = {
            "PlayerID": player_id,
            "Season": season,
            "PerMode": per_mode,
            "SeasonType": season_type,
            "LeagueID": "00",
            "DateFrom": "",
            "DateTo": "",
            "GameSegment": "",
            "LastNGames": 0,
            "Location": "",
            "Month": 0,
            "OpponentTeamID": 0,
            "Outcome": "",
            "Period": 0,
            "SeasonSegment": "",
            "VsConference": "",
            "VsDivision": "",
            "TeamID": 0
        }
        final_params = {k: v for k, v in params.items() if v != ""}
        return self.make_request(endpoint, final_params)

    def get_player_opponent_stats(
        self,
        player_id: int,
        season: str,
        per_mode: str = "PerGame",
        season_type: str = "Regular Season"
    ) -> Optional[Dict[str, Any]]:
        """Fetch player stats split by opponent."""
        endpoint = "/playerdashboardbyopponent" 
        params = {
            "PlayerID": player_id,
            "Season": season,
            "PerMode": per_mode,
            "SeasonType": season_type,
            "LeagueID": "00",
            "DateFrom": "",
            "DateTo": "",
            "GameSegment": "",
            "LastNGames": 0,
            "Location": "",
            "Month": 0,
            "OpponentTeamID": 0, # This being 0 usually means all opponents, specific ID filters to one
            "Outcome": "",
            "Period": 0,
            "SeasonSegment": "",
            "VsConference": "",
            "VsDivision": ""
        }
        final_params = {k: v for k, v in params.items() if v != ""}
        return self.make_request(endpoint, final_params)

    def get_lineup_stats(
        self,
        season: str,
        per_mode: str = "Per100Possessions", # As per paper's likely need for rate stats
        measure_type: str = "Base", # Can also be "Advanced", "Four Factors", etc.
        season_type: str = "Regular Season",
        group_quantity: int = 5 # For 5-man lineups
    ) -> Optional[Dict[str, Any]]:
        """Fetch lineup statistics."""
        endpoint = "/leaguedashlineups"
        params = {
            "Season": season,
            "PerMode": per_mode,
            "MeasureType": measure_type,
            "SeasonType": season_type,
            "GroupQuantity": group_quantity,
            "LeagueID": "00",
            "DateFrom": "",
            "DateTo": "",
            "GameSegment": "",
            "LastNGames": 0,
            "Location": "",
            "Month": 0,
            "OpponentTeamID": 0,
            "Outcome": "",
            "PaceAdjust": "N", # Pace adjustment is often useful
            "Period": 0,
            "PlusMinus": "N",
            "Rank": "N",
            "SeasonSegment": "",
            "TeamID": 0, # 0 for all teams
            "VsConference": "",
            "VsDivision": ""
        }
        final_params = {k: v for k, v in params.items() if v != ""}
        return self.make_request(endpoint, final_params)

    def get_play_by_play(
        self,
        game_id: str,
        start_period: int = 0, # 0 for all periods
        end_period: int = 0   # 0 for all periods
    ) -> Optional[Dict[str, Any]]:
        """Fetch play-by-play data for a specific game."""
        # playbyplayv2 is common, playbyplayv3 is newer but might have different params/structure
        endpoint = "/playbyplayv2" 
        params = {
            "GameID": game_id,
            "StartPeriod": start_period,
            "EndPeriod": end_period,
            "LeagueID": "00" # Though often not strictly needed for game-specific endpoints if GameID is global
        }
        # PBP doesn't usually take as many filtering params as dashboards
        # Clean out 0s if the API prefers them absent (depends on specific endpoint)
        return self.make_request(endpoint, params)

    def get_league_hustle_stats(
        self,
        season: str,
        season_type: str = "Regular Season",
        per_mode: str = "PerGame"
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch league-wide hustle statistics for all players.

        Hustle stats include screen assists, deflections, loose balls, charges drawn,
        contested shots, and box outs.

        Args:
            season: Season ID (e.g., "2023-24")
            season_type: Type of season ("Regular Season", "Playoffs")
            per_mode: Mode for stats ("PerGame", "Totals", "Per36Minutes", etc.)

        Returns:
            Optional[Dict[str, Any]]: API response containing hustle stats or None if request fails.
        """
        endpoint = "/leaguehustlestatsplayer" # Note: 'player' not 'players'
        params = {
            "Season": season,
            "SeasonType": season_type,
            "PerMode": per_mode,
            "LeagueID": "00",
            # Common optional parameters, kept minimal for a league-wide fetch
            "College": "",
            "Conference": "",
            "Country": "",
            "DateFrom": "",
            "DateTo": "",
            "Division": "",
            "DraftPick": "",
            "DraftYear": "",
            "GameScope": "",
            "Height": "",
            "LastNGames": 0,
            "Location": "",
            "Month": 0,
            "OpponentTeamID": 0,
            "Outcome": "",
            "PORound": 0,
            "PlayerExperience": "",
            "PlayerPosition": "",
            "SeasonSegment": "",
            "StarterBench": "",
            "TeamID": 0, # 0 for all teams
            "VsConference": "",
            "VsDivision": "",
            "Weight": ""
        }
        # Clean out parameters with empty string values or 0 (unless it's a meaningful 0 like OpponentTeamID)
        final_params = {k: v for k, v in params.items() if v != "" and (isinstance(v, str) or v != 0 or k in ["LeagueID", "OpponentTeamID", "TeamID", "Month", "LastNGames", "PORound"])} # keep meaningful 0s
        logger.info(f"Fetching league hustle stats: Season={season}, Type={season_type}, Mode={per_mode}")
        return self.make_request(endpoint, final_params) 

    def get_player_opponent_shooting_stats(
        self,
        season: str,
        per_mode: str = "PerGame",
        season_type: str = "Regular Season"
    ) -> Optional[Dict[str, Any]]:
        """
        Fetches opponent shooting statistics for players, league-wide.
        Data is from the leaguedashplayershotlocations endpoint with MeasureType="Opponent".
        """
        endpoint = "leaguedashplayershotlocations"
        params = {
            "MeasureType": "Opponent",
            "PerMode": per_mode,
            "Season": season,
            "SeasonType": season_type,
            "PlayerOrTeam": "Player",
            "DistanceRange": "By Zone",
            "LeagueID": "00",
            "PaceAdjust": "N",
            "PlusMinus": "N",
            "Rank": "N",
            "LastNGames": 0,
            "Month": 0,
            "OpponentTeamID": 0,
            "Period": 0,
            "TeamID": 0,
            "PORound": 0
        }
        
        logger.info(f"Fetching league-wide opponent shooting locations for Season {season} with simplified params.")
        return self.make_request(endpoint, params)

    def get_league_player_advanced_stats(self, season: str, season_type: str = "Regular Season") -> Optional[Dict[str, Any]]:
        """
        Get league-wide advanced player stats for a given season.

        Args:
            season: Season in YYYY-YY format (e.g., "2023-24")
            season_type: Type of season ("Regular Season", "Playoffs", etc.)

        Returns:
            Optional[Dict[str, Any]]: API response containing advanced player stats or None if request fails.
        """
        endpoint = "leaguedashplayerstats"
        params = {
            "MeasureType": "Advanced",
            "PerMode": "PerGame",
            "PlusMinus": "N",
            "PaceAdjust": "N",
            "Rank": "N",
            "Season": season,
            "SeasonType": season_type,
            "LastNGames": 0,
            "Month": 0,
            "OpponentTeamID": 0,
            "Period": 0,
            "SeasonSegment": "",
            "Conference": "",
            "Division": "",
            "GameSegment": "",
            "DateFrom": "",
            "DateTo": "",
            "Location": "",
            "Outcome": "",
            "PORound": 0,
            "TeamID": 0,
            "VsConference": "",
            "VsDivision": "",
            "College": "",
            "Country": "",
            "DraftPick": "",
            "DraftYear": "",
            "GameScope": "",
            "Height": "",
            "ISTRound": "",
            "PlayerExperience": "",
            "PlayerPosition": "",
            "ShotClockRange": "",
            "StarterBench": "",
            "Weight": "",
            "LeagueID": "00",
        }
        
        logger.info(f"Fetching league advanced player stats for season {season}")
        return self.make_request(endpoint, params) 

    def get_league_player_shot_locations(
        self,
        season: str,
        season_type: str = "Regular Season",
        distance_range: str = "By Zone"
    ) -> Optional[Dict[str, Any]]:
        """
        Fetches league-wide player shot locations, aggregated by distance/zone.

        Args:
            season: Season in YYYY-YY format.
            season_type: Type of season.
            distance_range: The distance range aggregation. "By Zone" is a common value.

        Returns:
            API response containing shot location data or None if request fails.
        """
        endpoint = "leaguedashplayershotlocations"
        params = {
            "MeasureType": "Base",
            "PerMode": "PerGame",
            "PlusMinus": "N",
            "PaceAdjust": "N",
            "Rank": "N",
            "Season": season,
            "SeasonType": season_type,
            "DistanceRange": distance_range,
            "LeagueID": "00",
            "TeamID": 0,
            "PlayerOrTeam": "Player",
            # Comprehensive list of parameters
            "College": "", "Conference": "", "Country": "", "DateFrom": "", "DateTo": "",
            "Division": "", "DraftPick": "", "DraftYear": "", "GameScope": "", "GameSegment": "",
            "Height": "", "ISTRound": "", "LastNGames": 0, "Location": "", "Month": 0,
            "OpponentTeamID": 0, "Outcome": "", "PORound": 0, "Period": 0, "PlayerExperience": "",
            "PlayerPosition": "", "SeasonSegment": "", "ShotClockRange": "", "StarterBench": "",
            "VsConference": "", "VsDivision": "", "Weight": ""
        }
        logger.info(f"Fetching league-wide player shot locations for Season {season}, DistanceRange '{distance_range}'")
        return self.make_request(endpoint, params) 

    def get_draft_combine_stats(self, season_year: str) -> Optional[Dict[str, Any]]:
        """
        Fetches draft combine stats for a given season.
        This corresponds to the 'draftcombinestats' endpoint.

        Args:
            season_year: The season year of the draft combine (e.g., "2023-24").
        
        Returns:
            A dictionary containing the draft combine stats.
        """
        endpoint = "draftcombinestats"
        params = {
            "LeagueID": "00",
            "SeasonYear": season_year
        }
        return self.make_request(endpoint, params) 