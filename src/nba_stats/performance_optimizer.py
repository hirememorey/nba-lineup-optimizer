"""
Performance Optimizer

This module provides performance optimization utilities for the model evaluators,
including lazy loading, caching, and performance monitoring.

Key Features:
1. Lazy loading of model coefficients
2. Result caching for repeated evaluations
3. Performance monitoring and metrics
4. Memory usage optimization
"""

import time
import logging
from typing import Dict, List, Any, Optional, Callable
from functools import wraps
import threading
from collections import defaultdict

# Set up logging
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor and track performance metrics for model operations."""
    
    def __init__(self):
        """Initialize the performance monitor."""
        self.metrics = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'errors': 0
        })
        self._lock = threading.Lock()
    
    def record_operation(self, operation: str, duration: float, success: bool = True):
        """Record an operation's performance metrics."""
        with self._lock:
            metrics = self.metrics[operation]
            metrics['count'] += 1
            metrics['total_time'] += duration
            metrics['min_time'] = min(metrics['min_time'], duration)
            metrics['max_time'] = max(metrics['max_time'], duration)
            if not success:
                metrics['errors'] += 1
    
    def get_metrics(self, operation: str = None) -> Dict[str, Any]:
        """Get performance metrics for an operation or all operations."""
        with self._lock:
            if operation:
                return dict(self.metrics[operation])
            else:
                return {op: dict(metrics) for op, metrics in self.metrics.items()}
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all performance metrics."""
        with self._lock:
            summary = {}
            for operation, metrics in self.metrics.items():
                if metrics['count'] > 0:
                    summary[operation] = {
                        'count': metrics['count'],
                        'avg_time': metrics['total_time'] / metrics['count'],
                        'min_time': metrics['min_time'],
                        'max_time': metrics['max_time'],
                        'error_rate': metrics['errors'] / metrics['count'],
                        'total_time': metrics['total_time']
                    }
            return summary

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def monitor_performance(operation_name: str):
    """Decorator to monitor the performance of a function."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                performance_monitor.record_operation(operation_name, duration, success)
        return wrapper
    return decorator

class ResultCache:
    """Simple cache for storing evaluation results."""
    
    def __init__(self, max_size: int = 1000):
        """Initialize the result cache."""
        self.cache = {}
        self.max_size = max_size
        self._lock = threading.Lock()
    
    def _make_key(self, lineup: List[int]) -> str:
        """Create a cache key from a lineup."""
        return str(sorted(lineup))
    
    def get(self, lineup: List[int]) -> Optional[Any]:
        """Get a cached result for a lineup."""
        with self._lock:
            key = self._make_key(lineup)
            return self.cache.get(key)
    
    def set(self, lineup: List[int], result: Any):
        """Cache a result for a lineup."""
        with self._lock:
            key = self._make_key(lineup)
            
            # If cache is full, remove oldest entry
            if len(self.cache) >= self.max_size:
                # Remove first item (oldest)
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            
            self.cache[key] = result
    
    def clear(self):
        """Clear the cache."""
        with self._lock:
            self.cache.clear()
    
    def size(self) -> int:
        """Get the current cache size."""
        with self._lock:
            return len(self.cache)

# Global result cache instance
result_cache = ResultCache()

class LazyModelLoader:
    """Lazy loader for model evaluators to improve startup time."""
    
    def __init__(self):
        """Initialize the lazy loader."""
        self._original_evaluator = None
        self._simple_evaluator = None
        self._lock = threading.Lock()
    
    def get_original_evaluator(self):
        """Get the original evaluator, creating it if necessary."""
        if self._original_evaluator is None:
            with self._lock:
                if self._original_evaluator is None:
                    logger.info("Lazy loading original ModelEvaluator...")
                    from .model_evaluator import ModelEvaluator
                    self._original_evaluator = ModelEvaluator()
                    logger.info("Original ModelEvaluator loaded")
        return self._original_evaluator
    
    def get_simple_evaluator(self):
        """Get the simple evaluator, creating it if necessary."""
        if self._simple_evaluator is None:
            with self._lock:
                if self._simple_evaluator is None:
                    logger.info("Lazy loading SimpleModelEvaluator...")
                    from .simple_model_evaluator import SimpleModelEvaluator
                    self._simple_evaluator = SimpleModelEvaluator()
                    logger.info("SimpleModelEvaluator loaded")
        return self._simple_evaluator
    
    def preload_models(self):
        """Preload both models for better performance."""
        logger.info("Preloading both model evaluators...")
        self.get_original_evaluator()
        self.get_simple_evaluator()
        logger.info("Both models preloaded successfully")

# Global lazy loader instance
lazy_loader = LazyModelLoader()

class OptimizedModelFactory:
    """Optimized version of ModelFactory with performance enhancements."""
    
    @staticmethod
    @monitor_performance("model_creation")
    def create_evaluator(model_type: str):
        """Create a model evaluator with performance monitoring."""
        if model_type == "original":
            return lazy_loader.get_original_evaluator()
        elif model_type == "simple":
            return lazy_loader.get_simple_evaluator()
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    @staticmethod
    @monitor_performance("lineup_evaluation")
    def evaluate_lineup_cached(lineup: List[int], model_type: str):
        """Evaluate a lineup with caching for performance."""
        # Check cache first
        cache_key = f"{model_type}:{sorted(lineup)}"
        cached_result = result_cache.get(lineup)
        
        if cached_result is not None:
            logger.debug("Cache hit for lineup evaluation")
            return cached_result
        
        # Evaluate and cache result
        evaluator = OptimizedModelFactory.create_evaluator(model_type)
        result = evaluator.evaluate_lineup(lineup)
        
        # Cache the result
        result_cache.set(lineup, result)
        logger.debug("Cached lineup evaluation result")
        
        return result
    
    @staticmethod
    def get_performance_summary() -> Dict[str, Any]:
        """Get a summary of performance metrics."""
        return performance_monitor.get_summary()
    
    @staticmethod
    def clear_cache():
        """Clear the result cache."""
        result_cache.clear()
        logger.info("Result cache cleared")
    
    @staticmethod
    def preload_models():
        """Preload both models for better performance."""
        lazy_loader.preload_models()

def get_performance_metrics() -> Dict[str, Any]:
    """Get current performance metrics."""
    return performance_monitor.get_summary()

def clear_performance_cache():
    """Clear the performance cache."""
    result_cache.clear()

def preload_models():
    """Preload both model evaluators."""
    lazy_loader.preload_models()
