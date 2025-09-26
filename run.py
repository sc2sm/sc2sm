#!/usr/bin/env python3
"""
Simple startup script for Source2Social Flask application
"""

import os
from app import app

if __name__ == "__main__":
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        print("Creating .env file from .env.example...")
        if os.path.exists('.env.example'):
            with open('.env.example', 'r') as example_file:
                with open('.env', 'w') as env_file:
                    env_file.write(example_file.read())
            print("✅ Created .env file. Please edit it with your actual API keys.")
        else:
            print("❌ .env.example not found. Creating basic .env file...")
            with open('.env', 'w') as env_file:
                env_file.write("""# GitHub Configuration
GITHUB_WEBHOOK_SECRET=your_github_webhook_secret_here

# Twitter API Configuration (optional)
TWITTER_API_KEY=your_twitter_api_key_here
TWITTER_API_SECRET=your_twitter_api_secret_here
TWITTER_ACCESS_TOKEN=your_twitter_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret_here

# OpenAI Configuration (optional)
OPENAI_API_KEY=your_openai_api_key_here

# Application Configuration
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
PORT=5000

# Database Configuration
DATABASE_PATH=sc2sm.db
""")

    port = 8000  # Use port 8000 to avoid macOS AirPlay conflict
    print("🚀 Starting Source2Social Flask application...")
    print(f"🌐 Open http://localhost:{port} in your browser")
    print("📝 Dashboard will show your generated posts")
    print(f"🔗 Webhook endpoint: http://localhost:{port}/webhook/github")
    print()
    print("💡 To test the webhook, run: python test_webhook.py")
    print()

    # Run the Flask application
    app.run(debug=True, host="0.0.0.0", port=port)