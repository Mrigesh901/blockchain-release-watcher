#!/usr/bin/env python3
"""
Test version comparison and production tag filtering.
This test verifies that the system correctly handles version comparisons
and filters out non-production tags to prevent noisy alerts.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.github_service import GitHubService


def test_version_comparison():
    """Test semantic version comparison."""
    print("Testing version comparison...")
    print("=" * 60)
    
    github_service = GitHubService()
    
    test_cases = [
        # (version1, version2, expected: -1=v1<v2, 0=equal, 1=v1>v2)
        ("v1.0.0", "v1.0.0", 0),
        ("v1.0.1", "v1.0.0", 1),
        ("v1.0.0", "v1.0.1", -1),
        ("v1.1.0", "v1.0.9", 1),
        ("v2.0.0", "v1.9.9", 1),
        ("1.36.1", "v0.9.6", 1),
        ("v0.9.6", "1.36.1", -1),
        ("v1.17.2", "v1.17.1", 1),
        # Versions with and without 'v' prefix
        ("1.0.0", "v1.0.0", 0),
        ("v1.0.0", "1.0.0", 0),
    ]
    
    passed = 0
    failed = 0
    
    for v1, v2, expected in test_cases:
        # Normalize versions first
        v1_norm = github_service._normalize_version(v1)
        v2_norm = github_service._normalize_version(v2)
        result = github_service._compare_versions(v1_norm, v2_norm)
        
        status = "✓" if result == expected else "❌"
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        result_str = "equal" if result == 0 else ("newer" if result > 0 else "older")
        expected_str = "equal" if expected == 0 else ("newer" if expected > 0 else "older")
        
        print(f"  {status} {v1:15} vs {v2:15} -> {result_str:6} (expected: {expected_str})")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_problematic_tags():
    """Test filtering of problematic tags that were causing noise."""
    print("\n" + "=" * 60)
    print("Testing problematic tag filtering...")
    print("=" * 60)
    
    github_service = GitHubService()
    
    # Tags that should be FILTERED OUT (non-production)
    non_production_tags = [
        "v1.17.2-1765930431",
        "v1.17.2-basefee-1769515040",
        "v1.14.1-set-with-bloom",
        "v1.14.1-randomize-compaction",
        "v2.0.0-rc.1",
        "v1.5.0-beta.2",
        "v1.3.0-alpha",
        "v1.2.0-dev",
        "v1.0.0-a1b2c3d",
        "v0.9.6-1234567890",
    ]
    
    # Tags that should PASS THROUGH (production)
    production_tags = [
        "v1.36.1",
        "v0.9.6",
        "v1.17.2",
        "v1.14.0",
        "v2.0.0",
        "1.5.3",
    ]
    
    print("\nNon-production tags (should be FILTERED):")
    filtered_count = 0
    for tag in non_production_tags:
        is_prod = github_service._is_production_tag(tag)
        status = "❌ PASSED" if is_prod else "✓ FILTERED"
        if not is_prod:
            filtered_count += 1
        print(f"  {status:12} {tag}")
    
    print(f"\nFiltered: {filtered_count}/{len(non_production_tags)}")
    
    print("\nProduction tags (should PASS):")
    passed_count = 0
    for tag in production_tags:
        is_prod = github_service._is_production_tag(tag)
        status = "✓ PASSED" if is_prod else "❌ FILTERED"
        if is_prod:
            passed_count += 1
        print(f"  {status:12} {tag}")
    
    print(f"\nPassed: {passed_count}/{len(production_tags)}")
    
    return filtered_count == len(non_production_tags) and passed_count == len(production_tags)


def test_version_normalization():
    """Test version normalization for consistent comparison."""
    print("\n" + "=" * 60)
    print("Testing version normalization...")
    print("=" * 60)
    
    github_service = GitHubService()
    
    test_cases = [
        ("1.36.1", "v1.36.1"),
        ("v0.9.6", "v0.9.6"),
        ("0.9.6", "v0.9.6"),
        ("v1.17.2", "v1.17.2"),
    ]
    
    passed = 0
    failed = 0
    
    for input_version, expected_output in test_cases:
        result = github_service._normalize_version(input_version)
        status = "✓" if result == expected_output else "❌"
        
        if result == expected_output:
            passed += 1
        else:
            failed += 1
        
        print(f"  {status} {input_version:15} -> {result:15} (expected: {expected_output})")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_update_detection_scenario():
    """Test the specific scenario causing noise."""
    print("\n" + "=" * 60)
    print("Testing update detection scenario...")
    print("=" * 60)
    
    github_service = GitHubService()
    
    scenarios = [
        {
            "name": "Flip-flop prevention: 1.36.1 vs v0.9.6",
            "last": "1.36.1",
            "latest": "v0.9.6",
            "should_alert": False,
            "reason": "Latest (v0.9.6) is older than last (1.36.1)"
        },
        {
            "name": "Flip-flop prevention: v0.9.6 vs 1.36.1",
            "last": "v0.9.6",
            "latest": "1.36.1",
            "should_alert": True,
            "reason": "Latest (1.36.1) is newer than last (v0.9.6)"
        },
        {
            "name": "Timestamp tag: v1.17.2-1765930431",
            "last": "v1.17.2",
            "latest": "v1.17.2-1765930431",
            "should_alert": False,
            "reason": "Timestamp tags should be filtered out"
        },
    ]
    
    passed = 0
    failed = 0
    
    for scenario in scenarios:
        last = github_service._normalize_version(scenario["last"])
        latest = github_service._normalize_version(scenario["latest"])
        
        # Check if latest tag would be filtered
        is_production = github_service._is_production_tag(latest)
        
        if not is_production:
            # Tag would be filtered, no update would be detected
            would_alert = False
        else:
            # Compare versions
            comparison = github_service._compare_versions(latest, last)
            would_alert = comparison > 0  # Alert if latest is newer
        
        status = "✓" if would_alert == scenario["should_alert"] else "❌"
        
        if would_alert == scenario["should_alert"]:
            passed += 1
        else:
            failed += 1
        
        alert_str = "WOULD ALERT" if would_alert else "NO ALERT"
        expected_str = "EXPECTED" if would_alert == scenario["should_alert"] else "UNEXPECTED"
        
        print(f"\n  {status} {scenario['name']}")
        print(f"     Last: {last}, Latest: {latest}")
        print(f"     Result: {alert_str} ({expected_str})")
        print(f"     Reason: {scenario['reason']}")
    
    print(f"\n\nResults: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    print("=" * 60)
    print("VERSION COMPARISON & TAG FILTERING TEST SUITE")
    print("=" * 60)
    
    all_passed = True
    
    all_passed &= test_version_comparison()
    all_passed &= test_problematic_tags()
    all_passed &= test_version_normalization()
    all_passed &= test_update_detection_scenario()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)
