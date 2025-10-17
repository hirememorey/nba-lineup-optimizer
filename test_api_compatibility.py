#!/usr/bin/env python3
"""
Phase 1.1.3: Minimal API Compatibility Test
Test 2018-19 vs 2022-23 API responses to identify potential issues
"""

import requests
import json
import sys
from datetime import datetime

def test_api_endpoint(season, endpoint_name, url_template, params_template):
    """Test a single API endpoint for a given season"""
    print(f"\n=== Testing {endpoint_name} for {season} ===")
    
    # Update parameters with season
    params = params_template.copy()
    params['Season'] = season
    
    # Make request
    try:
        response = requests.get(url_template, params=params, headers={
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
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS: {season}")
            print(f"   Status: {response.status_code}")
            print(f"   Response size: {len(response.text)} characters")
            
            # Check response structure
            if 'resultSets' in data:
                print(f"   Result sets: {len(data['resultSets'])}")
                for i, result_set in enumerate(data['resultSets']):
                    if 'headers' in result_set:
                        print(f"   Set {i} headers: {len(result_set['headers'])}")
                    if 'rowSet' in result_set:
                        print(f"   Set {i} rows: {len(result_set['rowSet'])}")
            else:
                print(f"   ⚠️  No 'resultSets' in response")
                
            return data
        else:
            print(f"❌ FAILED: {season}")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return None
            
    except Exception as e:
        print(f"❌ ERROR: {season}")
        print(f"   Exception: {str(e)}")
        return None

def compare_responses(season1_data, season2_data, season1_name, season2_name):
    """Compare two API responses to identify differences"""
    if not season1_data or not season2_data:
        print(f"⚠️  Cannot compare - missing data for {season1_name} or {season2_name}")
        return
    
    print(f"\n=== Comparing {season1_name} vs {season2_name} ===")
    
    # Compare top-level structure
    if 'resultSets' in season1_data and 'resultSets' in season2_data:
        sets1 = season1_data['resultSets']
        sets2 = season2_data['resultSets']
        
        print(f"Result sets count: {len(sets1)} vs {len(sets2)}")
        
        # Compare each result set
        for i in range(min(len(sets1), len(sets2))):
            set1 = sets1[i]
            set2 = sets2[i]
            
            print(f"\nResult Set {i}:")
            
            # Compare headers
            if 'headers' in set1 and 'headers' in set2:
                headers1 = set1['headers']
                headers2 = set2['headers']
                print(f"  Headers: {len(headers1)} vs {len(headers2)}")
                
                if headers1 != headers2:
                    print(f"  ⚠️  Header mismatch!")
                    print(f"    {season1_name}: {headers1}")
                    print(f"    {season2_name}: {headers2}")
                else:
                    print(f"  ✅ Headers match")
            
            # Compare row counts
            if 'rowSet' in set1 and 'rowSet' in set2:
                rows1 = len(set1['rowSet'])
                rows2 = len(set2['rowSet'])
                print(f"  Rows: {rows1} vs {rows2}")
                
                if abs(rows1 - rows2) > 50:  # Allow some variance
                    print(f"  ⚠️  Significant row count difference!")
                else:
                    print(f"  ✅ Row counts similar")
    else:
        print("⚠️  Cannot compare - missing 'resultSets' in one or both responses")

def main():
    print("Phase 1.1.3: API Compatibility Test")
    print("=" * 50)
    
    # Test parameters for player stats endpoint
    url_template = "https://stats.nba.com/stats/leaguedashplayerptshot"
    params_template = {
        'CloseDefDistRange': '',
        'College': '',
        'Conference': '',
        'Country': '',
        'DateFrom': '',
        'DateTo': '',
        'Division': '',
        'DraftPick': '',
        'DraftYear': '',
        'Height': '',
        'ISTRound': '',
        'LastNGames': '0',
        'LeagueID': '00',
        'Location': '',
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
        'SeasonSegment': '',
        'SeasonType': 'Regular Season',
        'ShotClockRange': '',
        'ShotDistRange': '',
        'StarterBench': '',
        'TeamID': '0',
        'TouchTimeRange': '',
        'VsConference': '',
        'VsDivision': '',
        'Weight': '',
        'GeneralRange': 'Overall',
        'DribbleRange': '',
        'GameScope': ''
    }
    
    # Test both seasons
    season_2022_23_data = test_api_endpoint('2022-23', 'Player Stats', url_template, params_template)
    season_2018_19_data = test_api_endpoint('2018-19', 'Player Stats', url_template, params_template)
    
    # Compare responses
    compare_responses(season_2022_23_data, season_2018_19_data, '2022-23', '2018-19')
    
    # Test a different endpoint - games
    print(f"\n{'='*50}")
    print("Testing Games endpoint...")
    
    games_url = "https://stats.nba.com/stats/leaguegamefinder"
    games_params = {
        'Season': '2022-23',
        'SeasonType': 'Regular Season',
        'PlayerOrTeam': 'T',
        'LeagueID': '00'
    }
    
    games_2022_23 = test_api_endpoint('2022-23', 'Games', games_url, games_params)
    games_2018_19 = test_api_endpoint('2018-19', 'Games', games_url, games_params)
    
    compare_responses(games_2022_23, games_2018_19, '2022-23 Games', '2018-19 Games')
    
    print(f"\n{'='*50}")
    print("API Compatibility Test Complete")
    print("Check output above for any warnings or errors")

if __name__ == "__main__":
    main()
