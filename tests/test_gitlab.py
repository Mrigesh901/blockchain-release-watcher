#!/usr/bin/env python3
"""
Test GitLab integration.
"""
from app.config import Config
from app.services.gitlab_service import GitLabService


def main():
    """Test GitLab service."""
    print("=" * 60)
    print("GitLab Service Test")
    print("=" * 60)
    print()
    
    # Check configuration
    print("Configuration:")
    print(f"  GitLab Token Configured: {bool(Config.GITLAB_TOKEN)}")
    print(f"  GitLab API Base: {Config.GITLAB_API_BASE}")
    print()
    
    if not Config.GITLAB_TOKEN:
        print("⚠ GitLab token not configured")
        print("  Note: GitLab token is optional for public repositories")
        print()
    
    # Test with a public GitLab repository
    print("-" * 60)
    print("Testing with public GitLab repository...")
    print("-" * 60)
    print()
    
    test_repo = "gitlab-org/gitlab-runner"  # Public repo
    print(f"Repository: {test_repo}")
    print()
    
    gitlab_service = GitLabService()
    
    try:
        # Test getting latest version
        print("Fetching latest version...")
        group, project = gitlab_service.parse_repo_name(test_repo)
        latest = gitlab_service.get_latest_version(group, project)
        
        if latest:
            print(f"✓ Latest version: {latest.get('tag_name')}")
            print(f"  Type: {latest.get('type')}")
            if latest.get('body'):
                print(f"  Description: {latest.get('body')[:100]}...")
            print()
        else:
            print("✗ Could not fetch latest version")
            print()
        
        # Test repo URL
        print("Testing repository URL generation...")
        repo_url = gitlab_service.get_repo_url(test_repo)
        print(f"✓ Repository URL: {repo_url}")
        print()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print()
    
    print("=" * 60)
    print("Summary:")
    print("=" * 60)
    print()
    print("To monitor GitLab repositories:")
    print("1. Add 'gitlab:' prefix to repository name in MONITORED_REPOS")
    print("   Example: gitlab:gitlab-org/gitlab-runner")
    print()
    print("2. (Optional) Add GITLAB_TOKEN to .env for private repos")
    print("   Get token from: https://gitlab.com/-/profile/personal_access_tokens")
    print()
    print("3. For self-hosted GitLab, set GITLAB_API_BASE")
    print("   Example: GITLAB_API_BASE=https://gitlab.example.com/api/v4")
    print()


if __name__ == "__main__":
    main()
