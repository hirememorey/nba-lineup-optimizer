import pytest
import sqlite3
from unittest.mock import MagicMock, patch
from src.nba_stats.scripts.populate_player_season_stats import (
    fetch_and_store_player_season_stats,
    fetch_player_stats_task,
    insert_raw_player_stats,
    insert_advanced_player_stats
)
from src.nba_stats.db.connection import register_datetime_adapters

# Mock data
MOCK_PLAYER_INFO = {'TEAM_ID': 1610612743}
MOCK_STATS_RESPONSE = {
    "resultSets": [{
        "name": "OverallPlayerDashboard",
        "headers": ["GP", "GS", "MIN", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", "FTM", "FTA", "FT_PCT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TOV", "PF", "PTS", "PLUS_MINUS"],
        "rowSet": [[82, 82, 34.6, 10.9, 20.8, 0.525, 2.9, 7.1, 0.41, 7.8, 8.7, 0.898, 1.1, 6.5, 7.6, 5.9, 1.0, 0.5, 3.5, 2.5, 32.5, 4.5]]
    }]
}
MOCK_ADVANCED_STATS_RESPONSE = {
    "resultSets": [{
        "name": "PlayerDashboardByYearOverYear",
        "headers": ["AGE", "W", "L", "W_PCT", "OFF_RATING", "DEF_RATING", "NET_RATING", "AST_PCT", "AST_TO", "AST_RATIO", "OREB_PCT", "DREB_PCT", "REB_PCT", "TM_TOV_PCT", "E_FG_PCT", "TS_PCT", "USG_PCT", "PACE", "PIE", "POSS"],
        "rowSet": [[25, 57, 25, 0.695, 122.2, 110.6, 11.6, 0.269, 1.68, 18.2, 0.029, 0.18, 0.104, 13.7, 0.596, 0.636, 0.32, 100.9, 0.203, 7000]]
    }]
}

@pytest.fixture
def test_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    register_datetime_adapters()
    cursor = conn.cursor()
    # Create Players, PlayerSeasonRawStats, and PlayerSeasonAdvancedStats tables
    cursor.execute("CREATE TABLE Players (player_id INTEGER PRIMARY KEY, player_name TEXT)")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PlayerSeasonRawStats (
            player_id INTEGER, season TEXT, team_id INTEGER, games_played INTEGER, games_started INTEGER,
            minutes_played REAL, field_goals_made INTEGER, field_goals_attempted INTEGER, field_goal_percentage REAL,
            three_pointers_made INTEGER, three_pointers_attempted INTEGER, three_point_percentage REAL,
            free_throws_made INTEGER, free_throws_attempted INTEGER, free_throw_percentage REAL,
            offensive_rebounds INTEGER, defensive_rebounds INTEGER, total_rebounds INTEGER,
            assists INTEGER, steals INTEGER, blocks INTEGER, turnovers INTEGER, personal_fouls INTEGER,
            points INTEGER, plus_minus REAL, created_at TEXT, updated_at TEXT,
            PRIMARY KEY (player_id, season, team_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PlayerSeasonAdvancedStats (
            player_id INTEGER, season TEXT, team_id INTEGER, age INTEGER, games_played INTEGER, wins INTEGER,
            losses INTEGER, win_percentage REAL, minutes_played REAL, offensive_rating REAL,
            defensive_rating REAL, net_rating REAL, assist_percentage REAL, assist_to_turnover_ratio REAL,
            assist_ratio REAL, offensive_rebound_percentage REAL, defensive_rebound_percentage REAL,
            rebound_percentage REAL, turnover_percentage REAL, effective_field_goal_percentage REAL,
            true_shooting_percentage REAL, usage_percentage REAL, pace REAL, pie REAL, possessions INTEGER,
            created_at TEXT, updated_at TEXT,
            PRIMARY KEY (player_id, season, team_id)
        )
    ''')
    conn.commit()
    yield conn
    conn.close()

def test_fetch_player_stats_task(mocker):
    """Test the task that fetches stats for a single player."""
    mock_client = MagicMock()
    mock_client.get_player_info.return_value = MOCK_PLAYER_INFO
    mock_client.get_player_stats.return_value = MOCK_STATS_RESPONSE
    mock_client.get_player_advanced_stats.return_value = MOCK_ADVANCED_STATS_RESPONSE
    
    mocker.patch('src.nba_stats.scripts.populate_player_season_stats.get_nba_stats_client', return_value=mock_client)
    
    player_info = (203999, "Nikola Jokic")
    season = "2023-24"
    
    player_id, player_name, player_info_res, stats_res, advanced_stats_res = fetch_player_stats_task(player_info, season)
    
    assert player_id == 203999
    assert player_name == "Nikola Jokic"
    assert player_info_res == MOCK_PLAYER_INFO
    assert stats_res == MOCK_STATS_RESPONSE
    assert advanced_stats_res == MOCK_ADVANCED_STATS_RESPONSE

def test_fetch_and_store_player_season_stats(test_db, mocker):
    """Test the main orchestrator function by mocking the task."""
    season = "2023-24"
    players_to_process = [(203999, "Nikola Jokic")]
    
    # Mock the DB calls
    mocker.patch('src.nba_stats.scripts.populate_player_season_stats.get_players_from_db', return_value=players_to_process)
    
    # Mock the task function to return canned data, avoiding threads and real API calls
    mock_task_result = (203999, "Nikola Jokic", MOCK_PLAYER_INFO, MOCK_STATS_RESPONSE, MOCK_ADVANCED_STATS_RESPONSE)
    mocker.patch(
        'src.nba_stats.scripts.populate_player_season_stats.fetch_player_stats_task',
        return_value=mock_task_result
    )

    # Use a real ThreadPoolExecutor but with a mocked task
    fetch_and_store_player_season_stats(season, conn=test_db)

    # Verify data in Raw stats table
    cursor = test_db.cursor()
    cursor.execute("SELECT * FROM PlayerSeasonRawStats WHERE player_id = ?", (203999,))
    raw_stats = cursor.fetchone()
    assert raw_stats is not None
    assert raw_stats[3] == 82  # games_played

    # Verify data in Advanced stats table
    cursor.execute("SELECT * FROM PlayerSeasonAdvancedStats WHERE player_id = ?", (203999,))
    advanced_stats = cursor.fetchone()
    assert advanced_stats is not None
    assert advanced_stats[3] == 25  # age 