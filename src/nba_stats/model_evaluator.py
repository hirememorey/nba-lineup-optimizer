"""
ModelEvaluator: Defensive Core for NBA Lineup Analysis

This module implements the core ModelEvaluator class that serves as the
foundation for all lineup analysis tools. It is designed to be defensive
against data incompleteness and schema inconsistencies.

Key Design Principles:
1. Data Integrity First: Only works with "blessed" players who have complete data
2. Schema Abstraction: Uses db_mapping to handle database reality
3. Defensive Programming: Fails fast with clear error messages
4. Single Source of Truth: All tools use this same logic
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import csv
from dataclasses import dataclass
try:
    from .db_mapping import db_mapping
except ImportError:
    # Handle direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from db_mapping import db_mapping


@dataclass
class Player:
    """Represents a complete player with all required data."""
    player_id: int
    player_name: str
    offensive_darko: float
    defensive_darko: float
    darko: float
    archetype_id: int
    archetype_name: str


@dataclass
class LineupEvaluation:
    """Result of evaluating a lineup."""
    predicted_outcome: float
    player_ids: List[int]
    player_names: List[str]
    archetype_ids: List[int]
    archetype_names: List[str]
    skill_scores: Dict[str, float]


class IncompletePlayerError(Exception):
    """Raised when trying to evaluate a player with incomplete data."""
    pass


class InvalidLineupError(Exception):
    """Raised when lineup doesn't meet requirements."""
    pass


