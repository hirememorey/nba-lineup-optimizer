"""
Pydantic Models for NBA API Response Validation

This module defines Pydantic models for validating NBA API responses.
These models ensure data integrity at the system boundary and provide
clear error messages when the API structure changes.
"""

from typing import List, Optional, Any, Dict, Union
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)

class NBAAPIResultSet(BaseModel):
    """Model for a single result set in an NBA API response."""
    name: str
    headers: List[str]
    rowSet: List[List[Any]]
    
    @validator('rowSet')
    def validate_row_set(cls, v, values):
        """Validate that rowSet has consistent structure with headers."""
        if 'headers' in values:
            headers = values['headers']
            for i, row in enumerate(v):
                if len(row) != len(headers):
                    logger.warning(f"Row {i} has {len(row)} columns but headers has {len(headers)}")
        return v

class NBAAPIResponse(BaseModel):
    """Model for the complete NBA API response structure."""
    resource: str
    parameters: Dict[str, Any]
    resultSets: List[NBAAPIResultSet]
    
    @validator('resultSets')
    def validate_result_sets(cls, v):
        """Ensure we have at least one result set."""
        if not v:
            raise ValueError("API response must contain at least one result set")
        return v

class PlayerBasicStats(BaseModel):
    """Model for basic player statistics from leaguedashplayerstats."""
    PLAYER_ID: int
    PLAYER_NAME: str
    TEAM_ID: int
    TEAM_ABBREVIATION: str
    GP: int = Field(ge=0, description="Games played must be non-negative")
    GS: int = Field(ge=0, description="Games started must be non-negative")
    MIN: float = Field(ge=0, description="Minutes must be non-negative")
    FGM: float = Field(ge=0, description="Field goals made must be non-negative")
    FGA: float = Field(ge=0, description="Field goals attempted must be non-negative")
    FG_PCT: Optional[float] = Field(ge=0, le=1, description="Field goal percentage must be between 0 and 1")
    FG3M: float = Field(ge=0, description="3-pointers made must be non-negative")
    FG3A: float = Field(ge=0, description="3-pointers attempted must be non-negative")
    FG3_PCT: Optional[float] = Field(ge=0, le=1, description="3-point percentage must be between 0 and 1")
    FTM: float = Field(ge=0, description="Free throws made must be non-negative")
    FTA: float = Field(ge=0, description="Free throws attempted must be non-negative")
    FT_PCT: Optional[float] = Field(ge=0, le=1, description="Free throw percentage must be between 0 and 1")
    OREB: float = Field(ge=0, description="Offensive rebounds must be non-negative")
    DREB: float = Field(ge=0, description="Defensive rebounds must be non-negative")
    REB: float = Field(ge=0, description="Total rebounds must be non-negative")
    AST: float = Field(ge=0, description="Assists must be non-negative")
    STL: float = Field(ge=0, description="Steals must be non-negative")
    BLK: float = Field(ge=0, description="Blocks must be non-negative")
    TOV: float = Field(ge=0, description="Turnovers must be non-negative")
    PF: float = Field(ge=0, description="Personal fouls must be non-negative")
    PTS: float = Field(ge=0, description="Points must be non-negative")
    PLUS_MINUS: Optional[float] = None

class PlayerAdvancedStats(BaseModel):
    """Model for advanced player statistics."""
    PLAYER_ID: int
    PLAYER_NAME: str
    TEAM_ID: int
    TEAM_ABBREVIATION: str
    GP: int = Field(ge=0)
    W: int = Field(ge=0)
    L: int = Field(ge=0)
    W_PCT: Optional[float] = Field(ge=0, le=1)
    MIN: float = Field(ge=0)
    E_OFF_RATING: Optional[float] = None
    OFF_RATING: Optional[float] = None
    E_DEF_RATING: Optional[float] = None
    DEF_RATING: Optional[float] = None
    E_NET_RATING: Optional[float] = None
    NET_RATING: Optional[float] = None
    AST_PCT: Optional[float] = Field(ge=0, le=1)
    AST_TO: Optional[float] = Field(ge=0)
    AST_RATIO: Optional[float] = Field(ge=0)
    OREB_PCT: Optional[float] = Field(ge=0, le=1)
    DREB_PCT: Optional[float] = Field(ge=0, le=1)
    REB_PCT: Optional[float] = Field(ge=0, le=1)
    TM_TOV_PCT: Optional[float] = Field(ge=0, le=1)
    EFG_PCT: Optional[float] = Field(ge=0, le=1)
    TS_PCT: Optional[float] = Field(ge=0, le=1)
    USG_PCT: Optional[float] = Field(ge=0, le=1)
    PACE: Optional[float] = Field(ge=0)
    PIE: Optional[float] = Field(ge=0, le=1)

