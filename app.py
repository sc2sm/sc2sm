"""
Flask backend for CodeRabbit Report Generation
Main application file with clean modular architecture
Sep 26, 2025
"""

import os
from typing import Dict, Any
from flask import Flask, jsonify
from dotenv import load_dotenv
from routes.reports import reports_bp

# Load environment variables
load_dotenv()


def create_app() -> Flask:
    """
    Application factory pattern for creating Flask app instance.
    
    This function creates and configures a Flask application with:
    - Environment-based configuration
    - Blueprint registration for modular routing
    - Health check endpoint for monitoring
    
    Returns:
        Flask: Configured Flask application instance
        
    Environment Variables:
        SECRET_KEY: Flask secret key for session management
    """
    app = Flask(__name__)

    # Configuration
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # Register Blueprints
    app.register_blueprint(reports_bp)

    # Health check endpoint
    @app.route("/health", methods=["GET"])
    def health_check() -> Dict[str, str]:
        """
        Simple health check endpoint for monitoring service status.
        
        Returns:
            Dict[str, str]: JSON response with service status information
        """
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
