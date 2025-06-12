# NBA Stats Package

A Python package for fetching and storing NBA player statistics.

## Features

- Fetch NBA player statistics for any season
- Store player data in a database
- Asynchronous data fetching for better performance
- Comprehensive logging and error handling

## Installation

```bash
pip install -e .
```

## Usage

```python
from nba_stats import NBAStatsFetcher, DatabaseConnection, SEASON_ID

# Initialize components
db = DatabaseConnection()
fetcher = NBAStatsFetcher()

# Fetch and save player data
players = fetcher.fetch_player_stats(SEASON_ID)
db.save_players(players)
```

## Project Structure

```
nba_stats/
├── src/
│   └── nba_stats/
│       ├── __init__.py
│       ├── __main__.py
│       ├── fetcher.py
│       ├── models.py
│       └── database.py
├── setup.py
└── README.md
```

## Dependencies

- requests>=2.31.0
- aiohttp>=3.9.1
- pandas>=2.1.0
- numpy>=1.24.0

## License

MIT 