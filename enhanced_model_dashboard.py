"""
Enhanced Model Dashboard

This dashboard provides an enhanced interface for using both the original
ModelEvaluator and the new SimpleModelEvaluator with model switching capabilities.

Key Features:
1. Model switching with fallback
2. Side-by-side comparison when needed
3. Unified interface for lineup evaluation
4. Performance monitoring
5. Error handling and recovery
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
import logging

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nba_stats.model_factory import ModelFactory, ModelType, NormalizedLineupEvaluation
from nba_stats.model_evaluator import ModelEvaluator
from nba_stats.simple_model_evaluator import SimpleModelEvaluator
from nba_stats.performance_optimizer import OptimizedModelFactory, get_performance_metrics, preload_models

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="NBA Enhanced Model Dashboard",
    page_icon="🏀",
    layout="wide"
)

class EnhancedModelDashboard:
    """Enhanced dashboard with model switching capabilities."""
    
    def __init__(self):
        """Initialize the enhanced dashboard."""
        self.original_evaluator = None
        self.simple_evaluator = None
        self.current_model = None
        self.performance_metrics = {
            "original": {"evaluations": 0, "total_time": 0, "errors": 0},
            "simple": {"evaluations": 0, "total_time": 0, "errors": 0}
        }
        
    def initialize_evaluators(self):
        """Initialize both model evaluators with performance optimization."""
        try:
            with st.spinner("Initializing model evaluators..."):
                # Use optimized factory with lazy loading
                preload_models()
                self.original_evaluator = OptimizedModelFactory.create_evaluator("original")
                self.simple_evaluator = OptimizedModelFactory.create_evaluator("simple")
            return True
        except Exception as e:
            st.error(f"Failed to initialize evaluators: {e}")
            logger.error(f"Evaluator initialization failed: {e}")
            return False
    
    def get_model_selector_ui(self):
        """Create the model selector UI in the sidebar."""
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎯 Model Selection")
        
        # Get available models
        available_models = ModelFactory.get_available_models()
        
        # Create model selection
        model_options = [f"{model['name']} ({model['status']})" for model in available_models]
        model_types = [model['type'] for model in available_models]
        
        selected_index = st.sidebar.selectbox(
            "Active Model",
            model_options,
            index=1,  # Default to production model
            help="Select which model to use for lineup evaluation"
        )
        
        selected_model_type = model_types[model_options.index(selected_index)]
        
        # Add comparison mode toggle
        comparison_mode = st.sidebar.checkbox(
            "Enable Comparison Mode",
            value=False,
            help="Show side-by-side comparison of both models"
        )
        
        # Add fallback toggle
        enable_fallback = st.sidebar.checkbox(
            "Enable Fallback",
            value=True,
            help="Automatically fallback to other model if primary fails"
        )
        
        return selected_model_type, comparison_mode, enable_fallback
    
    def evaluate_lineup_safe(self, lineup: List[int], model_type: str, enable_fallback: bool = True) -> Optional[NormalizedLineupEvaluation]:
        """Safely evaluate a lineup with error handling and performance tracking."""
        start_time = time.time()
        
        try:
            if enable_fallback:
                result = ModelFactory.evaluate_lineup_with_fallback(lineup, model_type)
            else:
                evaluator = ModelFactory.create_evaluator(model_type)
                raw_result = evaluator.evaluate_lineup(lineup)
                result = ModelFactory.normalize_result(raw_result)
            
            # Track performance
            elapsed_time = time.time() - start_time
            self.performance_metrics[result.model_type]["evaluations"] += 1
            self.performance_metrics[result.model_type]["total_time"] += elapsed_time
            
            return result
            
        except Exception as e:
            # Track errors
            self.performance_metrics[model_type]["errors"] += 1
            logger.error(f"Lineup evaluation failed with {model_type} model: {e}")
            st.error(f"Evaluation failed: {e}")
            return None
    
    def display_lineup_evaluation(self, result: NormalizedLineupEvaluation):
        """Display the results of a lineup evaluation."""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Predicted Outcome",
                f"{result.predicted_outcome:.4f}",
                help="Expected net points for this lineup"
            )
        
        with col2:
            st.metric(
                "Model Type",
                result.model_type.title(),
                help="Model used for this evaluation"
            )
        
        with col3:
            archetype_diversity = result.skill_scores.get('archetype_diversity', 0)
            st.metric(
                "Archetype Diversity",
                f"{archetype_diversity:.2f}",
                help="Diversity of player archetypes in lineup"
            )
        
        # Display player information
        st.subheader("👥 Lineup Details")
        
        player_data = []
        for i, (player_id, player_name, archetype_id, archetype_name) in enumerate(zip(
            result.player_ids, result.player_names, result.archetype_ids, result.archetype_names
        )):
            player_data.append({
                "Position": i + 1,
                "Player ID": player_id,
                "Player Name": player_name,
                "Archetype ID": archetype_id,
                "Archetype": archetype_name
            })
        
        df = pd.DataFrame(player_data)
        st.dataframe(df, use_container_width=True)
        
        # Display skill scores
        st.subheader("📊 Skill Analysis")
        
        skill_cols = st.columns(len(result.skill_scores))
        for i, (metric, value) in enumerate(result.skill_scores.items()):
            with skill_cols[i % len(skill_cols)]:
                st.metric(
                    metric.replace('_', ' ').title(),
                    f"{value:.4f}" if isinstance(value, (int, float)) else str(value)
                )
    
    def display_comparison(self, lineup: List[int]):
        """Display side-by-side comparison of both models."""
        st.subheader("⚖️ Model Comparison")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Original Model**")
            original_result = self.evaluate_lineup_safe(lineup, "original", enable_fallback=False)
            if original_result:
                self.display_lineup_evaluation(original_result)
        
        with col2:
            st.markdown("**Production Model**")
            simple_result = self.evaluate_lineup_safe(lineup, "simple", enable_fallback=False)
            if simple_result:
                self.display_lineup_evaluation(simple_result)
        
        # Show comparison metrics
        if original_result and simple_result:
            st.subheader("📈 Comparison Metrics")
            
            comparison_data = {
                "Metric": ["Predicted Outcome", "Model Type", "Archetype Count"],
                "Original Model": [
                    f"{original_result.predicted_outcome:.4f}",
                    original_result.model_type,
                    len(set(original_result.archetype_ids))
                ],
                "Production Model": [
                    f"{simple_result.predicted_outcome:.4f}",
                    simple_result.model_type,
                    len(set(simple_result.archetype_ids))
                ],
                "Difference": [
                    f"{simple_result.predicted_outcome - original_result.predicted_outcome:.4f}",
                    "N/A",
                    len(set(simple_result.archetype_ids)) - len(set(original_result.archetype_ids))
                ]
            }
            
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True)
    
    def display_performance_metrics(self):
        """Display performance metrics for both models."""
        st.subheader("📊 Performance Metrics")
        
        # Get optimized performance metrics
        optimized_metrics = get_performance_metrics()
        
        if optimized_metrics:
            st.markdown("**Optimized Performance Metrics:**")
            metrics_data = []
            for operation, metrics in optimized_metrics.items():
                metrics_data.append({
                    "Operation": operation,
                    "Count": metrics["count"],
                    "Avg Time (s)": f"{metrics['avg_time']:.3f}",
                    "Min Time (s)": f"{metrics['min_time']:.3f}",
                    "Max Time (s)": f"{metrics['max_time']:.3f}",
                    "Error Rate": f"{metrics['error_rate']:.1%}",
                    "Total Time (s)": f"{metrics['total_time']:.3f}"
                })
            
            metrics_df = pd.DataFrame(metrics_data)
            st.dataframe(metrics_df, use_container_width=True)
        
        # Also show legacy metrics
        st.markdown("**Legacy Performance Metrics:**")
        legacy_metrics_data = []
        for model_type, metrics in self.performance_metrics.items():
            avg_time = metrics["total_time"] / metrics["evaluations"] if metrics["evaluations"] > 0 else 0
            error_rate = metrics["errors"] / (metrics["evaluations"] + metrics["errors"]) if (metrics["evaluations"] + metrics["errors"]) > 0 else 0
            
            legacy_metrics_data.append({
                "Model": model_type.title(),
                "Evaluations": metrics["evaluations"],
                "Avg Time (s)": f"{avg_time:.3f}",
                "Errors": metrics["errors"],
                "Error Rate": f"{error_rate:.1%}"
            })
        
        legacy_metrics_df = pd.DataFrame(legacy_metrics_data)
        st.dataframe(legacy_metrics_df, use_container_width=True)
    
    def get_sample_lineups(self) -> List[Tuple[str, List[int]]]:
        """Get sample lineups for testing."""
        return [
            ("LeBron + Lakers Core", [2544, 101108, 201142, 201143, 201144]),
            ("Warriors Core", [201142, 201939, 201144, 201935, 201566]),
            ("Celtics Core", [201935, 201939, 201144, 201142, 201566]),
            ("Random Lineup", [201142, 201939, 201144, 201935, 201566])
        ]
    
    def run(self):
        """Run the enhanced dashboard."""
        st.title("🏀 NBA Enhanced Model Dashboard")
        st.markdown("**Advanced lineup evaluation with model switching and comparison capabilities**")
        
        # Initialize evaluators
        if not self.initialize_evaluators():
            st.stop()
        
        # Get model selection from sidebar
        selected_model_type, comparison_mode, enable_fallback = self.get_model_selector_ui()
        
        # Main content area
        tab1, tab2, tab3 = st.tabs(["🎯 Lineup Evaluation", "⚖️ Model Comparison", "📊 Performance"])
        
        with tab1:
            st.header("Lineup Evaluation")
            
            # Lineup input
            st.subheader("Enter Lineup")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Manual lineup input
                lineup_input = st.text_input(
                    "Player IDs (comma-separated)",
                    value="2544,101108,201142,201143,201144",
                    help="Enter 5 player IDs separated by commas"
                )
                
                try:
                    lineup = [int(x.strip()) for x in lineup_input.split(",")]
                    if len(lineup) != 5:
                        st.error("Please enter exactly 5 player IDs")
                        lineup = None
                except ValueError:
                    st.error("Please enter valid player IDs (numbers only)")
                    lineup = None
            
            with col2:
                # Sample lineup selection
                st.markdown("**Or select a sample:**")
                sample_lineups = self.get_sample_lineups()
                sample_names = [name for name, _ in sample_lineups]
                selected_sample = st.selectbox("Sample Lineup", sample_names)
                
                if st.button("Use Sample"):
                    lineup = next(lineup for name, lineup in sample_lineups if name == selected_sample)
                    st.rerun()
            
            # Evaluate lineup
            if lineup:
                if st.button("Evaluate Lineup", type="primary"):
                    with st.spinner("Evaluating lineup..."):
                        result = self.evaluate_lineup_safe(lineup, selected_model_type, enable_fallback)
                        
                        if result:
                            self.display_lineup_evaluation(result)
                        else:
                            st.error("Failed to evaluate lineup")
        
        with tab2:
            st.header("Model Comparison")
            
            if comparison_mode:
                # Lineup input for comparison
                st.subheader("Enter Lineup for Comparison")
                
                comparison_input = st.text_input(
                    "Player IDs (comma-separated)",
                    value="2544,101108,201142,201143,201144",
                    key="comparison_input",
                    help="Enter 5 player IDs to compare both models"
                )
                
                try:
                    comparison_lineup = [int(x.strip()) for x in comparison_input.split(",")]
                    if len(comparison_lineup) != 5:
                        st.error("Please enter exactly 5 player IDs")
                        comparison_lineup = None
                except ValueError:
                    st.error("Please enter valid player IDs (numbers only)")
                    comparison_lineup = None
                
                if comparison_lineup and st.button("Compare Models", type="primary"):
                    with st.spinner("Comparing models..."):
                        self.display_comparison(comparison_lineup)
            else:
                st.info("Enable Comparison Mode in the sidebar to compare both models")
        
        with tab3:
            st.header("Performance Metrics")
            self.display_performance_metrics()
            
            # Model information
            st.subheader("Model Information")
            available_models = ModelFactory.get_available_models()
            
            for model in available_models:
                with st.expander(f"{model['name']} - {model['status'].title()}"):
                    st.write(f"**Type:** {model['type']}")
                    st.write(f"**Description:** {model['description']}")
                    st.write(f"**Status:** {model['status']}")

def main():
    """Main function to run the enhanced dashboard."""
    dashboard = EnhancedModelDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()
