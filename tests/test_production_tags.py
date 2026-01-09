#!/usr/bin/env python3
"""
Test production tag filtering for ava-labs/avalanchego.
This test verifies that development/feature tags are filtered out.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.github_service import GitHubService


def test_production_tag_filter():
    """Test that non-production tags are filtered out."""
    print("Testing production tag filtering...")
    print("=" * 60)
    
    github_service = GitHubService()
    
    # Test tags that should be filtered out
    non_production_tags = [
        "v1.14.1-set-with-bloom",
        "v1.14.1-randomize-compaction",
        "v1.14.1-db-metrics-fix",
        "v1.14.1-antithesis-docker-image-fix",
        "v1.14.0-rc.0",
        "v1.14.0-fuji-rc.1",
        "v1.14.0-fuji",
        "v1.14.0-beta.1",
        "v1.13.0-alpha",
        "v1.12.0-dev",
    ]
    
    # Test tags that should pass through
    production_tags = [
        "v1.14.0",
        "v1.13.5",
        "v1.12.10",
    ]
    
    print("\nNon-production tags (should be filtered out):")
    for tag in non_production_tags:
        is_prod = github_service._is_production_tag(tag)
        status = "❌ PASSED THROUGH" if is_prod else "✓ FILTERED"
        print(f"  {tag:40} -> {status}")
    
    print("\nProduction tags (should pass through):")
    for tag in production_tags:
        is_prod = github_service._is_production_tag(tag)
        status = "✓ PASSED" if is_prod else "❌ FILTERED"
        print(f"  {tag:40} -> {status}")
    
    print("\n" + "=" * 60)
    print("Testing with real ava-labs/avalanchego repository...")
    print("=" * 60)
    
    # Get latest tag from ava-labs/avalanchego
    latest_tag = github_service.get_latest_tag("ava-labs", "avalanchego")
    
    if latest_tag:
        print(f"\n✓ Latest production tag found: {latest_tag['tag_name']}")
        print(f"  Type: {latest_tag['type']}")
        print(f"  Commit SHA: {latest_tag['commit_sha'][:12]}...")
    else:
        print("\n❌ No production tag found (this might indicate an issue)")
    
    # Get latest release
    latest_release = github_service.get_latest_release("ava-labs", "avalanchego")
    
    if latest_release:
        print(f"\n✓ Latest release found: {latest_release['tag_name']}")
        print(f"  Name: {latest_release['name']}")
        print(f"  Type: {latest_release['type']}")
        print(f"  Prerelease: {latest_release['prerelease']}")
    else:
        print("\n❌ No release found")
    
    print("\n" + "=" * 60)
    print("Test completed!")


if __name__ == "__main__":
    test_production_tag_filter()
