"""
Centralized Data Fetcher Module

This module provides a unified interface for fetching NBA player data from various
API endpoints, with built-in schema awareness and error handling.
"""

import logging
import time
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .nba_stats_client import NBAStatsClient
from ..utils.common_utils import logger
from .response_models import api_validator

# Add progress bar support
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

# Add retry logic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class DataType(Enum):
    """Data types for metrics."""
    COUNT = "count"
    PERCENTAGE = "percentage"
    TIME = "time"
    STRING = "string"
    CALCULATED = "calculated"
    MISSING = "missing"

@dataclass
class MetricMapping:
    """Represents a metric mapping to its API source."""
    canonical_name: str
    api_source: str
    api_column: str
    endpoint_params: Dict[str, Any]
    data_type: DataType
    required: bool
    notes: str

class DataFetcher:
    """
    Centralized data fetcher with schema awareness and error handling.
    """
    
    def __init__(self, client: Optional[NBAStatsClient] = None):
        """Initialize the data fetcher."""
        self.client = client or NBAStatsClient()
        self.metric_mappings = self._load_metric_mappings()
        self.cache = {}
        
    def _load_metric_mappings(self) -> Dict[str, MetricMapping]:
        """Load metric mappings from the definitive mapping."""
        # Import here to avoid circular imports
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
        from definitive_metric_mapping import DEFINITIVE_METRIC_MAPPING
        
        mappings = {}
        for metric, mapping_data in DEFINITIVE_METRIC_MAPPING.items():
            mappings[metric] = MetricMapping(
                canonical_name=mapping_data["canonical_name"],
                api_source=mapping_data["api_source"],
                api_column=mapping_data["api_column"],
                endpoint_params=mapping_data["endpoint_params"],
                data_type=DataType(mapping_data["data_type"]),
                required=mapping_data["required"],
                notes=mapping_data["notes"]
            )
        return mappings
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,))
    )
    def fetch_metric_data(self, metric: str, season: str = "2024-25") -> Optional[Dict[str, Any]]:
        """
        Fetch data for a specific metric.
        
        Args:
            metric: The canonical metric name
            season: The season to fetch data for
            
        Returns:
            Dictionary with player data or None if not available
        """
        if metric not in self.metric_mappings:
            logger.error(f"Unknown metric: {metric}")
            return None
            
        mapping = self.metric_mappings[metric]
        
        if mapping.data_type == DataType.MISSING:
            logger.warning(f"Metric {metric} is not available in the API: {mapping.notes}")
            return None
            
        try:
            # Add rate limiting
            time.sleep(random.uniform(0.1, 0.3))
            
            # Fetch data based on API source
            if mapping.api_source == "leaguedashplayerstats":
                return self._fetch_player_stats_data(metric, mapping, season)
            elif mapping.api_source == "leaguedashptstats":
                return self._fetch_tracking_data(metric, mapping, season)
            elif mapping.api_source == "commonplayerinfo":
                return self._fetch_player_info_data(metric, mapping)
            elif mapping.api_source == "leaguedashplayerhustlestats":
                return self._fetch_hustle_data(metric, mapping, season)
            else:
                logger.error(f"Unknown API source: {mapping.api_source}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching {metric}: {e}")
            return None
    
    def _fetch_player_stats_data(self, metric: str, mapping: MetricMapping, season: str) -> Optional[Dict[str, Any]]:
        """Fetch data from player stats endpoints."""
        try:
            if mapping.endpoint_params.get("MeasureType") == "Base":
                response = self.client.get_league_player_base_stats(
                    season=season, 
                    season_type=mapping.endpoint_params.get("SeasonType", "Regular Season")
                )
            else:  # Advanced
                response = self.client.get_league_player_advanced_stats(
                    season=season, 
                    season_type=mapping.endpoint_params.get("SeasonType", "Regular Season")
                )
            
            if not response or 'resultSets' not in response:
                logger.warning(f"No data returned for {metric}")
                return None
                
            return self._extract_player_data(response, mapping.api_column, metric)
            
        except Exception as e:
            logger.error(f"Error fetching player stats for {metric}: {e}")
            return None
    
    def _fetch_tracking_data(self, metric: str, mapping: MetricMapping, season: str) -> Optional[Dict[str, Any]]:
        """Fetch data from player tracking endpoints."""
        try:
            pt_measure_type = mapping.endpoint_params.get("PtMeasureType", "Drives")
            response = self.client.get_league_player_tracking_stats(
                season=season, 
                pt_measure_type=pt_measure_type
            )
            
            if not response or 'resultSets' not in response:
                logger.warning(f"No tracking data returned for {metric}")
                return None
                
            return self._extract_player_data(response, mapping.api_column, metric)
            
        except Exception as e:
            logger.error(f"Error fetching tracking data for {metric}: {e}")
            return None
    
    def _fetch_player_info_data(self, metric: str, mapping: MetricMapping) -> Optional[Dict[str, Any]]:
        """Fetch data from player info endpoints."""
        try:
            # For player info, we need to fetch for all players
            # This is a simplified version - in practice, you'd need to iterate through all players
            response = self.client.get_common_player_info(player_id=2544)  # LeBron as example
            
            if not response or 'resultSets' not in response:
                logger.warning(f"No player info data returned for {metric}")
                return None
                
            return self._extract_player_data(response, mapping.api_column, metric)
            
        except Exception as e:
            logger.error(f"Error fetching player info for {metric}: {e}")
            return None
    
    def _fetch_hustle_data(self, metric: str, mapping: MetricMapping, season: str) -> Optional[Dict[str, Any]]:
        """Fetch data from hustle stats endpoints."""
        try:
            response = self.client.get_league_hustle_stats(season=season)
            
            if not response or 'resultSets' not in response:
                logger.warning(f"No hustle data returned for {metric}")
                return None
                
            return self._extract_player_data(response, mapping.api_column, metric)
            
        except Exception as e:
            logger.error(f"Error fetching hustle data for {metric}: {e}")
            return None
    
    def _extract_player_data(self, response: Dict[str, Any], column_name: str, metric: str) -> Dict[str, Any]:
        """Extract player data from API response with validation."""
        try:
            # Validate the response structure first
            if not api_validator.validate_response(response):
                validation_errors = api_validator.get_validation_errors()
                logger.error(f"Response validation failed for {metric}: {validation_errors}")
                return {}
            
            result_sets = response.get('resultSets', [])
            if not result_sets:
                logger.warning(f"No result sets in response for {metric}")
                return {}
            
            # Use the first result set
            result_set = result_sets[0]
            headers = result_set.get('headers', [])
            rows = result_set.get('rowSet', [])
            
            if not headers or not rows:
                logger.warning(f"No data rows in response for {metric}")
                return {}
            
            # Find the column index
            try:
                column_index = headers.index(column_name)
            except ValueError:
                logger.warning(f"Column {column_name} not found in response for {metric}")
                return {}
            
            # Extract player data with validation
            player_data = {}
            for i, row in enumerate(rows):
                if len(row) > column_index:
                    player_id = row[0] if row else None  # Assuming first column is player ID
                    if player_id:
                        try:
                            # Validate the data type
                            value = row[column_index]
                            if value is not None:
                                # Basic type validation based on metric type
                                mapping = self.metric_mappings.get(metric)
                                if mapping and mapping.data_type == DataType.PERCENTAGE:
                                    if not (0 <= float(value) <= 1):
                                        logger.warning(f"Invalid percentage value for {metric}, player {player_id}: {value}")
                                        continue
                                elif mapping and mapping.data_type == DataType.COUNT:
                                    if float(value) < 0:
                                        logger.warning(f"Invalid count value for {metric}, player {player_id}: {value}")
                                        continue
                            
                            player_data[player_id] = value
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Invalid data type for {metric}, player {player_id}, row {i}: {e}")
                            continue
            
            logger.info(f"Extracted {len(player_data)} player records for {metric}")
            return player_data
            
        except Exception as e:
            logger.error(f"Error extracting player data for {metric}: {e}")
            return {}
    
    def fetch_all_available_metrics(self, season: str = "2024-25") -> Dict[str, Dict[str, Any]]:
        """
        Fetch data for all available metrics.
        
        Args:
            season: The season to fetch data for
            
        Returns:
            Dictionary mapping metric names to their player data
        """
        logger.info("Fetching data for all available metrics...")
        
        all_data = {}
        available_metrics = [metric for metric, mapping in self.metric_mappings.items() 
                           if mapping.data_type != DataType.MISSING]
        
        # Add progress bar if tqdm is available
        if TQDM_AVAILABLE:
            metric_iterator = tqdm(enumerate(available_metrics, 1), 
                                 total=len(available_metrics),
                                 desc="Fetching metrics",
                                 unit="metric")
        else:
            metric_iterator = enumerate(available_metrics, 1)
            
        for i, metric in metric_iterator:
            if not TQDM_AVAILABLE:  # Only log if no progress bar
                logger.info(f"Fetching {metric} ({i}/{len(available_metrics)})")
            
            data = self.fetch_metric_data(metric, season)
            if data:
                all_data[metric] = data
            else:
                logger.warning(f"Failed to fetch data for {metric}")
        
        logger.info(f"Successfully fetched data for {len(all_data)} metrics")
        return all_data
    
    def get_missing_metrics(self) -> List[str]:
        """Get list of metrics that are missing from the API."""
        return [metric for metric, mapping in self.metric_mappings.items() 
                if mapping.data_type == DataType.MISSING]
    
    def get_available_metrics(self) -> List[str]:
        """Get list of metrics that are available in the API."""
        return [metric for metric, mapping in self.metric_mappings.items() 
                if mapping.data_type != DataType.MISSING]
    
    def validate_data_completeness(self, data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate the completeness of fetched data.
        
        Args:
            data: Dictionary mapping metric names to their player data
            
        Returns:
            Validation results
        """
        validation_results = {
            "total_metrics": len(self.metric_mappings),
            "fetched_metrics": len(data),
            "missing_metrics": [],
            "empty_metrics": [],
            "coverage_stats": {}
        }
        
        # Check for missing metrics
        for metric in self.metric_mappings:
            if metric not in data:
                validation_results["missing_metrics"].append(metric)
        
        # Check for empty metrics
        for metric, player_data in data.items():
            if not player_data:
                validation_results["empty_metrics"].append(metric)
        
        # Calculate coverage stats
        for metric, player_data in data.items():
            if player_data:
                validation_results["coverage_stats"][metric] = {
                    "player_count": len(player_data),
                    "non_null_count": sum(1 for v in player_data.values() if v is not None),
                    "coverage_pct": (sum(1 for v in player_data.values() if v is not None) / len(player_data)) * 100
                }
        
        return validation_results

def create_data_fetcher() -> DataFetcher:
    """Create a new DataFetcher instance."""
    return DataFetcher()

if __name__ == "__main__":
    # Test the data fetcher
    fetcher = create_data_fetcher()
    
    print("Available metrics:", len(fetcher.get_available_metrics()))
    print("Missing metrics:", len(fetcher.get_missing_metrics()))
    
    # Test fetching a single metric
    test_metric = "FTPCT"
    print(f"\nTesting fetch for {test_metric}...")
    data = fetcher.fetch_metric_data(test_metric)
    if data:
        print(f"Successfully fetched data for {len(data)} players")
    else:
        print("Failed to fetch data")