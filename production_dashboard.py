"""
Production NBA Lineup Optimizer Dashboard

This is the main production dashboard that integrates all components:
- Authentication
- User onboarding
- Model evaluation
- Admin panel
- Monitoring
- Error handling
"""

import streamlit as st
import sys
from pathlib import Path
import logging
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import our production modules
from config import get_config, Config
from auth import auth_manager
from monitoring import track_performance, log_user_action, log_error, get_system_metrics
from error_handling import error_handler, monitor_performance
from user_onboarding import get_user_onboarding
from admin_panel import show_admin_panel

# Import model components
from nba_stats.model_factory import ModelFactory, ModelType, NormalizedLineupEvaluation
from nba_stats.model_evaluator import ModelEvaluator
from nba_stats.simple_model_evaluator import SimpleModelEvaluator
from nba_stats.performance_optimizer import OptimizedModelFactory, get_performance_metrics, preload_models

# Set up logging
config = get_config()
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="NBA Lineup Optimizer - Production",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

class ProductionDashboard:
    """Main production dashboard."""
    
    def __init__(self):
        self.config = config
        self.model_factory = None
        self.user_onboarding = get_user_onboarding(self.config)
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize session state variables."""
        if "dashboard_initialized" not in st.session_state:
            st.session_state.dashboard_initialized = True
            st.session_state.model_type = "simple"
            st.session_state.comparison_mode = False
            st.session_state.lineup_history = []
            st.session_state.error_count = 0
            st.session_state.tutorial_completed = False
            st.session_state.session_id = f"session_{int(time.time())}"
    
    @monitor_performance("dashboard_initialization")
    def initialize_models(self):
        """Initialize model factory and preload models."""
        try:
            if self.model_factory is None:
                self.model_factory = OptimizedModelFactory()
                preload_models()
                log_user_action("models_initialized")
            return True
        except Exception as e:
            log_error(e, "model_initialization")
            return False
    
    def show_sidebar(self):
        """Show sidebar with controls."""
        with st.sidebar:
            st.title("🏀 NBA Lineup Optimizer")
            st.markdown("---")
            
            # User info
            if auth_manager.is_authenticated():
                username = auth_manager.get_username()
                st.success(f"Welcome, {username}!")
                
                if username == "admin":
                    if st.button("🔧 Admin Panel"):
                        st.session_state.show_admin = True
                        st.rerun()
            else:
                st.warning("Please log in to access the dashboard")
            
            st.markdown("---")
            
            # Model selection
            st.subheader("Model Selection")
            model_options = {
                "Production Model (3-Archetype)": "simple",
                "Original Model (8-Archetype)": "original"
            }
            
            selected_model = st.selectbox(
                "Choose Model",
                options=list(model_options.keys()),
                index=0,
                help="Select which model to use for lineup evaluation"
            )
            
            st.session_state.model_type = model_options[selected_model]
            
            # Comparison mode
            st.session_state.comparison_mode = st.checkbox(
                "Enable Comparison Mode",
                value=False,
                help="Compare both models side-by-side"
            )
            
            st.markdown("---")
            
            # Quick actions
            st.subheader("Quick Actions")
            
            if st.button("📚 Tutorial"):
                st.session_state.show_tutorial = True
                st.rerun()
            
            if st.button("📊 My Dashboard"):
                st.session_state.show_user_dashboard = True
                st.rerun()
            
            if st.button("📈 System Metrics"):
                st.session_state.show_metrics = True
                st.rerun()
            
            st.markdown("---")
            
            # System status
            self.show_system_status()
    
    def show_system_status(self):
        """Show system status in sidebar."""
        st.subheader("System Status")
        
        # Database status
        db_path = Path(self.config.DATABASE_PATH)
        if db_path.exists():
            st.success("✅ Database")
        else:
            st.error("❌ Database")
        
        # Model coefficients status
        coeff_path = Path(self.config.MODEL_COEFFICIENTS_PATH)
        if coeff_path.exists():
            st.success("✅ Models")
        else:
            st.warning("⚠️ Models")
        
        # Error count
        if st.session_state.error_count > 0:
            st.warning(f"⚠️ {st.session_state.error_count} errors")
    
    @monitor_performance("lineup_evaluation")
    def evaluate_lineup(self, lineup_ids: list, model_type: str) -> NormalizedLineupEvaluation:
        """Evaluate lineup with error handling."""
        try:
            if not self.model_factory:
                if not self.initialize_models():
                    raise Exception("Failed to initialize models")
            
            result = self.model_factory.evaluate_lineup(lineup_ids, model_type)
            log_user_action("lineup_evaluated", {
                "lineup": lineup_ids,
                "model_type": model_type,
                "predicted_outcome": result.predicted_outcome
            })
            return result
            
        except Exception as e:
            log_error(e, "lineup_evaluation")
            st.session_state.error_count += 1
            raise
    
    def show_lineup_evaluation(self):
        """Show lineup evaluation interface."""
        st.header("Lineup Evaluation")
        
        # Sample lineups
        sample_lineups = {
            "LeBron + Lakers Core": [2544, 101108, 201142, 201143, 201144],
            "Warriors Core": [201142, 201939, 201144, 201935, 201566],
            "Celtics Core": [201935, 201939, 201144, 201142, 201566],
            "Random Lineup": [201142, 201939, 201144, 201935, 201566]
        }
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Manual lineup input
            st.subheader("Enter Player IDs")
            lineup_input = st.text_input(
                "Player IDs (comma-separated)",
                placeholder="2544, 101108, 201142, 201143, 201144",
                help="Enter 5 player IDs separated by commas"
            )
            
            if lineup_input:
                try:
                    lineup_ids = [int(x.strip()) for x in lineup_input.split(",")]
                    if len(lineup_ids) != 5:
                        st.error("Please enter exactly 5 player IDs")
                        lineup_ids = None
                except ValueError:
                    st.error("Please enter valid player IDs (numbers only)")
                    lineup_ids = None
            else:
                lineup_ids = None
        
        with col2:
            # Sample lineups
            st.subheader("Sample Lineups")
            selected_sample = st.selectbox(
                "Choose a sample lineup",
                options=list(sample_lineups.keys()),
                index=0
            )
            
            if st.button("Load Sample"):
                lineup_ids = sample_lineups[selected_sample]
                st.success(f"Loaded: {selected_sample}")
        
        # Evaluate button
        if lineup_ids and st.button("Evaluate Lineup", type="primary"):
            with st.spinner("Evaluating lineup..."):
                try:
                    if st.session_state.comparison_mode:
                        self.show_comparison_results(lineup_ids)
                    else:
                        self.show_single_result(lineup_ids)
                except Exception as e:
                    st.error(f"Failed to evaluate lineup: {str(e)}")
    
    def show_single_result(self, lineup_ids: list):
        """Show single model result."""
        try:
            result = self.evaluate_lineup(lineup_ids, st.session_state.model_type)
            
            # Display results
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Predicted Outcome", f"{result.predicted_outcome:.3f}")
            
            with col2:
                st.metric("Model Type", result.model_type)
            
            with col3:
                st.metric("Player Count", len(result.player_ids))
            
            # Player details
            st.subheader("Player Details")
            player_data = []
            for i, (player_id, player_name, archetype_id, archetype_name) in enumerate(
                zip(result.player_ids, result.player_names, result.archetype_ids, result.archetype_names)
            ):
                player_data.append({
                    "Player": player_name,
                    "ID": player_id,
                    "Archetype": archetype_name,
                    "Archetype ID": archetype_id
                })
            
            df = pd.DataFrame(player_data)
            st.dataframe(df, use_container_width=True)
            
            # Skill scores
            if hasattr(result, 'skill_scores') and result.skill_scores:
                st.subheader("Skill Scores")
                skill_df = pd.DataFrame([result.skill_scores])
                st.dataframe(skill_df, use_container_width=True)
                
        except Exception as e:
            st.error(f"Error evaluating lineup: {str(e)}")
    
    def show_comparison_results(self, lineup_ids: list):
        """Show comparison between both models."""
        st.subheader("Model Comparison")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Production Model (3-Archetype)**")
            try:
                result1 = self.evaluate_lineup(lineup_ids, "simple")
                st.metric("Predicted Outcome", f"{result1.predicted_outcome:.3f}")
                st.metric("Model Type", result1.model_type)
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        with col2:
            st.write("**Original Model (8-Archetype)**")
            try:
                result2 = self.evaluate_lineup(lineup_ids, "original")
                st.metric("Predicted Outcome", f"{result2.predicted_outcome:.3f}")
                st.metric("Model Type", result2.model_type)
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        # Comparison metrics
        try:
            if 'result1' in locals() and 'result2' in locals():
                st.subheader("Comparison Metrics")
                difference = result1.predicted_outcome - result2.predicted_outcome
                st.metric("Difference", f"{difference:.3f}")
                
                if abs(difference) > 0.1:
                    st.warning("Significant difference between models")
                else:
                    st.success("Models are in agreement")
        except:
            pass
    
    def show_user_dashboard(self):
        """Show user dashboard."""
        self.user_onboarding.show_user_dashboard()
    
    def show_metrics(self):
        """Show system metrics."""
        st.header("System Metrics")
        
        try:
            metrics = get_system_metrics()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Requests", metrics.get("requests", 0))
                st.metric("Model Evaluations", metrics.get("model_evaluations", 0))
            
            with col2:
                st.metric("Avg Response Time", f"{metrics.get('avg_response_time', 0):.2f}s")
                st.metric("Error Rate", f"{metrics.get('error_rate', 0):.2%}")
            
            with col3:
                st.metric("Uptime", f"{metrics.get('uptime_hours', 0):.1f} hours")
                st.metric("Requests/Hour", f"{metrics.get('requests_per_hour', 0):.1f}")
            
        except Exception as e:
            st.error(f"Failed to load metrics: {str(e)}")
    
    def run(self):
        """Run the production dashboard."""
        # Check authentication
        auth_manager.require_auth()
        
        # Initialize models
        if not self.initialize_models():
            st.error("Failed to initialize models. Please check the system status.")
            return
        
        # Show sidebar
        self.show_sidebar()
        
        # Main content based on state
        if st.session_state.get("show_admin", False):
            show_admin_panel()
            if st.button("← Back to Dashboard"):
                st.session_state.show_admin = False
                st.rerun()
        elif st.session_state.get("show_tutorial", False):
            self.user_onboarding.show_tutorial()
            if st.button("← Back to Dashboard"):
                st.session_state.show_tutorial = False
                st.rerun()
        elif st.session_state.get("show_user_dashboard", False):
            self.show_user_dashboard()
            if st.button("← Back to Dashboard"):
                st.session_state.show_user_dashboard = False
                st.rerun()
        elif st.session_state.get("show_metrics", False):
            self.show_metrics()
            if st.button("← Back to Dashboard"):
                st.session_state.show_metrics = False
                st.rerun()
        else:
            # Main dashboard
            st.title("🏀 NBA Lineup Optimizer")
            st.markdown("Advanced lineup analysis using player archetypes and Bayesian modeling")
            
            # Show lineup evaluation
            self.show_lineup_evaluation()
            
            # Show error handling
            if st.session_state.error_count > 0:
                st.warning(f"⚠️ {st.session_state.error_count} errors occurred during this session")
                
                if st.button("Reset Error Count"):
                    st.session_state.error_count = 0
                    st.rerun()
        
        # Footer
        st.markdown("---")
        st.markdown(f"**Version:** {self.config.VERSION} | **Environment:** {'Production' if not self.config.DEBUG else 'Development'}")

def main():
    """Main function."""
    try:
        # Validate configuration
        config.validate()
        
        # Create and run dashboard
        dashboard = ProductionDashboard()
        dashboard.run()
        
    except Exception as e:
        st.error(f"Failed to start dashboard: {str(e)}")
        logger.error(f"Dashboard startup error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
