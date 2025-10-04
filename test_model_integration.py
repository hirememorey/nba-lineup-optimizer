#!/usr/bin/env python3
"""
Test Model Integration

This script tests the integration between the original ModelEvaluator
and the new SimpleModelEvaluator to ensure they work correctly together.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nba_stats.model_evaluator import ModelEvaluator
from nba_stats.simple_model_evaluator import SimpleModelEvaluator


def test_basic_functionality():
    """Test basic functionality of both evaluators."""
    print("Testing Basic Functionality")
    print("=" * 40)
    
    try:
        # Initialize both evaluators
        print("Initializing evaluators...")
        original_evaluator = ModelEvaluator()
        simple_evaluator = SimpleModelEvaluator()
        
        print(f"✅ Original evaluator: {len(original_evaluator.get_available_players())} players")
        print(f"✅ Simple evaluator: {len(simple_evaluator.get_available_players())} players")
        
        return original_evaluator, simple_evaluator
        
    except Exception as e:
        print(f"❌ Error initializing evaluators: {e}")
        return None, None


def test_lineup_evaluation(original_evaluator, simple_evaluator):
    """Test lineup evaluation with both models."""
    print("\nTesting Lineup Evaluation")
    print("=" * 40)
    
    if not original_evaluator or not simple_evaluator:
        print("❌ Evaluators not available")
        return
    
    try:
        # Get common players
        original_players = original_evaluator.get_available_players()
        simple_players = simple_evaluator.get_available_players()
        
        # Find common players
        common_player_ids = set(p.player_id for p in original_players) & set(p.player_id for p in simple_players)
        common_player_ids = list(common_player_ids)
        
        print(f"Found {len(common_player_ids)} common players")
        
        if len(common_player_ids) < 5:
            print("❌ Not enough common players for testing")
            return
        
        # Test with first 5 common players
        test_lineup = common_player_ids[:5]
        
        # Evaluate with original model
        original_result = original_evaluator.evaluate_lineup(test_lineup)
        print(f"✅ Original model prediction: {original_result.predicted_outcome:.3f}")
        print(f"   Players: {', '.join(original_result.player_names)}")
        
        # Evaluate with simple model
        simple_result = simple_evaluator.evaluate_lineup(test_lineup)
        print(f"✅ Simple model prediction: {simple_result.predicted_outcome:.3f}")
        print(f"   Players: {', '.join(simple_result.player_names)}")
        print(f"   Model type: {simple_result.model_type}")
        
        # Calculate difference
        difference = simple_result.predicted_outcome - original_result.predicted_outcome
        relative_difference = (difference / abs(original_result.predicted_outcome)) * 100 if original_result.predicted_outcome != 0 else 0
        
        print(f"\n📊 Comparison:")
        print(f"   Difference: {difference:.3f}")
        print(f"   Relative difference: {relative_difference:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing lineup evaluation: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_coefficient_comparison(simple_evaluator):
    """Test coefficient comparison."""
    print("\nTesting Coefficient Comparison")
    print("=" * 40)
    
    if not simple_evaluator:
        print("❌ Simple evaluator not available")
        return
    
    try:
        # Get coefficients
        coeff_df = simple_evaluator.get_model_coefficients_for_ui()
        
        print("✅ Simple model coefficients:")
        print(coeff_df.to_string(index=False))
        
        # Check coefficient structure
        expected_columns = ['archetype_id', 'archetype_name', 'beta_offensive', 'beta_defensive']
        if all(col in coeff_df.columns for col in expected_columns):
            print("✅ Coefficient structure is correct")
        else:
            print("❌ Coefficient structure is incorrect")
            print(f"Expected: {expected_columns}")
            print(f"Got: {coeff_df.columns.tolist()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing coefficient comparison: {e}")
        return False


def test_performance_comparison(original_evaluator, simple_evaluator, num_tests=10):
    """Test performance comparison with random lineups."""
    print(f"\nTesting Performance Comparison ({num_tests} random lineups)")
    print("=" * 40)
    
    if not original_evaluator or not simple_evaluator:
        print("❌ Evaluators not available")
        return
    
    try:
        # Get common players
        original_players = original_evaluator.get_available_players()
        simple_players = simple_evaluator.get_available_players()
        
        common_player_ids = set(p.player_id for p in original_players) & set(p.player_id for p in simple_players)
        common_player_ids = list(common_player_ids)
        
        if len(common_player_ids) < 5:
            print("❌ Not enough common players for testing")
            return
        
        # Generate random lineups
        np.random.seed(42)  # For reproducibility
        results = []
        
        for i in range(num_tests):
            # Sample 5 random players
            lineup_ids = np.random.choice(common_player_ids, 5, replace=False).tolist()
            
            try:
                # Evaluate with both models
                original_result = original_evaluator.evaluate_lineup(lineup_ids)
                simple_result = simple_evaluator.evaluate_lineup(lineup_ids)
                
                difference = simple_result.predicted_outcome - original_result.predicted_outcome
                relative_difference = (difference / abs(original_result.predicted_outcome)) * 100 if original_result.predicted_outcome != 0 else 0
                
                results.append({
                    "original": original_result.predicted_outcome,
                    "simple": simple_result.predicted_outcome,
                    "difference": difference,
                    "relative_difference": relative_difference
                })
                
            except Exception as e:
                print(f"⚠️ Error with lineup {i}: {e}")
                continue
        
        if not results:
            print("❌ No valid comparisons generated")
            return False
        
        # Calculate summary statistics
        results_df = pd.DataFrame(results)
        
        print(f"✅ Generated {len(results)} valid comparisons")
        print(f"   Mean difference: {results_df['difference'].mean():.3f}")
        print(f"   Std difference: {results_df['difference'].std():.3f}")
        print(f"   Mean relative difference: {results_df['relative_difference'].mean():.1f}%")
        print(f"   Correlation: {results_df['original'].corr(results_df['simple']):.3f}")
        print(f"   Max difference: {results_df['difference'].max():.3f}")
        print(f"   Min difference: {results_df['difference'].min():.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing performance comparison: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("NBA Model Integration Test")
    print("=" * 50)
    
    # Test 1: Basic functionality
    original_evaluator, simple_evaluator = test_basic_functionality()
    
    if not original_evaluator or not simple_evaluator:
        print("\n❌ Basic functionality test failed - stopping")
        return
    
    # Test 2: Lineup evaluation
    lineup_test_passed = test_lineup_evaluation(original_evaluator, simple_evaluator)
    
    # Test 3: Coefficient comparison
    coeff_test_passed = test_coefficient_comparison(simple_evaluator)
    
    # Test 4: Performance comparison
    perf_test_passed = test_performance_comparison(original_evaluator, simple_evaluator, num_tests=20)
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Basic Functionality: {'✅ PASS' if original_evaluator and simple_evaluator else '❌ FAIL'}")
    print(f"Lineup Evaluation: {'✅ PASS' if lineup_test_passed else '❌ FAIL'}")
    print(f"Coefficient Comparison: {'✅ PASS' if coeff_test_passed else '❌ FAIL'}")
    print(f"Performance Comparison: {'✅ PASS' if perf_test_passed else '❌ FAIL'}")
    
    all_passed = all([
        original_evaluator and simple_evaluator,
        lineup_test_passed,
        coeff_test_passed,
        perf_test_passed
    ])
    
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 Model integration is working correctly!")
        print("You can now run the comparison dashboard with:")
        print("streamlit run model_comparison_dashboard.py")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    main()
