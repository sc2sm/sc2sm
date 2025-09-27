"""
Source2Social - Flask backend for turning GitHub commits into social media posts
"""

import os
import sqlite3
import json
import hmac
import hashlib
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass

import requests
try:
    import tweepy
except ImportError as e:
    print(f"Warning: tweepy not available: {e}")
    tweepy = None
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
import json as json_module
from dotenv import load_dotenv
from openai import OpenAI
from requests_oauthlib import OAuth2Session
from urllib.parse import urlencode

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

# Import and register Blueprints
from routes.reports import reports_bp
app.register_blueprint(reports_bp)

# Add custom Jinja2 filter
@app.template_filter('fromjson')
def fromjson_filter(value):
    return json_module.loads(value)

# Configuration
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
# For Vercel, use /tmp directory for temporary storage
DATABASE_PATH = os.getenv("DATABASE_PATH", "/tmp/sc2sm.db" if os.getenv("VERCEL") else "sc2sm.db")

# X OAuth Configuration
X_CLIENT_ID = os.getenv("X_CLIENT_ID")
X_CLIENT_SECRET = os.getenv("X_CLIENT_SECRET")
X_REDIRECT_URI = os.getenv("X_REDIRECT_URI", "http://localhost:5000/oauth/x/callback")
X_AUTHORIZATION_BASE_URL = "https://twitter.com/i/oauth2/authorize"
X_TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
X_SCOPE = ["tweet.read", "tweet.write", "users.read", "offline.access"]

# Initialize OpenAI client
openai_client = None
if OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        print(f"Warning: Could not initialize OpenAI client: {e}")
        openai_client = None

