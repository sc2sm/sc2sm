# Architecture Overview

This document provides a comprehensive overview of the Source2Social application architecture, including system design, data flow, and component interactions.

## Table of Contents
- [System Overview](#system-overview)
- [Architecture Diagram](#architecture-diagram)
- [Core Components](#core-components)
- [Data Flow](#data-flow)
- [Database Schema](#database-schema)
- [API Design](#api-design)
- [Security Considerations](#security-considerations)
- [Scalability](#scalability)
- [Deployment Architecture](#deployment-architecture)

## System Overview

Source2Social is a Flask-based web application that automatically transforms GitHub commits into social media posts. The system follows a microservices-inspired architecture with clear separation of concerns.

### Key Principles
- **Event-Driven**: Responds to GitHub webhook events
- **Modular**: Clear separation between web, business logic, and data layers
- **Extensible**: Easy to add new integrations and features
- **Stateless**: Designed for horizontal scaling

## Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub Repo   │───▶│  GitHub Webhook │───▶│  Source2Social  │
│                 │    │                 │    │     Backend     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Twitter/X     │◀───│  Social Media   │◀───│   Post Engine   │
│   Integration   │    │   Publisher     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CodeRabbit    │◀───│   Analytics     │◀───│   Database      │
│   Integration   │    │   Engine        │    │   (SQLite)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core Components

### 1. Web Layer (`app.py`)

**Purpose**: Handles HTTP requests and responses, manages routing and middleware.

**Key Responsibilities**:
- Route incoming webhook events
- Serve the web dashboard
- Handle authentication and sessions
- Manage API endpoints

**Key Classes/Functions**:
```python
# Main Flask application
app = Flask(__name__)

# Webhook endpoint
@app.route('/webhook/github', methods=['POST'])
def github_webhook()

# Dashboard endpoint
@app.route('/dashboard')
def dashboard()
```

### 2. Business Logic Layer

#### Post Generation Engine
**Purpose**: Transforms commit data into social media posts using AI.

**Key Responsibilities**:
- Parse GitHub webhook payloads
- Extract relevant commit information
- Generate social media content using LLMs
- Apply post templates and formatting

**Key Functions**:
```python
def generate_post_from_commit(commit_data)
def apply_post_template(content, template)
def enhance_with_coderabbit_insights(post, repo_data)
```

#### Integration Services
**Purpose**: Manages third-party service integrations.

**Services**:
- **GitHub Service**: Webhook validation and data extraction
- **Twitter Service**: Social media posting and OAuth
- **CodeRabbit Service**: Code analysis and insights
- **OpenAI Service**: Content generation

### 3. Data Layer (`database/db.py`)

**Purpose**: Manages data persistence and database operations.

**Key Responsibilities**:
- Database schema management
- CRUD operations for posts and reports
- Data validation and sanitization
- Connection pooling and transaction management

**Key Functions**:
```python
def init_db()
def create_post(post_data)
def get_posts_by_status(status)
def create_report(report_data)
```

### 4. Template Engine (`templates/`)

**Purpose**: Renders HTML pages and manages UI components.

**Key Templates**:
- `base.html`: Base template with navigation
- `dashboard.html`: Main dashboard interface
- `landing.html`: Public landing page
- `settings_*.html`: Configuration pages

## Data Flow

### 1. Commit to Post Flow

```
GitHub Commit → Webhook → Validation → Parse Data → Generate Post → Store → Publish
```

**Detailed Steps**:

1. **Webhook Reception**
   ```python
   @app.route('/webhook/github', methods=['POST'])
   def github_webhook():
       # Validate webhook signature
       # Extract commit data
       # Process commits
   ```

2. **Data Processing**
   ```python
   def process_commit_data(payload):
       # Extract commit information
       # Filter relevant commits
       # Prepare data for post generation
   ```

3. **Post Generation**
   ```python
   def generate_social_post(commit_data):
       # Use AI to generate content
       # Apply templates
       # Validate post content
   ```

4. **Storage and Publishing**
   ```python
   def store_and_publish(post):
       # Save to database
       # Queue for social media publishing
       # Update post status
   ```

### 2. Dashboard Data Flow

```
User Request → Authentication → Data Retrieval → Template Rendering → Response
```

### 3. Integration Data Flow

```
External Service → API Call → Data Processing → Storage → UI Update
```

## Database Schema

### Posts Table
```sql
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    commit_hash TEXT NOT NULL,
    commit_message TEXT NOT NULL,
    author TEXT NOT NULL,
    repository TEXT NOT NULL,
    generated_content TEXT NOT NULL,
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP,
    social_media_data TEXT
);
```

### Reports Table
```sql
CREATE TABLE reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization TEXT NOT NULL,
    from_date TEXT NOT NULL,
    to_date TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    report_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT
);
```

### Metrics Table
```sql
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER,
    metric_name TEXT NOT NULL,
    metric_value TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (report_id) REFERENCES reports (id)
);
```

## API Design

### RESTful Endpoints

#### Webhook Endpoints
- `POST /webhook/github` - GitHub webhook receiver
- `GET /webhook/status` - Webhook health check

#### Dashboard Endpoints
- `GET /dashboard` - Main dashboard
- `GET /posts` - List generated posts
- `POST /posts/{id}/publish` - Publish post
- `PUT /posts/{id}` - Update post

#### Integration Endpoints
- `GET /integrations/github` - GitHub integration status
- `POST /integrations/twitter/auth` - Twitter OAuth
- `GET /integrations/coderabbit/status` - CodeRabbit status

#### Report Endpoints
- `POST /reports/generate` - Generate CodeRabbit report
- `GET /reports/{id}` - Get report details
- `GET /reports` - List reports

### API Response Format

**Success Response**:
```json
{
    "status": "success",
    "data": { ... },
    "message": "Operation completed successfully"
}
```

**Error Response**:
```json
{
    "status": "error",
    "error": "Error description",
    "code": "ERROR_CODE"
}
```

## Security Considerations

### 1. Webhook Security
- **Signature Validation**: All GitHub webhooks are validated using HMAC-SHA256
- **Secret Management**: Webhook secrets stored in environment variables
- **Rate Limiting**: Implemented to prevent abuse

### 2. API Security
- **Input Validation**: All inputs are validated and sanitized
- **SQL Injection Prevention**: Using parameterized queries
- **CORS Configuration**: Properly configured for web requests

### 3. Data Protection
- **Sensitive Data**: API keys and tokens stored in environment variables
- **Data Encryption**: Sensitive data encrypted at rest
- **Access Control**: Role-based access control for different user types

### 4. OAuth Security
- **State Parameter**: CSRF protection for OAuth flows
- **Token Management**: Secure token storage and refresh
- **Scope Limitation**: Minimal required permissions

## Scalability

### Horizontal Scaling
- **Stateless Design**: Application can run on multiple instances
- **Load Balancing**: Can be deployed behind load balancers
- **Database Scaling**: SQLite can be replaced with PostgreSQL/MySQL

### Performance Optimization
- **Caching**: Implement Redis for session and data caching
- **Async Processing**: Use Celery for background tasks
- **CDN**: Static assets served via CDN

### Monitoring
- **Health Checks**: Built-in health check endpoints
- **Logging**: Structured logging for monitoring
- **Metrics**: Application metrics collection

## Deployment Architecture

### Development Environment
```
Developer Machine → Local Flask App → SQLite Database
```

### Production Environment (Vercel)
```
GitHub Webhook → Vercel Functions → Serverless Database
```

### Production Environment (Railway)
```
GitHub Webhook → Railway App → PostgreSQL Database
```

### Container Deployment
```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/sc2sm
    depends_on:
      - db
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=sc2sm
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Technology Stack

### Backend
- **Flask**: Web framework
- **SQLite/PostgreSQL**: Database
- **SQLAlchemy**: ORM (future)
- **Celery**: Background tasks (future)

### Frontend
- **Jinja2**: Template engine
- **Bootstrap**: CSS framework
- **JavaScript**: Client-side interactions

### Integrations
- **GitHub API**: Repository and webhook management
- **Twitter API**: Social media posting
- **OpenAI API**: Content generation
- **CodeRabbit API**: Code analysis

### Deployment
- **Vercel**: Serverless deployment
- **Railway**: Container deployment
- **Docker**: Containerization

## Future Architecture Considerations

### Microservices Migration
- **Post Service**: Dedicated service for post generation
- **Integration Service**: Centralized integration management
- **Analytics Service**: Dedicated analytics and reporting

### Event-Driven Architecture
- **Message Queue**: Redis/RabbitMQ for event processing
- **Event Sourcing**: Store all events for audit and replay
- **CQRS**: Separate read and write models

### Advanced Features
- **Multi-tenant**: Support for multiple organizations
- **Real-time Updates**: WebSocket connections for live updates
- **Advanced Analytics**: Machine learning for content optimization

---

This architecture provides a solid foundation for the current features while allowing for future growth and scalability.
