#!/usr/bin/env python3
"""
Enhanced Player Name Reconciliation Tool

This script handles both mapping existing players and creating new ones to achieve
100% data integrity for player salary and skill data.

Usage:
    python src/nba_stats/scripts/fix_player_names.py
"""

import os
import sys
import csv
import sqlite3
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import argparse

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from ..api.client import NBAStatsClient
from ..db.connection import get_db_connection

try:
    from rapidfuzz import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    print("Warning: rapidfuzz not available. Install with: pip install rapidfuzz")
    FUZZY_AVAILABLE = False

class PlayerReconciliationTool:
    def __init__(self, db_path: str, mapping_file: str):
        self.db_path = db_path
        self.mapping_file = mapping_file
        self.nba_client = NBAStatsClient()
        self.existing_mappings = self._load_existing_mappings()
        
    def _load_existing_mappings(self) -> Dict[str, str]:
        """Load existing mappings from the mapping file."""
        mappings = {}
        if os.path.exists(self.mapping_file):
            try:
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    # Check if file has content
                    try:
                        next(reader)  # Skip header
                    except StopIteration:
                        # Empty file, return empty mappings
                        return mappings
                    
                    for row in reader:
                        if len(row) >= 2:
                            csv_name, db_name = row[0].strip(), row[1].strip()
                            mappings[csv_name.lower()] = db_name
            except Exception as e:
                print(f"Warning: Could not load existing mappings: {e}")
        return mappings
    
    def _save_mapping(self, csv_name: str, db_name: str):
        """Save a new mapping to the mapping file."""
        # Ensure the mappings directory exists
        os.makedirs(os.path.dirname(self.mapping_file), exist_ok=True)
        
        # Check if file exists to determine if we need to write header
        file_exists = os.path.exists(self.mapping_file)
        
        with open(self.mapping_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['csv_name', 'db_name'])
            writer.writerow([csv_name, db_name])
        
        # Update in-memory mappings
        self.existing_mappings[csv_name.lower()] = db_name
        print(f"✓ Saved mapping: '{csv_name}' -> '{db_name}'")
    
    def _get_existing_players(self) -> List[Tuple[str, int]]:
        """Get all existing players from the database."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT player_name, player_id FROM Players ORDER BY player_name")
            return cursor.fetchall()
        finally:
            conn.close()
    
    def _find_fuzzy_matches(self, target_name: str, existing_players: List[Tuple[str, int]], limit: int = 5) -> List[Tuple[str, int, float]]:
        """Find fuzzy matches for a target name."""
        if not FUZZY_AVAILABLE:
            return []
        
        player_names = [player[0] for player in existing_players]
        matches = process.extract(target_name, player_names, limit=limit, scorer=fuzz.ratio)
        
        # Return matches with their player_id
        results = []
        for match_name, score, _ in matches:  # process.extract returns (match, score, index)
            for db_name, player_id in existing_players:
                if db_name == match_name:
                    results.append((match_name, player_id, score))
                    break
        return results
    
    def _search_nba_api_for_player(self, player_name: str) -> Optional[Dict]:
        """Search NBA API for a player by name."""
        try:
            # Search for players by name
            players = self.nba_client.search_players(player_name)
            
            if not players:
                return None
            
            # Return the first match (most relevant)
            player = players[0]
            return {
                'player_id': player.get('id'),
                'player_name': player.get('full_name'),
                'first_name': player.get('first_name'),
                'last_name': player.get('last_name')
            }
        except Exception as e:
            print(f"Error searching NBA API for '{player_name}': {e}")
            return None
    
    def _create_new_player(self, player_data: Dict) -> bool:
        """Create a new player in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Players (player_id, player_name, first_name, last_name)
                    VALUES (?, ?, ?, ?)
                """, (
                    player_data['player_id'],
                    player_data['player_name'],
                    player_data['first_name'],
                    player_data['last_name']
                ))
                conn.commit()
                print(f"✓ Created new player: {player_data['player_name']} (ID: {player_data['player_id']})")
                return True
            finally:
                conn.close()
        except Exception as e:
            print(f"Error creating player '{player_data['player_name']}': {e}")
            return False
    
    def _interactive_reconcile(self, csv_name: str, existing_players: List[Tuple[str, int]]) -> Optional[str]:
        """Interactively reconcile a CSV player name with database players."""
        print(f"\n{'='*60}")
        print(f"Unmatched: '{csv_name}'")
        print(f"{'='*60}")
        
        # Check if we already have a mapping
        if csv_name.lower() in self.existing_mappings:
            mapped_name = self.existing_mappings[csv_name.lower()]
            print(f"✓ Already mapped to: '{mapped_name}'")
            return mapped_name
        
        # Find fuzzy matches
        fuzzy_matches = self._find_fuzzy_matches(csv_name, existing_players)
        
        if fuzzy_matches:
            print("Suggestions:")
            for i, (match_name, player_id, score) in enumerate(fuzzy_matches, 1):
                print(f"  {i}. {match_name} (ID: {player_id}) - {score:.1f}% match")
        
        print("\nOptions:")
        print("  (1-5) Select a suggestion above")
        print("  (c)reate - Create a new player for this name")
        print("  (s)kip - Skip this player")
        print("  (q)uit - Exit the tool")
        
        while True:
            choice = input("\nYour choice: ").strip().lower()
            
            if choice == 'q':
                return None
            elif choice == 's':
                print(f"Skipped: '{csv_name}'")
                return None
            elif choice == 'c':
                # Create new player
                player_data = self._search_nba_api_for_player(csv_name)
                if not player_data:
                    print(f"❌ Could not find player '{csv_name}' in NBA API")
                    continue
                
                print(f"Found player: {player_data['player_name']} (ID: {player_data['player_id']})")
                confirm = input("Create this player? (y/n): ").strip().lower()
                if confirm == 'y':
                    if self._create_new_player(player_data):
                        # Save the mapping
                        self._save_mapping(csv_name, player_data['player_name'])
                        return player_data['player_name']
                else:
                    continue
            elif choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(fuzzy_matches):
                    selected_match = fuzzy_matches[choice_num - 1]
                    match_name, player_id, score = selected_match
                    
                    print(f"Selected: {match_name} (ID: {player_id}) - {score:.1f}% match")
                    confirm = input("Confirm this mapping? (y/n): ").strip().lower()
                    if confirm == 'y':
                        self._save_mapping(csv_name, match_name)
                        return match_name
                else:
                    print("Invalid choice. Please try again.")
            else:
                print("Invalid choice. Please try again.")
    
    def reconcile_csv_file(self, csv_file_path: str, name_column: str) -> Dict[str, str]:
        """Reconcile all player names in a CSV file."""
        print(f"\n🔄 Processing CSV file: {csv_file_path}")
        
        # Read CSV file
        csv_players = set()
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if name_column in row and row[name_column].strip():
                        csv_players.add(row[name_column].strip())
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return {}
        
        print(f"Found {len(csv_players)} unique player names in CSV")
        
        # Get existing players from database
        existing_players = self._get_existing_players()
        print(f"Found {len(existing_players)} players in database")
        
        # Reconcile each player
        mappings = {}
        unmatched = []
        
        for csv_name in sorted(csv_players):
            # Check if already mapped
            if csv_name.lower() in self.existing_mappings:
                mappings[csv_name] = self.existing_mappings[csv_name.lower()]
                continue
            
            # Check for exact match in database
            exact_match = None
            for db_name, player_id in existing_players:
                if csv_name.lower() == db_name.lower():
                    exact_match = db_name
                    break
            
            if exact_match:
                mappings[csv_name] = exact_match
                self._save_mapping(csv_name, exact_match)
                print(f"✓ Exact match: '{csv_name}' -> '{exact_match}'")
            else:
                # Interactive reconciliation
                reconciled_name = self._interactive_reconcile(csv_name, existing_players)
                if reconciled_name:
                    mappings[csv_name] = reconciled_name
                else:
                    unmatched.append(csv_name)
        
        print(f"\n📊 Reconciliation Summary:")
        print(f"  Total players in CSV: {len(csv_players)}")
        print(f"  Successfully mapped: {len(mappings)}")
        print(f"  Unmatched: {len(unmatched)}")
        
        if unmatched:
            print(f"\n⚠️  Unmatched players:")
            for player in unmatched:
                print(f"    - {player}")
        
        return mappings

def main():
    parser = argparse.ArgumentParser(description='Reconcile player names between CSV files and database')
    parser.add_argument('--db-path', default='src/nba_stats/db/nba_stats.db', 
                       help='Path to the database file')
    parser.add_argument('--mapping-file', default='mappings/player_name_map.csv',
                       help='Path to the mapping file')
    parser.add_argument('--salaries-csv', default='data/player_salaries_2024-25.csv',
                       help='Path to the salaries CSV file')
    parser.add_argument('--skills-csv', default='data/darko_dpm_2024-25.csv',
                       help='Path to the skills CSV file')
    
    args = parser.parse_args()
    
    # Validate file paths
    if not os.path.exists(args.db_path):
        print(f"❌ Database file not found: {args.db_path}")
        return 1
    
    if not os.path.exists(args.salaries_csv):
        print(f"❌ Salaries CSV file not found: {args.salaries_csv}")
        return 1
    
    if not os.path.exists(args.skills_csv):
        print(f"❌ Skills CSV file not found: {args.skills_csv}")
        return 1
    
    # Create reconciliation tool
    tool = PlayerReconciliationTool(args.db_path, args.mapping_file)
    
    print("🎯 Player Name Reconciliation Tool")
    print("=" * 50)
    
    # Reconcile salaries CSV
    print("\n1️⃣ Processing Salaries CSV...")
    salary_mappings = tool.reconcile_csv_file(args.salaries_csv, 'Player')
    
    # Reconcile skills CSV  
    print("\n2️⃣ Processing Skills CSV...")
    skills_mappings = tool.reconcile_csv_file(args.skills_csv, 'Player')
    
    # Final summary
    print(f"\n🎉 Reconciliation Complete!")
    print(f"  Salary mappings: {len(salary_mappings)}")
    print(f"  Skills mappings: {len(skills_mappings)}")
    print(f"  Mapping file: {args.mapping_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
