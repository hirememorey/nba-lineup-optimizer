"""
Test Enhanced Model Validation

This script tests the enhanced model evaluator against the ground truth validation
tests to see if the basketball intelligence enhancements fix the identified issues.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_model_evaluator import EnhancedModelEvaluator
from ground_truth_validation import GroundTruthValidator
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_validation():
    """Test the enhanced model evaluator against ground truth validation."""
    try:
        print("🧪 Testing Enhanced Model Against Ground Truth Validation")
        print("=" * 60)
        
        # Initialize enhanced model evaluator
        enhanced_evaluator = EnhancedModelEvaluator()
        
        # Initialize ground truth validator with enhanced evaluator
        validator = GroundTruthValidator(enhanced_evaluator)
        
        # Run all validation tests
        print("Running ground truth validation tests...")
        results = validator.run_validation()
        
        # Print results
        print(f"\n📊 VALIDATION RESULTS")
        print("=" * 30)
        print(f"Tests Passed: {results['summary']['passed_tests']}/{results['summary']['total_tests']} ({results['summary']['pass_rate']:.1f}%)")
        print(f"Status: {'✅ PASS' if results['summary']['validation_status'] == 'PASS' else '❌ FAIL'}")
        
        # Print individual test results
        print(f"\n📋 INDIVIDUAL TEST RESULTS")
        print("=" * 35)
        for test in results['test_results']:
            status = "✅ PASS" if test['passed'] else "❌ FAIL"
            print(f"{test['test_name']}: {status}")
            if not test['passed']:
                print(f"  Expected: {test['expected_value']:.3f}")
                print(f"  Actual: {test['actual_value']:.3f}")
                print(f"  Difference: {test['difference']:.3f}")
                if test.get('error_message'):
                    print(f"  Error: {test['error_message']}")
        
        # Save results
        output_file = "enhanced_validation_report.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📊 Enhanced validation report saved to: {output_file}")
        
        # Test specific ball dominance case
        print(f"\n🏀 BALL DOMINANCE TEST DETAILS")
        print("=" * 35)
        test_ball_dominance_detailed(enhanced_evaluator)
        
        return results
        
    except Exception as e:
        print(f"❌ Error running enhanced validation: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_ball_dominance_detailed(evaluator):
    """Test ball dominance with detailed analysis."""
    try:
        # Get ball handlers
        ball_handlers = [pid for pid, player in evaluator._blessed_players.items() 
                        if player.archetype_id == 1][:5]
        role_players = [pid for pid, player in evaluator._blessed_players.items() 
                       if player.archetype_id == 2][:5]
        
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
            
            print(f"Single Ball Handler Lineup:")
            print(f"  Prediction: {single_result.predicted_outcome:.3f}")
            print(f"  Base: {single_details['base_prediction']:.3f}")
            print(f"  Enhancement: {single_details['total_enhancement']:.3f}")
            print(f"  Archetypes: {single_details['archetype_distribution']}")
            
            print(f"\nMultiple Ball Handlers Lineup:")
            print(f"  Prediction: {multiple_result.predicted_outcome:.3f}")
            print(f"  Base: {multiple_details['base_prediction']:.3f}")
            print(f"  Enhancement: {multiple_details['total_enhancement']:.3f}")
            print(f"  Archetypes: {multiple_details['archetype_distribution']}")
            
            improvement = multiple_result.predicted_outcome - single_result.predicted_outcome
            print(f"\nImprovement: {improvement:.3f}")
            print(f"Expected: Negative (diminishing returns)")
            print(f"Result: {'✅ PASS' if improvement < 0 else '❌ FAIL'}")
            
    except Exception as e:
        print(f"Error in detailed ball dominance test: {e}")

if __name__ == "__main__":
    test_enhanced_validation()
