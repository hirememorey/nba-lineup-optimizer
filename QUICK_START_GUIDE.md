# Quick Start Guide - Production System

**Date**: October 3, 2025  
**Status**: ✅ **PRODUCTION READY**

## Overview

This guide provides quick instructions for using the production NBA Lineup Optimizer system. The system now includes authentication, user management, monitoring, and enterprise-grade features while maintaining the core analytical capabilities.

## Quick Start

### 1. Deploy the Production System

#### Option A: Docker Deployment (Recommended)

```bash
# Deploy the complete production system
docker-compose up -d

# Check logs
docker-compose logs -f

# Access dashboard at http://localhost:8502
```

#### Option B: Direct Python Deployment

```bash
# Run the production system
python run_production.py

# Access dashboard at http://localhost:8502
```

### 2. Login and Access Features

1. **Login**: Use default credentials:
   - Admin: `admin` / `admin123`
   - User: `user` / `user123`

2. **Navigate**: Use the sidebar to access:
   - Model switching and lineup evaluation
   - Personal dashboard and analytics
   - System metrics and monitoring
   - Admin panel (admin users only)

3. **Evaluate Lineups**: 
   - Enter 5 player IDs or use sample lineups
   - Switch between production and original models
   - Compare models side-by-side

4. **Compare Models**: Enable "Comparison Mode" to see both models side-by-side

### 3. Use in Code

```python
from src.nba_stats.model_factory import ModelFactory, evaluate_lineup

# Evaluate with production model
result = evaluate_lineup([2544, 101108, 201142, 201143, 201144], "simple")
print(f"Predicted outcome: {result.predicted_outcome}")
print(f"Model type: {result.model_type}")

# Evaluate with fallback (automatically falls back if primary fails)
result = ModelFactory.evaluate_lineup_with_fallback(lineup, "simple")
```

## Key Features

### 🎯 **Model Switching**
- **Sidebar Controls**: Easy toggle between models
- **Real-time Switching**: Instant model changes
- **Visual Indicators**: Clear model type display
- **Fallback Protection**: Automatic fallback if primary model fails

### ⚖️ **Comparison Mode**
- **Side-by-Side Evaluation**: Compare both models on same lineup
- **Detailed Metrics**: See differences in predictions
- **Performance Comparison**: Compare evaluation times
- **Result Validation**: Verify both models work correctly

### 📊 **Performance Monitoring**
- **Real-time Metrics**: Track evaluation times and errors
- **Caching Statistics**: See cache hit rates
- **Memory Usage**: Monitor resource consumption
- **Error Tracking**: Track and display error rates

## Sample Lineups

The dashboard includes several sample lineups for testing:

- **LeBron + Lakers Core**: [2544, 101108, 201142, 201143, 201144]
- **Warriors Core**: [201142, 201939, 201144, 201935, 201566]
- **Celtics Core**: [201935, 201939, 201144, 201142, 201566]
- **Random Lineup**: [201142, 201939, 201144, 201935, 201566]

## Troubleshooting

### Common Issues

1. **Model Coefficients Not Found**
   - **Solution**: Run `python run_production_model.py` to generate coefficients
   - **Fallback**: System will use placeholder coefficients

2. **Database Connection Failed**
   - **Solution**: Ensure `src/nba_stats/db/nba_stats.db` exists
   - **Fallback**: Run the data pipeline first

3. **Player Not Found**
   - **Solution**: Use player IDs from the blessed set (525 players)
   - **Fallback**: Check player IDs in the database

### Performance Issues

1. **Slow Loading**
   - **Solution**: Models use lazy loading - first evaluation may be slower
   - **Optimization**: Subsequent evaluations are cached and faster

2. **Memory Usage**
   - **Solution**: System uses lazy loading to minimize memory usage
   - **Monitoring**: Check performance metrics tab for usage statistics

## Advanced Usage

### Performance Optimization

```python
from src.nba_stats.performance_optimizer import preload_models, get_performance_metrics

# Preload both models for better performance
preload_models()

# Get performance metrics
metrics = get_performance_metrics()
print(metrics)
```

### Model Validation

```python
from src.nba_stats.model_factory import ModelFactory

# Validate model type
if ModelFactory.validate_model_type("simple"):
    print("Simple model is available")

# Get available models
models = ModelFactory.get_available_models()
for model in models:
    print(f"{model['name']}: {model['description']}")
```

## Next Steps

1. **Explore the Dashboard**: Try different lineups and model combinations
2. **Compare Models**: Use comparison mode to see differences
3. **Monitor Performance**: Check the performance metrics tab
4. **Integrate in Code**: Use the model factory in your own scripts
5. **Provide Feedback**: Report any issues or suggestions

## Support

- **Documentation**: See `IMPLEMENTATION_COMPLETE.md` for detailed information
- **Testing**: Run `python test_integration_end_to_end.py` to verify everything works
- **Issues**: Check the performance metrics tab for error information
- **Code Examples**: See the model factory documentation for usage examples

The model integration is complete and ready for production use!
