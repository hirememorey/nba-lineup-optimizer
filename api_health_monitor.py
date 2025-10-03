#!/usr/bin/env python3
"""
API Health Monitor for NBA Lineup Optimizer
Validates external dependencies before pipeline execution

This script tests all critical NBA Stats API endpoints to ensure they are
working and returning the expected data structure before running the pipeline.
"""

import requests
import json
import yaml
from pathlib import Path
from datetime import datetime
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_health_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class APIHealthMonitor:
    def __init__(self, config_file="api_endpoints.yml"):
        self.config_file = config_file
        self.endpoints = {}
        self.health_results = {}
        
    def load_endpoint_config(self):
        """Load API endpoint configuration from YAML file."""
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r') as f:
                    self.endpoints = yaml.safe_load(f)
                logger.info(f"Loaded endpoint configuration from {self.config_file}")
            else:
                # Create default configuration if file doesn't exist
                self._create_default_config()
                logger.info(f"Created default configuration at {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to load endpoint configuration: {e}")
            return False
        return True
    
    def _create_default_config(self):
        """Create default API endpoint configuration."""
        default_config = {
            'endpoints': {
                'shot_locations': {
                    'url': 'https://stats.nba.com/stats/leaguedashplayershotlocations',
                    'method': 'GET',
                    'status': 'active',
                    'description': 'Player shot locations by distance range',
                    'required_params': {
                        'College': '',
                        'Conference': '',
                        'Country': '',
                        'DateFrom': '',
                        'DateTo': '',
                        'DistanceRange': '5ft Range',
                        'Division': '',
                        'DraftPick': '',
                        'DraftYear': '',
                        'GameScope': '',
                        'GameSegment': '',
                        'Height': '',
                        'ISTRound': '',
                        'LastNGames': '0',
                        'Location': '',
                        'MeasureType': 'Base',
                        'Month': '0',
                        'OpponentTeamID': '0',
                        'Outcome': '',
                        'PORound': '0',
                        'PaceAdjust': 'N',
                        'PerMode': 'PerGame',
                        'Period': '0',
                        'PlayerExperience': '',
                        'PlayerPosition': '',
                        'PlusMinus': 'N',
                        'Rank': 'N',
                        'Season': '2024-25',
                        'SeasonSegment': '',
                        'SeasonType': 'Regular Season',
                        'ShotClockRange': '',
                        'StarterBench': '',
                        'TeamID': '0',
                        'VsConference': '',
                        'VsDivision': '',
                        'Weight': ''
                    },
                    'expected_fields': [
                        'PLAYER_ID', 'PLAYER_NAME', 'TEAM_ID', 'TEAM_ABBREVIATION',
                        'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT',
                        'RESTRICTED_AREA_FGM', 'RESTRICTED_AREA_FGA', 'RESTRICTED_AREA_FG_PCT',
                        'IN_THE_PAINT_NON_RA_FGM', 'IN_THE_PAINT_NON_RA_FGA', 'IN_THE_PAINT_NON_RA_FG_PCT',
                        'MID_RANGE_FGM', 'MID_RANGE_FGA', 'MID_RANGE_FG_PCT',
                        'LEFT_CORNER_3_FGM', 'LEFT_CORNER_3_FGA', 'LEFT_CORNER_3_FG_PCT',
                        'RIGHT_CORNER_3_FGM', 'RIGHT_CORNER_3_FGA', 'RIGHT_CORNER_3_FG_PCT',
                        'ABOVE_THE_BREAK_3_FGM', 'ABOVE_THE_BREAK_3_FGA', 'ABOVE_THE_BREAK_3_FG_PCT'
                    ]
                },
                'player_tracking': {
                    'url': 'https://stats.nba.com/stats/leaguedashptstats',
                    'method': 'GET',
                    'status': 'active',
                    'description': 'Player tracking statistics',
                    'required_params': {
                        'Season': '2024-25',
                        'SeasonType': 'Regular Season',
                        'PerMode': 'PerGame',
                        'PtMeasureType': 'Drives'
                    },
                    'expected_fields': [
                        'PLAYER_ID', 'PLAYER_NAME', 'TEAM_ID', 'TEAM_ABBREVIATION',
                        'DRIVES', 'DRIVE_FGA', 'DRIVE_FG_PCT', 'DRIVE_PTS'
                    ]
                },
                'catch_shoot': {
                    'url': 'https://stats.nba.com/stats/leaguedashplayershotlocations',
                    'method': 'GET',
                    'status': 'active',
                    'description': 'Catch and shoot statistics',
                    'required_params': {
                        'Season': '2024-25',
                        'SeasonType': 'Regular Season',
                        'PerMode': 'PerGame',
                        'MeasureType': 'CatchShoot'
                    },
                    'expected_fields': [
                        'PLAYER_ID', 'PLAYER_NAME', 'TEAM_ID', 'TEAM_ABBREVIATION',
                        'CATCH_SHOOT_FGM', 'CATCH_SHOOT_FGA', 'CATCH_SHOOT_FG_PCT'
                    ]
                }
            },
            'headers': {
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Origin': 'https://www.nba.com',
                'Pragma': 'no-cache',
                'Referer': 'https://www.nba.com/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
                'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"'
            },
            'timeout': 30,
            'retry_attempts': 3
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
    
    def test_endpoint(self, endpoint_name, endpoint_config):
        """Test a single API endpoint."""
        logger.info(f"Testing endpoint: {endpoint_name}")
        
        try:
            # Prepare request
            url = endpoint_config['url']
            params = endpoint_config.get('required_params', {})
            headers = self.endpoints.get('headers', {})
            timeout = self.endpoints.get('timeout', 30)
            
            # Make request
            logger.info(f"  Making request to: {url}")
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            
            # Check response status
            if response.status_code != 200:
                logger.error(f"  HTTP {response.status_code}: {response.text}")
                return {
                    'status': 'FAILED',
                    'error': f'HTTP {response.status_code}',
                    'details': response.text[:200]
                }
            
            # Parse JSON response
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"  JSON decode error: {e}")
                return {
                    'status': 'FAILED',
                    'error': 'Invalid JSON response',
                    'details': str(e)
                }
            
            # Check response structure
            if 'resultSets' not in data:
                logger.error("  Missing 'resultSets' in response")
                return {
                    'status': 'FAILED',
                    'error': 'Invalid response structure',
                    'details': 'Missing resultSets field'
                }
            
            # Check if we have data
            result_sets = data['resultSets']
            
            # Handle both dict and list formats for resultSets
            if isinstance(result_sets, dict):
                # Single result set as dictionary
                if 'rowSet' not in result_sets:
                    logger.error("  Missing 'rowSet' in result set")
                    return {
                        'status': 'FAILED',
                        'error': 'Invalid result set structure',
                        'details': 'Missing rowSet field'
                    }
                rows = result_sets['rowSet']
                headers = result_sets.get('headers', [])
            elif isinstance(result_sets, list):
                # Multiple result sets as list
                if not result_sets or len(result_sets) == 0:
                    logger.error("  No result sets in response")
                    return {
                        'status': 'FAILED',
                        'error': 'No data returned',
                        'details': 'Empty resultSets array'
                    }
                
                first_result = result_sets[0]
                if 'rowSet' not in first_result:
                    logger.error("  Missing 'rowSet' in first result set")
                    return {
                        'status': 'FAILED',
                        'error': 'Invalid result set structure',
                        'details': 'Missing rowSet field'
                    }
                rows = first_result['rowSet']
                headers = first_result.get('headers', [])
            else:
                logger.error("  Invalid resultSets format")
                return {
                    'status': 'FAILED',
                    'error': 'Invalid resultSets format',
                    'details': f'Expected dict or list, got {type(result_sets)}'
                }
            
            # Check data rows
            if not rows or len(rows) == 0:
                logger.error("  No data rows in response")
                return {
                    'status': 'FAILED',
                    'error': 'No data rows',
                    'details': 'Empty rowSet array'
                }
            
            # Check expected fields
            expected_fields = endpoint_config.get('expected_fields', [])
            missing_fields = []
            
            for field in expected_fields:
                if field not in headers:
                    missing_fields.append(field)
            
            if missing_fields:
                logger.warning(f"  Missing expected fields: {missing_fields}")
            
            # Success
            logger.info(f"  ✓ Success: {len(rows)} rows, {len(headers)} columns")
            return {
                'status': 'SUCCESS',
                'row_count': len(rows),
                'column_count': len(headers),
                'missing_fields': missing_fields,
                'sample_data': rows[0] if rows else None
            }
            
        except requests.exceptions.Timeout:
            logger.error(f"  Request timeout after {timeout} seconds")
            return {
                'status': 'FAILED',
                'error': 'Request timeout',
                'details': f'Timeout after {timeout} seconds'
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"  Request error: {e}")
            return {
                'status': 'FAILED',
                'error': 'Request failed',
                'details': str(e)
            }
        except Exception as e:
            logger.error(f"  Unexpected error: {e}")
            return {
                'status': 'FAILED',
                'error': 'Unexpected error',
                'details': str(e)
            }
    
    def run_health_check(self):
        """Run health check on all active endpoints."""
        logger.info("Starting API health check...")
        
        if not self.load_endpoint_config():
            logger.error("Failed to load endpoint configuration")
            return False
        
        endpoints = self.endpoints.get('endpoints', {})
        active_endpoints = {k: v for k, v in endpoints.items() if v.get('status') == 'active'}
        
        if not active_endpoints:
            logger.error("No active endpoints found in configuration")
            return False
        
        logger.info(f"Testing {len(active_endpoints)} active endpoints...")
        
        all_passed = True
        
        for endpoint_name, endpoint_config in active_endpoints.items():
            result = self.test_endpoint(endpoint_name, endpoint_config)
            self.health_results[endpoint_name] = result
            
            if result['status'] != 'SUCCESS':
                all_passed = False
        
        # Generate summary
        self._generate_summary()
        
        return all_passed
    
    def _generate_summary(self):
        """Generate health check summary."""
        total_endpoints = len(self.health_results)
        successful_endpoints = sum(1 for r in self.health_results.values() if r['status'] == 'SUCCESS')
        failed_endpoints = total_endpoints - successful_endpoints
        
        logger.info("=" * 50)
        logger.info("API HEALTH CHECK SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total endpoints tested: {total_endpoints}")
        logger.info(f"Successful: {successful_endpoints}")
        logger.info(f"Failed: {failed_endpoints}")
        logger.info("=" * 50)
        
        if failed_endpoints > 0:
            logger.error("FAILED ENDPOINTS:")
            for endpoint, result in self.health_results.items():
                if result['status'] != 'SUCCESS':
                    logger.error(f"  {endpoint}: {result['error']}")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"api_health_check_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_endpoints': total_endpoints,
                    'successful': successful_endpoints,
                    'failed': failed_endpoints,
                    'all_passed': failed_endpoints == 0
                },
                'results': self.health_results
            }, f, indent=2)
        
        logger.info(f"Detailed results saved to: {results_file}")

def main():
    """Main execution function."""
    monitor = APIHealthMonitor()
    
    success = monitor.run_health_check()
    
    if success:
        logger.info("All API endpoints are healthy!")
        sys.exit(0)
    else:
        logger.error("One or more API endpoints failed health check!")
        sys.exit(1)

if __name__ == "__main__":
    main()
