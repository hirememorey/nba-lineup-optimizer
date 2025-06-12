import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_PATH = 'nba_data.db'  # Make sure this matches the path used by your fetcher

TABLE_DEFINITIONS = [
    """
    CREATE TABLE IF NOT EXISTS player_tracking_driving (
        player_id INTEGER,
        player_name TEXT,
        team_id INTEGER,
        team_abbreviation TEXT,
        gp INTEGER,
        w INTEGER,
        l INTEGER,
        min REAL,
        drives INTEGER,
        drive_fgm REAL,
        drive_fga REAL,
        drive_fg_pct REAL,
        drive_ftm REAL,
        drive_fta REAL,
        drive_ft_pct REAL,
        drive_pts REAL,
        drive_pts_pct REAL,
        drive_passes REAL,
        drive_pass_pct REAL,
        drive_ast REAL,
        drive_ast_pct REAL,
        drive_tov REAL,
        drive_tov_pct REAL,
        drive_pf REAL,
        drive_pf_pct REAL,
        season TEXT,
        per_mode TEXT,
        measure_type TEXT,
        PRIMARY KEY (player_id, season, per_mode, measure_type)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS player_tracking_passing (
        player_id INTEGER,
        player_name TEXT,
        team_id INTEGER,
        team_abbreviation TEXT,
        gp INTEGER,
        w INTEGER,
        l INTEGER,
        min REAL,
        passes_made REAL,
        passes_received REAL,
        ast REAL,
        secondary_ast REAL,
        potential_ast REAL,
        ast_pts_created REAL,
        ast_adj REAL,
        ast_to_pass_pct REAL,
        ast_to_pass_pct_adj REAL,
        season TEXT,
        per_mode TEXT,
        measure_type TEXT,
        PRIMARY KEY (player_id, season, per_mode, measure_type)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS player_tracking_elbow_touch (
        player_id INTEGER,
        player_name TEXT,
        team_id INTEGER,
        team_abbreviation TEXT,
        gp INTEGER,
        w INTEGER,
        l INTEGER,
        min REAL,
        touches REAL,
        elbow_touch_fgm REAL,
        elbow_touch_fga REAL,
        elbow_touch_fg_pct REAL,
        elbow_touch_ftm REAL,
        elbow_touch_fta REAL,
        elbow_touch_ft_pct REAL,
        elbow_touch_pts REAL,
        elbow_touch_passes REAL,
        elbow_touch_pass_pct REAL,
        elbow_touch_ast REAL,
        elbow_touch_ast_pct REAL,
        elbow_touch_tov REAL,
        elbow_touch_tov_pct REAL,
        elbow_touch_pf REAL,
        elbow_touch_pf_pct REAL,
        season TEXT,
        per_mode TEXT,
        measure_type TEXT,
        PRIMARY KEY (player_id, season, per_mode, measure_type)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS player_tracking_post_touch (
        player_id INTEGER,
        player_name TEXT,
        team_id INTEGER,
        team_abbreviation TEXT,
        gp INTEGER,
        w INTEGER,
        l INTEGER,
        min REAL,
        touches REAL,
        post_touch_fgm REAL,
        post_touch_fga REAL,
        post_touch_fg_pct REAL,
        post_touch_ftm REAL,
        post_touch_fta REAL,
        post_touch_ft_pct REAL,
        post_touch_pts REAL,
        post_touch_passes REAL,
        post_touch_pass_pct REAL,
        post_touch_ast REAL,
        post_touch_ast_pct REAL,
        post_touch_tov REAL,
        post_touch_tov_pct REAL,
        post_touch_pf REAL,
        post_touch_pf_pct REAL,
        season TEXT,
        per_mode TEXT,
        measure_type TEXT,
        PRIMARY KEY (player_id, season, per_mode, measure_type)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS player_tracking_paint_touch (
        player_id INTEGER,
        player_name TEXT,
        team_id INTEGER,
        team_abbreviation TEXT,
        gp INTEGER,
        w INTEGER,
        l INTEGER,
        min REAL,
        touches REAL,
        paint_touch_fgm REAL,
        paint_touch_fga REAL,
        paint_touch_fg_pct REAL,
        paint_touch_ftm REAL,
        paint_touch_fta REAL,
        paint_touch_ft_pct REAL,
        paint_touch_pts REAL,
        paint_touch_passes REAL,
        paint_touch_pass_pct REAL,
        paint_touch_ast REAL,
        paint_touch_ast_pct REAL,
        paint_touch_tov REAL,
        paint_touch_tov_pct REAL,
        paint_touch_pf REAL,
        paint_touch_pf_pct REAL,
        season TEXT,
        per_mode TEXT,
        measure_type TEXT,
        PRIMARY KEY (player_id, season, per_mode, measure_type)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS player_tracking_catch_shoot (
        player_id INTEGER,
        player_name TEXT,
        team_id INTEGER,
        team_abbreviation TEXT,
        gp INTEGER,
        w INTEGER,
        l INTEGER,
        min REAL,
        catch_sh_fgm REAL,
        catch_sh_fga REAL,
        catch_sh_fg_pct REAL,
        catch_sh_fg3m REAL,
        catch_sh_fg3a REAL,
        catch_sh_fg3_pct REAL,
        catch_sh_efg_pct REAL,
        catch_sh_pts REAL,
        season TEXT,
        per_mode TEXT,
        measure_type TEXT,
        PRIMARY KEY (player_id, season, per_mode, measure_type)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS player_tracking_pull_up_shot (
        player_id INTEGER,
        player_name TEXT,
        team_id INTEGER,
        team_abbreviation TEXT,
        gp INTEGER,
        w INTEGER,
        l INTEGER,
        min REAL,
        pull_up_fgm REAL,
        pull_up_fga REAL,
        pull_up_fg_pct REAL,
        pull_up_fg3m REAL,
        pull_up_fg3a REAL,
        pull_up_fg3_pct REAL,
        pull_up_efg_pct REAL,
        pull_up_pts REAL,
        season TEXT,
        per_mode TEXT,
        measure_type TEXT,
        PRIMARY KEY (player_id, season, per_mode, measure_type)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS player_tracking_speeddistance (
        player_id INTEGER,
        player_name TEXT,
        team_id INTEGER,
        team_abbreviation TEXT,
        gp INTEGER,
        w INTEGER,
        l INTEGER,
        min REAL,
        min1 REAL,
        dist_feet REAL,
        dist_miles REAL,
        dist_miles_off REAL,
        dist_miles_def REAL,
        avg_speed REAL,
        avg_speed_off REAL,
        avg_speed_def REAL,
        season TEXT,
        per_mode TEXT,
        measure_type TEXT,
        PRIMARY KEY (player_id, season, per_mode, measure_type)
    );
    """
]

def create_tables():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        for table_sql in TABLE_DEFINITIONS:
            cursor.execute(table_sql)
        
        # Attempt to add 'min1' column to player_tracking_speeddistance if it doesn't exist
        try:
            logging.info("Checking for 'min1' column in player_tracking_speeddistance...")
            cursor.execute("PRAGMA table_info(player_tracking_speeddistance);")
            columns = [info[1] for info in cursor.fetchall()]
            if 'min1' not in columns:
                logging.info("'min1' column not found in player_tracking_speeddistance. Adding it...")
                cursor.execute("ALTER TABLE player_tracking_speeddistance ADD COLUMN min1 REAL;")
                logging.info("Successfully added 'min1' column to player_tracking_speeddistance.")
            else:
                logging.info("'min1' column already exists in player_tracking_speeddistance.")
        except sqlite3.Error as e:
            logging.warning(f"Could not alter player_tracking_speeddistance to add min1 (table might not exist yet or other error): {e}")
            # This might happen if the table itself doesn't exist yet, which is fine as CREATE TABLE will handle it.

        conn.commit()
        logging.info(f"Successfully created/verified tables in {DB_PATH}")
    except sqlite3.Error as e:
        logging.error(f"Database error while creating tables: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    create_tables() 