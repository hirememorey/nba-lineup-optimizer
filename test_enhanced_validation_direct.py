"""
Test Enhanced Model Validation - Direct Approach

This script directly tests the enhanced model evaluator against the ground truth validation
tests without going through the ModelFactory.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_model_evaluator import EnhancedModelEvaluator
import pandas as pd
import numpy as np
from pathlib import Path
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_validation_direct():
    """Test the enhanced model evaluator directly against ground truth validation."""
    try:
        print("🧪 Testing Enhanced Model - Direct Validation")
        print("=" * 50)
        
        # Initialize enhanced model evaluator
        evaluator = EnhancedModelEvaluator()
        
        # Load player data
        db_path = Path("src/nba_stats/db/nba_stats.db")
        conn = sqlite3.connect(db_path)
        players_df = pd.read_sql_query("""
            SELECT p.player_id, p.player_name, ps.offensive_skill_rating as offensive_darko,
                   ps.defensive_skill_rating as defensive_darko, psa.archetype_id
            FROM Players p
            JOIN PlayerSkills ps ON p.player_id = ps.player_id
            JOIN PlayerSeasonArchetypes psa ON p.player_id = psa.player_id
            WHERE ps.season_id = '2024-25' AND psa.season = '2024-25'
        """, conn)
        conn.close()
        
        print(f"Loaded {len(players_df)} players for validation")
        
        # Run individual tests
        test_results = []
        
        # Test 1: Basic Skill Impact
        print("\n🧪 Test 1: Basic Skill Impact")
        result1 = test_basic_skill_impact(evaluator, players_df)
        test_results.append(result1)
        print(f"Result: {'✅ PASS' if result1['passed'] else '❌ FAIL'}")
        
        # Test 2: Ball Dominance (the key failing test)
        print("\n🧪 Test 2: Ball Dominance")
        result2 = test_ball_dominance(evaluator, players_df)
        test_results.append(result2)
        print(f"Result: {'✅ PASS' if result2['passed'] else '❌ FAIL'}")
        
        # Test 3: Defensive Impact
        print("\n🧪 Test 3: Defensive Impact")
        result3 = test_defensive_impact(evaluator, players_df)
        test_results.append(result3)
        print(f"Result: {'✅ PASS' if result3['passed'] else '❌ FAIL'}")
        
        # Test 4: Context Sensitivity
        print("\n🧪 Test 4: Context Sensitivity")
        result4 = test_context_sensitivity(evaluator, players_df)
        test_results.append(result4)
        print(f"Result: {'✅ PASS' if result4['passed'] else '❌ FAIL'}")
        
        # Calculate summary
        passed_tests = sum(1 for result in test_results if result['passed'])
        total_tests = len(test_results)
        pass_rate = (passed_tests / total_tests) * 100
        
        print(f"\n📊 VALIDATION SUMMARY")
        print("=" * 25)
        print(f"Tests Passed: {passed_tests}/{total_tests} ({pass_rate:.1f}%)")
        print(f"Status: {'✅ PASS' if pass_rate >= 80 else '❌ FAIL'}")
        
        # Save results
        results = {
            "summary": {
                "total_tests": int(total_tests),
                "passed_tests": int(passed_tests),
                "pass_rate": float(pass_rate),
                "validation_status": "PASS" if pass_rate >= 80 else "FAIL"
            },
            "test_results": test_results
        }
        
        with open("enhanced_validation_direct_report.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📊 Results saved to: enhanced_validation_direct_report.json")
        
        return results
        
    except Exception as e:
        print(f"❌ Error running enhanced validation: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_basic_skill_impact(evaluator, players_df):
    """Test that better players make lineups better."""
    try:
        # Get high and low skill players
        high_skill_players = players_df.nlargest(5, 'offensive_darko')['player_id'].tolist()
        low_skill_players = players_df.nsmallest(5, 'offensive_darko')['player_id'].tolist()
        
        # Evaluate both lineups
        high_result = evaluator.evaluate_lineup(high_skill_players)
        low_result = evaluator.evaluate_lineup(low_skill_players)
        
        # Calculate skill difference
        high_skill_avg = players_df[players_df['player_id'].isin(high_skill_players)]['offensive_darko'].mean()
        low_skill_avg = players_df[players_df['player_id'].isin(low_skill_players)]['offensive_darko'].mean()
        skill_difference = high_skill_avg - low_skill_avg
        
        # Calculate prediction difference
        prediction_difference = high_result.predicted_outcome - low_result.predicted_outcome
        
        # Test passes if prediction difference is positive and significant
        passed = prediction_difference > 0.1
        
        return {
            "test_name": "basic_skill_impact",
            "passed": bool(passed),
            "actual_value": float(prediction_difference),
            "expected_value": float(skill_difference),
            "difference": float(abs(prediction_difference - skill_difference)),
            "tolerance": 0.1,
            "details": {
                "high_skill_avg": float(high_skill_avg),
                "low_skill_avg": float(low_skill_avg),
                "skill_difference": float(skill_difference),
                "high_prediction": float(high_result.predicted_outcome),
                "low_prediction": float(low_result.predicted_outcome),
                "prediction_difference": float(prediction_difference)
            }
        }
    except Exception as e:
        return {
            "test_name": "basic_skill_impact",
            "passed": False,
            "error": str(e)
        }

def test_ball_dominance(evaluator, players_df):
    """Test that multiple ball-dominant players have diminishing returns."""
    try:
        # Get ball handlers (archetype 1)
        ball_handlers = players_df[players_df['archetype_id'] == 1]['player_id'].tolist()
        role_players = players_df[players_df['archetype_id'] == 2]['player_id'].tolist()
        
        if len(ball_handlers) >= 3 and len(role_players) >= 2:
            # Single ball handler lineup
            single_lineup = [ball_handlers[0]] + role_players[:4]
            
            # Multiple ball handlers lineup
            multiple_lineup = ball_handlers[:3] + role_players[:2]
            
            # Evaluate both lineups
            single_result = evaluator.evaluate_lineup(single_lineup)
            multiple_result = evaluator.evaluate_lineup(multiple_lineup)
            
            # Get enhancement details
            single_details = evaluator.get_enhancement_details(single_lineup)
            multiple_details = evaluator.get_enhancement_details(multiple_lineup)
            
            # Calculate skill improvement
            single_skill = players_df[players_df['player_id'] == ball_handlers[0]]['offensive_darko'].iloc[0]
            multiple_skill = players_df[players_df['player_id'].isin(ball_handlers[:3])]['offensive_darko'].mean()
            skill_improvement = multiple_skill - single_skill
            
            # Calculate prediction improvement
            prediction_improvement = multiple_result.predicted_outcome - single_result.predicted_outcome
            
            # Test passes if improvement is negative (diminishing returns)
            passed = prediction_improvement < 0
            
            return {
                "test_name": "ball_dominance",
                "passed": bool(passed),
                "actual_value": float(prediction_improvement),
                "expected_value": float(skill_improvement),
                "difference": float(abs(prediction_improvement - skill_improvement)),
                "tolerance": 0.1,
                "details": {
                    "single_handler_skill": float(single_skill),
                    "multiple_handlers_skill": float(multiple_skill),
                    "skill_improvement": float(skill_improvement),
                    "single_prediction": float(single_result.predicted_outcome),
                    "multiple_prediction": float(multiple_result.predicted_outcome),
                    "prediction_improvement": float(prediction_improvement),
                    "single_enhancement": float(single_details['total_enhancement']),
                    "multiple_enhancement": float(multiple_details['total_enhancement']),
                    "single_archetypes": single_details['archetype_distribution'],
                    "multiple_archetypes": multiple_details['archetype_distribution']
                }
            }
        else:
            return {
                "test_name": "ball_dominance",
                "passed": False,
                "error": "Not enough ball handlers or role players for test"
            }
    except Exception as e:
        return {
            "test_name": "ball_dominance",
            "passed": False,
            "error": str(e)
        }

def test_defensive_impact(evaluator, players_df):
    """Test that adding good defenders improves defensive performance."""
    try:
        # Get players with different defensive ratings
        base_players = players_df.nsmallest(5, 'defensive_darko')['player_id'].tolist()
        good_defender = players_df.nlargest(1, 'defensive_darko')['player_id'].iloc[0]
        
        # Create lineups
        base_lineup = base_players
        improved_lineup = base_players[:4] + [good_defender]
        
        # Evaluate both lineups
        base_result = evaluator.evaluate_lineup(base_lineup)
        improved_result = evaluator.evaluate_lineup(improved_lineup)
        
        # Calculate defensive skill difference
        base_def_avg = players_df[players_df['player_id'].isin(base_players)]['defensive_darko'].mean()
        improved_def_avg = players_df[players_df['player_id'].isin(improved_lineup)]['defensive_darko'].mean()
        def_skill_difference = improved_def_avg - base_def_avg
        
        # Calculate prediction difference
        prediction_difference = improved_result.predicted_outcome - base_result.predicted_outcome
        
        # Test passes if prediction difference is positive (better defense)
        passed = prediction_difference > 0.1
        
        return {
            "test_name": "defensive_impact",
            "passed": bool(passed),
            "actual_value": float(prediction_difference),
            "expected_value": float(def_skill_difference),
            "difference": float(abs(prediction_difference - def_skill_difference)),
            "tolerance": 0.1,
            "details": {
                "base_def_avg": float(base_def_avg),
                "improved_def_avg": float(improved_def_avg),
                "def_skill_difference": float(def_skill_difference),
                "base_prediction": float(base_result.predicted_outcome),
                "improved_prediction": float(improved_result.predicted_outcome),
                "prediction_difference": float(prediction_difference)
            }
        }
    except Exception as e:
        return {
            "test_name": "defensive_impact",
            "passed": False,
            "error": str(e)
        }

def test_context_sensitivity(evaluator, players_df):
    """Test that same player has different value in different contexts."""
    try:
        # Get a versatile player
        versatile_player = players_df.iloc[0]['player_id']
        
        # Create two different contexts
        context1_players = players_df.nlargest(4, 'offensive_darko')['player_id'].tolist()
        context2_players = players_df.nsmallest(4, 'offensive_darko')['player_id'].tolist()
        
        # Add the versatile player to both contexts
        lineup1 = context1_players + [versatile_player]
        lineup2 = context2_players + [versatile_player]
        
        # Evaluate both lineups
        result1 = evaluator.evaluate_lineup(lineup1)
        result2 = evaluator.evaluate_lineup(lineup2)
        
        # Calculate context difference
        context1_skill_avg = players_df[players_df['player_id'].isin(context1_players)]['offensive_darko'].mean()
        context2_skill_avg = players_df[players_df['player_id'].isin(context2_players)]['offensive_darko'].mean()
        skill_difference = context1_skill_avg - context2_skill_avg
        
        # Calculate prediction difference
        prediction_difference = result1.predicted_outcome - result2.predicted_outcome
        
        # Test passes if prediction difference is significant
        passed = abs(prediction_difference) > 0.1
        
        return {
            "test_name": "context_sensitivity",
            "passed": bool(passed),
            "actual_value": float(prediction_difference),
            "expected_value": float(skill_difference),
            "difference": float(abs(prediction_difference - skill_difference)),
            "tolerance": 0.1,
            "details": {
                "context1_skill_avg": float(context1_skill_avg),
                "context2_skill_avg": float(context2_skill_avg),
                "skill_difference": float(skill_difference),
                "context1_prediction": float(result1.predicted_outcome),
                "context2_prediction": float(result2.predicted_outcome),
                "prediction_difference": float(prediction_difference)
            }
        }
    except Exception as e:
        return {
            "test_name": "context_sensitivity",
            "passed": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import sqlite3
    test_enhanced_validation_direct()
