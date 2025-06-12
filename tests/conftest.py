import pytest
from unittest.mock import MagicMock

MOCK_PLAYERS_RESPONSE = {
    "resultSets": [
        {
            "name": "CommonAllPlayers",
            "headers": [
                "PERSON_ID", "DISPLAY_LAST_COMMA_FIRST", "DISPLAY_FIRST_LAST",
                "ROSTERSTATUS", "FROM_YEAR", "TO_YEAR", "PLAYERCODE", "PLAYER_SLUG",
                "TEAM_ID", "TEAM_CITY", "TEAM_NAME", "TEAM_ABBREVIATION", "TEAM_CODE",
                "TEAM_SLUG", "GAMES_PLAYED_FLAG", "OTHERLEAGUE_EXPERIENCE_CH", "MIN"
            ],
            "rowSet": [
                [
                    203999, "Jokic, Nikola", "Nikola Jokic", 1, "2015", "2023",
                    "nikola_jokic", "nikola-jokic", 1610612743, "Denver",
                    "Nuggets", "DEN", "nuggets", "nuggets", "Y", "01", 34.6
                ],
                [
                    1628369, "Focus, Jayson", "Jayson Tatum", 1, "2017", "2023",
                    "jayson_tatum", "jayson-tatum", 1610612738, "Boston",
                    "Celtics", "BOS", "celtics", "celtics", "Y", "00", 36.7
                ]
            ]
        }
    ]
}

@pytest.fixture
def mock_nba_stats_client():
    mock_client = MagicMock()
    mock_client.get_all_players.return_value = MOCK_PLAYERS_RESPONSE
    return mock_client 