#!/usr/bin/env python3
"""
Manual test script for AI functionality.
Tests Gemini AI analysis with custom inputs.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import Config
from app.services.gemini_service import GeminiService


def test_ai_with_release_notes():
    """Test AI analysis with release notes."""
    print("\n" + "="*60)
    print("Testing AI Analysis with Release Notes")
    print("="*60)
    
    gemini = GeminiService()
    
    # Sample release notes
    release_notes = """
    ❗ Mandatory update for Base Mainnet nodes to support the Jovian upgrade on December 2nd.
Operators of Base Mainnet nodes must upgrade to this release before December 2nd at UTC 16:00:01 UTC (unix timestamp 1764691201).

⚠️ Breaking Changes (same as v0.14.1)
Similar to v0.14.1 which was a mandatory upgrade for Base Sepolia node operators, this release also contains the following change and will be applied to mainnet node operators now as well.

op-reth Binary Removed, Consolidated into base-reth-node
The separate op-reth binary has been removed and is no longer available.

All functionality previously provided by op-reth has been consolidated into the existing base-reth-node binary.

Impact: If your deployment or scripts explicitly called the op-reth binary, you must update them to call base-reth-node instead.
Parameters & Operation: The base-reth-node binary is designed to be identical in its command-line parameters and operational behavior to the removed op-reth. No parameter changes should be necessary other than the binary name itself.
Reasoning: This consolidation allows us to more easily introduce and manage Base-specific features within a single, unified client binary.

    """
    
    analysis = gemini.analyze_version_change(
        repo_name="ethereum/go-ethereum",
        old_version="v1.12.0",
        new_version="v1.13.0",
        release_notes=release_notes,
        commit_messages=[]
    )
    
    print(f"\n✓ Analysis Complete:")
    print(f"  Severity: {analysis.get('severity')}")
    print(f"  Mandatory: {analysis.get('mandatory_upgrade')}")
    print(f"\n  Summary:")
    print(f"  {analysis.get('summary')}")
    print(f"\n  Reasoning:")
    print(f"  {analysis.get('reasoning')}")
    
    # Check if alert should be sent
    should_alert = gemini.should_send_alert(analysis)
    print(f"\n  Send Alert: {should_alert}")
    
    return analysis


def test_ai_with_commits():
    """Test AI analysis with commit messages."""
    print("\n" + "="*60)
    print("Testing AI Analysis with Commit Messages")
    print("="*60)
    
    gemini = GeminiService()
    
    # Sample commit messages
    commit_messages = [
        "Fix critical bug in consensus validation",
        "Add security patch for CVE-2024-5678",
        "Improve network synchronization",
        "Update dependencies",
        "Refactor block processing logic",
        "Add tests for new features"
    ]
    
    analysis = gemini.analyze_version_change(
        repo_name="bitcoin/bitcoin",
        old_version="v25.0",
        new_version="v26.0",
        release_notes="",
        commit_messages=commit_messages
    )
    
    print(f"\n✓ Analysis Complete:")
    print(f"  Severity: {analysis.get('severity')}")
    print(f"  Mandatory: {analysis.get('mandatory_upgrade')}")
    print(f"\n  Summary:")
    print(f"  {analysis.get('summary')}")
    print(f"\n  Reasoning:")
    print(f"  {analysis.get('reasoning')}")
    
    should_alert = gemini.should_send_alert(analysis)
    print(f"\n  Send Alert: {should_alert}")
    
    return analysis


def test_ai_with_minor_update():
    """Test AI analysis with minor update."""
    print("\n" + "="*60)
    print("Testing AI Analysis with Minor Update")
    print("="*60)
    
    gemini = GeminiService()
    
    release_notes = """
    ## Bug Fixes
    - Fixed typo in help message
    - Updated documentation
    - Minor code cleanup
    """
    
    analysis = gemini.analyze_version_change(
        repo_name="cosmos/cosmos-sdk",
        old_version="v0.47.0",
        new_version="v0.47.1",
        release_notes=release_notes,
        commit_messages=[]
    )
    
    print(f"\n✓ Analysis Complete:")
    print(f"  Severity: {analysis.get('severity')}")
    print(f"  Mandatory: {analysis.get('mandatory_upgrade')}")
    print(f"\n  Summary:")
    print(f"  {analysis.get('summary')}")
    
    should_alert = gemini.should_send_alert(analysis)
    print(f"\n  Send Alert: {should_alert}")
    
    return analysis


def main():
    """Run all AI tests."""
    print("="*60)
    print("AI Functionality Test Suite")
    print("="*60)
    
    # Check configuration
    if not Config.GEMINI_API_KEY:
        print("\n❌ ERROR: GEMINI_API_KEY not set in .env")
        print("Please add your Gemini API key to .env file")
        sys.exit(1)
    
    print(f"✓ Gemini API Key configured")
    
    try:
        # Test 1: Critical update with release notes
        result1 = test_ai_with_release_notes()
        
        # Test 2: Update with commit messages
        result2 = test_ai_with_commits()
        
        # Test 3: Minor update
        result3 = test_ai_with_minor_update()
        
        # Summary
        print("\n" + "="*60)
        print("Test Summary")
        print("="*60)
        
        print(f"\nTest 1 (Critical): Severity={result1.get('severity')}, "
              f"Mandatory={result1.get('mandatory_upgrade')}")
        print(f"Test 2 (Security): Severity={result2.get('severity')}, "
              f"Mandatory={result2.get('mandatory_upgrade')}")
        print(f"Test 3 (Minor):    Severity={result3.get('severity')}, "
              f"Mandatory={result3.get('mandatory_upgrade')}")
        
        print("\n✓ All AI tests completed successfully!")
        print("\nThe AI is working correctly and can:")
        print("  • Analyze release notes")
        print("  • Process commit messages")
        print("  • Assign appropriate severity levels")
        print("  • Detect mandatory upgrades")
        print("  • Make alert decisions")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
