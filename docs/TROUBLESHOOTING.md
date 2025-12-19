# Troubleshooting Guide

## Common Issues and Solutions

### Installation Issues

#### Problem: `pip install` fails
```bash
# Solution: Upgrade pip first
pip install --upgrade pip
pip install -r requirements.txt
```

#### Problem: Virtual environment not activating
```bash
# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate

# If still fails, recreate:
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

### Configuration Issues

#### Problem: "Missing required configuration"
```bash
# Solution: Verify .env file exists and has all required variables
python test_config.py

# Check .env file:
cat .env

# Compare with example:
diff .env .env.example
```

#### Problem: GitHub token invalid
```bash
# Verify token:
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.github.com/user

# If fails, regenerate at:
# https://github.com/settings/tokens
```

#### Problem: Gemini API key invalid
```bash
# Test key manually:
curl -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_KEY"

# Get new key at:
# https://makersuite.google.com/app/apikey
```

### Email Issues

#### Problem: Gmail authentication fails
**Solution:**
1. Enable 2-Factor Authentication on Gmail
2. Generate App Password at: https://myaccount.google.com/apppasswords
3. Use App Password in `SMTP_PASSWORD`, NOT your regular password
4. Use your full email in `SMTP_USERNAME`

#### Problem: "SMTPAuthenticationError"
```python
# Verify credentials:
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your_email@gmail.com', 'your_app_password')
# Should succeed without error
```

#### Problem: Test email not received
- Check spam/junk folder
- Verify `EMAIL_TO` address is correct
- Try different recipient email
- Check Gmail "Less secure app access" (not needed with app passwords)

### GitHub API Issues

#### Problem: "Rate limit exceeded"
**Solutions:**
1. Verify you're using GitHub token (not anonymous)
2. Increase `CHECK_INTERVAL_MINUTES` in .env
3. Reduce number of `MONITORED_REPOS`
4. Check current rate limit:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.github.com/rate_limit
```

#### Problem: "Repository not found"
**Solutions:**
- Verify repository name format: `owner/repo`
- Ensure repository is public (or token has private repo access)
- Check repository exists: https://github.com/owner/repo

#### Problem: No releases or tags found
**Solutions:**
- Verify repository has releases or tags
- Check manually: https://github.com/owner/repo/releases
- Check tags: https://github.com/owner/repo/tags
- Some repos may not use releases - this is expected

### AI Analysis Issues

#### Problem: "Gemini API error"
**Solutions:**
1. Verify API key is valid
2. Check quota: https://makersuite.google.com/
3. Free tier limits: 60 requests/minute
4. Wait 1 minute and retry
5. Application falls back to default analysis on error

#### Problem: Invalid JSON response from AI
- Application has fallback handling
- Will use default severity and summary
- Check logs for actual response
- May indicate API quota exceeded

### Database Issues

#### Problem: "Permission denied" for database
```bash
# Solution: Ensure data directory exists and is writable
mkdir -p data
chmod 755 data

# Or change location in .env:
DATABASE_PATH=/tmp/blockchain_monitor.db
```

#### Problem: Database corruption
```bash
# Solution: Delete and reinitialize
rm data/blockchain_monitor.db
python run.py  # Will recreate
```

#### Problem: "Database is locked"
```bash
# Solution: Close other connections
pkill -f run.py
rm data/blockchain_monitor.db-journal  # If exists
python run.py
```

### Application Issues

#### Problem: Application crashes on startup
```bash
# Run test script first:
python test_config.py

# Check logs:
python run.py 2>&1 | tee app.log

# Verify Python version:
python --version  # Should be 3.10+
```

#### Problem: No alerts being sent
**Check:**
1. Are there actually new versions?
   ```bash
   curl http://localhost:5000/repos
   ```

2. Is severity HIGH or CRITICAL?
   - Alerts only sent for HIGH/CRITICAL or mandatory upgrades
   - Check alert criteria in logs

3. Has alert been sent before?
   ```bash
   curl http://localhost:5000/alerts
   ```

