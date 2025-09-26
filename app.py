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

class TwitterPoster:
    def __init__(self):
        if tweepy and all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
            self.client = tweepy.Client(
                consumer_key=TWITTER_API_KEY,
                consumer_secret=TWITTER_API_SECRET,
                access_token=TWITTER_ACCESS_TOKEN,
                access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
            )
        else:
            self.client = None

    def post_tweet(self, content: str) -> bool:
        """Post a tweet and return success status"""
        if not self.client:
            print("Twitter client not configured")
            return False

        try:
            self.client.create_tweet(text=content)
            return True
        except Exception as e:
            print(f"Failed to post tweet: {e}")
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
def landing():
    """Landing page"""
    return render_template("landing.html")

@app.route("/dashboard")
def dashboard():
    """Main dashboard showing recent posts"""
    posts = db.get_posts()
    return render_template("dashboard.html", posts=posts)

@app.route("/posts")
def posts_performance():
    """Posts performance analytics page"""
    posts = db.get_posts()

    # Calculate stats
    total_posts = len(posts)
    published_posts = len([p for p in posts if p['status'] == 'posted'])
    posts_this_week = len([p for p in posts if p['created_at']])  # Mock for now
    avg_engagement = 12.5  # Mock data for now

    return render_template("posts.html",
                         posts=posts,
                         total_posts=total_posts,
                         published_posts=published_posts,
                         posts_this_week=posts_this_week,
                         avg_engagement=avg_engagement)

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

@app.route("/posts/<int:post_id>/mark-published", methods=["POST"])
def mark_post_published(post_id):
    """Mark a post as published via URL sharing"""
    try:
        db.mark_posted(post_id, 'x')
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

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
    """Code Rabbit analysis API endpoint"""
    try:
        data = request.json
        project_name = data.get('project_name')
        branch = data.get('branch', 'main')
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        detailed = data.get('detailed', False)

        if not project_name or not from_date or not to_date:
            return jsonify({"error": "Missing required parameters"}), 400

        # TODO: Replace with actual Code Rabbit API integration
        # For now, return mock data for demonstration
        mock_response = {
            "summary": f"Analyzed {project_name} repository from {from_date} to {to_date}. Found several areas for improvement including code complexity and documentation coverage.",
            "commits_analyzed": 23,
            "files_changed": 45,
            "issues_found": 8,
            "score": "85/100",
            "project_name": project_name,
            "branch": branch,
            "date_range": f"{from_date} to {to_date}",
            "timestamp": datetime.now().isoformat()
        }

        if detailed:
            mock_response["detailed_analysis"] = f"""Code Quality Report for {project_name}:

✅ Strengths:
- Good test coverage (78%)
- Consistent code formatting
- Well-structured module organization

⚠️ Areas for Improvement:
- High cyclomatic complexity in 3 files
- Missing documentation for 12 functions
- Potential security issues in authentication module

🔍 Recommendations:
1. Break down complex functions in utils.py
2. Add JSDoc comments for public APIs
3. Review authentication token handling
4. Consider adding integration tests"""

        return jsonify(mock_response)

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