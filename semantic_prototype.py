"""
Semantic Prototype for Possession-Level Modeling

This module implements the critical "Semantic Prototyping" step that validates
the analytical logic using synthetic data before attempting to use real data.

This addresses the key insight from the pre-mortem: we need fast feedback
on whether our model makes basketball sense before running the expensive
18-hour Bayesian training process.
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')


@dataclass
class SemanticValidationResult:
    """Result of a semantic validation check."""
    check_name: str
    passed: bool
    message: str
    actual_value: Optional[float] = None
    expected_value: Optional[float] = None
    tolerance: float = 0.1


class SemanticPrototype:
    """
    Semantic prototype using synthetic data to validate analytical logic.
    
    This class implements the fast proxy model (Ridge Regression) that runs
    in seconds and provides immediate feedback on whether the model logic
    makes basketball sense.
    """
    
    def __init__(self):
        """Initialize the semantic prototype."""
        self.synthetic_data = None
        self.model = None
        self.scaler = StandardScaler()
        self.validation_results = []
    
    def generate_synthetic_data(self, n_possessions: int = 10000) -> pd.DataFrame:
        """
        Generate synthetic possession data that follows realistic patterns.
        
        Args:
            n_possessions: Number of synthetic possessions to generate
            
        Returns:
            DataFrame with synthetic possession data
        """
        np.random.seed(42)  # For reproducible results
        
        # Generate synthetic possessions with realistic patterns
        data = []
        
        for i in range(n_possessions):
            # Generate archetype combinations (8 archetypes, 5 players each)
            offensive_archetypes = np.random.choice(8, 5, replace=True)
            defensive_archetypes = np.random.choice(8, 5, replace=True)
            
            # Generate skill ratings (DARKO-style, centered around 0)
            offensive_skills = np.random.normal(0, 2, 5)
            defensive_skills = np.random.normal(0, 2, 5)
            
            # Generate lineup superclusters (6 superclusters)
            offensive_supercluster = np.random.choice(6)
            defensive_supercluster = np.random.choice(6)
            
            # Generate possession outcome based on realistic patterns
            # Higher offensive skill should increase outcome
            # Higher defensive skill should decrease outcome
            # Certain archetype matchups should matter
            
            base_outcome = 0.0
            
            # Skill effects (the core insight we want to validate)
            skill_effect = np.sum(offensive_skills) * 0.1 - np.sum(defensive_skills) * 0.1
            
            # Archetype interaction effects (simplified)
            archetype_effect = self._calculate_archetype_effect(
                offensive_archetypes, defensive_archetypes
            )
            
            # Supercluster effects
            supercluster_effect = self._calculate_supercluster_effect(
                offensive_supercluster, defensive_supercluster
            )
            
            # Add noise
            noise = np.random.normal(0, 0.5)
            
            outcome = base_outcome + skill_effect + archetype_effect + supercluster_effect + noise
            
            # Create possession record
            possession = {
                'possession_id': i,
                'offensive_archetype_1': offensive_archetypes[0],
                'offensive_archetype_2': offensive_archetypes[1],
                'offensive_archetype_3': offensive_archetypes[2],
                'offensive_archetype_4': offensive_archetypes[3],
                'offensive_archetype_5': offensive_archetypes[4],
                'defensive_archetype_1': defensive_archetypes[0],
                'defensive_archetype_2': defensive_archetypes[1],
                'defensive_archetype_3': defensive_archetypes[2],
                'defensive_archetype_4': defensive_archetypes[3],
                'defensive_archetype_5': defensive_archetypes[4],
                'offensive_skill_1': offensive_skills[0],
                'offensive_skill_2': offensive_skills[1],
                'offensive_skill_3': offensive_skills[2],
                'offensive_skill_4': offensive_skills[3],
                'offensive_skill_5': offensive_skills[4],
                'defensive_skill_1': defensive_skills[0],
                'defensive_skill_2': defensive_skills[1],
                'defensive_skill_3': defensive_skills[2],
                'defensive_skill_4': defensive_skills[3],
                'defensive_skill_5': defensive_skills[4],
                'offensive_supercluster': offensive_supercluster,
                'defensive_supercluster': defensive_supercluster,
                'outcome': outcome
            }
            
            data.append(possession)
        
        self.synthetic_data = pd.DataFrame(data)
        return self.synthetic_data
    
    def _calculate_archetype_effect(self, off_archetypes: np.ndarray, def_archetypes: np.ndarray) -> float:
        """Calculate archetype interaction effects."""
        # Simplified archetype effects
        # 0: Scoring Wings, 1: Non-Shooting Defensive Bigs, 2: Offensive Bigs, etc.
        
        effect = 0.0
        
        # Offensive archetype effects
        for arch in off_archetypes:
            if arch == 0:  # Scoring Wings - good for offense
                effect += 0.2
            elif arch == 1:  # Non-Shooting Defensive Bigs - bad for offense
                effect -= 0.1
            elif arch == 2:  # Offensive Bigs - good for offense
                effect += 0.15
            elif arch == 5:  # 3&D - good for offense
                effect += 0.1
        
        # Defensive archetype effects
        for arch in def_archetypes:
            if arch == 1:  # Non-Shooting Defensive Bigs - good for defense
                effect -= 0.2
            elif arch == 6:  # Defensive Minded Guards - good for defense
                effect -= 0.15
            elif arch == 0:  # Scoring Wings - bad for defense
                effect += 0.1
        
        return effect
    
    def _calculate_supercluster_effect(self, off_supercluster: int, def_supercluster: int) -> float:
        """Calculate lineup supercluster interaction effects."""
        # Simplified supercluster effects
        # 0: Three-Point Symphony, 1: Half-Court Individual Shot Creators, etc.
        
        effect = 0.0
        
        # Offensive supercluster effects
        if off_supercluster == 0:  # Three-Point Symphony - good for offense
            effect += 0.3
        elif off_supercluster == 1:  # Half-Court Individual Shot Creators - moderate
            effect += 0.1
        elif off_supercluster == 2:  # Slashing Offenses - good for offense
            effect += 0.2
        
        # Defensive supercluster effects
        if def_supercluster == 0:  # Three-Point Symphony - bad for defense
            effect += 0.1
        elif def_supercluster == 1:  # Half-Court Individual Shot Creators - good for defense
            effect -= 0.2
        
        return effect
    
    def build_feature_matrix(self) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Build the feature matrix for the proxy model.
        
        Returns:
            Tuple of (features, target)
        """
        if self.synthetic_data is None:
            raise ValueError("Must generate synthetic data first")
        
        # Create features for each archetype in each lineup position
        features = []
        
        for _, row in self.synthetic_data.iterrows():
            feature_row = {}
            
            # Offensive archetype features (one-hot encoded)
            for i in range(1, 6):
                for arch in range(8):
                    feature_row[f'off_arch_{i}_{arch}'] = 1 if row[f'offensive_archetype_{i}'] == arch else 0
            
            # Defensive archetype features (one-hot encoded)
            for i in range(1, 6):
                for arch in range(8):
                    feature_row[f'def_arch_{i}_{arch}'] = 1 if row[f'defensive_archetype_{i}'] == arch else 0
            
            # Skill features (summed by archetype)
            for arch in range(8):
                off_skill_sum = sum(row[f'offensive_skill_{i}'] for i in range(1, 6) 
                                  if row[f'offensive_archetype_{i}'] == arch)
                def_skill_sum = sum(row[f'defensive_skill_{i}'] for i in range(1, 6) 
                                  if row[f'defensive_archetype_{i}'] == arch)
                
                feature_row[f'off_skill_arch_{arch}'] = off_skill_sum
                feature_row[f'def_skill_arch_{arch}'] = def_skill_sum
            
            # Supercluster features
            for sc in range(6):
                feature_row[f'off_supercluster_{sc}'] = 1 if row['offensive_supercluster'] == sc else 0
                feature_row[f'def_supercluster_{sc}'] = 1 if row['defensive_supercluster'] == sc else 0
            
            features.append(feature_row)
        
        feature_df = pd.DataFrame(features)
        target = self.synthetic_data['outcome']
        
        return feature_df, target
    
    def train_proxy_model(self) -> None:
        """Train the Ridge Regression proxy model."""
        if self.synthetic_data is None:
            raise ValueError("Must generate synthetic data first")
        
        # Build feature matrix
        X, y = self.build_feature_matrix()
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Ridge Regression with non-negativity constraints
        # Note: Ridge doesn't support non-negativity directly, so we'll validate signs after
        self.model = Ridge(alpha=1.0, random_state=42)
        self.model.fit(X_scaled, y)
        
        print(f"Proxy model trained on {len(X)} synthetic possessions")
        print(f"Model R² score: {self.model.score(X_scaled, y):.3f}")
    
    def validate_semantic_correctness(self) -> List[SemanticValidationResult]:
        """
        Validate that the model makes basketball sense.
        
        Returns:
            List of validation results
        """
        if self.model is None:
            raise ValueError("Must train proxy model first")
        
        results = []
        
        # Check 1: Offensive skill should have positive impact
        result = self._validate_offensive_skill_impact()
        results.append(result)
        
        # Check 2: Defensive skill should have negative impact
        result = self._validate_defensive_skill_impact()
        results.append(result)
        
        # Check 3: Certain archetype combinations should make sense
        result = self._validate_archetype_combinations()
        results.append(result)
        
        # Check 4: Model should be able to distinguish good vs bad lineups
        result = self._validate_lineup_discrimination()
        results.append(result)
        
        # Check 5: Coefficient magnitudes should be reasonable
        result = self._validate_coefficient_magnitudes()
        results.append(result)
        
        self.validation_results = results
        return results
    
    def _validate_offensive_skill_impact(self) -> SemanticValidationResult:
        """Validate that offensive skill has positive impact."""
        # Get coefficients for offensive skill features
        feature_names = [f'off_skill_arch_{i}' for i in range(8)]
        coef_indices = [i for i, name in enumerate(self.scaler.feature_names_in_) 
                       if name in feature_names]
        
        if not coef_indices:
            return SemanticValidationResult(
                check_name="offensive_skill_impact",
                passed=False,
                message="No offensive skill features found in model"
            )
        
        offensive_coefs = [self.model.coef_[i] for i in coef_indices]
        avg_offensive_impact = np.mean(offensive_coefs)
        
        passed = avg_offensive_impact > 0
        return SemanticValidationResult(
            check_name="offensive_skill_impact",
            passed=passed,
            message=f"Average offensive skill impact: {avg_offensive_impact:.3f}",
            actual_value=avg_offensive_impact,
            expected_value=0.0,
            tolerance=0.0
        )
    
    def _validate_defensive_skill_impact(self) -> SemanticValidationResult:
        """Validate that defensive skill has negative impact."""
        # Get coefficients for defensive skill features
        feature_names = [f'def_skill_arch_{i}' for i in range(8)]
        coef_indices = [i for i, name in enumerate(self.scaler.feature_names_in_) 
                       if name in feature_names]
        
        if not coef_indices:
            return SemanticValidationResult(
                check_name="defensive_skill_impact",
                passed=False,
                message="No defensive skill features found in model"
            )
        
        defensive_coefs = [self.model.coef_[i] for i in coef_indices]
        avg_defensive_impact = np.mean(defensive_coefs)
        
        passed = avg_defensive_impact < 0
        return SemanticValidationResult(
            check_name="defensive_skill_impact",
            passed=passed,
            message=f"Average defensive skill impact: {avg_defensive_impact:.3f}",
            actual_value=avg_defensive_impact,
            expected_value=0.0,
            tolerance=0.0
        )
    
    def _validate_archetype_combinations(self) -> SemanticValidationResult:
        """Validate that archetype combinations make basketball sense."""
        # This is a simplified check - in practice, we'd test specific combinations
        # For now, just check that the model has learned some archetype effects
        
        archetype_features = [name for name in self.scaler.feature_names_in_ 
                            if 'arch_' in name and 'skill' not in name]
        
        if not archetype_features:
            return SemanticValidationResult(
                check_name="archetype_combinations",
                passed=False,
                message="No archetype features found in model"
            )
        
        # Check that some archetype coefficients are non-zero
        archetype_coef_indices = [i for i, name in enumerate(self.scaler.feature_names_in_) 
                                if name in archetype_features]
        archetype_coefs = [self.model.coef_[i] for i in archetype_coef_indices]
        non_zero_coefs = sum(1 for coef in archetype_coefs if abs(coef) > 0.01)
        
        passed = non_zero_coefs > 0
        return SemanticValidationResult(
            check_name="archetype_combinations",
            passed=passed,
            message=f"Non-zero archetype coefficients: {non_zero_coefs}/{len(archetype_coefs)}",
            actual_value=non_zero_coefs,
            expected_value=1,
            tolerance=0
        )
    
    def _validate_lineup_discrimination(self) -> SemanticValidationResult:
        """Validate that model can distinguish good vs bad lineups."""
        if self.synthetic_data is None:
            return SemanticValidationResult(
                check_name="lineup_discrimination",
                passed=False,
                message="No synthetic data available"
            )
        
        # Create test lineups: one with high offensive skill, one with low
        high_skill_lineup = self.synthetic_data.copy()
        high_skill_lineup['offensive_skill_1'] = 3.0
        high_skill_lineup['offensive_skill_2'] = 3.0
        high_skill_lineup['offensive_skill_3'] = 3.0
        high_skill_lineup['offensive_skill_4'] = 3.0
        high_skill_lineup['offensive_skill_5'] = 3.0
        
        low_skill_lineup = self.synthetic_data.copy()
        low_skill_lineup['offensive_skill_1'] = -3.0
        low_skill_lineup['offensive_skill_2'] = -3.0
        low_skill_lineup['offensive_skill_3'] = -3.0
        low_skill_lineup['offensive_skill_4'] = -3.0
        low_skill_lineup['offensive_skill_5'] = -3.0
        
        # Predict outcomes
        X_high, _ = self.build_feature_matrix_from_data(high_skill_lineup)
        X_low, _ = self.build_feature_matrix_from_data(low_skill_lineup)
        
        X_high_scaled = self.scaler.transform(X_high)
        X_low_scaled = self.scaler.transform(X_low)
        
        pred_high = self.model.predict(X_high_scaled)
        pred_low = self.model.predict(X_low_scaled)
        
        avg_high = np.mean(pred_high)
        avg_low = np.mean(pred_low)
        
        passed = avg_high > avg_low
        return SemanticValidationResult(
            check_name="lineup_discrimination",
            passed=passed,
            message=f"High skill prediction: {avg_high:.3f}, Low skill prediction: {avg_low:.3f}",
            actual_value=avg_high - avg_low,
            expected_value=0.0,
            tolerance=0.0
        )
    
    def _validate_coefficient_magnitudes(self) -> SemanticValidationResult:
        """Validate that coefficient magnitudes are reasonable."""
        max_coef = np.max(np.abs(self.model.coef_))
        
        # Coefficients should not be extremely large (indicating overfitting)
        passed = max_coef < 10.0
        
        return SemanticValidationResult(
            check_name="coefficient_magnitudes",
            passed=passed,
            message=f"Maximum coefficient magnitude: {max_coef:.3f}",
            actual_value=max_coef,
            expected_value=10.0,
            tolerance=0.0
        )
    
    def build_feature_matrix_from_data(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Build feature matrix from arbitrary data (for testing)."""
        # This is a simplified version - in practice, we'd need to handle
        # the full feature engineering pipeline
        features = []
        
        for _, row in data.iterrows():
            feature_row = {}
            
            # Offensive archetype features
            for i in range(1, 6):
                for arch in range(8):
                    feature_row[f'off_arch_{i}_{arch}'] = 1 if row[f'offensive_archetype_{i}'] == arch else 0
            
            # Defensive archetype features
            for i in range(1, 6):
                for arch in range(8):
                    feature_row[f'def_arch_{i}_{arch}'] = 1 if row[f'defensive_archetype_{i}'] == arch else 0
            
            # Skill features
            for arch in range(8):
                off_skill_sum = sum(row[f'offensive_skill_{i}'] for i in range(1, 6) 
                                  if row[f'offensive_archetype_{i}'] == arch)
                def_skill_sum = sum(row[f'defensive_skill_{i}'] for i in range(1, 6) 
                                  if row[f'defensive_archetype_{i}'] == arch)
                
                feature_row[f'off_skill_arch_{arch}'] = off_skill_sum
                feature_row[f'def_skill_arch_{arch}'] = def_skill_sum
            
            # Supercluster features
            for sc in range(6):
                feature_row[f'off_supercluster_{sc}'] = 1 if row['offensive_supercluster'] == sc else 0
                feature_row[f'def_supercluster_{sc}'] = 1 if row['defensive_supercluster'] == sc else 0
            
            features.append(feature_row)
        
        feature_df = pd.DataFrame(features)
        target = data['outcome']
        
        return feature_df, target
    
    def generate_validation_report(self) -> str:
        """Generate a human-readable validation report."""
        if not self.validation_results:
            return "No validation results available. Run validate_semantic_correctness() first."
        
        report_lines = ["Semantic Validation Report"]
        report_lines.append("=" * 50)
        
        all_passed = all(result.passed for result in self.validation_results)
        status = "✅ PASSED" if all_passed else "❌ FAILED"
        report_lines.append(f"Overall Status: {status}")
        report_lines.append("")
        
        for result in self.validation_results:
            status = "✅" if result.passed else "❌"
            report_lines.append(f"{status} {result.check_name}: {result.message}")
        
        return "\n".join(report_lines)


def run_semantic_prototype() -> bool:
    """
    Run the complete semantic prototype validation.
    
    Returns:
        True if all validations pass, False otherwise
    """
    print("Running Semantic Prototype Validation...")
    print("=" * 50)
    
    # Initialize prototype
    prototype = SemanticPrototype()
    
    # Generate synthetic data
    print("Generating synthetic data...")
    prototype.generate_synthetic_data(n_possessions=5000)
    print(f"Generated {len(prototype.synthetic_data)} synthetic possessions")
    
    # Train proxy model
    print("Training proxy model...")
    prototype.train_proxy_model()
    
    # Validate semantic correctness
    print("Validating semantic correctness...")
    results = prototype.validate_semantic_correctness()
    
    # Generate report
    report = prototype.generate_validation_report()
    print("\n" + report)
    
    # Save report to file
    with open("semantic_prototype_report.md", "w") as f:
        f.write(report)
    
    # Return success status
    all_passed = all(result.passed for result in results)
    return all_passed


if __name__ == "__main__":
    """Run semantic prototype from command line."""
    success = run_semantic_prototype()
    
    if success:
        print("\n✅ Semantic prototype validation PASSED")
        print("The analytical logic makes basketball sense. Safe to proceed with real data.")
    else:
        print("\n❌ Semantic prototype validation FAILED")
        print("The analytical logic has issues. Review and fix before proceeding with real data.")
        exit(1)
