#!/usr/bin/env python3
"""
Test monitoring a specific repository with tag filters.
"""
from app.config import Config
from app.db.database import Database
from app.services.github_service import GitHubService
from app.services.gemini_service import GeminiService
from app.services.email_service import EmailService
from app.monitor import check_repository_updates


def main():
    """Test checking Optimism repository with tag filters."""
    print("=" * 60)
    print("Testing Optimism Monitoring with Tag Filters")
    print("=" * 60)
    print()
    
    # Initialize services
    db = Database(Config.DATABASE_PATH)
    tag_filters = Config.get_repo_tag_filters()
    
    print(f"Tag filters: {tag_filters}")
    print()
    
    github_service = GitHubService(tag_filters=tag_filters)
    gemini_service = GeminiService()
    email_service = EmailService()
    
    # Test Optimism repo
    repo_name = "ethereum-optimism/optimism"
    
    print(f"Checking {repo_name}...")
    print(f"Filter: Only track releases containing 'op-geth' or 'op-node'")
    print()
    
    result = check_repository_updates(
        repo_name=repo_name,
        db=db,
        github_service=github_service,
        gemini_service=gemini_service,
        email_service=email_service
    )
    
    print()
    print("Result:", result)
    print()
    
    # Show what's in the database
    repo = db.get_repository(repo_name)
    if repo:
        print(f"Database record:")
        print(f"  Last version: {repo.last_version_or_tag}")
        print(f"  Last checked: {repo.last_checked}")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
