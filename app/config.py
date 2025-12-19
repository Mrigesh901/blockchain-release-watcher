"""
Application configuration management.
Loads environment variables and provides configuration settings.
"""
import os
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration class."""
    
    # GitHub Configuration
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_API_BASE: str = "https://api.github.com"
    
    # GitLab Configuration
    GITLAB_TOKEN: str = os.getenv("GITLAB_TOKEN", "")
    GITLAB_API_BASE: str = os.getenv("GITLAB_API_BASE", "https://gitlab.com/api/v4")
    
    # Google Gemini Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.5-flash"
    #"gemini-pro"
    
    # Email Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "")
    EMAIL_TO: str = os.getenv("EMAIL_TO", "")
    EMAIL_ALERTS_ENABLED: bool = os.getenv("EMAIL_ALERTS_ENABLED", "true").lower() == "true"
    
    # Slack Configuration
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
    SLACK_ALERTS_ENABLED: bool = os.getenv("SLACK_ALERTS_ENABLED", "true").lower() == "true"
    
    # Flask Configuration
    FLASK_HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))
    
    # Application Configuration
    CHECK_INTERVAL_MINUTES: int = int(os.getenv("CHECK_INTERVAL_MINUTES", "60"))
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "./data/blockchain_monitor.db")
    
    # Monitored Repositories
    MONITORED_REPOS: List[str] = [
        repo.strip() 
        for repo in os.getenv("MONITORED_REPOS", "").split(",") 
        if repo.strip()
    ]
    
    # Repository-specific tag filters (optional)
    # Format: repo_name:tag_pattern1,tag_pattern2;another_repo:pattern
    # Example: ethereum-optimism/optimism:op-geth,op-node
    @classmethod
    def get_repo_tag_filters(cls) -> Dict[str, List[str]]:
        """
        Parse repository-specific tag filters from environment.
        
        Returns:
            Dictionary mapping repo names to list of tag patterns.
        """
        filters = {}
        filter_str = os.getenv("REPO_TAG_FILTERS", "")
        
        if filter_str:
            # Split by semicolon for different repos
            for repo_filter in filter_str.split(";"):
                repo_filter = repo_filter.strip()
                if not repo_filter:
                    continue
                    
                # Split repo name and patterns
                if ":" in repo_filter:
                    repo_name, patterns = repo_filter.split(":", 1)
                    repo_name = repo_name.strip()
                    # Split patterns by comma
                    pattern_list = [p.strip() for p in patterns.split(",") if p.strip()]
                    if repo_name and pattern_list:
                        filters[repo_name] = pattern_list
        
        return filters
    
    @classmethod
    def validate(cls) -> List[str]:
        """
        Validate required configuration.
        
        Returns:
            List of missing configuration keys.
        """
        missing = []
        
        # Check if we have tokens for the platforms being used
        has_gitlab_repos = any(repo.startswith("gitlab:") for repo in cls.MONITORED_REPOS)
        has_github_repos = any(not repo.startswith("gitlab:") for repo in cls.MONITORED_REPOS)
        
        if has_github_repos and not cls.GITHUB_TOKEN:
            missing.append("GITHUB_TOKEN (required for GitHub repositories)")
        if has_gitlab_repos and not cls.GITLAB_TOKEN:
            missing.append("GITLAB_TOKEN (required for GitLab repositories)")
        
        if not cls.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        
        # Check if at least one notification method is configured
        email_configured = (cls.SMTP_USERNAME and cls.SMTP_PASSWORD and 
                          cls.EMAIL_FROM and cls.EMAIL_TO and cls.EMAIL_ALERTS_ENABLED)
        slack_configured = cls.SLACK_WEBHOOK_URL and cls.SLACK_ALERTS_ENABLED
        
        if not email_configured and not slack_configured:
            missing.append("At least one notification method (Email or Slack)")
        
        if not cls.MONITORED_REPOS:
            missing.append("MONITORED_REPOS")
            
        return missing
