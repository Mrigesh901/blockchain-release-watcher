#!/usr/bin/env python3
"""
Test script to verify configuration and services.
"""
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import Config
from app.db.database import Database
from app.services.github_service import GitHubService
from app.services.gemini_service import GeminiService
from app.services.email_service import EmailService


def test_configuration():
    """Test configuration loading."""
    print("\n" + "="*60)
    print("Testing Configuration")
    print("="*60)
    
    missing = Config.validate()
    
    if missing:
        print("❌ Missing configuration:")
        for item in missing:
            print(f"   - {item}")
        return False
    
    print("✓ All required configuration present")
    print(f"✓ Monitoring {len(Config.MONITORED_REPOS)} repositories")
    print(f"✓ Check interval: {Config.CHECK_INTERVAL_MINUTES} minutes")
    
    return True


def test_database():
    """Test database initialization."""
    print("\n" + "="*60)
    print("Testing Database")
    print("="*60)
    
    try:
        db = Database(Config.DATABASE_PATH)
        print("✓ Database initialized")
        
        # Test upsert
        db.upsert_repository("test/repo", "https://github.com/test/repo")
        print("✓ Database write successful")
        
        # Test read
        repo = db.get_repository("test/repo")
        if repo:
            print("✓ Database read successful")
        else:
            print("❌ Database read failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def test_github_service():
    """Test GitHub API connection."""
    print("\n" + "="*60)
    print("Testing GitHub Service")
    print("="*60)
    
    try:
        github = GitHubService()
        print("✓ GitHub service initialized")
        
        # Test with a known public repository
        latest = github.get_latest_version("ethereum", "go-ethereum")
        
        if latest:
            print(f"✓ GitHub API working")
            print(f"  Latest version: {latest.get('tag_name')}")
            print(f"  Rate limit remaining: {github.rate_limit_remaining}")
        else:
            print("❌ Could not fetch repository data")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ GitHub service error: {e}")
        return False


def test_gemini_service():
    """Test Gemini AI service."""
    print("\n" + "="*60)
    print("Testing Gemini Service")
    print("="*60)
    
    try:
        gemini = GeminiService()
        print("✓ Gemini service initialized")
        
        # Test with sample data
        analysis = gemini.analyze_version_change(
            repo_name="test/repo",
            old_version="v1.0.0",
            new_version="v1.1.0",
            release_notes="Bug fixes and performance improvements",
            commit_messages=[]
        )
        
        if analysis and "summary" in analysis:
            print("✓ Gemini API working")
            print(f"  Severity: {analysis.get('severity')}")
            print(f"  Mandatory: {analysis.get('mandatory_upgrade')}")
        else:
            print("❌ Invalid Gemini response")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini service error: {e}")
        return False


def test_email_service():
    """Test email service configuration."""
    print("\n" + "="*60)
    print("Testing Email Service")
    print("="*60)
    
    response = input("Send test email? (y/n): ")
    
    if response.lower() != 'y':
        print("⊘ Email test skipped")
        return True
    
    try:
        email = EmailService()
        print("✓ Email service initialized")
        
        success = email.send_test_email()
        
        if success:
            print("✓ Test email sent successfully")
            print(f"  Check inbox: {Config.EMAIL_TO}")
        else:
            print("❌ Failed to send test email")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Email service error: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Blockchain Release Monitor - Configuration Test")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Configuration", test_configuration()))
    results.append(("Database", test_database()))
    results.append(("GitHub Service", test_github_service()))
    results.append(("Gemini Service", test_gemini_service()))
    results.append(("Email Service", test_email_service()))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Ready to run the application.")
        print("\nRun: python run.py")
    else:
        print("\n❌ Some tests failed. Please check configuration.")
        sys.exit(1)


if __name__ == "__main__":
    main()
