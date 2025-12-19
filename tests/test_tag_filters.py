#!/usr/bin/env python3
"""
Test script for tag filtering functionality.
Tests that the monitor correctly filters releases based on tag patterns.
"""
import sys
from app.config import Config
from app.services.github_service import GitHubService


def test_tag_filter_parsing():
    """Test that tag filters are parsed correctly from environment."""
    print("Testing tag filter parsing...")
    filters = Config.get_repo_tag_filters()
    
    print(f"✓ Parsed filters: {filters}")
    
    if "ethereum-optimism/optimism" in filters:
        patterns = filters["ethereum-optimism/optimism"]
        print(f"✓ Optimism filters: {patterns}")
        assert "op-geth" in patterns, "op-geth should be in filters"
        assert "op-node" in patterns, "op-node should be in filters"
    
    print()


def test_github_service_with_filters():
    """Test GitHub service with tag filters."""
    print("Testing GitHub service with tag filters...")
    
    filters = Config.get_repo_tag_filters()
    github_service = GitHubService(tag_filters=filters)
    
    print(f"✓ GitHubService initialized with filters: {list(filters.keys())}")
    print()


def test_tag_matching():
    """Test that tag matching logic works correctly."""
    print("Testing tag matching logic...")
    
    filters = {
        "ethereum-optimism/optimism": ["op-geth", "op-node"]
    }
    
    github_service = GitHubService(tag_filters=filters)
    
    # Test cases
    test_cases = [
        ("op-geth-v1.0.0", "ethereum-optimism/optimism", True, "Should match op-geth"),
        ("op-node-v2.1.0", "ethereum-optimism/optimism", True, "Should match op-node"),
        ("op-proposer-v1.0.0", "ethereum-optimism/optimism", False, "Should NOT match op-proposer"),
        ("v1.0.0", "ethereum-optimism/optimism", False, "Should NOT match generic version"),
        ("v1.0.0", "other/repo", True, "Should match (no filter for this repo)"),
    ]
    
    for tag_name, repo_name, expected, description in test_cases:
        result = github_service._matches_tag_filter(tag_name, repo_name)
        status = "✓" if result == expected else "✗"
        print(f"{status} {description}: '{tag_name}' in {repo_name} -> {result}")
        
        if result != expected:
            print(f"  FAILED: Expected {expected}, got {result}")
            sys.exit(1)
    
    print()


def test_optimism_releases():
    """Test fetching filtered releases from Optimism repo."""
    print("Testing Optimism repository with filters...")
    
    filters = Config.get_repo_tag_filters()
    github_service = GitHubService(tag_filters=filters)
    
    try:
        print("Fetching latest op-geth or op-node release from ethereum-optimism/optimism...")
        latest = github_service.get_latest_version("ethereum-optimism", "optimism")
        
        if latest:
            tag_name = latest.get("tag_name")
            version_type = latest.get("type")
            print(f"✓ Found: {tag_name} (type: {version_type})")
            
            # Verify it matches our filter
            if "op-geth" in tag_name.lower() or "op-node" in tag_name.lower():
                print(f"✓ Tag matches filter criteria")
            else:
                print(f"✗ WARNING: Tag '{tag_name}' doesn't contain op-geth or op-node")
        else:
            print("✗ No matching releases found")
            print("  This could mean:")
            print("  - No releases match the filter patterns")
            print("  - GitHub API rate limit reached")
            print("  - Repository has no releases")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
    
    print()


def main():
    """Run all tests."""
    print("=" * 60)
    print("Tag Filter Testing")
    print("=" * 60)
    print()
    
    # Check configuration
    if not Config.GITHUB_TOKEN:
        print("✗ ERROR: GITHUB_TOKEN not set in .env")
        sys.exit(1)
    
    print(f"✓ GitHub token configured")
    print(f"✓ Monitored repos: {Config.MONITORED_REPOS}")
    print()
    
    # Run tests
    test_tag_filter_parsing()
    test_github_service_with_filters()
    test_tag_matching()
    test_optimism_releases()
    
    print("=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
