"""
Simple 2022-23 Evaluator for Ground Truth Validation

This module provides a minimal lineup evaluator specifically designed for 2022-23 data
to test ground truth basketball cases before attempting to reproduce the original paper.

Key Design Principles:
1. Data Reality First: Works with actual 2022-23 table structure
2. Simple Heuristics: Start with basic basketball logic
3. Ground Truth Focus: Test against known basketball outcomes
4. Minimal Dependencies: Avoid complex existing infrastructure
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Player2023:
    """Represents a 2022-23 player with available data."""
    player_id: int
    player_name: str
    offensive_darko: float
    defensive_darko: float
    darko: float
    # Archetype features (simplified)
    archetype_features: Dict[str, float]


@dataclass
class LineupEvaluation2023:
    """Result of evaluating a 2022-23 lineup."""
    lineup_ids: List[int]
    predicted_outcome: float
    confidence: float
    breakdown: Dict[str, float]
    basketball_explanation: str


class Simple2022_23Evaluator:
    """
    Minimal evaluator for 2022-23 data that focuses on ground truth validation.
    
    This evaluator is designed to test fundamental basketball principles
    before attempting to reproduce the complex original paper methodology.
    """
    
    def __init__(self, db_path: str = "src/nba_stats/db/nba_stats.db"):
        """
        Initialize the evaluator with 2022-23 data.
        
        Args:
            db_path: Path to the database
        """
        self.db_path = db_path
        self.players: Dict[int, Player2023] = {}
        self._load_2022_23_players()
        
        if not self.players:
            raise ValueError("No 2022-23 players loaded")
        
        print(f"✅ Simple2022_23Evaluator initialized with {len(self.players)} players")
    
    def _load_2022_23_players(self) -> None:
        """Load 2022-23 players with complete data."""
        with sqlite3.connect(self.db_path) as conn:
            # Load players with skills and archetype features
            query = """
            SELECT 
                p.player_id,
                pl.player_name,
                s.offensive_darko,
                s.defensive_darko,
                s.darko,
                p.FTPCT, p.TSPCT, p.THPAr, p.FTr, p.TRBPCT, p.ASTPCT,
                p.FRNTCTTCH, p.TOP, p.AVGSECPERTCH, p.AVGDRIBPERTCH, p.ELBWTCH,
                p.POSTUPS, p.PNTTOUCH, p.DRIVES, p.DRFGA, p.DRPTSPCT, p.DRPASSPCT,
                p.DRASTPCT, p.DRTOVPCT, p.DRPFPCT, p.DRIMFGPCT, p.CSFGA, p.CS3PA,
                p.PASSESMADE, p.SECAST, p.POTAST, p.PUFGA, p.PU3PA, p.PSTUPFGA,
                p.PSTUPPTSPCT, p.PSTUPPASSPCT, p.PSTUPASTPCT, p.PSTUPTOVPCT,
                p.PNTTCHS, p.PNTFGA, p.PNTPTSPCT, p.PNTPASSPCT, p.PNTASTPCT, p.PNTTVPCT,
                p.AVGFGATTEMPTEDAGAINSTPERGAME
            FROM PlayerArchetypeFeatures_2022_23 p
            JOIN Players pl ON p.player_id = pl.player_id
            JOIN PlayerSeasonSkill s ON p.player_id = s.player_id AND s.season = '2022-23'
            WHERE s.offensive_darko IS NOT NULL 
            AND s.defensive_darko IS NOT NULL
            ORDER BY s.darko DESC
            """
            
            df = pd.read_sql_query(query, conn)
            
            for _, row in df.iterrows():
                # Extract archetype features
                archetype_features = {
                    'FTPCT': row['FTPCT'], 'TSPCT': row['TSPCT'], 'THPAr': row['THPAr'],
                    'FTr': row['FTr'], 'TRBPCT': row['TRBPCT'], 'ASTPCT': row['ASTPCT'],
                    'FRNTCTTCH': row['FRNTCTTCH'], 'TOP': row['TOP'], 'AVGSECPERTCH': row['AVGSECPERTCH'],
                    'AVGDRIBPERTCH': row['AVGDRIBPERTCH'], 'ELBWTCH': row['ELBWTCH'], 'POSTUPS': row['POSTUPS'],
                    'PNTTOUCH': row['PNTTOUCH'], 'DRIVES': row['DRIVES'], 'DRFGA': row['DRFGA'],
                    'DRPTSPCT': row['DRPTSPCT'], 'DRPASSPCT': row['DRPASSPCT'], 'DRASTPCT': row['DRASTPCT'],
                    'DRTOVPCT': row['DRTOVPCT'], 'DRPFPCT': row['DRPFPCT'], 'DRIMFGPCT': row['DRIMFGPCT'],
                    'CSFGA': row['CSFGA'], 'CS3PA': row['CS3PA'], 'PASSESMADE': row['PASSESMADE'],
                    'SECAST': row['SECAST'], 'POTAST': row['POTAST'], 'PUFGA': row['PUFGA'],
                    'PU3PA': row['PU3PA'], 'PSTUPFGA': row['PSTUPFGA'], 'PSTUPPTSPCT': row['PSTUPPTSPCT'],
                    'PSTUPPASSPCT': row['PSTUPPASSPCT'], 'PSTUPASTPCT': row['PSTUPASTPCT'],
                    'PSTUPTOVPCT': row['PSTUPTOVPCT'], 'PNTTCHS': row['PNTTCHS'], 'PNTFGA': row['PNTFGA'],
                    'PNTPTSPCT': row['PNTPTSPCT'], 'PNTPASSPCT': row['PNTPASSPCT'],
                    'PNTASTPCT': row['PNTASTPCT'], 'PNTTVPCT': row['PNTTVPCT'],
                    'AVGFGATTEMPTEDAGAINSTPERGAME': row['AVGFGATTEMPTEDAGAINSTPERGAME']
                }
                
                player = Player2023(
                    player_id=int(row['player_id']),
                    player_name=str(row['player_name']),
                    offensive_darko=float(row['offensive_darko']),
                    defensive_darko=float(row['defensive_darko']),
                    darko=float(row['darko']),
                    archetype_features=archetype_features
                )
                self.players[player.player_id] = player
    
    def get_available_players(self) -> List[Player2023]:
        """Get all available 2022-23 players."""
        return list(self.players.values())
    
    def get_player_by_id(self, player_id: int) -> Optional[Player2023]:
        """Get a specific player by ID."""
        return self.players.get(player_id)
    
    def get_player_by_name(self, name: str) -> Optional[Player2023]:
        """Get a player by name (case-insensitive)."""
        name_lower = name.lower()
        for player in self.players.values():
            if player.player_name.lower() == name_lower:
                return player
        return None
    
    def evaluate_lineup(self, player_ids: List[int]) -> LineupEvaluation2023:
        """
        Evaluate a lineup using simple basketball heuristics.
        
        This is a simplified evaluation that focuses on testing fundamental
        basketball principles rather than reproducing the complex paper methodology.
        """
        if len(player_ids) != 5:
            raise ValueError("Lineup must have exactly 5 players")
        
        # Load players
        lineup_players = []
        for player_id in player_ids:
            if player_id not in self.players:
                raise ValueError(f"Player {player_id} not found in 2022-23 data")
            lineup_players.append(self.players[player_id])
        
        # Simple evaluation based on basketball principles
        total_offensive_skill = sum(p.offensive_darko for p in lineup_players)
        total_defensive_skill = sum(p.defensive_darko for p in lineup_players)
        
        # Basic skill balance
        skill_balance = min(total_offensive_skill, total_defensive_skill) / max(total_offensive_skill, total_defensive_skill) if max(total_offensive_skill, total_defensive_skill) > 0 else 0
        
        # Simple archetype diversity (based on key metrics)
        archetype_diversity = self._calculate_archetype_diversity(lineup_players)
        
        # Redundancy penalty (simplified)
        redundancy_penalty = self._calculate_redundancy_penalty(lineup_players)
        
        # Overall score
        base_score = (total_offensive_skill + total_defensive_skill) / 5
        balanced_score = base_score * skill_balance
        diverse_score = balanced_score * archetype_diversity
        final_score = diverse_score * (1 - redundancy_penalty)
        
        # Generate basketball explanation
        explanation = self._generate_basketball_explanation(
            lineup_players, total_offensive_skill, total_defensive_skill,
            skill_balance, archetype_diversity, redundancy_penalty
        )
        
        return LineupEvaluation2023(
            lineup_ids=player_ids,
            predicted_outcome=final_score,
            confidence=min(archetype_diversity, skill_balance),
            breakdown={
                'total_offensive_skill': total_offensive_skill,
                'total_defensive_skill': total_defensive_skill,
                'skill_balance': skill_balance,
                'archetype_diversity': archetype_diversity,
                'redundancy_penalty': redundancy_penalty
            },
            basketball_explanation=explanation
        )
    
    def _calculate_archetype_diversity(self, players: List[Player2023]) -> float:
        """Calculate archetype diversity based on key metrics."""
        # Use key metrics to determine player roles
        roles = []
        for player in players:
            features = player.archetype_features
            
            # Simple role classification based on key metrics
            if features['ASTPCT'] > 0.25 and features['DRIVES'] > 5:
                roles.append('playmaker')
            elif features['CS3PA'] > 2 and features['DRPTSPCT'] > 0.35:
                roles.append('3d_wing')
            elif features['POSTUPS'] > 1 and features['PNTTOUCH'] > 3:
                roles.append('big')
            elif features['DRIVES'] > 4 and features['PUFGA'] > 2:
                roles.append('scorer')
            else:
                roles.append('role_player')
        
        # Calculate diversity (more unique roles = higher diversity)
        unique_roles = len(set(roles))
        return min(unique_roles / 5, 1.0)  # Normalize to 0-1
    
    def _calculate_redundancy_penalty(self, players: List[Player2023]) -> float:
        """Calculate redundancy penalty for similar players."""
        # Simple redundancy based on similar skill profiles
        penalties = []
        
        for i, player1 in enumerate(players):
            for j, player2 in enumerate(players[i+1:], i+1):
                # Calculate similarity based on key metrics
                similarity = self._calculate_player_similarity(player1, player2)
                if similarity > 0.8:  # High similarity threshold
                    penalties.append(similarity * 0.1)  # Small penalty per redundant player
        
        return min(sum(penalties), 0.5)  # Cap at 50% penalty
    
    def _calculate_player_similarity(self, player1: Player2023, player2: Player2023) -> float:
        """Calculate similarity between two players based on key metrics."""
        key_metrics = ['ASTPCT', 'DRIVES', 'CS3PA', 'POSTUPS', 'PNTTOUCH', 'DRPTSPCT']
        
        similarities = []
        for metric in key_metrics:
            val1 = player1.archetype_features[metric]
            val2 = player2.archetype_features[metric]
            
            # Normalize and calculate similarity
            if val1 == 0 and val2 == 0:
                similarities.append(1.0)
            elif val1 == 0 or val2 == 0:
                similarities.append(0.0)
            else:
                similarity = 1 - abs(val1 - val2) / max(val1, val2)
                similarities.append(max(0, similarity))
        
        return np.mean(similarities)
    
    def _generate_basketball_explanation(self, players: List[Player2023], 
                                       off_skill: float, def_skill: float,
                                       balance: float, diversity: float, 
                                       redundancy: float) -> str:
        """Generate a basketball explanation for the lineup evaluation."""
        explanations = []
        
        # Skill level
        avg_skill = (off_skill + def_skill) / 10  # Normalize
        if avg_skill > 2.0:
            explanations.append("High overall talent level")
        elif avg_skill > 1.0:
            explanations.append("Solid talent level")
        else:
            explanations.append("Below average talent level")
        
        # Balance
        if balance > 0.8:
            explanations.append("excellent offensive/defensive balance")
        elif balance > 0.6:
            explanations.append("good offensive/defensive balance")
        else:
            explanations.append("imbalanced (too much offense or defense)")
        
        # Diversity
        if diversity > 0.8:
            explanations.append("good role diversity")
        elif diversity > 0.6:
            explanations.append("decent role diversity")
        else:
            explanations.append("limited role diversity")
        
        # Redundancy
        if redundancy > 0.3:
            explanations.append("some redundant skills")
        elif redundancy > 0.1:
            explanations.append("minimal redundancy")
        else:
            explanations.append("well-distributed skills")
        
        return f"Lineup has {', '.join(explanations)}."


def test_ground_truth_cases():
    """Test the evaluator against known basketball ground truth cases."""
    print("🏀 Testing Ground Truth Basketball Cases")
    print("=" * 50)
    
    evaluator = Simple2022_23Evaluator()
    
    # Test 1: Find key players
    lebron = evaluator.get_player_by_name("LeBron James")
    ad = evaluator.get_player_by_name("Anthony Davis")
    westbrook = evaluator.get_player_by_name("Russell Westbrook")
    kawhi = evaluator.get_player_by_name("Kawhi Leonard")
    
    print(f"Key players found:")
    print(f"  LeBron: {lebron.player_id if lebron else 'Not found'}")
    print(f"  AD: {ad.player_id if ad else 'Not found'}")
    print(f"  Westbrook: {westbrook.player_id if westbrook else 'Not found'}")
    print(f"  Kawhi: {kawhi.player_id if kawhi else 'Not found'}")
    
    if lebron and ad and westbrook and kawhi:
        # Test 2: Lakers lineup (LeBron + AD + Westbrook + 2 others)
        print(f"\\nTesting Lakers lineup...")
        lakers_players = [lebron, ad, westbrook]
        
        # Find 2 more Lakers players
        lakers_others = [p for p in evaluator.get_available_players() 
                        if p.player_name in ["Austin Reaves", "Rui Hachimura", "D'Angelo Russell"]][:2]
        
        if len(lakers_others) >= 2:
            lakers_lineup = [p.player_id for p in lakers_players + lakers_others]
            lakers_result = evaluator.evaluate_lineup(lakers_lineup)
            print(f"  Lakers lineup score: {lakers_result.predicted_outcome:.3f}")
            print(f"  Explanation: {lakers_result.basketball_explanation}")
        
        # Test 3: Clippers lineup (Kawhi + 4 others)
        print(f"\\nTesting Clippers lineup...")
        clippers_others = [p for p in evaluator.get_available_players() 
                          if p.player_name in ["Paul George", "Ivica Zubac", "Marcus Morris", "Reggie Jackson"]][:4]
        
        if len(clippers_others) >= 4:
            clippers_lineup = [kawhi.player_id] + [p.player_id for p in clippers_others]
            clippers_result = evaluator.evaluate_lineup(clippers_lineup)
            print(f"  Clippers lineup score: {clippers_result.predicted_outcome:.3f}")
            print(f"  Explanation: {clippers_result.basketball_explanation}")
    
    print(f"\\n✅ Ground truth testing complete!")


if __name__ == "__main__":
    test_ground_truth_cases()
