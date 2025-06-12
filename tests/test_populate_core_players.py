import pytest
import sqlite3
from unittest.mock import MagicMock
from src.nba_stats.scripts.populate_core_players import fetch_and_store_all_players
from src.nba_stats.models.player import Player
from src.nba_stats.db.connection import register_datetime_adapters

# In-memory SQLite database for testing
@pytest.fixture
def test_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    register_datetime_adapters()
    cursor = conn.cursor()
    # Teams table is needed for foreign key constraints
    cursor.execute("CREATE TABLE Teams (team_id INTEGER PRIMARY KEY, team_name TEXT)")
    # Create a minimal Players table for the test
    cursor.execute("""
        CREATE TABLE Players (
            player_id INTEGER PRIMARY KEY,
            player_name TEXT,
            first_name TEXT,
            last_name TEXT,
            team_id INTEGER,
            position TEXT,
            height TEXT,
            weight TEXT,
            birth_date TEXT,
            updated_at TEXT
        );
    """)
    conn.commit()
    yield conn
    conn.close()

def test_fetch_and_store_all_players(test_db, mock_nba_stats_client, mocker):
    mocker.patch('src.nba_stats.scripts.populate_core_players.get_db_connection', return_value=test_db)
    season_to_load = "2023-24"
    processed_players = fetch_and_store_all_players(season_to_load, nba_stats_client=mock_nba_stats_client)

    # Assertions
    assert len(processed_players) == 2
    assert isinstance(processed_players[0], Player)
    assert processed_players[0].player_id == 203999
    assert processed_players[1].player_name == "Jayson Tatum"

    # Verify the data was inserted into the database
    cursor = test_db.cursor()
    cursor.execute("SELECT * FROM Players")
    rows = cursor.fetchall()
    assert len(rows) == 2

    cursor.execute("SELECT player_name FROM Players WHERE player_id = ?", (203999,))
    jokic_name = cursor.fetchone()[0]
    assert jokic_name == "Nikola Jokic" 