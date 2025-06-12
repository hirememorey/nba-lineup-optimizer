"""Tests for the populate_player_average_shot_distance script."""
import pytest
import sqlite3
from unittest.mock import MagicMock
from src.nba_stats.scripts.populate_player_average_shot_distance import fetch_and_store_player_avg_shot_distance
from src.nba_stats.db.connection import register_datetime_adapters

MOCK_SHOT_CHART_RESPONSE = {
    "resultSets": [
        {
            "name": "Shot_Chart_Detail",
            "headers": ["GAME_ID", "TEAM_ID", "PLAYER_ID", "PLAYER_NAME", "SHOT_DISTANCE", "LOC_X", "LOC_Y"],
            "rowSet": [
                ["0022300001", 1610612743, 203999, "Nikola Jokic", 5, 50, -10],
                ["0022300001", 1610612743, 203999, "Nikola Jokic", 15, 150, 20],
                ["0022300001", 1610612743, 203999, "Nikola Jokic", 25, 250, 30],
            ]
        }
    ]
}

@pytest.fixture
def test_db_avg_shot_dist():
    """Create an in-memory SQLite database for testing avg_shot_distance."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    register_datetime_adapters()
    cursor = conn.cursor()

    # Create Players and PlayerSeasonRawStats tables
    cursor.execute("CREATE TABLE Players (player_id INTEGER PRIMARY KEY, player_name TEXT, team_id INTEGER)")
    cursor.execute("INSERT INTO Players (player_id, player_name, team_id) VALUES (203999, 'Nikola Jokic', 1610612743)")

    cursor.execute('''
        CREATE TABLE PlayerSeasonRawStats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            season TEXT NOT NULL,
            avg_shot_distance REAL,
            updated_at TIMESTAMP,
            UNIQUE(player_id, season)
        )
    ''')
    cursor.execute("INSERT INTO PlayerSeasonRawStats (player_id, season) VALUES (203999, '2023-24')")
    
    conn.commit()
    yield conn
    conn.close()

def test_fetch_and_store_player_avg_shot_distance(test_db_avg_shot_dist):
    """Test fetching, calculating, and storing player average shot distance."""
    season = "2023-24"
    mock_client = MagicMock()
    mock_client.get_shot_chart_detail.return_value = MOCK_SHOT_CHART_RESPONSE

    # Use the test-specific db fixture
    fetch_and_store_player_avg_shot_distance(season=season, conn=test_db_avg_shot_dist, client=mock_client)

    cursor = test_db_avg_shot_dist.cursor()
    cursor.execute("SELECT avg_shot_distance FROM PlayerSeasonRawStats WHERE player_id = ?", (203999,))
    stats = cursor.fetchone()

    assert stats is not None
    # Expected average is (5 + 15 + 25) / 3 = 15
    assert stats["avg_shot_distance"] == pytest.approx(15.0)

def test_no_shots_data(test_db_avg_shot_dist):
    """Test case where a player has no shots for the season."""
    season = "2023-24"
    mock_client = MagicMock()
    # Mock response with an empty rowSet
    MOCK_SHOT_CHART_EMPTY_RESPONSE = {
        "resultSets": [{"name": "Shot_Chart_Detail", "headers": ["SHOT_DISTANCE"], "rowSet": []}]
    }
    mock_client.get_shot_chart_detail.return_value = MOCK_SHOT_CHART_EMPTY_RESPONSE

    fetch_and_store_player_avg_shot_distance(season=season, conn=test_db_avg_shot_dist, client=mock_client)
    
    cursor = test_db_avg_shot_dist.cursor()
    cursor.execute("SELECT avg_shot_distance FROM PlayerSeasonRawStats WHERE player_id = ?", (203999,))
    stats = cursor.fetchone()

    assert stats is not None
    # Expect NULL or None when no shots are found
    assert stats["avg_shot_distance"] is None 