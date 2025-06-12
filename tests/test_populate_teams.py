import pytest
import sqlite3
from unittest.mock import MagicMock
from src.nba_stats.scripts.populate_teams import fetch_and_store_teams
from src.nba_stats.db.connection import register_datetime_adapters

MOCK_TEAMS_RESPONSE = {
    "resultSets": [
        {
            "name": "CommonTeamYears",
            "headers": ["TEAM_ID", "MIN_YEAR", "MAX_YEAR", "ABBREVIATION"],
            "rowSet": [
                [1610612737, "1949", "2023", "ATL"],
                [1610612738, "1946", "2023", "BOS"]
            ]
        }
    ]
}

@pytest.fixture
def test_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    register_datetime_adapters()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE Teams (
            id INTEGER PRIMARY KEY,
            team_id INTEGER UNIQUE,
            abbreviation TEXT,
            nickname TEXT,
            year_founded INTEGER,
            city TEXT,
            full_name TEXT,
            updated_at TEXT
        );
    """)
    conn.commit()
    yield conn
    conn.close()

@pytest.fixture
def mock_nba_stats_client():
    mock_client = MagicMock()
    mock_client.get_teams.return_value = MOCK_TEAMS_RESPONSE
    return mock_client

def test_fetch_and_store_teams(test_db, mock_nba_stats_client, mocker):
    mocker.patch('src.nba_stats.scripts.populate_teams.get_db_connection', return_value=test_db)
    fetch_and_store_teams(nba_stats_client=mock_nba_stats_client)

    cursor = test_db.cursor()
    cursor.execute("SELECT * FROM Teams")
    rows = cursor.fetchall()
    assert len(rows) == 2

    cursor.execute("SELECT abbreviation FROM Teams WHERE team_id = ?", (1610612737,))
    abbreviation = cursor.fetchone()[0]
    assert abbreviation == "ATL" 