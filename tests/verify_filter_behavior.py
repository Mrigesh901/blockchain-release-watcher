#!/usr/bin/env python3
"""
Verify that tag filtering correctly excludes non-matching releases.
"""
import requests
from app.config import Config


def main():
    """Check what releases exist in Optimism repo."""
    print("=" * 60)
    print("Optimism Repository - All Recent Releases")
    print("=" * 60)
    print()
    
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {Config.GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    url = "https://api.github.com/repos/ethereum-optimism/optimism/releases"
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        releases = response.json()
        
        print(f"Found {len(releases)} releases. Showing first 15:\n")
        
        for i, release in enumerate(releases[:15], 1):
            tag = release.get("tag_name", "")
            name = release.get("name", "")
            prerelease = release.get("prerelease", False)
            
            # Check if it matches our filter
            matches_filter = ("op-geth" in tag.lower() or "op-node" in tag.lower())
            status = "✓ MATCH" if matches_filter else "✗ SKIP"
            pre = " [PRERELEASE]" if prerelease else ""
            
            print(f"{i:2}. {status:10} {tag:30} {name}{pre}")
        
        print()
        print("Legend:")
        print("  ✓ MATCH - Would be tracked with op-geth,op-node filter")
        print("  ✗ SKIP  - Would be ignored (op-proposer, op-batcher, etc.)")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
