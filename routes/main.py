"""
Main routes for the application.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import User, Repository, Commit, Post
from app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard."""
    # Get user statistics
    repos_count = Repository.query.filter_by(user_id=current_user.id).count()
    commits_count = Commit.query.join(Repository).filter(Repository.user_id == current_user.id).count()
    posts_count = Post.query.filter_by(user_id=current_user.id).count()
    published_posts = Post.query.filter_by(user_id=current_user.id, status='published').count()
    
    # Get recent activity
    recent_commits = (Commit.query
                     .join(Repository)
                     .filter(Repository.user_id == current_user.id)
                     .order_by(Commit.committed_at.desc())
                     .limit(10)
                     .all())
    
    recent_posts = (Post.query
                   .filter_by(user_id=current_user.id)
                   .order_by(Post.created_at.desc())
                   .limit(5)
                   .all())
    
    # Get repositories with auto-posting enabled
    auto_post_repos = Repository.query.filter_by(
        user_id=current_user.id,
        auto_post_enabled=True
    ).all()
    
    return render_template('dashboard.html',
                         repos_count=repos_count,
                         commits_count=commits_count,
                         posts_count=posts_count,
                         published_posts=published_posts,
                         recent_commits=recent_commits,
                         recent_posts=recent_posts,
                         auto_post_repos=auto_post_repos)

@main_bp.route('/post-history')
@login_required
def post_history():
    """Post history page."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    posts = (Post.query
             .filter_by(user_id=current_user.id)
             .order_by(Post.created_at.desc())
             .paginate(page=page, per_page=per_page, error_out=False))
    
    return render_template('post_history.html', posts=posts)

@main_bp.route('/settings')
@login_required
def settings():
    """User settings page."""
    return render_template('settings.html')

@main_bp.route('/webhook', methods=['POST'])
def webhook():
    """GitHub webhook endpoint for receiving commit notifications."""
    # This is a placeholder - actual webhook processing will be implemented
    # in the GitHub service module
    import json
    
    try:
        payload = request.get_json()
        if not payload:
            return {'error': 'No payload received'}, 400
        
        # Log the webhook for debugging
        print(f"Webhook received: {json.dumps(payload, indent=2)}")
        
        # TODO: Process webhook payload
        # - Extract commit information
        # - Check if repository is tracked
        # - Generate social media post
        # - Schedule or publish post
        
        return {'status': 'received'}, 200
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return {'error': 'Webhook processing failed'}, 500

@main_bp.route('/health')
def health():
    """Health check endpoint."""
    return {'status': 'healthy', 'service': 'sc2sm'}, 200
