#!/usr/bin/env python3
"""
Demonstration of tag filtering feature.
Shows how the monitor handles multiple repos, some with filters and some without.
"""
from app.config import Config
from app.services.github_service import GitHubService


def demonstrate_filtering():
    """Demonstrate tag filtering with different scenarios."""
    print("=" * 70)
    print("TAG FILTERING DEMONSTRATION")
    print("=" * 70)
    print()
    
    # Show configuration
    print("Configuration:")
    print(f"  Monitored Repos: {Config.MONITORED_REPOS}")
    
    filters = Config.get_repo_tag_filters()
    if filters:
        print(f"  Tag Filters:")
        for repo, patterns in filters.items():
            print(f"    - {repo}: {', '.join(patterns)}")
    else:
        print("  Tag Filters: None configured")
    
    print()
    print("-" * 70)
    print()
    
    # Initialize GitHub service
    github_service = GitHubService(tag_filters=filters)
    
    # Test different repositories
    test_repos = [
        ("babylonlabs-io/babylon", "No filter - will track all releases"),
        ("ethereum-optimism/optimism", "Filtered - only op-geth and op-node"),
        ("InjectiveLabs/injective-chain-releases", "No filter - will track all releases"),
    ]
    
    for repo_name, description in test_repos:
        print(f"Repository: {repo_name}")
        print(f"Description: {description}")
        print()
        
        owner, repo = repo_name.split("/")
        
        try:
            # Get latest version
            latest = github_service.get_latest_version(owner, repo)
            
            if latest:
                tag_name = latest.get("tag_name")
                version_type = latest.get("type")
                
                print(f"  ✓ Latest version: {tag_name}")
                print(f"    Type: {version_type}")
                
                # Show if it matches a filter
                if repo_name in filters:
                    patterns = filters[repo_name]
                    matched = False
                    for pattern in patterns:
                        if pattern.lower() in tag_name.lower():
                            print(f"    ✓ Matches filter pattern: '{pattern}'")
                            matched = True
                            break
                    if not matched:
                        print(f"    ⚠ Does not match any filter pattern")
                else:
                    print(f"    No filter applied")
                
                # Show HTML URL if available
                if latest.get("html_url"):
                    print(f"    URL: {latest.get('html_url')}")
            else:
                print(f"  ✗ No matching releases found")
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        print()
        print("-" * 70)
        print()
    
    # Summary
    print("SUMMARY:")
    print()
    print("✓ Tag filtering allows you to monitor specific components from repos")
    print("  that publish multiple binaries (like Optimism with op-geth, op-node, etc.)")
    print()
    print("✓ Repos without filters continue to work normally, tracking all releases")
    print()
    print("✓ Configuration is simple: just add REPO_TAG_FILTERS to your .env file")
    print()
    print("Example:")
    print("  REPO_TAG_FILTERS=ethereum-optimism/optimism:op-geth,op-node")
    print()
    print("=" * 70)


if __name__ == "__main__":
    demonstrate_filtering()
