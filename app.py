"""
Flask backend for CodeRabbit Report Generation
Main application file with clean modular architecture
Sep 26, 2025
"""

import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from routes.reports import reports_bp

# Load environment variables
load_dotenv()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)

    # Configuration
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # Register Blueprints
    app.register_blueprint(reports_bp)

    # Health check endpoint
    @app.route("/health", methods=["GET"])
    def health_check():
        """Simple health check endpoint"""
        return jsonify({
            "status": "healthy",
            "service": "coderabbit-report-api"
        })

    return app

# Create the Flask app
app = create_app()

if __name__ == "__main__":
    # Development server
    app.run(debug=True, host="0.0.0.0", port=5001)
