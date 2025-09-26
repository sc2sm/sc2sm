from app import app

# Vercel handler function
def handler(request, context):
    return app

# WSGI application entry point
application = app
