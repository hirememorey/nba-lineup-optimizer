"""
Database Writer Service

This service provides a generic, robust interface for writing data to the database
with comprehensive validation, atomic transactions, and pre-flight schema checks.
"""

import sqlite3
import logging
from typing import List, Dict, Any, Optional, Type, Union
from pathlib import Path
from datetime import datetime

from ..models.database_dtos import (
    PlayerSeasonRawStatsDTO, 
    PlayerSeasonAdvancedStatsDTO, 
    DatabaseWriteResult
)

logger = logging.getLogger(__name__)


class DatabaseWriter:
    """
    Generic database writer service with pre-flight validation and atomic transactions.
    """
    
    def __init__(self, db_path: str = "src/nba_stats/db/nba_stats.db"):
        """Initialize the database writer."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
    def write_player_season_raw_stats(self, stats: List[PlayerSeasonRawStatsDTO]) -> DatabaseWriteResult:
        """
        Write player season raw stats to the database with full validation.
        
        Args:
            stats: List of validated PlayerSeasonRawStatsDTO objects
            
        Returns:
            DatabaseWriteResult with operation details
        """
        return self._write_data(
            table_name="PlayerSeasonRawStats",
            data=stats,
            dto_class=PlayerSeasonRawStatsDTO
        )
    
    def write_player_season_advanced_stats(self, stats: List[PlayerSeasonAdvancedStatsDTO]) -> DatabaseWriteResult:
        """
        Write player season advanced stats to the database with full validation.
        
        Args:
            stats: List of validated PlayerSeasonAdvancedStatsDTO objects
            
        Returns:
            DatabaseWriteResult with operation details
        """
        return self._write_data(
            table_name="PlayerSeasonAdvancedStats",
            data=stats,
            dto_class=PlayerSeasonAdvancedStatsDTO
        )
    
    def _write_data(
        self, 
        table_name: str, 
        data: List[Union[PlayerSeasonRawStatsDTO, PlayerSeasonAdvancedStatsDTO]], 
        dto_class: Type[Union[PlayerSeasonRawStatsDTO, PlayerSeasonAdvancedStatsDTO]]
    ) -> DatabaseWriteResult:
        """
        Generic method to write data to any table with full validation.
        
        Args:
            table_name: Name of the target table
            data: List of validated DTO objects
            dto_class: The DTO class for validation
            
        Returns:
            DatabaseWriteResult with operation details
        """
        if not data:
            return DatabaseWriteResult(
                success=True,
                rows_affected=0,
                table_name=table_name,
                error_message="No data to write"
            )
        
        try:
            # Pre-flight validation: Check schema compatibility
            schema_validation = self._validate_schema_compatibility(table_name, dto_class)
            if not schema_validation["compatible"]:
                return DatabaseWriteResult(
                    success=False,
                    rows_affected=0,
                    table_name=table_name,
                    error_message=f"Schema validation failed: {schema_validation['error']}"
                )
            
            # Convert DTOs to dictionaries
            data_dicts = [dto.model_dump() for dto in data]
            
            # Write data with atomic transaction
            return self._write_with_transaction(table_name, data_dicts)
            
        except Exception as e:
            logger.error(f"Error writing to {table_name}: {str(e)}")
            return DatabaseWriteResult(
                success=False,
                rows_affected=0,
                table_name=table_name,
                error_message=str(e)
            )
    
    def _validate_schema_compatibility(
        self, 
        table_name: str, 
        dto_class: Type[Union[PlayerSeasonRawStatsDTO, PlayerSeasonAdvancedStatsDTO]]
    ) -> Dict[str, Any]:
        """
        Pre-flight validation to ensure DTO schema matches database table schema.
        
        Args:
            table_name: Name of the target table
            dto_class: The DTO class to validate against
            
        Returns:
            Dictionary with validation results
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Enable foreign key constraints
                conn.execute("PRAGMA foreign_keys = ON")
                # Get database schema
                cursor = conn.execute(f"PRAGMA table_info({table_name})")
                db_columns = {row[1]: row[2] for row in cursor.fetchall()}  # {column_name: data_type}
                
                # Get DTO schema
                dto_fields = dto_class.model_fields
                dto_columns = {field_name: field_info.annotation for field_name, field_info in dto_fields.items()}
                
                # Check for missing columns in database
                missing_in_db = set(dto_columns.keys()) - set(db_columns.keys())
                if missing_in_db:
                    return {
                        "compatible": False,
                        "error": f"Database table '{table_name}' missing columns: {missing_in_db}"
                    }
                
                # Check for extra columns in database (warn but don't fail)
                extra_in_db = set(db_columns.keys()) - set(dto_columns.keys())
                if extra_in_db:
                    logger.warning(f"Database table '{table_name}' has extra columns: {extra_in_db}")
                
                return {"compatible": True, "error": None}
                
        except Exception as e:
            return {
                "compatible": False,
                "error": f"Failed to validate schema: {str(e)}"
            }
    
    def _write_with_transaction(self, table_name: str, data_dicts: List[Dict[str, Any]]) -> DatabaseWriteResult:
        """
        Write data using atomic transaction with audit verification.
        
        Args:
            table_name: Name of the target table
            data_dicts: List of dictionaries to write
            
        Returns:
            DatabaseWriteResult with operation details
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Enable foreign key constraints
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("BEGIN TRANSACTION")
                
                try:
                    # Prepare data for insertion
                    if not data_dicts:
                        conn.execute("COMMIT")
                        return DatabaseWriteResult(
                            success=True,
                            rows_affected=0,
                            table_name=table_name
                        )
                    
                    # Get column names from first record
                    columns = list(data_dicts[0].keys())
                    placeholders = ", ".join(["?" for _ in columns])
                    column_names = ", ".join(columns)
                    
                    # Insert data
                    insert_sql = f"INSERT OR REPLACE INTO {table_name} ({column_names}) VALUES ({placeholders})"
                    
                    rows_affected = 0
                    for record in data_dicts:
                        values = [record.get(col) for col in columns]
                        cursor = conn.execute(insert_sql, values)
                        rows_affected += cursor.rowcount
                    
                    # Audit: Verify the write within the same transaction
                    audit_result = self._audit_write(conn, table_name, len(data_dicts))
                    if not audit_result["success"]:
                        conn.execute("ROLLBACK")
                        return DatabaseWriteResult(
                            success=False,
                            rows_affected=0,
                            table_name=table_name,
                            error_message=f"Write audit failed: {audit_result['error']}"
                        )
                    
                    conn.execute("COMMIT")
                    
                    logger.info(f"Successfully wrote {rows_affected} rows to {table_name}")
                    return DatabaseWriteResult(
                        success=True,
                        rows_affected=rows_affected,
                        table_name=table_name
                    )
                    
                except Exception as e:
                    conn.execute("ROLLBACK")
                    raise e
                    
        except Exception as e:
            logger.error(f"Transaction failed for {table_name}: {str(e)}")
            return DatabaseWriteResult(
                success=False,
                rows_affected=0,
                table_name=table_name,
                error_message=str(e)
            )
    
    def _audit_write(self, conn: sqlite3.Connection, table_name: str, expected_count: int) -> Dict[str, Any]:
        """
        Audit a write operation by reading back sample data within the same transaction.
        
        Args:
            conn: Database connection
            table_name: Name of the table that was written to
            expected_count: Expected number of rows written
            
        Returns:
            Dictionary with audit results
        """
        try:
            # Count total rows
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_rows = cursor.fetchone()[0]
            
            # Sample a few rows to verify data integrity
            cursor = conn.execute(f"SELECT * FROM {table_name} ORDER BY ROWID DESC LIMIT 5")
            sample_rows = cursor.fetchall()
            
            # Basic validation
            if len(sample_rows) == 0 and expected_count > 0:
                return {
                    "success": False,
                    "error": "No data found after write operation"
                }
            
            # Check for NULL values in critical columns
            critical_columns = ["player_id", "season", "team_id"]
            for row in sample_rows:
                # Get column names
                cursor = conn.execute(f"PRAGMA table_info({table_name})")
                column_info = cursor.fetchall()
                column_names = [col[1] for col in column_info]
                
                # Check critical columns
                for i, col_name in enumerate(column_names):
                    if col_name in critical_columns and row[i] is None:
                        return {
                            "success": False,
                            "error": f"Critical column '{col_name}' is NULL in written data"
                        }
            
            return {"success": True, "error": None}
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Audit failed: {str(e)}"
            }
    
    def get_table_schema(self, table_name: str) -> Dict[str, str]:
        """
        Get the schema of a database table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary mapping column names to data types
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Enable foreign key constraints
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.execute(f"PRAGMA table_info({table_name})")
                return {row[1]: row[2] for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"Failed to get schema for {table_name}: {str(e)}")
            return {}
    
    def verify_data_integrity(self, table_name: str) -> Dict[str, Any]:
        """
        Verify data integrity for a specific table.
        
        Args:
            table_name: Name of the table to verify
            
        Returns:
            Dictionary with verification results
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Enable foreign key constraints
                conn.execute("PRAGMA foreign_keys = ON")
                # Count total rows
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                total_rows = cursor.fetchone()[0]
                
                # Check for NULL values in critical columns
                critical_columns = ["player_id", "season", "team_id"]
                null_checks = {}
                
                for col in critical_columns:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col} IS NULL")
                    null_count = cursor.fetchone()[0]
                    null_checks[col] = null_count
                
                return {
                    "success": True,
                    "total_rows": total_rows,
                    "null_checks": null_checks,
                    "has_data": total_rows > 0,
                    "critical_columns_valid": all(count == 0 for count in null_checks.values())
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "total_rows": 0,
                "has_data": False,
                "critical_columns_valid": False
            }
