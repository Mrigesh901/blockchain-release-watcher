"""Database models and data structures."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Repository:
    """Repository monitoring record."""
    
    id: Optional[int]
    repo_name: str
    repo_url: str
    last_checked: Optional[str]
    last_version_or_tag: Optional[str]
    last_alerted_version: Optional[str]
    severity: Optional[str]
    mandatory_upgrade: bool
    created_at: Optional[str]
    updated_at: Optional[str]


@dataclass
class AlertHistory:
    """Alert history record."""
    
    id: Optional[int]
    repo_name: str
    version: str
    severity: str
    mandatory_upgrade: bool
    summary: str
    alerted_at: str
