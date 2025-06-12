"""Player model for NBA stats application."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any

class Player(BaseModel):
    """Represents an NBA player and their statistics, validated with Pydantic."""
    model_config = ConfigDict(
        anystr_strip_whitespace=True,
        populate_by_name=True,
        extra='ignore'
    )

    player_id: int = Field(..., alias='PERSON_ID')
    player_name: str = Field(..., alias='DISPLAY_FIRST_LAST')
    team_id: int = Field(..., alias='TEAM_ID')
    position: Optional[str] = Field(None, alias='POSITION')
    birth_date: Optional[str] = Field(None, alias='BIRTH_DATE')
    season_id: str
    minutes_played: Optional[float] = Field(None, alias='MIN')
    
    # Basic Stats
    field_goal_percentage: Optional[float] = Field(None, alias='FG_PCT')
    three_point_percentage: Optional[float] = Field(None, alias='FG3_PCT')
    free_throw_percentage: Optional[float] = Field(None, alias='FT_PCT')
    rebounds: Optional[float] = Field(None, alias='REB')
    assists: Optional[float] = Field(None, alias='AST')
    steals: Optional[float] = Field(None, alias='STL')
    blocks: Optional[float] = Field(None, alias='BLK')
    points: Optional[float] = Field(None, alias='PTS')
    plus_minus: Optional[float] = Field(None, alias='PLUS_MINUS')
    
    # Advanced Stats
    usage_rate: Optional[float] = Field(None, alias='USG_PCT')
    player_efficiency_rating: Optional[float] = Field(None, alias='PIE')
    true_shooting_percentage: Optional[float] = Field(None, alias='TS_PCT')
    win_shares: Optional[float] = Field(None, alias='W_PCT') # Using W_PCT as a proxy for win shares
    box_plus_minus: Optional[float] = None
    value_over_replacement: Optional[float] = None
    
    # Physical Attributes
    height: Optional[str] = Field(None, alias='HEIGHT')
    weight: Optional[str] = Field(None, alias='WEIGHT')
    wingspan: Optional[float] = None
    
    # Tracking Stats
    average_speed: Optional[float] = Field(None, alias='AVG_SPEED')
    distance_covered: Optional[float] = Field(None, alias='DIST')
    average_speed_offense: Optional[float] = Field(None, alias='AVG_SPEED_OFF')
    average_speed_defense: Optional[float] = Field(None, alias='AVG_SPEED_DEF')
    
    # Defensive Stats
    defensive_rating: Optional[float] = Field(None, alias='DEF_RATING')
    defensive_win_shares: Optional[float] = Field(None, alias='D_W_PCT') # Using D_W_PCT as a proxy
    defensive_box_plus_minus: Optional[float] = None
    opponent_field_goal_percentage: Optional[float] = Field(None, alias='OPP_FG_PCT')
    opponent_three_point_percentage: Optional[float] = Field(None, alias='OPP_FG3_PCT')
    
    # Shot Location Stats
    shot_attempts_0_3: Optional[float] = Field(None, alias='FGA_0_3')
    shot_makes_0_3: Optional[float] = Field(None, alias='FGM_0_3')
    shot_attempts_3_10: Optional[float] = Field(None, alias='FGA_3_10')
    shot_makes_3_10: Optional[float] = Field(None, alias='FGM_3_10')
    shot_attempts_10_16: Optional[float] = Field(None, alias='FGA_10_16')
    shot_makes_10_16: Optional[float] = Field(None, alias='FGM_10_16')
    shot_attempts_16_3pt: Optional[float] = Field(None, alias='FGA_16_3PT')
    shot_makes_16_3pt: Optional[float] = Field(None, alias='FGM_16_3PT')
    shot_attempts_3pt: Optional[float] = Field(None, alias='FG3A')
    shot_makes_3pt: Optional[float] = Field(None, alias='FG3M')
    
    # Play Type Stats
    isolation_frequency: Optional[float] = Field(None, alias='ISO_FREQ')
    isolation_points_per_play: Optional[float] = Field(None, alias='ISO_PPP')
    pick_and_roll_frequency: Optional[float] = Field(None, alias='PNR_FREQ')
    pick_and_roll_points_per_play: Optional[float] = Field(None, alias='PNR_PPP')
    post_up_frequency: Optional[float] = Field(None, alias='POST_UP_FREQ')
    post_up_points_per_play: Optional[float] = Field(None, alias='POST_UP_PPP')
    spot_up_frequency: Optional[float] = Field(None, alias='SPOT_UP_FREQ')
    spot_up_points_per_play: Optional[float] = Field(None, alias='SPOT_UP_PPP')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Player':
        """Create a Player instance from a dictionary of data."""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Player instance to a dictionary."""
        return {k: v for k, v in self.__dict__.items() if v is not None} 