@dataclass
class CommitData:
    author_name: str
    commit_message: str
    timestamp: str
    added_files: List[str]
    modified_files: List[str]
    removed_files: List[str]
    repository_name: str
    branch: str
    sha: str

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Posts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repository_name TEXT NOT NULL,
                commit_sha TEXT NOT NULL,
                author_name TEXT NOT NULL,
                commit_message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                files_changed TEXT NOT NULL,
                generated_post TEXT NOT NULL,
                edited_post TEXT,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                posted_at TIMESTAMP,
                platform TEXT DEFAULT 'twitter'
            )
        ''')

        # Repositories table for configuration
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS repositories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                webhook_enabled BOOLEAN DEFAULT 1,
                auto_post BOOLEAN DEFAULT 0,
                post_template TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # OAuth tokens table for X (Twitter) integration
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS oauth_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL DEFAULT 'x',
                user_id TEXT NOT NULL,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                token_type TEXT DEFAULT 'Bearer',
                expires_at TIMESTAMP,
                scope TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(platform, user_id)
            )
        ''')

        # CodeRabbit reports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coderabbit_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_date TEXT NOT NULL,
                to_date TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                summary TEXT,
                commits_analyzed INTEGER,
                files_changed INTEGER,
                issues_found INTEGER,
                score TEXT,
                report_data TEXT,
                error_message TEXT,
                request_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def save_post(self, commit_data: CommitData, generated_post: str) -> int:
        """Save a generated post to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        files_changed_json = json.dumps({
            'added': commit_data.added_files,
            'modified': commit_data.modified_files,
            'removed': commit_data.removed_files
        })

        cursor.execute('''
            INSERT INTO posts (repository_name, commit_sha, author_name, commit_message,
                             timestamp, files_changed, generated_post)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            commit_data.repository_name, commit_data.sha, commit_data.author_name,
            commit_data.commit_message, commit_data.timestamp, files_changed_json, generated_post
        ))

        post_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return post_id

    def get_posts(self, status: Optional[str] = None) -> List[Dict]:
        """Get posts, optionally filtered by status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if status:
            cursor.execute('SELECT * FROM posts WHERE status = ? ORDER BY created_at DESC', (status,))
        else:
            cursor.execute('SELECT * FROM posts ORDER BY created_at DESC')

        columns = [description[0] for description in cursor.description]
        posts = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return posts

    def update_post(self, post_id: int, edited_post: str, status: str = 'edited'):
        """Update a post with edited content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE posts SET edited_post = ?, status = ? WHERE id = ?
        ''', (edited_post, status, post_id))

        conn.commit()
        conn.close()

    def mark_posted(self, post_id: int, platform: str = 'twitter'):
        """Mark a post as posted"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE posts SET status = 'posted', posted_at = CURRENT_TIMESTAMP, platform = ?
            WHERE id = ?
        ''', (platform, post_id))

        conn.commit()
        conn.close()

    def save_oauth_token(self, platform: str, user_id: str, access_token: str, 
                        refresh_token: str = None, expires_at: str = None, 
                        scope: str = None) -> int:
        """Save or update OAuth tokens for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO oauth_tokens 
            (platform, user_id, access_token, refresh_token, expires_at, scope, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (platform, user_id, access_token, refresh_token, expires_at, scope))

        token_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return token_id

    def get_oauth_token(self, platform: str, user_id: str) -> Optional[Dict]:
        """Get OAuth tokens for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM oauth_tokens 
            WHERE platform = ? AND user_id = ?
        ''', (platform, user_id))

        row = cursor.fetchone()
        conn.close()

        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None

    def delete_oauth_token(self, platform: str, user_id: str) -> bool:
        """Delete OAuth tokens for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM oauth_tokens
            WHERE platform = ? AND user_id = ?
        ''', (platform, user_id))

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted_count > 0

    def create_coderabbit_request(self, from_date: str, to_date: str, request_id: str = None) -> int:
        """Create a new CodeRabbit report request with pending status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO coderabbit_reports (from_date, to_date, status, request_id)
            VALUES (?, ?, 'pending', ?)
        ''', (from_date, to_date, request_id))

        report_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return report_id

    def update_coderabbit_report(self, report_id: int, report_data: Dict, status: str = 'completed') -> bool:
        """Update a CodeRabbit report with results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE coderabbit_reports
            SET status = ?, summary = ?, commits_analyzed = ?, files_changed = ?,
                issues_found = ?, score = ?, report_data = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            status,
            report_data.get('summary', ''),
            report_data.get('commits_analyzed', 0),
            report_data.get('files_changed', 0),
            report_data.get('issues_found', 0),
            report_data.get('score', ''),
            json.dumps(report_data),
            report_id
        ))

        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    def update_coderabbit_report_error(self, report_id: int, error_message: str) -> bool:
        """Update a CodeRabbit report with error status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE coderabbit_reports
            SET status = 'error', error_message = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (error_message, report_id))

        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    def save_coderabbit_report(self, report_data: Dict) -> int:
        """Save a completed CodeRabbit report to database (legacy method)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        from_date = report_data.get('date_range', '').split(' to ')[0] if ' to ' in report_data.get('date_range', '') else ''
        to_date = report_data.get('date_range', '').split(' to ')[1] if ' to ' in report_data.get('date_range', '') else ''

        cursor.execute('''
            INSERT INTO coderabbit_reports
            (from_date, to_date, status, summary, commits_analyzed, files_changed, issues_found, score, report_data, completed_at)
            VALUES (?, ?, 'completed', ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            from_date, to_date,
            report_data.get('summary', ''),
            report_data.get('commits_analyzed', 0),
            report_data.get('files_changed', 0),
            report_data.get('issues_found', 0),
            report_data.get('score', ''),
            json.dumps(report_data)
        ))

        report_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return report_id

    def get_latest_coderabbit_report(self) -> Optional[Dict]:
        """Get the most recent completed CodeRabbit report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT report_data FROM coderabbit_reports
            WHERE status = 'completed' AND report_data IS NOT NULL
            ORDER BY completed_at DESC LIMIT 1
        ''')

        row = cursor.fetchone()
        conn.close()

        if row and row[0]:
            return json.loads(row[0])
        return None

    def get_coderabbit_report_by_id(self, report_id: int) -> Optional[Dict]:
        """Get a specific CodeRabbit report by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM coderabbit_reports WHERE id = ?
        ''', (report_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None

    def get_coderabbit_reports(self, limit: int = 10) -> List[Dict]:
        """Get recent CodeRabbit reports"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM coderabbit_reports
            ORDER BY created_at DESC LIMIT ?
        ''', (limit,))

        columns = [description[0] for description in cursor.description]
        reports = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return reports

