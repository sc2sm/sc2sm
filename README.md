# SC2SM - GitHub to Social Media Converter

A Flask web application that automatically converts GitHub commits into engaging social media posts.

## Features

- **GitHub Integration**: Connect your GitHub account and track repositories
- **AI-Powered Content**: Transform technical commit messages into engaging social media posts
- **Multi-Platform Support**: Post to Twitter, LinkedIn, and other social media platforms
- **Webhook Support**: Real-time notifications for new commits
- **User Dashboard**: Manage repositories, view post history, and configure settings
- **Auto-Posting**: Automatically generate and post content when new commits are detected

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- GitHub OAuth App
- Twitter API Keys (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sc2sm
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Set up database**
   ```bash
   # Create PostgreSQL database
   createdb sc2sm
   
   # Initialize migrations
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

   The application will be available at `http://localhost:5000`

## Configuration

### Environment Variables

Copy `env.example` to `.env` and configure the following:

#### Required
- `SECRET_KEY`: Flask secret key for sessions
- `DATABASE_URL`: PostgreSQL connection string
- `GITHUB_CLIENT_ID`: GitHub OAuth app client ID
- `GITHUB_CLIENT_SECRET`: GitHub OAuth app client secret

#### Optional
- `TWITTER_API_KEY`: Twitter API key for posting
- `TWITTER_API_SECRET`: Twitter API secret
- `OPENAI_API_KEY`: OpenAI API key for AI content generation
- `WEBHOOK_SECRET`: Secret for webhook validation

### GitHub OAuth Setup

1. Go to GitHub Settings > Developer settings > OAuth Apps
2. Create a new OAuth App
3. Set Authorization callback URL to: `http://localhost:5000/auth/callback`
4. Copy Client ID and Client Secret to your `.env` file

### Twitter API Setup

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new app
3. Generate API keys and access tokens
4. Add them to your `.env` file

## Project Structure

```
sc2sm/
├── app.py                 # Application entry point
├── config.py             # Configuration settings
├── run.py                # Development server
├── wsgi.py               # Production WSGI entry point
├── requirements.txt      # Python dependencies
├── env.example           # Environment variables template
├── routes/               # Flask blueprints
│   ├── auth.py          # Authentication routes
│   ├── github.py        # GitHub integration routes
│   ├── twitter.py       # Twitter integration routes
│   └── main.py          # Main application routes
├── models/               # Database models
│   ├── user.py          # User model
│   ├── repository.py    # Repository model
│   ├── commit.py        # Commit model
│   └── post.py          # Post model
├── services/             # External service integrations
│   ├── github_service.py # GitHub API service
│   ├── twitter_service.py # Twitter API service
│   └── ai_service.py     # AI content generation service
├── utils/                # Utility functions
│   ├── helpers.py       # Helper functions
│   ├── filters.py       # Jinja2 filters
│   └── validators.py    # Data validation functions
├── templates/            # HTML templates
│   ├── base.html        # Base template
│   ├── index.html       # Home page
│   ├── dashboard.html   # User dashboard
│   ├── settings.html    # User settings
│   └── post_history.html # Post history
├── static/               # Static files
│   ├── css/             # Stylesheets
│   ├── js/              # JavaScript files
│   └── img/             # Images
└── migrations/           # Database migrations
    ├── env.py           # Migration environment
    ├── alembic.ini      # Alembic configuration
    └── versions/        # Migration files
```

## Usage

### 1. Authentication

- Visit the home page and click "Login with GitHub"
- Authorize the application to access your GitHub account
- You'll be redirected to the dashboard

### 2. Repository Management

- Go to "Repositories" to view your GitHub repositories
- Click "Track" to start monitoring a repository
- Configure auto-posting settings for each repository

### 3. Post Creation

- Go to "Posts" to create new social media posts
- Use the AI-powered content generator to convert commit messages
- Schedule or publish posts immediately

### 4. Webhook Setup

- Go to your repository settings on GitHub
- Add a webhook with URL: `https://your-domain.com/webhook`
- Select "Just the push event"
- The application will automatically process new commits

## API Endpoints

### Authentication
- `GET /auth/login` - Initiate GitHub OAuth login
- `GET /auth/callback` - Handle OAuth callback
- `GET /auth/logout` - Logout user

### GitHub Integration
- `GET /github/repositories` - List user repositories
- `POST /github/repositories/<id>/track` - Track repository
- `POST /github/repositories/<id>/untrack` - Stop tracking repository
- `GET /github/repositories/<id>/settings` - Repository settings
- `POST /github/repositories/<id>/sync` - Sync repository commits

### Twitter Integration
- `GET /twitter/posts` - List user posts
- `POST /twitter/posts/new` - Create new post
- `POST /twitter/posts/<id>/publish` - Publish post
- `POST /twitter/posts/<id>/edit` - Edit post
- `POST /twitter/posts/<id>/delete` - Delete post

### Webhooks
- `POST /webhook` - GitHub webhook endpoint

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-flask

# Run tests
pytest
```

### Database Migrations

```bash
# Create new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8

# Sort imports
isort .
```

## Deployment

### Production Setup

1. **Set up production database**
   ```bash
   # Use a managed PostgreSQL service like AWS RDS or Heroku Postgres
   export DATABASE_URL="postgresql://user:pass@host:port/dbname"
   ```

2. **Configure environment variables**
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY="your-production-secret-key"
   ```

3. **Deploy with Gunicorn**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 wsgi:application
   ```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "wsgi:application"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Join our community discussions

## Roadmap

- [ ] LinkedIn integration
- [ ] Facebook integration
- [ ] Advanced AI content generation
- [ ] Post scheduling
- [ ] Analytics dashboard
- [ ] Team collaboration features
- [ ] API rate limiting
- [ ] Content moderation
- [ ] Multi-language support