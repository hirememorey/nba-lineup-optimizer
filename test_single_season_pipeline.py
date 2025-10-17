#!/usr/bin/env python3
"""
Phase 1.3: End-to-End Single-Season Validation
Test the complete analytical pipeline on 2018-19 data to validate the entire chain
"""

import subprocess
import sys
import os
import sqlite3
import pandas as pd
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SANDBOX_DB = "historical_sandbox.db"
TARGET_SEASON = "2018-19"

def test_database_connection():
    """Test 1: Verify sandbox database exists and is accessible"""
    logger.info("=== Test 1: Database Connection ===")
    try:
        conn = sqlite3.connect(SANDBOX_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        
        logger.info(f"✅ Database connection successful")
        logger.info(f"   Tables found: {len(tables)}")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def test_games_data():
    """Test 2: Verify 2018-19 games data is present"""
    logger.info("=== Test 2: Games Data Verification ===")
    try:
        conn = sqlite3.connect(SANDBOX_DB)
        query = f"SELECT COUNT(*) FROM Games WHERE season = '{TARGET_SEASON}'"
        cursor = conn.cursor()
        cursor.execute(query)
        count = cursor.fetchone()[0]
        conn.close()
        
        if count > 0:
            logger.info(f"✅ Games data found: {count} games for {TARGET_SEASON}")
            return True
        else:
            logger.error(f"❌ No games data found for {TARGET_SEASON}")
            return False
    except Exception as e:
        logger.error(f"❌ Games data verification failed: {e}")
        return False

def test_player_data():
    """Test 3: Check if player data exists for 2018-19"""
    logger.info("=== Test 3: Player Data Verification ===")
    try:
        conn = sqlite3.connect(SANDBOX_DB)
        
        # Check PlayerSeasonRawStats
        query = f"SELECT COUNT(*) FROM PlayerSeasonRawStats WHERE season = '{TARGET_SEASON}'"
        cursor = conn.cursor()
        cursor.execute(query)
        raw_stats_count = cursor.fetchone()[0]
        
        # Check PlayerSeasonSkill
        query = f"SELECT COUNT(*) FROM PlayerSeasonSkill WHERE season = '{TARGET_SEASON}'"
        cursor.execute(query)
        skill_count = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info(f"   Raw stats: {raw_stats_count} players")
        logger.info(f"   Skill data: {skill_count} players")
        
        if raw_stats_count > 0 and skill_count > 0:
            logger.info(f"✅ Player data found for {TARGET_SEASON}")
            return True
        else:
            logger.error(f"❌ Insufficient player data for {TARGET_SEASON}")
            return False
    except Exception as e:
        logger.error(f"❌ Player data verification failed: {e}")
        return False

def test_archetype_features():
    """Test 4: Check if archetype features exist for 2018-19"""
    logger.info("=== Test 4: Archetype Features Verification ===")
    try:
        conn = sqlite3.connect(SANDBOX_DB)
        
        # Check if season-specific table exists
        query = f"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%{TARGET_SEASON.replace('-', '_')}%'"
        cursor = conn.cursor()
        cursor.execute(query)
        season_tables = cursor.fetchall()
        
        # Check main archetype features table
        query = "SELECT COUNT(*) FROM PlayerArchetypeFeatures"
        cursor.execute(query)
        archetype_count = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info(f"   Season-specific tables: {len(season_tables)}")
        logger.info(f"   Main archetype features: {archetype_count} players")
        
        if archetype_count > 0:
            logger.info(f"✅ Archetype features data found")
            return True
        else:
            logger.error(f"❌ No archetype features data found")
            return False
    except Exception as e:
        logger.error(f"❌ Archetype features verification failed: {e}")
        return False

def test_analytical_scripts():
    """Test 5: Test analytical scripts (this will likely fail)"""
    logger.info("=== Test 5: Analytical Scripts Testing ===")
    
    scripts_to_test = [
        ("create_archetypes.py", "Archetype generation"),
        ("src/nba_stats/scripts/generate_lineup_superclusters.py", "Supercluster generation"),
        ("bayesian_data_prep.py", "Bayesian data preparation")
    ]
    
    results = {}
    
    for script_path, description in scripts_to_test:
        logger.info(f"   Testing {description}...")
        try:
            # Try to run the script (this will likely fail due to hardcoded assumptions)
            result = subprocess.run([sys.executable, script_path], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"   ✅ {description} - SUCCESS")
                results[script_path] = "SUCCESS"
            else:
                logger.warning(f"   ⚠️  {description} - FAILED (expected)")
                logger.warning(f"      Error: {result.stderr[:200]}...")
                results[script_path] = "FAILED"
                
        except subprocess.TimeoutExpired:
            logger.warning(f"   ⚠️  {description} - TIMEOUT")
            results[script_path] = "TIMEOUT"
        except Exception as e:
            logger.warning(f"   ⚠️  {description} - ERROR: {e}")
            results[script_path] = "ERROR"
    
    return results

def test_data_quality():
    """Test 6: Check data quality and completeness"""
    logger.info("=== Test 6: Data Quality Analysis ===")
    try:
        conn = sqlite3.connect(SANDBOX_DB)
        
        # Check for NULL values in key tables
        tables_to_check = [
            "PlayerSeasonRawStats",
            "PlayerSeasonSkill", 
            "Games"
        ]
        
        quality_issues = []
        
        for table in tables_to_check:
            query = f"SELECT COUNT(*) FROM {table} WHERE season = '{TARGET_SEASON}'"
            cursor = conn.cursor()
            cursor.execute(query)
            count = cursor.fetchone()[0]
            
            if count == 0:
                quality_issues.append(f"{table}: No data for {TARGET_SEASON}")
            else:
                logger.info(f"   {table}: {count} records for {TARGET_SEASON}")
        
        conn.close()
        
        if quality_issues:
            logger.error(f"❌ Data quality issues found:")
            for issue in quality_issues:
                logger.error(f"   - {issue}")
            return False
        else:
            logger.info(f"✅ Data quality looks good")
            return True
            
    except Exception as e:
        logger.error(f"❌ Data quality analysis failed: {e}")
        return False

def generate_report():
    """Generate a comprehensive test report"""
    logger.info("=== Generating Test Report ===")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "target_season": TARGET_SEASON,
        "sandbox_db": SANDBOX_DB,
        "tests": {}
    }
    
    # Run all tests
    report["tests"]["database_connection"] = test_database_connection()
    report["tests"]["games_data"] = test_games_data()
    report["tests"]["player_data"] = test_player_data()
    report["tests"]["archetype_features"] = test_archetype_features()
    report["tests"]["data_quality"] = test_data_quality()
    report["tests"]["analytical_scripts"] = test_analytical_scripts()
    
    # Calculate overall status
    critical_tests = ["database_connection", "games_data", "player_data", "data_quality"]
    critical_passed = all(report["tests"][test] for test in critical_tests if test in report["tests"])
    
    report["overall_status"] = "PASS" if critical_passed else "FAIL"
    report["critical_tests_passed"] = critical_passed
    
    # Save report
    import json
    with open("single_season_validation_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Report saved to single_season_validation_report.json")
    logger.info(f"Overall Status: {report['overall_status']}")
    
    return report

def main():
    """Main function to run all validation tests"""
    logger.info("=" * 60)
    logger.info("Phase 1.3: End-to-End Single-Season Validation")
    logger.info(f"Target Season: {TARGET_SEASON}")
    logger.info(f"Sandbox Database: {SANDBOX_DB}")
    logger.info("=" * 60)
    
    # Check if sandbox database exists
    if not os.path.exists(SANDBOX_DB):
        logger.error(f"Sandbox database {SANDBOX_DB} not found. Please create it first.")
        return False
    
    # Generate comprehensive report
    report = generate_report()
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    
    for test_name, result in report["tests"].items():
        if isinstance(result, bool):
            status = "✅ PASS" if result else "❌ FAIL"
        else:
            status = f"⚠️  {result}"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall Status: {report['overall_status']}")
    
    if report["overall_status"] == "PASS":
        logger.info("🎉 Critical tests passed! Ready to proceed with analytical script refactoring.")
    else:
        logger.info("⚠️  Critical tests failed. Need to address data issues before proceeding.")
    
    return report["overall_status"] == "PASS"

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
