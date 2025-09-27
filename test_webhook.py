#!/usr/bin/env python3
"""
Source2Social Webhook Testing Script

This script provides comprehensive testing for the Source2Social webhook
functionality. It tests both the health check endpoint and the GitHub
webhook endpoint with realistic sample data.

Key Features:
- Health check endpoint testing
- GitHub webhook endpoint testing with sample payload
- Realistic commit data simulation
- Comprehensive error handling and reporting
- Development-friendly output formatting

Usage:
    python test_webhook.py

Prerequisites:
- Source2Social Flask application must be running
- Default URL: http://localhost:8000
- Webhook endpoint: /webhook/github
- Health endpoint: /health

Test Data:
- Simulates a realistic GitHub push event
- Includes commit metadata (author, message, files)
- Uses current timestamp for realistic testing
- Follows GitHub webhook payload structure

Author: Source2Social Team
Version: 1.0.0
"""

import json
import requests
from datetime import datetime

# =============================================================================
# SAMPLE WEBHOOK DATA
# =============================================================================

# Realistic GitHub webhook payload for testing
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

# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def test_webhook(base_url="http://localhost:8000"):
    """
    Test the GitHub webhook endpoint with sample commit data.
    
    This function sends a realistic GitHub webhook payload to the Source2Social
    webhook endpoint and validates the response. It checks for proper HTTP
    status codes and response content.
    
    Args:
        base_url: Base URL of the running Source2Social application
        
    Process:
        1. Constructs webhook URL
        2. Sets appropriate headers for GitHub webhook
        3. Sends POST request with sample payload
        4. Validates response status and content
        5. Reports success or failure with details
        
    Expected Response:
        - Status Code: 200 OK
        - Body: JSON with message about processed commits
        - Headers: Content-Type: application/json
    """
    webhook_url = f"{base_url}/webhook/github"

    # GitHub webhook headers
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "push"  # Indicates this is a push event
    }

    try:
        print(f"Testing webhook at: {webhook_url}")
        print(f"Payload: {json.dumps(SAMPLE_WEBHOOK_PAYLOAD, indent=2)}")
        
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
            return True
        else:
            print("❌ Webhook test failed!")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure the Flask app is running!")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timeout: Webhook took too long to respond")
        return False
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")
        return False

def test_health_check(base_url="http://localhost:8000"):
    """
    Test the health check endpoint for application status.
    
    This function verifies that the Source2Social application is running
    and responding correctly by calling the health check endpoint.
    
    Args:
        base_url: Base URL of the running Source2Social application
        
    Process:
        1. Constructs health check URL
        2. Sends GET request to health endpoint
        3. Validates response status and JSON content
        4. Reports application health status
        
    Expected Response:
        - Status Code: 200 OK
        - Body: JSON with status, service name, and version
        - Example: {"status": "healthy", "service": "source2social", "version": "1.0.0"}
    """
    health_url = f"{base_url}/health"

    try:
        print(f"Testing health check at: {health_url}")
        
        response = requests.get(health_url, timeout=5)
        print(f"Health check response: {response.status_code}")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"Response body: {json.dumps(health_data, indent=2)}")
            print("✅ Health check passed!")
            return True
        else:
            print(f"Response body: {response.text}")
            print("❌ Health check failed!")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure the Flask app is running!")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timeout: Health check took too long")
        return False
    except Exception as e:
        print(f"❌ Error testing health check: {e}")
        return False

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Source2Social Webhook Testing Script")
    print("=" * 60)
    print("Make sure the Flask app is running on localhost:8000")
    print("Start the app with: python run.py")
    print()

    # Test health check first
    print("1. Testing health check endpoint...")
    health_success = test_health_check()
    print()

    # Test webhook if health check passed
    if health_success:
        print("2. Testing GitHub webhook endpoint...")
        webhook_success = test_webhook()
        print()
        
        if webhook_success:
            print("🎉 All tests passed! Check the dashboard for generated posts.")
        else:
            print("⚠️  Webhook test failed. Check the application logs.")
    else:
        print("⚠️  Health check failed. Make sure the application is running.")
    
    print()
    print("Visit http://localhost:8000 to see the dashboard!")
    print("Visit http://localhost:8000/dashboard to manage posts!")