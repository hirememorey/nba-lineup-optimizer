"""
Fan-Friendly NBA Lineup Optimizer Dashboard

This dashboard provides an intuitive interface for NBA fans to:
- Select teams and view rosters
- Search for players by name
- Understand player-team fit with basketball explanations
- Get free agent recommendations
"""

import streamlit as st
import pandas as pd
from fan_friendly_mapping import FanFriendlyMapper, PlayerInfo, TeamInfo
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Optional

# Page configuration
st.set_page_config(
    page_title="NBA Lineup Optimizer - Fan Edition",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .team-card {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
    }
    .player-card {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.25rem 0;
        background-color: white;
    }
    .fit-good {
        color: #28a745;
        font-weight: bold;
    }
    .fit-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .fit-bad {
        color: #dc3545;
        font-weight: bold;
    }
    .position-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 3px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-right: 0.5rem;
    }
    .pg { background-color: #e3f2fd; color: #1976d2; }
    .sg { background-color: #f3e5f5; color: #7b1fa2; }
    .sf { background-color: #e8f5e8; color: #388e3c; }
    .pf { background-color: #fff3e0; color: #f57c00; }
    .c { background-color: #fce4ec; color: #c2185b; }
</style>
""", unsafe_allow_html=True)

class FanFriendlyDashboard:
    """Main dashboard class for fan-friendly interface."""
    
    def __init__(self):
        self.mapper = FanFriendlyMapper()
        self.players = []
        self.teams = []
        self.selected_team = None
        
    def initialize(self):
        """Initialize the dashboard with data."""
        if not self.mapper.connect_database():
            st.error("Failed to connect to database. Please check your database connection.")
            return False
        
        with st.spinner("Loading player and team data..."):
            self.players = self.mapper.load_players()
            self.teams = self.mapper.load_teams()
        
        if not self.players or not self.teams:
            st.error("Failed to load data. Please check your database.")
            return False
        
        return True
    
    def render_header(self):
        """Render the main header."""
        st.markdown('<h1 class="main-header">🏀 NBA Lineup Optimizer - Fan Edition</h1>', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <p style="font-size: 1.2rem; color: #666;">
                Find the perfect players for your favorite team using advanced analytics made simple
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """Render the sidebar with team selection and navigation."""
        st.sidebar.title("🎯 Team Selection")
        
        # Team selection dropdown
        team_names = [f"{team.team_name} ({team.team_abbreviation})" for team in self.teams]
        selected_team_name = st.sidebar.selectbox(
            "Choose your team:",
            team_names,
            index=0
        )
        
        # Find selected team
        selected_team_abbr = selected_team_name.split('(')[1].split(')')[0]
        self.selected_team = next((t for t in self.teams if t.team_abbreviation == selected_team_abbr), None)
        
        if self.selected_team:
            # Display team info
            st.sidebar.markdown(f"### {self.selected_team.team_name}")
            st.sidebar.markdown(f"**Players:** {len(self.selected_team.players)}")
            
            # Team needs
            needs = self.mapper.get_team_needs(self.selected_team)
            if needs:
                st.sidebar.markdown("**Team Needs:**")
                for need in needs:
                    st.sidebar.markdown(f"• {need}")
            else:
                st.sidebar.markdown("✅ **Well-balanced roster!**")
        
        # Navigation
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Analysis Tools")
        
        page = st.sidebar.radio(
            "Choose analysis:",
            ["Team Roster", "Player Search", "Free Agents", "Fit Analysis"]
        )
        
        return page
    
    def render_team_roster(self):
        """Render the team roster view."""
        if not self.selected_team:
            st.warning("Please select a team from the sidebar.")
            return
        
        st.header(f"👥 {self.selected_team.team_name} Roster")
        
        # Team overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Players", len(self.selected_team.players))
        
        with col2:
            position_balance = self.mapper.get_position_balance(self.selected_team)
            st.metric("Position Balance", f"{len(position_balance)} positions")
        
        with col3:
            needs = self.mapper.get_team_needs(self.selected_team)
            st.metric("Team Needs", len(needs))
        
        # Position balance chart
        if position_balance:
            fig = px.bar(
                x=list(position_balance.keys()),
                y=list(position_balance.values()),
                title="Position Distribution",
                labels={'x': 'Position', 'y': 'Number of Players'},
                color=list(position_balance.keys()),
                color_discrete_map={
                    'PG': '#e3f2fd', 'SG': '#f3e5f5', 'SF': '#e8f5e8', 
                    'PF': '#fff3e0', 'C': '#fce4ec'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Players by position
        st.subheader("📋 Players by Position")
        
        for position in ['PG', 'SG', 'SF', 'PF', 'C']:
            position_players = [p for p in self.selected_team.players if p.position == position]
            if position_players:
                st.markdown(f"### {position} - {len(position_players)} players")
                
                for player in sorted(position_players, key=lambda p: p.overall_rating, reverse=True):
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                        
                        with col1:
                            st.markdown(f"**{player.name}**")
                        
                        with col2:
                            st.markdown(f"<span class='position-badge {position.lower()}'>{position}</span>", unsafe_allow_html=True)
                        
                        with col3:
                            st.markdown(f"**{player.role}**")
                        
                        with col4:
                            st.markdown(f"Rating: {player.overall_rating:.1f}")
    
    def render_player_search(self):
        """Render the player search view."""
        st.header("🔍 Player Search")
        
        # Search input
        search_query = st.text_input(
            "Search for a player:",
            placeholder="Enter player name (e.g., LeBron, Curry, Durant)...",
            help="Search by any part of the player's name"
        )
        
        if search_query:
            # Perform search
            search_results = self.mapper.search_players(search_query, self.players)
            
            if search_results:
                st.success(f"Found {len(search_results)} players matching '{search_query}'")
                
                # Display results
                for i, player in enumerate(search_results[:10]):  # Show top 10
                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns([3, 1, 2, 2, 2])
                        
                        with col1:
                            st.markdown(f"**{player.name}**")
                        
                        with col2:
                            st.markdown(f"<span class='position-badge {player.position.lower()}'>{player.position}</span>", unsafe_allow_html=True)
                        
                        with col3:
                            st.markdown(f"**{player.role}**")
                        
                        with col4:
                            st.markdown(f"**{player.team_name}**")
                        
                        with col5:
                            st.markdown(f"Rating: {player.overall_rating:.1f}")
                        
                        # Show fit analysis if team is selected
                        if self.selected_team and player.team_id != self.selected_team.team_id:
                            fit_explanation = self.mapper.generate_fit_explanation(player, self.selected_team)
                            st.markdown(f"*{fit_explanation}*")
                        
                        st.markdown("---")
            else:
                st.warning(f"No players found matching '{search_query}'")
        else:
            st.info("Enter a player name to start searching")
    
    def render_free_agents(self):
        """Render the free agents view."""
        st.header("🆓 Free Agent Recommendations")
        
        if not self.selected_team:
            st.warning("Please select a team from the sidebar to see free agent recommendations.")
            return
        
        # Get free agents
        free_agents = self.mapper.get_free_agents(self.players)
        
        if not free_agents:
            st.info("No free agents found in the current database.")
            return
        
        st.success(f"Found {len(free_agents)} free agents")
        
        # Filter by team needs
        team_needs = self.mapper.get_team_needs(self.selected_team)
        needed_positions = [need.split()[-1] for need in team_needs]
        
        if needed_positions:
            st.subheader(f"🎯 Recommended for {self.selected_team.team_name}")
            st.markdown(f"*Based on team needs: {', '.join(needed_positions)}*")
            
            # Filter free agents by needed positions
            recommended_agents = [fa for fa in free_agents if fa.position in needed_positions]
            
            if recommended_agents:
                for player in sorted(recommended_agents, key=lambda p: p.overall_rating, reverse=True)[:5]:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 1, 2, 2])
                        
                        with col1:
                            st.markdown(f"**{player.name}**")
                        
                        with col2:
                            st.markdown(f"<span class='position-badge {player.position.lower()}'>{player.position}</span>", unsafe_allow_html=True)
                        
                        with col3:
                            st.markdown(f"**{player.role}**")
                        
                        with col4:
                            st.markdown(f"Rating: {player.overall_rating:.1f}")
                        
                        # Fit explanation
                        fit_explanation = self.mapper.generate_fit_explanation(player, self.selected_team)
                        st.markdown(f"*{fit_explanation}*")
                        
                        st.markdown("---")
            else:
                st.info("No free agents available for your team's needs")
        
        # All free agents
        st.subheader("📋 All Free Agents")
        
        for player in sorted(free_agents, key=lambda p: p.overall_rating, reverse=True)[:10]:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 2, 2])
                
                with col1:
                    st.markdown(f"**{player.name}**")
                
                with col2:
                    st.markdown(f"<span class='position-badge {player.position.lower()}'>{player.position}</span>", unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"**{player.role}**")
                
                with col4:
                    st.markdown(f"Rating: {player.overall_rating:.1f}")
                
                st.markdown("---")
    
    def render_fit_analysis(self):
        """Render the fit analysis view."""
        st.header("🔬 Fit Analysis")
        
        if not self.selected_team:
            st.warning("Please select a team from the sidebar to perform fit analysis.")
            return
        
        st.subheader(f"Analyzing {self.selected_team.team_name}")
        
        # Team analysis
        position_balance = self.mapper.get_position_balance(self.selected_team)
        team_needs = self.mapper.get_team_needs(self.selected_team)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Current Roster Balance")
            for position, count in position_balance.items():
                st.markdown(f"**{position}:** {count} players")
        
        with col2:
            st.markdown("### Team Needs")
            if team_needs:
                for need in team_needs:
                    st.markdown(f"• {need}")
            else:
                st.markdown("✅ Well-balanced roster!")
        
        # Player comparison
        st.subheader("Player Comparison")
        
        # Select two players to compare
        all_players = [p for p in self.players if p.team_id != self.selected_team.team_id]
        
        col1, col2 = st.columns(2)
        
        with col1:
            player1_name = st.selectbox(
                "Select Player 1:",
                [f"{p.name} ({p.position})" for p in all_players[:50]],  # Limit for performance
                key="player1"
            )
        
        with col2:
            player2_name = st.selectbox(
                "Select Player 2:",
                [f"{p.name} ({p.position})" for p in all_players[:50]],
                key="player2"
            )
        
        if player1_name and player2_name:
            # Find selected players
            player1 = next(p for p in all_players if f"{p.name} ({p.position})" == player1_name)
            player2 = next(p for p in all_players if f"{p.name} ({p.position})" == player2_name)
            
            # Compare players
            st.subheader("Comparison Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"### {player1.name}")
                st.markdown(f"**Position:** {player1.position}")
                st.markdown(f"**Role:** {player1.role}")
                st.markdown(f"**Overall Rating:** {player1.overall_rating:.1f}")
                st.markdown(f"**Offensive Rating:** {player1.offensive_rating:.1f}")
                st.markdown(f"**Defensive Rating:** {player1.defensive_rating:.1f}")
                
                fit1 = self.mapper.generate_fit_explanation(player1, self.selected_team)
                st.markdown(f"**Fit:** {fit1}")
            
            with col2:
                st.markdown(f"### {player2.name}")
                st.markdown(f"**Position:** {player2.position}")
                st.markdown(f"**Role:** {player2.role}")
                st.markdown(f"**Overall Rating:** {player2.overall_rating:.1f}")
                st.markdown(f"**Offensive Rating:** {player2.offensive_rating:.1f}")
                st.markdown(f"**Defensive Rating:** {player2.defensive_rating:.1f}")
                
                fit2 = self.mapper.generate_fit_explanation(player2, self.selected_team)
                st.markdown(f"**Fit:** {fit2}")
    
    def run(self):
        """Run the main dashboard."""
        if not self.initialize():
            return
        
        self.render_header()
        
        # Get selected page from sidebar
        page = self.render_sidebar()
        
        # Render selected page
        if page == "Team Roster":
            self.render_team_roster()
        elif page == "Player Search":
            self.render_player_search()
        elif page == "Free Agents":
            self.render_free_agents()
        elif page == "Fit Analysis":
            self.render_fit_analysis()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 0.9rem;">
            <p>NBA Lineup Optimizer - Fan Edition | Powered by Advanced Analytics</p>
        </div>
        """, unsafe_allow_html=True)

def main():
    """Main function to run the dashboard."""
    dashboard = FanFriendlyDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()
