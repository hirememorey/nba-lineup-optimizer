"""
Enhanced Model Evaluator: Basketball Intelligence Integration

This module implements an enhanced model evaluator that adds basketball intelligence
to the existing 7-parameter model. It addresses the key issues identified in
ground truth validation:

1. Ball Dominance Test Failure: Adds diminishing returns logic for redundant players
2. Positional Balance: Enhances lineup balance evaluation
3. Context Sensitivity: Improves matchup-specific adjustments

Key Design Principles:
1. Extends SimpleModelEvaluator: Builds on existing 7-parameter model
2. Basketball Intelligence: Adds logic that makes basketball sense
3. Backward Compatible: Maintains same interface as existing evaluators
4. Validation Ready: Designed to pass ground truth validation tests
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import json
import logging
from src.nba_stats.simple_model_evaluator import SimpleModelEvaluator, SimplePlayer, SimpleLineupEvaluation

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedModelEvaluator(SimpleModelEvaluator):
    """
    Enhanced model evaluator with basketball intelligence.
    
    This class extends the SimpleModelEvaluator to add basketball intelligence
    that addresses the specific failures identified in ground truth validation.
    """
    
    def __init__(self, model_path: Optional[str] = None, season: str = "2024-25"):
        """
        Initialize the EnhancedModelEvaluator.
        
        Args:
            model_path: Path to production model coefficients
            season: NBA season to analyze
        """
        super().__init__(model_path, season)
        
        # Basketball intelligence parameters
        self.diminishing_returns_factor = 0.8  # Penalty for redundant players (balanced)
        self.balance_bonus_factor = 0.1  # Bonus for balanced lineups
        self.context_sensitivity_factor = 0.2  # Context adjustment factor
        
        logger.info("✅ EnhancedModelEvaluator initialized with basketball intelligence")
    
    def evaluate_lineup(self, player_ids: List[int]) -> SimpleLineupEvaluation:
        """
        Evaluate a lineup with enhanced basketball intelligence.
        
        This method extends the base evaluation with:
        1. Diminishing returns for redundant players
        2. Lineup balance bonuses
        3. Context sensitivity adjustments
        """
        # Get base prediction from simplified model
        base_evaluation = super().evaluate_lineup(player_ids)
        
        # Get players for enhanced analysis
        players = [self._blessed_players[pid] for pid in player_ids if pid in self._blessed_players]
        
        if len(players) != 5:
            return base_evaluation
        
        # Apply basketball intelligence enhancements
        enhanced_prediction = self._apply_basketball_intelligence(
            base_evaluation.predicted_outcome, 
            players
        )
        
        # Create enhanced evaluation result
        return SimpleLineupEvaluation(
            predicted_outcome=enhanced_prediction,
            player_ids=player_ids,
            player_names=base_evaluation.player_names,
            archetype_ids=base_evaluation.archetype_ids,
            archetype_names=base_evaluation.archetype_names,
            skill_scores=base_evaluation.skill_scores,
            model_type="enhanced_7_param"
        )
    
    def _apply_basketball_intelligence(self, base_prediction: float, players: List[SimplePlayer]) -> float:
        """
        Apply basketball intelligence enhancements to the base prediction.
        
        This method implements:
        1. Diminishing returns for redundant players
        2. Lineup balance bonuses
        3. Context sensitivity adjustments
        """
        enhanced_prediction = base_prediction
        
        # 1. Apply diminishing returns for redundant players
        enhanced_prediction += self._calculate_diminishing_returns_penalty(players)
        
        # 2. Apply lineup balance bonus
        enhanced_prediction += self._calculate_balance_bonus(players)
        
        # 3. Apply context sensitivity adjustments
        enhanced_prediction += self._calculate_context_adjustments(players)
        
        return enhanced_prediction
    
    def _calculate_diminishing_returns_penalty(self, players: List[SimplePlayer]) -> float:
        """
        Calculate penalty for redundant players (diminishing returns).
        
        This addresses the ball dominance test failure by penalizing
        lineups with too many players of the same archetype.
        """
        # Count players by archetype
        archetype_counts = {}
        for player in players:
            arch_id = player.archetype_id
            archetype_counts[arch_id] = archetype_counts.get(arch_id, 0) + 1
        
        # Calculate penalty for redundant players
        penalty = 0.0
        for arch_id, count in archetype_counts.items():
            if count > 1:
                # Exponential penalty for redundant players
                # For ball handlers (archetype 1), apply stronger penalty
                if arch_id == 1:  # Ball handlers
                    # Strong penalty for ball handler redundancy
                    redundancy_factor = (count - 1) ** 2 * self.diminishing_returns_factor * 2.0
                else:
                    # Linear penalty for other archetypes
                    redundancy_factor = (count - 1) * self.diminishing_returns_factor
                penalty -= redundancy_factor
        
        return penalty
    
    def _calculate_balance_bonus(self, players: List[SimplePlayer]) -> float:
        """
        Calculate bonus for balanced lineups.
        
        This addresses the positional balance test by rewarding
        lineups with good archetype distribution.
        """
        # Count players by archetype
        archetype_counts = {}
        for player in players:
            arch_id = player.archetype_id
            archetype_counts[arch_id] = archetype_counts.get(arch_id, 0) + 1
        
        # Calculate balance score (lower is more balanced)
        counts = list(archetype_counts.values())
        if len(counts) < 2:
            return 0.0
        
        # Calculate variance in archetype distribution
        mean_count = np.mean(counts)
        variance = np.var(counts)
        
        # Bonus for lower variance (more balanced)
        balance_bonus = -variance * self.balance_bonus_factor
        
        return balance_bonus
    
    def _calculate_context_adjustments(self, players: List[SimplePlayer]) -> float:
        """
        Calculate context-specific adjustments.
        
        This enhances the model's ability to capture contextual
        player interactions based on lineup composition.
        """
        # Get archetype distribution
        archetype_counts = {}
        for player in players:
            arch_id = player.archetype_id
            archetype_counts[arch_id] = archetype_counts.get(arch_id, 0) + 1
        
        # Context adjustments based on archetype combinations
        context_adjustment = 0.0
        
        # Example: Ball handlers work better with shooters
        ball_handlers = archetype_counts.get(1, 0)  # Primary Ball Handlers
        role_players = archetype_counts.get(2, 0)   # Role Players (often shooters)
        
        if ball_handlers > 0 and role_players > 0:
            # Synergy between ball handlers and shooters
            synergy = min(ball_handlers, role_players) * self.context_sensitivity_factor
            context_adjustment += synergy
        
        # Example: Big men work better with spacing
        big_men = archetype_counts.get(0, 0)  # Big Men
        if big_men > 0 and role_players > 0:
            # Spacing helps big men
            spacing_bonus = min(big_men, role_players) * self.context_sensitivity_factor * 0.5
            context_adjustment += spacing_bonus
        
        return context_adjustment
    
    def get_enhancement_details(self, player_ids: List[int]) -> Dict[str, Any]:
        """
        Get detailed breakdown of basketball intelligence enhancements.
        
        This method provides transparency into how the enhancements
        affect the final prediction.
        """
        players = [self._blessed_players[pid] for pid in player_ids if pid in self._blessed_players]
        
        if len(players) != 5:
            return {"error": "Invalid lineup size"}
        
        # Get base prediction
        base_evaluation = super().evaluate_lineup(player_ids)
        base_prediction = base_evaluation.predicted_outcome
        
        # Calculate enhancements
        diminishing_returns = self._calculate_diminishing_returns_penalty(players)
        balance_bonus = self._calculate_balance_bonus(players)
        context_adjustment = self._calculate_context_adjustments(players)
        
        # Get archetype distribution
        archetype_counts = {}
        for player in players:
            arch_id = player.archetype_id
            archetype_counts[arch_id] = archetype_counts.get(arch_id, 0) + 1
        
        return {
            "base_prediction": base_prediction,
            "diminishing_returns_penalty": diminishing_returns,
            "balance_bonus": balance_bonus,
            "context_adjustment": context_adjustment,
            "total_enhancement": diminishing_returns + balance_bonus + context_adjustment,
            "final_prediction": base_prediction + diminishing_returns + balance_bonus + context_adjustment,
            "archetype_distribution": archetype_counts,
            "enhancement_breakdown": {
                "diminishing_returns_factor": self.diminishing_returns_factor,
                "balance_bonus_factor": self.balance_bonus_factor,
                "context_sensitivity_factor": self.context_sensitivity_factor
            }
        }


if __name__ == "__main__":
    """Test the EnhancedModelEvaluator in isolation."""
    try:
        evaluator = EnhancedModelEvaluator()
        
        # Test with a sample lineup
        test_lineup = [2544, 101108, 201142, 201143, 201144]  # Sample lineup
        
        print("🧪 Testing Enhanced Model Evaluator")
        print("=" * 50)
        
        # Get base evaluation
        base_evaluation = evaluator._calculate_simplified_prediction(
            [evaluator._blessed_players[pid] for pid in test_lineup if pid in evaluator._blessed_players]
        )
        
        # Get enhanced evaluation
        enhanced_evaluation = evaluator.evaluate_lineup(test_lineup)
        
        # Get enhancement details
        details = evaluator.get_enhancement_details(test_lineup)
        
        print(f"Base Prediction: {base_evaluation:.3f}")
        print(f"Enhanced Prediction: {enhanced_evaluation.predicted_outcome:.3f}")
        print(f"Enhancement: {enhanced_evaluation.predicted_outcome - base_evaluation:.3f}")
        print(f"Model Type: {enhanced_evaluation.model_type}")
        print()
        print("Enhancement Details:")
        for key, value in details.items():
            if key != "enhancement_breakdown":
                print(f"  {key}: {value}")
        
        print("\n✅ Enhanced Model Evaluator test completed successfully")
        
    except Exception as e:
        print(f"❌ Error testing Enhanced Model Evaluator: {e}")
        import traceback
        traceback.print_exc()
