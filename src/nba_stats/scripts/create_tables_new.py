"""Script to create all necessary database tables for NBA stats."""

import sqlite3
import logging
from .common_utils import get_db_connection, logger

def create_teams_table(conn: sqlite3.Connection) -> None:
    """Create the Teams table."""
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Teams (
        team_id INTEGER PRIMARY KEY,
        team_name TEXT NOT NULL,
        abbreviation TEXT,
        team_code TEXT NOT NULL,
        team_city TEXT NOT NULL,
        team_conference TEXT NOT NULL,
        team_division TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_teams_conference_division ON Teams(team_conference, team_division)")
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS teams_updated_at
    AFTER UPDATE ON Teams
    BEGIN
        UPDATE Teams SET updated_at = CURRENT_TIMESTAMP
        WHERE team_id = NEW.team_id;
    END;
    """)
    conn.commit()
    logger.info("Teams table checked/created.")

def create_games_table(conn: sqlite3.Connection) -> None:
    """Create the Games table."""
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Games (
        game_id TEXT PRIMARY KEY,
        game_date TEXT NOT NULL,
        home_team_id INTEGER NOT NULL,
        away_team_id INTEGER NOT NULL,
        home_team_score INTEGER,
        away_team_score INTEGER,
        season TEXT NOT NULL,
        season_type TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (home_team_id) REFERENCES Teams(team_id),
        FOREIGN KEY (away_team_id) REFERENCES Teams(team_id)
    )
    ''')
    logger.info("Games table checked/created.")

def create_players_table(conn: sqlite3.Connection) -> None:
    """Create the Players table."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Players (
            player_id INTEGER PRIMARY KEY,
            player_name TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            birth_date TEXT,
            country TEXT,
            height TEXT,
            weight INTEGER,
            jersey_number INTEGER,
            position TEXT,
            team_id INTEGER,
            wingspan REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES Teams(team_id)
        )
    """)
    logger.info("Players table checked/created.")


def create_player_season_raw_stats_table(conn: sqlite3.Connection) -> None:
    """Create the PlayerSeasonRawStats table."""
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PlayerSeasonRawStats (
        player_id INTEGER NOT NULL,
        season TEXT NOT NULL,
        team_id INTEGER NOT NULL,
        games_played INTEGER,
        games_started INTEGER,
        minutes_played REAL,
        field_goals_made INTEGER,
        field_goals_attempted INTEGER,
        field_goal_percentage REAL,
        three_pointers_made INTEGER,
        three_pointers_attempted INTEGER,
        three_point_percentage REAL,
        free_throws_made INTEGER,
        free_throws_attempted INTEGER,
        free_throw_percentage REAL,
        offensive_rebounds INTEGER,
        defensive_rebounds INTEGER,
        total_rebounds INTEGER,
        assists INTEGER,
        steals INTEGER,
        blocks INTEGER,
        turnovers INTEGER,
        personal_fouls INTEGER,
        points INTEGER,
        plus_minus REAL,
        avg_shot_distance REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (player_id, season, team_id),
        FOREIGN KEY (player_id) REFERENCES Players(player_id),
        FOREIGN KEY (team_id) REFERENCES Teams(team_id)
    )
    ''')
    logger.info("PlayerSeasonRawStats table checked/created.")


def create_player_season_advanced_stats_table(conn: sqlite3.Connection) -> None:
    """Create the PlayerSeasonAdvancedStats table."""
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PlayerSeasonAdvancedStats (
        player_id INTEGER NOT NULL,
        season TEXT NOT NULL,
        team_id INTEGER NOT NULL,
        age INTEGER,
        games_played INTEGER,
        wins INTEGER,
        losses INTEGER,
        win_percentage REAL,
        minutes_played REAL,
        offensive_rating REAL,
        defensive_rating REAL,
        net_rating REAL,
        assist_percentage REAL,
        assist_to_turnover_ratio REAL,
        assist_ratio REAL,
        offensive_rebound_percentage REAL,
        defensive_rebound_percentage REAL,
        rebound_percentage REAL,
        turnover_percentage REAL,
        effective_field_goal_percentage REAL,
        true_shooting_percentage REAL,
        usage_percentage REAL,
        pace REAL,
        pie REAL,
        possessions INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (player_id, season, team_id),
        FOREIGN KEY (player_id) REFERENCES Players(player_id),
        FOREIGN KEY (team_id) REFERENCES Teams(team_id)
    )
    ''')
    logger.info("PlayerSeasonAdvancedStats table checked/created.")

def create_player_season_shooting_distance_stats_table(conn: sqlite3.Connection) -> None:
    """Create the PlayerSeasonShootingDistanceStats table."""
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PlayerSeasonShootingDistanceStats (
        player_id INTEGER NOT NULL,
        season TEXT NOT NULL,
        team_id INTEGER NOT NULL,
        restricted_area_fgm INTEGER,
        restricted_area_fga INTEGER,
        restricted_area_fg_pct REAL,
        in_the_paint_non_ra_fgm INTEGER,
        in_the_paint_non_ra_fga INTEGER,
        in_the_paint_non_ra_fg_pct REAL,
        mid_range_fgm INTEGER,
        mid_range_fga INTEGER,
        mid_range_fg_pct REAL,
        left_corner_3_fgm INTEGER,
        left_corner_3_fga INTEGER,
        left_corner_3_fg_pct REAL,
        right_corner_3_fgm INTEGER,
        right_corner_3_fga INTEGER,
        right_corner_3_fg_pct REAL,
        above_the_break_3_fgm INTEGER,
        above_the_break_3_fga INTEGER,
        above_the_break_3_fg_pct REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (player_id, season, team_id),
        FOREIGN KEY (player_id) REFERENCES Players(player_id),
        FOREIGN KEY (team_id) REFERENCES Teams(team_id)
    )
    ''')
    logger.info("PlayerSeasonShootingDistanceStats table checked/created.")

def create_player_season_drive_stats_table(conn: sqlite3.Connection) -> None:
    """Create the PlayerSeasonDriveStats table."""
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PlayerSeasonDriveStats (
        player_id INTEGER NOT NULL,
        season TEXT NOT NULL,
        team_id INTEGER NOT NULL,
        minutes_played REAL,
        drives REAL,
        drive_fgm REAL,
        drive_fga REAL,
        drive_fg_pct REAL,
        drive_ftm REAL,
        drive_fta REAL,
        drive_ft_pct REAL,
        drive_pts REAL,
        drive_passes REAL,
        drive_pass_pct REAL,
        drive_ast REAL,
        drive_ast_pct REAL,
        drive_tov REAL,
        drive_tov_pct REAL,
        drive_pf REAL,
        drive_pf_pct REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (player_id, season, team_id),
        FOREIGN KEY (player_id) REFERENCES Players(player_id),
        FOREIGN KEY (team_id) REFERENCES Teams(team_id)
    )
    ''')
    logger.info("PlayerSeasonDriveStats table checked/created.")

def create_player_season_hustle_stats_table(conn: sqlite3.Connection) -> None:
    """Create the PlayerSeasonHustleStats table."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PlayerSeasonHustleStats (
            player_id INTEGER NOT NULL,
            season TEXT NOT NULL,
            team_id INTEGER NOT NULL,
            games_played INTEGER,
            minutes_played REAL,
            contested_shots REAL,
            contested_shots_2pt REAL,
            contested_shots_3pt REAL,
            charges_drawn REAL,
            deflections REAL,
            loose_balls_recovered REAL,
            screen_assists REAL,
            box_outs REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (player_id, season, team_id),
            FOREIGN KEY (player_id) REFERENCES Players(player_id),
            FOREIGN KEY (team_id) REFERENCES Teams(team_id)
        )
    """)
    logger.info("PlayerSeasonHustleStats table checked/created.")

def create_player_season_opponent_shooting_stats_table(conn: sqlite3.Connection) -> None:
    """Create the PlayerSeasonOpponentShootingStats table."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PlayerSeasonOpponentShootingStats (
            player_id INTEGER NOT NULL,
            season TEXT NOT NULL,
            team_id INTEGER NOT NULL,
            opp_fgm_lt_5ft REAL, opp_fga_lt_5ft REAL, opp_fg_pct_lt_5ft REAL,
            opp_fgm_5_9ft REAL, opp_fga_5_9ft REAL, opp_fg_pct_5_9ft REAL,
            opp_fgm_10_14ft REAL, opp_fga_10_14ft REAL, opp_fg_pct_10_14ft REAL,
            opp_fgm_15_19ft REAL, opp_fga_15_19ft REAL, opp_fg_pct_15_19ft REAL,
            opp_fgm_20_24ft REAL, opp_fga_20_24ft REAL, opp_fg_pct_20_24ft REAL,
            opp_fgm_25_29ft REAL, opp_fga_25_29ft REAL, opp_fg_pct_25_29ft REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (player_id, season, team_id),
            FOREIGN KEY (player_id) REFERENCES Players(player_id),
            FOREIGN KEY (team_id) REFERENCES Teams(team_id)
        )
    """)
    logger.info("PlayerSeasonOpponentShootingStats table checked/created.")

def create_player_season_tracking_touches_stats_table(conn: sqlite3.Connection) -> None:
    """Create the PlayerSeasonTrackingTouchesStats table."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PlayerSeasonTrackingTouchesStats (
            player_id INTEGER NOT NULL,
            season TEXT NOT NULL,
            team_id INTEGER NOT NULL,
            touches REAL,
            front_ct_touches REAL,
            time_of_poss REAL,
            avg_sec_per_touch REAL,
            avg_drib_per_touch REAL,
            pts_per_touch REAL,
            elbow_touches REAL,
            post_touches REAL,
            paint_touches REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (player_id, season, team_id),
            FOREIGN KEY (player_id) REFERENCES Players(player_id),
            FOREIGN KEY (team_id) REFERENCES Teams(team_id)
        )
    """)
    logger.info("PlayerSeasonTrackingTouchesStats table checked/created.")

def create_player_season_passing_stats_table(conn: sqlite3.Connection) -> None:
    """Create the PlayerSeasonPassingStats table."""
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PlayerSeasonPassingStats (
        player_id INTEGER NOT NULL,
        season TEXT NOT NULL,
        team_id INTEGER NOT NULL,
        passes_made REAL,
        passes_received REAL,
        assists REAL,
        secondary_assists REAL,
        potential_assists REAL,
        assist_points_created REAL,
        assist_to_pass_percentage REAL,
        assist_to_bad_pass_ratio REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (player_id, season, team_id),
        FOREIGN KEY (player_id) REFERENCES Players(player_id),
        FOREIGN KEY (team_id) REFERENCES Teams(team_id)
    )
    ''')
    logger.info("PlayerSeasonPassingStats table checked/created.")

def create_player_season_catch_shoot_stats_table(conn: sqlite3.Connection) -> None:
    """Create the PlayerSeasonCatchAndShootStats table."""
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PlayerSeasonCatchAndShootStats (
        player_id INTEGER NOT NULL,
        season TEXT NOT NULL,
        team_id INTEGER NOT NULL,
        catch_shoot_fgm REAL,
        catch_shoot_fga REAL,
        catch_shoot_fg_pct REAL,
        catch_shoot_3pm REAL,
        catch_shoot_3pa REAL,
        catch_shoot_3p_pct REAL,
        catch_shoot_efg_pct REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (player_id, season, team_id),
        FOREIGN KEY (player_id) REFERENCES Players(player_id),
        FOREIGN KEY (team_id) REFERENCES Teams(team_id)
    )
    ''')
    logger.info("PlayerSeasonCatchAndShootStats table checked/created.")

def create_player_season_pull_up_stats_table(conn: sqlite3.Connection) -> None:
    """Create the PlayerSeasonPullUpStats table."""
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PlayerSeasonPullUpStats (
        player_id INTEGER NOT NULL,
        season TEXT NOT NULL,
        team_id INTEGER NOT NULL,
        pull_up_fgm REAL,
        pull_up_fga REAL,
        pull_up_fg_pct REAL,
        pull_up_3pm REAL,
        pull_up_3pa REAL,
        pull_up_3p_pct REAL,
        pull_up_efg_pct REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (player_id, season, team_id),
        FOREIGN KEY (player_id) REFERENCES Players(player_id),
        FOREIGN KEY (team_id) REFERENCES Teams(team_id)
    )
    ''')
    logger.info("PlayerSeasonPullUpStats table checked/created.")

def create_player_lineup_stats_table(conn: sqlite3.Connection) -> None:
    """Create the PlayerLineupStats table."""
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PlayerLineupStats (
        lineup_id TEXT PRIMARY KEY,
        group_id TEXT,
        group_name TEXT,
        team_id INTEGER,
        team_abbreviation TEXT,
        season TEXT NOT NULL,
        minutes_played REAL,
        offensive_rating REAL,
        defensive_rating REAL,
        net_rating REAL,
        assist_percentage REAL,
        assist_to_turnover_ratio REAL,
        assist_ratio REAL,
        offensive_rebound_percentage REAL,
        defensive_rebound_percentage REAL,
        rebound_percentage REAL,
        turnover_percentage REAL,
        effective_field_goal_percentage REAL,
        true_shooting_percentage REAL,
        usage_percentage REAL,
        pace REAL,
        pie REAL,
        possessions INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (team_id) REFERENCES Teams(team_id)
    )
    ''')
    logger.info("PlayerLineupStats table checked/created.")

def create_player_season_rebounding_stats_table(conn: sqlite3.Connection) -> None:
    """Create the PlayerSeasonReboundingStats table."""
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PlayerSeasonReboundingStats (
        player_id INTEGER NOT NULL,
        season TEXT NOT NULL,
        team_id INTEGER NOT NULL,
        rebound_chances REAL,
        rebound_chance_pct REAL,
        contested_rebounds REAL,
        uncontested_rebounds REAL,
        offensive_rebound_chances REAL,
        offensive_rebound_pct REAL,
        defensive_rebound_chances REAL,
        defensive_rebound_pct REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (player_id, season, team_id),
        FOREIGN KEY (player_id) REFERENCES Players(player_id),
        FOREIGN KEY (team_id) REFERENCES Teams(team_id)
    )
    ''')
    logger.info("PlayerSeasonReboundingStats table checked/created.")

def create_player_season_post_up_stats_table(conn: sqlite3.Connection) -> None:
    """Create the PlayerSeasonPostUpStats table."""
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PlayerSeasonPostUpStats (
        player_id INTEGER NOT NULL,
        season TEXT NOT NULL,
        team_id INTEGER NOT NULL,
        post_up_touches REAL,
        post_up_pts REAL,
        post_up_fgm REAL,
        post_up_fga REAL,
        post_up_fg_pct REAL,
        post_up_ftm REAL,
        post_up_fta REAL,
        post_up_ft_pct REAL,
        post_up_pass REAL,
        post_up_pass_pct REAL,
        post_up_ast REAL,
        post_up_ast_pct REAL,
        post_up_tov REAL,
        post_up_tov_pct REAL,
        post_up_pf REAL,
        post_up_pf_pct REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (player_id, season, team_id),
        FOREIGN KEY (player_id) REFERENCES Players(player_id),
        FOREIGN KEY (team_id) REFERENCES Teams(team_id)
    )
    ''')
    logger.info("PlayerSeasonPostUpStats table checked/created.")

def create_player_season_paint_touch_stats_table(conn: sqlite3.Connection) -> None:
    """Create the PlayerSeasonPaintTouchStats table."""
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PlayerSeasonPaintTouchStats (
        player_id INTEGER NOT NULL,
        season TEXT NOT NULL,
        team_id INTEGER NOT NULL,
        paint_touches REAL,
        paint_touch_pts REAL,
        paint_touch_fgm REAL,
        paint_touch_fga REAL,
        paint_touch_fg_pct REAL,
        paint_touch_ftm REAL,
        paint_touch_fta REAL,
        paint_touch_ft_pct REAL,
        paint_touch_pass REAL,
        paint_touch_pass_pct REAL,
        paint_touch_ast REAL,
        paint_touch_ast_pct REAL,
        paint_touch_tov REAL,
        paint_touch_tov_pct REAL,
        paint_touch_pf REAL,
        paint_touch_pf_pct REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (player_id, season, team_id),
        FOREIGN KEY (player_id) REFERENCES Players(player_id),
        FOREIGN KEY (team_id) REFERENCES Teams(team_id)
    )
    ''')
    logger.info("PlayerSeasonPaintTouchStats table checked/created.")

def create_player_season_elbow_touch_stats_table(conn: sqlite3.Connection) -> None:
    """Create the PlayerSeasonElbowTouchStats table."""
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PlayerSeasonElbowTouchStats (
        player_id INTEGER NOT NULL,
        season TEXT NOT NULL,
        team_id INTEGER NOT NULL,
        elbow_touches REAL,
        elbow_touch_pts REAL,
        elbow_touch_fgm REAL,
        elbow_touch_fga REAL,
        elbow_touch_fg_pct REAL,
        elbow_touch_ftm REAL,
        elbow_touch_fta REAL,
        elbow_touch_ft_pct REAL,
        elbow_touch_pass REAL,
        elbow_touch_pass_pct REAL,
        elbow_touch_ast REAL,
        elbow_touch_ast_pct REAL,
        elbow_touch_tov REAL,
        elbow_touch_tov_pct REAL,
        elbow_touch_pf REAL,
        elbow_touch_pf_pct REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (player_id, season, team_id),
        FOREIGN KEY (player_id) REFERENCES Players(player_id),
        FOREIGN KEY (team_id) REFERENCES Teams(team_id)
    )
    ''')
    logger.info("PlayerSeasonElbowTouchStats table checked/created.")

def create_player_shot_chart_table(conn: sqlite3.Connection) -> None:
    """Create the PlayerShotChart table to store granular shot data for each player."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PlayerShotChart (
            shot_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            team_id INTEGER NOT NULL,
            game_id TEXT NOT NULL,
            season TEXT NOT NULL,
            action_type TEXT,
            event_type TEXT,
            shot_type TEXT,
            shot_zone_basic TEXT,
            shot_zone_area TEXT,
            shot_zone_range TEXT,
            shot_distance INTEGER,
            loc_x INTEGER,
            loc_y INTEGER,
            shot_made_flag INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES Players(player_id),
            FOREIGN KEY (team_id) REFERENCES Teams(team_id),
            FOREIGN KEY (game_id) REFERENCES Games(game_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_shot_chart_player_season ON PlayerShotChart(player_id, season)")
    logger.info("PlayerShotChart table checked/created.")

def create_player_season_skill_table(conn: sqlite3.Connection) -> None:
    """Create the PlayerSeasonSkill table for DARKO and other skill metrics."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PlayerSeasonSkill (
            player_id INTEGER NOT NULL,
            season TEXT NOT NULL,
            player_name TEXT,
            team_abbreviation TEXT,
            offensive_darko REAL,
            defensive_darko REAL,
            darko REAL,
            offensive_epm REAL,
            defensive_epm REAL,
            epm REAL,
            offensive_raptor REAL,
            defensive_raptor REAL,
            raptor REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (player_id, season),
            FOREIGN KEY (player_id) REFERENCES Players(player_id)
        )
    """)
    logger.info("PlayerSeasonSkill table checked/created.")


