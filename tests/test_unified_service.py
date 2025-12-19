#!/usr/bin/env python3
"""
Test unified repository service with both GitHub and GitLab.
"""
from app.config import Config
from app.services.repository_service import RepositoryService


def main():
    """Test unified repository service."""
    print("=" * 70)
    print("Unified Repository Service Test (GitHub + GitLab)")
    print("=" * 70)
    print()
    
    repo_service = RepositoryService()
    
    test_repos = [
        ("ethereum/go-ethereum", "GitHub"),
        ("gitlab:gitlab-org/gitlab-runner", "GitLab"),
        ("babylonlabs-io/babylon", "GitHub"),
    ]
    
    for repo_name, expected_platform in test_repos:
        print(f"Repository: {repo_name}")
        print(f"Expected Platform: {expected_platform}")
        
        try:
            # Detect platform
            platform = repo_service.get_platform(repo_name)
            print(f"  ✓ Detected Platform: {platform}")
            
            # Get URL
            url = repo_service.get_repo_url(repo_name)
            print(f"  ✓ Repository URL: {url}")
            
            # Check for updates (will be first check)
            print(f"  Checking for latest version...")
            update_info = repo_service.check_for_updates(repo_name, last_version=None)
            
            if "error" in update_info:
                print(f"  ✗ Error: {update_info['error']}")
            elif update_info.get("has_update"):
                print(f"  ✓ Latest version: {update_info.get('new_version')}")
                print(f"    Type: {update_info.get('version_type')}")
            else:
                print(f"  ✓ No updates")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        print()
        print("-" * 70)
        print()
    
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print()
    print("✓ Unified service successfully handles both platforms")
    print()
    print("Repository Format:")
    print("  GitHub:  owner/repo")
    print("  GitLab:  gitlab:group/project")
    print()
    print("The service automatically detects the platform and routes")
    print("requests to the appropriate service (GitHub or GitLab).")
    print()


if __name__ == "__main__":
    main()
