"""
Model Interrogation Tool

This is the interactive tool for exploring and validating the possession-level modeling system.
It's designed for interrogation, not presentation - allowing analysts to ask "why" questions
and explore the model's reasoning in real-time.

Based on the pre-mortem insight: we need to build an interrogation tool, not a demonstration tool.
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Page config
st.set_page_config(
    page_title="NBA Lineup Model Interrogation Tool",
    page_icon="🏀",
    layout="wide"
)

class ModelInterrogator:
    """Core class for interrogating the possession-level model."""
    
    def __init__(self, db_path: str = "src/nba_stats/db/nba_stats.db"):
        """Initialize the model interrogator."""
        self.db_path = db_path
        self.conn = None
        self.player_data = None
        self.archetype_data = None
        self.possession_data = None
        
    def connect_database(self):
        """Connect to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            return True
        except Exception as e:
            st.error(f"Database connection failed: {e}")
            return False
    
    def load_player_data(self):
        """Load player data with archetypes and skills."""
        if not self.conn:
            return False
            
        try:
            # Load players with archetypes and skills
            query = """
            SELECT 
                p.player_id,
                p.player_name,
                pa.archetype_id,
                a.archetype_name,
                ps.offensive_darko,
                ps.defensive_darko,
                ps.darko,
                ps.offensive_epm,
                ps.defensive_epm,
                ps.epm
            FROM Players p
            LEFT JOIN PlayerSeasonArchetypes pa ON p.player_id = pa.player_id AND pa.season = '2024-25'
            LEFT JOIN Archetypes a ON pa.archetype_id = a.archetype_id
            LEFT JOIN PlayerSeasonSkill ps ON p.player_id = ps.player_id AND ps.season = '2024-25'
            WHERE pa.archetype_id IS NOT NULL AND ps.offensive_darko IS NOT NULL
            ORDER BY ps.darko DESC
            """
            
            self.player_data = pd.read_sql_query(query, self.conn)
            return True
            
        except Exception as e:
            st.error(f"Failed to load player data: {e}")
            return False
    
    def load_archetype_data(self):
        """Load archetype definitions."""
        if not self.conn:
            return False
            
        try:
            query = "SELECT * FROM Archetypes ORDER BY archetype_id"
            self.archetype_data = pd.read_sql_query(query, self.conn)
            return True
        except Exception as e:
            st.error(f"Failed to load archetype data: {e}")
            return False
    
    def load_possession_sample(self, n_samples: int = 1000):
        """Load a sample of possession data for analysis."""
        if not self.conn:
            return False
            
        try:
            query = f"""
            SELECT 
                p.*,
                g.game_date,
                g.home_team_id,
                g.away_team_id
            FROM Possessions p
            JOIN Games g ON p.game_id = g.game_id
            WHERE p.home_player_1_id IS NOT NULL 
              AND p.home_player_2_id IS NOT NULL 
              AND p.home_player_3_id IS NOT NULL 
              AND p.home_player_4_id IS NOT NULL 
              AND p.home_player_5_id IS NOT NULL 
              AND p.away_player_1_id IS NOT NULL 
              AND p.away_player_2_id IS NOT NULL 
              AND p.away_player_3_id IS NOT NULL 
              AND p.away_player_4_id IS NOT NULL 
              AND p.away_player_5_id IS NOT NULL
            ORDER BY RANDOM()
            LIMIT {n_samples}
            """
            
            self.possession_data = pd.read_sql_query(query, self.conn)
            return True
            
        except Exception as e:
            st.error(f"Failed to load possession data: {e}")
            return False
    
    def get_player_by_name(self, name: str) -> Optional[pd.Series]:
        """Get player data by name (fuzzy matching)."""
        if self.player_data is None:
            return None
            
        # Try exact match first
        exact_match = self.player_data[self.player_data['player_name'].str.lower() == name.lower()]
        if not exact_match.empty:
            return exact_match.iloc[0]
        
        # Try partial match
        partial_match = self.player_data[self.player_data['player_name'].str.contains(name, case=False, na=False)]
        if not partial_match.empty:
            return partial_match.iloc[0]
        
        return None
    
    def get_archetype_players(self, archetype_id: int) -> pd.DataFrame:
        """Get all players of a specific archetype."""
        if self.player_data is None:
            return pd.DataFrame()
            
        return self.player_data[self.player_data['archetype_id'] == archetype_id].copy()
    
    def load_model_coefficients(self) -> bool:
        """Load the trained model coefficients."""
        try:
            # Load archetype coefficients
            if Path("model_coefficients.csv").exists():
                self.archetype_coefficients = pd.read_csv("model_coefficients.csv")
            else:
                st.warning("Model coefficients not found. Using placeholder values.")
                return False
            
            # Load supercluster coefficients
            if Path("supercluster_coefficients.csv").exists():
                self.supercluster_coefficients = pd.read_csv("supercluster_coefficients.csv")
            else:
                st.warning("Supercluster coefficients not found. Using placeholder values.")
                return False
            
            return True
        except Exception as e:
            st.error(f"Failed to load model coefficients: {e}")
            return False
    
    def calculate_lineup_value(self, player_ids: List[int], context: str = "offense") -> Dict[str, Any]:
        """
        Calculate the value of a lineup using the trained model.
        """
        if self.player_data is None:
            return {"error": "Player data not loaded"}
        
        # Get player data for the lineup
        lineup_players = self.player_data[self.player_data['player_id'].isin(player_ids)]
        
        if len(lineup_players) != len(player_ids):
            return {"error": "Some players not found in database"}
        
        # Calculate skill-based value
        total_offensive_skill = lineup_players['offensive_darko'].sum()
        total_defensive_skill = lineup_players['defensive_darko'].sum()
        
        # Use trained model coefficients if available
        if hasattr(self, 'archetype_coefficients') and self.archetype_coefficients is not None:
            # Calculate archetype-weighted skill values
            archetype_skill_value = 0
            archetype_counts = lineup_players['archetype_id'].value_counts()
            
            for arch_id, count in archetype_counts.items():
                arch_coef = self.archetype_coefficients[
                    self.archetype_coefficients['archetype_id'] == arch_id
                ]
                
                if not arch_coef.empty:
                    # Get total skill for this archetype
                    arch_players = lineup_players[lineup_players['archetype_id'] == arch_id]
                    arch_offensive_skill = arch_players['offensive_darko'].sum()
                    arch_defensive_skill = arch_players['defensive_darko'].sum()
                    
                    # Apply coefficients
                    arch_value = (
                        arch_offensive_skill * arch_coef['beta_offensive'].iloc[0] +
                        arch_defensive_skill * arch_coef['beta_defensive'].iloc[0]
                    )
                    archetype_skill_value += arch_value
            
            final_value = archetype_skill_value
        else:
            # Fallback to simple heuristic
            base_value = total_offensive_skill * 0.1 - total_defensive_skill * 0.1
            
            # Add archetype diversity penalty
            archetype_counts = lineup_players['archetype_id'].value_counts()
            diversity_penalty = 0
            for arch_id, count in archetype_counts.items():
                if count > 1:
                    diversity_penalty += (count - 1) * 0.05
            
            final_value = base_value - diversity_penalty
        
        return {
            "total_value": final_value,
            "offensive_skill": total_offensive_skill,
            "defensive_skill": total_defensive_skill,
            "archetype_diversity": len(archetype_counts),
            "breakdown": {
                "skill_value": final_value,
                "archetype_breakdown": archetype_counts.to_dict()
            }
        }


