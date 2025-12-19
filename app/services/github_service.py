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
            # Find first semantic version tag that matches filter
            for tag in data:
                tag_name = tag.get("name", "")
                if self._is_semantic_version(tag_name) and self._matches_tag_filter(tag_name, repo_name):
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
        
        # If no previous version, this is first check
        if not last_version:
            return {
                "has_update": True,
                "is_first_check": True,
                "old_version": None,
                "new_version": latest_version,
                "release_notes": latest.get("body", ""),
                "version_type": latest.get("type"),
                "html_url": latest.get("html_url", ""),
                "commit_messages": []
            }
        
        # Check if version has changed
        if latest_version == last_version:
            return {
                "has_update": False,
                "current_version": latest_version
            }
        
        # New version detected
        result = {
            "has_update": True,
            "is_first_check": False,
            "old_version": last_version,
            "new_version": latest_version,
            "release_notes": latest.get("body", ""),
            "version_type": latest.get("type"),
            "html_url": latest.get("html_url", ""),
            "commit_messages": []
        }
        
        # If no release notes, get commit messages between versions
        if not result["release_notes"] and latest.get("type") == "tag" and latest_version:
            commit_messages = self.get_commit_messages_between_tags(
                owner, repo, last_version, latest_version
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