class PlayerTrackingStats(BaseModel):
    """Model for player tracking statistics."""
    PLAYER_ID: int
    PLAYER_NAME: str
    TEAM_ID: int
    TEAM_ABBREVIATION: str
    GP: int = Field(ge=0)
    W: int = Field(ge=0)
    L: int = Field(ge=0)
    W_PCT: Optional[float] = Field(ge=0, le=1)
    MIN: float = Field(ge=0)
    # Drive stats
    DRIVES: Optional[float] = Field(ge=0)
    DRIVE_FGM: Optional[float] = Field(ge=0)
    DRIVE_FGA: Optional[float] = Field(ge=0)
    DRIVE_FG_PCT: Optional[float] = Field(ge=0, le=1)
    DRIVE_PTS: Optional[float] = Field(ge=0)
    DRIVE_PASSES: Optional[float] = Field(ge=0)
    DRIVE_AST: Optional[float] = Field(ge=0)
    DRIVE_TOV: Optional[float] = Field(ge=0)
    DRIVE_PF: Optional[float] = Field(ge=0)

class PlayerHustleStats(BaseModel):
    """Model for player hustle statistics."""
    PLAYER_ID: int
    PLAYER_NAME: str
    TEAM_ID: int
    TEAM_ABBREVIATION: str
    GP: int = Field(ge=0)
    W: int = Field(ge=0)
    L: int = Field(ge=0)
    W_PCT: Optional[float] = Field(ge=0, le=1)
    MIN: float = Field(ge=0)
    SCREEN_ASSISTS: Optional[float] = Field(ge=0)
    SCREEN_AST_PTS: Optional[float] = Field(ge=0)
    DEFLECTIONS: Optional[float] = Field(ge=0)
    LOOSE_BALLS_RECOVERED: Optional[float] = Field(ge=0)
    CHARGES_DRAWN: Optional[float] = Field(ge=0)
    CONTESTED_SHOTS: Optional[float] = Field(ge=0)
    CONTESTED_SHOTS_2PT: Optional[float] = Field(ge=0)
    CONTESTED_SHOTS_3PT: Optional[float] = Field(ge=0)
    CONTESTED_SHOTS_AT_RIM: Optional[float] = Field(ge=0)
    DEF_BOXOUTS: Optional[float] = Field(ge=0)
    OFF_BOXOUTS: Optional[float] = Field(ge=0)
    BOX_OUT_PLUS_MINUS: Optional[float] = None

class PlayerInfo(BaseModel):
    """Model for basic player information."""
    PERSON_ID: int
    DISPLAY_FIRST_LAST: str
    DISPLAY_LAST_COMMA_FIRST: str
    DISPLAY_FI_LAST: str
    PLAYER_SLUG: Optional[str] = None
    BIRTHDATE: Optional[str] = None
    SCHOOL: Optional[str] = None
    COUNTRY: Optional[str] = None
    LAST_AFFILIATION: Optional[str] = None
    HEIGHT: Optional[str] = None
    WEIGHT: Optional[str] = None
    SEASON_EXP: Optional[int] = Field(ge=0)
    JERSEY: Optional[str] = None
    POSITION: Optional[str] = None
    ROSTERSTATUS: Optional[str] = None
    GAMES_PLAYED_CURRENT_SEASON_FLAG: Optional[str] = None
    TEAM_ID: Optional[int] = None
    TEAM_NAME: Optional[str] = None
    TEAM_ABBREVIATION: Optional[str] = None
    PLAYERCODE: Optional[str] = None
    FROM_YEAR: Optional[int] = None
    TO_YEAR: Optional[int] = None
    DLEAGUE_FLAG: Optional[str] = None
    NBA_FLAG: Optional[str] = None
    GAMES_PLAYED_FLAG: Optional[str] = None
    DRAFT_YEAR: Optional[str] = None
    DRAFT_ROUND: Optional[str] = None
    DRAFT_NUMBER: Optional[str] = None

class TeamInfo(BaseModel):
    """Model for team information."""
    TEAM_ID: int
    TEAM_NAME: str
    TEAM_ABBREVIATION: str
    TEAM_CODE: str
    W: int = Field(ge=0)
    L: int = Field(ge=0)
    PCT: Optional[float] = Field(ge=0, le=1)
    CONF_RANK: Optional[int] = Field(ge=1, le=15)
    DIV_RANK: Optional[int] = Field(ge=1, le=5)
    MIN_YEAR: Optional[str] = None
    MAX_YEAR: Optional[str] = None

