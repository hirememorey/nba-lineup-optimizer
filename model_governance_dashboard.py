"""
Model Governance Dashboard

This is the critical component for human model validation. It provides a structured,
interactive workflow for comparing different model versions and making informed decisions
about which coefficients to promote to production.

Based on the pre-mortem insight: human trust is not a simple procedural step, but requires
a dedicated tool that codifies domain expertise into a structured validation process.
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
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Page config
st.set_page_config(
    page_title="NBA Model Governance Dashboard",
    page_icon="⚖️",
    layout="wide"
)

class ModelGovernanceDashboard:
    """Dashboard for comparing and validating different model versions."""
    
    def __init__(self, db_path: str = "src/nba_stats/db/nba_stats.db"):
        """Initialize the governance dashboard."""
        self.db_path = db_path
        self.conn = None
        self.player_data = None
        self.archetype_data = None
        self.current_model = None
        self.candidate_model = None
        self.audit_log = []
        
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
    
    def load_model_coefficients(self, model_path: str) -> Optional[Dict]:
        """Load model coefficients from a file."""
        try:
            if not Path(model_path).exists():
                return None
                
            archetype_coef = pd.read_csv(model_path)
            
            # Load supercluster coefficients if available
            supercluster_path = model_path.replace("model_coefficients", "supercluster_coefficients")
            supercluster_coef = None
            if Path(supercluster_path).exists():
                supercluster_coef = pd.read_csv(supercluster_path)
            
            return {
                'archetype_coefficients': archetype_coef,
                'supercluster_coefficients': supercluster_coef,
                'model_path': model_path,
                'load_time': datetime.now().isoformat()
            }
        except Exception as e:
            st.error(f"Failed to load model from {model_path}: {e}")
            return None
    
    def calculate_lineup_value(self, player_ids: List[int], model: Dict) -> Dict[str, Any]:
        """Calculate lineup value using specified model coefficients."""
        if self.player_data is None:
            return {"error": "Player data not loaded"}
        
        # Get player data for the lineup
        lineup_players = self.player_data[self.player_data['player_id'].isin(player_ids)]
        
        if len(lineup_players) != len(player_ids):
            return {"error": "Some players not found in database"}
        
        # Calculate skill-based value
        total_offensive_skill = lineup_players['offensive_darko'].sum()
        total_defensive_skill = lineup_players['defensive_darko'].sum()
        
        # Use model coefficients if available
        if model and 'archetype_coefficients' in model:
            archetype_coef = model['archetype_coefficients']
            archetype_skill_value = 0
            archetype_counts = lineup_players['archetype_id'].value_counts()
            
            for arch_id, count in archetype_counts.items():
                arch_coef = archetype_coef[archetype_coef['archetype_id'] == arch_id]
                
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
    
    def get_litmus_test_scenarios(self) -> Dict[str, List[int]]:
        """Define critical test scenarios for model validation."""
        if self.player_data is None:
            return {}
        
        # Define core lineups for testing
        scenarios = {}
        
        # Lakers Core (LeBron, AD, Reaves, Hachimura) - need 5th player
        lakers_core = []
        lakers_names = ["LeBron James", "Anthony Davis", "Austin Reaves", "Rui Hachimura"]
        for name in lakers_names:
            player = self.player_data[self.player_data['player_name'] == name]
            if not player.empty:
                lakers_core.append(player.iloc[0]['player_id'])
        
        if len(lakers_core) >= 4:
            scenarios["Lakers Core"] = lakers_core[:4]
        
        # Suns Core (Beal, Booker, Durant, Ayton) - need 5th player
        suns_core = []
        suns_names = ["Bradley Beal", "Devin Booker", "Kevin Durant", "Deandre Ayton"]
        for name in suns_names:
            player = self.player_data[self.player_data['player_name'] == name]
            if not player.empty:
                suns_core.append(player.iloc[0]['player_id'])
        
        if len(suns_core) >= 4:
            scenarios["Suns Core"] = suns_core[:4]
        
        # Pacers Core (Haliburton, Mathurin, Hield, Turner) - need 5th player
        pacers_core = []
        pacers_names = ["Tyrese Haliburton", "Bennedict Mathurin", "Buddy Hield", "Myles Turner"]
        for name in pacers_names:
            player = self.player_data[self.player_data['player_name'] == name]
            if not player.empty:
                pacers_core.append(player.iloc[0]['player_id'])
        
        if len(pacers_core) >= 4:
            scenarios["Pacers Core"] = pacers_core[:4]
        
        return scenarios
    
    def run_litmus_test(self, scenario_name: str, core_players: List[int], 
                       model: Dict, n_candidates: int = 5) -> Dict[str, Any]:
        """Run a litmus test for a specific scenario."""
        if len(core_players) < 4:
            return {"error": f"Not enough core players for {scenario_name}"}
        
        # Get all available players (excluding core players)
        available_players = self.player_data[
            ~self.player_data['player_id'].isin(core_players)
        ].copy()
        
        if available_players.empty:
            return {"error": "No available players for testing"}
        
        # Test each available player as the 5th player
        test_results = []
        
        for _, player in available_players.iterrows():
            test_lineup = core_players + [player['player_id']]
            lineup_value = self.calculate_lineup_value(test_lineup, model)
            
            if "error" not in lineup_value:
                test_results.append({
                    'player_id': player['player_id'],
                    'player_name': player['player_name'],
                    'archetype_name': player['archetype_name'],
                    'offensive_darko': player['offensive_darko'],
                    'defensive_darko': player['defensive_darko'],
                    'lineup_value': lineup_value['total_value'],
                    'archetype_diversity': lineup_value['archetype_diversity']
                })
        
        # Sort by lineup value and return top candidates
        test_results.sort(key=lambda x: x['lineup_value'], reverse=True)
        
        return {
            'scenario_name': scenario_name,
            'core_players': core_players,
            'top_candidates': test_results[:n_candidates],
            'total_tested': len(test_results)
        }
    
    def log_audit_event(self, event_type: str, details: Dict[str, Any]):
        """Log an audit event."""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details
        }
        self.audit_log.append(event)
    
    def save_audit_log(self, filename: str = "model_audit.md"):
        """Save the audit log to a markdown file."""
        try:
            with open(filename, 'w') as f:
                f.write("# Model Governance Audit Log\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for event in self.audit_log:
                    f.write(f"## {event['event_type']} - {event['timestamp']}\n\n")
                    f.write(f"```json\n{json.dumps(event['details'], indent=2)}\n```\n\n")
            
            return True
        except Exception as e:
            st.error(f"Failed to save audit log: {e}")
            return False


def main():
    """Main Streamlit application."""
    st.title("⚖️ NBA Model Governance Dashboard")
    st.markdown("**Structured validation workflow for model coefficient comparison and approval**")
    
    # Initialize the dashboard
    dashboard = ModelGovernanceDashboard()
    
    # Connect to database
    if not dashboard.connect_database():
        st.stop()
    
    # Load data
    with st.spinner("Loading data..."):
        if not dashboard.load_player_data():
            st.stop()
        if not dashboard.load_archetype_data():
            st.stop()
    
    st.success("✅ Data loaded successfully!")
    
    # Model selection
    st.header("📊 Model Selection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Current Production Model")
        current_model_path = st.selectbox(
            "Select current model",
            ["model_coefficients.csv"] + [f for f in Path(".").glob("model_coefficients_*.csv")],
            key="current_model"
        )
        
        if st.button("Load Current Model"):
            dashboard.current_model = dashboard.load_model_coefficients(current_model_path)
            if dashboard.current_model:
                st.success(f"✅ Loaded current model from {current_model_path}")
                dashboard.log_audit_event("model_loaded", {
                    "model_type": "current",
                    "model_path": current_model_path
                })
            else:
                st.error("❌ Failed to load current model")
    
    with col2:
        st.subheader("Candidate Model")
        candidate_model_path = st.selectbox(
            "Select candidate model",
            ["model_coefficients.csv"] + [f for f in Path(".").glob("model_coefficients_*.csv")],
            key="candidate_model"
        )
        
        if st.button("Load Candidate Model"):
            dashboard.candidate_model = dashboard.load_model_coefficients(candidate_model_path)
            if dashboard.candidate_model:
                st.success(f"✅ Loaded candidate model from {candidate_model_path}")
                dashboard.log_audit_event("model_loaded", {
                    "model_type": "candidate",
                    "model_path": candidate_model_path
                })
            else:
                st.error("❌ Failed to load candidate model")
    
    # Model comparison
    if dashboard.current_model and dashboard.candidate_model:
        st.header("🔍 Model Comparison")
        
        # Litmus test scenarios
        st.subheader("Litmus Test Scenarios")
        
        scenarios = dashboard.get_litmus_test_scenarios()
        
        if scenarios:
            scenario_name = st.selectbox(
                "Select test scenario",
                list(scenarios.keys())
            )
            
            if st.button("Run Litmus Test"):
                with st.spinner("Running litmus test..."):
                    # Run test with current model
                    current_result = dashboard.run_litmus_test(
                        scenario_name, 
                        scenarios[scenario_name], 
                        dashboard.current_model
                    )
                    
                    # Run test with candidate model
                    candidate_result = dashboard.run_litmus_test(
                        scenario_name, 
                        scenarios[scenario_name], 
                        dashboard.candidate_model
                    )
                    
                    if "error" not in current_result and "error" not in candidate_result:
                        # Display side-by-side comparison
                        st.subheader(f"Results for {scenario_name}")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Current Model Recommendations**")
                            current_df = pd.DataFrame(current_result['top_candidates'])
                            st.dataframe(current_df[['player_name', 'archetype_name', 'lineup_value']], 
                                       use_container_width=True)
                        
                        with col2:
                            st.write("**Candidate Model Recommendations**")
                            candidate_df = pd.DataFrame(candidate_result['top_candidates'])
                            st.dataframe(candidate_df[['player_name', 'archetype_name', 'lineup_value']], 
                                       use_container_width=True)
                        
                        # Structured review questions
                        st.subheader("Structured Review")
                        
                        st.write("**Please answer the following questions:**")
                        
                        q1 = st.radio(
                            "1. Do the candidate model's top recommendations appear logically sound?",
                            ["Yes", "No", "Uncertain"],
                            key="q1"
                        )
                        
                        q2 = st.radio(
                            "2. Are the archetype distributions in the recommendations reasonable?",
                            ["Yes", "No", "Uncertain"],
                            key="q2"
                        )
                        
                        q3 = st.radio(
                            "3. Do the lineup value differences between models make sense?",
                            ["Yes", "No", "Uncertain"],
                            key="q3"
                        )
                        
                        q4 = st.text_area(
                            "4. Additional comments or concerns:",
                            placeholder="Enter any additional observations...",
                            key="q4"
                        )
                        
                        # Overall assessment
                        st.subheader("Overall Assessment")
                        
                        overall_score = 0
                        if q1 == "Yes":
                            overall_score += 1
                        if q2 == "Yes":
                            overall_score += 1
                        if q3 == "Yes":
                            overall_score += 1
                        
                        st.write(f"**Score: {overall_score}/3**")
                        
                        if overall_score >= 2:
                            st.success("✅ Candidate model appears ready for promotion")
                        elif overall_score == 1:
                            st.warning("⚠️ Candidate model needs review before promotion")
                        else:
                            st.error("❌ Candidate model should not be promoted")
                        
                        # Log the review
                        dashboard.log_audit_event("litmus_test_review", {
                            "scenario": scenario_name,
                            "current_model_path": current_model_path,
                            "candidate_model_path": candidate_model_path,
                            "responses": {
                                "q1": q1,
                                "q2": q2,
                                "q3": q3,
                                "q4": q4
                            },
                            "overall_score": overall_score,
                            "recommendation": "promote" if overall_score >= 2 else "review" if overall_score == 1 else "reject"
                        })
                        
                        # Save audit log
                        if st.button("Save Audit Log"):
                            if dashboard.save_audit_log():
                                st.success("✅ Audit log saved successfully")
                            else:
                                st.error("❌ Failed to save audit log")
                    
                    else:
                        st.error("Error running litmus test")
        else:
            st.warning("No test scenarios available. Please ensure core players are in the database.")
    
    # Model promotion
    if dashboard.current_model and dashboard.candidate_model:
        st.header("🚀 Model Promotion")
        
        st.write("**Ready to promote the candidate model to production?**")
        
        if st.button("Promote Candidate Model", type="primary"):
            # This would implement the actual promotion logic
            st.success("✅ Model promotion initiated!")
            st.info("Note: This is a placeholder. Implement actual promotion logic here.")
            
            dashboard.log_audit_event("model_promotion", {
                "from_model": current_model_path,
                "to_model": candidate_model_path,
                "promoted_by": "governance_dashboard",
                "timestamp": datetime.now().isoformat()
            })


if __name__ == "__main__":
    main()
