# Developer Setup Guide

This guide will help you set up Source2Social for local development and contribution.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Development Workflow](#development-workflow)
- [Code Structure](#code-structure)
- [Contributing](#contributing)

## Prerequisites

Before setting up Source2Social locally, ensure you have:

- **Python 3.8+**: Check with `python3 --version`
- **Git**: For version control
- **GitHub Account**: For webhook testing
- **Twitter Developer Account**: For social media integration testing
- **CodeRabbit Account**: For enhanced code analysis (optional)

### Optional Tools
- **ngrok**: For local webhook testing
- **Postman/Insomnia**: For API testing
- **SQLite Browser**: For database inspection

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/sc2sm/sc2sm.git
cd sc2sm
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python test_imports.py
```

This will check if all required packages are properly installed.

## Environment Configuration

### 1. Copy Environment Template

```bash
cp .env.example .env
```

### 2. Configure Required Variables

Edit `.env` with your actual values:

```bash
# GitHub Configuration
GITHUB_WEBHOOK_SECRET=your_github_webhook_secret_here

# Twitter API Configuration (optional)
TWITTER_API_KEY=your_twitter_api_key_here
TWITTER_API_SECRET=your_twitter_api_secret_here
TWITTER_ACCESS_TOKEN=your_twitter_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret_here

# OpenAI Configuration (optional)
OPENAI_API_KEY=your_openai_api_key_here

# CodeRabbit Configuration (optional)
CODERABBIT_API_KEY=your_coderabbit_api_key_here

# Application Configuration
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
PORT=8000

# Database Configuration
DATABASE_PATH=sc2sm.db
```

### 3. Generate Webhook Secret

For GitHub webhook testing, generate a secure secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Use this output as your `GITHUB_WEBHOOK_SECRET`.

## Database Setup

Source2Social uses SQLite for local development. The database will be created automatically on first run.

### Manual Database Initialization

If you need to initialize the database manually:

```bash
python -c "from database.db import init_db; init_db()"
```

### Database Schema

The application uses the following main tables:
- `posts`: Generated social media posts
- `reports`: CodeRabbit analysis reports
- `metrics`: Report metrics and analytics

## Running the Application

### Option 1: Using the Startup Script (Recommended)

```bash
python run.py
```

This will:
- Create `.env` file if it doesn't exist
- Start the Flask application on port 8000
- Display helpful startup information

### Option 2: Direct Flask Execution

```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --port=8000
```

### Option 3: Direct Python Execution

```bash
python app.py
```

### Verify Application is Running

Visit `http://localhost:8000` in your browser. You should see the Source2Social landing page.

## Testing

### 1. Test Webhook Integration

```bash
python test_webhook.py
```

This will test the GitHub webhook endpoint with sample data.

### 2. Test Twitter Integration

```bash
python test_twitter.py
```

This will test Twitter API connectivity (requires valid credentials).

### 3. Test OpenAI Integration

```bash
python test_openai.py
```

This will test OpenAI API connectivity (requires valid API key).

### 4. Manual Testing

#### Test GitHub Webhook
1. Set up ngrok for local webhook testing:
   ```bash
   ngrok http 8000
   ```
2. Use the ngrok URL in your GitHub webhook configuration
3. Make a test commit to trigger the webhook

#### Test Dashboard
1. Navigate to `http://localhost:8000/dashboard`
2. Verify all sections load correctly
3. Test post generation and editing

## Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes
# ... your code changes ...

# Test changes
python test_imports.py
python test_webhook.py

# Commit changes
git add .
git commit -m "Add your feature description"
```

### 2. Database Changes

If you modify database schema:

```bash
# Test database operations
python -c "from database.db import test_db_operations; test_db_operations()"
```

### 3. Template Changes

When modifying HTML templates:
1. Test in multiple browsers
2. Verify responsive design
3. Check for JavaScript errors in console

### 4. API Changes

When modifying API endpoints:
1. Update API documentation
2. Test with Postman/Insomnia
3. Verify error handling

## Code Structure

```
sc2sm/
├── app.py                 # Main Flask application
├── run.py                 # Startup script
├── database/
│   ├── __init__.py
│   └── db.py             # Database operations
├── routes/
│   ├── __init__.py
│   └── reports.py        # CodeRabbit report routes
├── services/
│   ├── __init__.py
│   └── coderabbit.py     # CodeRabbit API service
├── templates/            # HTML templates
├── docs/                # Documentation
├── testdata/            # Test data files
└── tests/               # Test files
    ├── test_webhook.py
    ├── test_twitter.py
    └── test_openai.py
```

### Key Files

- **`app.py`**: Main Flask application with routes and business logic
- **`database/db.py`**: Database operations and schema management
- **`services/coderabbit.py`**: CodeRabbit API integration
- **`templates/`**: Jinja2 HTML templates for the web interface
- **`routes/reports.py`**: Blueprint for report-related endpoints

## Contributing

### 1. Code Style

Follow Python PEP 8 guidelines:
- Use 4 spaces for indentation
- Limit lines to 88 characters
- Use descriptive variable names
- Add docstrings to functions and classes

### 2. Commit Messages

Use conventional commit format:
```
feat: add new feature
fix: resolve bug
docs: update documentation
refactor: improve code structure
test: add tests
```

### 3. Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Submit a pull request

### 4. Testing Requirements

Before submitting a PR:
- [ ] All existing tests pass
- [ ] New features have tests
- [ ] Manual testing completed
- [ ] Documentation updated

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

#### Database Locked
```bash
# Check for running processes
ps aux | grep python

# Restart application
```

#### Import Errors
```bash
# Verify virtual environment is activated
which python

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### Webhook Not Receiving Data
1. Check ngrok is running and URL is correct
2. Verify webhook secret matches configuration
3. Check GitHub webhook delivery logs
4. Review application logs for errors

### Debug Mode

Enable debug mode for detailed error information:

```bash
export FLASK_DEBUG=1
python run.py
```

### Logging

Application logs are written to the console. For production, configure proper logging:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Next Steps

After completing the setup:

1. **Read the [User Guide](./USER_GUIDE.md)** to understand the application features
2. **Set up GitHub webhook** following the [GitHub Webhook Setup Guide](./GITHUB_WEBHOOK_SETUP.md)
3. **Configure social media integration** using the [Social Media Setup Guide](./X_OAUTH_SETUP.md)
4. **Explore the codebase** to understand the architecture
5. **Start contributing** by fixing issues or adding features

## Getting Help

- **Documentation**: Check other guides in the `/docs` folder
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Join community discussions
- **Code Review**: Request code reviews for complex changes

---

Happy coding! 🚀
