"""
Comprehensive Error Handling and Monitoring System

This module provides robust error handling, monitoring, and alerting
capabilities for the NBA Lineup Optimizer.
"""

import logging
import traceback
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import streamlit as st
from functools import wraps
import json

class ErrorHandler:
    """Comprehensive error handling system."""
    
    def __init__(self, config):
        self.config = config
        self.error_log_file = Path("logs/errors.log")
        self.error_log_file.parent.mkdir(exist_ok=True)
        self.setup_error_logging()
        self.error_counts = {}
        self.alert_thresholds = {
            "error_rate": 0.1,  # 10% error rate
            "consecutive_errors": 5,
            "critical_errors": 1
        }
    
    def setup_error_logging(self):
        """Setup error logging."""
        error_logger = logging.getLogger("error_handler")
        error_logger.setLevel(logging.ERROR)
        
        # Create file handler for errors
        handler = logging.FileHandler(self.error_log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        error_logger.addHandler(handler)
        
        self.error_logger = error_logger
    
    def handle_error(self, error: Exception, context: str = "", 
                    user_id: str = None, severity: str = "error") -> Dict[str, Any]:
        """Handle and log error."""
        error_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "user_id": user_id,
            "severity": severity,
            "traceback": traceback.format_exc()
        }
        
        # Log error
        self.error_logger.error(f"Error in {context}: {str(error)}", exc_info=True)
        
        # Update error counts
        self._update_error_counts(context, severity)
        
        # Check for alerts
        self._check_alerts()
        
        return error_info
    
    def _update_error_counts(self, context: str, severity: str):
        """Update error counts for monitoring."""
        if context not in self.error_counts:
            self.error_counts[context] = {
                "total": 0,
                "errors": 0,
                "warnings": 0,
                "critical": 0,
                "last_error": None
            }
        
        self.error_counts[context]["total"] += 1
        self.error_counts[context][severity] += 1
        self.error_counts[context]["last_error"] = datetime.utcnow().isoformat()
    
    def _check_alerts(self):
        """Check if alerts should be triggered."""
        for context, counts in self.error_counts.items():
            # Check error rate
            if counts["total"] > 10:  # Only check after 10 total events
                error_rate = counts["errors"] / counts["total"]
                if error_rate > self.alert_thresholds["error_rate"]:
                    self._trigger_alert(f"High error rate in {context}: {error_rate:.2%}")
            
            # Check consecutive errors
            if counts["errors"] >= self.alert_thresholds["consecutive_errors"]:
                self._trigger_alert(f"Consecutive errors in {context}: {counts['errors']}")
            
            # Check critical errors
            if counts["critical"] >= self.alert_thresholds["critical_errors"]:
                self._trigger_alert(f"Critical error in {context}: {counts['critical']}")
    
    def _trigger_alert(self, message: str):
        """Trigger alert (placeholder for actual alerting system)."""
        # In production, this would send alerts via email, Slack, etc.
        logging.critical(f"ALERT: {message}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary for monitoring."""
        total_errors = sum(counts["total"] for counts in self.error_counts.values())
        total_critical = sum(counts["critical"] for counts in self.error_counts.values())
        
        return {
            "total_errors": total_errors,
            "critical_errors": total_critical,
            "error_rate": total_errors / max(1, total_errors + 100),  # Placeholder for total requests
            "contexts": self.error_counts,
            "last_updated": datetime.utcnow().isoformat()
        }

class MonitoringSystem:
    """Comprehensive monitoring system."""
    
    def __init__(self, config):
        self.config = config
        self.start_time = time.time()
        self.metrics_file = Path("data/metrics.json")
        self.metrics_file.parent.mkdir(exist_ok=True)
        self.metrics = self._load_metrics()
    
    def _load_metrics(self) -> Dict[str, Any]:
        """Load metrics from file."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return self._initialize_metrics()
        return self._initialize_metrics()
    
    def _initialize_metrics(self) -> Dict[str, Any]:
        """Initialize metrics structure."""
        return {
            "requests": 0,
            "errors": 0,
            "model_evaluations": 0,
            "avg_response_time": 0.0,
            "response_times": [],
            "start_time": self.start_time,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def _save_metrics(self):
        """Save metrics to file."""
        self.metrics["last_updated"] = datetime.utcnow().isoformat()
        try:
            with open(self.metrics_file, "w") as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save metrics: {e}")
    
    def track_request(self, duration: float = 0.0):
        """Track API request."""
        self.metrics["requests"] += 1
        self.metrics["response_times"].append(duration)
        
        # Keep only last 1000 response times
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]
        
        # Update average response time
        self.metrics["avg_response_time"] = sum(self.metrics["response_times"]) / len(self.metrics["response_times"])
        
        self._save_metrics()
    
    def track_error(self):
        """Track error occurrence."""
        self.metrics["errors"] += 1
        self._save_metrics()
    
    def track_model_evaluation(self, duration: float):
        """Track model evaluation."""
        self.metrics["model_evaluations"] += 1
        self._save_metrics()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        uptime = time.time() - self.start_time
        error_rate = self.metrics["errors"] / max(1, self.metrics["requests"])
        
        return {
            **self.metrics,
            "uptime": uptime,
            "uptime_hours": uptime / 3600,
            "requests_per_hour": self.metrics["requests"] / (uptime / 3600) if uptime > 0 else 0,
            "error_rate": error_rate,
            "p95_response_time": self._calculate_percentile(95),
            "p99_response_time": self._calculate_percentile(99)
        }
    
    def _calculate_percentile(self, percentile: int) -> float:
        """Calculate response time percentile."""
        if not self.metrics["response_times"]:
            return 0.0
        
        sorted_times = sorted(self.metrics["response_times"])
        index = int(len(sorted_times) * percentile / 100)
        return sorted_times[min(index, len(sorted_times) - 1)]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status."""
        metrics = self.get_metrics()
        
        # Health checks
        health_checks = {
            "database": self._check_database_health(),
            "models": self._check_model_health(),
            "disk_space": self._check_disk_space(),
            "memory": self._check_memory_usage()
        }
        
        # Overall health
        overall_health = "healthy"
        if any(check["status"] != "healthy" for check in health_checks.values()):
            overall_health = "degraded"
        if any(check["status"] == "critical" for check in health_checks.values()):
            overall_health = "critical"
        
        return {
            "overall_health": overall_health,
            "health_checks": health_checks,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            db_path = Path(self.config.DATABASE_PATH)
            if not db_path.exists():
                return {"status": "critical", "message": "Database file not found"}
            
            # Check file size
            size_mb = db_path.stat().st_size / (1024 * 1024)
            if size_mb < 1:
                return {"status": "warning", "message": f"Database file is small: {size_mb:.1f}MB"}
            
            return {"status": "healthy", "message": f"Database OK ({size_mb:.1f}MB)"}
        except Exception as e:
            return {"status": "critical", "message": f"Database check failed: {str(e)}"}
    
    def _check_model_health(self) -> Dict[str, Any]:
        """Check model health."""
        try:
            coeff_path = Path(self.config.MODEL_COEFFICIENTS_PATH)
            if not coeff_path.exists():
                return {"status": "warning", "message": "Model coefficients not found"}
            
            return {"status": "healthy", "message": "Models OK"}
        except Exception as e:
            return {"status": "critical", "message": f"Model check failed: {str(e)}"}
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space."""
        try:
            import shutil
            total, used, free = shutil.disk_usage(".")
            free_percent = (free / total) * 100
            
            if free_percent < 5:
                return {"status": "critical", "message": f"Low disk space: {free_percent:.1f}%"}
            elif free_percent < 20:
                return {"status": "warning", "message": f"Disk space warning: {free_percent:.1f}%"}
            
            return {"status": "healthy", "message": f"Disk space OK: {free_percent:.1f}%"}
        except Exception as e:
            return {"status": "warning", "message": f"Disk space check failed: {str(e)}"}
    
    def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            used_percent = memory.percent
            
            if used_percent > 90:
                return {"status": "critical", "message": f"High memory usage: {used_percent:.1f}%"}
            elif used_percent > 80:
                return {"status": "warning", "message": f"Memory usage warning: {used_percent:.1f}%"}
            
            return {"status": "healthy", "message": f"Memory OK: {used_percent:.1f}%"}
        except Exception as e:
            return {"status": "warning", "message": f"Memory check failed: {str(e)}"}

def error_handler(error_type: str = "error", context: str = ""):
    """Decorator for error handling."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get error handler from config
                from config import get_config
                config = get_config()
                error_handler = ErrorHandler(config)
                
                error_info = error_handler.handle_error(e, context, severity=error_type)
                
                # Show user-friendly error message
                if error_type == "critical":
                    st.error(f"Critical error: {str(e)}")
                elif error_type == "warning":
                    st.warning(f"Warning: {str(e)}")
                else:
                    st.error(f"Error: {str(e)}")
                
                return None
        return wrapper
    return decorator

def monitor_performance(func_name: str):
    """Decorator for performance monitoring."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Track performance
                from config import get_config
                config = get_config()
                monitor = MonitoringSystem(config)
                monitor.track_request(duration)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                # Track error
                from config import get_config
                config = get_config()
                monitor = MonitoringSystem(config)
                monitor.track_error()
                
                raise
        return wrapper
    return decorator

# Global instances
error_handler = None
monitoring_system = None

def get_error_handler(config) -> ErrorHandler:
    """Get global error handler instance."""
    global error_handler
    if error_handler is None:
        error_handler = ErrorHandler(config)
    return error_handler

def get_monitoring_system(config) -> MonitoringSystem:
    """Get global monitoring system instance."""
    global monitoring_system
    if monitoring_system is None:
        monitoring_system = MonitoringSystem(config)
    return monitoring_system
