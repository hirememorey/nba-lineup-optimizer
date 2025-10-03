"""
Live Schema Validator

This module provides continuous schema validation to prevent schema drift
and ensure the database meets the requirements for possession-level modeling.

Based on the post-mortem insights from the previous developer, this validator
enforces the ground truth discovered through data archaeology.
"""

import sqlite3
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of a schema validation check."""
    table_name: str
    check_type: str
    passed: bool
    message: str
    actual_value: Optional[Any] = None
    expected_value: Optional[Any] = None


class SchemaDriftError(Exception):
    """Raised when schema validation fails due to drift from expectations."""
    pass


class LiveSchemaValidator:
    """
    Validates database schema against expectations defined in YAML configuration.
    
    This validator implements the critical insight from the post-mortem:
    schema drift is a continuous risk that must be caught at runtime.
    """
    
    def __init__(self, config_path: str = "schema_expectations.yml"):
        """
        Initialize the validator with configuration file.
        
        Args:
            config_path: Path to the schema expectations YAML file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.db_path = self.config['database_path']
    
    def _load_config(self) -> Dict[str, Any]:
        """Load and parse the schema expectations configuration."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Schema expectations file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in schema expectations: {e}")
    
    def validate(self) -> List[ValidationResult]:
        """
        Perform complete schema validation.
        
        Returns:
            List of validation results
            
        Raises:
            SchemaDriftError: If any critical validation fails
        """
        results = []
        
        # Validate database exists and is accessible
        results.extend(self._validate_database_connection())
        
        # Validate each required table
        for table_name, table_config in self.config['tables'].items():
            if table_config.get('required', False):
                results.extend(self._validate_table(table_name, table_config))
        
        # Validate data quality requirements
        results.extend(self._validate_data_quality())
        
        # Check for critical failures
        critical_failures = [r for r in results if not r.passed and r.check_type in ['table_exists', 'column_exists', 'min_rows']]
        
        if critical_failures:
            error_messages = [f"{r.table_name}: {r.message}" for r in critical_failures]
            raise SchemaDriftError(f"Schema validation failed:\n" + "\n".join(error_messages))
        
        return results
    
    def _validate_database_connection(self) -> List[ValidationResult]:
        """Validate that the database exists and is accessible."""
        results = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("SELECT 1")
            conn.close()
            results.append(ValidationResult(
                table_name="database",
                check_type="connection",
                passed=True,
                message="Database connection successful"
            ))
        except Exception as e:
            results.append(ValidationResult(
                table_name="database",
                check_type="connection",
                passed=False,
                message=f"Database connection failed: {e}"
            ))
        
        return results
    
    def _validate_table(self, table_name: str, table_config: Dict[str, Any]) -> List[ValidationResult]:
        """Validate a specific table against its configuration."""
        results = []
        
        # Check table exists
        table_exists = self._check_table_exists(table_name)
        results.append(ValidationResult(
            table_name=table_name,
            check_type="table_exists",
            passed=table_exists,
            message=f"Table {table_name} exists" if table_exists else f"Table {table_name} not found"
        ))
        
        if not table_exists:
            return results
        
        # Check required columns exist
        for column_name, expected_type in table_config.get('columns', {}).items():
            column_exists = self._check_column_exists(table_name, column_name)
            results.append(ValidationResult(
                table_name=table_name,
                check_type="column_exists",
                passed=column_exists,
                message=f"Column {column_name} exists" if column_exists else f"Column {column_name} not found in {table_name}",
                expected_value=column_name
            ))
        
        # Check minimum row count
        min_rows = table_config.get('min_rows', 0)
        if min_rows > 0:
            actual_count = self._get_table_row_count(table_name)
            passed = actual_count >= min_rows
            results.append(ValidationResult(
                table_name=table_name,
                check_type="min_rows",
                passed=passed,
                message=f"Row count {actual_count} >= {min_rows}" if passed else f"Row count {actual_count} < {min_rows}",
                actual_value=actual_count,
                expected_value=min_rows
            ))
        
        return results
    
    def _validate_data_quality(self) -> List[ValidationResult]:
        """Validate data quality requirements."""
        results = []
        
        if 'validation_queries' not in self.config:
            return results
        
        for query_name, query in self.config['validation_queries'].items():
            try:
                result = self._execute_validation_query(query)
                # Parse result based on query type
                if query_name == 'lineup_completeness':
                    total, complete = result[0]
                    completeness = complete / total if total > 0 else 0
                    required = self.config['data_quality']['possession_lineup_completeness']
                    passed = completeness >= required
                    results.append(ValidationResult(
                        table_name="Possessions",
                        check_type="data_quality",
                        passed=passed,
                        message=f"Lineup completeness {completeness:.2%} >= {required:.2%}" if passed else f"Lineup completeness {completeness:.2%} < {required:.2%}",
                        actual_value=completeness,
                        expected_value=required
                    ))
                elif query_name == 'archetype_coverage':
                    total_players, players_with_archetypes = result[0]
                    coverage = players_with_archetypes / total_players if total_players > 0 else 0
                    required = self.config['data_quality']['archetype_coverage']
                    passed = coverage >= required
                    results.append(ValidationResult(
                        table_name="PlayerSeasonArchetypes",
                        check_type="data_quality",
                        passed=passed,
                        message=f"Archetype coverage {coverage:.2%} >= {required:.2%}" if passed else f"Archetype coverage {coverage:.2%} < {required:.2%}",
                        actual_value=coverage,
                        expected_value=required
                    ))
                elif query_name == 'skill_coverage':
                    total_players, players_with_skills = result[0]
                    coverage = players_with_skills / total_players if total_players > 0 else 0
                    required = self.config['data_quality']['skill_coverage']
                    passed = coverage >= required
                    results.append(ValidationResult(
                        table_name="PlayerSeasonSkill",
                        check_type="data_quality",
                        passed=passed,
                        message=f"Skill coverage {coverage:.2%} >= {required:.2%}" if passed else f"Skill coverage {coverage:.2%} < {required:.2%}",
                        actual_value=coverage,
                        expected_value=required
                    ))
            except Exception as e:
                results.append(ValidationResult(
                    table_name="validation",
                    check_type="data_quality",
                    passed=False,
                    message=f"Validation query {query_name} failed: {e}"
                ))
        
        return results
    
    def _check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except Exception:
            return False
    
    def _check_column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            conn.close()
            return column_name in columns
        except Exception:
            return False
    
    def _get_table_row_count(self, table_name: str) -> int:
        """Get the row count for a table."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0
    
    def _execute_validation_query(self, query: str) -> List[tuple]:
        """Execute a validation query and return results."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_validation_report(self) -> str:
        """
        Generate a human-readable validation report.
        
        Returns:
            Formatted validation report
        """
        try:
            results = self.validate()
        except SchemaDriftError as e:
            return f"❌ SCHEMA VALIDATION FAILED\n\n{e}\n\nThis indicates schema drift. Check DATA_REALITY_REPORT.md for expected schema."
        
        report_lines = ["✅ SCHEMA VALIDATION PASSED\n"]
        
        # Group results by table
        by_table = {}
        for result in results:
            if result.table_name not in by_table:
                by_table[result.table_name] = []
            by_table[result.table_name].append(result)
        
        for table_name, table_results in by_table.items():
            report_lines.append(f"\n📊 {table_name}:")
            for result in table_results:
                status = "✅" if result.passed else "❌"
                report_lines.append(f"  {status} {result.check_type}: {result.message}")
        
        return "\n".join(report_lines)


def validate_schema(config_path: str = "schema_expectations.yml") -> None:
    """
    Convenience function to validate schema and raise exception on failure.
    
    Args:
        config_path: Path to schema expectations file
        
    Raises:
        SchemaDriftError: If validation fails
    """
    validator = LiveSchemaValidator(config_path)
    validator.validate()


if __name__ == "__main__":
    """Run schema validation from command line."""
    import sys
    
    config_path = sys.argv[1] if len(sys.argv) > 1 else "schema_expectations.yml"
    
    try:
        validator = LiveSchemaValidator(config_path)
        print(validator.get_validation_report())
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        sys.exit(1)

