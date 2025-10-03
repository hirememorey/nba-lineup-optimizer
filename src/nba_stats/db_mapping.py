"""
Database Mapping Anti-Corruption Layer

This module provides the critical mapping between logical column names
(used in application code) and actual database column names (discovered
through data archaeology).

This implements the key insight from the post-mortem: the database schema
is inconsistent with code expectations, requiring a mapping layer to prevent
the "documentation-driven development" trap.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class ColumnMapping:
    """Mapping between logical and actual column names."""
    logical_name: str
    actual_name: str
    table_name: str
    data_type: str


class DatabaseMapping:
    """
    Anti-corruption layer for database column name mapping.
    
    This class encapsulates all knowledge about the actual database schema,
    allowing the rest of the application to use logical, documentation-based
    column names while handling the messy reality of the actual database.
    """
    
    def __init__(self):
        """Initialize with mappings discovered through data archaeology."""
        self._column_mappings = self._build_column_mappings()
        self._table_mappings = self._build_table_mappings()
        self._query_templates = self._build_query_templates()
    
    def _build_column_mappings(self) -> Dict[str, ColumnMapping]:
        """Build column mappings based on data archaeology findings."""
        mappings = {}
        
        # PlayerSeasonSkill table mappings
        skill_columns = [
            ("offensive_rating", "offensive_darko", "PlayerSeasonSkill", "REAL"),
            ("defensive_rating", "defensive_darko", "PlayerSeasonSkill", "REAL"),
            ("overall_rating", "darko", "PlayerSeasonSkill", "REAL"),
            ("offensive_epm", "offensive_epm", "PlayerSeasonSkill", "REAL"),
            ("defensive_epm", "defensive_epm", "PlayerSeasonSkill", "REAL"),
            ("overall_epm", "epm", "PlayerSeasonSkill", "REAL"),
            ("offensive_raptor", "offensive_raptor", "PlayerSeasonSkill", "REAL"),
            ("defensive_raptor", "defensive_raptor", "PlayerSeasonSkill", "REAL"),
            ("overall_raptor", "raptor", "PlayerSeasonSkill", "REAL"),
        ]
        
        for logical, actual, table, dtype in skill_columns:
            key = f"{table}.{logical}"
            mappings[key] = ColumnMapping(logical, actual, table, dtype)
        
        # PlayerSeasonArchetypes table mappings
        archetype_columns = [
            ("archetype_name", "archetype_id", "PlayerSeasonArchetypes", "INTEGER"),
        ]
        
        for logical, actual, table, dtype in archetype_columns:
            key = f"{table}.{logical}"
            mappings[key] = ColumnMapping(logical, actual, table, dtype)
        
        # Possessions table mappings (lineup fields)
        possession_columns = [
            ("home_lineup", "home_player_1_id,home_player_2_id,home_player_3_id,home_player_4_id,home_player_5_id", "Possessions", "INTEGER"),
            ("away_lineup", "away_player_1_id,away_player_2_id,away_player_3_id,away_player_4_id,away_player_5_id", "Possessions", "INTEGER"),
            ("offensive_team", "offensive_team_id", "Possessions", "INTEGER"),
            ("defensive_team", "defensive_team_id", "Possessions", "INTEGER"),
        ]
        
        for logical, actual, table, dtype in possession_columns:
            key = f"{table}.{logical}"
            mappings[key] = ColumnMapping(logical, actual, table, dtype)
        
        return mappings
    
    def _build_table_mappings(self) -> Dict[str, str]:
        """Build table name mappings (currently 1:1 but prepared for changes)."""
        return {
            "PlayerSkills": "PlayerSeasonSkill",
            "PlayerArchetypes": "PlayerSeasonArchetypes",
            "PossessionData": "Possessions",
            "GameData": "Games",
            "PlayerData": "Players",
        }
    
    def _build_query_templates(self) -> Dict[str, str]:
        """Build common query templates using actual column names."""
        return {
            "get_player_skills": """
                SELECT 
                    ps.player_id,
                    ps.season,
                    p.player_name,
                    ps.offensive_darko,
                    ps.defensive_darko,
                    ps.darko,
                    ps.offensive_epm,
                    ps.defensive_epm,
                    ps.epm,
                    ps.offensive_raptor,
                    ps.defensive_raptor,
                    ps.raptor
                FROM PlayerSeasonSkill ps
                JOIN Players p ON ps.player_id = p.player_id
                WHERE ps.season = ?
            """,
            
            "get_player_archetypes": """
                SELECT 
                    pa.player_id,
                    pa.season,
                    pa.archetype_id,
                    a.archetype_name
                FROM PlayerSeasonArchetypes pa
                JOIN Archetypes a ON pa.archetype_id = a.archetype_id
                WHERE pa.season = ?
            """,
            
            "get_possessions_with_lineups": """
                SELECT 
                    p.game_id,
                    p.event_num,
                    p.event_type,
                    p.home_player_1_id,
                    p.home_player_2_id,
                    p.home_player_3_id,
                    p.home_player_4_id,
                    p.home_player_5_id,
                    p.away_player_1_id,
                    p.away_player_2_id,
                    p.away_player_3_id,
                    p.away_player_4_id,
                    p.away_player_5_id,
                    p.offensive_team_id,
                    p.defensive_team_id
                FROM Possessions p
                WHERE p.home_player_1_id IS NOT NULL
                AND p.home_player_2_id IS NOT NULL
                AND p.home_player_3_id IS NOT NULL
                AND p.home_player_4_id IS NOT NULL
                AND p.home_player_5_id IS NOT NULL
                AND p.away_player_1_id IS NOT NULL
                AND p.away_player_2_id IS NOT NULL
                AND p.away_player_3_id IS NOT NULL
                AND p.away_player_4_id IS NOT NULL
                AND p.away_player_5_id IS NOT NULL
            """,
            
            "get_games": """
                SELECT 
                    g.game_id,
                    g.game_date,
                    g.home_team_id,
                    g.away_team_id,
                    g.season
                FROM Games g
                WHERE g.season = ?
            """,
        }
    
    def get_actual_column_name(self, table_name: str, logical_column_name: str) -> str:
        """
        Get the actual database column name for a logical column name.
        
        Args:
            table_name: Logical table name
            logical_column_name: Logical column name
            
        Returns:
            Actual database column name
            
        Raises:
            KeyError: If mapping not found
        """
        key = f"{table_name}.{logical_column_name}"
        if key not in self._column_mappings:
            raise KeyError(f"No mapping found for {table_name}.{logical_column_name}")
        
        return self._column_mappings[key].actual_name
    
    def get_actual_table_name(self, logical_table_name: str) -> str:
        """
        Get the actual database table name for a logical table name.
        
        Args:
            logical_table_name: Logical table name
            
        Returns:
            Actual database table name
        """
        return self._table_mappings.get(logical_table_name, logical_table_name)
    
    def get_query_template(self, query_name: str) -> str:
        """
        Get a pre-built query template using actual column names.
        
        Args:
            query_name: Name of the query template
            
        Returns:
            SQL query template
            
        Raises:
            KeyError: If query template not found
        """
        if query_name not in self._query_templates:
            raise KeyError(f"No query template found for {query_name}")
        
        return self._query_templates[query_name]
    
    def get_column_mapping(self, table_name: str, logical_column_name: str) -> ColumnMapping:
        """
        Get the complete column mapping information.
        
        Args:
            table_name: Logical table name
            logical_column_name: Logical column name
            
        Returns:
            ColumnMapping object
            
        Raises:
            KeyError: If mapping not found
        """
        key = f"{table_name}.{logical_column_name}"
        if key not in self._column_mappings:
            raise KeyError(f"No mapping found for {table_name}.{logical_column_name}")
        
        return self._column_mappings[key]
    
    def get_all_mappings_for_table(self, table_name: str) -> List[ColumnMapping]:
        """
        Get all column mappings for a specific table.
        
        Args:
            table_name: Logical table name
            
        Returns:
            List of ColumnMapping objects
        """
        mappings = []
        for key, mapping in self._column_mappings.items():
            if mapping.table_name == table_name:
                mappings.append(mapping)
        return mappings
    
    def validate_mapping_exists(self, table_name: str, logical_column_name: str) -> bool:
        """
        Check if a mapping exists for a logical column name.
        
        Args:
            table_name: Logical table name
            logical_column_name: Logical column name
            
        Returns:
            True if mapping exists, False otherwise
        """
        key = f"{table_name}.{logical_column_name}"
        return key in self._column_mappings
    
    def get_mapping_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all mappings for debugging and documentation.
        
        Returns:
            Dictionary containing mapping summary
        """
        summary = {
            "total_mappings": len(self._column_mappings),
            "tables": {},
            "query_templates": list(self._query_templates.keys())
        }
        
        # Group mappings by table
        for mapping in self._column_mappings.values():
            table_name = mapping.table_name
            if table_name not in summary["tables"]:
                summary["tables"][table_name] = []
            
            summary["tables"][table_name].append({
                "logical_name": mapping.logical_name,
                "actual_name": mapping.actual_name,
                "data_type": mapping.data_type
            })
        
        return summary


# Global instance for easy access
db_mapping = DatabaseMapping()


def get_actual_column_name(table_name: str, logical_column_name: str) -> str:
    """Convenience function to get actual column name."""
    return db_mapping.get_actual_column_name(table_name, logical_column_name)


def get_actual_table_name(logical_table_name: str) -> str:
    """Convenience function to get actual table name."""
    return db_mapping.get_actual_table_name(logical_table_name)


def get_query_template(query_name: str) -> str:
    """Convenience function to get query template."""
    return db_mapping.get_query_template(query_name)


if __name__ == "__main__":
    """Print mapping summary for debugging."""
    mapping = DatabaseMapping()
    summary = mapping.get_mapping_summary()
    
    print("Database Mapping Summary")
    print("=" * 50)
    print(f"Total mappings: {summary['total_mappings']}")
    print(f"Query templates: {len(summary['query_templates'])}")
    print()
    
    for table_name, columns in summary['tables'].items():
        print(f"Table: {table_name}")
        for col in columns:
            print(f"  {col['logical_name']} -> {col['actual_name']} ({col['data_type']})")
        print()

