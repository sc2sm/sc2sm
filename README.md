# CodeRabbit Backend

A simple Flask backend that integrates with the CodeRabbit API to generate code review reports for GitHub repositories.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your CODERABBIT_API_KEY
```

## Running the Application

### Option 1: Using Flask CLI
```bash
export FLASK_APP=app.py
flask run
```

### Option 2: Direct Python execution
```bash
python app.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### GET /report
Generate a code review report for a GitHub repository.

**Query Parameters:**
- `repo_url` (required): GitHub repository URL
- `branch` (optional): Branch name, defaults to 'main'

**Example:**
```bash
curl "http://localhost:5000/report?repo_url=https://github.com/user/repo&branch=main"
```

### GET /health
Health check endpoint.

**Example:**
```bash
curl "http://localhost:5000/health"
```

## Environment Variables

- `CODERABBIT_API_KEY`: Your CodeRabbit API key (required)

## Error Handling

The API includes comprehensive error handling for:
- Missing required parameters
- API key not configured
- Network timeouts
- HTTP errors from CodeRabbit API
- General request failures
