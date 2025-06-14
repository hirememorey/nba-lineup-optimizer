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
        p.height,
        p.wingspan AS WINGSPAN,
        rs.minutes_played,
        rs.games_played,
        rs.field_goals_attempted,
        rs.three_pointers_attempted,
        rs.free_throws_attempted,
        rs.free_throw_percentage AS FTPCT,
        rs.points,
        adv.true_shooting_percentage AS TSPCT,
        adv.rebound_percentage AS TRBPCT,
        adv.assist_percentage AS ASTPCT,
        rs.avg_shot_distance AS AVGDIST,
        tts.front_ct_touches AS FRNTCTTCH,
        tts.time_of_poss AS TOP,
        tts.avg_sec_per_touch AS AVGSECPERTCH,
        tts.avg_drib_per_touch AS AVGDRIBPERTCH,
        ets.elbow_touches AS ELBWTCH,
        pus.possessions AS POSTUPS,
        pus.fga AS PSTUPFGA,
        pus.fg_pct AS PSTUPPTSPCT,
        pus.pass_frequency_pct AS PSTUPPASSPCT,
        pus.assist_pct AS PSTUPASTPCT,
        pus.tov_frequency_pct AS PSTUPTOVPCT,
        pts.paint_touches AS PNTTOUCH,
        pts.paint_touch_fga AS PNTFGA,
        pts.paint_touch_fg_pct AS PNTPTSPCT,
        pts.paint_touch_pass_pct AS PNTPASSPCT,
        pts.paint_touch_ast_pct AS PNTASTPCT,
        pts.paint_touch_tov_pct AS PNTTVPCT,
        ds.drives AS DRIVES,
        ds.drive_fga AS DRFGA,
        ds.drive_fg_pct AS DRPTSPCT,
        ds.drive_pass_pct AS DRPASSPCT,
        ds.drive_ast_pct AS DRASTPCT,
        ds.drive_tov_pct AS DRTOVPCT,
        ds.drive_pf_pct AS DRPFPCT,
        css.catch_shoot_fga AS CSFGA,
        css.catch_shoot_3pa AS CS3PA,
        passing.passes_made AS PASSESMADE,
        passing.secondary_assists AS SECAST,
        passing.potential_assists AS POTAST,
        pull_up.pull_up_fga AS PUFGA,
        pull_up.pull_up_3pa AS PU3PA,
        oss.opp_fgm_lt_5ft,
        oss.opp_fga_lt_5ft,
        oss.opp_fga_5_9ft,
        oss.opp_fga_10_14ft,
        oss.opp_fga_15_19ft,
        oss.opp_fga_20_24ft,
        oss.opp_fga_25_29ft,
        sc.shots_0_3_ft,
        sc.shots_3_10_ft,
        sc.shots_10_16_ft,
        sc.shots_16_3pt_ft
    FROM
        Players p
    INNER JOIN
        PlayerSeasonRawStats rs ON p.player_id = rs.player_id AND rs.season = '{season}' AND rs.minutes_played >= {min_minutes}
    LEFT JOIN
        PlayerSeasonAdvancedStats adv ON p.player_id = adv.player_id AND adv.season = rs.season
    LEFT JOIN
        PlayerSeasonTrackingTouchesStats tts ON p.player_id = tts.player_id AND tts.season = rs.season
    LEFT JOIN
        PlayerSeasonElbowTouchStats ets ON p.player_id = ets.player_id AND ets.season = rs.season
    LEFT JOIN
        PlayerSeasonPostUpStats pus ON p.player_id = pus.player_id AND pus.season = rs.season
    LEFT JOIN
        PlayerSeasonPaintTouchStats pts ON p.player_id = pts.player_id AND pts.season = rs.season
    LEFT JOIN
        PlayerSeasonDriveStats ds ON p.player_id = ds.player_id AND ds.season = rs.season
    LEFT JOIN
        PlayerSeasonCatchAndShootStats css ON p.player_id = css.player_id AND css.season = rs.season
    LEFT JOIN
        PlayerSeasonPassingStats passing ON p.player_id = passing.player_id AND passing.season = rs.season
    LEFT JOIN
        PlayerSeasonPullUpStats pull_up ON p.player_id = pull_up.player_id AND pull_up.season = rs.season
    LEFT JOIN
        PlayerSeasonOpponentShootingStats oss ON p.player_id = oss.player_id AND oss.season = rs.season
    LEFT JOIN (
        SELECT
            player_id,
            season,
            SUM(CASE WHEN shot_distance <= 3 THEN 1 ELSE 0 END) AS shots_0_3_ft,
            SUM(CASE WHEN shot_distance > 3 AND shot_distance <= 10 THEN 1 ELSE 0 END) AS shots_3_10_ft,
            SUM(CASE WHEN shot_distance > 10 AND shot_distance <= 16 THEN 1 ELSE 0 END) AS shots_10_16_ft,
            SUM(CASE WHEN shot_distance > 16 AND shot_type = '2PT Field Goal' THEN 1 ELSE 0 END) AS shots_16_3pt_ft
        FROM
            PlayerShotChart
        WHERE
            season = '{season}'
        GROUP BY
            player_id, season
    ) sc ON p.player_id = sc.player_id AND rs.season = sc.season;
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
    with get_db_connection() as conn:
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
        
        # Calculate shooting ratios from PlayerShotChart data
        features_df['Zto3r'] = features_df.apply(lambda row: row['shots_0_3_ft'] / row['field_goals_attempted'] if row['field_goals_attempted'] > 0 else 0, axis=1)
        features_df['THto10r'] = features_df.apply(lambda row: row['shots_3_10_ft'] / row['field_goals_attempted'] if row['field_goals_attempted'] > 0 else 0, axis=1)
        features_df['TENto16r'] = features_df.apply(lambda row: row['shots_10_16_ft'] / row['field_goals_attempted'] if row['field_goals_attempted'] > 0 else 0, axis=1)
        features_df['SIXTto3PTr'] = features_df.apply(lambda row: row['shots_16_3pt_ft'] / row['field_goals_attempted'] if row['field_goals_attempted'] > 0 else 0, axis=1)

        # Calculate AVGFGATTEMPTEDAGAINSTPERGAME
        opp_fga_cols = ['opp_fga_lt_5ft', 'opp_fga_5_9ft', 'opp_fga_10_14ft', 'opp_fga_15_19ft', 'opp_fga_20_24ft', 'opp_fga_25_29ft']
        features_df['AVGFGATTEMPTEDAGAINSTPERGAME'] = features_df.apply(
            lambda row: sum(row[c] if row[c] is not None else 0 for c in opp_fga_cols) / row['games_played'] if row['games_played'] > 0 else 0,
            axis=1
        )

        # Handle PNTTCHS (assumed to be same as PNTTOUCH)
        features_df['PNTTCHS'] = features_df['PNTTOUCH']
        
        # Calculate DRIMFGPCT
        features_df['DRIMFGPCT'] = features_df.apply(
            lambda row: row['opp_fgm_lt_5ft'] / row['opp_fga_lt_5ft'] if row['opp_fga_lt_5ft'] and row['opp_fga_lt_5ft'] > 0 else 0.0,
            axis=1
        )

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