def main():
    """Main Streamlit application."""
    st.title("🏀 NBA Lineup Model Interrogation Tool")
    st.markdown("**Interactive tool for exploring and validating the possession-level modeling system**")
    
    # Initialize the interrogator
    interrogator = ModelInterrogator()
    
    # Connect to database
    if not interrogator.connect_database():
        st.stop()
    
    # Load data
    with st.spinner("Loading data..."):
        if not interrogator.load_player_data():
            st.stop()
        if not interrogator.load_archetype_data():
            st.stop()
        if not interrogator.load_possession_sample(1000):
            st.stop()
        if not interrogator.load_model_coefficients():
            st.warning("⚠️ Model coefficients not found. Using placeholder calculations.")
    
    st.success("✅ Data loaded successfully!")
    
    # Model coefficient selection
    st.sidebar.markdown("---")
    st.sidebar.subheader("Model Configuration")
    
    # Find available coefficient files
    coefficient_files = ["model_coefficients.csv"] + [str(f) for f in Path(".").glob("model_coefficients_*.csv")]
    
    selected_coefficients = st.sidebar.selectbox(
        "Model Coefficients",
        coefficient_files,
        index=0
    )
    
    if st.sidebar.button("Reload Model"):
        with st.spinner("Reloading model coefficients..."):
            if interrogator.load_model_coefficients(selected_coefficients):
                st.sidebar.success("✅ Model reloaded!")
                st.rerun()
            else:
                st.sidebar.error("❌ Failed to reload model")
    
    # Create sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose Analysis Mode",
        ["Data Overview", "Player Explorer", "Archetype Analysis", "Lineup Builder", "Player Acquisition", "Model Validation"]
    )
    
    if page == "Data Overview":
        show_data_overview(interrogator)
    elif page == "Player Explorer":
        show_player_explorer(interrogator)
    elif page == "Archetype Analysis":
        show_archetype_analysis(interrogator)
    elif page == "Lineup Builder":
        show_lineup_builder(interrogator)
    elif page == "Player Acquisition":
        show_player_acquisition(interrogator)
    elif page == "Model Validation":
        show_model_validation(interrogator)


