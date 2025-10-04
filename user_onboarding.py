"""
User Onboarding and Analytics System

This module provides user onboarding, analytics tracking, and user experience
monitoring for the NBA Lineup Optimizer.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import streamlit as st
from data_protection import get_data_protection

class UserAnalytics:
    """User analytics and tracking system."""
    
    def __init__(self, config):
        self.config = config
        self.data_protection = get_data_protection(config)
        self.analytics_file = Path("data/user_analytics.json")
        self.analytics_file.parent.mkdir(exist_ok=True)
        self.analytics_data = self._load_analytics()
    
    def _load_analytics(self) -> Dict[str, Any]:
        """Load analytics data."""
        if self.analytics_file.exists():
            try:
                with open(self.analytics_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return self._initialize_analytics()
        return self._initialize_analytics()
    
    def _initialize_analytics(self) -> Dict[str, Any]:
        """Initialize analytics data structure."""
        return {
            "users": {},
            "sessions": {},
            "events": [],
            "metrics": {
                "total_users": 0,
                "total_sessions": 0,
                "total_events": 0,
                "avg_session_duration": 0,
                "most_used_features": {},
                "error_rate": 0
            }
        }
    
    def _save_analytics(self):
        """Save analytics data."""
        try:
            with open(self.analytics_file, "w") as f:
                json.dump(self.analytics_data, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save analytics: {e}")
    
    def track_user_session(self, user_id: str, session_id: str, start_time: datetime):
        """Track user session start."""
        if user_id not in self.analytics_data["users"]:
            self.analytics_data["users"][user_id] = {
                "first_seen": start_time.isoformat(),
                "last_seen": start_time.isoformat(),
                "total_sessions": 0,
                "total_events": 0,
                "features_used": set()
            }
        
        self.analytics_data["sessions"][session_id] = {
            "user_id": user_id,
            "start_time": start_time.isoformat(),
            "end_time": None,
            "duration": 0,
            "events": [],
            "features_used": set()
        }
        
        # Update user data
        self.analytics_data["users"][user_id]["last_seen"] = start_time.isoformat()
        self.analytics_data["users"][user_id]["total_sessions"] += 1
        
        self._save_analytics()
    
    def track_user_event(self, user_id: str, session_id: str, event_type: str, 
                        details: Dict[str, Any] = None):
        """Track user event."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "session_id": session_id,
            "event_type": event_type,
            "details": details or {}
        }
        
        self.analytics_data["events"].append(event)
        
        # Update session data
        if session_id in self.analytics_data["sessions"]:
            self.analytics_data["sessions"][session_id]["events"].append(event)
        
        # Update user data
        if user_id in self.analytics_data["users"]:
            self.analytics_data["users"][user_id]["total_events"] += 1
        
        # Update metrics
        self.analytics_data["metrics"]["total_events"] += 1
        
        self._save_analytics()
    
    def track_feature_usage(self, user_id: str, session_id: str, feature: str):
        """Track feature usage."""
        if user_id in self.analytics_data["users"]:
            self.analytics_data["users"][user_id]["features_used"].add(feature)
        
        if session_id in self.analytics_data["sessions"]:
            self.analytics_data["sessions"][session_id]["features_used"].add(feature)
        
        # Update metrics
        if feature not in self.analytics_data["metrics"]["most_used_features"]:
            self.analytics_data["metrics"]["most_used_features"][feature] = 0
        self.analytics_data["metrics"]["most_used_features"][feature] += 1
        
        self._save_analytics()
    
    def end_user_session(self, session_id: str):
        """End user session."""
        if session_id in self.analytics_data["sessions"]:
            end_time = datetime.utcnow()
            start_time = datetime.fromisoformat(
                self.analytics_data["sessions"][session_id]["start_time"]
            )
            duration = (end_time - start_time).total_seconds()
            
            self.analytics_data["sessions"][session_id]["end_time"] = end_time.isoformat()
            self.analytics_data["sessions"][session_id]["duration"] = duration
            
            # Update metrics
            self._update_session_metrics()
            
            self._save_analytics()
    
    def _update_session_metrics(self):
        """Update session-related metrics."""
        sessions = self.analytics_data["sessions"]
        completed_sessions = [s for s in sessions.values() if s["end_time"] is not None]
        
        if completed_sessions:
            total_duration = sum(s["duration"] for s in completed_sessions)
            self.analytics_data["metrics"]["avg_session_duration"] = total_duration / len(completed_sessions)
        
        self.analytics_data["metrics"]["total_sessions"] = len(sessions)
        self.analytics_data["metrics"]["total_users"] = len(self.analytics_data["users"])
    
    def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get analytics for specific user."""
        if user_id not in self.analytics_data["users"]:
            return {}
        
        user_data = self.analytics_data["users"][user_id].copy()
        user_data["features_used"] = list(user_data["features_used"])
        
        # Get user sessions
        user_sessions = [
            session for session in self.analytics_data["sessions"].values()
            if session["user_id"] == user_id
        ]
        user_data["sessions"] = user_sessions
        
        return user_data
    
    def get_system_analytics(self) -> Dict[str, Any]:
        """Get system-wide analytics."""
        metrics = self.analytics_data["metrics"].copy()
        
        # Convert sets to lists for JSON serialization
        for user_id, user_data in self.analytics_data["users"].items():
            if "features_used" in user_data:
                user_data["features_used"] = list(user_data["features_used"])
        
        return {
            "metrics": metrics,
            "total_users": len(self.analytics_data["users"]),
            "total_sessions": len(self.analytics_data["sessions"]),
            "total_events": len(self.analytics_data["events"]),
            "recent_events": self.analytics_data["events"][-100:]  # Last 100 events
        }

class UserOnboarding:
    """User onboarding system."""
    
    def __init__(self, config):
        self.config = config
        self.analytics = UserAnalytics(config)
    
    def show_welcome_screen(self):
        """Show welcome screen for new users."""
        st.title("🏀 Welcome to NBA Lineup Optimizer")
        st.markdown("---")
        
        st.markdown("""
        ### What is NBA Lineup Optimizer?
        
        The NBA Lineup Optimizer is an advanced analytics tool that helps NBA teams and analysts 
        make data-driven decisions about player acquisition and lineup construction. Our system 
        uses cutting-edge machine learning to analyze how players fit together in different 
        lineups, going beyond individual player statistics to understand team chemistry and 
        tactical effectiveness.
        
        ### Key Features:
        
        - **Player Archetype Analysis**: Categorizes players into basketball-meaningful roles
        - **Lineup Evaluation**: Predicts how well different player combinations will perform
        - **Model Comparison**: Compare different analytical approaches side-by-side
        - **Performance Monitoring**: Track system performance and reliability
        - **Export Capabilities**: Download results for further analysis
        
        ### Getting Started:
        
        1. **Choose a Model**: Select between our production model (3 archetypes) or original model (8 archetypes)
        2. **Enter Player IDs**: Input 5 player IDs to evaluate a lineup
        3. **Analyze Results**: Review predicted outcomes, player archetypes, and skill scores
        4. **Compare Models**: Use comparison mode to see how different models evaluate the same lineup
        """)
        
        st.markdown("---")
        
        # Track onboarding view
        if "session_id" in st.session_state:
            self.analytics.track_user_event(
                st.session_state.get("username", "anonymous"),
                st.session_state["session_id"],
                "onboarding_viewed"
            )
    
    def show_tutorial(self):
        """Show interactive tutorial."""
        st.header("📚 Interactive Tutorial")
        
        tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Player IDs", "Model Selection", "Results"])
        
        with tab1:
            st.markdown("""
            ### How to Use the Dashboard
            
            The dashboard is organized into several key sections:
            
            - **Sidebar**: Model selection, performance metrics, and system status
            - **Main Area**: Lineup evaluation interface and results
            - **Comparison Mode**: Side-by-side model comparison
            """)
            
            if st.button("Next: Player IDs", key="tutorial_1"):
                st.session_state.tutorial_step = 2
                st.rerun()
        
        with tab2:
            st.markdown("""
            ### Finding Player IDs
            
            Player IDs are unique identifiers for each NBA player. Here are some ways to find them:
            
            - **Sample Lineups**: Use the pre-loaded sample lineups in the sidebar
            - **NBA.com**: Player IDs are often in the URL when viewing player pages
            - **API Documentation**: Check our API documentation for player ID lists
            
            **Example Player IDs:**
            - LeBron James: 2544
            - Stephen Curry: 201142
            - Kevin Durant: 201142
            """)
            
            if st.button("Next: Model Selection", key="tutorial_2"):
                st.session_state.tutorial_step = 3
                st.rerun()
        
        with tab3:
            st.markdown("""
            ### Model Selection
            
            We offer two analytical models:
            
            **Production Model (3-Archetype)**:
            - Uses 3 player archetypes: Big Men, Primary Ball Handlers, Role Players
            - Optimized for accuracy and speed
            - Recommended for most use cases
            
            **Original Model (8-Archetype)**:
            - Uses 8 player archetypes for more granular analysis
            - More complex but potentially more detailed
            - Good for research and comparison
            """)
            
            if st.button("Next: Results", key="tutorial_3"):
                st.session_state.tutorial_step = 4
                st.rerun()
        
        with tab4:
            st.markdown("""
            ### Understanding Results
            
            **Predicted Outcome**: The expected net points for the possession
            - Positive values indicate offensive advantage
            - Negative values indicate defensive advantage
            
            **Player Archetypes**: Each player's role classification
            - Big Men: Height, wingspan, frontcourt presence
            - Primary Ball Handlers: High usage, driving ability, playmaking
            - Role Players: Balanced contributors, catch-and-shoot ability
            
            **Skill Scores**: Detailed breakdown of player abilities
            - Offensive and defensive skill ratings
            - Archetype-specific metrics
            """)
            
            if st.button("Complete Tutorial", key="tutorial_4"):
                st.session_state.tutorial_completed = True
                st.success("Tutorial completed! You're ready to start using the dashboard.")
                st.rerun()
    
    def track_user_journey(self, step: str, details: Dict[str, Any] = None):
        """Track user journey through the application."""
        if "session_id" in st.session_state:
            self.analytics.track_user_event(
                st.session_state.get("username", "anonymous"),
                st.session_state["session_id"],
                f"user_journey_{step}",
                details
            )
    
    def show_user_dashboard(self):
        """Show personalized user dashboard."""
        if "username" not in st.session_state:
            return
        
        user_id = st.session_state["username"]
        user_analytics = self.analytics.get_user_analytics(user_id)
        
        if not user_analytics:
            return
        
        st.header(f"👤 Your Dashboard - {user_id}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Sessions", user_analytics.get("total_sessions", 0))
        
        with col2:
            st.metric("Total Events", user_analytics.get("total_events", 0))
        
        with col3:
            first_seen = user_analytics.get("first_seen", "Unknown")
            if first_seen != "Unknown":
                first_seen = datetime.fromisoformat(first_seen).strftime("%Y-%m-%d")
            st.metric("First Seen", first_seen)
        
        # Feature usage
        features_used = user_analytics.get("features_used", [])
        if features_used:
            st.subheader("Features Used")
            for feature in features_used:
                st.write(f"✅ {feature}")
        
        # Recent activity
        st.subheader("Recent Activity")
        recent_sessions = user_analytics.get("sessions", [])[-5:]  # Last 5 sessions
        
        for session in recent_sessions:
            start_time = datetime.fromisoformat(session["start_time"])
            duration = session.get("duration", 0)
            st.write(f"Session: {start_time.strftime('%Y-%m-%d %H:%M')} ({duration:.0f}s)")

# Global instances
user_analytics = None
user_onboarding = None

def get_user_analytics(config) -> UserAnalytics:
    """Get global user analytics instance."""
    global user_analytics
    if user_analytics is None:
        user_analytics = UserAnalytics(config)
    return user_analytics

def get_user_onboarding(config) -> UserOnboarding:
    """Get global user onboarding instance."""
    global user_onboarding
    if user_onboarding is None:
        user_onboarding = UserOnboarding(config)
    return user_onboarding