class ModelEvaluator:
    """
    Defensive core for NBA lineup analysis.
    
    This class implements the key insight from the post-mortem: the code
    for validating the model and using the model must be the same code.
    All tools (validation, acquisition, optimization) use this class.
    """
    
    def __init__(self, model_path: Optional[str] = None, season: str = "2024-25"):
        """
        Initialize the ModelEvaluator with defensive data loading.
        
        Args:
            model_path: Path to model coefficients (placeholder for now)
            season: NBA season to analyze
            
        Raises:
            FileNotFoundError: If database not found
            ValueError: If no complete players found
        """
        self.season = season
        self.model_path = model_path
        self._blessed_players: Dict[int, Player] = {}
        self._model_coefficients: Optional[Dict[str, float]] = None
        self._trained_betas: Optional[Dict[str, Any]] = None  # {'beta0': float, 'beta_off': [8], 'beta_def': [8]}
        
        # Database path
        self.db_path = Path("src/nba_stats/db/nba_stats.db")
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}")
        
        # Load and validate data
        self._load_blessed_players()
        self._load_model_coefficients()
        
        if not self._blessed_players:
            raise ValueError(f"No complete players found for season {season}")
        
        print(f"✅ ModelEvaluator initialized with {len(self._blessed_players)} blessed players")
    
    def _load_blessed_players(self) -> None:
        """
        Load only players with complete data (skills + archetypes).
        
        This implements the critical insight: we must work with the intersection
        of skill and archetype data, not the union.
        """
        with sqlite3.connect(self.db_path) as conn:
            # Use the query template from db_mapping
            query = db_mapping.get_query_template("get_player_skills")
            skills_df = pd.read_sql_query(query, conn, params=[self.season])
            
            archetype_query = db_mapping.get_query_template("get_player_archetypes")
            archetypes_df = pd.read_sql_query(archetype_query, conn, params=[self.season])
            
            # Perform the critical inner join
            complete_players = pd.merge(
                skills_df, 
                archetypes_df, 
                on=['player_id', 'season'], 
                how='inner'
            )
            
            # Create blessed players dictionary
            for _, row in complete_players.iterrows():
                player = Player(
                    player_id=int(row['player_id']),
                    player_name=str(row['player_name']),
                    offensive_darko=float(row['offensive_darko']),
                    defensive_darko=float(row['defensive_darko']),
                    darko=float(row['darko']),
                    archetype_id=int(row['archetype_id']),
                    archetype_name=str(row['archetype_name'])
                )
                self._blessed_players[player.player_id] = player
    
    def _load_model_coefficients(self) -> None:
        """
        Load model coefficients from trained CSV if available; otherwise, use placeholders.
        
        Expected CSV schema: parameter,mean with rows like beta_0, beta_off[1..8], beta_def[1..8]
        """
        # Try to locate model coefficients
        csv_path = None
        if self.model_path and Path(self.model_path).exists():
            csv_path = Path(self.model_path)
        else:
            default_path = Path("model_coefficients.csv")
            if default_path.exists():
                csv_path = default_path
        
        if csv_path is not None:
            try:
                df = pd.read_csv(csv_path)
                params = dict(zip(df['parameter'], df['mean']))
                beta0 = float(params.get('beta_0', 0.0))
                beta_off = [0.0]*8
                beta_def = [0.0]*8
                for i in range(1, 9):
                    beta_off[i-1] = float(params.get(f'beta_off[{i}]', 0.0))
                    beta_def[i-1] = float(params.get(f'beta_def[{i}]', 0.0))
                self._trained_betas = {'beta0': beta0, 'beta_off': beta_off, 'beta_def': beta_def}
            except Exception:
                # Fall back to placeholder if CSV unreadable
                self._trained_betas = None
        
        # Always keep placeholder coefficients for auxiliary effects and as fallback
        self._model_coefficients = {
            'offensive_skill_impact': 0.1,
            'defensive_skill_impact': -0.08,
            'archetype_synergy_base': 0.05,
            'archetype_anti_synergy_base': -0.03,
            'lineup_balance_bonus': 0.02,
            'skill_variance_penalty': -0.01,
        }
    
    def get_available_players(self) -> List[Player]:
        """
        Get all players available for lineup evaluation.
        
        Returns:
            List of Player objects with complete data
            
        Note:
            This is the public contract. Any player returned by this method
            is guaranteed to work in evaluate_lineup().
        """
        return list(self._blessed_players.values())
    
    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """
        Get a specific player by ID.
        
        Args:
            player_id: Player ID to look up
            
        Returns:
            Player object if found and complete, None otherwise
        """
        return self._blessed_players.get(player_id)
    
    def evaluate_lineup(self, player_ids: List[int]) -> LineupEvaluation:
        """
        Evaluate a lineup of 5 players.
        
        Args:
            player_ids: List of exactly 5 player IDs
            
        Returns:
            LineupEvaluation object with prediction and metadata
            
        Raises:
            InvalidLineupError: If lineup doesn't have exactly 5 players
            IncompletePlayerError: If any player is not in blessed set
        """
        if len(player_ids) != 5:
            raise InvalidLineupError(f"Lineup must have exactly 5 players, got {len(player_ids)}")
        
        # Validate all players are blessed
        players = []
        for player_id in player_ids:
            if player_id not in self._blessed_players:
                raise IncompletePlayerError(
                    f"Player {player_id} not in blessed set. "
                    f"Use get_available_players() to see valid players."
                )
            players.append(self._blessed_players[player_id])
        
        # Calculate prediction using placeholder model
        prediction = self._calculate_lineup_prediction(players)
        
        # Create evaluation result
        return LineupEvaluation(
            predicted_outcome=prediction,
            player_ids=player_ids,
            player_names=[p.player_name for p in players],
            archetype_ids=[p.archetype_id for p in players],
            archetype_names=[p.archetype_name for p in players],
            skill_scores=self._calculate_skill_scores(players)
        )
    
    def _calculate_lineup_prediction(self, players: List[Player]) -> float:
        """
        Calculate lineup prediction using placeholder model.
        
        This implements a simplified version of the Bayesian model logic
        that makes basketball sense for validation purposes.
        """
        if not self._model_coefficients:
            raise ValueError("Model coefficients not loaded")
        
        # If trained betas are available, use them to weight skills by archetype
        if self._trained_betas is not None:
            beta0 = self._trained_betas['beta0']
            beta_off = self._trained_betas['beta_off']
            beta_def = self._trained_betas['beta_def']
            off_sum = 0.0
            def_sum = 0.0
            for p in players:
                idx = int(p.archetype_id)
                if 0 <= idx < 8:
                    off_sum += beta_off[idx] * float(p.offensive_darko)
                    def_sum += beta_def[idx] * float(p.defensive_darko)
            # Average to stabilize scale across 5 players
            skill_contribution = beta0 + (off_sum / 5.0) - (def_sum / 5.0)
        else:
            # Placeholder base skill contributions
            offensive_skill = np.mean([p.offensive_darko for p in players])
            defensive_skill = np.mean([p.defensive_darko for p in players])
            skill_contribution = (
                offensive_skill * self._model_coefficients['offensive_skill_impact'] +
                defensive_skill * self._model_coefficients['defensive_skill_impact']
            )
        
        # Archetype synergy effects
        archetype_ids = [p.archetype_id for p in players]
        synergy_contribution = self._calculate_archetype_synergy(archetype_ids)
        
        # Lineup balance effects
        balance_contribution = self._calculate_lineup_balance(players)
        
        # Total prediction
        total_prediction = skill_contribution + synergy_contribution + balance_contribution
        
        return float(total_prediction)
    
    def _calculate_archetype_synergy(self, archetype_ids: List[int]) -> float:
        """
        Calculate archetype synergy effects.
        
        This is a simplified version that checks for:
        - Balanced archetype distribution
        - Some basic synergy patterns
        """
        # Count archetype distribution
        archetype_counts = {}
        for arch_id in archetype_ids:
            archetype_counts[arch_id] = archetype_counts.get(arch_id, 0) + 1
        
        # Penalty for too many of the same archetype
        max_count = max(archetype_counts.values())
        diversity_penalty = (max_count - 1) * 0.01
        
        # Base synergy bonus for having different archetypes
        diversity_bonus = len(set(archetype_ids)) * 0.005
        
        return diversity_bonus - diversity_penalty
    
    def _calculate_lineup_balance(self, players: List[Player]) -> float:
        """
        Calculate lineup balance effects.
        
        This checks for:
        - Skill variance (too much or too little)
        - Overall skill level
        """
        skills = [p.darko for p in players]
        skill_variance = np.var(skills)
        skill_mean = np.mean(skills)
        
        # Penalty for extreme skill variance
        variance_penalty = skill_variance * self._model_coefficients['skill_variance_penalty']
        
        # Bonus for balanced skill distribution
        balance_bonus = self._model_coefficients['lineup_balance_bonus']
        
        return variance_penalty + balance_bonus
    
    def _calculate_skill_scores(self, players: List[Player]) -> Dict[str, float]:
        """Calculate various skill metrics for the lineup."""
        return {
            'avg_offensive_darko': np.mean([p.offensive_darko for p in players]),
            'avg_defensive_darko': np.mean([p.defensive_darko for p in players]),
            'avg_overall_darko': np.mean([p.darko for p in players]),
            'skill_variance': np.var([p.darko for p in players]),
            'archetype_diversity': len(set(p.archetype_id for p in players))
        }
    
    def find_best_fit(self, core_player_ids: List[int], candidate_ids: List[int]) -> Tuple[Player, LineupEvaluation]:
        """
        Find the best fifth player for a core of 4 players.
        
        Args:
            core_player_ids: List of 4 player IDs forming the core
            candidate_ids: List of candidate player IDs to evaluate
            
        Returns:
            Tuple of (best_player, best_evaluation)
            
        Raises:
            InvalidLineupError: If core doesn't have exactly 4 players
            ValueError: If no valid candidates found
        """
        if len(core_player_ids) != 4:
            raise InvalidLineupError(f"Core must have exactly 4 players, got {len(core_player_ids)}")
        
        # Filter candidates to only blessed players
        valid_candidates = [
            pid for pid in candidate_ids 
            if pid in self._blessed_players
        ]
        
        if not valid_candidates:
            raise ValueError("No valid candidates found in blessed player set")
        
        # Evaluate each candidate
        best_player = None
        best_evaluation = None
        best_score = float('-inf')
        
        for candidate_id in valid_candidates:
            try:
                lineup_ids = core_player_ids + [candidate_id]
                evaluation = self.evaluate_lineup(lineup_ids)
                
                if evaluation.predicted_outcome > best_score:
                    best_score = evaluation.predicted_outcome
                    best_player = self._blessed_players[candidate_id]
                    best_evaluation = evaluation
                    
            except (IncompletePlayerError, InvalidLineupError):
                # Skip invalid lineups
                continue
        
        if best_player is None:
            raise ValueError("No valid lineups could be formed with the given candidates")
        
        return best_player, best_evaluation
    
    def get_stats_summary(self) -> Dict[str, Any]:
        """Get summary statistics about the evaluator's data."""
        players = list(self._blessed_players.values())
        
        return {
            'total_players': len(players),
            'season': self.season,
            'archetype_distribution': {
                arch_id: sum(1 for p in players if p.archetype_id == arch_id)
                for arch_id in set(p.archetype_id for p in players)
            },
            'skill_ranges': {
                'offensive_darko': {
                    'min': min(p.offensive_darko for p in players),
                    'max': max(p.offensive_darko for p in players),
                    'mean': np.mean([p.offensive_darko for p in players])
                },
                'defensive_darko': {
                    'min': min(p.defensive_darko for p in players),
                    'max': max(p.defensive_darko for p in players),
                    'mean': np.mean([p.defensive_darko for p in players])
                }
            }
        }