def create_all_tables(conn: sqlite3.Connection):
    """Create all tables in the database."""
    create_teams_table(conn)
    create_games_table(conn)
    create_players_table(conn)
    create_player_season_raw_stats_table(conn)
    create_player_season_advanced_stats_table(conn)
    create_player_season_shooting_distance_stats_table(conn)
    create_player_season_drive_stats_table(conn)
    create_player_season_hustle_stats_table(conn)
    create_player_season_opponent_shooting_stats_table(conn)
    create_player_season_tracking_touches_stats_table(conn)
    create_player_season_passing_stats_table(conn)
    create_player_season_catch_shoot_stats_table(conn)
    create_player_season_pull_up_stats_table(conn)
    create_player_lineup_stats_table(conn)
    create_player_season_rebounding_stats_table(conn)
    create_player_season_post_up_stats_table(conn)
    create_player_season_paint_touch_stats_table(conn)
    create_player_season_elbow_touch_stats_table(conn)
    create_player_shot_chart_table(conn)
    create_player_season_skill_table(conn)
    conn.commit()
    logger.info("All tables checked/created successfully.")


def main():
    """Main function to create all tables."""
    conn = get_db_connection()
    if conn:
        create_all_tables(conn)
        conn.close()


if __name__ == "__main__":
    main() 