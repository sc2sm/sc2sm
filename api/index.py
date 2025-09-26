import sys
import os

# Add the parent directory to Python path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app import app
except ImportError as e:
    print(f"Import error: {e}")
    # Create a minimal Flask app as fallback
    from flask import Flask
    app = Flask(__name__)

    @app.route('/')
    def hello():
        return "Import error occurred. Check logs."

# Export the Flask app for Vercel
application = app

if __name__ == "__main__":
    app.run()