if __name__ == "__main__":
    """Test the ModelEvaluator in isolation."""
    try:
        evaluator = ModelEvaluator()
        
        print("ModelEvaluator Test Results")
        print("=" * 40)
        
        # Test basic functionality
        players = evaluator.get_available_players()
        print(f"✅ Loaded {len(players)} blessed players")
        
        # Test lineup evaluation
        if len(players) >= 5:
            test_lineup = [p.player_id for p in players[:5]]
            result = evaluator.evaluate_lineup(test_lineup)
            print(f"✅ Lineup evaluation: {result.predicted_outcome:.3f}")
            print(f"   Players: {', '.join(result.player_names)}")
        
        # Test error handling
        try:
            evaluator.evaluate_lineup([999999, 999998, 999997, 999996, 999995])  # Non-existent players
        except IncompletePlayerError as e:
            print(f"✅ Error handling: {e}")
        
        try:
            evaluator.evaluate_lineup([999999])  # Wrong number of players
        except InvalidLineupError as e:
            print(f"✅ Error handling: {e}")
        
        # Print stats summary
        stats = evaluator.get_stats_summary()
        print(f"\n📊 Stats Summary:")
        print(f"   Total players: {stats['total_players']}")
        print(f"   Archetype distribution: {stats['archetype_distribution']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
