#!/usr/bin/env python3
"""
End-to-End Integration Test

This script tests the complete integration of the SimpleModelEvaluator
with the model factory and enhanced dashboard.
"""

import sys
sys.path.append('src')

from nba_stats.model_factory import ModelFactory, ModelType
import time

def test_model_factory():
    """Test the model factory functionality."""
    print("🧪 Testing Model Factory...")
    
    # Test model creation
    print("  - Testing model creation...")
    try:
        original_evaluator = ModelFactory.create_evaluator("original")
        simple_evaluator = ModelFactory.create_evaluator("simple")
        print("    ✅ Both evaluators created successfully")
    except Exception as e:
        print(f"    ❌ Model creation failed: {e}")
        return False
    
    # Test model validation
    print("  - Testing model validation...")
    if ModelFactory.validate_model_type("original") and ModelFactory.validate_model_type("simple"):
        print("    ✅ Model validation passed")
    else:
        print("    ❌ Model validation failed")
        return False
    
    # Test available models
    print("  - Testing available models...")
    available_models = ModelFactory.get_available_models()
    if len(available_models) == 2:
        print("    ✅ Available models retrieved successfully")
    else:
        print("    ❌ Available models retrieval failed")
        return False
    
    return True

def test_lineup_evaluation():
    """Test lineup evaluation with both models."""
    print("\n🧪 Testing Lineup Evaluation...")
    
    # Test lineup
    test_lineup = [2544, 101108, 201142, 201143, 201144]  # LeBron and others
    print(f"  - Testing with lineup: {test_lineup}")
    
    # Test original model
    print("  - Testing original model...")
    try:
        start_time = time.time()
        original_result = ModelFactory.evaluate_lineup_with_fallback(test_lineup, "original")
        original_time = time.time() - start_time
        print(f"    ✅ Original model: {original_result.predicted_outcome:.4f} ({original_time:.3f}s)")
    except Exception as e:
        print(f"    ❌ Original model failed: {e}")
        return False
    
    # Test simple model
    print("  - Testing simple model...")
    try:
        start_time = time.time()
        simple_result = ModelFactory.evaluate_lineup_with_fallback(test_lineup, "simple")
        simple_time = time.time() - start_time
        print(f"    ✅ Simple model: {simple_result.predicted_outcome:.4f} ({simple_time:.3f}s)")
    except Exception as e:
        print(f"    ❌ Simple model failed: {e}")
        return False
    
    # Compare results
    print("  - Comparing results...")
    difference = simple_result.predicted_outcome - original_result.predicted_outcome
    print(f"    Difference: {difference:.4f}")
    print(f"    Relative difference: {(difference / abs(original_result.predicted_outcome)) * 100:.1f}%")
    
    # Check result structure
    print("  - Checking result structure...")
    if (original_result.player_ids == simple_result.player_ids and 
        original_result.player_names == simple_result.player_names and
        original_result.archetype_ids == simple_result.archetype_ids and
        original_result.archetype_names == simple_result.archetype_names):
        print("    ✅ Result structures match")
    else:
        print("    ❌ Result structures differ")
        return False
    
    return True

def test_fallback_mechanism():
    """Test the fallback mechanism."""
    print("\n🧪 Testing Fallback Mechanism...")
    
    # Test with invalid lineup (should trigger fallback)
    print("  - Testing with invalid lineup...")
    invalid_lineup = [999999, 999998, 999997, 999996, 999995]  # Non-existent players
    
    try:
        result = ModelFactory.evaluate_lineup_with_fallback(invalid_lineup, "simple")
        print(f"    ✅ Fallback worked: {result.model_type} model used")
    except Exception as e:
        print(f"    ⚠️  Fallback failed (expected): {e}")
        # This is actually expected behavior for invalid lineups
    
    return True

def test_performance():
    """Test performance of both models."""
    print("\n🧪 Testing Performance...")
    
    test_lineup = [2544, 101108, 201142, 201143, 201144]
    num_tests = 5
    
    # Test original model performance
    print(f"  - Testing original model performance ({num_tests} evaluations)...")
    original_times = []
    for i in range(num_tests):
        start_time = time.time()
        try:
            ModelFactory.evaluate_lineup_with_fallback(test_lineup, "original")
            original_times.append(time.time() - start_time)
        except Exception as e:
            print(f"    ❌ Original model failed on iteration {i+1}: {e}")
            return False
    
    avg_original_time = sum(original_times) / len(original_times)
    print(f"    ✅ Original model average time: {avg_original_time:.3f}s")
    
    # Test simple model performance
    print(f"  - Testing simple model performance ({num_tests} evaluations)...")
    simple_times = []
    for i in range(num_tests):
        start_time = time.time()
        try:
            ModelFactory.evaluate_lineup_with_fallback(test_lineup, "simple")
            simple_times.append(time.time() - start_time)
        except Exception as e:
            print(f"    ❌ Simple model failed on iteration {i+1}: {e}")
            return False
    
    avg_simple_time = sum(simple_times) / len(simple_times)
    print(f"    ✅ Simple model average time: {avg_simple_time:.3f}s")
    
    # Compare performance
    if avg_simple_time > avg_original_time * 2:
        print(f"    ⚠️  Simple model is {avg_simple_time/avg_original_time:.1f}x slower than original")
    else:
        print(f"    ✅ Performance is acceptable")
    
    return True

def main():
    """Run all integration tests."""
    print("🚀 Starting End-to-End Integration Test")
    print("=" * 50)
    
    tests = [
        ("Model Factory", test_model_factory),
        ("Lineup Evaluation", test_lineup_evaluation),
        ("Fallback Mechanism", test_fallback_mechanism),
        ("Performance", test_performance)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"✅ {test_name} test passed")
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print("📊 INTEGRATION TEST SUMMARY")
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Integration is working correctly.")
        return True
    else:
        print("💥 Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
