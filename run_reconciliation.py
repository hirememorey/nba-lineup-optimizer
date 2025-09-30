#!/usr/bin/env python3
"""
Run the player name reconciliation process to achieve 100% data integrity.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Run the reconciliation process."""
    print("🎯 NBA Player Name Reconciliation")
    print("=" * 50)
    print("This tool will help you achieve 100% data integrity for player salary and skill data.")
    print()
    
    # Check if required files exist
    db_path = "src/nba_stats/db/nba_stats.db"
    salaries_csv = "data/player_salaries_2024-25.csv"
    skills_csv = "data/darko_dpm_2024-25.csv"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("Please run the data population scripts first.")
        return 1
    
    if not os.path.exists(salaries_csv):
        print(f"❌ Salaries CSV not found: {salaries_csv}")
        return 1
    
    if not os.path.exists(skills_csv):
        print(f"❌ Skills CSV not found: {skills_csv}")
        return 1
    
    print("✅ All required files found")
    print()
    
    # Import and run the reconciliation tool
    try:
        from src.nba_stats.scripts.fix_player_names import main as reconcile_main
        return reconcile_main()
    except ImportError as e:
        print(f"❌ Error importing reconciliation tool: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error running reconciliation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
