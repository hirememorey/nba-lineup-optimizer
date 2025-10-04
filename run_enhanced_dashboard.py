#!/usr/bin/env python3
"""
Run the Enhanced Model Dashboard

This script launches the enhanced model dashboard with model switching capabilities.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the enhanced model dashboard."""
    print("🏀 Starting NBA Enhanced Model Dashboard")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("enhanced_model_dashboard.py").exists():
        print("❌ Error: enhanced_model_dashboard.py not found in current directory")
        print("Please run this script from the project root directory")
        sys.exit(1)
    
    # Check if database exists
    db_path = "src/nba_stats/db/nba_stats.db"
    if not Path(db_path).exists():
        print(f"❌ Error: Database not found at {db_path}")
        print("Please run the data pipeline first to populate the database")
        sys.exit(1)
    
    # Check if model coefficients exist
    coeff_path = "model_coefficients.csv"
    if not Path(coeff_path).exists():
        print(f"⚠️  Warning: Model coefficients not found at {coeff_path}")
        print("The SimpleModelEvaluator will use placeholder coefficients")
        print("Run the production model pipeline to generate real coefficients")
    
    print("✅ Database found")
    if Path(coeff_path).exists():
        print("✅ Model coefficients found")
    else:
        print("⚠️  Model coefficients not found - using placeholders")
    
    print("✅ Starting Streamlit app...")
    print()
    print("The dashboard will open in your browser at: http://localhost:8502")
    print("Press Ctrl+C to stop the server")
    print()
    
    try:
        # Launch Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "enhanced_model_dashboard.py",
            "--server.port", "8502",
            "--server.headless", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Enhanced dashboard stopped")
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
