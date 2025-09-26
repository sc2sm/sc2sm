# Source2Social 🛠️➡️📣

Source2Social is a lightweight developer-focused tool that turns your GitHub commits into shareable social media updates.

Ideal for indie hackers, startup teams, and builders-in-public, it captures coding progress and broadcasts your momentum — automatically.

## 🚀 Why Source2Social?

- Celebrate your build journey without extra effort
- Share what you're shipping — straight from your source control
- Engage your community with real-time progress updates
- Reduce friction between product and visibility

## 🧠 How It Works

1. **GitHub Webhook**: Set up a webhook on your repo to send commit data to our backend.
2. **Commit Parsing**: We extract relevant metadata from each push event (commit message, author, files changed, etc).
3. **Post Generation**: We summarize the changes using LLMs and generate a short social-ready post (X, LinkedIn).
4. **Manual or Auto-Share**: Choose to review, edit, or automatically post updates to your social channels.

## ✨ Features

- 📡 GitHub Webhook Integration
- 🧠 Commit Summarization using LLMs
- ✍️ Editable Post Templates
- 📅 Daily Digest or Real-Time Updates
- 👥 Multiple Developer Attribution
- 🔄 Optional cross-post to org Twitter/X or personal accounts

## 🔧 Setup

### 1. Clone the Repo

```bash
git clone https://github.com/your-org/source2social.git
cd source2social
```

---

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
# Test webhook
Webhook setup complete!
Testing webhook integration
