"""
Canonical list of 48 archetype metrics required for player clustering.

This list is extracted from the source paper and serves as our ground truth
for data mapping and verification.
"""

CANONICAL_48_METRICS = [
    # Basic shooting and efficiency metrics
    "FTPCT",           # Free Throw Percentage
    "TSPCT",           # True Shooting Percentage
    "THPAr",           # Three Point Attempt Rate
    "FTr",             # Free Throw Rate
    "TRBPCT",          # Total Rebound Percentage
    "ASTPCT",          # Assist Percentage
    
    # Shooting distance and location metrics
    "AVGDIST",         # Average Shot Distance
    "Zto3r",           # Zone to 3-Point Range
    "THto10r",         # Three to Ten Range
    "TENto16r",        # Ten to Sixteen Range
    "SIXTto3PTr",      # Sixteen to 3-Point Range
    
    # Physical attributes
    "HEIGHT",          # Player Height
    "WINGSPAN",        # Player Wingspan
    
    # Touch and possession metrics
    "FRNTCTTCH",       # Front Court Touches
    "TOP",             # Time of Possession
    "AVGSECPERTCH",    # Average Seconds Per Touch
    "AVGDRIBPERTCH",   # Average Dribbles Per Touch
    "ELBWTCH",         # Elbow Touches
    "POSTUPS",         # Post-Ups
    "PNTTOUCH",        # Paint Touches
    
    # Driving metrics
    "DRIVES",          # Drives
    "DRFGA",           # Drive Field Goal Attempts
    "DRPTSPCT",        # Drive Points Percentage
    "DRPASSPCT",       # Drive Pass Percentage
    "DRASTPCT",        # Drive Assist Percentage
    "DRTOVPCT",        # Drive Turnover Percentage
    "DRPFPCT",         # Drive Personal Foul Percentage
    "DRIMFGPCT",       # Drive Field Goal Percentage
    
    # Catch and shoot metrics
    "CSFGA",           # Catch and Shoot Field Goal Attempts
    "CS3PA",           # Catch and Shoot 3-Point Attempts
    
    # Passing metrics
    "PASSESMADE",      # Passes Made
    "SECAST",          # Secondary Assists
    "POTAST",          # Potential Assists
    
    # Pull-up shooting metrics
    "PUFGA",           # Pull-Up Field Goal Attempts
    "PU3PA",           # Pull-Up 3-Point Attempts
    
    # Post-up metrics
    "PSTUPFGA",        # Post-Up Field Goal Attempts
    "PSTUPPTSPCT",     # Post-Up Points Percentage
    "PSTUPPASSPCT",    # Post-Up Pass Percentage
    "PSTUPASTPCT",     # Post-Up Assist Percentage
    "PSTUPTOVPCT",     # Post-Up Turnover Percentage
    
    # Paint metrics
    "PNTTCHS",         # Paint Touches
    "PNTFGA",          # Paint Field Goal Attempts
    "PNTPTSPCT",       # Paint Points Percentage
    "PNTPASSPCT",      # Paint Pass Percentage
    "PNTASTPCT",       # Paint Assist Percentage
    "PNTTVPCT",        # Paint Turnover Percentage
    
    # Defensive metric
    "AVGFGATTEMPTEDAGAINSTPERGAME"  # Average Field Goals Attempted Against Per Game
]

def get_canonical_metrics():
    """Return the canonical list of 48 archetype metrics."""
    return CANONICAL_48_METRICS.copy()

def validate_metric_count():
    """Validate that we have exactly 48 metrics."""
    return len(CANONICAL_48_METRICS) == 48

if __name__ == "__main__":
    print(f"Canonical metrics count: {len(CANONICAL_48_METRICS)}")
    print(f"Validation passed: {validate_metric_count()}")
    print("\nMetrics:")
    for i, metric in enumerate(CANONICAL_48_METRICS, 1):
        print(f"{i:2d}. {metric}")
