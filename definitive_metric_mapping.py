"""
Definitive Metric Mapping

This module provides the authoritative mapping between the 48 canonical archetype
metrics and their actual API sources, based on comprehensive API reconnaissance.
"""

import json
from typing import Dict, List, Optional, Tuple
from canonical_metrics import CANONICAL_48_METRICS

# Load the API reconnaissance results
with open('api_reconnaissance_results.json', 'r') as f:
    api_data = json.load(f)

# Extract all available columns from the reconnaissance
all_columns = set()
for endpoint_data in api_data['api_column_map'].values():
    all_columns.update(endpoint_data)

# Create the definitive mapping based on actual API column names
DEFINITIVE_METRIC_MAPPING = {
    # Basic shooting and efficiency metrics
    "FTPCT": {
        "canonical_name": "Free Throw Percentage",
        "api_source": "leaguedashplayerstats",
        "api_column": "FT_PCT",
        "endpoint_params": {"MeasureType": "Base", "PerMode": "PerGame", "SeasonType": "Regular Season"},
        "data_type": "percentage",
        "required": True,
        "notes": "Direct mapping from base stats"
    },
    "TSPCT": {
        "canonical_name": "True Shooting Percentage", 
        "api_source": "leaguedashplayerstats",
        "api_column": "TS_PCT",
        "endpoint_params": {"MeasureType": "Advanced", "PerMode": "PerGame", "SeasonType": "Regular Season"},
        "data_type": "percentage",
        "required": True,
        "notes": "Direct mapping from advanced stats"
    },
    "THPAr": {
        "canonical_name": "Three Point Attempt Rate",
        "api_source": "leaguedashplayerstats", 
        "api_column": "FGA_PG",  # Will need to calculate as 3PA/FGA
        "endpoint_params": {"MeasureType": "Advanced", "PerMode": "PerGame", "SeasonType": "Regular Season"},
        "data_type": "calculated",
        "required": True,
        "notes": "Calculate as 3PA/FGA from base stats"
    },
    "FTr": {
        "canonical_name": "Free Throw Rate",
        "api_source": "leaguedashplayerstats",
        "api_column": "FTA",  # Will need to calculate as FTA/FGA
        "endpoint_params": {"MeasureType": "Base", "PerMode": "PerGame", "SeasonType": "Regular Season"},
        "data_type": "calculated", 
        "required": True,
        "notes": "Calculate as FTA/FGA from base stats"
    },
    "TRBPCT": {
        "canonical_name": "Total Rebound Percentage",
        "api_source": "leaguedashplayerstats",
        "api_column": "REB_PCT",
        "endpoint_params": {"MeasureType": "Advanced", "PerMode": "PerGame", "SeasonType": "Regular Season"},
        "data_type": "percentage",
        "required": True,
        "notes": "Direct mapping from advanced stats"
    },
    "ASTPCT": {
        "canonical_name": "Assist Percentage",
        "api_source": "leaguedashplayerstats",
        "api_column": "AST_PCT",
        "endpoint_params": {"MeasureType": "Advanced", "PerMode": "PerGame", "SeasonType": "Regular Season"},
        "data_type": "percentage",
        "required": True,
        "notes": "Direct mapping from advanced stats"
    },
    
    # Shooting distance metrics - These appear to be missing from current API
    "AVGDIST": {
        "canonical_name": "Average Shot Distance",
        "api_source": "MISSING",
        "api_column": "MISSING",
        "endpoint_params": {},
        "data_type": "missing",
        "required": True,
        "notes": "NOT FOUND in current API reconnaissance - needs investigation"
    },
    "Zto3r": {
        "canonical_name": "Zone to 3-Point Range",
        "api_source": "MISSING", 
        "api_column": "MISSING",
        "endpoint_params": {},
        "data_type": "missing",
        "required": True,
        "notes": "NOT FOUND in current API reconnaissance - needs investigation"
    },
    "THto10r": {
        "canonical_name": "Three to Ten Range",
        "api_source": "MISSING",
        "api_column": "MISSING", 
        "endpoint_params": {},
        "data_type": "missing",
        "required": True,
        "notes": "NOT FOUND in current API reconnaissance - needs investigation"
    },
    "TENto16r": {
        "canonical_name": "Ten to Sixteen Range",
        "api_source": "MISSING",
        "api_column": "MISSING",
        "endpoint_params": {},
        "data_type": "missing", 
        "required": True,
        "notes": "NOT FOUND in current API reconnaissance - needs investigation"
    },
    "SIXTto3PTr": {
        "canonical_name": "Sixteen to 3-Point Range",
        "api_source": "MISSING",
        "api_column": "MISSING",
        "endpoint_params": {},
        "data_type": "missing",
        "required": True,
        "notes": "NOT FOUND in current API reconnaissance - needs investigation"
    },
    
    # Physical attributes
    "HEIGHT": {
        "canonical_name": "Player Height",
        "api_source": "commonplayerinfo",
        "api_column": "HEIGHT",
        "endpoint_params": {},
        "data_type": "string",
        "required": True,
        "notes": "Direct mapping from player info"
    },
    "WINGSPAN": {
        "canonical_name": "Player Wingspan", 
        "api_source": "MISSING",
        "api_column": "MISSING",
        "endpoint_params": {},
        "data_type": "missing",
        "required": True,
        "notes": "NOT FOUND in current API reconnaissance - may need draft combine data"
    },
    
    # Touch and possession metrics
    "FRNTCTTCH": {
        "canonical_name": "Front Court Touches",
        "api_source": "leaguedashptstats",
        "api_column": "FRONT_CT_TOUCHES",
        "endpoint_params": {"PtMeasureType": "Possessions", "PerMode": "PerGame"},
        "data_type": "count",
        "required": True,
        "notes": "Direct mapping from possessions tracking"
    },
    "TOP": {
        "canonical_name": "Time of Possession",
        "api_source": "leaguedashptstats",
        "api_column": "TIME_OF_POSS",
        "endpoint_params": {"PtMeasureType": "Possessions", "PerMode": "PerGame"},
        "data_type": "time",
        "required": True,
        "notes": "Direct mapping from possessions tracking"
    },
    "AVGSECPERTCH": {
        "canonical_name": "Average Seconds Per Touch",
        "api_source": "leaguedashptstats",
        "api_column": "AVG_SEC_PER_TOUCH",
        "endpoint_params": {"PtMeasureType": "Possessions", "PerMode": "PerGame"},
        "data_type": "time",
        "required": True,
        "notes": "Direct mapping from possessions tracking"
    },
    "AVGDRIBPERTCH": {
        "canonical_name": "Average Dribbles Per Touch",
        "api_source": "leaguedashptstats",
        "api_column": "AVG_DRIB_PER_TOUCH",
        "endpoint_params": {"PtMeasureType": "Possessions", "PerMode": "PerGame"},
        "data_type": "count",
        "required": True,
        "notes": "Direct mapping from possessions tracking"
    },
    "ELBWTCH": {
        "canonical_name": "Elbow Touches",
        "api_source": "leaguedashptstats",
        "api_column": "ELBOW_TOUCHES",
        "endpoint_params": {"PtMeasureType": "ElbowTouch", "PerMode": "PerGame"},
        "data_type": "count",
        "required": True,
        "notes": "Direct mapping from elbow touch tracking"
    },
    "POSTUPS": {
        "canonical_name": "Post-Ups",
        "api_source": "leaguedashptstats",
        "api_column": "POST_TOUCHES",
        "endpoint_params": {"PtMeasureType": "PostTouch", "PerMode": "PerGame"},
        "data_type": "count",
        "required": True,
        "notes": "Direct mapping from post touch tracking"
    },
    "PNTTOUCH": {
        "canonical_name": "Paint Touches",
        "api_source": "leaguedashptstats",
        "api_column": "PAINT_TOUCHES",
        "endpoint_params": {"PtMeasureType": "PaintTouch", "PerMode": "PerGame"},
        "data_type": "count",
        "required": True,
        "notes": "Direct mapping from paint touch tracking"
    },
    
    # Driving metrics
    "DRIVES": {
        "canonical_name": "Drives",
        "api_source": "leaguedashptstats",
        "api_column": "DRIVES",
        "endpoint_params": {"PtMeasureType": "Drives", "PerMode": "PerGame"},
        "data_type": "count",
        "required": True,
        "notes": "Direct mapping from drives tracking"
    },
    "DRFGA": {
        "canonical_name": "Drive Field Goal Attempts",
        "api_source": "leaguedashptstats",
        "api_column": "DRIVE_FGA",
        "endpoint_params": {"PtMeasureType": "Drives", "PerMode": "PerGame"},
        "data_type": "count",
        "required": True,
        "notes": "Direct mapping from drives tracking"
    },
    "DRPTSPCT": {
        "canonical_name": "Drive Points Percentage",
        "api_source": "leaguedashptstats",
        "api_column": "DRIVE_PTS_PCT",
        "endpoint_params": {"PtMeasureType": "Drives", "PerMode": "PerGame"},
        "data_type": "percentage",
        "required": True,
        "notes": "Direct mapping from drives tracking"
    },
    "DRPASSPCT": {
        "canonical_name": "Drive Pass Percentage",
        "api_source": "leaguedashptstats",
        "api_column": "DRIVE_PASSES_PCT",
        "endpoint_params": {"PtMeasureType": "Drives", "PerMode": "PerGame"},
        "data_type": "percentage",
        "required": True,
        "notes": "Direct mapping from drives tracking"
    },
    "DRASTPCT": {
        "canonical_name": "Drive Assist Percentage",
        "api_source": "leaguedashptstats",
        "api_column": "DRIVE_AST_PCT",
        "endpoint_params": {"PtMeasureType": "Drives", "PerMode": "PerGame"},
        "data_type": "percentage",
        "required": True,
        "notes": "Direct mapping from drives tracking"
    },
    "DRTOVPCT": {
        "canonical_name": "Drive Turnover Percentage",
        "api_source": "leaguedashptstats",
        "api_column": "DRIVE_TOV_PCT",
        "endpoint_params": {"PtMeasureType": "Drives", "PerMode": "PerGame"},
        "data_type": "percentage",
        "required": True,
        "notes": "Direct mapping from drives tracking"
    },
    "DRPFPCT": {
        "canonical_name": "Drive Personal Foul Percentage",
        "api_source": "leaguedashptstats",
        "api_column": "DRIVE_PF_PCT",
        "endpoint_params": {"PtMeasureType": "Drives", "PerMode": "PerGame"},
        "data_type": "percentage",
        "required": True,
        "notes": "Direct mapping from drives tracking"
    },
    "DRIMFGPCT": {
        "canonical_name": "Drive Field Goal Percentage",
        "api_source": "leaguedashptstats",
        "api_column": "DRIVE_FG_PCT",
        "endpoint_params": {"PtMeasureType": "Drives", "PerMode": "PerGame"},
        "data_type": "percentage",
        "required": True,
        "notes": "Direct mapping from drives tracking"
    },
    
    # Catch and shoot metrics
    "CSFGA": {
        "canonical_name": "Catch and Shoot Field Goal Attempts",
        "api_source": "leaguedashptstats",
        "api_column": "CATCH_SHOOT_FGA",
        "endpoint_params": {"PtMeasureType": "CatchShoot", "PerMode": "PerGame"},
        "data_type": "count",
        "required": True,
        "notes": "Direct mapping from catch and shoot tracking"
    },
    "CS3PA": {
        "canonical_name": "Catch and Shoot 3-Point Attempts",
        "api_source": "leaguedashptstats",
        "api_column": "CATCH_SHOOT_FG3A",
        "endpoint_params": {"PtMeasureType": "CatchShoot", "PerMode": "PerGame"},
        "data_type": "count",
        "required": True,
        "notes": "Direct mapping from catch and shoot tracking"
    },
    
    # Passing metrics
    "PASSESMADE": {
        "canonical_name": "Passes Made",
        "api_source": "leaguedashptstats",
        "api_column": "PASSES_MADE",
        "endpoint_params": {"PtMeasureType": "Passing", "PerMode": "PerGame"},
        "data_type": "count",
        "required": True,
        "notes": "Direct mapping from passing tracking"
    },
    "SECAST": {
        "canonical_name": "Secondary Assists",
        "api_source": "leaguedashptstats",
        "api_column": "SECONDARY_AST",
        "endpoint_params": {"PtMeasureType": "Passing", "PerMode": "PerGame"},
        "data_type": "count",
        "required": True,
        "notes": "Direct mapping from passing tracking"
    },
    "POTAST": {
        "canonical_name": "Potential Assists",
        "api_source": "leaguedashptstats",
        "api_column": "POTENTIAL_AST",
        "endpoint_params": {"PtMeasureType": "Passing", "PerMode": "PerGame"},
        "data_type": "count",
        "required": True,
        "notes": "Direct mapping from passing tracking"
    },
    
    # Pull-up shooting metrics
    "PUFGA": {
        "canonical_name": "Pull-Up Field Goal Attempts",
        "api_source": "leaguedashptstats",
        "api_column": "PULL_UP_FGA",
        "endpoint_params": {"PtMeasureType": "PullUpShot", "PerMode": "PerGame"},
        "data_type": "count",
        "required": True,
        "notes": "Direct mapping from pull-up shot tracking"
    },
    "PU3PA": {
        "canonical_name": "Pull-Up 3-Point Attempts",
        "api_source": "leaguedashptstats",
        "api_column": "PULL_UP_FG3A",
        "endpoint_params": {"PtMeasureType": "PullUpShot", "PerMode": "PerGame"},
        "data_type": "count",
        "required": True,
        "notes": "Direct mapping from pull-up shot tracking"
    },
    
    # Post-up metrics
    "PSTUPFGA": {
        "canonical_name": "Post-Up Field Goal Attempts",
        "api_source": "leaguedashptstats",
        "api_column": "POST_TOUCH_FGA",
        "endpoint_params": {"PtMeasureType": "PostTouch", "PerMode": "PerGame"},
        "data_type": "count",
        "required": True,
        "notes": "Direct mapping from post touch tracking"
    },
    "PSTUPPTSPCT": {
        "canonical_name": "Post-Up Points Percentage",
        "api_source": "leaguedashptstats",
        "api_column": "POST_TOUCH_PTS_PCT",
        "endpoint_params": {"PtMeasureType": "PostTouch", "PerMode": "PerGame"},
        "data_type": "percentage",
        "required": True,
        "notes": "Direct mapping from post touch tracking"
    },
    "PSTUPPASSPCT": {
        "canonical_name": "Post-Up Pass Percentage",
        "api_source": "leaguedashptstats",
        "api_column": "POST_TOUCH_PASSES_PCT",
        "endpoint_params": {"PtMeasureType": "PostTouch", "PerMode": "PerGame"},
        "data_type": "percentage",
        "required": True,
        "notes": "Direct mapping from post touch tracking"
    },
    "PSTUPASTPCT": {
        "canonical_name": "Post-Up Assist Percentage",
        "api_source": "leaguedashptstats",
        "api_column": "POST_TOUCH_AST_PCT",
        "endpoint_params": {"PtMeasureType": "PostTouch", "PerMode": "PerGame"},
        "data_type": "percentage",
        "required": True,
        "notes": "Direct mapping from post touch tracking"
    },
    "PSTUPTOVPCT": {
        "canonical_name": "Post-Up Turnover Percentage",
        "api_source": "leaguedashptstats",
        "api_column": "POST_TOUCH_TOV_PCT",
        "endpoint_params": {"PtMeasureType": "PostTouch", "PerMode": "PerGame"},
        "data_type": "percentage",
        "required": True,
        "notes": "Direct mapping from post touch tracking"
    },
    
    # Paint metrics
    "PNTTCHS": {
        "canonical_name": "Paint Touches",
        "api_source": "leaguedashptstats",
        "api_column": "PAINT_TOUCHES",
        "endpoint_params": {"PtMeasureType": "PaintTouch", "PerMode": "PerGame"},
        "data_type": "count",
        "required": True,
        "notes": "Direct mapping from paint touch tracking"
    },
    "PNTFGA": {
        "canonical_name": "Paint Field Goal Attempts",
        "api_source": "leaguedashptstats",
        "api_column": "PAINT_TOUCH_FGA",
        "endpoint_params": {"PtMeasureType": "PaintTouch", "PerMode": "PerGame"},
        "data_type": "count",
        "required": True,
        "notes": "Direct mapping from paint touch tracking"
    },
    "PNTPTSPCT": {
        "canonical_name": "Paint Points Percentage",
        "api_source": "leaguedashptstats",
        "api_column": "PAINT_TOUCH_PTS_PCT",
        "endpoint_params": {"PtMeasureType": "PaintTouch", "PerMode": "PerGame"},
        "data_type": "percentage",
        "required": True,
        "notes": "Direct mapping from paint touch tracking"
    },
    "PNTPASSPCT": {
        "canonical_name": "Paint Pass Percentage",
        "api_source": "leaguedashptstats",
        "api_column": "PAINT_TOUCH_PASSES_PCT",
        "endpoint_params": {"PtMeasureType": "PaintTouch", "PerMode": "PerGame"},
        "data_type": "percentage",
        "required": True,
        "notes": "Direct mapping from paint touch tracking"
    },
    "PNTASTPCT": {
        "canonical_name": "Paint Assist Percentage",
        "api_source": "leaguedashptstats",
        "api_column": "PAINT_TOUCH_AST_PCT",
        "endpoint_params": {"PtMeasureType": "PaintTouch", "PerMode": "PerGame"},
        "data_type": "percentage",
        "required": True,
        "notes": "Direct mapping from paint touch tracking"
    },
    "PNTTVPCT": {
        "canonical_name": "Paint Turnover Percentage",
        "api_source": "leaguedashptstats",
        "api_column": "PAINT_TOUCH_TOV_PCT",
        "endpoint_params": {"PtMeasureType": "PaintTouch", "PerMode": "PerGame"},
        "data_type": "percentage",
        "required": True,
        "notes": "Direct mapping from paint touch tracking"
    },
    
    # Defensive metric
    "AVGFGATTEMPTEDAGAINSTPERGAME": {
        "canonical_name": "Average Field Goals Attempted Against Per Game",
        "api_source": "leaguedashplayerhustlestats",
        "api_column": "CONTESTED_SHOTS",  # This is the closest match
        "endpoint_params": {"PerMode": "PerGame"},
        "data_type": "count",
        "required": True,
        "notes": "Using contested shots as proxy - may need adjustment"
    }
}

