# Blockchain Release Monitor

A Python application that monitors **GitHub and GitLab** blockchain repositories for new versions and sends intelligent alerts via Email and/or Slack using AI analysis.

## 🚀 Features

✅ **Multi-Platform Support** - Monitor both GitHub and GitLab repositories  
✅ **Multi-Repository Monitoring** - Track multiple blockchain projects simultaneously  
✅ **Smart Version Detection** - Monitors both releases and Git tags  
✅ **Tag Filtering** - Filter specific binaries/components from repos with multiple releases  
✅ **AI-Powered Analysis** - Uses Google Gemini to analyze changes and assess severity  
✅ **Flexible Notifications** - Send alerts via Email, Slack, or both  
✅ **Intelligent Alerts** - Only sends notifications for HIGH/CRITICAL updates or mandatory upgrades  
✅ **Tag-Only Support** - Handles repos that publish tags without releases  
✅ **Commit Analysis** - Analyzes commit messages when release notes aren't available  
✅ **Flask API** - REST endpoints for status checks and manual triggers  
✅ **GitHub Webhooks** - Real-time notifications via webhook integration  
✅ **SQLite Database** - Persistent state tracking to prevent duplicate alerts  
✅ **Scheduled Checks** - Automatic periodic polling with configurable intervals

## 📦 Quick Start

```bash
# 1. Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your credentials

# 3. Test configuration
python test_config.py

# 4. Run application
python run.py
```

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Fast setup guide
- **[SETUP.md](SETUP.md)** - Complete documentation with all features
- **[examples/email_examples.py](examples/email_examples.py)** - Sample alert emails

## 🛠️ Technology Stack

- Python 3.10+
- Flask (REST API)
- GitHub REST API
- Google Gemini AI
- SQLite
- APScheduler
- SMTP (email)

## 📋 Requirements

Get these free API keys:

1. **GitHub Token**: https://github.com/settings/tokens
2. **Gemini API Key**: https://makersuite.google.com/app/apikey
3. **Email**: Gmail with app password

## 🎯 Usage

### API Endpoints

```bash
# Health check
curl http://localhost:5000/health

# View monitored repos
curl http://localhost:5000/repos

# Manually check a repo
curl -X POST http://localhost:5000/repos/ethereum/go-ethereum/check

# View alerts
curl http://localhost:5000/alerts

# Test email
curl -X POST http://localhost:5000/test/email
```

### Configuration

Edit `.env`:

```env
GITHUB_TOKEN=your_token
GEMINI_API_KEY=your_key
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=recipient@example.com
MONITORED_REPOS=ethereum/go-ethereum,bitcoin/bitcoin,cosmos/cosmos-sdk
CHECK_INTERVAL_MINUTES=60

# Optional: Filter specific tags/binaries from repos
# Format: owner/repo:pattern1,pattern2;another/repo:pattern
REPO_TAG_FILTERS=ethereum-optimism/optimism:op-geth,op-node
```

### Tag Filtering

For repositories that publish multiple binaries or components (like Optimism with `op-geth`, `op-node`, etc.), you can filter to only monitor specific ones:

```env
# Only monitor op-geth and op-node releases from Optimism
REPO_TAG_FILTERS=ethereum-optimism/optimism:op-geth,op-node

# Multiple repos with filters (semicolon-separated)
REPO_TAG_FILTERS=ethereum-optimism/optimism:op-geth,op-node;cosmos/gaia:v1,v2
```

The monitor will only track releases/tags that contain the specified patterns in their names.

## 📧 Email Alerts

Alerts are sent when:
- `mandatory_upgrade == true`, OR
- `severity >= HIGH`

Example alert:

```
Subject: 🚨 CRITICAL [MANDATORY] ethereum/go-ethereum Update: v1.13.0

Repository: ethereum/go-ethereum
Version Change: v1.12.2 → v1.13.0
Severity: CRITICAL
Mandatory Upgrade: YES

SUMMARY:
Security vulnerability patched in consensus layer. Hard fork
activation at block 18500000. All nodes must upgrade before
October 15, 2024.
```

See [examples/email_examples.py](examples/email_examples.py) for more examples.

## 🗂️ Project Structure

```
blockchain-release-monitor/
├── app/
│   ├── config.py              # Configuration
│   ├── main.py                # Application entry
│   ├── monitor.py             # Monitoring logic
│   ├── db/
│   │   └── database.py        # SQLite layer
│   ├── models/
│   │   └── __init__.py        # Data models
│   ├── routes/
│   │   └── api.py             # Flask API
│   └── services/
│       ├── github_service.py  # GitHub API
│       ├── gemini_service.py  # AI analysis
│       └── email_service.py   # Email alerts
├── examples/
│   └── email_examples.py      # Sample emails
├── .env.example               # Config template
├── requirements.txt           # Dependencies
├── run.py                     # Entry point
├── test_config.py            # Test script
├── QUICKSTART.md             # Quick guide
└── SETUP.md                  # Full docs
```

## 🔍 How It Works

1. **Monitor**: Polls GitHub for new releases/tags
2. **Detect**: Compares versions, gets release notes or commits
3. **Analyze**: Gemini AI determines severity and if mandatory
4. **Alert**: Sends email for HIGH/CRITICAL or mandatory updates
5. **Track**: Stores in SQLite to prevent duplicates

## 🐛 Troubleshooting

**No alerts?**
- Check email config with `/test/email`
- Verify repositories have new versions
- Review logs for severity thresholds

**Rate limits?**
- Increase `CHECK_INTERVAL_MINUTES`
- Use webhooks instead of polling
- Check GitHub token permissions

**AI errors?**
- Verify Gemini API key
- Check quota limits
- Review fallback responses in logs

## 📄 License

MIT License

## 🤝 Contributing

Contributions welcome! Submit issues and PRs on GitHub.

---

**Built for the blockchain community** 🚀

