#!/usr/bin/env python3
"""
Test script for Source2Social webhook functionality
"""

import json
import requests
from datetime import datetime

# Sample GitHub webhook payload
SAMPLE_WEBHOOK_PAYLOAD = {
    "ref": "refs/heads/main",
    "repository": {
        "name": "source2social",
        "full_name": "user/source2social",
        "html_url": "https://github.com/user/source2social"
    },
    "commits": [
        {
            "id": "abc123def456",
            "message": "Add social media post generation feature",
            "timestamp": datetime.now().isoformat(),
            "author": {
                "name": "John Developer",
                "email": "john@example.com"
            },
            "added": ["app.py", "templates/dashboard.html"],
            "modified": ["requirements.txt", "README.md"],
            "removed": [],
            "parents": ["def456abc789"]
        }
    ]
}

def test_webhook(base_url="http://localhost:8000"):
    """Test the GitHub webhook endpoint"""
    webhook_url = f"{base_url}/webhook/github"

    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "push"
    }

    try:
        response = requests.post(
            webhook_url,
            json=SAMPLE_WEBHOOK_PAYLOAD,
            headers=headers,
            timeout=10
        )

        print(f"Webhook response: {response.status_code}")
        print(f"Response body: {response.text}")

        if response.status_code == 200:
            print("✅ Webhook test passed!")
        else:
            print("❌ Webhook test failed!")

    except Exception as e:
        print(f"❌ Error testing webhook: {e}")

def test_health_check(base_url="http://localhost:8000"):
    """Test the health check endpoint"""
    health_url = f"{base_url}/health"

    try:
        response = requests.get(health_url, timeout=5)
        print(f"Health check response: {response.status_code}")
        print(f"Response body: {response.json()}")

        if response.status_code == 200:
            print("✅ Health check passed!")
        else:
            print("❌ Health check failed!")

    except Exception as e:
        print(f"❌ Error testing health check: {e}")

if __name__ == "__main__":
    print("Testing Source2Social Flask application...")
    print("Make sure the Flask app is running on localhost:8000")
    print()

    print("1. Testing health check endpoint...")
    test_health_check()
    print()

    print("2. Testing GitHub webhook endpoint...")
    test_webhook()
    print()

    print("Visit http://localhost:8000 to see the dashboard!")