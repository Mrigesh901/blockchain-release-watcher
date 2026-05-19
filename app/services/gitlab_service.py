"""
GitLab API service.
Handles interaction with GitLab REST API for releases, tags, and commits.
"""
import requests
import re
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from urllib.parse import quote

from app.config import Config


class GitLabService:
    """Service for interacting with GitLab API."""
    
    def __init__(self, tag_filters: Optional[Dict[str, List[str]]] = None):
        """Initialize GitLab service with API token and optional tag filters.
        
        Args:
            tag_filters: Dictionary mapping repo names to list of tag patterns to filter.
        """
        self.token = Config.GITLAB_TOKEN
        self.base_url = Config.GITLAB_API_BASE
        self.headers = {
            "PRIVATE-TOKEN": self.token
        } if self.token else {}
        self.tag_filters = tag_filters or {}
    
    def _make_request(self, url: str) -> Optional[Dict[Any, Any]]:
        """
        Make authenticated request to GitLab API.
        
        Args:
            url: API endpoint URL.
            
        Returns:
            JSON response or None on error.
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 404:
                print(f"Resource not found: {url}")
                return None
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError as e:
            print(f"GitLab API connection error: {e}")
            return None
        except requests.exceptions.Timeout as e:
            print(f"GitLab API timeout: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"GitLab API request failed: {e}")
            return None
    
    def _is_semantic_version(self, tag_name: str) -> bool:
        """
        Check if tag follows semantic versioning.
        
        Args:
            tag_name: Tag name to check.
            
        Returns:
            True if tag is semantic version.
        """
        # Match v1.2.3, 1.2.3, v1.2.3-beta, etc.
        pattern = r'^v?\d+\.\d+\.\d+.*$'
        return bool(re.match(pattern, tag_name))
    
    def _matches_tag_filter(self, tag_name: str, repo_name: str) -> bool:
        """
        Check if tag matches any filter patterns for the repository.
        
        Args:
            tag_name: Tag name to check.
            repo_name: Repository name (group/project).
            
        Returns:
            True if tag matches filter or no filter exists for this repo.
        """
        # If no filter for this repo, accept all tags
        if repo_name not in self.tag_filters:
            return True
        
        patterns = self.tag_filters[repo_name]
        tag_lower = tag_name.lower()
        
        # Check if tag contains any of the filter patterns
        for pattern in patterns:
            pattern_lower = pattern.lower()
            if pattern_lower in tag_lower:
                return True
        
        return False
    
    def _extract_version(self, tag_name: str) -> str:
        """
        Extract version number from tag name.
        
        Args:
            tag_name: Tag name.
            
        Returns:
            Version string.
        """
        # Remove 'v' prefix if present
        return tag_name.lstrip('v')
    
    def _is_production_tag(self, tag_name: str) -> bool:
        """
        Check if tag is a production release (not a dev/test/feature tag).
        
        Args:
            tag_name: Tag name to check.
            
        Returns:
            True if tag appears to be a production release.
        """
        tag_lower = tag_name.lower()
        
        # Exclude common non-production suffixes
        non_production_patterns = [
            '-rc',           # release candidate
            '-alpha',        # alpha release
            '-beta',         # beta release
            '-dev',          # development
            '-test',         # test
            '-snapshot',     # snapshot
            '-nightly',      # nightly build
            '-preview',      # preview
            '-experimental', # experimental
            '-set-with',     # feature branch
            '-randomize',    # feature branch
            '-db-metrics',   # feature branch
            '-basefee',      # feature branch
            '-pre',          # pre-release
            '-canary',       # canary release
            '-edge',         # edge build
        ]
        
        # Check if tag contains any non-production pattern
        for pattern in non_production_patterns:
            if pattern in tag_lower:
                return False
        
        # Check for timestamp-based tags (e.g., v1.17.2-1765930431)
        timestamp_pattern = r'-\d{10,}'
        if re.search(timestamp_pattern, tag_name):
            return False
        
        # Check for hash-like suffixes (e.g., -a1b2c3d)
        hash_pattern = r'-[0-9a-f]{6,8}$'
        if re.search(hash_pattern, tag_lower):
            return False
        
        # Check for unrealistic major version numbers
        clean_tag = tag_name.lstrip('v')
        version_parts = clean_tag.split('.')[0].split('-')[0]
        try:
            major_version = int(version_parts)
            # Major version > 1000 is likely a date-based or malformed tag
            if major_version > 1000:
                return False
        except (ValueError, IndexError):
            pass
        
        # Check for date-like patterns that might be malformed
        date_pattern = r'^v?\d{4,5}\.\d{1,2}\.\d{1,2}'
        if re.match(date_pattern, tag_name):
            return False
        
        return True
    
    def _normalize_version(self, version: str) -> str:
        """
        Normalize version string for consistent comparison.
        
        Args:
            version: Version string with or without 'v' prefix.
            
        Returns:
            Normalized version string with 'v' prefix.
        """
        if not version:
            return ""
        
        if not version.startswith('v'):
            return f"v{version}"
        return version
    
    def _parse_version_parts(self, version: str) -> tuple:
        """
        Parse version string into comparable parts.
        
        Args:
            version: Version string (e.g., 'v1.2.3' or '1.2.3-beta')
            
        Returns:
            Tuple of (major, minor, patch, suffix) for comparison.
        """
        clean_version = version.lstrip('v')
        parts = clean_version.split('-', 1)
        version_part = parts[0]
        suffix = parts[1] if len(parts) > 1 else ""
        
        try:
            version_numbers = version_part.split('.')
            major = int(version_numbers[0]) if len(version_numbers) > 0 else 0
            minor = int(version_numbers[1]) if len(version_numbers) > 1 else 0
            patch = int(version_numbers[2]) if len(version_numbers) > 2 else 0
            return (major, minor, patch, suffix)
        except (ValueError, IndexError):
            return (0, 0, 0, clean_version)
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two semantic versions.
        
        Args:
            version1: First version string.
            version2: Second version string.
            
        Returns:
            -1 if version1 < version2, 0 if equal, 1 if version1 > version2
        """
        if not version1 and not version2:
            return 0
        if not version1:
            return -1
        if not version2:
            return 1
        
        v1_parts = self._parse_version_parts(version1)
        v2_parts = self._parse_version_parts(version2)
        
        for i in range(3):
            if v1_parts[i] < v2_parts[i]:
                return -1
            elif v1_parts[i] > v2_parts[i]:
                return 1
        
        # If version numbers are equal, version without suffix is greater
        suffix1, suffix2 = v1_parts[3], v2_parts[3]
        if not suffix1 and suffix2:
            return 1
        elif suffix1 and not suffix2:
            return -1
        
        return 0
    
    def get_latest_release(self, group: str, project: str, filter_key: str = None) -> Optional[Dict[str, Any]]:
        """
        Get latest release from GitLab project.
        
        Args:
            group: Project group/namespace.
            project: Project name.
            filter_key: Key to use for tag filter lookup (defaults to group/project).
            
        Returns:
            Release data or None if no releases exist.
        """
        repo_name = filter_key or f"{group}/{project}"
        project_id = quote(f"{group}/{project}", safe='')
        
        # If tag filters exist for this repo, get all releases and filter
        if repo_name in self.tag_filters:
            url = f"{self.base_url}/projects/{project_id}/releases"
            data = self._make_request(url)
            
            if data and isinstance(data, list):
                for release in data:
                    tag_name = release.get("tag_name", "")
                    if self._matches_tag_filter(tag_name, repo_name):
                        return {
                            "type": "release",
                            "name": release.get("name", release.get("tag_name")),
                            "tag_name": tag_name,
                            "released_at": release.get("released_at"),
                            "body": release.get("description", ""),
                            "html_url": release.get("_links", {}).get("self", ""),
                        }
            return None
        
        # No filter - get latest release
        url = f"{self.base_url}/projects/{project_id}/releases"
        data = self._make_request(url)
        
        if data and isinstance(data, list) and len(data) > 0:
            release = data[0]  # First release is the latest
            return {
                "type": "release",
                "name": release.get("name", release.get("tag_name")),
                "tag_name": release.get("tag_name"),
                "released_at": release.get("released_at"),
                "body": release.get("description", ""),
                "html_url": release.get("_links", {}).get("self", ""),
            }
        
        return None
    
    def get_latest_tag(self, group: str, project: str, filter_key: str = None) -> Optional[Dict[str, Any]]:
        """
        Get latest semantic version tag from repository.
        
        Args:
            group: Project group/namespace.
            project: Project name.
            filter_key: Key to use for tag filter lookup (defaults to group/project).
            
        Returns:
            Tag data or None if no tags exist.
        """
        repo_name = filter_key or f"{group}/{project}"
        project_id = quote(f"{group}/{project}", safe='')
        url = f"{self.base_url}/projects/{project_id}/repository/tags"
        data = self._make_request(url)
        
        if data and isinstance(data, list) and len(data) > 0:
            # Find first production semantic version tag that matches filter
            for tag in data:
                tag_name = tag.get("name", "")
                if (self._is_semantic_version(tag_name) and 
                    self._is_production_tag(tag_name) and 
                    self._matches_tag_filter(tag_name, repo_name)):
                    return {
                        "type": "tag",
                        "name": tag_name,
                        "tag_name": tag_name,
                        "commit_sha": tag.get("commit", {}).get("id"),
                        "commit_url": tag.get("commit", {}).get("web_url")
                    }
        
        return None
    
    def get_latest_version(self, group: str, project: str, filter_key: str = None) -> Optional[Dict[str, Any]]:
        """
        Get latest version - prioritize releases, fall back to tags.
        
        Args:
            group: Project group/namespace.
            project: Project name.
            filter_key: Key to use for tag filter lookup (e.g., 'tezos/tezos#octez').
            
        Returns:
            Version data (release or tag) or None.
        """
        # Try to get latest release first
        release = self.get_latest_release(group, project, filter_key=filter_key)
        if release:
            return release
        
        # Fall back to tags
        tag = self.get_latest_tag(group, project, filter_key=filter_key)
        return tag
    
    def compare_commits(self, group: str, project: str, 
                       base: str, head: str) -> Optional[Dict[str, Any]]:
        """
        Compare commits between two versions.
        
        Args:
            group: Project group/namespace.
            project: Project name.
            base: Base version/tag.
            head: Head version/tag.
            
        Returns:
            Comparison data including commit messages.
        """
        project_id = quote(f"{group}/{project}", safe='')
        url = f"{self.base_url}/projects/{project_id}/repository/compare?from={base}&to={head}"
        data = self._make_request(url)
        
        if data:
            commits = data.get("commits", [])
            commit_messages = [
                commit.get("message", "")
                for commit in commits
            ]
            
            return {
                "ahead_by": len(commits),
                "total_commits": len(commits),
                "commit_messages": commit_messages,
                "html_url": data.get("web_url", "")
            }
        
        return None
    
    def get_commit_messages_between_tags(self, group: str, project: str,
                                        old_tag: str, new_tag: str) -> List[str]:
        """
        Get commit messages between two tags.
        
        Args:
            group: Project group/namespace.
            project: Project name.
            old_tag: Old tag name.
            new_tag: New tag name.
            
        Returns:
            List of commit messages.
        """
        comparison = self.compare_commits(group, project, old_tag, new_tag)
        
        if comparison:
            return comparison.get("commit_messages", [])
        
        return []
    
    def parse_repo_name(self, repo_name: str) -> Tuple[str, str]:
        """
        Parse repository name into group and project.
        
        Args:
            repo_name: Repository name in format 'group/project' or 'group/project#alias'.
            
        Returns:
            Tuple of (group, project).
        """
        # Strip component alias (e.g., "tezos/tezos#octez" -> "tezos/tezos")
        clean = repo_name.split('#', 1)[0]
        parts = clean.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid repository name format: {repo_name}")
        
        return parts[0], parts[1]
    
    def check_for_updates(self, repo_name: str, 
                         last_version: Optional[str] = None) -> Dict[str, Any]:
        """
        Check if repository has new version available.
        
        Args:
            repo_name: Repository name (group/project).
            last_version: Last known version.
            
        Returns:
            Dictionary with update information.
        """
        group, project = self.parse_repo_name(repo_name)
        
        # Get latest version, passing full repo_name (with #alias) as filter_key
        latest = self.get_latest_version(group, project, filter_key=repo_name)
        
        if not latest:
            return {
                "has_update": False,
                "error": "Could not fetch latest version"
            }
        
        latest_version = latest.get("tag_name")
        
        # Normalize versions for consistent comparison
        latest_version_normalized = self._normalize_version(latest_version)
        
        # If no previous version, this is first check
        if not last_version:
            return {
                "has_update": True,
                "is_first_check": True,
                "old_version": None,
                "new_version": latest_version_normalized,
                "release_notes": latest.get("body", ""),
                "version_type": latest.get("type"),
                "html_url": latest.get("html_url", ""),
                "commit_messages": []
            }
        
        # Normalize last version for comparison
        last_version_normalized = self._normalize_version(last_version)
        
        # Compare versions semantically
        comparison = self._compare_versions(latest_version_normalized, last_version_normalized)
        
        # If latest version is not newer, no update
        if comparison <= 0:
            return {
                "has_update": False,
                "current_version": last_version_normalized
            }
        
        # New version detected (latest is newer than last)
        result = {
            "has_update": True,
            "is_first_check": False,
            "old_version": last_version_normalized,
            "new_version": latest_version_normalized,
            "release_notes": latest.get("body", ""),
            "version_type": latest.get("type"),
            "html_url": latest.get("html_url", ""),
            "commit_messages": []
        }
        
        # If no release notes, get commit messages between versions
        if not result["release_notes"] and latest.get("type") == "tag" and latest_version_normalized:
            commit_messages = self.get_commit_messages_between_tags(
                group, project, last_version_normalized, latest_version_normalized
            )
            result["commit_messages"] = commit_messages
        
        return result
    
    def get_repo_url(self, repo_name: str) -> str:
        """
        Get GitLab repository URL.
        
        Args:
            repo_name: Repository name (group/project).
            
        Returns:
            Repository URL.
        """
        # Extract base GitLab instance URL from API base
        gitlab_host = self.base_url.replace("/api/v4", "")
        return f"{gitlab_host}/{repo_name}"
