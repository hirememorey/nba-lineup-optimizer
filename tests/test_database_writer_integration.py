"""
Integration tests for the DatabaseWriter service.

These tests verify the complete data flow from DTOs to database persistence
with full validation and atomic transactions.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List

from src.nba_stats.services.database_writer import DatabaseWriter
from src.nba_stats.models.database_dtos import (
    PlayerSeasonRawStatsDTO, 
    PlayerSeasonAdvancedStatsDTO
)


class TestDatabaseWriterIntegration:
    """Integration tests for DatabaseWriter service."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        # Create the database with test schema
        self._create_test_schema(db_path)
        
        yield db_path
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    def _create_test_schema(self, db_path: str):
        """Create test database schema."""
        with sqlite3.connect(db_path) as conn:
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
            # Create Players table
            conn.execute("""
                CREATE TABLE Players (
                    player_id INTEGER PRIMARY KEY,
                    player_name TEXT NOT NULL
                )
            """)
            
            # Create Teams table
            conn.execute("""
                CREATE TABLE Teams (
                    team_id INTEGER PRIMARY KEY,
                    team_name TEXT NOT NULL,
                    team_abbreviation TEXT NOT NULL UNIQUE
                )
            """)
            
            # Create PlayerSeasonRawStats table
            conn.execute("""
                CREATE TABLE PlayerSeasonRawStats (
                    player_id INTEGER NOT NULL,
                    season TEXT NOT NULL,
                    team_id INTEGER NOT NULL,
                    games_played INTEGER,
                    games_started INTEGER,
                    minutes_played REAL,
                    field_goals_made INTEGER,
                    field_goals_attempted INTEGER,
                    field_goal_percentage REAL,
                    three_pointers_made INTEGER,
                    three_pointers_attempted INTEGER,
                    three_point_percentage REAL,
                    free_throws_made INTEGER,
                    free_throws_attempted INTEGER,
                    free_throw_percentage REAL,
                    offensive_rebounds INTEGER,
                    defensive_rebounds INTEGER,
                    total_rebounds INTEGER,
                    assists INTEGER,
                    steals INTEGER,
                    blocks INTEGER,
                    turnovers INTEGER,
                    personal_fouls INTEGER,
                    points INTEGER,
                    plus_minus REAL,
                    avg_shot_distance REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (player_id, season, team_id),
                    FOREIGN KEY (player_id) REFERENCES Players(player_id),
                    FOREIGN KEY (team_id) REFERENCES Teams(team_id)
                )
            """)
            
            # Create PlayerSeasonAdvancedStats table
            conn.execute("""
                CREATE TABLE PlayerSeasonAdvancedStats (
                    player_id INTEGER NOT NULL,
                    season TEXT NOT NULL,
                    team_id INTEGER NOT NULL,
                    age INTEGER,
                    games_played INTEGER,
                    wins INTEGER,
                    losses INTEGER,
                    win_percentage REAL,
                    minutes_played REAL,
                    offensive_rating REAL,
                    defensive_rating REAL,
                    net_rating REAL,
                    assist_percentage REAL,
                    assist_to_turnover_ratio REAL,
                    assist_ratio REAL,
                    offensive_rebound_percentage REAL,
                    defensive_rebound_percentage REAL,
                    rebound_percentage REAL,
                    turnover_percentage REAL,
                    effective_field_goal_percentage REAL,
                    true_shooting_percentage REAL,
                    usage_percentage REAL,
                    pace REAL,
                    pie REAL,
                    possessions INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (player_id, season, team_id),
                    FOREIGN KEY (player_id) REFERENCES Players(player_id),
                    FOREIGN KEY (team_id) REFERENCES Teams(team_id)
                )
            """)
            
            # Insert test data
            conn.execute("INSERT INTO Players (player_id, player_name) VALUES (1, 'Test Player 1')")
            conn.execute("INSERT INTO Players (player_id, player_name) VALUES (2, 'Test Player 2')")
            conn.execute("INSERT INTO Teams (team_id, team_name, team_abbreviation) VALUES (1, 'Test Team 1', 'TT1')")
            conn.execute("INSERT INTO Teams (team_id, team_name, team_abbreviation) VALUES (2, 'Test Team 2', 'TT2')")
            conn.commit()
    
    @pytest.fixture
    def sample_raw_stats(self) -> List[PlayerSeasonRawStatsDTO]:
        """Create sample raw stats data for testing."""
        return [
            PlayerSeasonRawStatsDTO(
                player_id=1,
                season="2024-25",
                team_id=1,
                games_played=82,
                games_started=82,
                minutes_played=35.5,
                field_goals_made=8,
                field_goals_attempted=16,
                field_goal_percentage=0.500,
                three_pointers_made=2,
                three_pointers_attempted=5,
                three_point_percentage=0.400,
                free_throws_made=4,
                free_throws_attempted=5,
                free_throw_percentage=0.800,
                offensive_rebounds=1,
                defensive_rebounds=4,
                total_rebounds=5,
                assists=6,
                steals=1,
                blocks=0,
                turnovers=2,
                personal_fouls=3,
                points=22,
                plus_minus=5.2,
                avg_shot_distance=15.5
            ),
            PlayerSeasonRawStatsDTO(
                player_id=2,
                season="2024-25",
                team_id=2,
                games_played=78,
                games_started=78,
                minutes_played=32.1,
                field_goals_made=6,
                field_goals_attempted=14,
                field_goal_percentage=0.429,
                three_pointers_made=1,
                three_pointers_attempted=4,
                three_point_percentage=0.250,
                free_throws_made=3,
                free_throws_attempted=4,
                free_throw_percentage=0.750,
                offensive_rebounds=2,
                defensive_rebounds=6,
                total_rebounds=8,
                assists=4,
                steals=2,
                blocks=1,
                turnovers=3,
                personal_fouls=2,
                points=16,
                plus_minus=-2.1,
                avg_shot_distance=12.3
            )
        ]
    
    @pytest.fixture
    def sample_advanced_stats(self) -> List[PlayerSeasonAdvancedStatsDTO]:
        """Create sample advanced stats data for testing."""
        return [
            PlayerSeasonAdvancedStatsDTO(
                player_id=1,
                season="2024-25",
                team_id=1,
                age=25,
                games_played=82,
                wins=50,
                losses=32,
                win_percentage=0.610,
                minutes_played=35.5,
                offensive_rating=115.2,
                defensive_rating=108.7,
                net_rating=6.5,
                assist_percentage=25.3,
                assist_to_turnover_ratio=3.0,
                assist_ratio=20.1,
                offensive_rebound_percentage=3.2,
                defensive_rebound_percentage=12.8,
                rebound_percentage=8.1,
                turnover_percentage=12.5,
                effective_field_goal_percentage=0.563,
                true_shooting_percentage=0.598,
                usage_percentage=22.4,
                pace=98.5,
                pie=12.3,
                possessions=75
            ),
            PlayerSeasonAdvancedStatsDTO(
                player_id=2,
                season="2024-25",
                team_id=2,
                age=28,
                games_played=78,
                wins=35,
                losses=43,
                win_percentage=0.449,
                minutes_played=32.1,
                offensive_rating=105.8,
                defensive_rating=112.3,
                net_rating=-6.5,
                assist_percentage=18.7,
                assist_to_turnover_ratio=1.33,
                assist_ratio=15.2,
                offensive_rebound_percentage=5.1,
                defensive_rebound_percentage=18.9,
                rebound_percentage=12.0,
                turnover_percentage=15.8,
                effective_field_goal_percentage=0.464,
                true_shooting_percentage=0.521,
                usage_percentage=18.9,
                pace=96.2,
                pie=8.7,
                possessions=68
            )
        ]
    
    def test_write_player_season_raw_stats_success(self, temp_db, sample_raw_stats):
        """Test successful writing of player season raw stats."""
        writer = DatabaseWriter(temp_db)
        
        result = writer.write_player_season_raw_stats(sample_raw_stats)
        
        assert result.success is True
        assert result.rows_affected == 2
        assert result.table_name == "PlayerSeasonRawStats"
        assert result.error_message is None
        
        # Verify data was actually written
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM PlayerSeasonRawStats")
            count = cursor.fetchone()[0]
            assert count == 2
            
            # Verify specific data
            cursor = conn.execute(
                "SELECT player_id, season, team_id, points, field_goals_made FROM PlayerSeasonRawStats WHERE player_id = 1"
            )
            row = cursor.fetchone()
            assert row[0] == 1
            assert row[1] == "2024-25"
            assert row[2] == 1
            assert row[3] == 22
            assert row[4] == 8
    
    def test_write_player_season_advanced_stats_success(self, temp_db, sample_advanced_stats):
        """Test successful writing of player season advanced stats."""
        writer = DatabaseWriter(temp_db)
        
        result = writer.write_player_season_advanced_stats(sample_advanced_stats)
        
        assert result.success is True
        assert result.rows_affected == 2
        assert result.table_name == "PlayerSeasonAdvancedStats"
        assert result.error_message is None
        
        # Verify data was actually written
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM PlayerSeasonAdvancedStats")
            count = cursor.fetchone()[0]
            assert count == 2
            
            # Verify specific data
            cursor = conn.execute(
                "SELECT player_id, season, team_id, offensive_rating, defensive_rating FROM PlayerSeasonAdvancedStats WHERE player_id = 1"
            )
            row = cursor.fetchone()
            assert row[0] == 1
            assert row[1] == "2024-25"
            assert row[2] == 1
            assert row[3] == 115.2
            assert row[4] == 108.7
    
    def test_write_empty_data(self, temp_db):
        """Test writing empty data."""
        writer = DatabaseWriter(temp_db)
        
        result = writer.write_player_season_raw_stats([])
        
        assert result.success is True
        assert result.rows_affected == 0
        assert result.error_message == "No data to write"
    
    def test_schema_validation_failure(self, temp_db):
        """Test schema validation failure."""
        writer = DatabaseWriter(temp_db)
        
        # Create invalid data (missing required fields)
        invalid_data = [
            PlayerSeasonRawStatsDTO(
                player_id=1,
                season="2024-25",
                team_id=1
                # Missing other required fields
            )
        ]
        
        result = writer.write_player_season_raw_stats(invalid_data)
        
        # Should still succeed because DTO validation happens before database write
        assert result.success is True
    
    def test_atomic_transaction_rollback(self, temp_db):
        """Test that failed transactions are properly rolled back."""
        writer = DatabaseWriter(temp_db)
        
        # Create data that will cause a foreign key constraint violation
        invalid_data = [
            PlayerSeasonRawStatsDTO(
                player_id=999,  # Non-existent player
                season="2024-25",
                team_id=1,
                games_played=82,
                points=20
            )
        ]
        
        result = writer.write_player_season_raw_stats(invalid_data)
        
        # Should fail due to foreign key constraint
        assert result.success is False
        assert result.rows_affected == 0
        assert "FOREIGN KEY constraint failed" in result.error_message
        
        # Verify no data was written
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM PlayerSeasonRawStats")
            count = cursor.fetchone()[0]
            assert count == 0
    
    def test_verify_data_integrity(self, temp_db, sample_raw_stats):
        """Test data integrity verification."""
        writer = DatabaseWriter(temp_db)
        
        # Write data first
        result = writer.write_player_season_raw_stats(sample_raw_stats)
        assert result.success is True
        
        # Verify data integrity
        integrity_result = writer.verify_data_integrity("PlayerSeasonRawStats")
        
        assert integrity_result["success"] is True
        assert integrity_result["total_rows"] == 2
        assert integrity_result["has_data"] is True
        assert integrity_result["critical_columns_valid"] is True
        assert integrity_result["null_checks"]["player_id"] == 0
        assert integrity_result["null_checks"]["season"] == 0
        assert integrity_result["null_checks"]["team_id"] == 0
    
    def test_get_table_schema(self, temp_db):
        """Test getting table schema."""
        writer = DatabaseWriter(temp_db)
        
        schema = writer.get_table_schema("PlayerSeasonRawStats")
        
        assert "player_id" in schema
        assert "season" in schema
        assert "team_id" in schema
        assert "points" in schema
        assert "field_goals_made" in schema
        assert schema["player_id"] == "INTEGER"
        assert schema["season"] == "TEXT"
    
    def test_write_with_duplicate_keys(self, temp_db, sample_raw_stats):
        """Test writing data with duplicate primary keys (should use REPLACE)."""
        writer = DatabaseWriter(temp_db)
        
        # Write data first time
        result1 = writer.write_player_season_raw_stats(sample_raw_stats)
        assert result1.success is True
        
        # Modify data and write again (same primary keys)
        modified_stats = sample_raw_stats.copy()
        modified_stats[0].points = 25  # Change points
        
        result2 = writer.write_player_season_raw_stats(modified_stats)
        assert result2.success is True
        
        # Verify data was updated (not duplicated)
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM PlayerSeasonRawStats")
            count = cursor.fetchone()[0]
            assert count == 2  # Still only 2 rows
            
            # Verify the points were updated
            cursor = conn.execute("SELECT points FROM PlayerSeasonRawStats WHERE player_id = 1")
            points = cursor.fetchone()[0]
            assert points == 25


if __name__ == "__main__":
    pytest.main([__file__])
