"""
Mapping of the 48 canonical archetype metrics to their source population scripts.

This mapping is based on analysis of the existing population scripts and their
database table schemas.
"""

from canonical_metrics import CANONICAL_48_METRICS

# Mapping of metrics to their source scripts and database tables
METRIC_TO_SCRIPT_MAPPING = {
    # Basic shooting and efficiency metrics (from populate_player_season_stats.py)
    "FTPCT": {
        "script": "populate_player_season_stats.py",
        "table": "PlayerSeasonRawStats",
        "column": "free_throw_percentage",
        "api_endpoint": "leaguedashplayerstats",
        "api_measure_type": "Base"
    },
    "TSPCT": {
        "script": "populate_player_season_stats.py", 
        "table": "PlayerSeasonAdvancedStats",
        "column": "ts_pct",
        "api_endpoint": "leaguedashplayerstats",
        "api_measure_type": "Advanced"
    },
    "THPAr": {
        "script": "populate_player_season_stats.py",
        "table": "PlayerSeasonAdvancedStats", 
        "column": "fg3a_per_fga_pct",
        "api_endpoint": "leaguedashplayerstats",
        "api_measure_type": "Advanced"
    },
    "FTr": {
        "script": "populate_player_season_stats.py",
        "table": "PlayerSeasonAdvancedStats",
        "column": "fta_per_fga_pct", 
        "api_endpoint": "leaguedashplayerstats",
        "api_measure_type": "Advanced"
    },
    "TRBPCT": {
        "script": "populate_player_season_stats.py",
        "table": "PlayerSeasonAdvancedStats",
        "column": "reb_pct",
        "api_endpoint": "leaguedashplayerstats", 
        "api_measure_type": "Advanced"
    },
    "ASTPCT": {
        "script": "populate_player_season_stats.py",
        "table": "PlayerSeasonAdvancedStats",
        "column": "ast_pct",
        "api_endpoint": "leaguedashplayerstats",
        "api_measure_type": "Advanced"
    },
    
    # Shooting distance metrics (from populate_player_average_shot_distance.py)
    "AVGDIST": {
        "script": "populate_player_average_shot_distance.py",
        "table": "PlayerSeasonShotDistanceStats",
        "column": "avg_shot_distance",
        "api_endpoint": "leaguedashplayershotlocations",
        "api_measure_type": "Base"
    },
    "Zto3r": {
        "script": "populate_player_average_shot_distance.py",
        "table": "PlayerSeasonShotDistanceStats", 
        "column": "zone_to_3pt_range",
        "api_endpoint": "leaguedashplayershotlocations",
        "api_measure_type": "Base"
    },
    "THto10r": {
        "script": "populate_player_average_shot_distance.py",
        "table": "PlayerSeasonShotDistanceStats",
        "column": "three_to_ten_range",
        "api_endpoint": "leaguedashplayershotlocations",
        "api_measure_type": "Base"
    },
    "TENto16r": {
        "script": "populate_player_average_shot_distance.py",
        "table": "PlayerSeasonShotDistanceStats",
        "column": "ten_to_sixteen_range", 
        "api_endpoint": "leaguedashplayershotlocations",
        "api_measure_type": "Base"
    },
    "SIXTto3PTr": {
        "script": "populate_player_average_shot_distance.py",
        "table": "PlayerSeasonShotDistanceStats",
        "column": "sixteen_to_3pt_range",
        "api_endpoint": "leaguedashplayershotlocations",
        "api_measure_type": "Base"
    },
    
    # Physical attributes (from populate_player_physicals.py)
    "HEIGHT": {
        "script": "populate_player_physicals.py",
        "table": "Players",
        "column": "height",
        "api_endpoint": "commonplayerinfo",
        "api_measure_type": "Base"
    },
    "WINGSPAN": {
        "script": "populate_player_wingspan.py",
        "table": "Players", 
        "column": "wingspan",
        "api_endpoint": "commonplayerinfo",
        "api_measure_type": "Base"
    },
    
    # Touch and possession metrics (from populate_player_tracking_touches_stats.py)
    "FRNTCTTCH": {
        "script": "populate_player_tracking_touches_stats.py",
        "table": "PlayerSeasonTrackingTouchesStats",
        "column": "front_court_touches",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "Possessions"
    },
    "TOP": {
        "script": "populate_player_tracking_touches_stats.py",
        "table": "PlayerSeasonTrackingTouchesStats",
        "column": "time_of_possession",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "Possessions"
    },
    "AVGSECPERTCH": {
        "script": "populate_player_tracking_touches_stats.py",
        "table": "PlayerSeasonTrackingTouchesStats",
        "column": "avg_sec_per_touch",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "Possessions"
    },
    "AVGDRIBPERTCH": {
        "script": "populate_player_tracking_touches_stats.py",
        "table": "PlayerSeasonTrackingTouchesStats",
        "column": "avg_dribbles_per_touch",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "Possessions"
    },
    "ELBWTCH": {
        "script": "populate_player_elbow_touch_stats.py",
        "table": "PlayerSeasonElbowTouchStats",
        "column": "elbow_touches",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "ElbowTouch"
    },
    "POSTUPS": {
        "script": "populate_player_post_up_stats.py",
        "table": "PlayerSeasonPostUpStats",
        "column": "post_ups",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "PostTouch"
    },
    "PNTTOUCH": {
        "script": "populate_player_paint_touch_stats.py",
        "table": "PlayerSeasonPaintTouchStats",
        "column": "paint_touches",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "PaintTouch"
    },
    
    # Driving metrics (from populate_player_drive_stats.py)
    "DRIVES": {
        "script": "populate_player_drive_stats.py",
        "table": "PlayerSeasonDriveStats",
        "column": "drives",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "Drives"
    },
    "DRFGA": {
        "script": "populate_player_drive_stats.py",
        "table": "PlayerSeasonDriveStats",
        "column": "drive_fga",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "Drives"
    },
    "DRPTSPCT": {
        "script": "populate_player_drive_stats.py",
        "table": "PlayerSeasonDriveStats",
        "column": "drive_pts_pct",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "Drives"
    },
    "DRPASSPCT": {
        "script": "populate_player_drive_stats.py",
        "table": "PlayerSeasonDriveStats",
        "column": "drive_pass_pct",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "Drives"
    },
    "DRASTPCT": {
        "script": "populate_player_drive_stats.py",
        "table": "PlayerSeasonDriveStats",
        "column": "drive_ast_pct",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "Drives"
    },
    "DRTOVPCT": {
        "script": "populate_player_drive_stats.py",
        "table": "PlayerSeasonDriveStats",
        "column": "drive_tov_pct",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "Drives"
    },
    "DRPFPCT": {
        "script": "populate_player_drive_stats.py",
        "table": "PlayerSeasonDriveStats",
        "column": "drive_pf_pct",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "Drives"
    },
    "DRIMFGPCT": {
        "script": "populate_player_drive_stats.py",
        "table": "PlayerSeasonDriveStats",
        "column": "drive_fg_pct",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "Drives"
    },
    
    # Catch and shoot metrics (from populate_player_catch_shoot_stats.py)
    "CSFGA": {
        "script": "populate_player_catch_shoot_stats.py",
        "table": "PlayerSeasonCatchShootStats",
        "column": "cs_fga",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "CatchShoot"
    },
    "CS3PA": {
        "script": "populate_player_catch_shoot_stats.py",
        "table": "PlayerSeasonCatchShootStats",
        "column": "cs_3pa",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "CatchShoot"
    },
    
    # Passing metrics (from populate_player_passing_stats.py)
    "PASSESMADE": {
        "script": "populate_player_passing_stats.py",
        "table": "PlayerSeasonPassingStats",
        "column": "passes_made",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "Passing"
    },
    "SECAST": {
        "script": "populate_player_passing_stats.py",
        "table": "PlayerSeasonPassingStats",
        "column": "secondary_assists",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "Passing"
    },
    "POTAST": {
        "script": "populate_player_passing_stats.py",
        "table": "PlayerSeasonPassingStats",
        "column": "potential_assists",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "Passing"
    },
    
    # Pull-up shooting metrics (from populate_player_pull_up_stats.py)
    "PUFGA": {
        "script": "populate_player_pull_up_stats.py",
        "table": "PlayerSeasonPullUpStats",
        "column": "pu_fga",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "PullUpShot"
    },
    "PU3PA": {
        "script": "populate_player_pull_up_stats.py",
        "table": "PlayerSeasonPullUpStats",
        "column": "pu_3pa",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "PullUpShot"
    },
    
    # Post-up metrics (from populate_player_post_up_stats.py)
    "PSTUPFGA": {
        "script": "populate_player_post_up_stats.py",
        "table": "PlayerSeasonPostUpStats",
        "column": "post_up_fga",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "PostTouch"
    },
    "PSTUPPTSPCT": {
        "script": "populate_player_post_up_stats.py",
        "table": "PlayerSeasonPostUpStats",
        "column": "post_up_pts_pct",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "PostTouch"
    },
    "PSTUPPASSPCT": {
        "script": "populate_player_post_up_stats.py",
        "table": "PlayerSeasonPostUpStats",
        "column": "post_up_pass_pct",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "PostTouch"
    },
    "PSTUPASTPCT": {
        "script": "populate_player_post_up_stats.py",
        "table": "PlayerSeasonPostUpStats",
        "column": "post_up_ast_pct",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "PostTouch"
    },
    "PSTUPTOVPCT": {
        "script": "populate_player_post_up_stats.py",
        "table": "PlayerSeasonPostUpStats",
        "column": "post_up_tov_pct",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "PostTouch"
    },
    
    # Paint metrics (from populate_player_paint_touch_stats.py)
    "PNTTCHS": {
        "script": "populate_player_paint_touch_stats.py",
        "table": "PlayerSeasonPaintTouchStats",
        "column": "paint_touches",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "PaintTouch"
    },
    "PNTFGA": {
        "script": "populate_player_paint_touch_stats.py",
        "table": "PlayerSeasonPaintTouchStats",
        "column": "paint_fga",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "PaintTouch"
    },
    "PNTPTSPCT": {
        "script": "populate_player_paint_touch_stats.py",
        "table": "PlayerSeasonPaintTouchStats",
        "column": "paint_pts_pct",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "PaintTouch"
    },
    "PNTPASSPCT": {
        "script": "populate_player_paint_touch_stats.py",
        "table": "PlayerSeasonPaintTouchStats",
        "column": "paint_pass_pct",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "PaintTouch"
    },
    "PNTASTPCT": {
        "script": "populate_player_paint_touch_stats.py",
        "table": "PlayerSeasonPaintTouchStats",
        "column": "paint_ast_pct",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "PaintTouch"
    },
    "PNTTVPCT": {
        "script": "populate_player_paint_touch_stats.py",
        "table": "PlayerSeasonPaintTouchStats",
        "column": "paint_tov_pct",
        "api_endpoint": "leaguedashptstats",
        "api_measure_type": "PaintTouch"
    },
    
    # Defensive metric (from populate_player_hustle_stats.py)
    "AVGFGATTEMPTEDAGAINSTPERGAME": {
        "script": "populate_player_hustle_stats.py",
        "table": "PlayerSeasonHustleStats",
        "column": "avg_fg_attempted_against_per_game",
        "api_endpoint": "leaguedashplayerhustlestats",
        "api_measure_type": "Base"
    }
}