4. Is email configuration working?
   ```bash
   curl -X POST http://localhost:5000/test/email
   ```

#### Problem: Scheduler not running
```bash
# Check logs for "Scheduler started" message
# Verify CHECK_INTERVAL_MINUTES is set
# Ensure application stays running:
nohup python run.py > app.log 2>&1 &
```

### Flask API Issues

#### Problem: "Address already in use"
```bash
# Change port in .env:
FLASK_PORT=5001

# Or kill existing process:
lsof -ti:5000 | xargs kill -9
```

#### Problem: API endpoints not responding
```bash
# Verify Flask is running:
curl http://localhost:5000/health

# Check firewall:
sudo ufw allow 5000

# If remote, bind to 0.0.0.0:
FLASK_HOST=0.0.0.0
```

### Webhook Issues

#### Problem: GitHub webhook fails
**Solutions:**
1. Expose local server:
   ```bash
   # Use ngrok or similar:
   ngrok http 5000
   ```

2. Configure webhook in GitHub:
   - URL: `https://your-domain.com/webhook/github`
   - Content type: `application/json`
   - Events: Releases, Create (for tags)

3. Check webhook deliveries in GitHub settings

4. Verify repository is in `MONITORED_REPOS`

### Performance Issues

#### Problem: Checks taking too long
**Solutions:**
1. Reduce number of monitored repos
2. Increase check interval
3. Use webhooks instead of polling
4. Check GitHub rate limits

#### Problem: High memory usage
**Solutions:**
1. Reduce `CHECK_INTERVAL_MINUTES` (check less often)
2. Monitor fewer repositories
3. Restart application periodically
4. Check for database growth (vacuum if needed)

## Debug Mode

Enable detailed logging:

```python
# In app/main.py, change:
app.run(debug=True)

# Or add logging:
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Getting Help

1. **Check logs** - Application prints detailed status
2. **Run test script** - `python test_config.py`
3. **Verify APIs** - Test GitHub and Gemini manually
4. **Check documentation** - SETUP.md has full details
5. **Review examples** - examples/email_examples.py

## Quick Diagnostics

Run this diagnostic script:

```bash
# Save as diagnose.sh
echo "=== Python Version ==="
python --version

echo -e "\n=== Virtual Environment ==="
which python

echo -e "\n=== Installed Packages ==="
pip list | grep -E "Flask|requests|google-generativeai|APScheduler|python-dotenv"

echo -e "\n=== Environment Variables ==="
grep -v "PASSWORD\|TOKEN\|KEY" .env 2>/dev/null || echo ".env not found"

echo -e "\n=== Database ==="
ls -lh data/*.db 2>/dev/null || echo "Database not created yet"

echo -e "\n=== Test Configuration ==="
python test_config.py

echo -e "\n=== API Connectivity ==="
curl -s http://localhost:5000/health 2>/dev/null || echo "API not running"
```

Run: `bash diagnose.sh`

## Common Error Messages

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'flask'` | `pip install -r requirements.txt` |
| `ModuleNotFoundError: No module named 'app'` | Run from project root: `python run.py` |
| `FileNotFoundError: [Errno 2] No such file or directory: '.env'` | `cp .env.example .env` |
| `requests.exceptions.ConnectionError` | Check internet connection |
| `sqlite3.OperationalError: unable to open database file` | Create data directory: `mkdir data` |
| `SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')` | Use Gmail app password |
| `google.api_core.exceptions.PermissionDenied` | Invalid Gemini API key |
| `github.RateLimitExceededException` | Wait or increase interval |

## Still Having Issues?

1. Delete everything and start fresh:
   ```bash
   rm -rf venv data
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with credentials
   python test_config.py
   python run.py
   ```

2. Check GitHub issues for similar problems

3. Review logs carefully - they usually indicate the problem

4. Verify all prerequisites are met:
   - Python 3.10+
   - Valid GitHub token
   - Valid Gemini API key
   - Working email credentials
   - Internet connectivity
