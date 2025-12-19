# Quick Reference: GitLab Support

## Add GitLab Repositories

### Format
```env
# GitHub (default - no prefix)
MONITORED_REPOS=ethereum/go-ethereum,bitcoin/bitcoin

# GitLab (with gitlab: prefix)
MONITORED_REPOS=gitlab:gitlab-org/gitlab-runner,gitlab:inkle/ink

# Mixed (both platforms)
MONITORED_REPOS=ethereum/go-ethereum,gitlab:gitlab-org/gitlab-runner
```

## Configuration

### Public Repositories (No Token Needed)
```env
MONITORED_REPOS=gitlab:gitlab-org/gitlab-runner
```
Works without `GITLAB_TOKEN` for public repos!

### Private Repositories (Token Required)
```env
GITLAB_TOKEN=your_token_here
MONITORED_REPOS=gitlab:your-group/private-project
```

### Self-Hosted GitLab
```env
GITLAB_TOKEN=your_token
GITLAB_API_BASE=https://gitlab.company.com/api/v4
MONITORED_REPOS=gitlab:internal-team/blockchain-node
```

## Get GitLab Token

1. Visit: https://gitlab.com/-/profile/personal_access_tokens
2. Create token with `read_api` scope
3. Copy to `.env`

## Examples

### Popular GitLab Blockchain Projects
```env
MONITORED_REPOS=\
  gitlab:parity/substrate,\
  gitlab:polkadot/polkadot,\
  gitlab:gitlab-org/gitlab-runner
```

### Tag Filtering (Works with GitLab!)
```env
REPO_TAG_FILTERS=gitlab:parity/polkadot:v1.0,v2.0
```

## Testing

```bash
# Test GitLab service
python3 test_gitlab.py

# Test both GitHub and GitLab
python3 test_unified_service.py
```

## Platform Detection

| Repository Format | Detected Platform |
|-------------------|-------------------|
| `owner/repo` | GitHub |
| `gitlab:group/project` | GitLab |
| `github:owner/repo` | GitHub (explicit) |

## Features Supported

✅ Release monitoring  
✅ Tag monitoring  
✅ Tag filtering  
✅ Commit analysis  
✅ AI analysis  
✅ Email/Slack alerts  
✅ API endpoints  

## Status Messages

```
Initializing monitored repositories:
  - ethereum/go-ethereum [GitHub]
  - gitlab:gitlab-org/gitlab-runner [GitLab]
```

## API Usage

```bash
# Check GitLab repository
curl -X POST http://localhost:5000/repos/gitlab:gitlab-org/gitlab-runner/check

# Works exactly like GitHub repos!
```

## Troubleshooting

**Q: "Resource not found"**  
A: Check format is `gitlab:group/project` (no gitlab.com domain)

**Q: "401 Unauthorized"**  
A: Add `GITLAB_TOKEN` for private repos

**Q: Different GitLab instance?**  
A: Set `GITLAB_API_BASE=https://your-gitlab.com/api/v4`

## Migration

1. Add GitLab token (optional for public):
   ```env
   GITLAB_TOKEN=your_token
   ```

2. Add GitLab repos with prefix:
   ```env
   MONITORED_REPOS=existing-repos,gitlab:new-gitlab-repo
   ```

3. Run:
   ```bash
   python3 run.py
   ```

That's it! 🚀
