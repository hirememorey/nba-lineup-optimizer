"""
Model Failure Investigation Tools

This module provides tools to investigate WHY ground truth validation tests fail,
not just THAT they fail. It helps understand the model's behavior and identify
specific issues that need to be addressed.

Key Features:
1. Detailed model behavior analysis
2. Coefficient interpretation and validation
3. Lineup composition analysis
4. Player skill impact analysis
5. Archetype interaction analysis
6. Context sensitivity analysis
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import json
import logging
from src.nba_stats.model_factory import ModelFactory, evaluate_lineup
from ground_truth_validation import GroundTruthValidator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelFailureInvestigator:
    """
    Investigates model failures to understand root causes.
    
    This class provides detailed analysis tools to understand why the model
    fails ground truth validation tests. It examines model behavior, coefficients,
    and decision-making patterns to identify specific issues.
    """
    
    def __init__(self, model_type: str = "simple"):
        """Initialize the investigator."""
        self.model_type = model_type
        self.evaluator = ModelFactory.create_evaluator(model_type)
        self.db_path = Path("src/nba_stats/db/nba_stats.db")
        
        # Load player data
        self._load_player_data()
        
        logger.info(f"✅ ModelFailureInvestigator initialized for {model_type} model")
    
    def _load_player_data(self) -> None:
        """Load comprehensive player data for analysis."""
        with sqlite3.connect(self.db_path) as conn:
            query = """
            SELECT 
                ps.player_id,
                p.player_name,
                ps.offensive_darko,
                ps.defensive_darko,
                ps.darko,
                pa.archetype_id,
                a.archetype_name
            FROM PlayerSeasonSkill ps
            JOIN Players p ON ps.player_id = p.player_id
            JOIN PlayerSeasonArchetypes pa ON ps.player_id = pa.player_id
            JOIN Archetypes a ON pa.archetype_id = a.archetype_id
            WHERE ps.season = '2024-25'
            AND ps.offensive_darko IS NOT NULL
            AND ps.defensive_darko IS NOT NULL
            AND pa.archetype_id IS NOT NULL
            """
            
            self.players_df = pd.read_sql_query(query, conn)
            
            # Create analysis groups
            self.players_by_skill = self.players_df.sort_values('darko', ascending=False)
            self.players_by_archetype = self.players_df.groupby('archetype_id')
            
            logger.info(f"✅ Loaded {len(self.players_df)} players for investigation")
    
    def investigate_model_coefficients(self) -> Dict[str, Any]:
        """Investigate model coefficients and their interpretation."""
        logger.info("🔍 Investigating Model Coefficients")
        
        # Get model coefficients
        if hasattr(self.evaluator, 'get_model_coefficients_for_ui'):
            coeff_df = self.evaluator.get_model_coefficients_for_ui()
        else:
            # Fallback for models without coefficient export
            coeff_df = pd.DataFrame()
        
        analysis = {
            "coefficients_available": not coeff_df.empty,
            "coefficient_data": coeff_df.to_dict('records') if not coeff_df.empty else [],
            "coefficient_analysis": {}
        }
        
        if not coeff_df.empty:
            # Analyze coefficient patterns
            offensive_coeffs = coeff_df['beta_offensive'].values
            defensive_coeffs = coeff_df['beta_defensive'].values
            
            analysis["coefficient_analysis"] = {
                "offensive_coefficients": {
                    "values": offensive_coeffs.tolist(),
                    "range": [float(np.min(offensive_coeffs)), float(np.max(offensive_coeffs))],
                    "variance": float(np.var(offensive_coeffs)),
                    "all_positive": bool(np.all(offensive_coeffs > 0)),
                    "all_negative": bool(np.all(offensive_coeffs < 0))
                },
                "defensive_coefficients": {
                    "values": defensive_coeffs.tolist(),
                    "range": [float(np.min(defensive_coeffs)), float(np.max(defensive_coeffs))],
                    "variance": float(np.var(defensive_coeffs)),
                    "all_positive": bool(np.all(defensive_coeffs > 0)),
                    "all_negative": bool(np.all(defensive_coeffs < 0))
                },
                "coefficient_relationships": {
                    "off_def_correlation": float(np.corrcoef(offensive_coeffs, defensive_coeffs)[0, 1]),
                    "offensive_dominance": bool(np.mean(offensive_coeffs) > np.mean(defensive_coeffs)),
                    "coefficient_balance": float(np.std(offensive_coeffs) / np.std(defensive_coeffs))
                }
            }
        
        return analysis
    
    def investigate_skill_impact_patterns(self) -> Dict[str, Any]:
        """Investigate how the model responds to different skill levels."""
        logger.info("🔍 Investigating Skill Impact Patterns")
        
        # Test different skill levels systematically
        skill_levels = [0.1, 0.2, 0.5, 1.0, 2.0, 5.0]  # Multipliers for skill
        results = []
        
        # Get a baseline lineup
        baseline_players = self.players_by_skill.iloc[10:15]  # Middle skill players
        baseline_lineup = baseline_players['player_id'].tolist()
        baseline_result = self.evaluator.evaluate_lineup(baseline_lineup)
        
        for multiplier in skill_levels:
            # Create modified lineup with scaled skills
            modified_lineup = []
            for player_id in baseline_lineup:
                player = self.players_df[self.players_df['player_id'] == player_id].iloc[0]
                
                # Find a player with similar archetype but different skill
                archetype_players = self.players_df[self.players_df['archetype_id'] == player['archetype_id']]
                target_skill = player['darko'] * multiplier
                
                # Find closest player to target skill
                skill_diffs = np.abs(archetype_players['darko'] - target_skill)
                closest_idx = skill_diffs.idxmin()
                closest_player = archetype_players.loc[closest_idx]
                
                modified_lineup.append(closest_player['player_id'])
            
            # Evaluate modified lineup
            modified_result = self.evaluator.evaluate_lineup(modified_lineup)
            
            # Calculate skill change
            baseline_skill = np.mean([self.players_df[self.players_df['player_id'] == pid]['darko'].iloc[0] 
                                    for pid in baseline_lineup])
            modified_skill = np.mean([self.players_df[self.players_df['player_id'] == pid]['darko'].iloc[0] 
                                    for pid in modified_lineup])
            
            results.append({
                "multiplier": multiplier,
                "baseline_skill": baseline_skill,
                "modified_skill": modified_skill,
                "skill_change": modified_skill - baseline_skill,
                "baseline_prediction": baseline_result.predicted_outcome,
                "modified_prediction": modified_result.predicted_outcome,
                "prediction_change": modified_result.predicted_outcome - baseline_result.predicted_outcome,
                "sensitivity": (modified_result.predicted_outcome - baseline_result.predicted_outcome) / (modified_skill - baseline_skill) if modified_skill != baseline_skill else 0
            })
        
        # Analyze patterns
        sensitivities = [r['sensitivity'] for r in results if r['sensitivity'] != 0]
        
        analysis = {
            "skill_impact_tests": results,
            "sensitivity_analysis": {
                "mean_sensitivity": float(np.mean(sensitivities)) if sensitivities else 0,
                "sensitivity_variance": float(np.var(sensitivities)) if sensitivities else 0,
                "sensitivity_range": [float(np.min(sensitivities)), float(np.max(sensitivities))] if sensitivities else [0, 0],
                "consistent_response": float(np.std(sensitivities)) < 0.1 if sensitivities else True
            },
            "skill_response_quality": {
                "monotonic": all(results[i]['prediction_change'] >= results[i-1]['prediction_change'] 
                               for i in range(1, len(results)) if results[i]['skill_change'] > results[i-1]['skill_change']),
                "proportional": abs(np.corrcoef([r['skill_change'] for r in results], 
                                              [r['prediction_change'] for r in results])[0, 1]) > 0.8,
                "reasonable_magnitude": all(abs(r['prediction_change']) < 10 for r in results)
            }
        }
        
        return analysis
    
    def investigate_archetype_interactions(self) -> Dict[str, Any]:
        """Investigate how different archetype combinations affect predictions."""
        logger.info("🔍 Investigating Archetype Interactions")
        
        # Get players from each archetype
        archetype_groups = {arch_id: group for arch_id, group in self.players_by_archetype}
        archetype_ids = list(archetype_groups.keys())
        
        if len(archetype_ids) < 2:
            return {"error": "Not enough archetypes for interaction analysis"}
        
        # Test different archetype combinations
        combinations = []
        
        # Test all possible 2-archetype combinations
        for i, arch1 in enumerate(archetype_ids):
            for j, arch2 in enumerate(archetype_ids[i+1:], i+1):
                arch1_players = archetype_groups[arch1]
                arch2_players = archetype_groups[arch2]
                
                if len(arch1_players) >= 3 and len(arch2_players) >= 2:
                    # Create lineup: 3 from arch1, 2 from arch2
                    lineup = (arch1_players.iloc[:3]['player_id'].tolist() + 
                            arch2_players.iloc[:2]['player_id'].tolist())
                    
                    result = self.evaluator.evaluate_lineup(lineup)
                    
                    combinations.append({
                        "archetype1": arch1,
                        "archetype2": arch2,
                        "archetype1_name": arch1_players.iloc[0]['archetype_name'],
                        "archetype2_name": arch2_players.iloc[0]['archetype_name'],
                        "lineup": lineup,
                        "prediction": result.predicted_outcome,
                        "archetype_distribution": {
                            arch1: 3,
                            arch2: 2
                        }
                    })
        
        # Analyze interaction patterns
        if combinations:
            predictions = [c['prediction'] for c in combinations]
            archetype_pairs = [(c['archetype1'], c['archetype2']) for c in combinations]
            
            # Calculate interaction effects
            interaction_effects = {}
            for i, combo1 in enumerate(combinations):
                for j, combo2 in enumerate(combinations[i+1:], i+1):
                    if combo1['archetype1'] == combo2['archetype1'] or combo1['archetype2'] == combo2['archetype2']:
                        # These combinations share an archetype, compare them
                        shared_arch = combo1['archetype1'] if combo1['archetype1'] == combo2['archetype1'] else combo1['archetype2']
                        other_arch1 = combo1['archetype2'] if combo1['archetype1'] == combo2['archetype1'] else combo1['archetype1']
                        other_arch2 = combo2['archetype2'] if combo1['archetype1'] == combo2['archetype1'] else combo2['archetype1']
                        
                        interaction_key = f"{shared_arch}_{other_arch1}_vs_{other_arch2}"
                        interaction_effects[interaction_key] = {
                            "shared_archetype": shared_arch,
                            "other_archetypes": [other_arch1, other_arch2],
                            "prediction_difference": combo1['prediction'] - combo2['prediction'],
                            "combo1_prediction": combo1['prediction'],
                            "combo2_prediction": combo2['prediction']
                        }
            
            analysis = {
                "archetype_combinations": combinations,
                "interaction_effects": interaction_effects,
                "prediction_statistics": {
                    "mean": float(np.mean(predictions)),
                    "std": float(np.std(predictions)),
                    "range": [float(np.min(predictions)), float(np.max(predictions))],
                    "variance": float(np.var(predictions))
                },
                "interaction_quality": {
                    "has_meaningful_differences": float(np.std(predictions)) > 0.01,
                    "interaction_consistency": len([e for e in interaction_effects.values() if abs(e['prediction_difference']) > 0.01]) > 0,
                    "archetype_sensitivity": len(set(predictions)) > 1
                }
            }
        else:
            analysis = {"error": "No valid archetype combinations found"}
        
        return analysis
    
    def investigate_context_sensitivity(self) -> Dict[str, Any]:
        """Investigate how player value changes in different contexts."""
        logger.info("🔍 Investigating Context Sensitivity")
        
        # Get a good player to test
        test_player = self.players_by_skill.iloc[0]
        test_player_id = test_player['player_id']
        
        # Create different contexts
        contexts = []
        
        # Context 1: With other high-skill players
        high_skill_players = self.players_by_skill.iloc[1:5]['player_id'].tolist()
        context1_lineup = high_skill_players + [test_player_id]
        context1_result = self.evaluator.evaluate_lineup(context1_lineup)
        # Note: Can't evaluate 4-player baseline, so we'll use a different approach
        
        # Context 2: With low-skill players
        low_skill_players = self.players_by_skill.tail(4)['player_id'].tolist()
        context2_lineup = low_skill_players + [test_player_id]
        context2_result = self.evaluator.evaluate_lineup(context2_lineup)
        # Note: Can't evaluate 4-player baseline, so we'll use a different approach
        
        # Context 3: With same archetype players
        same_archetype_players = self.players_df[
            (self.players_df['archetype_id'] == test_player['archetype_id']) & 
            (self.players_df['player_id'] != test_player_id)
        ].iloc[:4]['player_id'].tolist()
        
        if len(same_archetype_players) >= 4:
            context3_lineup = same_archetype_players + [test_player_id]
            context3_result = self.evaluator.evaluate_lineup(context3_lineup)
            # Note: Can't evaluate 4-player baseline
        else:
            context3_result = None
        
        # Context 4: With different archetype players
        different_archetype_players = self.players_df[
            self.players_df['archetype_id'] != test_player['archetype_id']
        ].iloc[:4]['player_id'].tolist()
        
        context4_lineup = different_archetype_players + [test_player_id]
        context4_result = self.evaluator.evaluate_lineup(context4_lineup)
        # Note: Can't evaluate 4-player baseline
        
        # For context sensitivity analysis, we'll compare the full lineups directly
        # since we can't evaluate 4-player baselines
        marginal_values = {
            "high_skill_context": context1_result.predicted_outcome,
            "low_skill_context": context2_result.predicted_outcome,
            "different_archetype_context": context4_result.predicted_outcome
        }
        
        if context3_result:
            marginal_values["same_archetype_context"] = context3_result.predicted_outcome
        
        # Analyze context sensitivity
        marginal_value_list = list(marginal_values.values())
        
        analysis = {
            "test_player": {
                "player_id": test_player_id,
                "player_name": test_player['player_name'],
                "archetype_id": test_player['archetype_id'],
                "archetype_name": test_player['archetype_name'],
                "skill_level": test_player['darko']
            },
            "contexts": {
                "high_skill_context": {
                    "lineup": context1_lineup,
                    "prediction": context1_result.predicted_outcome,
                    "context_type": "high_skill_supporting_cast"
                },
                "low_skill_context": {
                    "lineup": context2_lineup,
                    "prediction": context2_result.predicted_outcome,
                    "context_type": "low_skill_supporting_cast"
                },
                "different_archetype_context": {
                    "lineup": context4_lineup,
                    "prediction": context4_result.predicted_outcome,
                    "context_type": "different_archetype_supporting_cast"
                }
            },
            "context_sensitivity_analysis": {
                "predictions": marginal_values,
                "prediction_variance": float(np.var(marginal_value_list)),
                "prediction_range": [float(np.min(marginal_value_list)), float(np.max(marginal_value_list))],
                "has_context_sensitivity": float(np.var(marginal_value_list)) > 0.01,
                "context_differences": {
                    "high_vs_low": marginal_values["high_skill_context"] - marginal_values["low_skill_context"],
                    "different_archetype_vs_high": marginal_values["different_archetype_context"] - marginal_values["high_skill_context"],
                    "different_archetype_vs_low": marginal_values["different_archetype_context"] - marginal_values["low_skill_context"]
                }
            }
        }
        
        if context3_result:
            analysis["contexts"]["same_archetype_context"] = {
                "lineup": context3_lineup,
                "prediction": context3_result.predicted_outcome,
                "context_type": "same_archetype_supporting_cast"
            }
        
        return analysis
    
    def investigate_model_decision_patterns(self) -> Dict[str, Any]:
        """Investigate the model's decision-making patterns."""
        logger.info("🔍 Investigating Model Decision Patterns")
        
        # Test various lineup patterns
        patterns = []
        
        # Pattern 1: All same archetype
        for arch_id, group in self.players_by_archetype:
            if len(group) >= 5:
                lineup = group.iloc[:5]['player_id'].tolist()
                result = self.evaluator.evaluate_lineup(lineup)
                patterns.append({
                    "pattern": "all_same_archetype",
                    "archetype_id": arch_id,
                    "archetype_name": group.iloc[0]['archetype_name'],
                    "lineup": lineup,
                    "prediction": result.predicted_outcome,
                    "skill_stats": {
                        "mean_skill": float(np.mean(group.iloc[:5]['darko'])),
                        "skill_variance": float(np.var(group.iloc[:5]['darko'])),
                        "mean_offensive": float(np.mean(group.iloc[:5]['offensive_darko'])),
                        "mean_defensive": float(np.mean(group.iloc[:5]['defensive_darko']))
                    }
                })
        
        # Pattern 2: Balanced archetype distribution
        archetype_ids = list(self.players_by_archetype.groups.keys())
        if len(archetype_ids) >= 3:
            balanced_lineup = []
            for i, arch_id in enumerate(archetype_ids[:3]):
                group = self.players_by_archetype.get_group(arch_id)
                if len(group) > 0:
                    balanced_lineup.append(group.iloc[0]['player_id'])
            
            # Fill remaining spots with role players
            role_players = self.players_df[self.players_df['archetype_id'] == 2]
            while len(balanced_lineup) < 5 and len(role_players) > 0:
                balanced_lineup.append(role_players.iloc[len(balanced_lineup) - 3]['player_id'])
            
            if len(balanced_lineup) == 5:
                result = self.evaluator.evaluate_lineup(balanced_lineup)
                patterns.append({
                    "pattern": "balanced_archetypes",
                    "lineup": balanced_lineup,
                    "prediction": result.predicted_outcome,
                    "archetype_distribution": {
                        arch_id: sum(1 for pid in balanced_lineup 
                                   if self.players_df[self.players_df['player_id'] == pid]['archetype_id'].iloc[0] == arch_id)
                        for arch_id in archetype_ids
                    }
                })
        
        # Pattern 3: High skill vs low skill
        high_skill_lineup = self.players_by_skill.iloc[:5]['player_id'].tolist()
        low_skill_lineup = self.players_by_skill.tail(5)['player_id'].tolist()
        
        high_result = self.evaluator.evaluate_lineup(high_skill_lineup)
        low_result = self.evaluator.evaluate_lineup(low_skill_lineup)
        
        patterns.extend([
            {
                "pattern": "high_skill",
                "lineup": high_skill_lineup,
                "prediction": high_result.predicted_outcome,
                "skill_stats": {
                    "mean_skill": float(np.mean(self.players_by_skill.iloc[:5]['darko'])),
                    "skill_variance": float(np.var(self.players_by_skill.iloc[:5]['darko']))
                }
            },
            {
                "pattern": "low_skill",
                "lineup": low_skill_lineup,
                "prediction": low_result.predicted_outcome,
                "skill_stats": {
                    "mean_skill": float(np.mean(self.players_by_skill.tail(5)['darko'])),
                    "skill_variance": float(np.var(self.players_by_skill.tail(5)['darko']))
                }
            }
        ])
        
        # Analyze patterns
        predictions = [p['prediction'] for p in patterns]
        
        analysis = {
            "tested_patterns": patterns,
            "pattern_analysis": {
                "prediction_range": [float(np.min(predictions)), float(np.max(predictions))],
                "prediction_variance": float(np.var(predictions)),
                "has_meaningful_differences": float(np.std(predictions)) > 0.01,
                "pattern_consistency": len(set(predictions)) > 1
            },
            "skill_vs_prediction_correlation": {
                "high_skill_prediction": high_result.predicted_outcome,
                "low_skill_prediction": low_result.predicted_outcome,
                "skill_difference": float(np.mean(self.players_by_skill.iloc[:5]['darko']) - 
                                        np.mean(self.players_by_skill.tail(5)['darko'])),
                "prediction_difference": high_result.predicted_outcome - low_result.predicted_outcome,
                "correlation_direction": "positive" if high_result.predicted_outcome > low_result.predicted_outcome else "negative"
            }
        }
        
        return analysis
    
    def run_comprehensive_investigation(self) -> Dict[str, Any]:
        """Run comprehensive investigation of model failures."""
        logger.info("🔍 Starting Comprehensive Model Investigation")
        logger.info("=" * 60)
        
        investigation = {
            "model_type": self.model_type,
            "investigation_timestamp": pd.Timestamp.now().isoformat(),
            "coefficient_analysis": self.investigate_model_coefficients(),
            "skill_impact_analysis": self.investigate_skill_impact_patterns(),
            "archetype_interaction_analysis": self.investigate_archetype_interactions(),
            "context_sensitivity_analysis": self.investigate_context_sensitivity(),
            "decision_pattern_analysis": self.investigate_model_decision_patterns()
        }
        
        # Generate summary insights
        investigation["summary_insights"] = self._generate_investigation_insights(investigation)
        
        return investigation
    
    def _generate_investigation_insights(self, investigation: Dict[str, Any]) -> List[str]:
        """Generate insights from investigation results."""
        insights = []
        
        # Coefficient insights
        coeff_analysis = investigation.get("coefficient_analysis", {})
        if coeff_analysis.get("coefficients_available"):
            coeff_data = coeff_analysis.get("coefficient_analysis", {})
            if not coeff_data.get("offensive_coefficients", {}).get("all_positive", True):
                insights.append("⚠️ Some offensive coefficients are negative - this may indicate model issues")
            if not coeff_data.get("defensive_coefficients", {}).get("all_positive", True):
                insights.append("⚠️ Some defensive coefficients are negative - this may indicate model issues")
        
        # Skill impact insights
        skill_analysis = investigation.get("skill_impact_analysis", {})
        if not skill_analysis.get("skill_response_quality", {}).get("monotonic", True):
            insights.append("❌ Model does not show monotonic response to skill changes")
        if not skill_analysis.get("skill_response_quality", {}).get("proportional", True):
            insights.append("❌ Model does not show proportional response to skill changes")
        
        # Archetype interaction insights
        arch_analysis = investigation.get("archetype_interaction_analysis", {})
        if not arch_analysis.get("interaction_quality", {}).get("has_meaningful_differences", True):
            insights.append("❌ Model does not show meaningful differences between archetype combinations")
        
        # Context sensitivity insights
        context_analysis = investigation.get("context_sensitivity_analysis", {})
        if not context_analysis.get("context_sensitivity_analysis", {}).get("has_context_sensitivity", True):
            insights.append("❌ Model does not show context sensitivity - player value is constant across contexts")
        
        # Decision pattern insights
        pattern_analysis = investigation.get("decision_pattern_analysis", {})
        if not pattern_analysis.get("pattern_analysis", {}).get("has_meaningful_differences", True):
            insights.append("❌ Model does not show meaningful differences between lineup patterns")
        
        if not insights:
            insights.append("✅ Model shows reasonable behavior patterns")
        
        return insights


def main():
    """Run comprehensive model investigation."""
    print("🔍 NBA Lineup Optimizer - Model Failure Investigation")
    print("=" * 60)
    
    try:
        # Initialize investigator
        investigator = ModelFailureInvestigator(model_type="simple")
        
        # Run comprehensive investigation
        investigation = investigator.run_comprehensive_investigation()
        
        # Save investigation results
        with open("model_failure_investigation.json", "w") as f:
            json.dump(investigation, f, indent=2, default=str)
        
        print(f"\n📊 Investigation Report saved to: model_failure_investigation.json")
        
        # Print summary insights
        print(f"\n💡 Investigation Insights:")
        for insight in investigation["summary_insights"]:
            print(f"   {insight}")
        
        return investigation
        
    except Exception as e:
        print(f"❌ Investigation failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    investigation = main()
    if investigation:
        print("\n✅ Investigation completed successfully")
    else:
        print("\n❌ Investigation failed")
        exit(1)
