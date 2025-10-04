#!/usr/bin/env python3
"""
Production Run of Simplified Bayesian Model

This script runs the simplified Bayesian model with production-quality
parameters to achieve proper convergence.
"""

import time
from simplified_bayesian_model import SimplifiedBayesianModel

def main():
    print("Production Run - Simplified Bayesian Model")
    print("=" * 50)
    
    # Initialize model
    model = SimplifiedBayesianModel()
    
    # Load data
    print("Loading data...")
    if not model.load_data():
        print("Failed to load data")
        return
    
    # Create model
    print("Creating model...")
    model.create_model()
    
    # Run production sampling with more chains and longer tuning
    print("Running production sampling...")
    print("Parameters: draws=2000, tune=1000, chains=4")
    
    start_time = time.time()
    
    try:
        model.sample(draws=2000, tune=1000, chains=4)
        
        total_time = time.time() - start_time
        print(f"\nSampling completed in {total_time:.1f} seconds")
        
        # Check convergence
        conv_stats = model.check_convergence()
        print(f"\nConvergence Results:")
        print(f"  Max R-hat: {conv_stats['max_rhat']:.3f}")
        print(f"  Min ESS: {conv_stats['min_ess']:.0f}")
        print(f"  Divergent transitions: {conv_stats['divergent_transitions']}")
        print(f"  Convergence passed: {conv_stats['convergence_passed']}")
        
        if conv_stats['convergence_passed']:
            print("\n🎉 PRODUCTION MODEL CONVERGED SUCCESSFULLY!")
            
            # Analyze coefficients
            coeff_df = model.analyze_coefficients()
            print(f"\nCoefficient Analysis:")
            print(coeff_df[['archetype', 'type', 'mean', 'hdi_3%', 'hdi_97%']].to_string(index=False))
            
            # Create plots
            model.plot_coefficients("production_coefficient_plots.png")
            
            # Save results
            model.save_results("production_model_results")
            
            print(f"\n✅ Production model complete!")
            print(f"   - Results saved to: production_model_results/")
            print(f"   - Plots saved to: production_coefficient_plots.png")
            print(f"   - Model is ready for integration with ModelEvaluator")
            
        else:
            print("\n⚠️  Model still not fully converged, but close:")
            print(f"   - R-hat: {conv_stats['max_rhat']:.3f} (target: <1.01)")
            print(f"   - ESS: {conv_stats['min_ess']:.0f} (target: >400)")
            print("   - Consider running with even more chains/tuning")
            
            # Still save results for analysis
            model.save_results("production_model_results")
            print(f"   - Partial results saved to: production_model_results/")
            
    except Exception as e:
        print(f"Error during production sampling: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
