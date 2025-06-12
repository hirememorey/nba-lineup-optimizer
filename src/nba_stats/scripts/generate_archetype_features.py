"""
This script queries the database for player-season stats, calculates the 48 features
required for archetype clustering as defined in the "Algorithmic NBA Player Acquisition" paper,
and stores the results in a new database table or CSV file.
"""

import sqlite3
import argparse
import logging
import pandas as pd
from pathlib import Path

# Add project root to sys.path to allow for relative imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


from nba_stats.db.connection import get_db_connection
from nba_stats.config import settings

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# List of 48 archetype features from the paper
# FTPCT, TSPCT, THPAr, FTr, TRBPCT, ASTPCT, AVGDIST, Zto3r, THto10r, TENto16r,
# SIXTto3PTr, HEIGHT, WINGSPAN, FRNTCTTCH, TOP, AVGSECPERTCH, AVGDRIBPERTCH,
# ELBWTCH, POSTUPS, PNTTOUCH, DRIVES, DRFGA, DRPTSPCT, DRPASSPCT, DRASTPCT,
# DRTOVPCT, DRPFPCT, DRIMFGPCT, CSFGA, CS3PA, PASSESMADE, SECAST, POTAST,
# PUFGA, PU3PA, PSTUPFGA, PSTUPPTSPCT, PSTUPPASSPCT, PSTUPASTPCT,
# PSTUPTOVPCT, PNTTCHS, PNTFGA, PNTPTSPCT, PNTPASSPCT, PNTASTPCT, PNTTVPCT,
# AVGFGATTEMPTEDAGAINSTPERGAME

def _get_feature_query(season: str, min_minutes: int) -> str:
    """Returns the SQL query to fetch all raw features from the database."""
    return f"""
    SELECT
        p.player_id,
        p.player_name,
        COALESCE(p.height, '0-0') as height,
        p.wingspan,
        -- Raw Stats
        rs.minutes_played,
        rs.games_played,
        COALESCE(rs.field_goals_attempted, 0) as field_goals_attempted,
        COALESCE(rs.three_pointers_attempted, 0) as three_pointers_attempted,
        COALESCE(rs.free_throws_attempted, 0) as free_throws_attempted,
        COALESCE(rs.free_throw_percentage, 0) AS FTPCT,
        COALESCE(rs.points, 0) AS points,
        -- Advanced Stats
        COALESCE(adv.true_shooting_percentage, 0) AS TSPCT,
        COALESCE(adv.rebound_percentage, 0) AS TRBPCT,
        COALESCE(adv.assist_percentage, 0) AS ASTPCT,
        -- Avg Shot Distance
        COALESCE(rs.avg_shot_distance, 0) AS AVGDIST,
        -- Shooting Distance Stats
        COALESCE(sds.restricted_area_fga, 0) as restricted_area_fga,
        COALESCE(sds.in_the_paint_non_ra_fga, 0) as in_the_paint_non_ra_fga,
        COALESCE(sds.mid_range_fga, 0) as mid_range_fga,
        -- Tracking Touches Stats
        COALESCE(tts.front_ct_touches, 0) AS FRNTCTTCH,
        COALESCE(tts.time_of_poss, 0) AS TOP,
        COALESCE(tts.avg_sec_per_touch, 0) AS AVGSECPERTCH,
        COALESCE(tts.avg_drib_per_touch, 0) AS AVGDRIBPERTCH,
        -- Elbow Touch Stats
        COALESCE(ets.elbow_touches, 0) AS ELBWTCH,
        -- Post Up Stats
        COALESCE(pus.possessions, 0) AS POSTUPS,
        COALESCE(pus.fga, 0) AS PSTUPFGA,
        COALESCE(pus.fg_pct, 0) AS PSTUPPTSPCT,
        COALESCE(pus.pass_frequency_pct, 0) AS PSTUPPASSPCT,
        COALESCE(pus.assist_pct, 0) AS PSTUPASTPCT,
        COALESCE(pus.tov_frequency_pct, 0) AS PSTUPTOVPCT,
        -- Paint Touch Stats
        COALESCE(pts.paint_touches, 0) AS PNTTOUCH,
        COALESCE(pts.paint_touch_fga, 0) AS PNTFGA,
        COALESCE(pts.paint_touch_fg_pct, 0) AS PNTPTSPCT,
        COALESCE(pts.paint_touch_pass_pct, 0) AS PNTPASSPCT,
        COALESCE(pts.paint_touch_ast_pct, 0) AS PNTASTPCT,
        COALESCE(pts.paint_touch_tov_pct, 0) AS PNTTVPCT,
        -- Drive Stats
        COALESCE(ds.drives, 0) AS DRIVES,
        COALESCE(ds.drive_fga, 0) AS DRFGA,
        COALESCE(ds.drive_fg_pct, 0) AS DRPTSPCT,
        COALESCE(ds.drive_pass_pct, 0) AS DRPASSPCT,
        COALESCE(ds.drive_ast_pct, 0) AS DRASTPCT,
        COALESCE(ds.drive_tov_pct, 0) AS DRTOVPCT,
        COALESCE(ds.drive_pf_pct, 0) AS DRPFPCT,
        -- Catch & Shoot Stats
        COALESCE(css.catch_shoot_fga, 0) AS CSFGA,
        COALESCE(css.catch_shoot_3pa, 0) AS CS3PA,
        -- Passing Stats
        COALESCE(passing.passes_made, 0) AS PASSESMADE,
        COALESCE(passing.secondary_assists, 0) AS SECAST,
        COALESCE(passing.potential_assists, 0) AS POTAST,
        -- Pull Up Stats
        COALESCE(pull_up.pull_up_fga, 0) AS PUFGA,
        COALESCE(pull_up.pull_up_3pa, 0) AS PU3PA,
        -- Opponent Shooting
        COALESCE(oss.opp_fga_lt_5ft, 0) as opp_fga_lt_5ft,
        COALESCE(oss.opp_fga_5_9ft, 0) as opp_fga_5_9ft,
        COALESCE(oss.opp_fga_10_14ft, 0) as opp_fga_10_14ft,
        COALESCE(oss.opp_fga_15_19ft, 0) as opp_fga_15_19ft,
        COALESCE(oss.opp_fga_20_24ft, 0) as opp_fga_20_24ft,
        COALESCE(oss.opp_fga_25_29ft, 0) as opp_fga_25_29ft,
        p.created_at,
        p.updated_at
    FROM
        Players p
    JOIN
        PlayerSeasonRawStats rs ON p.player_id = rs.player_id AND rs.season = '{season}'
    LEFT JOIN
        PlayerSeasonAdvancedStats adv ON p.player_id = adv.player_id AND adv.season = '{season}'
    LEFT JOIN
        PlayerSeasonShootingDistanceStats sds ON p.player_id = sds.player_id AND sds.season = '{season}'
    LEFT JOIN
        PlayerSeasonTrackingTouchesStats tts ON p.player_id = tts.player_id AND tts.season = '{season}'
    LEFT JOIN
        PlayerSeasonElbowTouchStats ets ON p.player_id = ets.player_id AND ets.season = '{season}'
    LEFT JOIN
        PlayerSeasonPostUpStats pus ON p.player_id = pus.player_id AND pus.season = '{season}'
    LEFT JOIN
        PlayerSeasonPaintTouchStats pts ON p.player_id = pts.player_id AND pts.season = '{season}'
    LEFT JOIN
        PlayerSeasonDriveStats ds ON p.player_id = ds.player_id AND ds.season = '{season}'
    LEFT JOIN
        PlayerSeasonCatchAndShootStats css ON p.player_id = css.player_id AND css.season = '{season}'
    LEFT JOIN
        PlayerSeasonPassingStats passing ON p.player_id = passing.player_id AND passing.season = '{season}'
    LEFT JOIN
        PlayerSeasonPullUpStats pull_up ON p.player_id = pull_up.player_id AND pull_up.season = '{season}'
    LEFT JOIN
        PlayerSeasonOpponentShootingStats oss ON p.player_id = oss.player_id AND oss.season = '{season}'
    WHERE
        rs.minutes_played >= {min_minutes}
    """


