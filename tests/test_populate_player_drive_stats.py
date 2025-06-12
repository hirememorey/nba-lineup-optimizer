import pytest
import sqlite3
from unittest.mock import MagicMock, patch
from src.nba_stats.scripts.populate_player_drive_stats import fetch_and_store_player_drive_stats
from src.nba_stats.db.connection import register_datetime_adapters

# Mock data for get_player_drive_stats
MOCK_DRIVE_STATS_RESPONSE = {
    "resultSets": [{
        "name": "DrivePlayerDash",
        "headers": ["PLAYER_ID", "PLAYER_NAME", "TEAM_ID", "TEAM_ABBREVIATION", "GP", "W", "L", "MIN", "DRIVES", "DRIVE_FGM", "DRIVE_FGA", "DRIVE_FG_PCT", "DRIVE_FTM", "DRIVE_FTA", "DRIVE_FT_PCT", "DRIVE_PTS", "DRIVE_PASSES", "DRIVE_PASSES_PCT", "DRIVE_AST", "DRIVE_AST_PCT", "DRIVE_TOV", "DRIVE_TOV_PCT", "DRIVE_PF", "DRIVE_PF_PCT"],
        "rowSet": [
            [203999, "Nikola Jokic", 1610612743, "DEN", 79, 56, 23, 34.6, 10.0, 5.0, 8.0, 0.625, 2.5, 3.0, 0.833, 12.5, 5.0, 0.500, 2.5, 0.500, 1.0, 0.100, 1.0, 0.100]
        ]
    }]
}

@pytest.fixture
def test_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    register_datetime_adapters()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE Players (player_id INTEGER PRIMARY KEY, player_name TEXT)")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PlayerSeasonDriveStats (
            player_id INTEGER, season TEXT, team_id INTEGER, minutes_played REAL,
            drives REAL, drive_fgm REAL, drive_fga REAL, drive_fg_pct REAL,
            drive_ftm REAL, drive_fta REAL, drive_ft_pct REAL, drive_pts REAL,
            drive_passes REAL, drive_pass_pct REAL, drive_ast REAL, drive_ast_pct REAL,
            drive_tov REAL, drive_tov_pct REAL, drive_pf REAL, drive_pf_pct REAL,
            updated_at TEXT,
            PRIMARY KEY (player_id, season, team_id)
        )
    ''')
    conn.commit()
    yield conn
    conn.close()

def test_fetch_and_store_player_drive_stats(test_db, mocker):
    season = "2023-24"
    players_to_process = [(203999, "Nikola Jokic")]

    mock_client = MagicMock()
    mock_client.get_player_drive_stats.return_value = MOCK_DRIVE_STATS_RESPONSE

    mocker.patch('src.nba_stats.scripts.populate_player_drive_stats.get_players_from_db', return_value=players_to_process)

    fetch_and_store_player_drive_stats(season, conn=test_db, client=mock_client)

    cursor = test_db.cursor()
    cursor.execute("SELECT * FROM PlayerSeasonDriveStats WHERE player_id = ?", (203999,))
    stats = cursor.fetchone()
    assert stats is not None
    assert stats[4] == 10.0  # drives 