"""Tests for the populate_player_hustle_stats script."""
import pytest
import sqlite3
from unittest.mock import MagicMock
from src.nba_stats.scripts.populate_player_hustle_stats import fetch_and_store_league_hustle_stats
from src.nba_stats.db.connection import register_datetime_adapters

MOCK_HUSTLE_STATS_RESPONSE = {
    "resultSets": [{
        "name": "HustleStatsPlayer",
        "headers": ["PLAYER_ID", "PLAYER_NAME", "TEAM_ID", "TEAM_ABBREVIATION", "G", "MIN", "CONTESTED_SHOTS", "CONTESTED_SHOTS_2PT", "CONTESTED_SHOTS_3PT", "CHARGES_DRAWN", "DEFLECTIONS", "LOOSE_BALLS_RECOVERED", "SCREEN_ASSISTS", "BOX_OUTS"],
        "rowSet": [
            [203999, "Nikola Jokic", 1610612743, "DEN", 79, 34.6, 10.0, 5.0, 5.0, 0.5, 2.0, 1.0, 1.5, 3.0]
        ]
    }]
}

@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    register_datetime_adapters()
    cursor = conn.cursor()
    # Create Players and Teams tables to satisfy foreign key constraints
    cursor.execute("CREATE TABLE Players (player_id INTEGER PRIMARY KEY, player_name TEXT)")
    cursor.execute("INSERT INTO Players (player_id, player_name) VALUES (203999, 'Nikola Jokic')")
    cursor.execute("CREATE TABLE Teams (team_id INTEGER PRIMARY KEY, team_name TEXT)")
    cursor.execute("INSERT INTO Teams (team_id, team_name) VALUES (1610612743, 'Denver Nuggets')")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PlayerSeasonHustleStats (
            player_id INTEGER NOT NULL,
            season TEXT NOT NULL,
            team_id INTEGER NOT NULL,
            team_abbreviation TEXT,
            games_played INTEGER,
            minutes_played REAL,
            contested_shots INTEGER,
            contested_2pt_shots INTEGER,
            contested_3pt_shots INTEGER,
            deflections INTEGER,
            loose_balls_recovered INTEGER,
            charges_drawn REAL,
            screen_assists REAL,
            box_outs REAL,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY (player_id, season, team_id),
            FOREIGN KEY (player_id) REFERENCES Players(player_id),
            FOREIGN KEY (team_id) REFERENCES Teams(team_id)
        )
    ''')
    conn.commit()
    yield conn
    conn.close()

def test_fetch_and_store_league_hustle_stats(test_db):
    """Test fetching and storing league hustle stats."""
    season = "2023-24"
    mock_client = MagicMock()
    mock_client.get_league_hustle_stats.return_value = MOCK_HUSTLE_STATS_RESPONSE

    fetch_and_store_league_hustle_stats(season=season, conn=test_db, client=mock_client)

    cursor = test_db.cursor()
    cursor.execute("SELECT * FROM PlayerSeasonHustleStats WHERE player_id = ?", (203999,))
    stats = cursor.fetchone()
    assert stats is not None
    # Verify a few key data points
    assert stats[0] == 203999  # player_id
    assert stats[1] == "2023-24" # season
    assert stats[2] == 1610612743 # team_id
    assert stats[6] == 10.0  # contested_shots
    assert stats[11] == 0.5  # charges_drawn 