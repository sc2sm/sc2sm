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
import tweepy
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
import json as json_module
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

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
DATABASE_PATH = os.getenv("DATABASE_PATH", "sc2sm.db")

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
        if all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
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

@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "source2social",
        "version": "1.0.0"
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=port)