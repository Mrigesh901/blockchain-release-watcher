"""
Unified repository service.
Handles both GitHub and GitLab repositories.
"""
from typing import Optional, Dict, Any, List
from app.services.github_service import GitHubService
from app.services.gitlab_service import GitLabService


class RepositoryService:
    """Unified service for interacting with GitHub and GitLab repositories."""
    
    def __init__(self, tag_filters: Optional[Dict[str, List[str]]] = None):
        """
        Initialize repository service with both GitHub and GitLab services.
        
        Args:
            tag_filters: Dictionary mapping repo names to list of tag patterns to filter.
        """
        self.github_service = GitHubService(tag_filters=tag_filters)
        self.gitlab_service = GitLabService(tag_filters=tag_filters)
        self.tag_filters = tag_filters or {}
    
    def _detect_platform(self, repo_name: str) -> str:
        """
        Detect if repository is from GitHub or GitLab.
        
        Args:
            repo_name: Repository name (can include platform prefix).
            
        Returns:
            'github' or 'gitlab'.
        """
        # Check for explicit prefix
        if repo_name.startswith("gitlab:"):
            return "gitlab"
        if repo_name.startswith("github:"):
            return "github"
        
        # Default to GitHub for backward compatibility
        return "github"
    
    def _clean_repo_name(self, repo_name: str) -> str:
        """
        Remove platform prefix from repository name.
        
        Args:
            repo_name: Repository name with optional prefix.
            
        Returns:
            Clean repository name without prefix.
        """
        if repo_name.startswith("gitlab:"):
            return repo_name[7:]  # Remove 'gitlab:' prefix
        if repo_name.startswith("github:"):
            return repo_name[7:]  # Remove 'github:' prefix
        return repo_name
    
    def check_for_updates(self, repo_name: str, 
                         last_version: Optional[str] = None) -> Dict[str, Any]:
        """
        Check if repository has new version available.
        
        Args:
            repo_name: Repository name (owner/repo or gitlab:group/project).
            last_version: Last known version.
            
        Returns:
            Dictionary with update information.
        """
        platform = self._detect_platform(repo_name)
        clean_name = self._clean_repo_name(repo_name)
        
        if platform == "gitlab":
            return self.gitlab_service.check_for_updates(clean_name, last_version)
        else:
            return self.github_service.check_for_updates(clean_name, last_version)
    
    def get_repo_url(self, repo_name: str) -> str:
        """
        Get repository URL.
        
        Args:
            repo_name: Repository name (owner/repo or gitlab:group/project).
            
        Returns:
            Repository URL.
        """
        platform = self._detect_platform(repo_name)
        clean_name = self._clean_repo_name(repo_name)
        
        if platform == "gitlab":
            return self.gitlab_service.get_repo_url(clean_name)
        else:
            return self.github_service.get_repo_url(clean_name)
    
    def get_platform(self, repo_name: str) -> str:
        """
        Get platform name for repository.
        
        Args:
            repo_name: Repository name.
            
        Returns:
            'GitHub' or 'GitLab'.
        """
        platform = self._detect_platform(repo_name)
        return "GitLab" if platform == "gitlab" else "GitHub"
