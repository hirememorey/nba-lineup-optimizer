"""NBA Stats API client."""

import time
import random
import logging
import requests
from typing import Dict, Any, Optional
from ..config.settings import (
    API_BASE_URL,
    ENDPOINTS,
    MAX_RETRIES,
    API_TIMEOUT,
    MIN_SLEEP,
    MAX_SLEEP,
    RETRY_BACKOFF_BASE,
    RETRY_BACKOFF_FACTOR,
    MAX_BACKOFF_SLEEP,
    BASE_HEADERS,
    USER_AGENTS
)

class NBAStatsClient:
    """Client for making requests to the NBA Stats API."""
    
    def __init__(self):
        """Initialize the NBA Stats API client."""
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Host": "stats.nba.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Connection": "keep-alive",
            "x-nba-stats-origin": "stats",
            "x-nba-stats-token": "true",
            "Referer": "https://www.nba.com/",
            "Origin": "https://www.nba.com",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        })
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API request with random user agent."""
        headers = self.session.headers.copy()
        headers["User-Agent"] = random.choice(USER_AGENTS)
        return headers
    
    def _handle_rate_limit(self, response: requests.Response) -> None:
        """Handle rate limiting by waiting for the specified time."""
        if response.status_code == 429:  # Too Many Requests
            retry_after = int(response.headers.get("Retry-After", 30))
            logging.warning(f"Rate limited. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
    
    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff time."""
        backoff = min(
            RETRY_BACKOFF_BASE * (RETRY_BACKOFF_FACTOR ** attempt),
            MAX_BACKOFF_SLEEP
        )
        return backoff + random.uniform(MIN_SLEEP, MAX_SLEEP)
    
    def make_request(
        self,
        endpoint: str,
        params: Dict[str, Any],
        max_retries: int = MAX_RETRIES
    ) -> Optional[Dict[str, Any]]:
        """Make a request to the NBA Stats API with retries and backoff.
        
        Args:
            endpoint: API endpoint to call
            params: Query parameters for the request
            max_retries: Maximum number of retry attempts
            
        Returns:
            Optional[Dict[str, Any]]: JSON response data or None if request fails
            
        Raises:
            requests.exceptions.RequestException: If all retry attempts fail
        """
        url = f"{API_BASE_URL}{endpoint}"
        
        for attempt in range(max_retries):
            try:
                # Add random delay between requests
                time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
                
                response = self.session.get(
                    url,
                    params=params,
                    headers=self._get_headers(),
                    timeout=API_TIMEOUT
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    self._handle_rate_limit(response)
                    continue
                else:
                    logging.error(
                        f"API request failed with status {response.status_code}"
                    )
                    
                # Calculate and apply backoff
                if attempt < max_retries - 1:
                    backoff = self._calculate_backoff(attempt)
                    logging.warning(f"Retrying in {backoff:.2f} seconds...")
                    time.sleep(backoff)
                    
            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed: {e}")
                if attempt < max_retries - 1:
                    backoff = self._calculate_backoff(attempt)
                    logging.warning(f"Retrying in {backoff:.2f} seconds...")
                    time.sleep(backoff)
                else:
                    raise
        
        return None
    
    def get_player_stats(
        self,
        player_id: int,
        season: str,
        season_type: str = "Regular Season"
    ) -> Optional[Dict[str, Any]]:
        """Get player statistics.
        
        Args:
            player_id: NBA player ID
            season: Season ID (e.g., "2024-25")
            season_type: Type of season (Regular Season, Playoffs, etc.)
            
        Returns:
            Optional[Dict[str, Any]]: Player statistics or None if request fails
        """
        params = {
            "PlayerID": player_id,
            "Season": season,
            "SeasonType": season_type,
            "LeagueID": "00",
            "PerMode": "PerGame"
        }
        
        return self.make_request(ENDPOINTS["player_stats"], params)
    
    def get_player_advanced_stats(
        self,
        player_id: int,
        season: str,
        season_type: str = "Regular Season"
    ) -> Optional[Dict[str, Any]]:
        """Get player advanced statistics.
        
        Args:
            player_id: NBA player ID
            season: Season ID (e.g., "2024-25")
            season_type: Type of season (Regular Season, Playoffs, etc.)
            
        Returns:
            Optional[Dict[str, Any]]: Player advanced statistics or None if request fails
        """
        params = {
            "PlayerID": player_id,
            "Season": season,
            "SeasonType": season_type,
            "LeagueID": "00",
            "PerMode": "PerGame",
            "MeasureType": "Advanced"
        }
        
        return self.make_request(ENDPOINTS["player_advanced"], params)
    
    def get_player_tracking_stats(
        self,
        player_id: int,
        season: str,
        season_type: str = "Regular Season"
    ) -> Optional[Dict[str, Any]]:
        """Get player tracking statistics.
        
        Args:
            player_id: NBA player ID
            season: Season ID (e.g., "2024-25")
            season_type: Type of season (Regular Season, Playoffs, etc.)
            
        Returns:
            Optional[Dict[str, Any]]: Player tracking statistics or None if request fails
        """
        params = {
            "PlayerID": player_id,
            "Season": season,
            "SeasonType": season_type,
            "LeagueID": "00",
            "PerMode": "PerGame"
        }
        
        return self.make_request(ENDPOINTS["player_tracking"], params)
    
    def get_player_shooting_splits(
        self,
        player_id: int,
        season: str,
        season_type: str = "Regular Season"
    ) -> Optional[Dict[str, Any]]:
        """Get player shooting splits by distance.
        
        Args:
            player_id: NBA player ID
            season: Season ID (e.g., "2024-25")
            season_type: Type of season (Regular Season, Playoffs, etc.)
            
        Returns:
            Optional[Dict[str, Any]]: Player shooting splits or None if request fails
        """
        params = {
            "PlayerID": player_id,
            "Season": season,
            "SeasonType": season_type,
            "LeagueID": "00",
            "PerMode": "PerGame"
        }
        
        return self.make_request(ENDPOINTS["shooting_splits"], params) 