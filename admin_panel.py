"""
Admin Panel for NBA Lineup Optimizer

This module provides administrative functionality including user management,
system monitoring, data export, and configuration management.
"""

import streamlit as st
import pandas as pd
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import io
import base64

from config import get_config
from auth import auth_manager
from monitoring import MonitoringSystem, log_error
from user_onboarding import get_user_analytics
from data_protection import get_data_protection

class AdminPanel:
    """Admin panel for system management."""
    
    def __init__(self):
        self.config = get_config()
        self.monitoring = MonitoringSystem()
        self.error_handler = log_error
        self.user_analytics = get_user_analytics(self.config)
        self.data_protection = get_data_protection(self.config)
    
    def show_admin_dashboard(self):
        """Show main admin dashboard."""
        st.title("🔧 Admin Panel")
        st.markdown("---")
        
        # Check admin access
        if not self._check_admin_access():
            st.error("Access denied. Admin privileges required.")
            return
        
        # Admin tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "System Status", "User Management", "Data Export", 
            "Logs & Monitoring", "Configuration"
        ])
        
        with tab1:
            self.show_system_status()
        
        with tab2:
            self.show_user_management()
        
        with tab3:
            self.show_data_export()
        
        with tab4:
            self.show_logs_monitoring()
        
        with tab5:
            self.show_configuration()
    
    def _check_admin_access(self) -> bool:
        """Check if current user has admin access."""
        if not auth_manager.is_authenticated():
            return False
        
        username = auth_manager.get_username()
        return username == "admin"
    
    def show_system_status(self):
        """Show system status overview."""
        st.header("System Status")
        
        # Health status
        health_status = self.monitoring.get_health_status()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            health_color = {
                "healthy": "🟢",
                "degraded": "🟡", 
                "critical": "🔴"
            }.get(health_status["overall_health"], "⚪")
            st.metric("Overall Health", f"{health_color} {health_status['overall_health'].title()}")
        
        with col2:
            uptime_hours = health_status["metrics"]["uptime_hours"]
            st.metric("Uptime", f"{uptime_hours:.1f} hours")
        
        with col3:
            error_rate = health_status["metrics"]["error_rate"]
            st.metric("Error Rate", f"{error_rate:.2%}")
        
        # Health checks
        st.subheader("Health Checks")
        for check_name, check_data in health_status["health_checks"].items():
            status_icon = {
                "healthy": "✅",
                "warning": "⚠️",
                "critical": "❌"
            }.get(check_data["status"], "❓")
            
            st.write(f"{status_icon} **{check_name.title()}**: {check_data['message']}")
        
        # Metrics
        st.subheader("Performance Metrics")
        metrics = health_status["metrics"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Requests", metrics["requests"])
            st.metric("Model Evaluations", metrics["model_evaluations"])
        
        with col2:
            st.metric("Avg Response Time", f"{metrics['avg_response_time']:.2f}s")
            st.metric("P95 Response Time", f"{metrics['p95_response_time']:.2f}s")
    
    def show_user_management(self):
        """Show user management interface."""
        st.header("User Management")
        
        # User analytics
        system_analytics = self.user_analytics.get_system_analytics()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Users", system_analytics["total_users"])
        
        with col2:
            st.metric("Total Sessions", system_analytics["total_sessions"])
        
        with col3:
            st.metric("Total Events", system_analytics["total_events"])
        
        # User list
        st.subheader("User List")
        users_data = []
        for user_id, user_data in self.user_analytics.analytics_data["users"].items():
            users_data.append({
                "User ID": user_id,
                "First Seen": user_data["first_seen"],
                "Last Seen": user_data["last_seen"],
                "Total Sessions": user_data["total_sessions"],
                "Total Events": user_data["total_events"],
                "Features Used": len(user_data["features_used"])
            })
        
        if users_data:
            df = pd.DataFrame(users_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No user data available")
        
        # Feature usage
        st.subheader("Feature Usage")
        feature_usage = system_analytics["metrics"]["most_used_features"]
        if feature_usage:
            feature_df = pd.DataFrame([
                {"Feature": feature, "Usage Count": count}
                for feature, count in feature_usage.items()
            ])
            st.dataframe(feature_df, use_container_width=True)
        else:
            st.info("No feature usage data available")
    
    def show_data_export(self):
        """Show data export interface."""
        st.header("Data Export")
        
        # Export options
        export_type = st.selectbox(
            "Select data to export",
            ["User Analytics", "System Metrics", "Error Logs", "Audit Logs", "Database Backup"]
        )
        
        if st.button("Generate Export"):
            with st.spinner("Generating export..."):
                if export_type == "User Analytics":
                    self._export_user_analytics()
                elif export_type == "System Metrics":
                    self._export_system_metrics()
                elif export_type == "Error Logs":
                    self._export_error_logs()
                elif export_type == "Audit Logs":
                    self._export_audit_logs()
                elif export_type == "Database Backup":
                    self._export_database_backup()
    
    def _export_user_analytics(self):
        """Export user analytics data."""
        system_analytics = self.user_analytics.get_system_analytics()
        
        # Create CSV
        csv_data = []
        for user_id, user_data in self.user_analytics.analytics_data["users"].items():
            csv_data.append({
                "user_id": user_id,
                "first_seen": user_data["first_seen"],
                "last_seen": user_data["last_seen"],
                "total_sessions": user_data["total_sessions"],
                "total_events": user_data["total_events"],
                "features_used": ", ".join(user_data["features_used"])
            })
        
        df = pd.DataFrame(csv_data)
        csv = df.to_csv(index=False)
        
        # Download button
        st.download_button(
            label="Download User Analytics CSV",
            data=csv,
            file_name=f"user_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    def _export_system_metrics(self):
        """Export system metrics."""
        metrics = self.monitoring.get_metrics()
        
        # Create JSON
        json_data = json.dumps(metrics, indent=2)
        
        # Download button
        st.download_button(
            label="Download System Metrics JSON",
            data=json_data,
            file_name=f"system_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def _export_error_logs(self):
        """Export error logs."""
        error_file = Path("logs/errors.log")
        if error_file.exists():
            with open(error_file, "r") as f:
                log_data = f.read()
            
            st.download_button(
                label="Download Error Logs",
                data=log_data,
                file_name=f"error_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                mime="text/plain"
            )
        else:
            st.warning("No error logs found")
    
    def _export_audit_logs(self):
        """Export audit logs."""
        audit_logs = self.data_protection.get_audit_logs()
        
        if audit_logs:
            # Convert to CSV
            csv_data = []
            for log in audit_logs:
                csv_data.append({
                    "timestamp": log["timestamp"],
                    "event_type": log["event_type"],
                    "user": log["user"],
                    "details": json.dumps(log["details"])
                })
            
            df = pd.DataFrame(csv_data)
            csv = df.to_csv(index=False)
            
            st.download_button(
                label="Download Audit Logs CSV",
                data=csv,
                file_name=f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No audit logs found")
    
    def _export_database_backup(self):
        """Export database backup."""
        try:
            # Create encrypted backup
            backup_path = f"backups/database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.enc"
            self.data_protection.create_secure_backup(
                self.config.DATABASE_PATH,
                backup_path
            )
            
            # Read backup file
            with open(backup_path, "rb") as f:
                backup_data = f.read()
            
            # Encode for download
            b64_data = base64.b64encode(backup_data).decode()
            
            st.download_button(
                label="Download Encrypted Database Backup",
                data=b64_data,
                file_name=f"database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.enc",
                mime="application/octet-stream"
            )
            
            st.success("Database backup created successfully")
            
        except Exception as e:
            st.error(f"Failed to create database backup: {str(e)}")
    
    def show_logs_monitoring(self):
        """Show logs and monitoring interface."""
        st.header("Logs & Monitoring")
        
        # Error summary
        error_summary = self.error_handler.get_error_summary()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Errors", error_summary["total_errors"])
        
        with col2:
            st.metric("Critical Errors", error_summary["critical_errors"])
        
        with col3:
            st.metric("Error Rate", f"{error_summary['error_rate']:.2%}")
        
        # Error contexts
        st.subheader("Error Contexts")
        if error_summary["contexts"]:
            context_data = []
            for context, counts in error_summary["contexts"].items():
                context_data.append({
                    "Context": context,
                    "Total": counts["total"],
                    "Errors": counts["errors"],
                    "Warnings": counts["warnings"],
                    "Critical": counts["critical"],
                    "Last Error": counts["last_error"]
                })
            
            df = pd.DataFrame(context_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No error data available")
        
        # Recent events
        st.subheader("Recent Events")
        system_analytics = self.user_analytics.get_system_analytics()
        recent_events = system_analytics["recent_events"]
        
        if recent_events:
            event_data = []
            for event in recent_events[-20:]:  # Last 20 events
                event_data.append({
                    "Timestamp": event["timestamp"],
                    "User": event["user_id"],
                    "Event": event["event_type"],
                    "Details": json.dumps(event["details"]) if event["details"] else ""
                })
            
            df = pd.DataFrame(event_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No recent events available")
    
    def show_configuration(self):
        """Show configuration management."""
        st.header("Configuration Management")
        
        # Current configuration
        st.subheader("Current Configuration")
        config_data = {
            "Environment": self.config.ENVIRONMENT,
            "Debug Mode": self.config.DEBUG,
            "Authentication Enabled": self.config.ENABLE_AUTH,
            "Database Path": self.config.DATABASE_PATH,
            "Model Coefficients Path": self.config.MODEL_COEFFICIENTS_PATH,
            "API Rate Limit": self.config.API_RATE_LIMIT,
            "Log Level": self.config.LOG_LEVEL
        }
        
        for key, value in config_data.items():
            st.write(f"**{key}**: {value}")
        
        # System actions
        st.subheader("System Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Refresh Metrics"):
                st.rerun()
            
            if st.button("Clear Error Counts"):
                self.error_handler.error_counts = {}
                st.success("Error counts cleared")
        
        with col2:
            if st.button("Cleanup Old Logs"):
                self.data_protection.cleanup_old_logs()
                st.success("Old logs cleaned up")
            
            if st.button("Generate Health Report"):
                health_status = self.monitoring.get_health_status()
                st.json(health_status)

def show_admin_panel():
    """Show admin panel if user has access."""
    admin_panel = AdminPanel()
    admin_panel.show_admin_dashboard()
