"""
Basketball Validation Test Suite

This script tests the fan-friendly system with real-world examples
to ensure recommendations make basketball sense.
"""

from fan_friendly_mapping import FanFriendlyMapper, PlayerInfo, TeamInfo
import pandas as pd

class BasketballValidator:
    """Validates that recommendations make basketball sense."""
    
    def __init__(self):
        self.mapper = FanFriendlyMapper()
        self.players = []
        self.teams = []
        
    def initialize(self):
        """Initialize with data."""
        if not self.mapper.connect_database():
            print("❌ Failed to connect to database")
            return False
        
        self.players = self.mapper.load_players()
        self.teams = self.mapper.load_teams()
        
        if not self.players or not self.teams:
            print("❌ Failed to load data")
            return False
        
        print(f"✅ Loaded {len(self.players)} players and {len(self.teams)} teams")
        return True
    
    def test_well_known_players(self):
        """Test that well-known players are categorized correctly."""
        print("\n🧪 Testing Well-Known Player Categorizations")
        print("=" * 50)
        
        # Test cases: (player_name, expected_position, expected_role)
        test_cases = [
            ("LeBron James", "PG", "Playmaker"),
            ("Stephen Curry", "PG", "Playmaker"),
            ("Anthony Davis", "C", "Rim Protector"),
            ("Rudy Gobert", "C", "Rim Protector"),
            ("Kawhi Leonard", "SF", "3&D Wing"),
            ("Klay Thompson", "SF", "3&D Wing"),
        ]
        
        for player_name, expected_pos, expected_role in test_cases:
            # Find player
            player = next((p for p in self.players if player_name in p.name), None)
            
            if player:
                pos_match = player.position == expected_pos
                role_match = player.role == expected_role
                
                status = "✅" if pos_match and role_match else "❌"
                print(f"{status} {player.name}: {player.position}/{player.role} (expected: {expected_pos}/{expected_role})")
                
                if not pos_match or not role_match:
                    print(f"   ⚠️  Mismatch: Got {player.position}/{player.role}, expected {expected_pos}/{expected_role}")
            else:
                print(f"❌ {player_name}: Player not found")
    
    def test_team_balance_analysis(self):
        """Test team balance analysis makes sense."""
        print("\n🧪 Testing Team Balance Analysis")
        print("=" * 50)
        
        # Test a few teams
        test_teams = ["Lakers", "Warriors", "Celtics", "Heat"]
        
        for team_name in test_teams:
            team = next((t for t in self.teams if team_name in t.team_name), None)
            
            if team:
                print(f"\n📊 {team.team_name} Analysis:")
                
                # Position balance
                position_balance = self.mapper.get_position_balance(team)
                print(f"   Position Balance: {position_balance}")
                
                # Team needs
                needs = self.mapper.get_team_needs(team)
                print(f"   Team Needs: {needs}")
                
                # Check if needs make sense
                if needs:
                    print(f"   ✅ Identified {len(needs)} team needs")
                else:
                    print(f"   ✅ Well-balanced roster")
            else:
                print(f"❌ {team_name}: Team not found")
    
    def test_fit_explanations(self):
        """Test that fit explanations make basketball sense."""
        print("\n🧪 Testing Fit Explanations")
        print("=" * 50)
        
        # Test with Lakers (should need a PG based on our mapping)
        lakers = next((t for t in self.teams if "Lakers" in t.team_name), None)
        
        if lakers:
            print(f"\n🏀 Testing fit explanations for {lakers.team_name}")
            
            # Test with a few players
            test_players = ["LeBron James", "Stephen Curry", "Anthony Davis", "Kawhi Leonard"]
            
            for player_name in test_players:
                player = next((p for p in self.players if player_name in p.name), None)
                
                if player and player.team_id != lakers.team_id:
                    fit_explanation = self.mapper.generate_fit_explanation(player, lakers)
                    print(f"\n   {player.name} ({player.position} - {player.role}):")
                    print(f"   {fit_explanation}")
                elif player:
                    print(f"\n   {player.name}: Already on {lakers.team_name}")
                else:
                    print(f"\n   {player_name}: Player not found")
    
    def test_search_functionality(self):
        """Test player search functionality."""
        print("\n🧪 Testing Player Search")
        print("=" * 50)
        
        # Test search queries
        search_queries = ["LeBron", "Curry", "Davis", "Leonard", "Giannis"]
        
        for query in search_queries:
            results = self.mapper.search_players(query, self.players)
            print(f"\n🔍 Search: '{query}' -> {len(results)} results")
            
            for player in results[:3]:  # Show top 3
                print(f"   • {player.name} ({player.position} - {player.role}) - {player.team_name}")
    
    def test_free_agent_recommendations(self):
        """Test free agent recommendations."""
        print("\n🧪 Testing Free Agent Recommendations")
        print("=" * 50)
        
        # Get free agents
        free_agents = self.mapper.get_free_agents(self.players)
        print(f"📋 Found {len(free_agents)} free agents")
        
        if free_agents:
            # Show top 5 free agents
            top_free_agents = sorted(free_agents, key=lambda p: p.overall_rating, reverse=True)[:5]
            
            print("\n🏆 Top 5 Free Agents:")
            for i, player in enumerate(top_free_agents, 1):
                print(f"   {i}. {player.name} ({player.position} - {player.role}) - Rating: {player.overall_rating:.1f}")
    
    def test_position_mapping_consistency(self):
        """Test that position mapping is consistent."""
        print("\n🧪 Testing Position Mapping Consistency")
        print("=" * 50)
        
        # Check that all players have valid positions
        valid_positions = {'PG', 'SG', 'SF', 'PF', 'C'}
        valid_roles = {'Rim Protector', 'Playmaker', '3&D Wing'}
        
        invalid_positions = [p for p in self.players if p.position not in valid_positions]
        invalid_roles = [p for p in self.players if p.role not in valid_roles]
        
        if invalid_positions:
            print(f"❌ Found {len(invalid_positions)} players with invalid positions:")
            for player in invalid_positions[:5]:
                print(f"   • {player.name}: {player.position}")
        else:
            print("✅ All players have valid positions")
        
        if invalid_roles:
            print(f"❌ Found {len(invalid_roles)} players with invalid roles:")
            for player in invalid_roles[:5]:
                print(f"   • {player.name}: {player.role}")
        else:
            print("✅ All players have valid roles")
    
    def run_all_tests(self):
        """Run all validation tests."""
        print("🏀 Basketball Validation Test Suite")
        print("=" * 50)
        
        if not self.initialize():
            return False
        
        # Run all tests
        self.test_well_known_players()
        self.test_team_balance_analysis()
        self.test_fit_explanations()
        self.test_search_functionality()
        self.test_free_agent_recommendations()
        self.test_position_mapping_consistency()
        
        print("\n🎉 All tests completed!")
        return True
    
    def close(self):
        """Close database connection."""
        self.mapper.close()

def main():
    """Run the validation tests."""
    validator = BasketballValidator()
    
    try:
        validator.run_all_tests()
    finally:
        validator.close()

if __name__ == "__main__":
    main()
