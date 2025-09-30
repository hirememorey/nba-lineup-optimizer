-- schema.sql
-- ⚠️ DEPRECATED - DO NOT USE ⚠️
-- 
-- This file is dangerously outdated and does not reflect the actual database structure.
-- The project uses a multi-database architecture with data distributed across three SQLite files.
-- 
-- For the current, accurate database structure, see:
-- - docs/data_dictionary.md (definitive reference)
-- - docs/database_setup.md (setup guide)
-- 
-- To inspect actual table schemas, use:
-- sqlite3 src/nba_stats/db/nba_stats.db ".schema TableName"
--
-- This file is kept for historical reference only and should not be used for development.

-- Basic Metadata Tables
CREATE TABLE Seasons (
    season_id TEXT PRIMARY KEY, -- e.g., "2024-25"
    start_date DATE,
    end_date DATE
);

CREATE TABLE Players (
    player_id INTEGER PRIMARY KEY, -- Use official NBA player ID
    player_name TEXT NOT NULL
);

CREATE TABLE Teams (
    team_id INTEGER PRIMARY KEY, -- Use official NBA team ID
    team_name TEXT NOT NULL,
    team_abbreviation TEXT NOT NULL UNIQUE
);

CREATE TABLE Games (
    game_id INTEGER PRIMARY KEY, -- Use official NBA game ID
    season_id TEXT NOT NULL,
    game_date DATE NOT NULL,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    FOREIGN KEY (season_id) REFERENCES Seasons(season_id),
    FOREIGN KEY (home_team_id) REFERENCES Teams(team_id),
    FOREIGN KEY (away_team_id) REFERENCES Teams(team_id)
);

-- Data for Analysis Input Tables
CREATE TABLE PlayerSeasonRawStats (
    player_season_stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    season_id TEXT NOT NULL,
    team_id INTEGER NOT NULL, -- Team player accumulated stats with (handle trades if necessary later)
    minutes_played INTEGER,
    -- Metrics from Sec 2.1 (Replace with exact names from your data source)
    FTPCT REAL, TSPCT REAL, THPAr REAL, FTr REAL, TRBPCT REAL, ASTPCT REAL,
    AVGDIST REAL, Zto3r REAL, THto10r REAL, TENto16r REAL, SIXTto3PTr REAL,
    HEIGHT REAL, WINGSPAN REAL, FRNTCTTCH REAL, TOP REAL, AVGSECPERTCH REAL,
    AVGDRIBPERTCH REAL, ELBWTCH REAL, POSTUPS REAL, PNTTOUCH REAL, DRIVES REAL,
    DRFGA REAL, DRPTSPCT REAL, DRPASSPCT REAL, DRASTPCT REAL, DRTOVPCT REAL,
    DRPFPCT REAL, DRIMFGPCT REAL, CSFGA REAL, CS3PA REAL, PASSESMADE REAL,
    SECAST REAL, POTAST REAL, PUFGA REAL, PU3PA REAL, PSTUPFGA REAL,
    PSTUPPTSPCT REAL, PSTUPPASSPCT REAL, PSTUPASTPCT REAL, PSTUPTOVPCT REAL,
    PNTTCHS REAL, PNTFGA REAL, PNTPTSPCT REAL, PNTPASSPCT REAL, PNTASTPCT REAL,
    PNTTVPCT REAL, AVGFGATTEMPTEDAGAINSTPERGAME REAL,
    -- Ensure all 48 metrics are included here
    FOREIGN KEY (player_id) REFERENCES Players(player_id),
    FOREIGN KEY (season_id) REFERENCES Seasons(season_id),
    FOREIGN KEY (team_id) REFERENCES Teams(team_id),
    UNIQUE (player_id, season_id, team_id) -- Assumes stats are aggregated per team if traded mid-season
);

CREATE TABLE PlayerSeasonSkills (
    player_season_skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    season_id TEXT NOT NULL,
    offensive_skill_rating REAL,
    defensive_skill_rating REAL,
    skill_metric_source TEXT NOT NULL, -- e.g., 'DARKO', 'EPM', 'LEBRON'
    FOREIGN KEY (player_id) REFERENCES Players(player_id),
    FOREIGN KEY (season_id) REFERENCES Seasons(season_id),
    UNIQUE (player_id, season_id, skill_metric_source)
);

