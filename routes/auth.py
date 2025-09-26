"""
Authentication routes for GitHub OAuth.
"""
import requests
from flask import Blueprint, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    """Initiate GitHub OAuth login."""
    github_client_id = current_app.config.get('GITHUB_CLIENT_ID')
    if not github_client_id:
        flash('GitHub OAuth not configured', 'error')
        return redirect(url_for('main.index'))
    
    # GitHub OAuth URL
    github_oauth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={github_client_id}"
        f"&scope=user:email,repo"
        f"&redirect_uri={request.url_root}auth/callback"
    )
    
    return redirect(github_oauth_url)

@auth_bp.route('/callback')
def callback():
    """Handle GitHub OAuth callback."""
    code = request.args.get('code')
    if not code:
        flash('Authorization failed', 'error')
        return redirect(url_for('main.index'))
    
    try:
        # Exchange code for access token
        token_response = requests.post(
            'https://github.com/login/oauth/access_token',
            data={
                'client_id': current_app.config.get('GITHUB_CLIENT_ID'),
                'client_secret': current_app.config.get('GITHUB_CLIENT_SECRET'),
                'code': code
            },
            headers={'Accept': 'application/json'}
        )
        
        if token_response.status_code != 200:
            flash('Failed to obtain access token', 'error')
            return redirect(url_for('main.index'))
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        if not access_token:
            flash('No access token received', 'error')
            return redirect(url_for('main.index'))
        
        # Get user information from GitHub
        user_response = requests.get(
            'https://api.github.com/user',
            headers={'Authorization': f'token {access_token}'}
        )
        
        if user_response.status_code != 200:
            flash('Failed to get user information', 'error')
            return redirect(url_for('main.index'))
        
        github_user = user_response.json()
        
        # Check if user exists
        user = User.query.filter_by(github_id=github_user['id']).first()
        
        if user:
            # Update existing user
            user.username = github_user['login']
            user.email = github_user.get('email')
            user.avatar_url = github_user.get('avatar_url')
            user.access_token = access_token
            user.last_login = db.func.now()
        else:
            # Create new user
            user = User(
                github_id=github_user['id'],
                username=github_user['login'],
                email=github_user.get('email'),
                avatar_url=github_user.get('avatar_url'),
                access_token=access_token
            )
            db.session.add(user)
        
        db.session.commit()
        login_user(user, remember=True)
        
        flash('Successfully logged in!', 'success')
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        flash(f'Login failed: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user."""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    return redirect(url_for('main.settings'))
