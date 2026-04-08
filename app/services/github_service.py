"""
GitHub API service.
Handles interaction with GitHub REST API for releases, tags, and commits.
"""
import requests
import re
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from app.config import Config


class GitHubService:
    """Service for interacting with GitHub API."""
    
    def __init__(self, tag_filters: Optional[Dict[str, List[str]]] = None):
        """Initialize GitHub service with API token and optional tag filters.
        
        Args:
            tag_filters: Dictionary mapping repo names to list of tag patterns to filter.
        """
        self.token = Config.GITHUB_TOKEN
        self.base_url = Config.GITHUB_API_BASE
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        self.tag_filters = tag_filters or {}
    
    def _make_request(self, url: str) -> Optional[Dict[Any, Any]]:
        """
        Make authenticated request to GitHub API.
        
        Args:
            url: API endpoint URL.
            
        Returns:
            JSON response or None on error.
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            
            # Update rate limit info
            self.rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")
            self.rate_limit_reset = response.headers.get("X-RateLimit-Reset")
            
            if response.status_code == 403:
                print(f"Rate limit exceeded. Resets at: {self.rate_limit_reset}")
                return None
            
            if response.status_code == 404:
                print(f"Resource not found: {url}")
                return None
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError as e:
            print(f"GitHub API connection error: {e}")
            return None
        except requests.exceptions.Timeout as e:
            print(f"GitHub API timeout: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"GitHub API request failed: {e}")
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
            '-fuji',         # testnet (Avalanche specific)
            '-set-with',     # feature branch
            '-randomize',    # feature branch
            '-db-metrics',   # feature branch
            '-antithesis',   # testing/CI specific
            '-docker-image', # CI/build specific
            '-backport',     # backport branch
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
        # Pattern: version followed by dash and 10+ digits
        timestamp_pattern = r'-\d{10,}'
        if re.search(timestamp_pattern, tag_name):
            return False
        
        # Check for hash-like suffixes (e.g., -a1b2c3d)
        # Pattern: short alphanumeric strings that look like git hashes
        hash_pattern = r'-[0-9a-f]{6,8}$'
        if re.search(hash_pattern, tag_lower):
            return False
        
        # Check for unrealistic major version numbers
        # Parse the version to check if major version is suspiciously high
        clean_tag = tag_name.lstrip('v')
        version_parts = clean_tag.split('.')[0].split('-')[0]
        try:
            major_version = int(version_parts)
            # Major version > 1000 is likely a date-based or malformed tag
            # (e.g., v20201.01.02, v2020.01.02)
            if major_version > 1000:
                return False
        except (ValueError, IndexError):
            # If we can't parse it, let other checks handle it
            pass
        
        # Check for date-like patterns that might be malformed
        # Pattern: 4-5 digits at start (likely a year or malformed date)
        date_pattern = r'^v?\d{4,5}\.\d{1,2}\.\d{1,2}'
        if re.match(date_pattern, tag_name):
            return False
        
        # Tag appears to be production if it passes all checks
        return True
    
    def _matches_tag_filter(self, tag_name: str, repo_name: str) -> bool:
        """
        Check if tag matches any filter patterns for the repository.
        
        Args:
            tag_name: Tag name to check.
            repo_name: Repository name (owner/repo).
            
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
    
    def _normalize_version(self, version: str) -> str:
        """
        Normalize version string for consistent comparison.
        Ensures version always has 'v' prefix.
        
        Args:
            version: Version string with or without 'v' prefix.
            
        Returns:
            Normalized version string with 'v' prefix.
        """
        if not version:
            return ""
        
        # Add 'v' prefix if not present
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
        # Remove 'v' prefix
        clean_version = version.lstrip('v')
        
        # Split on dash to separate version from suffix
        parts = clean_version.split('-', 1)
        version_part = parts[0]
        suffix = parts[1] if len(parts) > 1 else ""
        
        # Parse version numbers
        try:
            version_numbers = version_part.split('.')
            major = int(version_numbers[0]) if len(version_numbers) > 0 else 0
            minor = int(version_numbers[1]) if len(version_numbers) > 1 else 0
            patch = int(version_numbers[2]) if len(version_numbers) > 2 else 0
            return (major, minor, patch, suffix)
        except (ValueError, IndexError):
            # Return zeros if parsing fails
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
        
        # Parse both versions
        v1_parts = self._parse_version_parts(version1)
        v2_parts = self._parse_version_parts(version2)
        
        # Compare major, minor, patch
        for i in range(3):
            if v1_parts[i] < v2_parts[i]:
                return -1
            elif v1_parts[i] > v2_parts[i]:
                return 1
        
        # If version numbers are equal, version without suffix is greater
        # (e.g., v1.0.0 > v1.0.0-beta)
        suffix1, suffix2 = v1_parts[3], v2_parts[3]
        if not suffix1 and suffix2:
            return 1
        elif suffix1 and not suffix2:
            return -1
        
        # Both have suffixes or both don't - they're equal
        return 0
    
    def get_latest_release(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """
        Get latest release from GitHub repository.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            
        Returns:
            Release data or None if no releases exist.
        """
        repo_name = f"{owner}/{repo}"
        
        # If tag filters exist for this repo, get all releases and filter
        if repo_name in self.tag_filters:
            url = f"{self.base_url}/repos/{owner}/{repo}/releases"
            data = self._make_request(url)
            
            if data and isinstance(data, list):
                for release in data:
                    tag_name = release.get("tag_name", "")
                    if self._matches_tag_filter(tag_name, repo_name) and not release.get("prerelease", False):
                        return {
                            "type": "release",
                            "name": release.get("name", release.get("tag_name")),
                            "tag_name": tag_name,
                            "published_at": release.get("published_at"),
                            "body": release.get("body", ""),
                            "html_url": release.get("html_url"),
                            "prerelease": release.get("prerelease", False)
                        }
            return None
        
        # No filter - use the latest release endpoint
        url = f"{self.base_url}/repos/{owner}/{repo}/releases/latest"
        data = self._make_request(url)
        
        if data and not isinstance(data, list):
            return {
                "type": "release",
                "name": data.get("name", data.get("tag_name")),
                "tag_name": data.get("tag_name"),
                "published_at": data.get("published_at"),
                "body": data.get("body", ""),
                "html_url": data.get("html_url"),
                "prerelease": data.get("prerelease", False)
            }
        
        return None
    
    def get_latest_tag(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """
        Get latest semantic version tag from repository.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            
        Returns:
            Tag data or None if no tags exist.
        """
        repo_name = f"{owner}/{repo}"
        url = f"{self.base_url}/repos/{owner}/{repo}/tags"
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
                        "commit_sha": tag.get("commit", {}).get("sha"),
                        "commit_url": tag.get("commit", {}).get("url")
                    }
        
        return None
    
    def get_latest_version(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """
        Get latest version - prioritize releases, fall back to tags.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            
        Returns:
            Version data (release or tag) or None.
        """
        # Try to get latest release first
        release = self.get_latest_release(owner, repo)
        if release and not release.get("prerelease"):
            return release
        
        # Fall back to tags
        tag = self.get_latest_tag(owner, repo)
        return tag
    
    def compare_commits(self, owner: str, repo: str, 
                       base: str, head: str) -> Optional[Dict[str, Any]]:
        """
        Compare commits between two versions.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            base: Base version/tag.
            head: Head version/tag.
            
        Returns:
            Comparison data including commit messages.
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/compare/{base}...{head}"
        data = self._make_request(url)
        
        if data:
            commits = data.get("commits", [])
            commit_messages = [
                commit.get("commit", {}).get("message", "")
                for commit in commits
            ]
            
            return {
                "ahead_by": data.get("ahead_by", 0),
                "behind_by": data.get("behind_by", 0),
                "total_commits": data.get("total_commits", 0),
                "commit_messages": commit_messages,
                "html_url": data.get("html_url")
            }
        
        return None
    
    def get_commit_messages_between_tags(self, owner: str, repo: str,
                                        old_tag: str, new_tag: str) -> List[str]:
        """
        Get commit messages between two tags.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            old_tag: Old tag name.
            new_tag: New tag name.
            
        Returns:
            List of commit messages.
        """
        comparison = self.compare_commits(owner, repo, old_tag, new_tag)
        
        if comparison:
            return comparison.get("commit_messages", [])
        
        return []
    
    def parse_repo_name(self, repo_name: str) -> Tuple[str, str]:
        """
        Parse repository name into owner and repo.
        
        Args:
            repo_name: Repository name in format 'owner/repo'.
            
        Returns:
            Tuple of (owner, repo).
        """
        parts = repo_name.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid repository name format: {repo_name}")
        
        return parts[0], parts[1]
    
    def check_for_updates(self, repo_name: str, 
                         last_version: Optional[str] = None) -> Dict[str, Any]:
        """
        Check if repository has new version available.
        
        Args:
            repo_name: Repository name (owner/repo).
            last_version: Last known version.
            
        Returns:
            Dictionary with update information.
        """
        owner, repo = self.parse_repo_name(repo_name)
        
        # Get latest version
        latest = self.get_latest_version(owner, repo)
        
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
                owner, repo, last_version_normalized, latest_version_normalized
            )
            result["commit_messages"] = commit_messages
        
        return result
    
    def get_repo_url(self, repo_name: str) -> str:
        """
        Get GitHub repository URL.
        
        Args:
            repo_name: Repository name (owner/repo).
            
        Returns:
            Repository URL.
        """
        return f"https://github.com/{repo_name}"
