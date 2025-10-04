"""
Monitoring and logging system for NBA Lineup Optimizer
"""

import logging
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from functools import wraps
import streamlit as st
from config import get_config

class MonitoringSystem:
    """Monitoring and logging system."""
    
    def __init__(self):
        self.config = get_config()
        self.setup_logging()
        self.metrics = {
            "requests": 0,
            "errors": 0,
            "model_evaluations": 0,
            "avg_response_time": 0.0,
            "start_time": time.time()
        }
    
    def setup_logging(self):
        """Setup logging configuration."""
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.config.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def log_request(self, endpoint: str, user: Optional[str] = None, duration: float = 0.0):
        """Log API request."""
        self.metrics["requests"] += 1
        self.update_avg_response_time(duration)
        
        self.logger.info(f"Request: {endpoint} | User: {user} | Duration: {duration:.2f}s")
    
    def log_error(self, error: Exception, context: str = ""):
        """Log error."""
        self.metrics["errors"] += 1
        self.logger.error(f"Error in {context}: {str(error)}", exc_info=True)
    
    def log_model_evaluation(self, model_type: str, duration: float):
        """Log model evaluation."""
        self.metrics["model_evaluations"] += 1
        self.logger.info(f"Model evaluation: {model_type} | Duration: {duration:.2f}s")
    
    def update_avg_response_time(self, duration: float):
        """Update average response time."""
        current_avg = self.metrics["avg_response_time"]
        request_count = self.metrics["requests"]
        
        if request_count == 1:
            self.metrics["avg_response_time"] = duration
        else:
            self.metrics["avg_response_time"] = (current_avg * (request_count - 1) + duration) / request_count
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        uptime = time.time() - self.metrics["start_time"]
        return {
            **self.metrics,
            "uptime": uptime,
            "uptime_hours": uptime / 3600,
            "requests_per_hour": self.metrics["requests"] / (uptime / 3600) if uptime > 0 else 0,
            "error_rate": self.metrics["errors"] / self.metrics["requests"] if self.metrics["requests"] > 0 else 0
        }
    
    def save_metrics(self):
        """Save metrics to file."""
        metrics_file = Path("logs/metrics.json")
        with open(metrics_file, "w") as f:
            json.dump(self.get_metrics(), f, indent=2)
    
    def monitor_function(self, func_name: str):
        """Decorator to monitor function execution."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    self.log_request(func_name, duration=duration)
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    self.log_error(e, func_name)
                    raise
            return wrapper
        return decorator

# Global monitoring instance
monitor = MonitoringSystem()

def track_performance(func_name: str):
    """Decorator to track function performance."""
    return monitor.monitor_function(func_name)

def log_user_action(action: str, details: Dict[str, Any] = None):
    """Log user action."""
    user = st.session_state.get("username", "anonymous")
    monitor.logger.info(f"User action: {action} | User: {user} | Details: {details or {}}")

def log_error(error: Exception, context: str = ""):
    """Log error."""
    monitor.log_error(error, context)

def get_system_metrics() -> Dict[str, Any]:
    """Get system metrics."""
    return monitor.get_metrics()
