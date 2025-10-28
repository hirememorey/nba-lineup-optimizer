#!/usr/bin/env python3
"""
Minimal Phase 3 Validation Predictor

This script loads trained coefficients and validation data, then computes predictions
using the simplified model: y = beta_0 + z_off × beta_off - z_def × beta_def
"""

import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_coefficients(coeff_path: str) -> np.ndarray:
    """Load coefficients from CSV by row index (0-17)."""
    df = pd.read_csv(coeff_path)

    # Extract means into array (row 0 = beta_0, rows 1-8 = beta_off[1-8], rows 9-16 = beta_def[1-8])
    coefficients = df['mean'].values

    if len(coefficients) != 17:
        raise ValueError(f"Expected 17 coefficients, got {len(coefficients)}")

    logging.info(f"Loaded {len(coefficients)} coefficients: beta_0={coefficients[0]:.6f}")
    return coefficients

def load_validation_data(data_path: str) -> pd.DataFrame:
    """Load validation data with outcome and Z-matrix columns."""
    df = pd.read_csv(data_path)

    # Verify required columns exist
    z_off_cols = [f'z_off_{i}' for i in range(8)]
    z_def_cols = [f'z_def_{i}' for i in range(8)]
    required_cols = ['outcome'] + z_off_cols + z_def_cols

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    logging.info(f"Loaded {len(df)} validation possessions")
    return df

def compute_predictions(coefficients: np.ndarray, validation_data: pd.DataFrame) -> np.ndarray:
    """Compute predictions using the simplified model formula."""

    # Extract beta_0, beta_off[1-8], beta_def[1-8]
    beta_0 = coefficients[0]
    beta_off = coefficients[1:9]  # indices 1-8 in Stan → array indices 0-7
    beta_def = coefficients[9:17]  # indices 9-16 in Stan → array indices 0-7

    # Extract Z-matrices (8 columns each, indices 0-7)
    z_off_cols = [f'z_off_{i}' for i in range(8)]
    z_def_cols = [f'z_def_{i}' for i in range(8)]

    z_off = validation_data[z_off_cols].values
    z_def = validation_data[z_def_cols].values

    # Compute predictions: beta_0 + Σ(z_off[i] * beta_off[i]) - Σ(z_def[i] * beta_def[i])
    predictions = beta_0 + np.sum(z_off * beta_off, axis=1) - np.sum(z_def * beta_def, axis=1)

    logging.info(f"Prediction range: [{predictions.min():.3f}, {predictions.max():.3f}]")
    return predictions

def compute_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
    """Compute MSE, MAE, and R-squared."""
    mse = np.mean((actual - predicted) ** 2)
    mae = np.mean(np.abs(actual - predicted))

    # R-squared: 1 - SS_res / SS_tot
    ss_res = np.sum((actual - predicted) ** 2)
    ss_tot = np.sum((actual - np.mean(actual)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

    return {
        'mse': mse,
        'mae': mae,
        'r2': r2,
        'n_samples': len(actual)
    }

def main():
    """Run Phase 3 validation predictions."""

    # File paths
    coeff_path = "multi_season_coefficients.csv"
    data_path = "validation_2022_23_data.csv"
    output_path = "validation_2022_23_predictions.csv"

    try:
        # Load data
        logging.info("Loading coefficients...")
        coefficients = load_coefficients(coeff_path)

        logging.info("Loading validation data...")
        validation_data = load_validation_data(data_path)

        # Compute predictions
        logging.info("Computing predictions...")
        predictions = compute_predictions(coefficients, validation_data)

        # Compute metrics
        actual = validation_data['outcome'].values
        metrics = compute_metrics(actual, predictions)

        # Save results
        results_df = pd.DataFrame({
            'actual': actual,
            'predicted': predictions,
            'residual': actual - predictions
        })
        results_df.to_csv(output_path, index=False)

        # Print metrics
        logging.info("=== VALIDATION RESULTS ===")
        logging.info(f"MSE: {metrics['mse']:.6f}")
        logging.info(f"MAE: {metrics['mae']:.6f}")
        logging.info(f"R²: {metrics['r2']:.6f}")
        logging.info(f"Samples: {metrics['n_samples']:,}")
        logging.info(f"Results saved to: {output_path}")

    except Exception as e:
        logging.error(f"Prediction failed: {e}")
        raise

if __name__ == "__main__":
    main()