def _convert_height_to_inches(height: str) -> float | None:
    """Converts height string 'feet-inches' to inches."""
    if not height or '-' not in height:
        return None
    try:
        feet, inches = map(int, height.split('-'))
        return feet * 12 + inches
    except (ValueError, TypeError):
        return None


def generate_features(season: str):
    """
    Queries the database, calculates the 48 archetype features,
    and saves them to the PlayerArchetypeFeatures table.
    """
    conn = get_db_connection()
    if not conn:
        return

    try:
        logger.info(f"Generating archetype features for season: {season}")

        query = _get_feature_query(season, settings.MIN_MINUTES_THRESHOLD)
        features_df = pd.read_sql_query(query, conn)

        logger.info(f"Successfully fetched raw features for {len(features_df)} players.")

        # --- Feature Calculations & Cleaning ---

        # Convert height to inches
        features_df['HEIGHT'] = features_df['height'].apply(_convert_height_to_inches)

        # Calculate rate stats (handle division by zero)
        features_df['THPAr'] = features_df.apply(lambda row: row['three_pointers_attempted'] / row['field_goals_attempted'] if row['field_goals_attempted'] > 0 else 0, axis=1)
        features_df['FTr'] = features_df.apply(lambda row: row['free_throws_attempted'] / row['field_goals_attempted'] if row['field_goals_attempted'] > 0 else 0, axis=1)
        
        # ---- NEW: back-fill TSPCT if missing ----
        def _calc_tspct(row):
            denom = (row['field_goals_attempted'] + 0.44 * row['free_throws_attempted'])
            if denom > 0:
                return row['points'] / (2 * denom)
            return 0
        mask_missing_tspct = (features_df['TSPCT'] == 0) | (features_df['TSPCT'].isna())
        features_df.loc[mask_missing_tspct, 'TSPCT'] = features_df[mask_missing_tspct].apply(_calc_tspct, axis=1)
        # ---- END NEW ----
        
        # Calculate shooting ratios
        features_df['Zto3r'] = features_df.apply(lambda row: row['restricted_area_fga'] / row['field_goals_attempted'] if row['field_goals_attempted'] > 0 else 0, axis=1)
        # Note: The paper's shooting range names (e.g., THto10r) don't perfectly match NBA.com's.
        # We are using `in_the_paint_non_ra_fga` and `mid_range_fga` as available proxies.
        features_df['THto10r'] = features_df.apply(lambda row: row['in_the_paint_non_ra_fga'] / row['field_goals_attempted'] if row['field_goals_attempted'] > 0 else 0, axis=1)
        features_df['TENto16r'] = features_df.apply(lambda row: row['mid_range_fga'] / row['field_goals_attempted'] if row['field_goals_attempted'] > 0 else 0, axis=1)
        
        # This feature is a bit ambiguous in the paper. For now, we will set it to 0 as we cannot accurately calculate it.
        features_df['SIXTto3PTr'] = 0.0

        # Calculate AVGFGATTEMPTEDAGAINSTPERGAME
        opp_fga_cols = ['opp_fga_lt_5ft', 'opp_fga_5_9ft', 'opp_fga_10_14ft', 'opp_fga_15_19ft', 'opp_fga_20_24ft', 'opp_fga_25_29ft']
        features_df['AVGFGATTEMPTEDAGAINSTPERGAME'] = features_df.apply(
            lambda row: sum(row[c] for c in opp_fga_cols) / row['games_played'] if row['games_played'] > 0 else 0,
            axis=1
        )

        # Handle PNTTCHS (assumed to be same as PNTTOUCH) and DRIMFGPCT (missing data)
        features_df['PNTTCHS'] = features_df['PNTTOUCH']
        features_df['DRIMFGPCT'] = 0.0 # Data not available in current tables

        # --- Final Feature Selection & Cleaning ---
        
        feature_columns = [
            'FTPCT', 'TSPCT', 'THPAr', 'FTr', 'TRBPCT', 'ASTPCT', 'AVGDIST', 'Zto3r',
            'THto10r', 'TENto16r', 'SIXTto3PTr', 'HEIGHT', 'WINGSPAN', 'FRNTCTTCH',
            'TOP', 'AVGSECPERTCH', 'AVGDRIBPERTCH', 'ELBWTCH', 'POSTUPS', 'PNTTOUCH',
            'DRIVES', 'DRFGA', 'DRPTSPCT', 'DRPASSPCT', 'DRASTPCT', 'DRTOVPCT',
            'DRPFPCT', 'DRIMFGPCT', 'CSFGA', 'CS3PA', 'PASSESMADE', 'SECAST',
            'POTAST', 'PUFGA', 'PU3PA', 'PSTUPFGA', 'PSTUPPTSPCT', 'PSTUPPASSPCT',
            'PSTUPASTPCT', 'PSTUPTOVPCT', 'PNTTCHS', 'PNTFGA', 'PNTPTSPCT',
            'PNTPASSPCT', 'PNTASTPCT', 'PNTTVPCT', 'AVGFGATTEMPTEDAGAINSTPERGAME'
        ]

        # Ensure all feature columns exist, fill missing with 0
        for col in feature_columns:
            if col not in features_df.columns:
                features_df[col] = 0.0
        
        final_features_df = features_df[['player_id'] + feature_columns].copy()
        final_features_df['season'] = season

        # ---- NEW: Ensure correct dtypes ----
        # Cast every feature column to float explicitly so SQLite stores them as REAL
        for col in feature_columns:
            final_features_df[col] = final_features_df[col].astype(float)
        # player_id integer and season text types
        final_features_df['player_id'] = final_features_df['player_id'].astype(int)
        final_features_df['season'] = final_features_df['season'].astype(str)
        # ---- END NEW ----

        # All columns should now be populated from the query, so imputation is a fallback.
        for col in feature_columns:
            if final_features_df[col].isnull().any():
                logger.warning(f"Found unexpected nulls in column '{col}'. Imputing with 0.")
                final_features_df[col] = final_features_df[col].fillna(0)

        # --- Save to Database ---
        final_features_df.to_sql('PlayerArchetypeFeatures', conn, if_exists='replace', index=False)
        logger.info(f"Successfully generated and saved archetype features for {len(final_features_df)} players.")

    except (pd.errors.DatabaseError, sqlite3.Error) as e:
        logger.error(f"A database error occurred: {e}")
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description="Generate Player Archetype Features.")
    parser.add_argument(
        "--season", 
        type=str, 
        default=settings.SEASON_ID,
        help=f"The season to generate features for (e.g., '{settings.SEASON_ID}')."
    )
    args = parser.parse_args()

    generate_features(season=args.season)

if __name__ == "__main__":
    main() 