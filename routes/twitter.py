"""
Twitter-related routes for social media posting.
"""
from flask import Blueprint, request, jsonify, flash, redirect, url_for, render_template
from flask_login import login_required, current_user
from models import Post, Repository, Commit
from app import db

twitter_bp = Blueprint('twitter', __name__)

@twitter_bp.route('/posts')
@login_required
def posts():
    """List user's Twitter posts."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    posts = (Post.query
             .filter_by(user_id=current_user.id, platform='twitter')
             .order_by(Post.created_at.desc())
             .paginate(page=page, per_page=per_page, error_out=False))
    
    return render_template('twitter/posts.html', posts=posts)

@twitter_bp.route('/posts/new', methods=['GET', 'POST'])
@login_required
def new_post():
    """Create a new Twitter post."""
    if request.method == 'POST':
        content = request.form.get('content')
        commit_id = request.form.get('commit_id')
        repository_id = request.form.get('repository_id')
        
        if not content:
            flash('Post content is required', 'error')
            return redirect(url_for('twitter.new_post'))
        
        # Create new post
        post = Post(
            content=content,
            platform='twitter',
            status='draft',
            user_id=current_user.id,
            repository_id=repository_id if repository_id else None,
            commit_id=commit_id if commit_id else None
        )
        
        db.session.add(post)
        db.session.commit()
        
        flash('Post created successfully', 'success')
        return redirect(url_for('twitter.posts'))
    
    # Get recent commits for reference
    recent_commits = (Commit.query
                     .join(Repository)
                     .filter(Repository.user_id == current_user.id)
                     .order_by(Commit.committed_at.desc())
                     .limit(10)
                     .all())
    
    return render_template('twitter/new_post.html', recent_commits=recent_commits)

@twitter_bp.route('/posts/<int:post_id>/publish', methods=['POST'])
@login_required
def publish_post(post_id):
    """Publish a Twitter post."""
    try:
        post = Post.query.filter_by(
            id=post_id,
            user_id=current_user.id,
            platform='twitter'
        ).first()
        
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        if post.status == 'published':
            return jsonify({'error': 'Post already published'}), 400
        
        # TODO: Implement actual Twitter API posting
        # For now, just mark as published
        post.status = 'published'
        post.published_at = db.func.now()
        
        db.session.commit()
        
        return jsonify({'message': 'Post published successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@twitter_bp.route('/posts/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    """Edit a Twitter post."""
    post = Post.query.filter_by(
        id=post_id,
        user_id=current_user.id,
        platform='twitter'
    ).first()
    
    if not post:
        flash('Post not found', 'error')
        return redirect(url_for('twitter.posts'))
    
    if request.method == 'POST':
        content = request.form.get('content')
        
        if not content:
            flash('Post content is required', 'error')
            return redirect(url_for('twitter.edit_post', post_id=post_id))
        
        post.content = content
        post.status = 'draft'  # Reset to draft when edited
        
        db.session.commit()
        flash('Post updated successfully', 'success')
        return redirect(url_for('twitter.posts'))
    
    return render_template('twitter/edit_post.html', post=post)

@twitter_bp.route('/posts/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    """Delete a Twitter post."""
    try:
        post = Post.query.filter_by(
            id=post_id,
            user_id=current_user.id,
            platform='twitter'
        ).first()
        
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({'message': 'Post deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@twitter_bp.route('/settings')
@login_required
def settings():
    """Twitter settings page."""
    return render_template('twitter/settings.html')

@twitter_bp.route('/connect', methods=['POST'])
@login_required
def connect():
    """Connect Twitter account."""
    # TODO: Implement Twitter OAuth connection
    flash('Twitter connection not yet implemented', 'info')
    return redirect(url_for('twitter.settings'))

@twitter_bp.route('/disconnect', methods=['POST'])
@login_required
def disconnect():
    """Disconnect Twitter account."""
    # TODO: Implement Twitter disconnection
    flash('Twitter disconnection not yet implemented', 'info')
    return redirect(url_for('twitter.settings'))
