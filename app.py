"""
Flask backend for CodeRabbit API integration
"""

import os
import requests
from flask import Flask, request, jsonify, abort
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
CODERABBIT_API_URL = "https://api.coderabbit.ai/v1/review"  # Placeholder URL
CODERABBIT_API_KEY = os.getenv("CODERABBIT_API_KEY")


@app.route("/report", methods=["GET"])
def generate_report():
    """
    Generate a code review report for a GitHub repository using CodeRabbit API
    
    Query parameters:
    - repo_url (required): GitHub repository URL
    - branch (optional): Branch name, defaults to 'main'
    
    Returns:
    - JSON response from CodeRabbit API
    """
    
    # Get query parameters
    repo_url = request.args.get("repo_url")
    branch = request.args.get("branch", "main")  # Default to 'main' if not provided
    
    # Validate required parameters
    if not repo_url:
        return jsonify({"error": "repo_url parameter is required"}), 400
    
    # Check if API key is configured
    if not CODERABBIT_API_KEY:
        return jsonify({"error": "CODERABBIT_API_KEY not configured"}), 500
    
    try:
        # Prepare request payload for CodeRabbit API
        payload = {
            "repository_url": repo_url,
            "branch": branch,
            "api_key": CODERABBIT_API_KEY
        }
        
        # Make request to CodeRabbit API
        response = requests.post(
            CODERABBIT_API_URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {CODERABBIT_API_KEY}"
            },
            timeout=30  # 30 second timeout
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        # Return the raw JSON response from CodeRabbit
        return jsonify(response.json())
        
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to CodeRabbit API timed out"}), 504
        
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Failed to connect to CodeRabbit API"}), 503
        
    except requests.exceptions.HTTPError as e:
        # Handle HTTP errors (4xx, 5xx)
        error_message = f"CodeRabbit API error: {e.response.status_code}"
        try:
            error_details = e.response.json()
            error_message += f" - {error_details.get('message', 'Unknown error')}"
        except:
            error_message += f" - {e.response.text}"
        
        return jsonify({"error": error_message}), e.response.status_code
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request failed: {str(e)}"}), 500
        
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy", "service": "coderabbit-backend"})


if __name__ == "__main__":
    # Development server
    app.run(debug=True, host="0.0.0.0", port=5000)
