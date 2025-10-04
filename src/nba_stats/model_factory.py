"""
Model Factory

This module provides a factory pattern for creating and managing different
model evaluators. It handles the differences between model types and provides
a unified interface for the UI components.

Key Features:
1. Unified model creation interface
2. Result normalization for UI compatibility
3. Error handling and fallback mechanisms
4. Model type validation
"""

from typing import Dict, List, Any, Optional, Union
from enum import Enum
import logging

# Import the model evaluators
from .model_evaluator import ModelEvaluator, LineupEvaluation
from .simple_model_evaluator import SimpleModelEvaluator, SimpleLineupEvaluation

# Set up logging
logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Enumeration of available model types."""
    ORIGINAL = "original"
    SIMPLE = "simple"

class NormalizedLineupEvaluation:
    """Normalized result object that works with any model type."""
    
    def __init__(self, 
                 predicted_outcome: float,
                 player_ids: List[int],
                 player_names: List[str],
                 archetype_ids: List[int],
                 archetype_names: List[str],
                 skill_scores: Dict[str, Any],
                 model_type: str = "unknown"):
        self.predicted_outcome = predicted_outcome
        self.player_ids = player_ids
        self.player_names = player_names
        self.archetype_ids = archetype_ids
        self.archetype_names = archetype_names
        self.skill_scores = skill_scores
        self.model_type = model_type

class ModelFactory:
    """Factory for creating and managing model evaluators."""
    
    @staticmethod
    def create_evaluator(model_type: Union[str, ModelType]) -> Union[ModelEvaluator, SimpleModelEvaluator]:
        """
        Create a model evaluator instance.
        
        Args:
            model_type: Type of model to create ("original" or "simple")
            
        Returns:
            Model evaluator instance
            
        Raises:
            ValueError: If model_type is not recognized
            Exception: If model initialization fails
        """
        # Normalize model type
        if isinstance(model_type, str):
            model_type = model_type.lower()
            if model_type == "original":
                model_type = ModelType.ORIGINAL
            elif model_type == "simple":
                model_type = ModelType.SIMPLE
            else:
                raise ValueError(f"Unknown model type: {model_type}. Must be 'original' or 'simple'")
        
        try:
            if model_type == ModelType.ORIGINAL:
                logger.info("Creating original ModelEvaluator")
                return ModelEvaluator()
            elif model_type == ModelType.SIMPLE:
                logger.info("Creating SimpleModelEvaluator")
                return SimpleModelEvaluator()
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
        except Exception as e:
            logger.error(f"Failed to create {model_type.value} evaluator: {e}")
            raise
    
    @staticmethod
    def normalize_result(result: Union[LineupEvaluation, SimpleLineupEvaluation]) -> NormalizedLineupEvaluation:
        """
        Convert any model result to a normalized format for UI consumption.
        
        Args:
            result: Result from any model evaluator
            
        Returns:
            Normalized result object
        """
        # Extract common attributes
        predicted_outcome = result.predicted_outcome
        player_ids = result.player_ids
        player_names = result.player_names
        archetype_ids = result.archetype_ids
        archetype_names = result.archetype_names
        skill_scores = result.skill_scores
        
        # Extract model type if available
        model_type = getattr(result, 'model_type', 'original')
        
        return NormalizedLineupEvaluation(
            predicted_outcome=predicted_outcome,
            player_ids=player_ids,
            player_names=player_names,
            archetype_ids=archetype_ids,
            archetype_names=archetype_names,
            skill_scores=skill_scores,
            model_type=model_type
        )
    
    @staticmethod
    def evaluate_lineup_with_fallback(lineup: List[int], 
                                    preferred_model: Union[str, ModelType] = ModelType.SIMPLE) -> NormalizedLineupEvaluation:
        """
        Evaluate a lineup with fallback to the other model if the preferred one fails.
        
        Args:
            lineup: List of player IDs
            preferred_model: Preferred model type to use first
            
        Returns:
            Normalized evaluation result
        """
        # Try preferred model first
        try:
            evaluator = ModelFactory.create_evaluator(preferred_model)
            result = evaluator.evaluate_lineup(lineup)
            logger.info(f"Successfully evaluated lineup with {preferred_model} model")
            return ModelFactory.normalize_result(result)
        except Exception as e:
            logger.warning(f"Preferred model {preferred_model} failed: {e}")
            
            # Fallback to the other model
            fallback_model = ModelType.ORIGINAL if preferred_model == ModelType.SIMPLE else ModelType.SIMPLE
            try:
                evaluator = ModelFactory.create_evaluator(fallback_model)
                result = evaluator.evaluate_lineup(lineup)
                logger.info(f"Successfully evaluated lineup with fallback {fallback_model} model")
                return ModelFactory.normalize_result(result)
            except Exception as e2:
                logger.error(f"Both models failed. Original error: {e}, Fallback error: {e2}")
                raise Exception(f"Both models failed to evaluate lineup. Last error: {e2}")
    
    @staticmethod
    def get_available_models() -> List[Dict[str, str]]:
        """
        Get list of available models with their descriptions.
        
        Returns:
            List of model information dictionaries
        """
        return [
            {
                "type": "original",
                "name": "Original Model (8-Archetype)",
                "description": "Original model with placeholder coefficients and 8-archetype system",
                "status": "stable"
            },
            {
                "type": "simple", 
                "name": "Production Model (3-Archetype)",
                "description": "Production model with real coefficients and 3-archetype system",
                "status": "production"
            }
        ]
    
    @staticmethod
    def validate_model_type(model_type: str) -> bool:
        """
        Validate if a model type is supported.
        
        Args:
            model_type: Model type to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            ModelFactory.create_evaluator(model_type)
            return True
        except (ValueError, Exception):
            return False

# Convenience functions for easy access
def create_evaluator(model_type: Union[str, ModelType]) -> Union[ModelEvaluator, SimpleModelEvaluator]:
    """Convenience function to create a model evaluator."""
    return ModelFactory.create_evaluator(model_type)

def evaluate_lineup(lineup: List[int], model_type: Union[str, ModelType] = ModelType.SIMPLE) -> NormalizedLineupEvaluation:
    """Convenience function to evaluate a lineup with a specific model."""
    evaluator = ModelFactory.create_evaluator(model_type)
    result = evaluator.evaluate_lineup(lineup)
    return ModelFactory.normalize_result(result)

def evaluate_lineup_with_fallback(lineup: List[int], preferred_model: Union[str, ModelType] = ModelType.SIMPLE) -> NormalizedLineupEvaluation:
    """Convenience function to evaluate a lineup with fallback."""
    return ModelFactory.evaluate_lineup_with_fallback(lineup, preferred_model)
