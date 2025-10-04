"""
Model Comparison Dashboard

This dashboard provides side-by-side comparison between the original ModelEvaluator
and the new SimpleModelEvaluator to validate the production model integration.

Key Features:
1. Side-by-side lineup evaluation comparison
2. Coefficient comparison visualization
3. Performance metrics comparison
4. Litmus test scenarios validation
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Tuple, Any, Optional
import sys
from pathlib import Path
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nba_stats.model_evaluator import ModelEvaluator
from nba_stats.simple_model_evaluator import SimpleModelEvaluator

# Page config
st.set_page_config(
    page_title="NBA Model Comparison Dashboard",
    page_icon="⚖️",
    layout="wide"
)

class ModelComparisonDashboard:
    """Dashboard for comparing original and simplified model evaluators."""
    
    def __init__(self):
        """Initialize the comparison dashboard."""
        self.original_evaluator = None
        self.simple_evaluator = None
        self.comparison_results = {}
        
    def initialize_evaluators(self):
        """Initialize both model evaluators."""
        try:
            with st.spinner("Initializing model evaluators..."):
                self.original_evaluator = ModelEvaluator()
                self.simple_evaluator = SimpleModelEvaluator()
            return True
        except Exception as e:
            st.error(f"Failed to initialize evaluators: {e}")
            return False
    
    def compare_lineup_evaluation(self, player_ids: List[int]) -> Dict[str, Any]:
        """Compare lineup evaluation between both models."""
        if not self.original_evaluator or not self.simple_evaluator:
            return {"error": "Evaluators not initialized"}
        
        try:
            # Evaluate with original model
            original_result = self.original_evaluator.evaluate_lineup(player_ids)
            
            # Evaluate with simple model
            simple_result = self.simple_evaluator.evaluate_lineup(player_ids)
            
            return {
                "original": {
                    "predicted_outcome": original_result.predicted_outcome,
                    "player_names": original_result.player_names,
                    "archetype_names": original_result.archetype_names,
                    "skill_scores": original_result.skill_scores
                },
                "simple": {
                    "predicted_outcome": simple_result.predicted_outcome,
                    "player_names": simple_result.player_names,
                    "archetype_names": simple_result.archetype_names,
                    "skill_scores": simple_result.skill_scores,
                    "model_type": simple_result.model_type
                },
                "difference": simple_result.predicted_outcome - original_result.predicted_outcome,
                "relative_difference": (simple_result.predicted_outcome - original_result.predicted_outcome) / abs(original_result.predicted_outcome) * 100 if original_result.predicted_outcome != 0 else 0
            }
        except Exception as e:
            return {"error": str(e)}
    
    def compare_coefficients(self) -> Dict[str, Any]:
        """Compare model coefficients between both models."""
        if not self.original_evaluator or not self.simple_evaluator:
            return {"error": "Evaluators not initialized"}
        
        # Get original model coefficients (placeholder)
        original_coeffs = self.original_evaluator._model_coefficients
        
        # Get simple model coefficients
        simple_coeffs_df = self.simple_evaluator.get_model_coefficients_for_ui()
        
        return {
            "original": original_coeffs,
            "simple": simple_coeffs_df.to_dict('records'),
            "simple_df": simple_coeffs_df
        }
    
    def run_performance_comparison(self, num_lineups: int = 100) -> Dict[str, Any]:
        """Run performance comparison on random lineups."""
        if not self.original_evaluator or not self.simple_evaluator:
            return {"error": "Evaluators not initialized"}
        
        # Get available players
        original_players = self.original_evaluator.get_available_players()
        simple_players = self.simple_evaluator.get_available_players()
        
        # Find common players
        common_player_ids = set(p.player_id for p in original_players) & set(p.player_id for p in simple_players)
        common_player_ids = list(common_player_ids)
        
        if len(common_player_ids) < 5:
            return {"error": "Not enough common players for comparison"}
        
        # Generate random lineups
        np.random.seed(42)  # For reproducibility
        results = []
        
        for i in range(num_lineups):
            # Sample 5 random players
            lineup_ids = np.random.choice(common_player_ids, 5, replace=False).tolist()
            
            # Compare evaluation
            comparison = self.compare_lineup_evaluation(lineup_ids)
            
            if "error" not in comparison:
                results.append({
                    "lineup_id": i,
                    "original_prediction": comparison["original"]["predicted_outcome"],
                    "simple_prediction": comparison["simple"]["predicted_outcome"],
                    "difference": comparison["difference"],
                    "relative_difference": comparison["relative_difference"]
                })
        
        if not results:
            return {"error": "No valid comparisons generated"}
        
        results_df = pd.DataFrame(results)
        
        return {
            "results_df": results_df,
            "summary_stats": {
                "mean_difference": results_df["difference"].mean(),
                "std_difference": results_df["difference"].std(),
                "mean_relative_difference": results_df["relative_difference"].mean(),
                "correlation": results_df["original_prediction"].corr(results_df["simple_prediction"]),
                "max_difference": results_df["difference"].max(),
                "min_difference": results_df["difference"].min()
            }
        }
    
    def get_litmus_test_scenarios(self) -> Dict[str, List[int]]:
        """Get litmus test scenarios for validation."""
        if not self.original_evaluator or not self.simple_evaluator:
            return {}
        
        # Get common players
        original_players = self.original_evaluator.get_available_players()
        simple_players = self.simple_evaluator.get_available_players()
        common_player_ids = set(p.player_id for p in original_players) & set(p.player_id for p in simple_players)
        
        # Create scenarios with common players
        scenarios = {}
        
        # High-skill lineup
        high_skill_players = [p for p in original_players if p.darko > 2.0][:5]
        if len(high_skill_players) >= 5:
            scenarios["High-Skill Lineup"] = [p.player_id for p in high_skill_players[:5]]
        
        # Balanced lineup (one from each archetype)
        archetype_players = {}
        for p in original_players:
            if p.player_id in common_player_ids:
                if p.archetype_id not in archetype_players:
                    archetype_players[p.archetype_id] = p
                elif p.darko > archetype_players[p.archetype_id].darko:
                    archetype_players[p.archetype_id] = p
        
        if len(archetype_players) >= 3:
            balanced_lineup = list(archetype_players.values())[:3]
            # Add 2 more random players
            remaining_players = [p for p in original_players if p.player_id not in [bp.player_id for bp in balanced_lineup] and p.player_id in common_player_ids]
            if len(remaining_players) >= 2:
                balanced_lineup.extend(remaining_players[:2])
                scenarios["Balanced Lineup"] = [p.player_id for p in balanced_lineup]
        
        # Low-skill lineup
        low_skill_players = [p for p in original_players if p.darko < 0.0][:5]
        if len(low_skill_players) >= 5:
            scenarios["Low-Skill Lineup"] = [p.player_id for p in low_skill_players[:5]]
        
        return scenarios


def show_comparison_overview(dashboard: ModelComparisonDashboard):
    """Show the main comparison overview."""
    st.header("📊 Model Comparison Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Original Model")
        if dashboard.original_evaluator:
            stats = dashboard.original_evaluator.get_stats_summary()
            st.metric("Total Players", stats['total_players'])
            st.metric("Season", stats['season'])
            st.metric("Model Type", "Placeholder (8 archetypes)")
        else:
            st.error("Not initialized")
    
    with col2:
        st.subheader("Simple Model")
        if dashboard.simple_evaluator:
            stats = dashboard.simple_evaluator.get_stats_summary()
            st.metric("Total Players", stats['total_players'])
            st.metric("Season", stats['season'])
            st.metric("Model Type", stats['model_type'])
        else:
            st.error("Not initialized")


def show_coefficient_comparison(dashboard: ModelComparisonDashboard):
    """Show coefficient comparison."""
    st.header("🔢 Coefficient Comparison")
    
    comparison = dashboard.compare_coefficients()
    
    if "error" in comparison:
        st.error(f"Error comparing coefficients: {comparison['error']}")
        return
    
    # Show simple model coefficients
    st.subheader("Simple Model Coefficients")
    simple_df = comparison["simple_df"]
    st.dataframe(simple_df, use_container_width=True)
    
    # Create coefficient visualization
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Offensive Coefficients', 'Defensive Coefficients'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Offensive coefficients
    fig.add_trace(
        go.Bar(
            x=simple_df['archetype_name'],
            y=simple_df['beta_offensive'],
            name='Offensive',
            marker_color='blue'
        ),
        row=1, col=1
    )
    
    # Defensive coefficients
    fig.add_trace(
        go.Bar(
            x=simple_df['archetype_name'],
            y=simple_df['beta_defensive'],
            name='Defensive',
            marker_color='red'
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        title="Model Coefficients Comparison",
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def show_lineup_comparison(dashboard: ModelComparisonDashboard):
    """Show lineup comparison interface."""
    st.header("🏀 Lineup Comparison")
    
    # Player selection
    if dashboard.original_evaluator and dashboard.simple_evaluator:
        original_players = dashboard.original_evaluator.get_available_players()
        simple_players = dashboard.simple_evaluator.get_available_players()
        
        # Find common players
        common_players = []
        for op in original_players:
            for sp in simple_players:
                if op.player_id == sp.player_id:
                    common_players.append({
                        'player_id': op.player_id,
                        'player_name': op.player_name,
                        'archetype_name': op.archetype_name,
                        'darko': op.darko
                    })
                    break
        
        common_players_df = pd.DataFrame(common_players)
        
        if len(common_players_df) >= 5:
            st.subheader("Select Lineup")
            
            # Multi-select for 5 players
            selected_players = st.multiselect(
                "Choose 5 players:",
                options=common_players_df['player_name'].tolist(),
                default=common_players_df['player_name'].head(5).tolist(),
                max_selections=5
            )
            
            if len(selected_players) == 5:
                # Get player IDs
                lineup_ids = []
                for name in selected_players:
                    player_id = common_players_df[common_players_df['player_name'] == name]['player_id'].iloc[0]
                    lineup_ids.append(player_id)
                
                # Compare evaluation
                if st.button("Compare Lineup Evaluation"):
                    with st.spinner("Evaluating lineup..."):
                        comparison = dashboard.compare_lineup_evaluation(lineup_ids)
                    
                    if "error" not in comparison:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("Original Model")
                            st.metric(
                                "Predicted Outcome",
                                f"{comparison['original']['predicted_outcome']:.3f}"
                            )
                            st.write("**Players:**")
                            for name in comparison['original']['player_names']:
                                st.write(f"- {name}")
                        
                        with col2:
                            st.subheader("Simple Model")
                            st.metric(
                                "Predicted Outcome",
                                f"{comparison['simple']['predicted_outcome']:.3f}"
                            )
                            st.write("**Players:**")
                            for name in comparison['simple']['player_names']:
                                st.write(f"- {name}")
                        
                        # Show difference
                        st.subheader("Comparison")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric(
                                "Difference",
                                f"{comparison['difference']:.3f}",
                                delta=f"{comparison['relative_difference']:.1f}%"
                            )
                        
                        with col2:
                            st.metric(
                                "Original Model",
                                f"{comparison['original']['predicted_outcome']:.3f}"
                            )
                        
                        with col3:
                            st.metric(
                                "Simple Model",
                                f"{comparison['simple']['predicted_outcome']:.3f}"
                            )
                    else:
                        st.error(f"Error comparing lineup: {comparison['error']}")
            else:
                st.warning("Please select exactly 5 players")
        else:
            st.error("Not enough common players for comparison")
    else:
        st.error("Evaluators not initialized")


def show_performance_comparison(dashboard: ModelComparisonDashboard):
    """Show performance comparison results."""
    st.header("⚡ Performance Comparison")
    
    num_lineups = st.slider("Number of random lineups to test", 10, 500, 100)
    
    if st.button("Run Performance Comparison"):
        with st.spinner(f"Testing {num_lineups} random lineups..."):
            start_time = time.time()
            results = dashboard.run_performance_comparison(num_lineups)
            end_time = time.time()
        
        if "error" in results:
            st.error(f"Error running performance comparison: {results['error']}")
            return
        
        st.success(f"Performance comparison completed in {end_time - start_time:.2f} seconds")
        
        # Show summary statistics
        st.subheader("Summary Statistics")
        stats = results["summary_stats"]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Mean Difference", f"{stats['mean_difference']:.3f}")
            st.metric("Std Difference", f"{stats['std_difference']:.3f}")
        
        with col2:
            st.metric("Mean Relative Difference", f"{stats['mean_relative_difference']:.1f}%")
            st.metric("Correlation", f"{stats['correlation']:.3f}")
        
        with col3:
            st.metric("Max Difference", f"{stats['max_difference']:.3f}")
            st.metric("Min Difference", f"{stats['min_difference']:.3f}")
        
        # Show scatter plot
        st.subheader("Prediction Correlation")
        results_df = results["results_df"]
        
        fig = px.scatter(
            results_df,
            x="original_prediction",
            y="simple_prediction",
            title="Original vs Simple Model Predictions",
            labels={
                "original_prediction": "Original Model Prediction",
                "simple_prediction": "Simple Model Prediction"
            }
        )
        
        # Add diagonal line
        min_val = min(results_df["original_prediction"].min(), results_df["simple_prediction"].min())
        max_val = max(results_df["original_prediction"].max(), results_df["simple_prediction"].max())
        fig.add_trace(
            go.Scatter(
                x=[min_val, max_val],
                y=[min_val, max_val],
                mode='lines',
                name='Perfect Correlation',
                line=dict(dash='dash', color='red')
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show difference distribution
        st.subheader("Difference Distribution")
        fig = px.histogram(
            results_df,
            x="difference",
            title="Distribution of Prediction Differences",
            labels={"difference": "Prediction Difference (Simple - Original)"}
        )
        st.plotly_chart(fig, use_container_width=True)


def show_litmus_tests(dashboard: ModelComparisonDashboard):
    """Show litmus test scenarios."""
    st.header("🧪 Litmus Test Scenarios")
    
    scenarios = dashboard.get_litmus_test_scenarios()
    
    if not scenarios:
        st.error("No litmus test scenarios available")
        return
    
    scenario_name = st.selectbox("Select test scenario", list(scenarios.keys()))
    
    if st.button("Run Litmus Test"):
        lineup_ids = scenarios[scenario_name]
        
        with st.spinner("Running litmus test..."):
            comparison = dashboard.compare_lineup_evaluation(lineup_ids)
        
        if "error" not in comparison:
            st.subheader(f"Results for {scenario_name}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Original Model")
                st.metric(
                    "Predicted Outcome",
                    f"{comparison['original']['predicted_outcome']:.3f}"
                )
                st.write("**Players:**")
                for name in comparison['original']['player_names']:
                    st.write(f"- {name}")
            
            with col2:
                st.subheader("Simple Model")
                st.metric(
                    "Predicted Outcome",
                    f"{comparison['simple']['predicted_outcome']:.3f}"
                )
                st.write("**Players:**")
                for name in comparison['simple']['player_names']:
                    st.write(f"- {name}")
            
            # Show difference
            st.subheader("Comparison")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Difference",
                    f"{comparison['difference']:.3f}",
                    delta=f"{comparison['relative_difference']:.1f}%"
                )
            
            with col2:
                st.metric(
                    "Original Model",
                    f"{comparison['original']['predicted_outcome']:.3f}"
                )
            
            with col3:
                st.metric(
                    "Simple Model",
                    f"{comparison['simple']['predicted_outcome']:.3f}"
                )
        else:
            st.error(f"Error running litmus test: {comparison['error']}")


def main():
    """Main Streamlit application."""
    st.title("⚖️ NBA Model Comparison Dashboard")
    st.markdown("**Side-by-side comparison between original and simplified model evaluators**")
    
    # Initialize the dashboard
    dashboard = ModelComparisonDashboard()
    
    # Initialize evaluators
    if not dashboard.initialize_evaluators():
        st.stop()
    
    st.success("✅ Both model evaluators initialized successfully!")
    
    # Create sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose Analysis Mode",
        ["Overview", "Coefficient Comparison", "Lineup Comparison", "Performance Comparison", "Litmus Tests"]
    )
    
    if page == "Overview":
        show_comparison_overview(dashboard)
    elif page == "Coefficient Comparison":
        show_coefficient_comparison(dashboard)
    elif page == "Lineup Comparison":
        show_lineup_comparison(dashboard)
    elif page == "Performance Comparison":
        show_performance_comparison(dashboard)
    elif page == "Litmus Tests":
        show_litmus_tests(dashboard)


if __name__ == "__main__":
    main()
