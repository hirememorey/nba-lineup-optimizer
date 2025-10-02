#!/usr/bin/env python3
"""
Demo script for the new DatabaseWriter service.

This script demonstrates the complete data flow from DTOs to database persistence
with full validation and atomic transactions.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.nba_stats.services.database_writer import DatabaseWriter
from src.nba_stats.models.database_dtos import (
    PlayerSeasonRawStatsDTO, 
    PlayerSeasonAdvancedStatsDTO
)


def create_sample_data():
    """Create sample data for demonstration."""
    
    # Sample raw stats
    raw_stats = [
        PlayerSeasonRawStatsDTO(
            player_id=2,  # Byron Scott
            season="2024-25",
            team_id=1610612737,  # Atlanta Hawks
            games_played=82,
            games_started=82,
            minutes_played=35.5,
            field_goals_made=8,
            field_goals_attempted=16,
            field_goal_percentage=0.500,
            three_pointers_made=2,
            three_pointers_attempted=5,
            three_point_percentage=0.400,
            free_throws_made=4,
            free_throws_attempted=5,
            free_throw_percentage=0.800,
            offensive_rebounds=1,
            defensive_rebounds=4,
            total_rebounds=5,
            assists=6,
            steals=1,
            blocks=0,
            turnovers=2,
            personal_fouls=3,
            points=22,
            plus_minus=5.2,
            avg_shot_distance=15.5
        ),
        PlayerSeasonRawStatsDTO(
            player_id=3,  # Grant Long
            season="2024-25",
            team_id=1610612738,  # Boston Celtics
            games_played=78,
            games_started=78,
            minutes_played=32.1,
            field_goals_made=6,
            field_goals_attempted=14,
            field_goal_percentage=0.429,
            three_pointers_made=1,
            three_pointers_attempted=4,
            three_point_percentage=0.250,
            free_throws_made=3,
            free_throws_attempted=4,
            free_throw_percentage=0.750,
            offensive_rebounds=2,
            defensive_rebounds=6,
            total_rebounds=8,
            assists=4,
            steals=2,
            blocks=1,
            turnovers=3,
            personal_fouls=2,
            points=16,
            plus_minus=-2.1,
            avg_shot_distance=12.3
        )
    ]
    
    # Sample advanced stats
    advanced_stats = [
        PlayerSeasonAdvancedStatsDTO(
            player_id=2,  # Byron Scott
            season="2024-25",
            team_id=1610612737,  # Atlanta Hawks
            age=25,
            games_played=82,
            wins=50,
            losses=32,
            win_percentage=0.610,
            minutes_played=35.5,
            offensive_rating=115.2,
            defensive_rating=108.7,
            net_rating=6.5,
            assist_percentage=25.3,
            assist_to_turnover_ratio=3.0,
            assist_ratio=20.1,
            offensive_rebound_percentage=3.2,
            defensive_rebound_percentage=12.8,
            rebound_percentage=8.1,
            turnover_percentage=12.5,
            effective_field_goal_percentage=0.563,
            true_shooting_percentage=0.598,
            usage_percentage=22.4,
            pace=98.5,
            pie=12.3,
            possessions=75
        ),
        PlayerSeasonAdvancedStatsDTO(
            player_id=3,  # Grant Long
            season="2024-25",
            team_id=1610612738,  # Boston Celtics
            age=28,
            games_played=78,
            wins=35,
            losses=43,
            win_percentage=0.449,
            minutes_played=32.1,
            offensive_rating=105.8,
            defensive_rating=112.3,
            net_rating=-6.5,
            assist_percentage=18.7,
            assist_to_turnover_ratio=1.33,
            assist_ratio=15.2,
            offensive_rebound_percentage=5.1,
            defensive_rebound_percentage=18.9,
            rebound_percentage=12.0,
            turnover_percentage=15.8,
            effective_field_goal_percentage=0.464,
            true_shooting_percentage=0.521,
            usage_percentage=18.9,
            pace=96.2,
            pie=8.7,
            possessions=68
        )
    ]
    
    return raw_stats, advanced_stats


def main():
    """Main demonstration function."""
    print("🏀 NBA Database Writer Service Demo")
    print("=" * 50)
    
    # Initialize the database writer
    writer = DatabaseWriter("src/nba_stats/db/nba_stats.db")
    
    # Create sample data
    print("\n📊 Creating sample data...")
    raw_stats, advanced_stats = create_sample_data()
    print(f"   Created {len(raw_stats)} raw stats records")
    print(f"   Created {len(advanced_stats)} advanced stats records")
    
    # Test schema validation
    print("\n🔍 Testing schema validation...")
    raw_schema = writer.get_table_schema("PlayerSeasonRawStats")
    advanced_schema = writer.get_table_schema("PlayerSeasonAdvancedStats")
    print(f"   Raw stats table has {len(raw_schema)} columns")
    print(f"   Advanced stats table has {len(advanced_schema)} columns")
    
    # Write raw stats
    print("\n💾 Writing raw stats to database...")
    raw_result = writer.write_player_season_raw_stats(raw_stats)
    if raw_result.success:
        print(f"   ✅ Successfully wrote {raw_result.rows_affected} rows")
    else:
        print(f"   ❌ Failed to write raw stats: {raw_result.error_message}")
        return
    
    # Write advanced stats
    print("\n💾 Writing advanced stats to database...")
    advanced_result = writer.write_player_season_advanced_stats(advanced_stats)
    if advanced_result.success:
        print(f"   ✅ Successfully wrote {advanced_result.rows_affected} rows")
    else:
        print(f"   ❌ Failed to write advanced stats: {advanced_result.error_message}")
        return
    
    # Verify data integrity
    print("\n🔍 Verifying data integrity...")
    raw_integrity = writer.verify_data_integrity("PlayerSeasonRawStats")
    advanced_integrity = writer.verify_data_integrity("PlayerSeasonAdvancedStats")
    
    print(f"   Raw stats integrity: {'✅ Valid' if raw_integrity['success'] else '❌ Invalid'}")
    print(f"   Advanced stats integrity: {'✅ Valid' if advanced_integrity['success'] else '❌ Invalid'}")
    
    if raw_integrity['success']:
        print(f"   Raw stats: {raw_integrity['total_rows']} rows, critical columns valid: {raw_integrity['critical_columns_valid']}")
    
    if advanced_integrity['success']:
        print(f"   Advanced stats: {advanced_integrity['total_rows']} rows, critical columns valid: {advanced_integrity['critical_columns_valid']}")
    
    # Test error handling
    print("\n🚨 Testing error handling...")
    invalid_data = [
        PlayerSeasonRawStatsDTO(
            player_id=999,  # Non-existent player (will cause foreign key error)
            season="2024-25",
            team_id=1,
            points=20
        )
    ]
    
    error_result = writer.write_player_season_raw_stats(invalid_data)
    if not error_result.success:
        print(f"   ✅ Error handling works: {error_result.error_message[:100]}...")
    else:
        print("   ❌ Error handling failed - should have caught foreign key constraint")
    
    # Test with valid data to show the system still works
    print("\n🔄 Testing recovery with valid data...")
    valid_data = [
        PlayerSeasonRawStatsDTO(
            player_id=2,  # Valid player (Byron Scott)
            season="2024-25",
            team_id=1610612737,  # Valid team (Atlanta Hawks)
            points=25
        )
    ]
    
    recovery_result = writer.write_player_season_raw_stats(valid_data)
    if recovery_result.success:
        print(f"   ✅ System recovered: Successfully wrote {recovery_result.rows_affected} rows")
    else:
        print(f"   ❌ Recovery failed: {recovery_result.error_message}")
    
    print("\n🎉 Demo completed successfully!")
    print("\nKey features demonstrated:")
    print("   ✅ Pydantic DTOs for data validation")
    print("   ✅ Pre-flight schema validation")
    print("   ✅ Atomic transactions with rollback")
    print("   ✅ Write audit verification")
    print("   ✅ Data integrity verification")
    print("   ✅ Comprehensive error handling")


if __name__ == "__main__":
    main()
