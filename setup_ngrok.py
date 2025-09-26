#!/usr/bin/env python3
"""
Helper script to set up ngrok for Source2Social webhook testing
"""

import json
import requests
import subprocess
import time
from datetime import datetime

def start_ngrok():
    """Start ngrok tunnel for port 8000"""
    print("🌐 Starting ngrok tunnel for port 8000...")

    try:
        # Start ngrok in the background
        process = subprocess.Popen(
            ["ngrok", "http", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        print("⏳ Waiting for ngrok to initialize...")
        time.sleep(3)

        # Get the public URL from ngrok API
        try:
            response = requests.get("http://localhost:4040/api/tunnels")
            if response.status_code == 200:
                tunnels = response.json()["tunnels"]
                if tunnels:
                    public_url = tunnels[0]["public_url"]
                    print(f"✅ ngrok tunnel active: {public_url}")
                    print(f"🔗 Webhook URL: {public_url}/webhook/github")
                    print()
                    print("📋 GitHub Webhook Configuration:")
                    print(f"   Payload URL: {public_url}/webhook/github")
                    print("   Content type: application/json")
                    print("   Events: Push events")
                    print()
                    return public_url, process
                else:
                    print("❌ No tunnels found")
                    return None, process
            else:
                print("❌ Could not connect to ngrok API")
                return None, process
        except Exception as e:
            print(f"❌ Error getting ngrok URL: {e}")
            return None, process

    except FileNotFoundError:
        print("❌ ngrok not found. Please install ngrok:")
        print("   brew install ngrok")
        print("   or download from https://ngrok.com/")
        return None, None

def test_webhook_with_ngrok(ngrok_url):
    """Test the webhook with a sample payload"""
    webhook_url = f"{ngrok_url}/webhook/github"

    # Sample GitHub webhook payload
    payload = {
        "ref": "refs/heads/main",
        "repository": {
            "name": "source2social-test",
            "full_name": "user/source2social-test",
            "html_url": "https://github.com/user/source2social-test"
        },
        "commits": [
            {
                "id": "abc123def456789",
                "message": "Add AI-powered social media post generation 🚀",
                "timestamp": datetime.now().isoformat(),
                "author": {
                    "name": "Developer",
                    "email": "dev@example.com"
                },
                "added": ["src/post_generator.py", "templates/dashboard.html"],
                "modified": ["app.py", "requirements.txt"],
                "removed": [],
                "parents": ["def456abc789123"]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "push",
        "User-Agent": "GitHub-Hookshot/abc123"
    }

    try:
        print(f"🧪 Testing webhook: {webhook_url}")
        response = requests.post(webhook_url, json=payload, headers=headers, timeout=10)

        print(f"📊 Response: {response.status_code}")
        print(f"📄 Body: {response.text}")

        if response.status_code == 200:
            print("✅ Webhook test successful!")
            print("🎯 Check your dashboard at http://localhost:8000 to see the generated post")
        else:
            print("⚠️  Webhook test had issues, but this might be expected (signature verification)")

    except Exception as e:
        print(f"❌ Error testing webhook: {e}")

if __name__ == "__main__":
    print("🔧 Source2Social ngrok Setup")
    print("=" * 50)

    # Start ngrok
    ngrok_url, ngrok_process = start_ngrok()

    if ngrok_url:
        print("🎯 Next steps:")
        print("1. Copy the webhook URL above")
        print("2. Go to your GitHub repo settings")
        print("3. Add the webhook URL")
        print("4. Make a commit to test!")
        print()

        test_choice = input("Would you like to test the webhook now? (y/n): ").lower()
        if test_choice == 'y':
            test_webhook_with_ngrok(ngrok_url)

        print()
        print("🔄 ngrok is running in the background")
        print("📊 Visit http://localhost:4040 for ngrok dashboard")
        print("🖥️  Visit http://localhost:8000 for Source2Social dashboard")
        print("⏹️  Press Ctrl+C to stop ngrok")

        try:
            if ngrok_process:
                ngrok_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping ngrok...")
            if ngrok_process:
                ngrok_process.terminate()
    else:
        print("❌ Could not start ngrok tunnel")