class XOAuthManager:
    def __init__(self):
        self.client_id = X_CLIENT_ID
        self.client_secret = X_CLIENT_SECRET
        self.redirect_uri = X_REDIRECT_URI
        self.authorization_base_url = X_AUTHORIZATION_BASE_URL
        self.token_url = X_TOKEN_URL
        self.scope = X_SCOPE

    def get_authorization_url(self, state: str = None) -> str:
        """Generate X OAuth authorization URL"""
        if not self.client_id:
            raise ValueError("X_CLIENT_ID not configured")
        
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scope),
            'state': state or 'default_state',
            'code_challenge': 'challenge',  # For PKCE
            'code_challenge_method': 'plain'
        }
        
        return f"{self.authorization_base_url}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str, code_verifier: str = None) -> Dict:
        """Exchange authorization code for access token"""
        if not self.client_secret:
            raise ValueError("X_CLIENT_SECRET not configured")
        
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri,
        }
        
        if code_verifier:
            data['code_verifier'] = code_verifier
        
        response = requests.post(self.token_url, data=data)
        response.raise_for_status()
        
        return response.json()

    def refresh_access_token(self, refresh_token: str) -> Dict:
        """Refresh access token using refresh token"""
        if not self.client_secret:
            raise ValueError("X_CLIENT_SECRET not configured")
        
        data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token,
        }
        
        response = requests.post(self.token_url, data=data)
        response.raise_for_status()
        
        return response.json()

    def get_user_info(self, access_token: str) -> Dict:
        """Get user information using access token"""
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get('https://api.twitter.com/2/users/me', headers=headers)
        response.raise_for_status()
        
        return response.json()

class PostGenerator:
    def __init__(self):
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load the prompt template from prompt.md"""
        try:
            with open('prompt.md', 'r') as f:
                return f.read()
        except FileNotFoundError:
            return """You are a tech co-founder building in public. Your tone should blend engineering insight with product marketing clarity. You write like you're tweeting to other technical founders on X (formerly Twitter).

Use the following commit metadata to craft a short BuildInPublic-style social post:
- Author: {{author_name}}
- Commit message: {{commit_message}}
- Timestamp: {{timestamp}}
- Files changed: {{added}}, {{modified}}, {{removed}}

