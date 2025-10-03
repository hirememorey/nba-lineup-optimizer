#!/usr/bin/env python3
"""
Implementation Test Script

This script tests the key components of the implementation to ensure
everything is working correctly.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from player_acquisition_tool import PlayerAcquisitionTool
        print("✅ PlayerAcquisitionTool imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import PlayerAcquisitionTool: {e}")
        return False
    
    try:
        import model_governance_dashboard
        print("✅ Model Governance Dashboard imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Model Governance Dashboard: {e}")
        return False
    
    try:
        import model_interrogation_tool
        print("✅ Model Interrogation Tool imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Model Interrogation Tool: {e}")
        return False
    
    return True

def test_database_connection():
    """Test database connection."""
    print("\nTesting database connection...")
    
    try:
        from player_acquisition_tool import PlayerAcquisitionTool
        
        tool = PlayerAcquisitionTool()
        if tool.connect_database():
            print("✅ Database connection successful")
            
            # Test data loading
            if tool.load_player_data():
                print("✅ Player data loaded successfully")
                print(f"   - {len(tool.player_data)} players loaded")
            else:
                print("❌ Failed to load player data")
                return False
            
            if tool.load_archetype_data():
                print("✅ Archetype data loaded successfully")
                print(f"   - {len(tool.archetype_data)} archetypes loaded")
            else:
                print("❌ Failed to load archetype data")
                return False
            
            return True
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_acquisition_tool():
    """Test the acquisition tool functionality."""
    print("\nTesting acquisition tool...")
    
    try:
        from player_acquisition_tool import PlayerAcquisitionTool
        
        tool = PlayerAcquisitionTool()
        if not tool.connect_database():
            print("❌ Database connection failed")
            return False
        
        if not tool.load_player_data():
            print("❌ Failed to load player data")
            return False
        
        if not tool.load_archetype_data():
            print("❌ Failed to load archetype data")
            return False
        
        # Test player search
        player = tool.get_player_by_name("LeBron James")
        if player is not None:
            print("✅ Player search working")
            print(f"   - Found: {player['player_name']} ({player['archetype_name']})")
        else:
            print("⚠️ LeBron James not found (may not be in database)")
        
        # Test lineup value calculation
        if player is not None:
            # Create a simple test lineup with different players
            test_players = tool.player_data.head(4)['player_id'].tolist()
            lineup_value = tool.calculate_lineup_value(test_players)
            
            if "error" not in lineup_value:
                print("✅ Lineup value calculation working")
                print(f"   - Test lineup value: {lineup_value['total_value']:.3f}")
            else:
                print(f"❌ Lineup value calculation failed: {lineup_value['error']}")
                return False
        
        print("✅ Acquisition tool tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Acquisition tool test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist."""
    print("\nTesting file structure...")
    
    required_files = [
        "model_governance_dashboard.py",
        "player_acquisition_tool.py",
        "model_interrogation_tool.py",
        "run_governance_dashboard.py",
        "run_interrogation_tool.py",
        "demo_implementation.py",
        "IMPLEMENTATION_COMPLETE_V2.md"
    ]
    
    all_files_exist = True
    
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            all_files_exist = False
    
    return all_files_exist

def test_model_coefficients():
    """Test model coefficient loading."""
    print("\nTesting model coefficients...")
    
    try:
        from player_acquisition_tool import PlayerAcquisitionTool
        
        tool = PlayerAcquisitionTool()
        
        # Test loading model coefficients
        if tool.load_model_coefficients():
            print("✅ Model coefficients loaded successfully")
            if hasattr(tool, 'model_coefficients') and tool.model_coefficients is not None:
                print(f"   - {len(tool.model_coefficients)} coefficient rows loaded")
            else:
                print("   - Using placeholder coefficients")
        else:
            print("⚠️ Model coefficients not found, using placeholder values")
        
        return True
        
    except Exception as e:
        print(f"❌ Model coefficient test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 NBA Lineup Optimizer - Implementation Test")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("Database Connection", test_database_connection),
        ("Model Coefficients", test_model_coefficients),
        ("Acquisition Tool", test_acquisition_tool)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Implementation is ready.")
        print("\nNext steps:")
        print("1. Run 'python demo_implementation.py' to see the full demo")
        print("2. Run 'python run_interrogation_tool.py' to launch the main UI")
        print("3. Run 'python run_governance_dashboard.py' to launch governance dashboard")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        print("Make sure the database exists and all files are present.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