def get_metric_mapping(metric: str) -> Dict:
    """Get the complete mapping for a specific metric."""
    return DEFINITIVE_METRIC_MAPPING.get(metric, {})

def get_missing_metrics() -> List[str]:
    """Get list of metrics that are missing from the API."""
    return [metric for metric, mapping in DEFINITIVE_METRIC_MAPPING.items() 
            if mapping.get("api_source") == "MISSING"]

def get_available_metrics() -> List[str]:
    """Get list of metrics that are available in the API."""
    return [metric for metric, mapping in DEFINITIVE_METRIC_MAPPING.items() 
            if mapping.get("api_source") != "MISSING"]

def get_metrics_by_api_source() -> Dict[str, List[str]]:
    """Group metrics by their API source."""
    by_source = {}
    for metric, mapping in DEFINITIVE_METRIC_MAPPING.items():
        source = mapping.get("api_source", "UNKNOWN")
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(metric)
    return by_source

def validate_mapping_completeness() -> Dict:
    """Validate that all 48 metrics are mapped."""
    mapped_metrics = set(DEFINITIVE_METRIC_MAPPING.keys())
    canonical_metrics = set(CANONICAL_48_METRICS)
    
    missing_metrics = canonical_metrics - mapped_metrics
    extra_metrics = mapped_metrics - canonical_metrics
    
    return {
        "complete": len(missing_metrics) == 0,
        "missing_metrics": list(missing_metrics),
        "extra_metrics": list(extra_metrics),
        "total_mapped": len(mapped_metrics),
        "total_canonical": len(canonical_metrics),
        "available_count": len(get_available_metrics()),
        "missing_count": len(get_missing_metrics())
    }