def get_script_for_metric(metric: str) -> dict:
    """Get the script and table information for a given metric."""
    return METRIC_TO_SCRIPT_MAPPING.get(metric, {})

def get_all_scripts() -> set:
    """Get all unique scripts that populate the 48 metrics."""
    return set(mapping["script"] for mapping in METRIC_TO_SCRIPT_MAPPING.values())

def get_all_api_endpoints() -> set:
    """Get all unique API endpoints used for the 48 metrics."""
    return set(mapping["api_endpoint"] for mapping in METRIC_TO_SCRIPT_MAPPING.values())

def validate_mapping_completeness():
    """Validate that all 48 metrics are mapped."""
    mapped_metrics = set(METRIC_TO_SCRIPT_MAPPING.keys())
    canonical_metrics = set(CANONICAL_48_METRICS)
    
    missing_metrics = canonical_metrics - mapped_metrics
    extra_metrics = mapped_metrics - canonical_metrics
    
    return {
        "complete": len(missing_metrics) == 0,
        "missing_metrics": list(missing_metrics),
        "extra_metrics": list(extra_metrics),
        "total_mapped": len(mapped_metrics),
        "total_canonical": len(canonical_metrics)
    }

if __name__ == "__main__":
    validation = validate_mapping_completeness()
    print(f"Mapping validation: {validation}")
    print(f"\nAll scripts: {get_all_scripts()}")
    print(f"\nAll API endpoints: {get_all_api_endpoints()}")