class APIDataValidator:
    """
    Utility class for validating NBA API responses using Pydantic models.
    """
    
    def __init__(self):
        self.validation_errors = []
    
    def validate_response(self, response: Dict[str, Any], model_class: type = NBAAPIResponse) -> bool:
        """
        Validate an API response against a Pydantic model.
        
        Args:
            response: The API response dictionary
            model_class: The Pydantic model class to validate against
            
        Returns:
            True if validation passes, False otherwise
        """
        try:
            model_class(**response)
            return True
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            self.validation_errors.append(error_msg)
            logger.error(error_msg)
            return False
    
    def validate_player_stats(self, response: Dict[str, Any]) -> bool:
        """Validate player stats response."""
        if not self.validate_response(response, NBAAPIResponse):
            return False
        
        # Validate each player in the result set
        for result_set in response.get('resultSets', []):
            if result_set.get('name') == 'PlayerStats':
                headers = result_set.get('headers', [])
                rows = result_set.get('rowSet', [])
                
                for i, row in enumerate(rows):
                    try:
                        player_data = dict(zip(headers, row))
                        PlayerBasicStats(**player_data)
                    except Exception as e:
                        error_msg = f"Player stats validation error for row {i}: {str(e)}"
                        self.validation_errors.append(error_msg)
                        logger.error(error_msg)
                        return False
        
        return True
    
    def validate_advanced_stats(self, response: Dict[str, Any]) -> bool:
        """Validate advanced stats response."""
        if not self.validate_response(response, NBAAPIResponse):
            return False
        
        # Validate each player in the result set
        for result_set in response.get('resultSets', []):
            if result_set.get('name') == 'PlayerStats':
                headers = result_set.get('headers', [])
                rows = result_set.get('rowSet', [])
                
                for i, row in enumerate(rows):
                    try:
                        player_data = dict(zip(headers, row))
                        PlayerAdvancedStats(**player_data)
                    except Exception as e:
                        error_msg = f"Advanced stats validation error for row {i}: {str(e)}"
                        self.validation_errors.append(error_msg)
                        logger.error(error_msg)
                        return False
        
        return True
    
    def validate_tracking_stats(self, response: Dict[str, Any]) -> bool:
        """Validate tracking stats response."""
        if not self.validate_response(response, NBAAPIResponse):
            return False
        
        # Validate each player in the result set
        for result_set in response.get('resultSets', []):
            if result_set.get('name') == 'PlayerTrackingStats':
                headers = result_set.get('headers', [])
                rows = result_set.get('rowSet', [])
                
                for i, row in enumerate(rows):
                    try:
                        player_data = dict(zip(headers, row))
                        PlayerTrackingStats(**player_data)
                    except Exception as e:
                        error_msg = f"Tracking stats validation error for row {i}: {str(e)}"
                        self.validation_errors.append(error_msg)
                        logger.error(error_msg)
                        return False
        
        return True
    
    def validate_hustle_stats(self, response: Dict[str, Any]) -> bool:
        """Validate hustle stats response."""
        if not self.validate_response(response, NBAAPIResponse):
            return False
        
        # Validate each player in the result set
        for result_set in response.get('resultSets', []):
            if result_set.get('name') == 'HustleStatsPlayer':
                headers = result_set.get('headers', [])
                rows = result_set.get('rowSet', [])
                
                for i, row in enumerate(rows):
                    try:
                        player_data = dict(zip(headers, row))
                        PlayerHustleStats(**player_data)
                    except Exception as e:
                        error_msg = f"Hustle stats validation error for row {i}: {str(e)}"
                        self.validation_errors.append(error_msg)
                        logger.error(error_msg)
                        return False
        
        return True
    
    def validate_player_info(self, response: Dict[str, Any]) -> bool:
        """Validate player info response."""
        if not self.validate_response(response, NBAAPIResponse):
            return False
        
        # Validate each player in the result set
        for result_set in response.get('resultSets', []):
            if result_set.get('name') == 'CommonPlayerInfo':
                headers = result_set.get('headers', [])
                rows = result_set.get('rowSet', [])
                
                for i, row in enumerate(rows):
                    try:
                        player_data = dict(zip(headers, row))
                        PlayerInfo(**player_data)
                    except Exception as e:
                        error_msg = f"Player info validation error for row {i}: {str(e)}"
                        self.validation_errors.append(error_msg)
                        logger.error(error_msg)
                        return False
        
        return True
    
    def get_validation_errors(self) -> List[str]:
        """Get list of validation errors."""
        return self.validation_errors.copy()
    
    def clear_errors(self) -> None:
        """Clear validation errors."""
        self.validation_errors.clear()

# Create a global validator instance
api_validator = APIDataValidator()
