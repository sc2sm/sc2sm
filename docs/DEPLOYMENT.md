# Deployment and Configuration Guide

## Overview

This guide covers how to deploy and configure the CodeRabbit Report API in different environments, from local development to production deployment.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- CodeRabbit API key
- Git (for cloning the repository)

## Environment Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd sc2sm
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

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

### 4. Environment Configuration

Create a `.env` file in the project root:

```bash
# Copy example environment file
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Required: CodeRabbit API Key
CODERABBIT_API_KEY=your_coderabbit_api_key_here

# Optional: Database configuration
DATABASE_PATH=reports.db

# Optional: Flask configuration
SECRET_KEY=your_secret_key_here
FLASK_ENV=development
FLASK_DEBUG=True

# Optional: Server configuration
HOST=0.0.0.0
PORT=5001
```

## Local Development

### Running the Application

#### Option 1: Direct Python execution
```bash
python app.py
```

#### Option 2: Using Flask CLI
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5001
```

#### Option 3: Using Python module
```bash
python -m flask run --host=0.0.0.0 --port=5001
```

The server will start on `http://localhost:5001`

### Development Tools

#### Code Formatting
```bash
# Format code with Black
black .

# Check code style with Flake8
flake8 .
```

#### Testing
```bash
# Run tests with pytest
pytest
```

## Production Deployment

### Docker Deployment

#### 1. Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# Run the application
CMD ["python", "app.py"]
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  coderabbit-api:
    build: .
    ports:
      - "5001:5001"
    environment:
      - CODERABBIT_API_KEY=${CODERABBIT_API_KEY}
      - DATABASE_PATH=/app/data/reports.db
      - SECRET_KEY=${SECRET_KEY}
      - FLASK_ENV=production
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

#### 3. Deploy with Docker Compose

```bash
# Create data directory
mkdir -p data

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Cloud Deployment

#### AWS EC2 Deployment

1. **Launch EC2 Instance**
   - Choose Ubuntu 20.04 LTS
   - Select appropriate instance type (t3.micro for testing)
   - Configure security group to allow port 5001

2. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv git nginx
   ```

3. **Deploy Application**
   ```bash
   git clone <repository-url>
   cd sc2sm
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure Nginx**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:5001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

5. **Setup Systemd Service**
   ```ini
   [Unit]
   Description=CodeRabbit Report API
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/sc2sm
   Environment=PATH=/home/ubuntu/sc2sm/venv/bin
   ExecStart=/home/ubuntu/sc2sm/venv/bin/python app.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

#### Heroku Deployment

1. **Create Procfile**
   ```
   web: python app.py
   ```

2. **Create runtime.txt**
   ```
   python-3.11.0
   ```

3. **Deploy to Heroku**
   ```bash
   # Install Heroku CLI
   # Login to Heroku
   heroku login

   # Create Heroku app
   heroku create your-app-name

   # Set environment variables
   heroku config:set CODERABBIT_API_KEY=your_api_key
   heroku config:set SECRET_KEY=your_secret_key

   # Deploy
   git push heroku main
   ```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CODERABBIT_API_KEY` | Yes | - | CodeRabbit API key for authentication |
| `DATABASE_PATH` | No | `reports.db` | Path to SQLite database file |
| `SECRET_KEY` | No | `dev-secret-key-change-in-production` | Flask secret key for sessions |
| `FLASK_ENV` | No | `development` | Flask environment mode |
| `FLASK_DEBUG` | No | `True` | Enable Flask debug mode |
| `HOST` | No | `0.0.0.0` | Host to bind the server |
| `PORT` | No | `5001` | Port to bind the server |

## Database Management

### Database Initialization

The database is automatically initialized when the application starts. The following tables are created:

- `reports`: Main table for storing report metadata and data
- `report_metrics`: Table for storing structured metrics

### Database Backup

```bash
# Backup database
cp reports.db reports_backup_$(date +%Y%m%d_%H%M%S).db

# Restore database
cp reports_backup_20240101_120000.db reports.db
```

### Database Migration

For production deployments, consider migrating to PostgreSQL or MySQL:

1. Install database adapter (e.g., `psycopg2` for PostgreSQL)
2. Update database connection logic
3. Create migration scripts for existing data

## Monitoring and Logging

### Application Logs

The application uses Python's built-in logging module. Configure logging levels:

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### Health Monitoring

The `/health` endpoint provides basic health monitoring:

```bash
curl http://localhost:5001/health
```

### Performance Monitoring

Consider integrating with monitoring services:
- **Prometheus + Grafana**: For metrics collection and visualization
- **Sentry**: For error tracking and performance monitoring
- **DataDog**: For comprehensive application monitoring

## Security Considerations

### API Key Security

- Store API keys in environment variables, never in code
- Use secret management services in production (AWS Secrets Manager, Azure Key Vault)
- Rotate API keys regularly

### Database Security

- Use file permissions to restrict database access
- Consider encrypting sensitive data at rest
- Implement database connection pooling for production

### Network Security

- Use HTTPS in production (configure SSL certificates)
- Implement rate limiting
- Use reverse proxy (Nginx) for additional security layers
- Configure firewall rules appropriately

## Troubleshooting

### Common Issues

1. **API Key Not Configured**
   ```
   Error: CODERABBIT_API_KEY not configured
   ```
   Solution: Set the `CODERABBIT_API_KEY` environment variable

2. **Database Permission Errors**
   ```
   Error: database is locked
   ```
   Solution: Check file permissions and ensure no other processes are accessing the database

3. **Port Already in Use**
   ```
   Error: Address already in use
   ```
   Solution: Change the port or kill the process using the port

### Debug Mode

Enable debug mode for development:

```bash
export FLASK_DEBUG=True
export FLASK_ENV=development
python app.py
```

### Log Analysis

```bash
# View application logs
tail -f app.log

# Filter error logs
grep ERROR app.log

# Monitor real-time logs
tail -f app.log | grep -E "(ERROR|WARNING)"
```

## Scaling Considerations

### Horizontal Scaling

- Use load balancer (Nginx, HAProxy) to distribute traffic
- Implement session storage in Redis or database
- Use shared database (PostgreSQL, MySQL) instead of SQLite

### Vertical Scaling

- Increase server resources (CPU, RAM)
- Optimize database queries
- Implement caching for frequently accessed data

### Microservices Architecture

Consider breaking down into microservices:
- Report generation service
- Database service
- Authentication service
- Notification service
