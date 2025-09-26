"""
GitHub API service for repository and commit management.
"""
import requests
import hmac
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from models import Repository, Commit, User
from app import db

class GitHubService:
    """Service for interacting with GitHub API."""
    
    def __init__(self, access_token: str = None):
        self.access_token = access_token
        self.base_url = "https://api.github.com"
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'SC2SM/1.0'
        }
        
        if access_token:
            self.headers['Authorization'] = f'token {access_token}'
    
    def get_user_repositories(self, user: User) -> List[Dict[str, Any]]:
        """Get user's repositories from GitHub."""
        try:
            response = requests.get(
                f"{self.base_url}/user/repos",
                headers=self.headers,
                params={'per_page': 100, 'sort': 'updated'}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching repositories: {e}")
            return []
    
    def get_repository(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """Get repository information from GitHub."""
        try:
            response = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching repository {owner}/{repo}: {e}")
            return None
    
    def get_repository_commits(self, owner: str, repo: str, since: datetime = None) -> List[Dict[str, Any]]:
        """Get repository commits from GitHub."""
        try:
            params = {'per_page': 100}
            if since:
                params['since'] = since.isoformat()
            
            response = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}/commits",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching commits for {owner}/{repo}: {e}")
            return []
    
    def get_commit_details(self, owner: str, repo: str, sha: str) -> Optional[Dict[str, Any]]:
        """Get detailed commit information from GitHub."""
        try:
            response = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}/commits/{sha}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching commit {sha}: {e}")
            return None
    
    def sync_repository_commits(self, repository: Repository) -> int:
        """Sync commits for a repository from GitHub."""
        if not repository.auto_post_enabled:
            return 0
        
        # Get commits since last sync
        since = repository.last_commit_at
        commits_data = self.get_repository_commits(
            repository.full_name.split('/')[0],
            repository.full_name.split('/')[1],
            since
        )
        
        new_commits = 0
        for commit_data in commits_data:
            # Check if commit already exists
            existing_commit = Commit.query.filter_by(
                github_id=commit_data['sha'],
                repository_id=repository.id
            ).first()
            
            if not existing_commit:
                # Create new commit record
                commit = Commit(
                    github_id=commit_data['sha'],
                    message=commit_data['commit']['message'],
                    author_name=commit_data['commit']['author']['name'],
                    author_email=commit_data['commit']['author']['email'],
                    committer_name=commit_data['commit']['committer']['name'],
                    committer_email=commit_data['commit']['committer']['email'],
                    html_url=commit_data['html_url'],
                    committed_at=datetime.fromisoformat(
                        commit_data['commit']['committer']['date'].replace('Z', '+00:00')
                    ),
                    repository_id=repository.id
                )
                
                # Get detailed commit info for stats
                detailed_commit = self.get_commit_details(
                    repository.full_name.split('/')[0],
                    repository.full_name.split('/')[1],
                    commit_data['sha']
                )
                
                if detailed_commit:
                    commit.additions = detailed_commit.get('stats', {}).get('additions', 0)
                    commit.deletions = detailed_commit.get('stats', {}).get('deletions', 0)
                    commit.changed_files = len(detailed_commit.get('files', []))
                
                db.session.add(commit)
                new_commits += 1
        
        if new_commits > 0:
            repository.last_commit_at = datetime.utcnow()
            db.session.commit()
        
        return new_commits
    
    def verify_webhook_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify GitHub webhook signature."""
        if not signature.startswith('sha256='):
            return False
        
        expected_signature = 'sha256=' + hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def process_webhook_payload(self, payload: Dict[str, Any]) -> bool:
        """Process GitHub webhook payload for push events."""
        try:
            if payload.get('ref_type') != 'branch':
                return False
            
            repository_data = payload.get('repository', {})
            commits = payload.get('commits', [])
            
            if not commits:
                return False
            
            # Find repository in database
            repository = Repository.query.filter_by(
                github_id=repository_data['id']
            ).first()
            
            if not repository or not repository.auto_post_enabled:
                return False
            
            # Process each commit
            for commit_data in commits:
                # Check if commit already exists
                existing_commit = Commit.query.filter_by(
                    github_id=commit_data['id'],
                    repository_id=repository.id
                ).first()
                
                if not existing_commit:
                    # Create new commit record
                    commit = Commit(
                        github_id=commit_data['id'],
                        message=commit_data['message'],
                        author_name=commit_data['author']['name'],
                        author_email=commit_data['author']['email'],
                        committer_name=commit_data['committer']['name'],
                        committer_email=commit_data['committer']['email'],
                        html_url=commit_data['url'],
                        committed_at=datetime.fromisoformat(
                            commit_data['timestamp'].replace('Z', '+00:00')
                        ),
                        repository_id=repository.id,
                        additions=commit_data.get('added', 0),
                        deletions=commit_data.get('removed', 0),
                        changed_files=len(commit_data.get('modified', [])) + 
                                    len(commit_data.get('added', [])) + 
                                    len(commit_data.get('removed', []))
                    )
                    
                    db.session.add(commit)
            
            db.session.commit()
            return True
            
        except Exception as e:
            print(f"Error processing webhook payload: {e}")
            db.session.rollback()
            return False
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get authenticated user information from GitHub."""
        try:
            response = requests.get(
                f"{self.base_url}/user",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching user info: {e}")
            return None
    
    def check_repository_access(self, owner: str, repo: str) -> bool:
        """Check if user has access to a repository."""
        try:
            response = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}",
                headers=self.headers
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
