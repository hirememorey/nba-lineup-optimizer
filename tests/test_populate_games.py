import pytest
import sqlite3
from unittest.mock import MagicMock
from src.nba_stats.scripts.populate_games import populate_games
from src.nba_stats.db.connection import register_datetime_adapters

# Mock response for get_schedule
MOCK_SCHEDULE_RESPONSE = [
    {'gameId': '0022300001', 'gameDate': '2023-10-24', 'teamId': 1610612743},
    {'gameId': '0022300001', 'gameDate': '2023-10-24', 'teamId': 1610612747}
]

@pytest.fixture
def test_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    register_datetime_adapters()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE Teams (
            team_id INTEGER PRIMARY KEY,
            team_name TEXT
        )
    ''')
    cursor.execute("INSERT INTO Teams (team_id, team_name) VALUES (1610612743, 'Nuggets')")
    cursor.execute("INSERT INTO Teams (team_id, team_name) VALUES (1610612747, 'Lakers')")
    cursor.execute('''
        CREATE TABLE Games (
            game_id TEXT PRIMARY KEY,
            game_date TEXT,
            season TEXT,
            season_type TEXT,
            home_team_id INTEGER,
            away_team_id INTEGER,
            home_team_score INTEGER,
            away_team_score INTEGER,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')
    conn.commit()
    yield conn
    conn.close()

def test_populate_games(test_db, mocker):
    season = "2023-24"
    mock_client = MagicMock()
    mock_client.get_schedule.return_value = MOCK_SCHEDULE_RESPONSE

    mocker.patch('src.nba_stats.scripts.populate_games.get_nba_stats_client', return_value=mock_client)

    populate_games(conn=test_db, season=season)

    cursor = test_db.cursor()
    # The original logic inserts one row per team for a game, so we expect 2 rows for game_id 0022300001
    cursor.execute("SELECT * FROM Games WHERE game_id = ?", ("0022300001",))
    game = cursor.fetchone()
    assert game is not None
    assert game['home_team_id'] == 1610612743
    assert game['away_team_id'] == 1610612747 