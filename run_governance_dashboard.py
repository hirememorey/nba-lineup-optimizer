#!/usr/bin/env python3
"""
Launcher script for the Model Governance Dashboard.

This script launches the Streamlit-based governance dashboard for model validation.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the Model Governance Dashboard."""
    print("🏀 Launching NBA Model Governance Dashboard...")
    print("This tool enables structured validation of model coefficients.")
    print("")
    
    # Check if we're in the right directory
    if not Path("model_governance_dashboard.py").exists():
        print("❌ Error: model_governance_dashboard.py not found in current directory")
        print("Please run this script from the project root directory.")
        sys.exit(1)
    
    # Check if database exists
    db_path = "src/nba_stats/db/nba_stats.db"
    if not Path(db_path).exists():
        print(f"❌ Error: Database not found at {db_path}")
        print("Please run the data pipeline first to create the database.")
        sys.exit(1)
    
    print("✅ Database found")
    print("✅ Starting governance dashboard...")
    print("")
    print("The dashboard will open in your browser at: http://localhost:8502")
    print("Press Ctrl+C to stop the server")
    print("")
    
    try:
        # Launch Streamlit with the governance dashboard
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "model_governance_dashboard.py",
            "--server.port", "8502",
            "--server.headless", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Governance dashboard stopped.")
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
