"""
WSGI entry point for production deployment.
"""
import os
from app import create_app

# Create application instance
application = create_app()

if __name__ == "__main__":
    # For development
    application.run()
