# Stan Model Scaling Issues

**Date**: October 3, 2025  
**Status**: ❌ **CRITICAL ISSUE - BLOCKING PRODUCTION**

## Problem Summary

The Stan model implementation works perfectly on small samples (≤5,000 possessions) but hangs indefinitely on larger samples (≥95,000 possessions). This prevents production deployment on the full 574k possession dataset.

## What We Know

### ✅ What Works
- **Small samples (≤5k possessions)**: Model compiles, runs, and converges successfully
- **Model validation**: Stan and PyMC produce similar results on same data
- **Data preparation**: Scales well (3 seconds for 95k possessions)
- **Model architecture**: Mathematically correct implementation

### ❌ What Fails
- **Large samples (≥95k possessions)**: Model hangs indefinitely during sampling
- **Production training**: 18-hour training run would likely fail
- **Memory usage**: May be excessive for large datasets

## Technical Details

### Model Complexity
The current Stan model has:
- **Parameters**: 3 + (M × 6) where M = number of unique matchups
- **For 95k sample**: ~570 unique matchups = ~3,420 parameters
- **For 574k dataset**: ~3,000+ unique matchups = ~18,000+ parameters

### Sampling Configuration
```python
# Current settings that work on small samples
chains = 2
iter_warmup = 500
iter_sampling = 1000
adapt_delta = 0.8
```

## Potential Solutions

### 1. Model Simplification
- **Reduce parameter count**: Use fewer matchup-specific parameters
- **Hierarchical structure**: Use hierarchical priors instead of separate parameters per matchup
- **Regularization**: Add stronger priors to prevent overfitting

### 2. Sampling Optimization
- **More chains**: Increase from 2 to 4+ chains
- **Longer tuning**: Increase warmup iterations
- **Different algorithm**: Try NUTS with different settings
- **Chunked processing**: Process data in smaller batches

### 3. Alternative Approaches
- **Use PyMC**: The prototype works reliably on all sample sizes
- **Different Stan syntax**: Try alternative Stan model formulations
- **Memory optimization**: Reduce memory footprint of data structures

## Immediate Workarounds

### Option 1: Use PyMC for Production
```python
# This works reliably on all sample sizes
from bayesian_model_prototype import BayesianModelPrototype

model = BayesianModelPrototype(data_path="production_bayesian_data.csv")
model.run_training()
```

### Option 2: Chunked Stan Processing
```python
# Process data in smaller chunks
chunk_size = 5000
for chunk in data_chunks:
    model.sample(data=chunk, ...)
```

## Investigation Steps

### 1. Memory Profiling
```python
import psutil
import time

# Monitor memory usage during sampling
process = psutil.Process()
start_memory = process.memory_info().rss / 1024 / 1024  # MB
# ... run sampling ...
end_memory = process.memory_info().rss / 1024 / 1024  # MB
print(f"Memory usage: {end_memory - start_memory:.1f} MB")
```

### 2. Parameter Count Analysis
```python
# Calculate actual parameter count
M = len(data['matchup'].unique())
total_params = 3 + (M * 6)  # 3 global + 6 per matchup
print(f"Total parameters: {total_params}")
```

### 3. Convergence Testing
```python
# Test different sample sizes incrementally
for size in [1000, 5000, 10000, 25000, 50000]:
    test_data = data.head(size)
    # Run model and check if it completes
```

## Recommendations

### For Immediate Production
1. **Use PyMC prototype** - It's proven to work on all sample sizes
2. **Implement monitoring** - Track memory and convergence metrics
3. **Document limitations** - Clearly mark Stan model as experimental

### For Future Development
1. **Investigate model simplification** - Reduce parameter complexity
2. **Test hierarchical approaches** - Use shared priors across matchups
3. **Consider alternative libraries** - PyMC, JAX, or other Bayesian frameworks

## Files Affected

- `bayesian_model.stan` - Stan model definition
- `train_bayesian_model.py` - Stan training script
- `compare_models.py` - Model comparison utility
- `create_production_sample.py` - Large sample creation

## Status

- **Current**: Stan model blocked for production use
- **Workaround**: PyMC prototype available for production
- **Next**: Investigate model simplification or use PyMC
