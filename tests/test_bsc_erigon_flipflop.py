#!/usr/bin/env python3
"""
Test the specific v1.4.3 ↔ v20201.01.02 flip-flop issue.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.github_service import GitHubService


def test_bsc_erigon_scenario():
    """Test the specific BSC Erigon flip-flop scenario."""
    print("=" * 60)
    print("Testing BSC Erigon v1.4.3 ↔ v20201.01.02 Flip-Flop")
    print("=" * 60)
    
    github_service = GitHubService()
    
    print("\n1. Checking if v20201.01.02 is filtered as non-production:")
    is_production = github_service._is_production_tag("v20201.01.02")
    print(f"   v20201.01.02 is production: {is_production}")
    if not is_production:
        print("   ✓ CORRECT: Tag will be filtered out")
    else:
        print("   ❌ ERROR: Tag should be filtered")
    
    print("\n2. Checking if v1.4.3 is accepted as production:")
    is_production = github_service._is_production_tag("v1.4.3")
    print(f"   v1.4.3 is production: {is_production}")
    if is_production:
        print("   ✓ CORRECT: Tag is valid production release")
    else:
        print("   ❌ ERROR: Tag should be accepted")
    
    print("\n3. Simulating alert scenario v1.4.3 → v20201.01.02:")
    last_version = "v1.4.3"
    latest_version = "v20201.01.02"
    
    # Check if latest would be filtered
    is_prod = github_service._is_production_tag(latest_version)
    if not is_prod:
        print(f"   Latest version {latest_version} is filtered out")
        print("   ✓ NO ALERT - Tag is non-production")
        scenario1_passed = True
    else:
        print(f"   ❌ Latest version {latest_version} passed filter")
        print("   ❌ WOULD ALERT - Bug still present")
        scenario1_passed = False
    
    print("\n4. Simulating alert scenario v20201.01.02 → v1.4.3:")
    last_version = "v20201.01.02"
    latest_version = "v1.4.3"
    
    # Check if latest would be filtered
    is_prod = github_service._is_production_tag(latest_version)
    if is_prod:
        # Also check if last version would have been filtered initially
        last_is_prod = github_service._is_production_tag(last_version)
        if not last_is_prod:
            print(f"   Previous version {last_version} should never have been stored")
            print("   ✓ NO ALERT - Previous version was invalid")
            scenario2_passed = True
        else:
            # Compare versions
            comparison = github_service._compare_versions(
                github_service._normalize_version(latest_version),
                github_service._normalize_version(last_version)
            )
            if comparison > 0:
                print(f"   {latest_version} is newer than {last_version}")
                print("   WOULD ALERT - But this should not happen if v20201.01.02 was filtered")
                scenario2_passed = False
            else:
                print(f"   {latest_version} is not newer than {last_version}")
                print("   ✓ NO ALERT - Version comparison correct")
                scenario2_passed = True
    else:
        print(f"   Latest version {latest_version} is filtered out")
        print("   ❌ ERROR - v1.4.3 should be accepted as production")
        scenario2_passed = False
    
    print("\n5. Testing other date-based variants:")
    date_tags = [
        "v2020.01.02",
        "v2021.12.31",
        "v20201.1.2",
        "20201.01.02",
        "v10000.0.1",
    ]
    
    all_filtered = True
    for tag in date_tags:
        is_prod = github_service._is_production_tag(tag)
        status = "✓ FILTERED" if not is_prod else "❌ PASSED"
        print(f"   {status}: {tag}")
        if is_prod:
            all_filtered = False
    
    print("\n" + "=" * 60)
    if scenario1_passed and scenario2_passed and all_filtered:
        print("✓ ALL TESTS PASSED - Flip-flop issue is FIXED")
        print("\nSummary:")
        print("- v20201.01.02 will be filtered and never stored in database")
        print("- v1.4.3 is correctly identified as production release")
        print("- No alerts will be generated for date-based tags")
        print("- No flip-flopping between v1.4.3 and v20201.01.02")
    else:
        print("❌ SOME TESTS FAILED - Issue may still exist")
    print("=" * 60)
    
    return scenario1_passed and scenario2_passed and all_filtered


if __name__ == "__main__":
    success = test_bsc_erigon_scenario()
    sys.exit(0 if success else 1)
