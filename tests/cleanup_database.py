#!/usr/bin/env python3
"""
Database cleanup script to fix repositories with malformed version numbers.
This script identifies and corrects repositories that have date-based or 
malformed tags stored in the database.
"""
import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config
from app.db.database import Database
from app.services.github_service import GitHubService
from app.services.gitlab_service import GitLabService


def is_malformed_version(version: str) -> bool:
    """Check if a version appears to be malformed."""
    if not version:
        return False
    
    github_service = GitHubService()
    return not github_service._is_production_tag(version)


def cleanup_database():
    """Clean up malformed versions from the database."""
    print("=" * 60)
    print("Database Cleanup: Malformed Version Detection")
    print("=" * 60)
    
    db = Database(Config.DATABASE_PATH)
    
    print(f"\nConnecting to database: {Config.DATABASE_PATH}")
    
    # Get all repositories
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, repo_name, last_version_or_tag, last_alerted_version FROM repositories")
    repos = cursor.fetchall()
    
    print(f"\nFound {len(repos)} repositories in database\n")
    
    malformed_count = 0
    fixed_count = 0
    
    for repo_id, repo_name, last_version, last_alerted in repos:
        has_malformed = False
        fixes = []
        
        # Check last_version_or_tag
        if last_version and is_malformed_version(last_version):
            has_malformed = True
            fixes.append(f"  - last_version_or_tag: {last_version} (MALFORMED)")
            malformed_count += 1
        
        # Check last_alerted_version
        if last_alerted and is_malformed_version(last_alerted):
            has_malformed = True
            fixes.append(f"  - last_alerted_version: {last_alerted} (MALFORMED)")
        
        if has_malformed:
            print(f"📛 {repo_name}")
            for fix in fixes:
                print(fix)
            
            # Reset to NULL to trigger fresh detection
            cursor.execute(
                "UPDATE repositories SET last_version_or_tag = NULL, last_alerted_version = NULL WHERE id = ?",
                (repo_id,)
            )
            conn.commit()
            fixed_count += 1
            print(f"  ✓ Reset to NULL (will re-detect on next check)\n")
    
    conn.close()
    
    print("=" * 60)
    print(f"Summary:")
    print(f"  Total repositories: {len(repos)}")
    print(f"  Repositories with malformed versions: {malformed_count}")
    print(f"  Repositories reset: {fixed_count}")
    print("=" * 60)
    
    if fixed_count > 0:
        print("\n⚠️  IMPORTANT:")
        print("The affected repositories have been reset to NULL.")
        print("On the next monitoring cycle:")
        print("  1. The system will fetch the latest production release")
        print("  2. It will be marked as 'first check' (no alert)")
        print("  3. Future updates will alert correctly")
        print()
    else:
        print("\n✓ No malformed versions found in database!")
    
    return fixed_count


if __name__ == "__main__":
    try:
        fixed = cleanup_database()
        print("\n✓ Cleanup completed successfully")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