CREATE TABLE PlayerSalaries (
    player_salary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    season_id TEXT NOT NULL,
    salary REAL,
    salary_source TEXT, -- e.g., 'HoopsHype', 'Spotrac'
    FOREIGN KEY (player_id) REFERENCES Players(player_id),
    FOREIGN KEY (season_id) REFERENCES Seasons(season_id),
    UNIQUE (player_id, season_id)
);

-- Raw Play-by-Play Data Table
CREATE TABLE PossessionEvents (
    possession_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    period INTEGER NOT NULL,
    game_clock_seconds REAL NOT NULL,
    event_sequence_number INTEGER NOT NULL, -- Unique identifier for event order within a game
    event_type TEXT, -- e.g., 'SHOT', 'TURNOVER', 'FOUL', 'REBOUND', 'FT'
    event_description TEXT,
    off_team_id INTEGER NOT NULL, -- Team on offense during this event
    def_team_id INTEGER NOT NULL, -- Team on defense during this event
    -- Player IDs on court at the time of the event
    off_p1_id INTEGER, off_p2_id INTEGER, off_p3_id INTEGER, off_p4_id INTEGER, off_p5_id INTEGER,
    def_p1_id INTEGER, def_p2_id INTEGER, def_p3_id INTEGER, def_p4_id INTEGER, def_p5_id INTEGER,
    points_scored_on_event INTEGER DEFAULT 0, -- Points from this specific event (e.g., 2/3 for shot, 1 for FT)
    -- Player IDs involved in the specific event (optional but helpful for detailed analysis)
    player1_id INTEGER, -- Main actor (shooter, turnover, fouler)
    player2_id INTEGER, -- Secondary actor (assist, fouled, rebounder)
    player3_id INTEGER, -- Tertiary actor (blocker, steal)
    FOREIGN KEY (game_id) REFERENCES Games(game_id),
    FOREIGN KEY (off_team_id) REFERENCES Teams(team_id),
    FOREIGN KEY (def_team_id) REFERENCES Teams(team_id),
    FOREIGN KEY (off_p1_id) REFERENCES Players(player_id),
    FOREIGN KEY (off_p2_id) REFERENCES Players(player_id),
    FOREIGN KEY (off_p3_id) REFERENCES Players(player_id),
    FOREIGN KEY (off_p4_id) REFERENCES Players(player_id),
    FOREIGN KEY (off_p5_id) REFERENCES Players(player_id),
    FOREIGN KEY (def_p1_id) REFERENCES Players(player_id),
    FOREIGN KEY (def_p2_id) REFERENCES Players(player_id),
    FOREIGN KEY (def_p3_id) REFERENCES Players(player_id),
    FOREIGN KEY (def_p4_id) REFERENCES Players(player_id),
    FOREIGN KEY (def_p5_id) REFERENCES Players(player_id),
    FOREIGN KEY (player1_id) REFERENCES Players(player_id),
    FOREIGN KEY (player2_id) REFERENCES Players(player_id),
    FOREIGN KEY (player3_id) REFERENCES Players(player_id),
    UNIQUE (game_id, event_sequence_number)
);

-- Indexes for Performance
CREATE INDEX idx_games_season_date ON Games(season_id, game_date);
CREATE INDEX idx_player_season_stats_player_season ON PlayerSeasonRawStats(player_id, season_id);
CREATE INDEX idx_player_season_skills_player_season ON PlayerSeasonSkills(player_id, season_id);
CREATE INDEX idx_player_salaries_player_season ON PlayerSalaries(player_id, season_id);
CREATE INDEX idx_possession_events_game_id ON PossessionEvents(game_id);
CREATE INDEX idx_possession_events_players ON PossessionEvents(off_p1_id, off_p2_id, off_p3_id, off_p4_id, off_p5_id);
CREATE INDEX idx_possession_events_event_type ON PossessionEvents(event_type); 