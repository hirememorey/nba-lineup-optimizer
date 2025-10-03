"""
Player Acquisition Tool

This tool implements the core player acquisition functionality, allowing users to
find the best 5th player for a given 4-player core lineup.

Based on the research paper methodology: given four solidified starters, which fifth 
player should we add to the lineup to maximize effectiveness?
"""

import pandas as pd
import numpy as np
import sqlite3
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class PlayerAcquisitionTool:
    """Core class for player acquisition analysis."""
    
    def __init__(self, db_path: str = "src/nba_stats/db/nba_stats.db"):
        """Initialize the acquisition tool."""
        self.db_path = db_path
        self.conn = None
        self.player_data = None
        self.archetype_data = None
        self.model_coefficients = None
        
    def connect_database(self):
        """Connect to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def load_player_data(self):
        """Load player data with archetypes and skills."""
        if not self.conn:
            return False
            
        try:
            query = """
            SELECT 
                p.player_id,
                p.player_name,
                pa.archetype_id,
                a.archetype_name,
                ps.offensive_darko,
                ps.defensive_darko,
                ps.darko,
                ps.offensive_epm,
                ps.defensive_epm,
                ps.epm
            FROM Players p
            LEFT JOIN PlayerSeasonArchetypes pa ON p.player_id = pa.player_id AND pa.season = '2024-25'
            LEFT JOIN Archetypes a ON pa.archetype_id = a.archetype_id
            LEFT JOIN PlayerSeasonSkill ps ON p.player_id = ps.player_id AND ps.season = '2024-25'
            WHERE pa.archetype_id IS NOT NULL AND ps.offensive_darko IS NOT NULL
            ORDER BY ps.darko DESC
            """
            
            self.player_data = pd.read_sql_query(query, self.conn)
            return True
            
        except Exception as e:
            print(f"Failed to load player data: {e}")
            return False
    
    def load_archetype_data(self):
        """Load archetype definitions."""
        if not self.conn:
            return False
            
        try:
            query = "SELECT * FROM Archetypes ORDER BY archetype_id"
            self.archetype_data = pd.read_sql_query(query, self.conn)
            return True
        except Exception as e:
            print(f"Failed to load archetype data: {e}")
            return False
    
    def load_model_coefficients(self, model_path: str = "model_coefficients.csv") -> bool:
        """Load the trained model coefficients."""
        try:
            if Path(model_path).exists():
                self.model_coefficients = pd.read_csv(model_path)
                return True
            else:
                print(f"Model coefficients not found at {model_path}. Using placeholder values.")
                return False
        except Exception as e:
            print(f"Failed to load model coefficients: {e}")
            return False
    
    def calculate_lineup_value(self, player_ids: List[int]) -> Dict[str, Any]:
        """Calculate the value of a lineup using the trained model."""
        if self.player_data is None:
            return {"error": "Player data not loaded"}
        
        # Get player data for the lineup
        lineup_players = self.player_data[self.player_data['player_id'].isin(player_ids)]
        
        if len(lineup_players) != len(player_ids):
            return {"error": "Some players not found in database"}
        
        # Calculate skill-based value
        total_offensive_skill = lineup_players['offensive_darko'].sum()
        total_defensive_skill = lineup_players['defensive_darko'].sum()
        
        # Use trained model coefficients if available
        if self.model_coefficients is not None:
            # Calculate archetype-weighted skill values
            archetype_skill_value = 0
            archetype_counts = lineup_players['archetype_id'].value_counts()
            
            for arch_id, count in archetype_counts.items():
                arch_coef = self.model_coefficients[
                    self.model_coefficients['archetype_id'] == arch_id
                ]
                
                if not arch_coef.empty:
                    # Get total skill for this archetype
                    arch_players = lineup_players[lineup_players['archetype_id'] == arch_id]
                    arch_offensive_skill = arch_players['offensive_darko'].sum()
                    arch_defensive_skill = arch_players['defensive_darko'].sum()
                    
                    # Apply coefficients
                    arch_value = (
                        arch_offensive_skill * arch_coef['beta_offensive'].iloc[0] +
                        arch_defensive_skill * arch_coef['beta_defensive'].iloc[0]
                    )
                    archetype_skill_value += arch_value
            
            final_value = archetype_skill_value
        else:
            # Fallback to simple heuristic
            base_value = total_offensive_skill * 0.1 - total_defensive_skill * 0.1
            
            # Add archetype diversity penalty
            archetype_counts = lineup_players['archetype_id'].value_counts()
            diversity_penalty = 0
            for arch_id, count in archetype_counts.items():
                if count > 1:
                    diversity_penalty += (count - 1) * 0.05
            
            final_value = base_value - diversity_penalty
        
        return {
            "total_value": final_value,
            "offensive_skill": total_offensive_skill,
            "defensive_skill": total_defensive_skill,
            "archetype_diversity": len(archetype_counts),
            "breakdown": {
                "skill_value": final_value,
                "archetype_breakdown": archetype_counts.to_dict()
            }
        }
    
    def find_best_fifth_player(self, core_player_ids: List[int], 
                              max_salary: float = 25_000_000,
                              exclude_player_ids: List[int] = None) -> List[Dict[str, Any]]:
        """
        Find the best 5th player for a given 4-player core lineup.
        
        Args:
            core_player_ids: List of 4 player IDs forming the core lineup
            max_salary: Maximum salary for the 5th player (placeholder - not implemented yet)
            exclude_player_ids: List of player IDs to exclude from consideration
        
        Returns:
            List of recommended players sorted by lineup value
        """
        if len(core_player_ids) != 4:
            return [{"error": "Core lineup must contain exactly 4 players"}]
        
        if self.player_data is None:
            return [{"error": "Player data not loaded"}]
        
        # Get available players (excluding core players and any excluded players)
        exclude_ids = set(core_player_ids)
        if exclude_player_ids:
            exclude_ids.update(exclude_player_ids)
        
        available_players = self.player_data[
            ~self.player_data['player_id'].isin(exclude_ids)
        ].copy()
        
        if available_players.empty:
            return [{"error": "No available players for acquisition"}]
        
        # Test each available player as the 5th player
        recommendations = []
        
        for _, player in available_players.iterrows():
            test_lineup = core_player_ids + [player['player_id']]
            lineup_value = self.calculate_lineup_value(test_lineup)
            
            if "error" not in lineup_value:
                # Calculate the marginal value this player adds
                core_value = self.calculate_lineup_value(core_player_ids)
                if "error" not in core_value:
                    marginal_value = lineup_value['total_value'] - core_value['total_value']
                else:
                    marginal_value = lineup_value['total_value']
                
                recommendations.append({
                    'player_id': player['player_id'],
                    'player_name': player['player_name'],
                    'archetype_name': player['archetype_name'],
                    'offensive_darko': player['offensive_darko'],
                    'defensive_darko': player['defensive_darko'],
                    'overall_darko': player['darko'],
                    'lineup_value': lineup_value['total_value'],
                    'marginal_value': marginal_value,
                    'archetype_diversity': lineup_value['archetype_diversity'],
                    'skill_breakdown': {
                        'offensive_skill': lineup_value['offensive_skill'],
                        'defensive_skill': lineup_value['defensive_skill']
                    }
                })
        
        # Sort by marginal value (how much this player improves the lineup)
        recommendations.sort(key=lambda x: x['marginal_value'], reverse=True)
        
        return recommendations
    
    def get_player_by_name(self, name: str) -> Optional[pd.Series]:
        """Get player data by name (fuzzy matching)."""
        if self.player_data is None:
            return None
            
        # Try exact match first
        exact_match = self.player_data[self.player_data['player_name'].str.lower() == name.lower()]
        if not exact_match.empty:
            return exact_match.iloc[0]
        
        # Try partial match
        partial_match = self.player_data[self.player_data['player_name'].str.contains(name, case=False, na=False)]
        if not partial_match.empty:
            return partial_match.iloc[0]
        
        return None
    
    def analyze_core_lineup(self, core_player_ids: List[int]) -> Dict[str, Any]:
        """Analyze the current core lineup to understand its characteristics."""
        if len(core_player_ids) != 4:
            return {"error": "Core lineup must contain exactly 4 players"}
        
        if self.player_data is None:
            return {"error": "Player data not loaded"}
        
        # Get core player data
        core_players = self.player_data[self.player_data['player_id'].isin(core_player_ids)]
        
        if len(core_players) != 4:
            return {"error": "Some core players not found in database"}
        
        # Calculate core lineup value
        core_value = self.calculate_lineup_value(core_player_ids)
        
        if "error" in core_value:
            return core_value
        
        # Analyze archetype distribution
        archetype_counts = core_players['archetype_id'].value_counts()
        archetype_names = {}
        for arch_id, count in archetype_counts.items():
            arch_name = core_players[core_players['archetype_id'] == arch_id]['archetype_name'].iloc[0]
            archetype_names[arch_name] = count
        
        # Calculate skill statistics
        total_offensive_skill = core_players['offensive_darko'].sum()
        total_defensive_skill = core_players['defensive_darko'].sum()
        avg_offensive_skill = core_players['offensive_darko'].mean()
        avg_defensive_skill = core_players['defensive_darko'].mean()
        
        return {
            "core_value": core_value['total_value'],
            "archetype_distribution": archetype_names,
            "archetype_diversity": len(archetype_counts),
            "skill_summary": {
                "total_offensive_skill": total_offensive_skill,
                "total_defensive_skill": total_defensive_skill,
                "avg_offensive_skill": avg_offensive_skill,
                "avg_defensive_skill": avg_defensive_skill
            },
            "players": core_players[['player_name', 'archetype_name', 'offensive_darko', 'defensive_darko']].to_dict('records')
        }


def main():
    """Demo the Player Acquisition Tool."""
    print("🏀 NBA Player Acquisition Tool Demo")
    print("=" * 50)
    
    # Initialize the tool
    tool = PlayerAcquisitionTool()
    
    # Connect to database
    if not tool.connect_database():
        print("❌ Failed to connect to database")
        return
    
    # Load data
    print("Loading data...")
    if not tool.load_player_data():
        print("❌ Failed to load player data")
        return
    
    if not tool.load_archetype_data():
        print("❌ Failed to load archetype data")
        return
    
    if not tool.load_model_coefficients():
        print("⚠️ Using placeholder model coefficients")
    
    print("✅ Data loaded successfully!")
    print()
    
    # Demo: Lakers core analysis
    print("Demo: Lakers Core Analysis")
    print("-" * 30)
    
    # Find Lakers core players
    lakers_core_names = ["LeBron James", "Anthony Davis", "Austin Reaves", "Rui Hachimura"]
    lakers_core_ids = []
    
    for name in lakers_core_names:
        player = tool.get_player_by_name(name)
        if player is not None:
            lakers_core_ids.append(player['player_id'])
            print(f"Found: {name} ({player['archetype_name']})")
        else:
            print(f"Not found: {name}")
    
    if len(lakers_core_ids) == 4:
        print()
        
        # Analyze core lineup
        core_analysis = tool.analyze_core_lineup(lakers_core_ids)
        
        if "error" not in core_analysis:
            print(f"Core lineup value: {core_analysis['core_value']:.3f}")
            print(f"Archetype diversity: {core_analysis['archetype_diversity']}")
            print("Archetype distribution:")
            for arch, count in core_analysis['archetype_distribution'].items():
                print(f"  {arch}: {count}")
            
            print()
            print("Finding best 5th player...")
            
            # Find best 5th player
            recommendations = tool.find_best_fifth_player(lakers_core_ids, max_salary=25_000_000)
            
            if recommendations and "error" not in recommendations[0]:
                print(f"Top 5 recommendations:")
                print()
                
                for i, rec in enumerate(recommendations[:5], 1):
                    print(f"{i}. {rec['player_name']} ({rec['archetype_name']})")
                    print(f"   Marginal value: {rec['marginal_value']:.3f}")
                    print(f"   Overall DARKO: {rec['overall_darko']:.2f}")
                    print(f"   Offensive: {rec['offensive_darko']:.2f}, Defensive: {rec['defensive_darko']:.2f}")
                    print()
            else:
                print("❌ No recommendations found")
        else:
            print(f"❌ Error analyzing core lineup: {core_analysis['error']}")
    else:
        print(f"❌ Only found {len(lakers_core_ids)}/4 Lakers core players")
    
    print("Demo complete!")


if __name__ == "__main__":
    main()
