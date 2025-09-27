#!/usr/bin/env python3
"""
Source2Social Application Startup Script

This script provides a convenient way to start the Source2Social Flask application
with proper configuration and environment setup. It handles environment file
creation, port configuration, and provides helpful startup information.

Key Features:
- Automatic .env file creation from template
- Port configuration to avoid conflicts
- Helpful startup messages and instructions
- Development-friendly configuration
- Webhook endpoint information

Usage:
    python run.py

Environment Setup:
- Creates .env file from .env.example if it doesn't exist
- Falls back to basic .env template if .env.example is missing
- Configures development-friendly settings

Port Configuration:
- Uses port 8000 to avoid macOS AirPlay conflicts
- Configurable via PORT environment variable
- Binds to all interfaces (0.0.0.0) for network access

Author: Source2Social Team
Version: 1.0.0
"""

import os
from app import app

if __name__ == "__main__":
    # =============================================================================
    # ENVIRONMENT CONFIGURATION
    # =============================================================================
    
    # Create .env file if it doesn't exist for easier development setup
    if not os.path.exists('.env'):
        print("Creating .env file from .env.example...")
        if os.path.exists('.env.example'):
            # Copy from existing template
            with open('.env.example', 'r') as example_file:
                with open('.env', 'w') as env_file:
                    env_file.write(example_file.read())
            print("✅ Created .env file. Please edit it with your actual API keys.")
        else:
            # Create basic template if .env.example doesn't exist
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

    # =============================================================================
    # APPLICATION STARTUP
    # =============================================================================
    
    # Use port 8000 to avoid macOS AirPlay conflict on port 5000
    port = 8000
    
    # Display helpful startup information
    print("🚀 Starting Source2Social Flask application...")
    print(f"🌐 Open http://localhost:{port} in your browser")
    print("📝 Dashboard will show your generated posts")
    print(f"🔗 Webhook endpoint: http://localhost:{port}/webhook/github")
    print()
    print("💡 To test the webhook, run: python test_webhook.py")
    print()

    # Start the Flask application with development configuration
    app.run(debug=True, host="0.0.0.0", port=port)