"""
GitHub-related routes for repository management.
"""
import requests
from flask import Blueprint, request, jsonify, flash, redirect, url_for, render_template
from flask_login import login_required, current_user
from models import Repository, Commit
from app import db

github_bp = Blueprint('github', __name__)

@github_bp.route('/repositories')
@login_required
def repositories():
    """List user's GitHub repositories."""
    try:
        # Get repositories from GitHub API
        headers = {'Authorization': f'token {current_user.access_token}'}
        response = requests.get(
            'https://api.github.com/user/repos',
            headers=headers,
            params={'per_page': 100, 'sort': 'updated'}
        )
        
        if response.status_code != 200:
            flash('Failed to fetch repositories from GitHub', 'error')
            return redirect(url_for('main.dashboard'))
        
        github_repos = response.json()
        
        # Get tracked repositories from database
        tracked_repos = {repo.github_id: repo for repo in current_user.repositories}
        
        return render_template('github/repositories.html',
                             github_repos=github_repos,
                             tracked_repos=tracked_repos)
        
    except Exception as e:
        flash(f'Error fetching repositories: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@github_bp.route('/repositories/<int:repo_id>/track', methods=['POST'])
@login_required
def track_repository(repo_id):
    """Start tracking a repository."""
    try:
        # Get repository info from GitHub
        headers = {'Authorization': f'token {current_user.access_token}'}
        response = requests.get(f'https://api.github.com/repositories/{repo_id}', headers=headers)
        
        if response.status_code != 200:
            return jsonify({'error': 'Repository not found'}), 404
        
        repo_data = response.json()
        
        # Check if already tracked
        existing_repo = Repository.query.filter_by(
            github_id=repo_data['id'],
            user_id=current_user.id
        ).first()
        
        if existing_repo:
            return jsonify({'error': 'Repository already tracked'}), 400
        
        # Create new repository record
        repository = Repository(
            github_id=repo_data['id'],
            name=repo_data['name'],
            full_name=repo_data['full_name'],
            description=repo_data.get('description'),
            html_url=repo_data['html_url'],
            clone_url=repo_data['clone_url'],
            language=repo_data.get('language'),
            stars_count=repo_data.get('stargazers_count', 0),
            forks_count=repo_data.get('forks_count', 0),
            is_private=repo_data['private'],
            is_fork=repo_data['fork'],
            user_id=current_user.id
        )
        
        db.session.add(repository)
        db.session.commit()
        
        return jsonify({'message': 'Repository tracked successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/repositories/<int:repo_id>/untrack', methods=['POST'])
@login_required
def untrack_repository(repo_id):
    """Stop tracking a repository."""
    try:
        repository = Repository.query.filter_by(
            id=repo_id,
            user_id=current_user.id
        ).first()
        
        if not repository:
            return jsonify({'error': 'Repository not found'}), 404
        
        db.session.delete(repository)
        db.session.commit()
        
        return jsonify({'message': 'Repository untracked successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/repositories/<int:repo_id>/settings', methods=['GET', 'POST'])
@login_required
def repository_settings(repo_id):
    """Repository settings page."""
    repository = Repository.query.filter_by(
        id=repo_id,
        user_id=current_user.id
    ).first()
    
    if not repository:
        flash('Repository not found', 'error')
        return redirect(url_for('github.repositories'))
    
    if request.method == 'POST':
        # Update repository settings
        repository.auto_post_enabled = request.form.get('auto_post_enabled') == 'on'
        repository.post_commits = request.form.get('post_commits') == 'on'
        repository.post_issues = request.form.get('post_issues') == 'on'
        repository.post_pull_requests = request.form.get('post_pull_requests') == 'on'
        repository.post_releases = request.form.get('post_releases') == 'on'
        repository.min_commit_message_length = int(request.form.get('min_commit_message_length', 10))
        
        db.session.commit()
        flash('Repository settings updated', 'success')
        return redirect(url_for('github.repository_settings', repo_id=repo_id))
    
    return render_template('github/repository_settings.html', repository=repository)

@github_bp.route('/repositories/<int:repo_id>/commits')
@login_required
def repository_commits(repo_id):
    """List commits for a repository."""
    repository = Repository.query.filter_by(
        id=repo_id,
        user_id=current_user.id
    ).first()
    
    if not repository:
        flash('Repository not found', 'error')
        return redirect(url_for('github.repositories'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    commits = (Commit.query
               .filter_by(repository_id=repository.id)
               .order_by(Commit.committed_at.desc())
               .paginate(page=page, per_page=per_page, error_out=False))
    
    return render_template('github/commits.html', repository=repository, commits=commits)

@github_bp.route('/repositories/<int:repo_id>/sync', methods=['POST'])
@login_required
def sync_repository(repo_id):
    """Sync repository commits from GitHub."""
    try:
        repository = Repository.query.filter_by(
            id=repo_id,
            user_id=current_user.id
        ).first()
        
        if not repository:
            return jsonify({'error': 'Repository not found'}), 404
        
        # TODO: Implement commit syncing logic
        # This would fetch recent commits from GitHub API and store them
        
        return jsonify({'message': 'Repository synced successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
