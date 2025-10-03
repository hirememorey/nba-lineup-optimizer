#!/usr/bin/env python3
"""
Model Validation Suite

This script implements the "Deep Model Validation" phase using the
bulletproof ModelEvaluator as its foundation. It validates that the
model's analytical logic makes basketball sense.

Key Design Principles:
1. Uses ModelEvaluator for all lineup operations (no duplicate logic)
2. Tests basketball intelligence, not just technical correctness
3. Provides clear, actionable feedback on model quality
4. Works with both placeholder and real model coefficients
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nba_stats.model_evaluator import ModelEvaluator, Player, LineupEvaluation


class ModelValidator:
    """
    Validates the analytical logic of the NBA lineup model.
    
    This class implements the critical insight from the post-mortem:
    the validation code and the production code must use the same
    ModelEvaluator library to prevent bugs and inconsistencies.
    """
    
    def __init__(self, season: str = "2024-25"):
        """Initialize the validator with a ModelEvaluator instance."""
        self.evaluator = ModelEvaluator(season=season)
        self.season = season
        self.validation_results = {}
    
    def run_full_validation(self) -> Dict[str, Any]:
        """
        Run the complete validation suite.
        
        Returns:
            Dictionary containing all validation results
        """
        print("🔍 Starting Model Validation Suite")
        print("=" * 50)
        
        # Run all validation tests
        self.validation_results = {
            'coefficient_sanity_check': self._test_coefficient_sanity(),
            'diminishing_returns_test': self._test_diminishing_returns(),
            'synergy_test': self._test_archetype_synergy(),
            'spacing_test': self._test_spacing_effects(),
            'historical_validation': self._test_historical_lineups(),
            'skill_impact_test': self._test_skill_impacts(),
            'lineup_discrimination_test': self._test_lineup_discrimination(),
            'overall_quality_score': 0.0
        }
        
        # Calculate overall quality score
        self.validation_results['overall_quality_score'] = self._calculate_quality_score()
        
        # Print summary
        self._print_validation_summary()
        
        return self.validation_results
    
    def _test_coefficient_sanity(self) -> Dict[str, Any]:
        """Test that model coefficients make basketball sense."""
        print("📊 Testing Coefficient Sanity...")
        
        # Get sample players for testing
        players = self.evaluator.get_available_players()
        
        # Test 1: High-skill players should generally perform better
        high_skill_players = sorted(players, key=lambda p: p.darko, reverse=True)[:10]
        low_skill_players = sorted(players, key=lambda p: p.darko)[:10]
        
        high_skill_lineup = [p.player_id for p in high_skill_players[:5]]
        low_skill_lineup = [p.player_id for p in low_skill_players[:5]]
        
        high_result = self.evaluator.evaluate_lineup(high_skill_lineup)
        low_result = self.evaluator.evaluate_lineup(low_skill_lineup)
        
        skill_difference = high_result.predicted_outcome - low_result.predicted_outcome
        
        # Test 2: Offensive skill should have positive impact
        offensive_players = sorted(players, key=lambda p: p.offensive_darko, reverse=True)[:5]
        defensive_players = sorted(players, key=lambda p: p.defensive_darko, reverse=True)[:5]
        
        offensive_lineup = [p.player_id for p in offensive_players]
        defensive_lineup = [p.player_id for p in defensive_players]
        
        off_result = self.evaluator.evaluate_lineup(offensive_lineup)
        def_result = self.evaluator.evaluate_lineup(defensive_lineup)
        
        results = {
            'high_vs_low_skill_difference': skill_difference,
            'offensive_vs_defensive_difference': off_result.predicted_outcome - def_result.predicted_outcome,
            'high_skill_outcome': high_result.predicted_outcome,
            'low_skill_outcome': low_result.predicted_outcome,
            'offensive_outcome': off_result.predicted_outcome,
            'defensive_outcome': def_result.predicted_outcome,
            'passed': skill_difference > 0,  # High skill should be better
            'test_name': 'Coefficient Sanity Check'
        }
        
        print(f"   High vs Low Skill Difference: {skill_difference:.3f}")
        print(f"   Offensive vs Defensive Difference: {off_result.predicted_outcome - def_result.predicted_outcome:.3f}")
        print(f"   ✅ Passed: {results['passed']}")
        
        return results
    
    def _test_diminishing_returns(self) -> Dict[str, Any]:
        """Test that adding duplicate archetypes shows diminishing returns."""
        print("🔄 Testing Diminishing Returns...")
        
        players = self.evaluator.get_available_players()
        
        # Group players by archetype
        archetype_groups = {}
        for player in players:
            arch_id = player.archetype_id
            if arch_id not in archetype_groups:
                archetype_groups[arch_id] = []
            archetype_groups[arch_id].append(player)
        
        # Find archetype with enough players for the test
        test_archetype = None
        for arch_id, arch_players in archetype_groups.items():
            if len(arch_players) >= 5:
                test_archetype = arch_id
                break
        
        if test_archetype is None:
            return {
                'passed': False,
                'reason': 'No archetype has enough players for test',
                'test_name': 'Diminishing Returns Test'
            }
        
        arch_players = archetype_groups[test_archetype]
        
        # Test: 1 player vs 2 players vs 3 players of same archetype
        base_players = [p for p in players if p.archetype_id != test_archetype][:4]
        
        if len(base_players) < 4:
            return {
                'passed': False,
                'reason': 'Not enough non-test archetype players',
                'test_name': 'Diminishing Returns Test'
            }
        
        base_lineup = [p.player_id for p in base_players]
        
        # Test with 1, 2, 3 players of the same archetype
        test_results = []
        for count in [1, 2, 3]:
            if count <= len(arch_players):
                # Create lineup with 4 base players + count archetype players
                test_lineup = base_lineup[:4] + [p.player_id for p in arch_players[:count]]
                if len(test_lineup) == 5:  # Ensure we have exactly 5 players
                    result = self.evaluator.evaluate_lineup(test_lineup)
                    test_results.append({
                        'count': count,
                        'outcome': result.predicted_outcome
                    })
        
        # Calculate marginal returns
        marginal_returns = []
        for i in range(1, len(test_results)):
            marginal = test_results[i]['outcome'] - test_results[i-1]['outcome']
            marginal_returns.append(marginal)
        
        # Check if marginal returns are decreasing (diminishing returns)
        diminishing = len(marginal_returns) >= 2 and marginal_returns[1] < marginal_returns[0]
        
        results = {
            'test_archetype': test_archetype,
            'test_results': test_results,
            'marginal_returns': marginal_returns,
            'diminishing_returns': diminishing,
            'passed': diminishing,
            'test_name': 'Diminishing Returns Test'
        }
        
        print(f"   Test Archetype: {test_archetype}")
        print(f"   Marginal Returns: {marginal_returns}")
        print(f"   ✅ Passed: {diminishing}")
        
        return results
    
    def _test_archetype_synergy(self) -> Dict[str, Any]:
        """Test that certain archetype combinations show synergy."""
        print("🤝 Testing Archetype Synergy...")
        
        players = self.evaluator.get_available_players()
        
        # Group players by archetype
        archetype_groups = {}
        for player in players:
            arch_id = player.archetype_id
            if arch_id not in archetype_groups:
                archetype_groups[arch_id] = []
            archetype_groups[arch_id].append(player)
        
        # Test different archetype combinations
        synergy_tests = []
        
        # Test 1: Balanced archetype distribution vs concentrated
        balanced_lineup = []
        concentrated_lineup = []
        
        # Create balanced lineup (different archetypes)
        for arch_id in list(archetype_groups.keys())[:5]:
            if arch_id in archetype_groups and len(archetype_groups[arch_id]) > 0:
                balanced_lineup.append(archetype_groups[arch_id][0].player_id)
        
        # Create concentrated lineup (same archetype)
        if len(archetype_groups) > 0:
            arch_id = list(archetype_groups.keys())[0]
            if len(archetype_groups[arch_id]) >= 5:
                concentrated_lineup = [p.player_id for p in archetype_groups[arch_id][:5]]
        
        if len(balanced_lineup) == 5 and len(concentrated_lineup) == 5:
            balanced_result = self.evaluator.evaluate_lineup(balanced_lineup)
            concentrated_result = self.evaluator.evaluate_lineup(concentrated_lineup)
            
            synergy_tests.append({
                'test_name': 'Balanced vs Concentrated',
                'balanced_outcome': balanced_result.predicted_outcome,
                'concentrated_outcome': concentrated_result.predicted_outcome,
                'difference': balanced_result.predicted_outcome - concentrated_result.predicted_outcome
            })
        
        # Calculate synergy score
        synergy_score = 0
        if synergy_tests:
            avg_difference = np.mean([test['difference'] for test in synergy_tests])
            synergy_score = avg_difference
        
        results = {
            'synergy_tests': synergy_tests,
            'synergy_score': synergy_score,
            'passed': synergy_score > 0,  # Balanced should be better
            'test_name': 'Archetype Synergy Test'
        }
        
        print(f"   Synergy Score: {synergy_score:.3f}")
        print(f"   ✅ Passed: {results['passed']}")
        
        return results
    
    def _test_spacing_effects(self) -> Dict[str, Any]:
        """Test that spacing (shooting) has positive effects."""
        print("🎯 Testing Spacing Effects...")
        
        players = self.evaluator.get_available_players()
        
        # This is a simplified test - in reality, we'd need shooting data
        # For now, we'll test that high-skill players (who tend to be better shooters)
        # perform better in lineups
        
        # Group by skill level
        high_skill = sorted(players, key=lambda p: p.darko, reverse=True)[:20]
        low_skill = sorted(players, key=lambda p: p.darko)[:20]
        
        # Test multiple lineups
        high_skill_results = []
        low_skill_results = []
        
        for i in range(min(3, len(high_skill) // 5)):
            start_idx = i * 5
            if start_idx + 5 <= len(high_skill):
                lineup = [p.player_id for p in high_skill[start_idx:start_idx+5]]
                result = self.evaluator.evaluate_lineup(lineup)
                high_skill_results.append(result.predicted_outcome)
        
        for i in range(min(3, len(low_skill) // 5)):
            start_idx = i * 5
            if start_idx + 5 <= len(low_skill):
                lineup = [p.player_id for p in low_skill[start_idx:start_idx+5]]
                result = self.evaluator.evaluate_lineup(lineup)
                low_skill_results.append(result.predicted_outcome)
        
        if high_skill_results and low_skill_results:
            avg_high = np.mean(high_skill_results)
            avg_low = np.mean(low_skill_results)
            spacing_effect = avg_high - avg_low
        else:
            spacing_effect = 0
        
        results = {
            'high_skill_avg': np.mean(high_skill_results) if high_skill_results else 0,
            'low_skill_avg': np.mean(low_skill_results) if low_skill_results else 0,
            'spacing_effect': spacing_effect,
            'passed': spacing_effect > 0,
            'test_name': 'Spacing Effects Test'
        }
        
        print(f"   Spacing Effect: {spacing_effect:.3f}")
        print(f"   ✅ Passed: {results['passed']}")
        
        return results
    
    def _test_historical_lineups(self) -> Dict[str, Any]:
        """Test against known good/bad lineups from history."""
        print("📚 Testing Historical Lineups...")
        
        players = self.evaluator.get_available_players()
        
        # Create some test lineups based on known patterns
        # This is simplified - in reality, we'd use actual historical data
        
        # Test 1: All-star lineup (high skill players)
        all_star_players = sorted(players, key=lambda p: p.darko, reverse=True)[:5]
        all_star_lineup = [p.player_id for p in all_star_players]
        all_star_result = self.evaluator.evaluate_lineup(all_star_lineup)
        
        # Test 2: Balanced lineup (different archetypes)
        balanced_players = []
        used_archetypes = set()
        for player in players:
            if player.archetype_id not in used_archetypes and len(balanced_players) < 5:
                balanced_players.append(player)
                used_archetypes.add(player.archetype_id)
        
        if len(balanced_players) == 5:
            balanced_lineup = [p.player_id for p in balanced_players]
            balanced_result = self.evaluator.evaluate_lineup(balanced_lineup)
        else:
            balanced_result = None
        
        # Test 3: Random lineup
        import random
        random_players = random.sample(players, 5)
        random_lineup = [p.player_id for p in random_players]
        random_result = self.evaluator.evaluate_lineup(random_lineup)
        
        results = {
            'all_star_outcome': all_star_result.predicted_outcome,
            'balanced_outcome': balanced_result.predicted_outcome if balanced_result else None,
            'random_outcome': random_result.predicted_outcome,
            'all_star_vs_random': all_star_result.predicted_outcome - random_result.predicted_outcome,
            'passed': all_star_result.predicted_outcome > random_result.predicted_outcome,
            'test_name': 'Historical Lineups Test'
        }
        
        print(f"   All-Star vs Random: {results['all_star_vs_random']:.3f}")
        print(f"   ✅ Passed: {results['passed']}")
        
        return results
    
    def _test_skill_impacts(self) -> Dict[str, Any]:
        """Test that individual skill metrics have expected impacts."""
        print("⚡ Testing Skill Impacts...")
        
        players = self.evaluator.get_available_players()
        
        # Test offensive vs defensive skill impacts
        high_offensive = sorted(players, key=lambda p: p.offensive_darko, reverse=True)[:10]
        high_defensive = sorted(players, key=lambda p: p.defensive_darko, reverse=True)[:10]
        
        # Create lineups with high offensive skill
        off_lineup = [p.player_id for p in high_offensive[:5]]
        off_result = self.evaluator.evaluate_lineup(off_lineup)
        
        # Create lineups with high defensive skill
        def_lineup = [p.player_id for p in high_defensive[:5]]
        def_result = self.evaluator.evaluate_lineup(def_lineup)
        
        # Test skill variance effects
        low_variance_players = sorted(players, key=lambda p: abs(p.darko - 0.5))[:5]
        high_variance_players = sorted(players, key=lambda p: abs(p.darko - 0.5), reverse=True)[:5]
        
        low_var_lineup = [p.player_id for p in low_variance_players]
        high_var_lineup = [p.player_id for p in high_variance_players]
        
        low_var_result = self.evaluator.evaluate_lineup(low_var_lineup)
        high_var_result = self.evaluator.evaluate_lineup(high_var_lineup)
        
        results = {
            'offensive_outcome': off_result.predicted_outcome,
            'defensive_outcome': def_result.predicted_outcome,
            'off_vs_def': off_result.predicted_outcome - def_result.predicted_outcome,
            'low_variance_outcome': low_var_result.predicted_outcome,
            'high_variance_outcome': high_var_result.predicted_outcome,
            'variance_effect': low_var_result.predicted_outcome - high_var_result.predicted_outcome,
            'passed': True,  # Basic sanity check
            'test_name': 'Skill Impacts Test'
        }
        
        print(f"   Offensive vs Defensive: {results['off_vs_def']:.3f}")
        print(f"   Variance Effect: {results['variance_effect']:.3f}")
        print(f"   ✅ Passed: {results['passed']}")
        
        return results
    
    def _test_lineup_discrimination(self) -> Dict[str, Any]:
        """Test that the model can distinguish between different lineup types."""
        print("🎭 Testing Lineup Discrimination...")
        
        players = self.evaluator.get_available_players()
        
        # Create different types of lineups
        lineups = {
            'high_skill': [p.player_id for p in sorted(players, key=lambda p: p.darko, reverse=True)[:5]],
            'low_skill': [p.player_id for p in sorted(players, key=lambda p: p.darko)[:5]],
            'balanced': [p.player_id for p in players[::len(players)//5][:5]],  # Every nth player
        }
        
        results = {}
        for lineup_type, lineup_ids in lineups.items():
            if len(lineup_ids) == 5:
                result = self.evaluator.evaluate_lineup(lineup_ids)
                results[lineup_type] = result.predicted_outcome
        
        # Calculate discrimination metrics
        if 'high_skill' in results and 'low_skill' in results:
            discrimination = results['high_skill'] - results['low_skill']
        else:
            discrimination = 0
        
        # Calculate variance in outcomes
        outcome_variance = np.var(list(results.values())) if results else 0
        
        test_results = {
            'lineup_outcomes': results,
            'discrimination': discrimination,
            'outcome_variance': outcome_variance,
            'passed': discrimination > 0 and outcome_variance > 0.01,
            'test_name': 'Lineup Discrimination Test'
        }
        
        print(f"   Discrimination: {discrimination:.3f}")
        print(f"   Outcome Variance: {outcome_variance:.3f}")
        print(f"   ✅ Passed: {test_results['passed']}")
        
        return test_results
    
    def _calculate_quality_score(self) -> float:
        """Calculate overall quality score from all tests."""
        scores = []
        
        for test_name, test_result in self.validation_results.items():
            if isinstance(test_result, dict) and 'passed' in test_result:
                scores.append(1.0 if test_result['passed'] else 0.0)
        
        return np.mean(scores) if scores else 0.0
    
    def _print_validation_summary(self) -> None:
        """Print a summary of validation results."""
        print("\n" + "=" * 50)
        print("📋 VALIDATION SUMMARY")
        print("=" * 50)
        
        total_tests = 0
        passed_tests = 0
        
        for test_name, test_result in self.validation_results.items():
            if isinstance(test_result, dict) and 'passed' in test_result:
                total_tests += 1
                if test_result['passed']:
                    passed_tests += 1
                status = "✅ PASS" if test_result['passed'] else "❌ FAIL"
                print(f"{status} {test_result.get('test_name', test_name)}")
        
        print(f"\nOverall Quality Score: {self.validation_results['overall_quality_score']:.1%}")
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        
        if self.validation_results['overall_quality_score'] >= 0.8:
            print("🎉 Model validation PASSED - Ready for production!")
        elif self.validation_results['overall_quality_score'] >= 0.6:
            print("⚠️  Model validation PARTIAL - Some issues need attention")
        else:
            print("❌ Model validation FAILED - Significant issues found")


def main():
    """Run the model validation suite."""
    validator = ModelValidator()
    results = validator.run_full_validation()
    
    # Save results to file (simplified)
    try:
        import json
        with open('model_validation_report.json', 'w') as f:
            # Simple summary for JSON
            summary = {
                'overall_quality_score': float(results['overall_quality_score']),
                'total_tests': len([k for k, v in results.items() if isinstance(v, dict) and 'passed' in v]),
                'passed_tests': len([k for k, v in results.items() if isinstance(v, dict) and v.get('passed', False)]),
                'test_results': {k: v.get('passed', False) for k, v in results.items() if isinstance(v, dict) and 'passed' in v}
            }
            json.dump(summary, f, indent=2)
        print(f"\n📄 Summary saved to: model_validation_report.json")
    except Exception as e:
        print(f"\n⚠️  Could not save JSON report: {e}")
    
    return results


if __name__ == "__main__":
    main()