def show_data_overview(interrogator: ModelInterrogator):
    """Show data overview and statistics."""
    st.header("📊 Data Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Players", len(interrogator.player_data))
        st.metric("Players with Archetypes", len(interrogator.player_data[interrogator.player_data['archetype_id'].notna()]))
    
    with col2:
        st.metric("Players with Skills", len(interrogator.player_data[interrogator.player_data['offensive_darko'].notna()]))
        st.metric("Possession Samples", len(interrogator.possession_data))
    
    with col3:
        st.metric("Archetypes", len(interrogator.archetype_data))
        st.metric("Data Completeness", f"{len(interrogator.player_data[interrogator.player_data['archetype_id'].notna()]) / len(interrogator.player_data) * 100:.1f}%")
    
    # Show archetype distribution
    st.subheader("Archetype Distribution")
    archetype_counts = interrogator.player_data['archetype_name'].value_counts()
    
    fig = px.bar(
        x=archetype_counts.index,
        y=archetype_counts.values,
        title="Players by Archetype",
        labels={'x': 'Archetype', 'y': 'Number of Players'}
    )
    fig.update_xaxis(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Show skill distribution
    st.subheader("Skill Distribution")
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.histogram(
            interrogator.player_data,
            x='offensive_darko',
            title="Offensive DARKO Distribution",
            nbins=30
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.histogram(
            interrogator.player_data,
            x='defensive_darko',
            title="Defensive DARKO Distribution",
            nbins=30
        )
        st.plotly_chart(fig, use_container_width=True)


def show_player_explorer(interrogator: ModelInterrogator):
    """Show player exploration interface."""
    st.header("🔍 Player Explorer")
    
    # Player search
    search_term = st.text_input("Search for a player:", placeholder="Enter player name...")
    
    if search_term:
        player = interrogator.get_player_by_name(search_term)
        if player is not None:
            st.success(f"Found: {player['player_name']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Archetype", player['archetype_name'])
            with col2:
                st.metric("Offensive DARKO", f"{player['offensive_darko']:.2f}")
            with col3:
                st.metric("Defensive DARKO", f"{player['defensive_darko']:.2f}")
        else:
            st.warning("Player not found. Try a different search term.")
    
    # Top players by skill
    st.subheader("Top Players by Skill")
    
    skill_type = st.selectbox("Skill Type", ["darko", "offensive_darko", "defensive_darko", "epm"])
    n_players = st.slider("Number of players to show", 5, 50, 20)
    
    top_players = interrogator.player_data.nlargest(n_players, skill_type)
    
    st.dataframe(
        top_players[['player_name', 'archetype_name', 'offensive_darko', 'defensive_darko', 'darko']],
        use_container_width=True
    )


def show_archetype_analysis(interrogator: ModelInterrogator):
    """Show archetype analysis."""
    st.header("🎭 Archetype Analysis")
    
    # Select archetype
    archetype_name = st.selectbox(
        "Select Archetype",
        interrogator.archetype_data['archetype_name'].tolist()
    )
    
    archetype_id = interrogator.archetype_data[
        interrogator.archetype_data['archetype_name'] == archetype_name
    ]['archetype_id'].iloc[0]
    
    # Get players of this archetype
    archetype_players = interrogator.get_archetype_players(archetype_id)
    
    st.subheader(f"Players in {archetype_name} Archetype")
    st.write(f"Total players: {len(archetype_players)}")
    
    if len(archetype_players) > 0:
        # Show skill statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Avg Offensive DARKO", f"{archetype_players['offensive_darko'].mean():.2f}")
        with col2:
            st.metric("Avg Defensive DARKO", f"{archetype_players['defensive_darko'].mean():.2f}")
        with col3:
            st.metric("Avg Overall DARKO", f"{archetype_players['darko'].mean():.2f}")
        
        # Show skill distribution
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Offensive DARKO", "Defensive DARKO")
        )
        
        fig.add_trace(
            go.Histogram(x=archetype_players['offensive_darko'], name="Offensive"),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Histogram(x=archetype_players['defensive_darko'], name="Defensive"),
            row=1, col=2
        )
        
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Show top players in this archetype
        st.subheader("Top Players in This Archetype")
        top_archetype_players = archetype_players.nlargest(10, 'darko')
        st.dataframe(
            top_archetype_players[['player_name', 'offensive_darko', 'defensive_darko', 'darko']],
            use_container_width=True
        )


def show_lineup_builder(interrogator: ModelInterrogator):
    """Show lineup builder interface."""
    st.header("🏗️ Lineup Builder")
    
    st.markdown("**Build and analyze lineups to test the model's logic**")
    
    # Player selection
    st.subheader("Select Players")
    
    # Get all players with both archetype and skill data
    available_players = interrogator.player_data[
        interrogator.player_data['archetype_id'].notna() & 
        interrogator.player_data['offensive_darko'].notna()
    ].copy()
    
    selected_players = []
    
    for i in range(5):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            player_name = st.selectbox(
                f"Player {i+1}",
                [""] + available_players['player_name'].tolist(),
                key=f"player_{i+1}"
            )
        
        with col2:
            if player_name:
                player = available_players[available_players['player_name'] == player_name].iloc[0]
                selected_players.append(player['player_id'])
                st.write(f"**{player['archetype_name']}**")
                st.write(f"O: {player['offensive_darko']:.1f}")
                st.write(f"D: {player['defensive_darko']:.1f}")
            else:
                selected_players.append(None)
    
    # Analyze lineup
    if all(p is not None for p in selected_players):
        st.subheader("Lineup Analysis")
        
        # Calculate lineup value (placeholder)
        lineup_value = interrogator.calculate_lineup_value(selected_players)
        
        if "error" in lineup_value:
            st.error(lineup_value["error"])
        else:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Value", f"{lineup_value['total_value']:.3f}")
            with col2:
                st.metric("Offensive Skill", f"{lineup_value['offensive_skill']:.1f}")
            with col3:
                st.metric("Defensive Skill", f"{lineup_value['defensive_skill']:.1f}")
            with col4:
                st.metric("Archetype Diversity", lineup_value['archetype_diversity'])
            
            # Show breakdown
            st.subheader("Value Breakdown")
            breakdown = lineup_value['breakdown']
            
            fig = go.Figure(data=[
                go.Bar(name='Base Value', x=['Value'], y=[breakdown['base_value']]),
                go.Bar(name='Diversity Penalty', x=['Value'], y=[-breakdown['diversity_penalty']])
            ])
            
            fig.update_layout(
                title="Lineup Value Components",
                barmode='relative',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)


def show_player_acquisition(interrogator: ModelInterrogator):
    """Show player acquisition interface."""
    st.header("🎯 Player Acquisition Tool")
    
    st.markdown("**Find the best 5th player for your 4-player core lineup**")
    st.markdown("Based on the research paper methodology: given four solidified starters, which fifth player should we add to maximize lineup effectiveness?")
    
    # Core lineup selection
    st.subheader("Select Your Core 4 Players")
    
    # Get all players with both archetype and skill data
    available_players = interrogator.player_data[
        interrogator.player_data['archetype_id'].notna() & 
        interrogator.player_data['offensive_darko'].notna()
    ].copy()
    
    selected_core_players = []
    
    for i in range(4):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            player_name = st.selectbox(
                f"Core Player {i+1}",
                [""] + available_players['player_name'].tolist(),
                key=f"core_player_{i+1}"
            )
        
        with col2:
            if player_name:
                player = available_players[available_players['player_name'] == player_name].iloc[0]
                selected_core_players.append(player['player_id'])
                st.write(f"**{player['archetype_name']}**")
                st.write(f"O: {player['offensive_darko']:.1f}")
                st.write(f"D: {player['defensive_darko']:.1f}")
            else:
                selected_core_players.append(None)
    
    # Analyze core lineup
    if all(p is not None for p in selected_core_players):
        st.subheader("Core Lineup Analysis")
        
        # Calculate core lineup value
        core_value = interrogator.calculate_lineup_value(selected_core_players)
        
        if "error" in core_value:
            st.error(core_value["error"])
        else:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Core Value", f"{core_value['total_value']:.3f}")
            with col2:
                st.metric("Offensive Skill", f"{core_value['offensive_skill']:.1f}")
            with col3:
                st.metric("Defensive Skill", f"{core_value['defensive_skill']:.1f}")
            with col4:
                st.metric("Archetype Diversity", core_value['archetype_diversity'])
            
            # Show archetype breakdown
            st.write("**Archetype Distribution:**")
            archetype_counts = interrogator.player_data[
                interrogator.player_data['player_id'].isin(selected_core_players)
            ]['archetype_name'].value_counts()
            
            for arch, count in archetype_counts.items():
                st.write(f"- {arch}: {count}")
            
            # Find best 5th player
            st.subheader("Find Best 5th Player")
            
            # Acquisition parameters
            col1, col2 = st.columns(2)
            
            with col1:
                max_salary = st.number_input(
                    "Maximum Salary (Million $)", 
                    min_value=0.0, 
                    max_value=50.0, 
                    value=25.0,
                    step=1.0
                ) * 1_000_000
            
            with col2:
                n_recommendations = st.slider("Number of recommendations", 5, 20, 10)
            
            if st.button("Find Best 5th Player", type="primary"):
                with st.spinner("Analyzing all available players..."):
                    # Import the acquisition tool
                    from player_acquisition_tool import PlayerAcquisitionTool
                    
                    # Initialize acquisition tool
                    acquisition_tool = PlayerAcquisitionTool()
                    acquisition_tool.conn = interrogator.conn
                    acquisition_tool.player_data = interrogator.player_data
                    acquisition_tool.archetype_data = interrogator.archetype_data
                    
                    # Load model coefficients if available
                    if hasattr(interrogator, 'archetype_coefficients') and interrogator.archetype_coefficients is not None:
                        acquisition_tool.model_coefficients = interrogator.archetype_coefficients
                    
                    # Find recommendations
                    recommendations = acquisition_tool.find_best_fifth_player(
                        selected_core_players, 
                        max_salary=max_salary
                    )
                    
                    if recommendations and "error" not in recommendations[0]:
                        st.success(f"✅ Found {len(recommendations)} recommendations!")
                        
                        # Display top recommendations
                        st.subheader(f"Top {min(n_recommendations, len(recommendations))} Recommendations")
                        
                        for i, rec in enumerate(recommendations[:n_recommendations], 1):
                            with st.expander(f"{i}. {rec['player_name']} ({rec['archetype_name']}) - Marginal Value: {rec['marginal_value']:.3f}"):
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric("Marginal Value", f"{rec['marginal_value']:.3f}")
                                    st.metric("Lineup Value", f"{rec['lineup_value']:.3f}")
                                
                                with col2:
                                    st.metric("Overall DARKO", f"{rec['overall_darko']:.2f}")
                                    st.metric("Archetype Diversity", rec['archetype_diversity'])
                                
                                with col3:
                                    st.metric("Offensive DARKO", f"{rec['offensive_darko']:.2f}")
                                    st.metric("Defensive DARKO", f"{rec['defensive_darko']:.2f}")
                                
                                # Show reasoning
                                st.write("**Why this player?**")
                                st.write(f"- Adds {rec['marginal_value']:.3f} points to the lineup")
                                st.write(f"- Brings {rec['archetype_name']} archetype to the team")
                                st.write(f"- High overall skill rating: {rec['overall_darko']:.2f}")
                        
                        # Summary statistics
                        st.subheader("Recommendation Summary")
                        
                        rec_df = pd.DataFrame(recommendations[:n_recommendations])
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Archetype Distribution:**")
                            arch_counts = rec_df['archetype_name'].value_counts()
                            for arch, count in arch_counts.items():
                                st.write(f"- {arch}: {count}")
                        
                        with col2:
                            st.write("**Skill Statistics:**")
                            st.write(f"- Avg Marginal Value: {rec_df['marginal_value'].mean():.3f}")
                            st.write(f"- Avg Overall DARKO: {rec_df['overall_darko'].mean():.2f}")
                            st.write(f"- Avg Archetype Diversity: {rec_df['archetype_diversity'].mean():.1f}")
                        
                        # Create visualization
                        fig = px.scatter(
                            rec_df.head(10),
                            x='marginal_value',
                            y='overall_darko',
                            color='archetype_name',
                            hover_data=['player_name', 'offensive_darko', 'defensive_darko'],
                            title="Top 10 Recommendations: Marginal Value vs Overall Skill"
                        )
                        fig.update_layout(height=500)
                        st.plotly_chart(fig, use_container_width=True)
                        
                    else:
                        st.error("❌ No recommendations found")
                        if recommendations and "error" in recommendations[0]:
                            st.error(f"Error: {recommendations[0]['error']}")
    else:
        st.warning("⚠️ Please select all 4 core players to begin analysis")


def show_model_validation(interrogator: ModelInterrogator):
    """Show model validation interface."""
    st.header("✅ Model Validation")
    
    st.markdown("**Test the model's basketball logic and validate its reasoning**")
    
    # Basketball logic tests
    st.subheader("Basketball Logic Tests")
    
    # Test 1: High skill players should be valued higher
    st.write("**Test 1: Skill Impact**")
    st.write("Do high-skill players contribute more to lineup value?")
    
    if st.button("Run Skill Impact Test"):
        # Get top and bottom skill players
        top_players = interrogator.player_data.nlargest(5, 'darko')
        bottom_players = interrogator.player_data.nsmallest(5, 'darko')
        
        # Create lineups with these players
        top_lineup = top_players['player_id'].tolist()
        bottom_lineup = bottom_players['player_id'].tolist()
        
        top_value = interrogator.calculate_lineup_value(top_lineup)
        bottom_value = interrogator.calculate_lineup_value(bottom_lineup)
        
        if "error" not in top_value and "error" not in bottom_value:
            st.write(f"Top skill lineup value: {top_value['total_value']:.3f}")
            st.write(f"Bottom skill lineup value: {bottom_value['total_value']:.3f}")
            
            if top_value['total_value'] > bottom_value['total_value']:
                st.success("✅ Test PASSED: High skill players create better lineups")
            else:
                st.error("❌ Test FAILED: Model doesn't properly value skill")
        else:
            st.error("Error calculating lineup values")
    
    # Test 2: Archetype diversity
    st.write("**Test 2: Archetype Diversity**")
    st.write("Do diverse lineups perform better than homogeneous ones?")
    
    if st.button("Run Diversity Test"):
        # Create a diverse lineup (different archetypes)
        diverse_players = []
        for archetype_id in range(1, 6):  # First 5 archetypes
            arch_players = interrogator.get_archetype_players(archetype_id)
            if not arch_players.empty:
                diverse_players.append(arch_players.iloc[0]['player_id'])
        
        # Create a homogeneous lineup (same archetype)
        if not interrogator.player_data.empty:
            same_arch = interrogator.player_data['archetype_id'].iloc[0]
            homog_players = interrogator.get_archetype_players(same_arch)
            if len(homog_players) >= 5:
                homog_lineup = homog_players.head(5)['player_id'].tolist()
            else:
                homog_lineup = []
        
        if len(diverse_players) == 5 and len(homog_lineup) == 5:
            diverse_value = interrogator.calculate_lineup_value(diverse_players)
            homog_value = interrogator.calculate_lineup_value(homog_lineup)
            
            if "error" not in diverse_value and "error" not in homog_value:
                st.write(f"Diverse lineup value: {diverse_value['total_value']:.3f}")
                st.write(f"Homogeneous lineup value: {homog_value['total_value']:.3f}")
                
                if diverse_value['total_value'] > homog_value['total_value']:
                    st.success("✅ Test PASSED: Diverse lineups perform better")
                else:
                    st.warning("⚠️ Test INCONCLUSIVE: Diversity may not always be better")
            else:
                st.error("Error calculating lineup values")
        else:
            st.error("Not enough players to create test lineups")


if __name__ == "__main__":
    main()
