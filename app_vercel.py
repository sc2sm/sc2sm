"""
Source2Social - Flask backend for turning GitHub commits into social media posts
Vercel-optimized version with better error handling
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

# Try to import and register Blueprints, but handle gracefully if they fail
try:
    from routes.reports import reports_bp
    app.register_blueprint(reports_bp)
    print("✓ Reports blueprint registered")
except ImportError as e:
    print(f"Warning: Could not import reports blueprint: {e}")

# Add custom Jinja2 filter
@app.template_filter('fromjson')
def fromjson_filter(value):
    return json_module.loads(value)

# Basic route to test deployment
@app.route('/')
def dashboard():
    """Main dashboard showing recent posts"""
    try:
        # Try to use the full dashboard functionality
        posts = db.get_posts() if 'db' in globals() else []
        return render_template("dashboard.html", posts=posts)
    except Exception as e:
        # Fallback to simple HTML if templates fail
        return f'''
        <h1>Source2Social Dashboard</h1>
        <p>Application is running on Vercel!</p>
        <p>Error with full functionality: {str(e)}</p>
        <p><a href="/health">Check health</a></p>
        '''

@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "source2social",
        "version": "1.0.0",
        "environment": "vercel" if os.getenv("VERCEL") else "local"
    })

# Export for Vercel
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=port)