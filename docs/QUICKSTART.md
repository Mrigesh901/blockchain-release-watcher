# Quick Start Guide

## 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

## 2. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your credentials
nano .env  # or vim, code, etc.
```

Required configuration:
- ✅ `GITHUB_TOKEN` - Get from https://github.com/settings/tokens
- ✅ `GEMINI_API_KEY` - Get from https://makersuite.google.com/app/apikey
- ✅ `SMTP_USERNAME` and `SMTP_PASSWORD` - Your email credentials
- ✅ `EMAIL_FROM` and `EMAIL_TO` - Email addresses
- ✅ `MONITORED_REPOS` - Comma-separated list like `ethereum/go-ethereum,bitcoin/bitcoin`

## 3. Test Configuration

```bash
# Start the application
python run.py
```

The app will:
1. Initialize the database
2. Run an initial check of all repositories
3. Start the Flask API server
4. Begin scheduled periodic checks

## 4. Test Email

```bash
# In another terminal, test email configuration
curl -X POST http://localhost:5000/test/email
```

## 5. Check Status

```bash
# View all monitored repositories
curl http://localhost:5000/repos

# View alert history
curl http://localhost:5000/alerts
```

## 6. Manually Trigger Check

```bash
# Check specific repository
curl -X POST http://localhost:5000/repos/ethereum/go-ethereum/check
```

## Common Issues

### Gmail Authentication Fails
- Enable 2-Factor Authentication
- Create App Password at https://myaccount.google.com/apppasswords
- Use App Password in `SMTP_PASSWORD`, not your regular password

### GitHub Rate Limit
- Ensure you have a valid `GITHUB_TOKEN`
- Increase `CHECK_INTERVAL_MINUTES` to 60 or higher
- GitHub allows 5000 requests/hour with token

### Gemini API Error
- Verify API key is correct
- Check quota at https://makersuite.google.com/
- Free tier: 60 requests/minute

## Production Deployment

### Run as Background Service

```bash
# Using nohup
nohup python run.py > monitor.log 2>&1 &

# Or use systemd (see SETUP.md for details)
```

### Monitor Logs

```bash
# Follow application logs
tail -f monitor.log
```

## Next Steps

1. ✅ Test with 1-2 repositories first
2. ✅ Verify alerts are being sent correctly
3. ✅ Add more repositories to `MONITORED_REPOS`
4. ✅ Set up GitHub webhooks for real-time notifications (optional)
5. ✅ Configure systemd for automatic startup (production)

## Help & Support

- Full documentation: See `SETUP.md`
- Check API health: `curl http://localhost:5000/health`
- View logs: Check terminal output or `monitor.log`
