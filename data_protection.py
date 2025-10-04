"""
Data Protection and Encryption System

This module provides data encryption, audit logging, and data protection
features for the NBA Lineup Optimizer.
"""

import hashlib
import hmac
import json
import logging
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class DataProtection:
    """Data protection and encryption system."""
    
    def __init__(self, config):
        self.config = config
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.audit_logger = self._setup_audit_logger()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key."""
        key_file = Path("data/encryption.key")
        key_file.parent.mkdir(exist_ok=True)
        
        if key_file.exists():
            with open(key_file, "rb") as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            # Set restrictive permissions
            key_file.chmod(0o600)
            return key
    
    def _setup_audit_logger(self) -> logging.Logger:
        """Setup audit logger."""
        audit_logger = logging.getLogger("audit")
        audit_logger.setLevel(logging.INFO)
        
        # Create audit log file
        audit_file = Path("logs/audit.log")
        audit_file.parent.mkdir(exist_ok=True)
        
        # Create file handler
        handler = logging.FileHandler(audit_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        audit_logger.addHandler(handler)
        
        return audit_logger
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt data."""
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logging.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data."""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            logging.error(f"Decryption failed: {e}")
            raise
    
    def hash_sensitive_data(self, data: str) -> str:
        """Create hash of sensitive data for verification."""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def create_data_integrity_hash(self, data: Dict[str, Any]) -> str:
        """Create integrity hash for data verification."""
        # Sort keys for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True)
        return hashlib.sha256(sorted_data.encode()).hexdigest()
    
    def verify_data_integrity(self, data: Dict[str, Any], expected_hash: str) -> bool:
        """Verify data integrity."""
        actual_hash = self.create_data_integrity_hash(data)
        return hmac.compare_digest(actual_hash, expected_hash)
    
    def log_audit_event(self, event_type: str, user: str, details: Dict[str, Any]):
        """Log audit event."""
        audit_event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user": user,
            "details": details,
            "session_id": self._get_session_id()
        }
        
        self.audit_logger.info(json.dumps(audit_event))
    
    def _get_session_id(self) -> str:
        """Get current session ID."""
        # This would be integrated with the session management system
        return os.environ.get("SESSION_ID", "unknown")
    
    def protect_database_connection(self, db_path: str) -> sqlite3.Connection:
        """Create protected database connection with audit logging."""
        conn = sqlite3.connect(db_path)
        
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys=ON")
        
        # Set secure pragmas
        conn.execute("PRAGMA secure_delete=ON")
        conn.execute("PRAGMA synchronous=FULL")
        
        return conn
    
    def encrypt_database_field(self, value: str) -> str:
        """Encrypt a database field value."""
        if value is None:
            return None
        return self.encrypt_data(str(value))
    
    def decrypt_database_field(self, encrypted_value: str) -> str:
        """Decrypt a database field value."""
        if encrypted_value is None:
            return None
        return self.decrypt_data(encrypted_value)
    
    def create_secure_backup(self, source_path: str, backup_path: str):
        """Create encrypted backup of database."""
        try:
            # Read source database
            with open(source_path, "rb") as f:
                data = f.read()
            
            # Encrypt the data
            encrypted_data = self.cipher_suite.encrypt(data)
            
            # Write encrypted backup
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(exist_ok=True)
            
            with open(backup_path, "wb") as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions
            backup_path.chmod(0o600)
            
            # Log backup creation
            self.log_audit_event(
                "backup_created",
                "system",
                {
                    "source": source_path,
                    "backup": str(backup_path),
                    "size": len(encrypted_data)
                }
            )
            
        except Exception as e:
            logging.error(f"Backup creation failed: {e}")
            raise
    
    def restore_from_backup(self, backup_path: str, restore_path: str):
        """Restore database from encrypted backup."""
        try:
            # Read encrypted backup
            with open(backup_path, "rb") as f:
                encrypted_data = f.read()
            
            # Decrypt the data
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            
            # Write restored database
            restore_path = Path(restore_path)
            restore_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(restore_path, "wb") as f:
                f.write(decrypted_data)
            
            # Set restrictive permissions
            restore_path.chmod(0o600)
            
            # Log restore operation
            self.log_audit_event(
                "backup_restored",
                "system",
                {
                    "backup": backup_path,
                    "restore": str(restore_path),
                    "size": len(decrypted_data)
                }
            )
            
        except Exception as e:
            logging.error(f"Backup restore failed: {e}")
            raise
    
    def get_audit_logs(self, start_date: Optional[datetime] = None, 
                      end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get audit logs within date range."""
        audit_file = Path("logs/audit.log")
        if not audit_file.exists():
            return []
        
        logs = []
        with open(audit_file, "r") as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    log_time = datetime.fromisoformat(log_entry["timestamp"])
                    
                    if start_date and log_time < start_date:
                        continue
                    if end_date and log_time > end_date:
                        continue
                    
                    logs.append(log_entry)
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
        
        return logs
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old audit logs."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Read all logs
        logs = self.get_audit_logs()
        
        # Filter recent logs
        recent_logs = [
            log for log in logs 
            if datetime.fromisoformat(log["timestamp"]) > cutoff_date
        ]
        
        # Write back recent logs
        audit_file = Path("logs/audit.log")
        with open(audit_file, "w") as f:
            for log in recent_logs:
                f.write(json.dumps(log) + "\n")
        
        # Log cleanup operation
        self.log_audit_event(
            "log_cleanup",
            "system",
            {
                "days_kept": days_to_keep,
                "logs_removed": len(logs) - len(recent_logs)
            }
        )

# Global data protection instance
data_protection = None

def get_data_protection(config) -> DataProtection:
    """Get global data protection instance."""
    global data_protection
    if data_protection is None:
        data_protection = DataProtection(config)
    return data_protection