Goals:
- Write in first person ("I" or "we")
- Make it feel like a real dev update or product milestone
- Add light context or takeaway (what this improves, why it's useful, or what was tricky)
- Avoid buzzwords; focus on clarity and curiosity
- End with a relatable insight or a simple question

Tone:
- Technical but approachable
- Confident but not arrogant
- Curious and iterative
- No hashtags, unless organic"""

    def generate_post(self, commit_data: CommitData) -> str:
        """Generate a social media post from commit data"""

        # Format file changes for the prompt
        files_summary = []
        if commit_data.added_files:
            files_summary.append(f"Added: {', '.join(commit_data.added_files[:3])}")
        if commit_data.modified_files:
            files_summary.append(f"Modified: {', '.join(commit_data.modified_files[:3])}")
        if commit_data.removed_files:
            files_summary.append(f"Removed: {', '.join(commit_data.removed_files[:3])}")

        files_text = "; ".join(files_summary) if files_summary else "No file changes"

        # Create the full prompt
        prompt = f"""{self.prompt_template}

Commit Details:
- Author: {commit_data.author_name}
- Commit message: {commit_data.commit_message}
- Timestamp: {commit_data.timestamp}
- Files changed: {files_text}
- Repository: {commit_data.repository_name}

Generate a single social media post (STRICT LIMIT: exactly 250 characters maximum for Twitter, count carefully):"""

        try:
            if openai_client:
                response = openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an expert at writing engaging technical social media posts for developers building in public."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=150,
                    temperature=0.7
                )

                return response.choices[0].message.content.strip()
            else:
                # Fallback if OpenAI is not configured
                return f"Just shipped: {commit_data.commit_message} 🚀\n\nWorking on {commit_data.repository_name} - {files_text}\n\nWhat's everyone else building today?"

        except Exception as e:
            # Fallback to simple template if OpenAI fails
            print(f"OpenAI API error: {e}")
            return f"Just shipped: {commit_data.commit_message} 🚀\n\nWorking on {commit_data.repository_name} - {files_text}\n\nWhat's everyone else building today?"

    def generate_tweet_from_report(self, report_data: Dict) -> str:
        """Generate a tweet from CodeRabbit report data"""

        # Extract report content
        report_content = ""
        if report_data and report_data.get('result') and report_data['result'].get('data'):
            reports = report_data['result']['data']
            report_content = "\n\n".join([item.get('report', '') for item in reports if item.get('report')])

        if not report_content or report_content.strip() == "":
            report_content = "No pull request activity found in the analyzed period"

        # Create prompt for tweet generation
        prompt = f"""You are a tech co-founder building in public. Create an engaging tweet from this CodeRabbit analysis report.

Report Content:
{report_content}

Guidelines:
- Write in first person ("I" or "we")
- Make it engaging and share insights about the development work
- Keep it under 280 characters for Twitter
- Focus on key takeaways, metrics, or interesting findings
- Add personality - make it feel human and authentic
- If no activity was found, frame it positively (planning phase, reflection time, etc.)
- No hashtags unless they feel organic
- End with a question or insight that encourages engagement

Generate a single tweet:"""

        try:
            if openai_client:
                response = openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an expert at writing engaging technical social media posts for developers building in public."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=100,
                    temperature=0.8
                )

                return response.choices[0].message.content.strip()
            else:
                # Fallback if OpenAI is not configured
                if "No pull request activity" in report_content:
                    return "Taking some time to plan and reflect on the codebase this week. Sometimes the best development happens between the commits 🤔\n\nWhat's your approach to planning vs. coding time?"
                else:
                    return f"Just reviewed our recent development work with CodeRabbit AI. Great insights into our code quality and team patterns! 🚀\n\nWhat tools do you use for code analysis?"

        except Exception as e:
            # Fallback to simple template if OpenAI fails
            print(f"OpenAI API error: {e}")
            if "No pull request activity" in report_content:
                return "Taking some time to plan and reflect on the codebase this week. Sometimes the best development happens between the commits 🤔"
            else:
                return "Just reviewed our development work with AI-powered code analysis. Always learning something new from these insights! 🚀"

class TwitterPoster:
    def __init__(self):
        print("Initializing TwitterPoster with hardcoded Twitter API v1.1 credentials...")
        print(f"tweepy available: {tweepy is not None}")

        self.client = None
        self.api = None

        if tweepy and TWITTER_API_KEY and TWITTER_API_SECRET and TWITTER_ACCESS_TOKEN and TWITTER_ACCESS_TOKEN_SECRET:
            # Check for obvious credential issues
            if TWITTER_ACCESS_TOKEN == TWITTER_ACCESS_TOKEN_SECRET:
                print("❌ Twitter credential error: ACCESS_TOKEN and ACCESS_TOKEN_SECRET are identical")
                print("   This indicates invalid credentials. Please check your .env file.")
                self.client = None
                self.api = None
                return

            try:
                print("Using hardcoded Twitter API v1.1 credentials for authentication...")
                print(f"API Key length: {len(TWITTER_API_KEY)}")
                print(f"API Secret length: {len(TWITTER_API_SECRET)}")
                print(f"Access Token format: {TWITTER_ACCESS_TOKEN[:10]}...{TWITTER_ACCESS_TOKEN[-10:]}")
                print(f"Access Token Secret length: {len(TWITTER_ACCESS_TOKEN_SECRET)}")

                # Set up v1.1 authentication
                auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
                auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)

                # Create API v1.1 instance (for posting tweets)
                self.api = tweepy.API(auth, wait_on_rate_limit=True)

                # Test the connection with more detailed error info
                print("Testing Twitter API v1.1 connection...")
                user = self.api.verify_credentials()
                print(f"✅ Twitter API v1.1 authentication successful! Connected as: @{user.screen_name}")

                # Also create v2 client if possible (for modern features)
                try:
                    self.client = tweepy.Client(
                        consumer_key=TWITTER_API_KEY,
                        consumer_secret=TWITTER_API_SECRET,
                        access_token=TWITTER_ACCESS_TOKEN,
                        access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
                        wait_on_rate_limit=True
                    )
                    print("✅ Twitter API v2 client also initialized successfully")
                except Exception as e:
                    print(f"Note: Twitter API v2 client failed: {e}")

            except tweepy.TweepyException as e:
                print(f"❌ Twitter authentication failed (TweepyException): {e}")
                if hasattr(e, 'response') and e.response:
                    print(f"   HTTP Status: {e.response.status_code}")
                    print(f"   Response: {e.response.text}")
                self.client = None
                self.api = None
            except Exception as e:
                print(f"❌ Twitter authentication failed (General Exception): {e}")
                print("   Common causes:")
                print("   1. Invalid or expired credentials")
                print("   2. Incorrect access token/secret pair")
                print("   3. App permissions not set to 'Read and Write'")
                print("   4. Account suspended or restricted")
                self.client = None
                self.api = None
        else:
            print("❌ Missing Twitter API credentials in environment variables:")
            print(f"   TWITTER_API_KEY: {'✅' if TWITTER_API_KEY else '❌'}")
            print(f"   TWITTER_API_SECRET: {'✅' if TWITTER_API_SECRET else '❌'}")
            print(f"   TWITTER_ACCESS_TOKEN: {'✅' if TWITTER_ACCESS_TOKEN else '❌'}")
            print(f"   TWITTER_ACCESS_TOKEN_SECRET: {'✅' if TWITTER_ACCESS_TOKEN_SECRET else '❌'}")

    def post_tweet(self, content: str) -> bool:
        """Post a tweet and return success status"""
        if not self.client and not self.api:
            print("Twitter API not configured - missing API credentials")
            return False

        try:
            print(f"Attempting to post tweet: {content[:50]}...")

            # Try v2 API first (required for basic access level)
            if self.client:
                try:
                    print("Using v2 API for posting...")
                    response = self.client.create_tweet(text=content)
                    tweet_id = response.data['id'] if response.data else 'Unknown'
                    print(f"✅ Tweet posted via v2 API! Tweet ID: {tweet_id}")
                    return True
                except Exception as e2:
                    print(f"❌ v2 API failed: {e2}")

            # Fallback to v1.1 API if v2 fails and available
            if self.api:
                try:
                    print("Trying v1.1 API as fallback...")
                    status = self.api.update_status(content)
                    print(f"✅ Tweet posted successfully! Tweet ID: {status.id}")
                    print(f"Tweet URL: https://twitter.com/{status.user.screen_name}/status/{status.id}")
                    return True
                except Exception as e:
                    print(f"❌ v1.1 API fallback also failed: {e}")

            return False

        except Exception as e:
            print(f"❌ Failed to post tweet: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False

# Initialize components
db = DatabaseManager(DATABASE_PATH)
post_generator = PostGenerator()
twitter_poster = TwitterPoster()
x_oauth_manager = XOAuthManager()

def verify_github_signature(payload_body: bytes, signature_header: str) -> bool:
    """Verify GitHub webhook signature"""
    if not GITHUB_WEBHOOK_SECRET or GITHUB_WEBHOOK_SECRET == "your_github_webhook_secret_here":
        print("⚠️  Skipping signature verification (no secret configured)")
        return True  # Skip verification if no secret is set

    if not signature_header:
        return False

    hash_object = hmac.new(
        GITHUB_WEBHOOK_SECRET.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()

    return hmac.compare_digest(expected_signature, signature_header)

@app.route("/webhook/github", methods=["POST"])
def github_webhook():
    """Handle GitHub webhook events"""

    # Verify signature
    signature = request.headers.get('X-Hub-Signature-256')
    if not verify_github_signature(request.data, signature):
        return jsonify({"error": "Invalid signature"}), 401

    # Parse payload
    payload = request.json

    # Only handle push events
    if request.headers.get('X-GitHub-Event') != 'push':
        return jsonify({"message": "Event ignored"}), 200

    # Extract commit data
    repository_name = payload['repository']['name']
    commits = payload['commits']

    for commit in commits:
        # Skip merge commits (check if parents exist and has multiple parents)
        if commit.get('parents', []) and len(commit['parents']) > 1:
            continue

        commit_data = CommitData(
            author_name=commit['author']['name'],
            commit_message=commit['message'],
            timestamp=commit['timestamp'],
            added_files=commit['added'],
            modified_files=commit['modified'],
            removed_files=commit['removed'],
            repository_name=repository_name,
            branch=payload['ref'].split('/')[-1],
            sha=commit['id']
        )

        # Generate post
        generated_post = post_generator.generate_post(commit_data)

        # Save to database
        post_id = db.save_post(commit_data, generated_post)

        print(f"Generated post {post_id} for commit {commit_data.sha[:7]}")

    return jsonify({"message": f"Processed {len(commits)} commits"}), 200

@app.route("/")
def dashboard():
    """Main dashboard showing recent posts"""
    posts = db.get_posts()
    return render_template("dashboard.html", posts=posts)

@app.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
def edit_post(post_id):
    """Edit a post"""
    posts = db.get_posts()
    post = next((p for p in posts if p['id'] == post_id), None)

    if not post:
        flash("Post not found", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        edited_content = request.form.get("content")
        db.update_post(post_id, edited_content)
        flash("Post updated successfully", "success")
        return redirect(url_for("dashboard"))

    return render_template("edit_post.html", post=post)

@app.route("/posts/<int:post_id>/publish", methods=["POST"])
def publish_post(post_id):
    """Publish a post to Twitter"""
    posts = db.get_posts()
    post = next((p for p in posts if p['id'] == post_id), None)

    if not post:
        flash("Post not found", "error")
        return redirect(url_for("dashboard"))

    # Use edited post if available, otherwise use generated post
    content = post['edited_post'] or post['generated_post']

    if twitter_poster.post_tweet(content):
        db.mark_posted(post_id, 'twitter')
        flash("Post published successfully!", "success")
    else:
        flash("Failed to publish post", "error")

    return redirect(url_for("dashboard"))

# Settings routes (from UI branch)
@app.route("/settings/source")
def settings_source():
    """Source code settings page"""
    return render_template("settings_source.html")

@app.route("/settings/social")
def settings_social():
    """Social media settings page"""
    return render_template("settings_social.html")

@app.route("/settings/coderabbit")
def settings_coderabbit():
    """Code Rabbit settings page"""
    return render_template("settings_coderabbit.html")

@app.route("/settings/post")
def settings_post():
    """Post settings page"""
    return render_template("settings_post.html")

@app.route("/settings/llm")
def settings_llm():
    """LLM settings page"""
    return render_template("settings_llm.html")

@app.route("/integrations/coderabbit")
def integrations_coderabbit():
    """Code Rabbit integration page"""
    return render_template("integrations_coderabbit.html")

@app.route("/api/coderabbit/analyze", methods=["POST"])
def api_coderabbit_analyze():
    """Start CodeRabbit analysis - creates request and triggers API call"""
    import uuid
    import threading
    from services.coderabbit import generate_coderabbit_report, validate_report_parameters

    try:
        data = request.json
        from_date = data.get('from_date')
        to_date = data.get('to_date')

        if not from_date or not to_date:
            return jsonify({"error": "Missing required parameters: from_date and to_date"}), 400

        # Validate parameters
        is_valid, error_msg, validated_params = validate_report_parameters(data)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        # Create a unique request ID
        request_id = str(uuid.uuid4())

        # Create database entry with pending status
        report_id = db.create_coderabbit_request(from_date, to_date, request_id)

        # Start async report generation in background
        def generate_report_async():
            try:
                result = generate_coderabbit_report(
                    from_date=validated_params['from_date'],
                    to_date=validated_params['to_date'],
                    **validated_params.get('optional_params', {})
                )

                if result.get('status') == 'error':
                    db.update_coderabbit_report_error(report_id, result.get('error', 'Unknown error'))
                else:
                    # Format response data
                    report_data = result.get('data', {})
                    response_data = {
                        "summary": f"Analyzed repository from {from_date} to {to_date}.",
                        "commits_analyzed": report_data.get('commits_analyzed', 0),
                        "files_changed": report_data.get('files_changed', 0),
                        "issues_found": report_data.get('issues_found', 0),
                        "score": report_data.get('score', 'N/A'),
                        "date_range": f"{from_date} to {to_date}",
                        "timestamp": datetime.now().isoformat(),
                        "raw_data": report_data
                    }

                    db.update_coderabbit_report(report_id, response_data)

            except Exception as e:
                db.update_coderabbit_report_error(report_id, str(e))

        # Start background thread
        thread = threading.Thread(target=generate_report_async)
        thread.daemon = True
        thread.start()

        return jsonify({
            "message": "Report generation started",
            "report_id": report_id,
            "request_id": request_id,
            "status": "pending",
            "estimated_time": "2-5 minutes"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/coderabbit/reports", methods=["POST"])
def api_coderabbit_save_report():
    """Save a CodeRabbit report to database"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        report_id = db.save_coderabbit_report(data)
        return jsonify({"id": report_id, "message": "Report saved successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/coderabbit/reports/latest", methods=["GET"])
def api_coderabbit_latest_report():
    """Get the most recent CodeRabbit report from database"""
    try:
        # Use the same database as reports routes
        from database.db import get_db_connection

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT report_data FROM reports
            WHERE status = 'completed' AND report_data IS NOT NULL
            ORDER BY created_at DESC LIMIT 1
        ''')

        row = cursor.fetchone()
        conn.close()

        if row and row[0]:
            import json
            report_data = json.loads(row[0])
            return jsonify({"data": report_data})
        else:
            return jsonify({"data": None, "message": "No reports found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/coderabbit/reports", methods=["GET"])
def api_coderabbit_list_reports():
    """Get list of CodeRabbit reports from database"""
    try:
        limit = request.args.get('limit', 10, type=int)
        reports = db.get_coderabbit_reports(limit=limit)
        return jsonify({"data": reports, "count": len(reports)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/coderabbit/reports/<int:report_id>/status", methods=["GET"])
def api_coderabbit_report_status(report_id):
    """Check the status of a specific CodeRabbit report"""
    try:
        report = db.get_coderabbit_report_by_id(report_id)
        if not report:
            return jsonify({"error": "Report not found"}), 404

        response = {
            "id": report['id'],
            "status": report['status'],
            "from_date": report['from_date'],
            "to_date": report['to_date'],
            "created_at": report['created_at'],
            "completed_at": report['completed_at']
        }

        if report['status'] == 'completed' and report['report_data']:
            response['data'] = json.loads(report['report_data'])
        elif report['status'] == 'error':
            response['error_message'] = report['error_message']

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# X OAuth routes (from main branch)
@app.route("/oauth/x/authorize")
def x_oauth_authorize():
    """Initiate X OAuth flow"""
    try:
        # Generate a random state for security
        import secrets
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        
        # Get authorization URL
        auth_url = x_oauth_manager.get_authorization_url(state)
        
        return redirect(auth_url)
    except ValueError as e:
        flash(f"OAuth configuration error: {str(e)}", "error")
        return redirect(url_for("dashboard"))
    except Exception as e:
        flash(f"Failed to initiate OAuth: {str(e)}", "error")
        return redirect(url_for("dashboard"))

@app.route("/oauth/x/callback")
def x_oauth_callback():
    """Handle X OAuth callback"""
    try:
        # Verify state parameter
        state = request.args.get('state')
        if state != session.get('oauth_state'):
            flash("Invalid OAuth state", "error")
            return redirect(url_for("dashboard"))
        
        # Get authorization code
        code = request.args.get('code')
        if not code:
            error = request.args.get('error')
            flash(f"OAuth authorization failed: {error}", "error")
            return redirect(url_for("dashboard"))
        
        # Exchange code for tokens
        token_response = x_oauth_manager.exchange_code_for_token(code)
        
        # Get user information
        user_info = x_oauth_manager.get_user_info(token_response['access_token'])
        user_id = user_info['data']['id']
        username = user_info['data']['username']
        
        # Calculate expiration time
        expires_at = None
        if 'expires_in' in token_response:
            expires_at = datetime.now().timestamp() + token_response['expires_in']
        
        # Save tokens to database
        db.save_oauth_token(
            platform='x',
            user_id=user_id,
            access_token=token_response['access_token'],
            refresh_token=token_response.get('refresh_token'),
            expires_at=expires_at,
            scope=' '.join(token_response.get('scope', []))
        )
        
        # Clear OAuth state from session
        session.pop('oauth_state', None)
        
        flash(f"Successfully connected to X account @{username}!", "success")
        return redirect(url_for("dashboard"))
        
    except Exception as e:
        flash(f"OAuth callback failed: {str(e)}", "error")
        return redirect(url_for("dashboard"))

@app.route("/oauth/x/disconnect")
def x_oauth_disconnect():
    """Disconnect X OAuth account"""
    try:
        # For now, we'll disconnect the first available account
        # In a real app, you'd want to identify which user to disconnect
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id FROM oauth_tokens WHERE platform = 'x' LIMIT 1")
        result = cursor.fetchone()
        
        if result:
            user_id = result[0]
            db.delete_oauth_token('x', user_id)
            flash("Successfully disconnected X account", "success")
        else:
            flash("No X account connected", "info")
        
        conn.close()
        return redirect(url_for("dashboard"))
        
    except Exception as e:
        flash(f"Failed to disconnect X account: {str(e)}", "error")
        return redirect(url_for("dashboard"))

@app.route("/oauth/x/status")
def x_oauth_status():
    """Check X OAuth connection status"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT user_id, expires_at FROM oauth_tokens WHERE platform = 'x' LIMIT 1")
        result = cursor.fetchone()

        if result:
            user_id, expires_at = result
            is_expired = expires_at and datetime.now().timestamp() > float(expires_at)

            return jsonify({
                "connected": True,
                "user_id": user_id,
                "expired": is_expired,
                "expires_at": expires_at
            })
        else:
            return jsonify({
                "connected": False,
                "user_id": None,
                "expired": False,
                "expires_at": None
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/reports/generate-tweet", methods=["POST"])
def api_generate_tweet_from_report():
    """Generate a tweet from CodeRabbit report data using OpenAI"""
    try:
        data = request.json
        if not data or 'report_data' not in data:
            return jsonify({"error": "report_data is required"}), 400

        report_data = data['report_data']

        # Generate tweet using the PostGenerator
        tweet_content = post_generator.generate_tweet_from_report(report_data)

        return jsonify({
            "tweet_content": tweet_content,
            "posted": False,  # Just generated, not posted yet
            "message": "Tweet generated successfully"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/reports/post-tweet", methods=["POST"])
def api_post_tweet():
    """Post a tweet using the Twitter API"""
    try:
        data = request.json
        if not data or 'tweet_content' not in data:
            return jsonify({"error": "tweet_content is required"}), 400

        tweet_content = data['tweet_content']

        # Check if Twitter API is available
        if not twitter_poster.client and not twitter_poster.api:
            return jsonify({
                "posted": False,
                "error": "Twitter API not configured. Check your credentials in .env file.",
                "details": "TWITTER_ACCESS_TOKEN and TWITTER_ACCESS_TOKEN_SECRET may be invalid or expired"
            }), 400

        # Post tweet using TwitterPoster
        print(f"Attempting to post tweet via API: {tweet_content[:50]}...")
        success = twitter_poster.post_tweet(tweet_content)

        if success:
            print("✅ Tweet posted successfully via API endpoint")
            return jsonify({
                "posted": True,
                "tweet_content": tweet_content,
                "message": "Tweet posted successfully"
            })
        else:
            print("❌ Tweet posting failed via API endpoint")
            return jsonify({
                "posted": False,
                "error": "Failed to post tweet. Twitter API returned an error.",
                "details": "Check server logs for specific error details. Credentials may be invalid or expired."
            }), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/reports/generate-and-post-tweet", methods=["POST"])
def api_generate_and_post_tweet():
    """Generate and immediately post a tweet from CodeRabbit report data"""
    try:
        data = request.json
        if not data or 'report_data' not in data:
            return jsonify({"error": "report_data is required"}), 400

        report_data = data['report_data']

        # Generate tweet
        tweet_content = post_generator.generate_tweet_from_report(report_data)

        # Post tweet
        success = twitter_poster.post_tweet(tweet_content)

        return jsonify({
            "tweet_content": tweet_content,
            "posted": success,
            "message": "Tweet generated and posted successfully" if success else "Tweet generated but posting failed"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "source2social",
        "version": "1.0.0"
    })

# For Vercel deployment
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=port)

# Export the app for Vercel
app = app