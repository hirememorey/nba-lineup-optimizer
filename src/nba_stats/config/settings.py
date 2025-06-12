"""Configuration settings for the NBA Stats application."""

import os
from typing import List

# Project Root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Database Configuration
DB_PATH = os.path.join(PROJECT_ROOT, "src", "nba_stats", "db", "nba_stats.db")
SEASON_ID = "2024-25"
MIN_MINUTES_THRESHOLD = 1000

# HTTP Request Configuration
MAX_WORKERS = 2
MAX_RETRIES = 12
API_TIMEOUT = 120

# Delay/Backoff Configuration
MIN_SLEEP = 3.0
MAX_SLEEP = 6.0
RETRY_BACKOFF_BASE = 2
RETRY_BACKOFF_FACTOR = 1.2
MAX_BACKOFF_SLEEP = 300

# Database Writer Configuration
BATCH_SIZE = 50
SENTINEL = object()  # Signal for the writer thread to stop

# User Agents for API requests
USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.0.0 Safari/537.36"
]

# Base headers for API requests
BASE_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Host": "stats.nba.com",
    "Origin": "https://www.nba.com",
    "Referer": "https://www.nba.com/",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
}

# Logging Configuration
LOG_FILE = "nba_stats.log"
LOG_LEVEL = "INFO"

# API Endpoints
API_BASE_URL = "https://stats.nba.com/stats"
ENDPOINTS = {
    "player_stats": "/leaguedashplayerstats",
    "player_dashboard": "/playerdashboardbygeneralsplits",
    "player_advanced": "/playerdashboardbygeneralsplits",
    "player_info": "/commonplayerinfo",
    "shooting_splits": "/playerdashboardbyshootingsplits",
    "player_tracking": "/leaguedashptstats",
    "player_hustle": "/playerhustlestats",
    "player_clutch": "/playerclutchsplits",
    "shot_tracking": "/playershottracking",
    "passing": "/playerpasstracking",
    "defense": "/playerdefensetracking",
    "defensive_matchups": "/leaguedashptdefend",
    "play_types": "/playerdashboardbyplaytype"
} 