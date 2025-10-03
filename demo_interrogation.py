#!/usr/bin/env python3
"""
Demo: Using the Model Interrogation Tool Programmatically

This script demonstrates how to use the ModelInterrogator class
programmatically without the Streamlit interface.
"""

from model_interrogation_tool import ModelInterrogator
import pandas as pd

def main():
    """Demonstrate the interrogation tool capabilities."""
    print("🏀 NBA Lineup Model Interrogation Tool - Programmatic Demo")
    print("=" * 70)
    
    # Initialize the interrogator
    interrogator = ModelInterrogator()
    
    # Connect to database
    print("1. Connecting to database...")
    if not interrogator.connect_database():
        print("❌ Failed to connect to database")
        return
    print("✅ Database connected")
    
    # Load data
    print("\n2. Loading data...")
    if not interrogator.load_player_data():
        print("❌ Failed to load player data")
        return
    print(f"✅ Loaded {len(interrogator.player_data)} players")
    
    if not interrogator.load_archetype_data():
        print("❌ Failed to load archetype data")
        return
    print(f"✅ Loaded {len(interrogator.archetype_data)} archetypes")
    
    if not interrogator.load_model_coefficients():
        print("⚠️ Model coefficients not found, using placeholder calculations")
    else:
        print("✅ Model coefficients loaded")
    
    # Show data overview
    print("\n3. Data Overview:")
    print(f"   - Total players: {len(interrogator.player_data)}")
    print(f"   - Players with archetypes: {len(interrogator.player_data[interrogator.player_data['archetype_id'].notna()])}")
    print(f"   - Players with skills: {len(interrogator.player_data[interrogator.player_data['offensive_darko'].notna()])}")
    
    # Show archetype distribution
    print("\n4. Archetype Distribution:")
    archetype_counts = interrogator.player_data['archetype_name'].value_counts()
    for arch, count in archetype_counts.items():
        print(f"   - {arch}: {count} players")
    
    # Find a specific player
    print("\n5. Player Search Demo:")
    search_terms = ["LeBron", "Curry", "Giannis", "Jokic"]
    
    for term in search_terms:
        player = interrogator.get_player_by_name(term)
        if player is not None:
            print(f"   - Found {player['player_name']}: {player['archetype_name']} "
                  f"(O: {player['offensive_darko']:.1f}, D: {player['defensive_darko']:.1f})")
        else:
            print(f"   - {term}: Not found")
    
    # Show top players by skill
    print("\n6. Top 10 Players by Overall DARKO:")
    top_players = interrogator.player_data.nlargest(10, 'darko')
    for _, player in top_players.iterrows():
        print(f"   - {player['player_name']}: {player['archetype_name']} "
              f"(DARKO: {player['darko']:.1f})")
    
    # Test lineup calculation
    print("\n7. Lineup Calculation Demo:")
    print("   Building a lineup with top 5 players...")
    
    top_5_players = interrogator.player_data.nlargest(5, 'darko')
    lineup_ids = top_5_players['player_id'].tolist()
    
    print("   Lineup players:")
    for _, player in top_5_players.iterrows():
        print(f"   - {player['player_name']} ({player['archetype_name']})")
    
    # Calculate lineup value
    lineup_value = interrogator.calculate_lineup_value(lineup_ids)
    
    if "error" in lineup_value:
        print(f"   ❌ Error: {lineup_value['error']}")
    else:
        print(f"\n   Lineup Analysis:")
        print(f"   - Total Value: {lineup_value['total_value']:.3f}")
        print(f"   - Offensive Skill: {lineup_value['offensive_skill']:.1f}")
        print(f"   - Defensive Skill: {lineup_value['defensive_skill']:.1f}")
        print(f"   - Archetype Diversity: {lineup_value['archetype_diversity']}")
        
        print(f"\n   Archetype Breakdown:")
        for arch_id, count in lineup_value['breakdown']['archetype_breakdown'].items():
            arch_name = interrogator.archetype_data[
                interrogator.archetype_data['archetype_id'] == arch_id
            ]['archetype_name'].iloc[0]
            print(f"   - {arch_name}: {count} players")
    
    # Test archetype analysis
    print("\n8. Archetype Analysis Demo:")
    print("   Analyzing '3&D' archetype...")
    
    arch_3d = interrogator.archetype_data[
        interrogator.archetype_data['archetype_name'] == '3&D'
    ]
    
    if not arch_3d.empty:
        arch_id = arch_3d['archetype_id'].iloc[0]
        arch_players = interrogator.get_archetype_players(arch_id)
        
        print(f"   - Total 3&D players: {len(arch_players)}")
        print(f"   - Avg Offensive DARKO: {arch_players['offensive_darko'].mean():.2f}")
        print(f"   - Avg Defensive DARKO: {arch_players['defensive_darko'].mean():.2f}")
        print(f"   - Avg Overall DARKO: {arch_players['darko'].mean():.2f}")
        
        print(f"\n   Top 3&D players:")
        top_3d = arch_players.nlargest(3, 'darko')
        for _, player in top_3d.iterrows():
            print(f"   - {player['player_name']} (DARKO: {player['darko']:.1f})")
    
    print("\n🎉 Demo completed successfully!")
    print("\nTo use the interactive interface, run:")
    print("   python run_interrogation_tool.py")

if __name__ == "__main__":
    main()
