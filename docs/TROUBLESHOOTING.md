# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with Source2Social. It covers setup problems, runtime errors, integration issues, and performance problems.

## Table of Contents
- [Quick Diagnostics](#quick-diagnostics)
- [Setup Issues](#setup-issues)
- [Runtime Errors](#runtime-errors)
- [GitHub Integration Issues](#github-integration-issues)
- [Social Media Integration Issues](#social-media-integration-issues)
- [Database Issues](#database-issues)
- [Performance Issues](#performance-issues)
- [Deployment Issues](#deployment-issues)
- [Debugging Tools](#debugging-tools)
- [Getting Help](#getting-help)

## Quick Diagnostics

### Health Check Commands

```bash
# Check if application is running
curl http://localhost:8000/health

# Check database connectivity
python -c "from database.db import test_connection; test_connection()"

# Check all imports
python test_imports.py

# Check webhook endpoint
curl -X POST http://localhost:8000/webhook/github \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

### Common Error Patterns

| Error Pattern | Likely Cause | Quick Fix |
|---------------|--------------|-----------|
| `ModuleNotFoundError` | Missing dependencies | `pip install -r requirements.txt` |
| `ConnectionError` | Database not accessible | Check database path and permissions |
| `401 Unauthorized` | Invalid API keys | Verify environment variables |
| `500 Internal Server Error` | Application crash | Check logs for specific error |
| `Webhook not receiving` | Network/firewall issue | Check webhook URL accessibility |

## Setup Issues

### 1. Python Environment Issues

#### Problem: `python: command not found`
```bash
# Solution: Install Python or use python3
python3 --version
# If not installed, install Python 3.8+
```

#### Problem: `pip: command not found`
```bash
# Solution: Install pip
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
```

#### Problem: Virtual environment not activating
```bash
# Check if virtual environment exists
ls -la venv/

# Recreate if needed
rm -rf venv/
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows
```

### 2. Dependency Installation Issues

#### Problem: `pip install` fails with permission errors
```bash
# Solution: Use user installation or virtual environment
pip install --user -r requirements.txt
# OR
source venv/bin/activate
pip install -r requirements.txt
```

#### Problem: Package conflicts
```bash
# Solution: Check for conflicting packages
pip list | grep conflicting-package

# Uninstall conflicting package
pip uninstall conflicting-package

# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

#### Problem: Platform-specific package issues
```bash
# For macOS with Apple Silicon
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir

# For Windows
pip install -r requirements.txt --no-cache-dir --force-reinstall
```

### 3. Environment Configuration Issues

#### Problem: `.env` file not found
```bash
# Solution: Create from template
cp .env.example .env
# Edit .env with your actual values
```

#### Problem: Environment variables not loading
```bash
# Check if .env file is in correct location
ls -la .env

# Verify file format (no spaces around =)
cat .env | grep -v "^#" | grep "="

# Test environment loading
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('GITHUB_WEBHOOK_SECRET'))"
```

## Runtime Errors

### 1. Application Startup Issues

#### Problem: `Address already in use`
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
export PORT=8001
python run.py
```

#### Problem: `Permission denied` on database file
```bash
# Check file permissions
ls -la sc2sm.db

# Fix permissions
chmod 664 sc2sm.db

# Or delete and recreate
rm sc2sm.db
python -c "from database.db import init_db; init_db()"
```

#### Problem: `ImportError` for specific modules
```bash
# Check if module is installed
python -c "import module_name"

# Install missing module
pip install module_name

# Check Python path
python -c "import sys; print(sys.path)"
```

### 2. Database Connection Issues

#### Problem: `sqlite3.OperationalError: database is locked`
```bash
# Check for running processes
ps aux | grep python

# Kill any stuck processes
pkill -f "python.*app.py"

# Check database file locks
lsof sc2sm.db

# Restart application
python run.py
```

#### Problem: `sqlite3.DatabaseError: database disk image is malformed`
```bash
# Backup current database
cp sc2sm.db sc2sm.db.backup

# Try to recover data
sqlite3 sc2sm.db ".dump" > recovery.sql

# Create new database
rm sc2sm.db
python -c "from database.db import init_db; init_db()"

# Restore data if possible
sqlite3 sc2sm.db < recovery.sql
```

### 3. Memory Issues

#### Problem: `MemoryError` during post generation
```bash
# Check memory usage
free -h  # Linux
vm_stat  # macOS

# Reduce batch size in configuration
# Edit app.py to process fewer commits at once
```

## GitHub Integration Issues

### 1. Webhook Not Receiving Data

#### Problem: Webhook URL not accessible
```bash
# Test webhook endpoint locally
curl -X POST http://localhost:8000/webhook/github \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# For external access, use ngrok
ngrok http 8000
# Use the ngrok URL in GitHub webhook settings
```

#### Problem: Webhook signature validation failing
```bash
# Check webhook secret configuration
echo $GITHUB_WEBHOOK_SECRET

# Verify secret in GitHub webhook settings
# Secret should match exactly (no extra spaces)

# Test signature validation
python test_webhook.py
```

#### Problem: Webhook receiving data but not processing
```bash
# Check application logs
tail -f app.log

# Enable debug mode
export FLASK_DEBUG=1
python run.py

# Test webhook processing manually
python -c "
from app import process_github_webhook
import json
with open('testdata/sample_webhook.json') as f:
    data = json.load(f)
process_github_webhook(data)
"
```

### 2. GitHub API Issues

#### Problem: `403 Forbidden` from GitHub API
```bash
# Check API rate limits
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/rate_limit

# Use personal access token if needed
# Generate token at: https://github.com/settings/tokens
```

#### Problem: Repository not found
```bash
# Verify repository URL format
# Should be: https://github.com/username/repository

# Check repository permissions
# Ensure repository is public or you have access
```

## Social Media Integration Issues

### 1. Twitter/X Integration Problems

#### Problem: `401 Unauthorized` from Twitter API
```bash
# Check API credentials
echo $TWITTER_API_KEY
echo $TWITTER_API_SECRET

# Verify credentials are correct
# Check Twitter Developer Portal: https://developer.twitter.com/

# Test API connection
python test_twitter.py
```

#### Problem: `403 Forbidden` from Twitter API
```bash
# Check app permissions
# Ensure app has "Read and Write" permissions

# Check rate limits
# Twitter has strict rate limits

# Verify OAuth tokens
# Tokens may have expired
```

#### Problem: Posts not appearing on Twitter
```bash
# Check post content length
# Twitter has character limits

# Verify posting permissions
# Check app has write access

# Test with simple post
python -c "
from app import publish_to_twitter
publish_to_twitter('Test post from Source2Social')
"
```

### 2. OAuth Flow Issues

#### Problem: OAuth callback not working
```bash
# Check callback URL configuration
# Should match exactly in Twitter app settings

# Verify OAuth state parameter
# Prevents CSRF attacks

# Check redirect URI
# Must be whitelisted in Twitter app
```

## Database Issues

### 1. SQLite Specific Problems

#### Problem: Database file corruption
```bash
# Check database integrity
sqlite3 sc2sm.db "PRAGMA integrity_check;"

# If corrupted, try recovery
sqlite3 sc2sm.db ".dump" > backup.sql
rm sc2sm.db
sqlite3 sc2sm.db < backup.sql
```

#### Problem: Database performance issues
```bash
# Check database size
ls -lh sc2sm.db

# Analyze query performance
sqlite3 sc2sm.db "EXPLAIN QUERY PLAN SELECT * FROM posts WHERE status='draft';"

# Add indexes if needed
sqlite3 sc2sm.db "CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);"
```

### 2. Migration Issues

#### Problem: Schema changes not applied
```bash
# Check current schema
sqlite3 sc2sm.db ".schema"

# Apply migrations manually
python -c "from database.db import migrate_schema; migrate_schema()"

# Backup before major changes
cp sc2sm.db sc2sm.db.backup.$(date +%Y%m%d)
```

## Performance Issues

### 1. Slow Response Times

#### Problem: Application responding slowly
```bash
# Check system resources
top
htop  # if available

# Profile application
python -m cProfile -o profile.stats app.py

# Analyze profile
python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(10)
"
```

#### Problem: Database queries slow
```bash
# Enable query logging
export SQLALCHEMY_ECHO=True

# Check for missing indexes
sqlite3 sc2sm.db ".indices"

# Analyze slow queries
sqlite3 sc2sm.db "EXPLAIN QUERY PLAN SELECT * FROM posts ORDER BY created_at DESC LIMIT 10;"
```

### 2. Memory Usage Issues

#### Problem: High memory usage
```bash
# Monitor memory usage
ps aux | grep python

# Check for memory leaks
# Restart application periodically

# Optimize data structures
# Use generators instead of lists for large datasets
```

## Deployment Issues

### 1. Vercel Deployment Problems

#### Problem: Build fails on Vercel
```bash
# Check build logs in Vercel dashboard

# Verify requirements.txt
pip install -r requirements.txt

# Check Python version compatibility
# Vercel uses Python 3.9 by default

# Test build locally
vercel build
```

#### Problem: Environment variables not set
```bash
# Check Vercel dashboard
# Go to Project Settings > Environment Variables

# Verify variable names match code
grep -r "os.getenv" app.py

# Test environment loading
vercel env pull .env.local
```

### 2. Railway Deployment Problems

#### Problem: Application not starting
```bash
# Check Railway logs
railway logs

# Verify Procfile or start command
# Should be: web: python app.py

# Check port configuration
# Railway sets PORT environment variable
```

#### Problem: Database connection issues
```bash
# Check DATABASE_URL environment variable
echo $DATABASE_URL

# Verify database service is running
railway status

# Test database connection
railway run python -c "from database.db import test_connection; test_connection()"
```

## Debugging Tools

### 1. Logging Configuration

#### Enable Debug Logging
```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

#### Add Custom Logging
```python
import logging
logger = logging.getLogger(__name__)

def process_webhook(payload):
    logger.info(f"Processing webhook with {len(payload.get('commits', []))} commits")
    try:
        # Process webhook
        result = process_commits(payload)
        logger.info(f"Successfully processed {len(result)} posts")
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
```

### 2. Debug Mode

#### Enable Flask Debug Mode
```bash
export FLASK_DEBUG=1
export FLASK_ENV=development
python run.py
```

#### Add Debug Endpoints
```python
@app.route('/debug/info')
def debug_info():
    if not app.debug:
        return "Debug mode not enabled", 403
    
    return {
        'environment': dict(os.environ),
        'database_path': app.config.get('DATABASE_PATH'),
        'posts_count': get_posts_count(),
        'last_webhook': get_last_webhook_time()
    }
```

### 3. Testing Tools

#### Webhook Testing
```bash
# Test webhook with sample data
python test_webhook.py

# Test with custom payload
curl -X POST http://localhost:8000/webhook/github \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=test" \
  -d @testdata/sample_webhook.json
```

#### API Testing
```bash
# Test all endpoints
python -m pytest tests/test_api.py -v

# Test specific endpoint
curl -X GET http://localhost:8000/health
curl -X GET http://localhost:8000/posts
```

## Getting Help

### 1. Self-Diagnosis Checklist

Before seeking help, check:

- [ ] Application is running (`curl http://localhost:8000/health`)
- [ ] Environment variables are set (`env | grep -E "(GITHUB|TWITTER|OPENAI)"`)
- [ ] Dependencies are installed (`python test_imports.py`)
- [ ] Database is accessible (`python -c "from database.db import test_connection; test_connection()"`)
- [ ] Webhook endpoint responds (`curl -X POST http://localhost:8000/webhook/github -d '{}'`)

### 2. Collecting Debug Information

When reporting issues, include:

```bash
# System information
python --version
pip list
uname -a  # Linux/macOS
systeminfo  # Windows

# Application logs
tail -n 100 app.log

# Environment configuration (remove sensitive data)
env | grep -E "(GITHUB|TWITTER|OPENAI|DATABASE)" | sed 's/=.*/=***/'

# Database status
sqlite3 sc2sm.db "SELECT COUNT(*) FROM posts;"
sqlite3 sc2sm.db ".schema"
```

### 3. Common Solutions Summary

| Issue | Quick Fix |
|-------|-----------|
| Module not found | `pip install -r requirements.txt` |
| Port in use | `lsof -i :8000 && kill -9 <PID>` |
| Database locked | `pkill -f python && python run.py` |
| Webhook not working | Check ngrok URL and GitHub webhook settings |
| API errors | Verify API keys and rate limits |
| Slow performance | Check system resources and add indexes |

### 4. Community Resources

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check other guides in `/docs` folder
- **Stack Overflow**: Search for Flask/Python related issues
- **Discord/Slack**: Join developer communities for real-time help

### 5. Professional Support

For complex issues or production problems:

- **Log Analysis**: Provide detailed logs and error messages
- **System Architecture**: Describe your deployment setup
- **Reproduction Steps**: Provide exact steps to reproduce the issue
- **Expected vs Actual**: Describe what should happen vs what actually happens

---

Remember: Most issues are configuration-related. Double-check your environment variables, API keys, and network connectivity before diving into complex debugging.
