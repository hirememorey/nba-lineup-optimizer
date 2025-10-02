"""
Database Data Transfer Objects (DTOs)

This module defines Pydantic models that represent the exact schema of database tables.
These DTOs serve as the "sacred schema" contract between data processing and persistence layers.
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PlayerSeasonRawStatsDTO(BaseModel):
    """Data Transfer Object for PlayerSeasonRawStats table."""
    
    # Primary key components
    player_id: int = Field(..., description="NBA player ID")
    season: str = Field(..., description="Season identifier (e.g., '2024-25')")
    team_id: int = Field(..., description="NBA team ID")
    
    # Basic stats
    games_played: Optional[int] = Field(None, description="Games played")
    games_started: Optional[int] = Field(None, description="Games started")
    minutes_played: Optional[float] = Field(None, description="Minutes played")
    
    # Shooting stats
    field_goals_made: Optional[int] = Field(None, description="Field goals made")
    field_goals_attempted: Optional[int] = Field(None, description="Field goals attempted")
    field_goal_percentage: Optional[float] = Field(None, description="Field goal percentage")
    three_pointers_made: Optional[int] = Field(None, description="Three pointers made")
    three_pointers_attempted: Optional[int] = Field(None, description="Three pointers attempted")
    three_point_percentage: Optional[float] = Field(None, description="Three point percentage")
    free_throws_made: Optional[int] = Field(None, description="Free throws made")
    free_throws_attempted: Optional[int] = Field(None, description="Free throws attempted")
    free_throw_percentage: Optional[float] = Field(None, description="Free throw percentage")
    
    # Rebounding stats
    offensive_rebounds: Optional[int] = Field(None, description="Offensive rebounds")
    defensive_rebounds: Optional[int] = Field(None, description="Defensive rebounds")
    total_rebounds: Optional[int] = Field(None, description="Total rebounds")
    
    # Other stats
    assists: Optional[int] = Field(None, description="Assists")
    steals: Optional[int] = Field(None, description="Steals")
    blocks: Optional[int] = Field(None, description="Blocks")
    turnovers: Optional[int] = Field(None, description="Turnovers")
    personal_fouls: Optional[int] = Field(None, description="Personal fouls")
    points: Optional[int] = Field(None, description="Points")
    plus_minus: Optional[float] = Field(None, description="Plus/minus")
    
    # Advanced metrics
    avg_shot_distance: Optional[float] = Field(None, description="Average shot distance")
    
    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Record creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Record update timestamp")
    
    model_config = {
        "validate_assignment": True,
        "use_enum_values": True
    }


class PlayerSeasonAdvancedStatsDTO(BaseModel):
    """Data Transfer Object for PlayerSeasonAdvancedStats table."""
    
    # Primary key components
    player_id: int = Field(..., description="NBA player ID")
    season: str = Field(..., description="Season identifier (e.g., '2024-25')")
    team_id: int = Field(..., description="NBA team ID")
    
    # Basic info
    age: Optional[int] = Field(None, description="Player age")
    games_played: Optional[int] = Field(None, description="Games played")
    wins: Optional[int] = Field(None, description="Team wins when player played")
    losses: Optional[int] = Field(None, description="Team losses when player played")
    win_percentage: Optional[float] = Field(None, description="Win percentage")
    minutes_played: Optional[float] = Field(None, description="Minutes played")
    
    # Rating stats
    offensive_rating: Optional[float] = Field(None, description="Offensive rating")
    defensive_rating: Optional[float] = Field(None, description="Defensive rating")
    net_rating: Optional[float] = Field(None, description="Net rating")
    
    # Percentage stats
    assist_percentage: Optional[float] = Field(None, description="Assist percentage")
    assist_to_turnover_ratio: Optional[float] = Field(None, description="Assist to turnover ratio")
    assist_ratio: Optional[float] = Field(None, description="Assist ratio")
    offensive_rebound_percentage: Optional[float] = Field(None, description="Offensive rebound percentage")
    defensive_rebound_percentage: Optional[float] = Field(None, description="Defensive rebound percentage")
    rebound_percentage: Optional[float] = Field(None, description="Rebound percentage")
    turnover_percentage: Optional[float] = Field(None, description="Turnover percentage")
    effective_field_goal_percentage: Optional[float] = Field(None, description="Effective field goal percentage")
    true_shooting_percentage: Optional[float] = Field(None, description="True shooting percentage")
    usage_percentage: Optional[float] = Field(None, description="Usage percentage")
    
    # Pace and possessions
    pace: Optional[float] = Field(None, description="Pace")
    pie: Optional[float] = Field(None, description="Player Impact Estimate")
    possessions: Optional[int] = Field(None, description="Possessions")
    
    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Record creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Record update timestamp")
    
    model_config = {
        "validate_assignment": True,
        "use_enum_values": True
    }


class DatabaseWriteResult(BaseModel):
    """Result of a database write operation."""
    
    success: bool = Field(..., description="Whether the write operation succeeded")
    rows_affected: int = Field(..., description="Number of rows affected")
    error_message: Optional[str] = Field(None, description="Error message if operation failed")
    table_name: str = Field(..., description="Name of the table that was written to")
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
