#!/usr/bin/env python3
"""
Runner script for the Fan-Friendly NBA Lineup Optimizer Dashboard
"""

import subprocess
import sys
import os

def main():
    """Run the fan-friendly dashboard."""
    print("🏀 Starting NBA Lineup Optimizer - Fan Edition")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("fan_friendly_dashboard.py"):
        print("❌ Error: fan_friendly_dashboard.py not found")
        print("Please run this script from the project root directory")
        sys.exit(1)
    
    # Check if database exists
    if not os.path.exists("src/nba_stats/db/nba_stats.db"):
        print("❌ Error: Database not found")
        print("Please ensure the database is set up first")
        sys.exit(1)
    
    print("✅ Database found")
    print("🚀 Starting dashboard...")
    print("\nThe dashboard will open in your browser at: http://localhost:8501")
    print("Press Ctrl+C to stop the dashboard")
    print("=" * 50)
    
    try:
        # Run the Streamlit dashboard
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "fan_friendly_dashboard.py",
            "--server.port", "8501",
            "--server.headless", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error running dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
