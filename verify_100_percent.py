#!/usr/bin/env python3
"""
Verify that we have achieved 100% data integrity after reconciliation.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_data_integrity():
    """Check the current data integrity status."""
    db_path = "src/nba_stats/db/nba_stats.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get counts
        cursor.execute("SELECT COUNT(*) FROM Players")
        total_players = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM PlayerSalaries WHERE season_id = '2024-25'")
        salary_players = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM PlayerSkills WHERE season_id = '2024-25'")
        skill_players = cursor.fetchone()[0]
        
        # Calculate coverage percentages
        salary_coverage = (salary_players / total_players * 100) if total_players > 0 else 0
        skill_coverage = (skill_players / total_players * 100) if total_players > 0 else 0
        
        print("📊 Data Integrity Report")
        print("=" * 30)
        print(f"Total players in database: {total_players}")
        print(f"Players with salary data: {salary_players} ({salary_coverage:.1f}%)")
        print(f"Players with skill data: {skill_players} ({skill_coverage:.1f}%)")
        print()
        
        # Check if we've achieved 100%
        if salary_coverage >= 100 and skill_coverage >= 100:
            print("🎉 SUCCESS: 100% data integrity achieved!")
            return True
        else:
            print("⚠️  Data integrity not yet at 100%")
            if salary_coverage < 100:
                print(f"   - Salary coverage: {salary_coverage:.1f}% (need 100%)")
            if skill_coverage < 100:
                print(f"   - Skill coverage: {skill_coverage:.1f}% (need 100%)")
            return False
            
    finally:
        conn.close()

def main():
    """Main verification function."""
    print("🔍 Verifying Data Integrity")
    print("=" * 30)
    
    success = check_data_integrity()
    
    if not success:
        print()
        print("💡 To achieve 100% data integrity, run:")
        print("   python run_reconciliation.py")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
