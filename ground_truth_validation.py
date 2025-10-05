"""
Ground Truth Basketball Validation Framework

This module implements comprehensive ground truth validation tests to ensure
our model captures fundamental basketball principles before proceeding with
complex validation against the original paper's examples.

Key Principle: Statistical convergence does not equal semantic validity.
We must validate the model's basketball intelligence before trusting it
with complex analysis.

Test Categories:
1. Basic Skill Impact - Better players should make lineups better
2. Positional Balance - Balanced lineups should outperform imbalanced ones
3. Defensive Impact - Adding good defenders should improve defense
4. Shooting Spacing - Adding shooters should help spacing-dependent lineups
5. Ball Dominance - Multiple ball-dominant players should have diminishing returns
6. Archetype Interactions - Different archetypes should interact meaningfully
7. Context Sensitivity - Same player should have different value in different contexts
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import json
import logging
from src.nba_stats.model_factory import ModelFactory, evaluate_lineup

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ValidationTest:
    """Represents a single ground truth validation test."""
    name: str
    description: str
    test_function: callable
    expected_result: str
    tolerance: float = 0.1

@dataclass
class ValidationResult:
    """Result of a validation test."""
    test_name: str
    passed: bool
    actual_value: float
    expected_value: float
    difference: float
    tolerance: float
    details: Dict[str, Any]
    error_message: Optional[str] = None

class GroundTruthValidator:
    """
    Validates the model against fundamental basketball principles.
    
    This class implements a comprehensive test suite that validates the model
    against basic basketball truths that any fan would agree with. The goal
    is to ensure the model has basketball intelligence before proceeding with
    complex validation.
    """
    
    def __init__(self, model_type: str = "simple"):
        """
        Initialize the validator.
        
        Args:
            model_type: Model type to validate ("simple" or "original")
        """
        self.model_type = model_type
        self.db_path = Path("src/nba_stats/db/nba_stats.db")
        self.evaluator = ModelFactory.create_evaluator(model_type)
        
        # Load player data for testing
        self._load_player_data()
        
        # Define validation tests
        self.tests = self._define_validation_tests()
        
        logger.info(f"✅ GroundTruthValidator initialized with {len(self.tests)} tests")
    
    def _load_player_data(self) -> None:
        """Load player data needed for validation tests."""
        with sqlite3.connect(self.db_path) as conn:
            # Load player skills and archetypes
            query = """
            SELECT 
                ps.player_id,
                p.player_name,
                ps.offensive_darko,
                ps.defensive_darko,
                ps.darko,
                pa.archetype_id,
                a.archetype_name
            FROM PlayerSeasonSkill ps
            JOIN Players p ON ps.player_id = p.player_id
            JOIN PlayerSeasonArchetypes pa ON ps.player_id = pa.player_id
            JOIN Archetypes a ON pa.archetype_id = a.archetype_id
            WHERE ps.season = '2024-25'
            AND ps.offensive_darko IS NOT NULL
            AND ps.defensive_darko IS NOT NULL
            AND pa.archetype_id IS NOT NULL
            """
            
            self.players_df = pd.read_sql_query(query, conn)
            
            # Create player lookup dictionaries
            self.players_by_skill = self.players_df.sort_values('darko', ascending=False)
            self.players_by_archetype = self.players_df.groupby('archetype_id')
            
            logger.info(f"✅ Loaded {len(self.players_df)} players for validation")
    
    def _define_validation_tests(self) -> List[ValidationTest]:
        """Define all validation tests."""
        return [
            ValidationTest(
                name="basic_skill_impact",
                description="Better players should make lineups better",
                test_function=self._test_basic_skill_impact,
                expected_result="Higher skill players should produce better lineup predictions",
                tolerance=0.1
            ),
            ValidationTest(
                name="positional_balance",
                description="Balanced lineups should outperform imbalanced ones",
                test_function=self._test_positional_balance,
                expected_result="Lineups with diverse archetypes should perform better",
                tolerance=0.1
            ),
            ValidationTest(
                name="defensive_impact",
                description="Adding good defenders should improve defensive performance",
                test_function=self._test_defensive_impact,
                expected_result="Adding high defensive skill players should improve lineup",
                tolerance=0.1
            ),
            ValidationTest(
                name="shooting_spacing",
                description="Adding shooters should help spacing-dependent lineups",
                test_function=self._test_shooting_spacing,
                expected_result="Adding shooters should help lineups with poor spacing",
                tolerance=0.1
            ),
            ValidationTest(
                name="ball_dominance",
                description="Multiple ball-dominant players should have diminishing returns",
                test_function=self._test_ball_dominance,
                expected_result="Adding multiple ball handlers should show diminishing returns",
                tolerance=0.1
            ),
            ValidationTest(
                name="archetype_interactions",
                description="Different archetypes should interact meaningfully",
                test_function=self._test_archetype_interactions,
                expected_result="Archetype combinations should show different performance patterns",
                tolerance=0.1
            ),
            ValidationTest(
                name="context_sensitivity",
                description="Same player should have different value in different contexts",
                test_function=self._test_context_sensitivity,
                expected_result="Player value should depend on lineup context",
                tolerance=0.1
            )
        ]
    
    def run_all_tests(self) -> List[ValidationResult]:
        """Run all validation tests and return results."""
        results = []
        
        logger.info("🏀 Starting Ground Truth Basketball Validation")
        logger.info("=" * 60)
        
        for test in self.tests:
            logger.info(f"\n🧪 Running Test: {test.name}")
            logger.info(f"   Description: {test.description}")
            
            try:
                result = test.test_function()
                results.append(result)
                
                if result.passed:
                    logger.info(f"   ✅ PASSED: {result.actual_value:.3f} vs expected {result.expected_value:.3f}")
                else:
                    logger.warning(f"   ❌ FAILED: {result.actual_value:.3f} vs expected {result.expected_value:.3f}")
                    if result.error_message:
                        logger.warning(f"   Error: {result.error_message}")
                        
            except Exception as e:
                logger.error(f"   💥 ERROR: {str(e)}")
                results.append(ValidationResult(
                    test_name=test.name,
                    passed=False,
                    actual_value=0.0,
                    expected_value=0.0,
                    difference=0.0,
                    tolerance=test.tolerance,
                    details={},
                    error_message=str(e)
                ))
        
        # Summary
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        
        logger.info(f"\n📊 VALIDATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Tests Passed: {passed}/{total} ({passed/total*100:.1f}%)")
        
        if passed >= total * 0.8:  # 80% pass rate
            logger.info("✅ VALIDATION SUCCESS: Model shows basketball intelligence")
        else:
            logger.warning("❌ VALIDATION FAILURE: Model lacks basketball understanding")
        
        return results
    
    def _test_basic_skill_impact(self) -> ValidationResult:
        """Test that better players make lineups better."""
        # Get top and bottom skill players
        top_players = self.players_by_skill.head(10)
        bottom_players = self.players_by_skill.tail(10)
        
        # Create lineups with different skill levels
        high_skill_lineup = top_players['player_id'].iloc[:5].tolist()
        low_skill_lineup = bottom_players['player_id'].iloc[:5].tolist()
        
        # Evaluate both lineups
        high_skill_result = self.evaluator.evaluate_lineup(high_skill_lineup)
        low_skill_result = self.evaluator.evaluate_lineup(low_skill_lineup)
        
        # Calculate skill difference
        high_skill_avg = np.mean([self.players_df[self.players_df['player_id'] == pid]['darko'].iloc[0] 
                                 for pid in high_skill_lineup])
        low_skill_avg = np.mean([self.players_df[self.players_df['player_id'] == pid]['darko'].iloc[0] 
                                for pid in low_skill_lineup])
        
        skill_difference = high_skill_avg - low_skill_avg
        prediction_difference = high_skill_result.predicted_outcome - low_skill_result.predicted_outcome
        
        # Test passes if higher skill lineup has better prediction
        passed = prediction_difference > 0
        
        return ValidationResult(
            test_name="basic_skill_impact",
            passed=passed,
            actual_value=prediction_difference,
            expected_value=skill_difference,
            difference=abs(prediction_difference - skill_difference),
            tolerance=0.1,
            details={
                "high_skill_avg": high_skill_avg,
                "low_skill_avg": low_skill_avg,
                "skill_difference": skill_difference,
                "high_skill_prediction": high_skill_result.predicted_outcome,
                "low_skill_prediction": low_skill_result.predicted_outcome,
                "prediction_difference": prediction_difference
            }
        )
    
    def _test_positional_balance(self) -> ValidationResult:
        """Test that balanced lineups outperform imbalanced ones."""
        # Get players by archetype
        archetype_groups = {arch_id: group for arch_id, group in self.players_by_archetype}
        
        # Create balanced lineup (one player from each archetype)
        balanced_lineup = []
        for arch_id in archetype_groups.keys():
            if len(archetype_groups[arch_id]) > 0:
                balanced_lineup.append(archetype_groups[arch_id].iloc[0]['player_id'])
        
        # Create imbalanced lineup (all same archetype)
        if len(balanced_lineup) >= 5:
            balanced_lineup = balanced_lineup[:5]
            imbalanced_lineup = archetype_groups[0].iloc[:5]['player_id'].tolist()
            
            # Evaluate both lineups
            balanced_result = self.evaluator.evaluate_lineup(balanced_lineup)
            imbalanced_result = self.evaluator.evaluate_lineup(imbalanced_lineup)
            
            # Test passes if balanced lineup performs better
            passed = balanced_result.predicted_outcome > imbalanced_result.predicted_outcome
            
            return ValidationResult(
                test_name="positional_balance",
                passed=passed,
                actual_value=balanced_result.predicted_outcome - imbalanced_result.predicted_outcome,
                expected_value=0.1,  # Expected improvement
                difference=abs(balanced_result.predicted_outcome - imbalanced_result.predicted_outcome),
                tolerance=0.1,
                details={
                    "balanced_prediction": balanced_result.predicted_outcome,
                    "imbalanced_prediction": imbalanced_result.predicted_outcome,
                    "balanced_archetypes": [self.players_df[self.players_df['player_id'] == pid]['archetype_id'].iloc[0] 
                                          for pid in balanced_lineup],
                    "imbalanced_archetypes": [self.players_df[self.players_df['player_id'] == pid]['archetype_id'].iloc[0] 
                                            for pid in imbalanced_lineup]
                }
            )
        else:
            return ValidationResult(
                test_name="positional_balance",
                passed=False,
                actual_value=0.0,
                expected_value=0.1,
                difference=0.0,
                tolerance=0.1,
                details={},
                error_message="Not enough archetypes for balanced lineup test"
            )
    
    def _test_defensive_impact(self) -> ValidationResult:
        """Test that adding good defenders improves lineup performance."""
        # Get players sorted by defensive skill
        defensive_players = self.players_df.sort_values('defensive_darko', ascending=False)
        
        # Create base lineup with average defenders
        base_lineup = defensive_players.iloc[50:55]['player_id'].tolist()
        
        # Create improved lineup with top defenders
        improved_lineup = defensive_players.iloc[:5]['player_id'].tolist()
        
        # Evaluate both lineups
        base_result = self.evaluator.evaluate_lineup(base_lineup)
        improved_result = self.evaluator.evaluate_lineup(improved_lineup)
        
        # Calculate defensive skill difference
        base_def_avg = np.mean([self.players_df[self.players_df['player_id'] == pid]['defensive_darko'].iloc[0] 
                               for pid in base_lineup])
        improved_def_avg = np.mean([self.players_df[self.players_df['player_id'] == pid]['defensive_darko'].iloc[0] 
                                   for pid in improved_lineup])
        
        def_skill_difference = improved_def_avg - base_def_avg
        prediction_difference = improved_result.predicted_outcome - base_result.predicted_outcome
        
        # Test passes if better defenders improve lineup
        passed = prediction_difference > 0
        
        return ValidationResult(
            test_name="defensive_impact",
            passed=passed,
            actual_value=prediction_difference,
            expected_value=def_skill_difference,
            difference=abs(prediction_difference - def_skill_difference),
            tolerance=0.1,
            details={
                "base_def_avg": base_def_avg,
                "improved_def_avg": improved_def_avg,
                "def_skill_difference": def_skill_difference,
                "base_prediction": base_result.predicted_outcome,
                "improved_prediction": improved_result.predicted_outcome,
                "prediction_difference": prediction_difference
            }
        )
    
    def _test_shooting_spacing(self) -> ValidationResult:
        """Test that adding shooters helps spacing-dependent lineups."""
        # This is a simplified test - in reality, we'd need to identify
        # spacing-dependent lineups and test adding shooters
        
        # For now, test that adding high-usage players (who need spacing)
        # benefits from adding role players (who provide spacing)
        
        # Get high-usage players (ball handlers) and role players
        ball_handlers = self.players_df[self.players_df['archetype_id'] == 1]  # Primary Ball Handlers
        role_players = self.players_df[self.players_df['archetype_id'] == 2]   # Role Players
        
        if len(ball_handlers) >= 3 and len(role_players) >= 2:
            # Create lineup with 3 ball handlers + 2 role players
            balanced_lineup = (ball_handlers.iloc[:3]['player_id'].tolist() + 
                              role_players.iloc[:2]['player_id'].tolist())
            
            # Create lineup with 5 ball handlers (poor spacing)
            imbalanced_lineup = ball_handlers.iloc[:5]['player_id'].tolist()
            
            # Evaluate both lineups
            balanced_result = self.evaluator.evaluate_lineup(balanced_lineup)
            imbalanced_result = self.evaluator.evaluate_lineup(imbalanced_lineup)
            
            # Test passes if balanced lineup (with spacing) performs better
            passed = balanced_result.predicted_outcome > imbalanced_result.predicted_outcome
            
            return ValidationResult(
                test_name="shooting_spacing",
                passed=passed,
                actual_value=balanced_result.predicted_outcome - imbalanced_result.predicted_outcome,
                expected_value=0.1,  # Expected improvement
                difference=abs(balanced_result.predicted_outcome - imbalanced_result.predicted_outcome),
                tolerance=0.1,
                details={
                    "balanced_prediction": balanced_result.predicted_outcome,
                    "imbalanced_prediction": imbalanced_result.predicted_outcome,
                    "balanced_archetypes": [self.players_df[self.players_df['player_id'] == pid]['archetype_id'].iloc[0] 
                                          for pid in balanced_lineup],
                    "imbalanced_archetypes": [self.players_df[self.players_df['player_id'] == pid]['archetype_id'].iloc[0] 
                                            for pid in imbalanced_lineup]
                }
            )
        else:
            return ValidationResult(
                test_name="shooting_spacing",
                passed=False,
                actual_value=0.0,
                expected_value=0.1,
                difference=0.0,
                tolerance=0.1,
                details={},
                error_message="Not enough players for shooting spacing test"
            )
    
    def _test_ball_dominance(self) -> ValidationResult:
        """Test that multiple ball-dominant players have diminishing returns."""
        # Get ball handlers (high usage players)
        ball_handlers = self.players_df[self.players_df['archetype_id'] == 1]  # Primary Ball Handlers
        
        if len(ball_handlers) >= 5:
            # Create lineup with 1 ball handler + 4 role players
            single_handler_lineup = ([ball_handlers.iloc[0]['player_id']] + 
                                   self.players_df[self.players_df['archetype_id'] == 2].iloc[:4]['player_id'].tolist())
            
            # Create lineup with 3 ball handlers + 2 role players
            multiple_handlers_lineup = (ball_handlers.iloc[:3]['player_id'].tolist() + 
                                      self.players_df[self.players_df['archetype_id'] == 2].iloc[:2]['player_id'].tolist())
            
            # Evaluate both lineups
            single_result = self.evaluator.evaluate_lineup(single_handler_lineup)
            multiple_result = self.evaluator.evaluate_lineup(multiple_handlers_lineup)
            
            # Calculate expected improvement (should be less than linear)
            single_handler_skill = ball_handlers.iloc[0]['offensive_darko']
            multiple_handlers_skill = np.mean(ball_handlers.iloc[:3]['offensive_darko'])
            
            skill_improvement = multiple_handlers_skill - single_handler_skill
            prediction_improvement = multiple_result.predicted_outcome - single_result.predicted_outcome
            
            # Test passes if improvement is less than linear (diminishing returns)
            # This is a simplified test - in reality, we'd need more sophisticated analysis
            passed = prediction_improvement < skill_improvement * 1.5  # Allow some improvement but not linear
            
            return ValidationResult(
                test_name="ball_dominance",
                passed=passed,
                actual_value=prediction_improvement,
                expected_value=skill_improvement,
                difference=abs(prediction_improvement - skill_improvement),
                tolerance=0.1,
                details={
                    "single_handler_skill": single_handler_skill,
                    "multiple_handlers_skill": multiple_handlers_skill,
                    "skill_improvement": skill_improvement,
                    "single_prediction": single_result.predicted_outcome,
                    "multiple_prediction": multiple_result.predicted_outcome,
                    "prediction_improvement": prediction_improvement
                }
            )
        else:
            return ValidationResult(
                test_name="ball_dominance",
                passed=False,
                actual_value=0.0,
                expected_value=0.0,
                difference=0.0,
                tolerance=0.1,
                details={},
                error_message="Not enough ball handlers for diminishing returns test"
            )
    
    def _test_archetype_interactions(self) -> ValidationResult:
        """Test that different archetype combinations show different performance patterns."""
        # Get players from different archetypes
        archetype_groups = {arch_id: group for arch_id, group in self.players_by_archetype}
        
        if len(archetype_groups) >= 2:
            # Create lineups with different archetype combinations
            arch1_players = archetype_groups[list(archetype_groups.keys())[0]]
            arch2_players = archetype_groups[list(archetype_groups.keys())[1]]
            
            if len(arch1_players) >= 3 and len(arch2_players) >= 2:
                # Lineup 1: 3 from archetype 1, 2 from archetype 2
                lineup1 = (arch1_players.iloc[:3]['player_id'].tolist() + 
                          arch2_players.iloc[:2]['player_id'].tolist())
                
                # Lineup 2: 2 from archetype 1, 3 from archetype 2
                lineup2 = (arch1_players.iloc[:2]['player_id'].tolist() + 
                          arch2_players.iloc[:3]['player_id'].tolist())
                
                # Evaluate both lineups
                result1 = self.evaluator.evaluate_lineup(lineup1)
                result2 = self.evaluator.evaluate_lineup(lineup2)
                
                # Test passes if different combinations produce different results
                # (indicating archetype interactions matter)
                difference = abs(result1.predicted_outcome - result2.predicted_outcome)
                passed = difference > 0.01  # Some meaningful difference
                
                return ValidationResult(
                    test_name="archetype_interactions",
                    passed=passed,
                    actual_value=difference,
                    expected_value=0.05,  # Expected meaningful difference
                    difference=abs(difference - 0.05),
                    tolerance=0.1,
                    details={
                        "lineup1_prediction": result1.predicted_outcome,
                        "lineup2_prediction": result2.predicted_outcome,
                        "difference": difference,
                        "lineup1_archetypes": [self.players_df[self.players_df['player_id'] == pid]['archetype_id'].iloc[0] 
                                             for pid in lineup1],
                        "lineup2_archetypes": [self.players_df[self.players_df['player_id'] == pid]['archetype_id'].iloc[0] 
                                             for pid in lineup2]
                    }
                )
        
        return ValidationResult(
            test_name="archetype_interactions",
            passed=False,
            actual_value=0.0,
            expected_value=0.05,
            difference=0.0,
            tolerance=0.1,
            details={},
            error_message="Not enough archetypes for interaction test"
        )
    
    def _test_context_sensitivity(self) -> ValidationResult:
        """Test that same player has different value in different contexts."""
        # Get a good player
        good_player = self.players_by_skill.iloc[0]
        good_player_id = good_player['player_id']
        
        # Create two different contexts with 5 players each
        # Context 1: With other good players
        other_good_players = self.players_by_skill.iloc[1:5]['player_id'].tolist()
        context1_lineup = other_good_players + [good_player_id]
        
        # Context 2: With poor players
        poor_players = self.players_by_skill.tail(4)['player_id'].tolist()
        context2_lineup = poor_players + [good_player_id]
        
        # Ensure we have exactly 5 players in each lineup
        if len(context1_lineup) != 5 or len(context2_lineup) != 5:
            return ValidationResult(
                test_name="context_sensitivity",
                passed=False,
                actual_value=0.0,
                expected_value=0.05,
                difference=0.0,
                tolerance=0.1,
                details={},
                error_message=f"Invalid lineup sizes: context1={len(context1_lineup)}, context2={len(context2_lineup)}"
            )
        
        # Evaluate both lineups
        context1_result = self.evaluator.evaluate_lineup(context1_lineup)
        context2_result = self.evaluator.evaluate_lineup(context2_lineup)
        
        # For context sensitivity, we'll test if the same player produces different
        # results when placed in different contexts (different supporting casts)
        # We'll use a simplified approach: compare the predictions directly
        prediction_difference = abs(context1_result.predicted_outcome - context2_result.predicted_outcome)
        
        # Test passes if there's meaningful difference between contexts
        passed = prediction_difference > 0.01  # Some meaningful difference
        
        return ValidationResult(
            test_name="context_sensitivity",
            passed=passed,
            actual_value=prediction_difference,
            expected_value=0.05,  # Expected meaningful difference
            difference=abs(prediction_difference - 0.05),
            tolerance=0.1,
            details={
                "context1_prediction": context1_result.predicted_outcome,
                "context2_prediction": context2_result.predicted_outcome,
                "prediction_difference": prediction_difference,
                "context1_skill_avg": float(np.mean([self.players_df[self.players_df['player_id'] == pid]['darko'].iloc[0] 
                                                   for pid in context1_lineup])),
                "context2_skill_avg": float(np.mean([self.players_df[self.players_df['player_id'] == pid]['darko'].iloc[0] 
                                                   for pid in context2_lineup]))
            }
        )
    
    def generate_validation_report(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Generate a comprehensive validation report."""
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        
        # Convert numpy types to Python types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, (np.bool_, bool)):
                return bool(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            elif isinstance(obj, tuple):
                return tuple(convert_numpy_types(item) for item in obj)
            else:
                return obj
        
        report = {
            "summary": {
                "total_tests": total,
                "passed_tests": passed,
                "failed_tests": total - passed,
                "pass_rate": passed / total * 100,
                "validation_status": "PASS" if passed >= total * 0.8 else "FAIL"
            },
            "test_results": [
                {
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "actual_value": float(r.actual_value),
                    "expected_value": float(r.expected_value),
                    "difference": float(r.difference),
                    "tolerance": float(r.tolerance),
                    "error_message": r.error_message,
                    "details": convert_numpy_types(r.details)
                }
                for r in results
            ],
            "recommendations": self._generate_recommendations(results)
        }
        
        return report
    
    def _generate_recommendations(self, results: List[ValidationResult]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        failed_tests = [r for r in results if not r.passed]
        
        if not failed_tests:
            recommendations.append("✅ All tests passed - model shows strong basketball intelligence")
            recommendations.append("✅ Proceed with data migration and paper validation")
        else:
            recommendations.append("❌ Some tests failed - model needs improvement before proceeding")
            
            for result in failed_tests:
                if result.test_name == "basic_skill_impact":
                    recommendations.append("🔧 Fix basic skill impact - model may not properly weight player skills")
                elif result.test_name == "positional_balance":
                    recommendations.append("🔧 Fix positional balance - model may not understand lineup composition")
                elif result.test_name == "defensive_impact":
                    recommendations.append("🔧 Fix defensive impact - model may not properly value defense")
                elif result.test_name == "shooting_spacing":
                    recommendations.append("🔧 Fix shooting spacing - model may not understand spacing interactions")
                elif result.test_name == "ball_dominance":
                    recommendations.append("🔧 Fix ball dominance - model may not capture diminishing returns")
                elif result.test_name == "archetype_interactions":
                    recommendations.append("🔧 Fix archetype interactions - model may not capture player role interactions")
                elif result.test_name == "context_sensitivity":
                    recommendations.append("🔧 Fix context sensitivity - model may not understand contextual player value")
        
        return recommendations


def main():
    """Run ground truth validation."""
    print("🏀 NBA Lineup Optimizer - Ground Truth Validation")
    print("=" * 60)
    
    try:
        # Initialize validator
        validator = GroundTruthValidator(model_type="simple")
        
        # Run all tests
        results = validator.run_all_tests()
        
        # Generate report
        report = validator.generate_validation_report(results)
        
        # Save report
        try:
            with open("ground_truth_validation_report.json", "w") as f:
                json.dump(report, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to save JSON report: {e}")
            # Save a simplified version
            simplified_report = {
                "summary": report["summary"],
                "test_results": [
                    {
                        "test_name": r["test_name"],
                        "passed": r["passed"],
                        "actual_value": float(r["actual_value"]),
                        "expected_value": float(r["expected_value"]),
                        "error_message": r.get("error_message")
                    }
                    for r in report["test_results"]
                ]
            }
            with open("ground_truth_validation_report.json", "w") as f:
                json.dump(simplified_report, f, indent=2)
        
        print(f"\n📊 Validation Report saved to: ground_truth_validation_report.json")
        print(f"📊 Pass Rate: {report['summary']['pass_rate']:.1f}%")
        print(f"📊 Status: {report['summary']['validation_status']}")
        
        # Print recommendations
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"   {rec}")
        
        return report['summary']['validation_status'] == "PASS"
        
    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
