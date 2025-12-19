"""
SQLite database management.
Handles database initialization, schema creation, and CRUD operations.
"""
import sqlite3
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from app.models import Repository, AlertHistory


class Database:
    """SQLite database manager for blockchain monitor."""
    
    def __init__(self, db_path: str):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_schema()
    
    def _ensure_db_directory(self):
        """Create database directory if it doesn't exist."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Database connection.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_schema(self):
        """Initialize database schema."""
        schema = """
        CREATE TABLE IF NOT EXISTS repositories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_name TEXT UNIQUE NOT NULL,
            repo_url TEXT NOT NULL,
            last_checked TEXT,
            last_version_or_tag TEXT,
            last_alerted_version TEXT,
            severity TEXT,
            mandatory_upgrade INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS alert_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_name TEXT NOT NULL,
            version TEXT NOT NULL,
            severity TEXT NOT NULL,
            mandatory_upgrade INTEGER NOT NULL,
            summary TEXT,
            alerted_at TEXT NOT NULL,
            FOREIGN KEY (repo_name) REFERENCES repositories (repo_name)
        );
        
        CREATE INDEX IF NOT EXISTS idx_repo_name ON repositories(repo_name);
        CREATE INDEX IF NOT EXISTS idx_alert_repo ON alert_history(repo_name);
        CREATE INDEX IF NOT EXISTS idx_alert_date ON alert_history(alerted_at);
        """
        
        with self._get_connection() as conn:
            conn.executescript(schema)
    
    def get_repository(self, repo_name: str) -> Optional[Repository]:
        """
        Get repository by name.
        
        Args:
            repo_name: Repository name (owner/repo).
            
        Returns:
            Repository object or None if not found.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM repositories WHERE repo_name = ?",
                (repo_name,)
            )
            row = cursor.fetchone()
            
            if row:
                return Repository(
                    id=row["id"],
                    repo_name=row["repo_name"],
                    repo_url=row["repo_url"],
                    last_checked=row["last_checked"],
                    last_version_or_tag=row["last_version_or_tag"],
                    last_alerted_version=row["last_alerted_version"],
                    severity=row["severity"],
                    mandatory_upgrade=bool(row["mandatory_upgrade"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
            return None
    
    def get_all_repositories(self) -> List[Repository]:
        """
        Get all monitored repositories.
        
        Returns:
            List of Repository objects.
        """
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM repositories ORDER BY repo_name")
            rows = cursor.fetchall()
            
            return [
                Repository(
                    id=row["id"],
                    repo_name=row["repo_name"],
                    repo_url=row["repo_url"],
                    last_checked=row["last_checked"],
                    last_version_or_tag=row["last_version_or_tag"],
                    last_alerted_version=row["last_alerted_version"],
                    severity=row["severity"],
                    mandatory_upgrade=bool(row["mandatory_upgrade"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
                for row in rows
            ]
    
    def upsert_repository(self, repo_name: str, repo_url: str, 
                         last_version_or_tag: Optional[str] = None,
                         last_alerted_version: Optional[str] = None,
                         severity: Optional[str] = None,
                         mandatory_upgrade: bool = False) -> None:
        """
        Insert or update repository record.
        
        Args:
            repo_name: Repository name (owner/repo).
            repo_url: Repository URL.
            last_version_or_tag: Latest detected version or tag.
            last_alerted_version: Last version that triggered an alert.
            severity: Severity level.
            mandatory_upgrade: Whether upgrade is mandatory.
        """
        now = datetime.utcnow().isoformat()
        
        with self._get_connection() as conn:
            # Check if repository exists
            existing = self.get_repository(repo_name)
            
            if existing:
                # Update existing
                conn.execute(
                    """
                    UPDATE repositories 
                    SET repo_url = ?,
                        last_checked = ?,
                        last_version_or_tag = COALESCE(?, last_version_or_tag),
                        last_alerted_version = COALESCE(?, last_alerted_version),
                        severity = COALESCE(?, severity),
                        mandatory_upgrade = ?,
                        updated_at = ?
                    WHERE repo_name = ?
                    """,
                    (repo_url, now, last_version_or_tag, last_alerted_version,
                     severity, int(mandatory_upgrade), now, repo_name)
                )
            else:
                # Insert new
                conn.execute(
                    """
                    INSERT INTO repositories 
                    (repo_name, repo_url, last_checked, last_version_or_tag, 
                     last_alerted_version, severity, mandatory_upgrade, 
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (repo_name, repo_url, now, last_version_or_tag,
                     last_alerted_version, severity, int(mandatory_upgrade), 
                     now, now)
                )
    
    def add_alert_history(self, repo_name: str, version: str, severity: str,
                          mandatory_upgrade: bool, summary: str) -> None:
        """
        Add alert to history.
        
        Args:
            repo_name: Repository name.
            version: Version that triggered alert.
            severity: Severity level.
            mandatory_upgrade: Whether upgrade is mandatory.
            summary: AI-generated summary.
        """
        now = datetime.utcnow().isoformat()
        
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO alert_history 
                (repo_name, version, severity, mandatory_upgrade, summary, alerted_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (repo_name, version, severity, int(mandatory_upgrade), summary, now)
            )
    
    def get_alert_history(self, repo_name: Optional[str] = None, 
                         limit: int = 50) -> List[AlertHistory]:
        """
        Get alert history.
        
        Args:
            repo_name: Optional repository name to filter by.
            limit: Maximum number of records to return.
            
        Returns:
            List of AlertHistory objects.
        """
        with self._get_connection() as conn:
            if repo_name:
                cursor = conn.execute(
                    """
                    SELECT * FROM alert_history 
                    WHERE repo_name = ? 
                    ORDER BY alerted_at DESC 
                    LIMIT ?
                    """,
                    (repo_name, limit)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM alert_history 
                    ORDER BY alerted_at DESC 
                    LIMIT ?
                    """,
                    (limit,)
                )
            
            rows = cursor.fetchall()
            
            return [
                AlertHistory(
                    id=row["id"],
                    repo_name=row["repo_name"],
                    version=row["version"],
                    severity=row["severity"],
                    mandatory_upgrade=bool(row["mandatory_upgrade"]),
                    summary=row["summary"],
                    alerted_at=row["alerted_at"]
                )
                for row in rows
            ]
