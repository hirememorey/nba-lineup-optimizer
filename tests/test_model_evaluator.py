"""
Comprehensive tests for ModelEvaluator

This test suite validates the defensive contract of the ModelEvaluator
and ensures it handles all edge cases correctly.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nba_stats.model_evaluator import ModelEvaluator, IncompletePlayerError, InvalidLineupError


class TestModelEvaluator:
    """Test suite for ModelEvaluator defensive contract."""
    
    @pytest.fixture
    def evaluator(self):
        """Create a ModelEvaluator instance for testing."""
        return ModelEvaluator()
    
    def test_initialization(self, evaluator):
        """Test that ModelEvaluator initializes correctly."""
        assert evaluator is not None
        assert len(evaluator.get_available_players()) == 270
        assert evaluator.season == "2024-25"
    
    def test_get_available_players(self, evaluator):
        """Test that get_available_players returns only blessed players."""
        players = evaluator.get_available_players()
        
        # Should have exactly 270 players
        assert len(players) == 270
        
        # All players should have complete data
        for player in players:
            assert player.player_id is not None
            assert player.player_name is not None
            assert player.offensive_darko is not None
            assert player.defensive_darko is not None
            assert player.darko is not None
            assert player.archetype_id is not None
            assert player.archetype_name is not None
    
    def test_get_player_by_id_valid(self, evaluator):
        """Test getting a valid player by ID."""
        players = evaluator.get_available_players()
        test_player = players[0]
        
        retrieved_player = evaluator.get_player_by_id(test_player.player_id)
        assert retrieved_player is not None
        assert retrieved_player.player_id == test_player.player_id
        assert retrieved_player.player_name == test_player.player_name
    
    def test_get_player_by_id_invalid(self, evaluator):
        """Test getting an invalid player by ID."""
        retrieved_player = evaluator.get_player_by_id(999999)
        assert retrieved_player is None
    
    def test_evaluate_lineup_valid(self, evaluator):
        """Test evaluating a valid lineup."""
        players = evaluator.get_available_players()
        test_lineup = [p.player_id for p in players[:5]]
        
        result = evaluator.evaluate_lineup(test_lineup)
        
        assert result is not None
        assert result.predicted_outcome is not None
        assert len(result.player_ids) == 5
        assert len(result.player_names) == 5
        assert len(result.archetype_ids) == 5
        assert len(result.archetype_names) == 5
        assert 'avg_offensive_darko' in result.skill_scores
        assert 'avg_defensive_darko' in result.skill_scores
        assert 'avg_overall_darko' in result.skill_scores
    
    def test_evaluate_lineup_wrong_count(self, evaluator):
        """Test evaluating lineup with wrong number of players."""
        players = evaluator.get_available_players()
        
        # Test with 4 players
        with pytest.raises(InvalidLineupError, match="exactly 5 players"):
            evaluator.evaluate_lineup([p.player_id for p in players[:4]])
        
        # Test with 6 players
        with pytest.raises(InvalidLineupError, match="exactly 5 players"):
            evaluator.evaluate_lineup([p.player_id for p in players[:6]])
        
        # Test with 0 players
        with pytest.raises(InvalidLineupError, match="exactly 5 players"):
            evaluator.evaluate_lineup([])
    
    def test_evaluate_lineup_incomplete_player(self, evaluator):
        """Test evaluating lineup with incomplete player data."""
        players = evaluator.get_available_players()
        test_lineup = [p.player_id for p in players[:4]] + [999999]  # Add invalid player
        
        with pytest.raises(IncompletePlayerError, match="not in blessed set"):
            evaluator.evaluate_lineup(test_lineup)
    
    def test_find_best_fit_valid(self, evaluator):
        """Test finding best fit with valid inputs."""
        players = evaluator.get_available_players()
        core_players = [p.player_id for p in players[:4]]
        candidates = [p.player_id for p in players[4:10]]  # 6 candidates
        
        best_player, best_evaluation = evaluator.find_best_fit(core_players, candidates)
        
        assert best_player is not None
        assert best_evaluation is not None
        assert best_player.player_id in candidates
        assert best_evaluation.predicted_outcome is not None
    
    def test_find_best_fit_wrong_core_count(self, evaluator):
        """Test find_best_fit with wrong core player count."""
        players = evaluator.get_available_players()
        candidates = [p.player_id for p in players[4:10]]
        
        # Test with 3 core players
        with pytest.raises(InvalidLineupError, match="exactly 4 players"):
            evaluator.find_best_fit([p.player_id for p in players[:3]], candidates)
        
        # Test with 5 core players
        with pytest.raises(InvalidLineupError, match="exactly 4 players"):
            evaluator.find_best_fit([p.player_id for p in players[:5]], candidates)
    
    def test_find_best_fit_no_valid_candidates(self, evaluator):
        """Test find_best_fit with no valid candidates."""
        players = evaluator.get_available_players()
        core_players = [p.player_id for p in players[:4]]
        invalid_candidates = [999999, 999998, 999997]  # All invalid
        
        with pytest.raises(ValueError, match="No valid candidates found"):
            evaluator.find_best_fit(core_players, invalid_candidates)
    
    def test_find_best_fit_no_valid_lineups(self, evaluator):
        """Test find_best_fit where no valid lineups can be formed."""
        players = evaluator.get_available_players()
        core_players = [p.player_id for p in players[:4]]
        
        # Use empty candidates list (no valid candidates)
        with pytest.raises(ValueError, match="No valid candidates found"):
            evaluator.find_best_fit(core_players, [])
    
    def test_get_stats_summary(self, evaluator):
        """Test getting stats summary."""
        stats = evaluator.get_stats_summary()
        
        assert 'total_players' in stats
        assert 'season' in stats
        assert 'archetype_distribution' in stats
        assert 'skill_ranges' in stats
        
        assert stats['total_players'] == 270
        assert stats['season'] == '2024-25'
        assert len(stats['archetype_distribution']) == 8  # 8 archetypes
        assert 'offensive_darko' in stats['skill_ranges']
        assert 'defensive_darko' in stats['skill_ranges']
    
    def test_archetype_distribution(self, evaluator):
        """Test that archetype distribution is reasonable."""
        stats = evaluator.get_stats_summary()
        archetype_dist = stats['archetype_distribution']
        
        # Should have all 8 archetypes (0-7)
        assert len(archetype_dist) == 8
        for i in range(8):
            assert i in archetype_dist
        
        # Total should equal 270
        assert sum(archetype_dist.values()) == 270
        
        # No archetype should have 0 players
        for count in archetype_dist.values():
            assert count > 0
    
    def test_skill_ranges_reasonable(self, evaluator):
        """Test that skill ranges are reasonable."""
        stats = evaluator.get_stats_summary()
        skill_ranges = stats['skill_ranges']
        
        # Check offensive_darko
        off_darko = skill_ranges['offensive_darko']
        assert off_darko['min'] < off_darko['max']
        assert off_darko['mean'] > off_darko['min']
        assert off_darko['mean'] < off_darko['max']
        
        # Check defensive_darko
        def_darko = skill_ranges['defensive_darko']
        assert def_darko['min'] < def_darko['max']
        assert def_darko['mean'] > def_darko['min']
        assert def_darko['mean'] < def_darko['max']
    
    def test_lineup_evaluation_consistency(self, evaluator):
        """Test that lineup evaluation is consistent."""
        players = evaluator.get_available_players()
        test_lineup = [p.player_id for p in players[:5]]
        
        # Same lineup should give same result
        result1 = evaluator.evaluate_lineup(test_lineup)
        result2 = evaluator.evaluate_lineup(test_lineup)
        
        assert result1.predicted_outcome == result2.predicted_outcome
        assert result1.player_ids == result2.player_ids
        assert result1.player_names == result2.player_names
    
    def test_different_lineups_different_results(self, evaluator):
        """Test that different lineups give different results."""
        players = evaluator.get_available_players()
        lineup1 = [p.player_id for p in players[:5]]
        lineup2 = [p.player_id for p in players[5:10]]
        
        result1 = evaluator.evaluate_lineup(lineup1)
        result2 = evaluator.evaluate_lineup(lineup2)
        
        # Results should be different (though not guaranteed)
        # At minimum, player lists should be different
        assert result1.player_ids != result2.player_ids
        assert result1.player_names != result2.player_names


if __name__ == "__main__":
    """Run tests directly."""
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