def generate_mapping_report() -> str:
    """Generate a comprehensive mapping report."""
    validation = validate_mapping_completeness()
    by_source = get_metrics_by_api_source()
    
    report_lines = []
    report_lines.append("# Definitive Metric Mapping Report")
    report_lines.append("")
    report_lines.append("## Summary")
    report_lines.append(f"- Total canonical metrics: {validation['total_canonical']}")
    report_lines.append(f"- Total mapped metrics: {validation['total_mapped']}")
    report_lines.append(f"- Available in API: {validation['available_count']}")
    report_lines.append(f"- Missing from API: {validation['missing_count']}")
    report_lines.append(f"- Mapping complete: {validation['complete']}")
    report_lines.append("")
    
    if validation['missing_metrics']:
        report_lines.append("## Missing Metrics")
        for metric in validation['missing_metrics']:
            report_lines.append(f"- {metric}")
        report_lines.append("")
    
    report_lines.append("## Metrics by API Source")
    for source, metrics in by_source.items():
        report_lines.append(f"### {source} ({len(metrics)} metrics)")
        for metric in sorted(metrics):
            mapping = DEFINITIVE_METRIC_MAPPING[metric]
            report_lines.append(f"- {metric}: {mapping['canonical_name']}")
        report_lines.append("")
    
    report_lines.append("## Missing API Sources")
    missing_metrics = get_missing_metrics()
    if missing_metrics:
        report_lines.append("The following metrics are not available in the current API:")
        for metric in missing_metrics:
            mapping = DEFINITIVE_METRIC_MAPPING[metric]
            report_lines.append(f"- {metric}: {mapping['canonical_name']} - {mapping['notes']}")
    
    return "\n".join(report_lines)

if __name__ == "__main__":
    validation = validate_mapping_completeness()
    print(f"Mapping validation: {validation}")
    
    print(f"\nMissing metrics: {get_missing_metrics()}")
    print(f"Available metrics: {len(get_available_metrics())}")
    
    # Generate and save report
    report = generate_mapping_report()
    with open("definitive_metric_mapping_report.md", "w") as f:
        f.write(report)
    print(f"\nReport saved to: definitive_metric_mapping_report.md")
