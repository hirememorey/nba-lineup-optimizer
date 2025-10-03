#!/usr/bin/env python3
"""
Run the Model Interrogation Tool

This script launches the Streamlit-based interrogation tool for exploring
and validating the possession-level modeling system.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the interrogation tool."""
    print("🏀 Starting NBA Lineup Model Interrogation Tool")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("model_interrogation_tool.py").exists():
        print("❌ Error: model_interrogation_tool.py not found in current directory")
        print("Please run this script from the project root directory")
        sys.exit(1)
    
    # Check if database exists
    db_path = "src/nba_stats/db/nba_stats.db"
    if not Path(db_path).exists():
        print(f"❌ Error: Database not found at {db_path}")
        print("Please run the data pipeline first to populate the database")
        sys.exit(1)
    
    print("✅ Database found")
    print("✅ Starting Streamlit app...")
    print()
    print("The tool will open in your browser at: http://localhost:8501")
    print("Press Ctrl+C to stop the server")
    print()
    
    try:
        # Launch Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "model_interrogation_tool.py",
            "--server.port", "8501",
            "--server.headless", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Interrogation tool stopped")
    except Exception as e:
        print(f"❌ Error launching tool: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
