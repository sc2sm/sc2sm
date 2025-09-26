"""
Flask application entry point for GitHub to Social Media converter.
"""
import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    """Application factory pattern."""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost/sc2sm')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # GitHub OAuth configuration
    app.config['GITHUB_CLIENT_ID'] = os.getenv('GITHUB_CLIENT_ID')
    app.config['GITHUB_CLIENT_SECRET'] = os.getenv('GITHUB_CLIENT_SECRET')
    
    # Twitter API configuration
    app.config['TWITTER_API_KEY'] = os.getenv('TWITTER_API_KEY')
    app.config['TWITTER_API_SECRET'] = os.getenv('TWITTER_API_SECRET')
    app.config['TWITTER_ACCESS_TOKEN'] = os.getenv('TWITTER_ACCESS_TOKEN')
    app.config['TWITTER_ACCESS_TOKEN_SECRET'] = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.github import github_bp
    from routes.twitter import twitter_bp
    from routes.main import main_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(github_bp, url_prefix='/github')
    app.register_blueprint(twitter_bp, url_prefix='/twitter')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
