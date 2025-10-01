#!/usr/bin/env python3
"""
API Contract Tests

This module contains automated tests to enforce the contracts between
data producers and consumers in the NBA stats system. These tests prevent
the contract drift that caused the original verification failures.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.nba_stats.api.nba_stats_client import NBAStatsClient
from src.nba_stats.api.data_fetcher import create_data_fetcher

class TestAPIContracts:
    """Test suite for API contract enforcement."""
    
    @pytest.fixture
    def client(self):
        """Provide NBAStatsClient instance for tests."""
        return NBAStatsClient()
    
    @pytest.fixture
    def data_fetcher(self):
        """Provide DataFetcher instance for tests."""
        return create_data_fetcher()
    
    def test_get_players_with_stats_structure(self, client):
        """Test that get_players_with_stats returns expected structure."""
        players = client.get_players_with_stats("2024-25")
        
        assert isinstance(players, list), "get_players_with_stats should return a list"
        assert len(players) > 0, "Should return at least one player"
        
        # Check structure of first player
        first_player = players[0]
        expected_keys = {"playerId", "playerName", "teamId"}
        actual_keys = set(first_player.keys())
        
        assert actual_keys == expected_keys, f"Expected keys {expected_keys}, got {actual_keys}"
        
        # Verify data types
        assert isinstance(first_player["playerId"], int), "playerId should be int"
        assert isinstance(first_player["playerName"], str), "playerName should be str"
        assert isinstance(first_player["teamId"], int), "teamId should be int"
    
    def test_get_player_stats_structure(self, client):
        """Test that get_player_stats returns expected structure."""
        # Test with LeBron James (player_id: 2544)
        stats = client.get_player_stats(2544, "2024-25")
        
        assert isinstance(stats, dict), "get_player_stats should return a dict"
        assert "resultSets" in stats, "Response should contain resultSets"
        
        result_sets = stats["resultSets"]
        assert isinstance(result_sets, list), "resultSets should be a list"
        assert len(result_sets) > 0, "Should have at least one result set"
        
        first_set = result_sets[0]
        assert "headers" in first_set, "Result set should have headers"
        assert "rowSet" in first_set, "Result set should have rowSet"
        
        headers = first_set["headers"]
        rows = first_set["rowSet"]
        
        assert isinstance(headers, list), "Headers should be a list"
        assert isinstance(rows, list), "RowSet should be a list"
        assert len(rows) > 0, "Should have at least one row"
        
        # Verify row structure matches headers
        if rows:
            first_row = rows[0]
            assert len(first_row) == len(headers), "Row length should match headers length"
    
    def test_data_fetcher_metric_structure(self, data_fetcher):
        """Test that data fetcher returns expected metric structure."""
        # Test with a known metric
        metric_data = data_fetcher.fetch_metric_data("FTPCT", "2024-25")
        
        assert isinstance(metric_data, dict), "fetch_metric_data should return a dict"
        assert len(metric_data) > 0, "Should return data for at least one player"
        
        # Check structure of first entry
        first_player_id, first_value = next(iter(metric_data.items()))
        
        assert isinstance(first_player_id, (str, int)), "Player ID should be string or int"
        assert isinstance(first_value, (int, float)), "Metric value should be numeric"
        
        # Verify percentage metrics are in valid range
        if first_value is not None:
            assert 0 <= float(first_value) <= 1, f"Percentage metric should be 0-1, got {first_value}"
    
    def test_data_fetcher_available_metrics(self, data_fetcher):
        """Test that data fetcher provides available metrics."""
        available_metrics = data_fetcher.get_available_metrics()
        
        assert isinstance(available_metrics, list), "get_available_metrics should return a list"
        assert len(available_metrics) > 0, "Should have at least one available metric"
        
        # Check that all metrics are strings
        for metric in available_metrics:
            assert isinstance(metric, str), f"Metric name should be string, got {type(metric)}"
    
    def test_critical_metrics_availability(self, data_fetcher):
        """Test that critical metrics are available through data fetcher."""
        critical_metrics = ["FTPCT", "TSPCT", "THPAr", "FTr", "TRBPCT"]
        
        for metric in critical_metrics:
            data = data_fetcher.fetch_metric_data(metric, "2024-25")
            assert data is not None, f"Critical metric {metric} should be available"
            assert len(data) > 0, f"Critical metric {metric} should have data"
    
    def test_contract_consistency(self, client, data_fetcher):
        """Test that both API client and data fetcher work together consistently."""
        # Get players from API client
        players = client.get_players_with_stats("2024-25")
        player_ids = {str(p["playerId"]) for p in players}
        
        # Get metric data from data fetcher
        metric_data = data_fetcher.fetch_metric_data("FTPCT", "2024-25")
        metric_player_ids = {str(pid) for pid in metric_data.keys()}
        
        # There should be some overlap between the two
        overlap = player_ids.intersection(metric_player_ids)
        assert len(overlap) > 0, f"API client and data fetcher should have overlapping player IDs. API: {len(player_ids)}, Metric: {len(metric_player_ids)}, Overlap: {len(overlap)}"
    
    def test_percentage_metrics_validation(self, data_fetcher):
        """Test that percentage metrics are properly validated."""
        percentage_metrics = ["FTPCT", "TSPCT"]
        
        for metric in percentage_metrics:
            data = data_fetcher.fetch_metric_data(metric, "2024-25")
            
            if data:
                invalid_count = 0
                for player_id, value in data.items():
                    if value is not None:
                        try:
                            float_val = float(value)
                            if not (0 <= float_val <= 1):
                                invalid_count += 1
                        except (ValueError, TypeError):
                            invalid_count += 1
                
                # Allow for some invalid values due to data quality issues
                invalid_percentage = (invalid_count / len(data)) * 100
                assert invalid_percentage < 10, f"Too many invalid percentage values for {metric}: {invalid_percentage:.1f}%"
    
    def test_data_completeness(self, data_fetcher):
        """Test that data is sufficiently complete for analysis."""
        test_metrics = ["FTPCT", "TSPCT", "THPAr"]
        
        for metric in test_metrics:
            data = data_fetcher.fetch_metric_data(metric, "2024-25")
            
            assert data is not None, f"Metric {metric} should be available"
            assert len(data) >= 100, f"Metric {metric} should have at least 100 players"
            
            # Check for reasonable null rate
            null_count = sum(1 for value in data.values() if value is None)
            null_percentage = (null_count / len(data)) * 100
            assert null_percentage < 50, f"Too many null values for {metric}: {null_percentage:.1f}%"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
