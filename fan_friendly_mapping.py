"""
Fan-Friendly Data Mapping System

This module provides basketball-intuitive mappings and explanations
that fans can understand, replacing technical archetype terminology
with familiar basketball concepts.
"""

import sqlite3
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json

@dataclass
class PlayerInfo:
    """Player information with fan-friendly data."""
    player_id: int
    name: str
    position: str  # PG, SG, SF, PF, C
    role: str  # Shooter, Defender, Playmaker, etc.
    archetype_id: int
    team_id: int
    team_name: str
    offensive_rating: float
    defensive_rating: float
    overall_rating: float

@dataclass
class TeamInfo:
    """Team information with roster data."""
    team_id: int
    team_name: str
    team_abbreviation: str
    primary_color: str
    secondary_color: str
    players: List[PlayerInfo]

class FanFriendlyMapper:
    """Maps technical archetypes to basketball positions and roles."""
    
    def __init__(self, db_path: str = "src/nba_stats/db/nba_stats.db"):
        self.db_path = db_path
        self.conn = None
        
        # Archetype to position mapping - more nuanced approach
        self.archetype_to_position = {
            0: "C",  # Big Men -> Center
            1: "PG", # Primary Ball Handlers -> Point Guard
            2: "SF"  # Role Players -> Small Forward (most versatile)
        }
        
        # Archetype to role mapping
        self.archetype_to_role = {
            0: "Rim Protector",  # Big Men
            1: "Playmaker",      # Primary Ball Handlers
            2: "3&D Wing"        # Role Players
        }
        
        # Special player mappings for better accuracy
        self.special_player_mappings = {
            "Kawhi Leonard": ("SF", "3&D Wing"),
            "Paul George": ("SF", "3&D Wing"),
            "Jimmy Butler": ("SF", "3&D Wing"),
            "Jayson Tatum": ("SF", "3&D Wing"),
            "Brandon Ingram": ("SF", "3&D Wing"),
            "Jaylen Brown": ("SG", "3&D Wing"),
            "Devin Booker": ("SG", "3&D Wing"),
            "Bradley Beal": ("SG", "3&D Wing"),
            "Donovan Mitchell": ("SG", "3&D Wing"),
            "Zach LaVine": ("SG", "3&D Wing"),
            "Pascal Siakam": ("PF", "3&D Wing"),
            "Draymond Green": ("PF", "Rim Protector"),
            "Bam Adebayo": ("PF", "Rim Protector"),
            "Karl-Anthony Towns": ("PF", "Rim Protector"),
            "Jaren Jackson Jr.": ("PF", "Rim Protector"),
        }
        
        # Position descriptions for fans
        self.position_descriptions = {
            "PG": "Point Guard - Primary ball handler and playmaker",
            "SG": "Shooting Guard - Perimeter scorer and defender",
            "SF": "Small Forward - Versatile wing player",
            "PF": "Power Forward - Interior scorer and rebounder",
            "C": "Center - Rim protector and post scorer"
        }
        
        # Role descriptions for fans
        self.role_descriptions = {
            "Rim Protector": "Defensive anchor who protects the paint",
            "Playmaker": "Primary ball handler who creates for others",
            "3&D Wing": "Shooter and defender who spaces the floor"
        }
    
    def connect_database(self) -> bool:
        """Connect to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def load_players(self) -> List[PlayerInfo]:
        """Load all players with fan-friendly mappings."""
        if not self.conn:
            return []
        
        query = """
        SELECT 
            p.player_id,
            p.player_name,
            pa.archetype_id,
            a.archetype_name,
            ps.offensive_darko,
            ps.defensive_darko,
            ps.darko,
            p.team_id,
            t.team_name
        FROM Players p
        LEFT JOIN PlayerSeasonArchetypes pa ON p.player_id = pa.player_id AND pa.season = '2024-25'
        LEFT JOIN Archetypes a ON pa.archetype_id = a.archetype_id
        LEFT JOIN PlayerSeasonSkill ps ON p.player_id = ps.player_id AND ps.season = '2024-25'
        LEFT JOIN Teams t ON p.team_id = t.team_id
        WHERE pa.archetype_id IS NOT NULL AND ps.offensive_darko IS NOT NULL
        ORDER BY ps.darko DESC
        """
        
        df = pd.read_sql_query(query, self.conn)
        
        players = []
        for _, row in df.iterrows():
            # Check for special player mappings first
            if row['player_name'] in self.special_player_mappings:
                position, role = self.special_player_mappings[row['player_name']]
            else:
                position = self.archetype_to_position.get(row['archetype_id'], 'SF')
                role = self.archetype_to_role.get(row['archetype_id'], '3&D Wing')
            
            player = PlayerInfo(
                player_id=row['player_id'],
                name=row['player_name'],
                position=position,
                role=role,
                archetype_id=row['archetype_id'],
                team_id=row['team_id'],
                team_name=row['team_name'],
                offensive_rating=row['offensive_darko'],
                defensive_rating=row['defensive_darko'],
                overall_rating=row['darko']
            )
            players.append(player)
        
        return players
    
    def load_teams(self) -> List[TeamInfo]:
        """Load all teams with their rosters."""
        if not self.conn:
            return []
        
        # Load team basic info
        team_query = """
        SELECT team_id, team_name, team_abbreviation
        FROM Teams
        ORDER BY team_name
        """
        
        teams_df = pd.read_sql_query(team_query, self.conn)
        players = self.load_players()
        
        teams = []
        for _, team_row in teams_df.iterrows():
            team_players = [p for p in players if p.team_id == team_row['team_id']]
            
            team = TeamInfo(
                team_id=team_row['team_id'],
                team_name=team_row['team_name'],
                team_abbreviation=team_row['team_abbreviation'],
                primary_color=self._get_team_color(team_row['team_abbreviation']),
                secondary_color=self._get_team_secondary_color(team_row['team_abbreviation']),
                players=team_players
            )
            teams.append(team)
        
        return teams
    
    def _get_team_color(self, team_abbr: str) -> str:
        """Get primary team color."""
        team_colors = {
            'ATL': '#E03A3E', 'BOS': '#007A33', 'BKN': '#000000', 'CHA': '#1D1160',
            'CHI': '#CE1141', 'CLE': '#860038', 'DAL': '#00538C', 'DEN': '#0E2240',
            'DET': '#C8102E', 'GSW': '#1D428A', 'HOU': '#CE1141', 'IND': '#002D62',
            'LAC': '#C8102E', 'LAL': '#552583', 'MEM': '#5D76A9', 'MIA': '#98002E',
            'MIL': '#00471B', 'MIN': '#0C2340', 'NOP': '#0C2340', 'NYK': '#006BB6',
            'OKC': '#007AC1', 'ORL': '#0077C0', 'PHI': '#006BB6', 'PHX': '#1D1160',
            'POR': '#E03A3E', 'SAC': '#5A2D0C', 'SAS': '#C4CED4', 'TOR': '#CE1141',
            'UTA': '#002B5C', 'WAS': '#002B5C'
        }
        return team_colors.get(team_abbr, '#666666')
    
    def _get_team_secondary_color(self, team_abbr: str) -> str:
        """Get secondary team color."""
        team_secondary_colors = {
            'ATL': '#C1D32F', 'BOS': '#BA9653', 'BKN': '#FFFFFF', 'CHA': '#00788C',
            'CHI': '#000000', 'CLE': '#FDBB30', 'DAL': '#002B5C', 'DEN': '#FEC524',
            'DET': '#1D42A2', 'GSW': '#FFC72C', 'HOU': '#000000', 'IND': '#FDBB30',
            'LAC': '#1D428A', 'LAL': '#FDB927', 'MEM': '#12173F', 'MIA': '#F9A01B',
            'MIL': '#EEE1C6', 'MIN': '#236192', 'NOP': '#C8102E', 'NYK': '#F58426',
            'OKC': '#EF3B24', 'ORL': '#C4CED4', 'PHI': '#ED174C', 'PHX': '#E56020',
            'POR': '#000000', 'SAC': '#63727A', 'SAS': '#000000', 'TOR': '#000000',
            'UTA': '#F9A01B', 'WAS': '#E31837'
        }
        return team_secondary_colors.get(team_abbr, '#CCCCCC')
    
    def get_position_balance(self, team: TeamInfo) -> Dict[str, int]:
        """Get team's position balance for analysis."""
        position_counts = {}
        for player in team.players:
            position_counts[player.position] = position_counts.get(player.position, 0) + 1
        return position_counts
    
    def get_team_needs(self, team: TeamInfo) -> List[str]:
        """Identify what positions the team needs."""
        position_balance = self.get_position_balance(team)
        
        # Ideal balance: 1 PG, 1 SG, 1 SF, 1 PF, 1 C
        ideal_balance = {'PG': 1, 'SG': 1, 'SF': 1, 'PF': 1, 'C': 1}
        
        needs = []
        for position, ideal_count in ideal_balance.items():
            current_count = position_balance.get(position, 0)
            if current_count < ideal_count:
                needs.append(f"Need a {position}")
        
        return needs
    
    def generate_fit_explanation(self, player: PlayerInfo, team: TeamInfo) -> str:
        """Generate basketball-intuitive fit explanation."""
        team_needs = self.get_team_needs(team)
        position_balance = self.get_position_balance(team)
        
        # Check if team needs this position
        if f"Need a {player.position}" in team_needs:
            return f"✅ Great fit! {team.team_name} needs a {player.position} and {player.name} is a {player.role}."
        
        # Check if position is already filled
        current_count = position_balance.get(player.position, 0)
        if current_count >= 2:
            return f"⚠️ {team.team_name} already has {current_count} {player.position}s. {player.name} might be redundant."
        
        # Check role fit
        if player.role == "Rim Protector" and position_balance.get('C', 0) == 0:
            return f"✅ Good fit! {team.team_name} needs rim protection and {player.name} provides that."
        elif player.role == "Playmaker" and position_balance.get('PG', 0) == 0:
            return f"✅ Good fit! {team.team_name} needs playmaking and {player.name} is a great facilitator."
        elif player.role == "3&D Wing" and position_balance.get('SF', 0) < 2:
            return f"✅ Good fit! {player.name} provides shooting and defense that {team.team_name} can use."
        
        return f"🤔 {player.name} is a solid player but might not address {team.team_name}'s biggest needs."
    
    def search_players(self, query: str, players: List[PlayerInfo]) -> List[PlayerInfo]:
        """Search players by name with fuzzy matching."""
        query_lower = query.lower()
        matches = []
        
        for player in players:
            if query_lower in player.name.lower():
                matches.append(player)
        
        # Sort by overall rating (best players first)
        matches.sort(key=lambda p: p.overall_rating, reverse=True)
        return matches
    
    def get_free_agents(self, players: List[PlayerInfo]) -> List[PlayerInfo]:
        """Get players who are free agents (not on any team)."""
        # For demonstration, return some players as "free agents"
        # In a real implementation, this would check against current rosters
        # For now, we'll simulate by taking some players from specific teams
        # Using actual team IDs from the database
        free_agent_teams = [1610612737, 1610612738, 1610612739]  # First 3 teams as "free agent pool"
        return [p for p in players if p.team_id in free_agent_teams]
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

def main():
    """Test the fan-friendly mapping system."""
    mapper = FanFriendlyMapper()
    
    if not mapper.connect_database():
        print("Failed to connect to database")
        return
    
    # Load data
    players = mapper.load_players()
    teams = mapper.load_teams()
    
    print(f"Loaded {len(players)} players and {len(teams)} teams")
    
    # Test search
    search_results = mapper.search_players("LeBron", players)
    print(f"\nSearch results for 'LeBron': {len(search_results)}")
    for player in search_results[:3]:
        print(f"  {player.name} - {player.position} - {player.role}")
    
    # Test team analysis
    if teams:
        team = teams[0]  # First team
        print(f"\n{team.team_name} analysis:")
        print(f"  Players: {len(team.players)}")
        print(f"  Position balance: {mapper.get_position_balance(team)}")
        print(f"  Team needs: {mapper.get_team_needs(team)}")
    
    mapper.close()

if __name__ == "__main__":
    main()
