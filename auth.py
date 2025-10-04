"""
Authentication system for NBA Lineup Optimizer
"""

import streamlit as st
import hashlib
import time
from typing import Optional, Dict
from config import get_config

class AuthManager:
    """Simple authentication manager for Streamlit."""
    
    def __init__(self):
        self.config = get_config()
        self.session_timeout = 3600  # 1 hour
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return self.hash_password(password) == hashed
    
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate user."""
        if not self.config.ENABLE_AUTH:
            return True
        
        if username not in self.config.AUTH_USERS:
            return False
        
        stored_password = self.config.AUTH_USERS[username]
        return self.verify_password(password, stored_password)
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        if not self.config.ENABLE_AUTH:
            return True
        
        if "authenticated" not in st.session_state:
            return False
        
        if "auth_time" not in st.session_state:
            return False
        
        # Check session timeout
        if time.time() - st.session_state.auth_time > self.session_timeout:
            self.logout()
            return False
        
        return st.session_state.authenticated
    
    def login(self, username: str, password: str) -> bool:
        """Login user."""
        if self.authenticate(username, password):
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.auth_time = time.time()
            return True
        return False
    
    def logout(self):
        """Logout user."""
        for key in ["authenticated", "username", "auth_time"]:
            if key in st.session_state:
                del st.session_state[key]
    
    def get_username(self) -> Optional[str]:
        """Get current username."""
        if self.is_authenticated():
            return st.session_state.get("username")
        return None
    
    def require_auth(self):
        """Decorator to require authentication for a function."""
        if not self.is_authenticated():
            self.show_login_form()
            st.stop()
    
    def show_login_form(self):
        """Show login form."""
        st.title("🔐 NBA Lineup Optimizer - Login")
        st.markdown("Please log in to access the dashboard.")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                if self.login(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.markdown("---")
        st.markdown("**Demo Credentials:**")
        st.markdown("- Username: `admin` | Password: `admin123`")
        st.markdown("- Username: `user` | Password: `user123`")

# Global auth manager instance
auth_manager = AuthManager()
