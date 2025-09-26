import sys
import os

# Add the parent directory to Python path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel handler
def handler(request):
    return app(request.environ, request.start_response)

# For Vercel serverless functions
app = app