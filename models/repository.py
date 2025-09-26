"""
Repository model for tracking GitHub repositories.
"""
from datetime import datetime
from app import db

class Repository(db.Model):
    """Repository model for tracking GitHub repositories."""
    
    __tablename__ = 'repositories'
    
    id = db.Column(db.Integer, primary_key=True)
    github_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    html_url = db.Column(db.String(200), nullable=False)
    clone_url = db.Column(db.String(200), nullable=False)
    language = db.Column(db.String(50), nullable=True)
    stars_count = db.Column(db.Integer, default=0)
    forks_count = db.Column(db.Integer, default=0)
    is_private = db.Column(db.Boolean, default=False)
    is_fork = db.Column(db.Boolean, default=False)
    
    # Repository settings for posting
    auto_post_enabled = db.Column(db.Boolean, default=False)
    post_commits = db.Column(db.Boolean, default=True)
    post_issues = db.Column(db.Boolean, default=False)
    post_pull_requests = db.Column(db.Boolean, default=False)
    post_releases = db.Column(db.Boolean, default=True)
    min_commit_message_length = db.Column(db.Integer, default=10)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_commit_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    commits = db.relationship('Commit', backref='repository', lazy='dynamic', cascade='all, delete-orphan')
    posts = db.relationship('Post', backref='repository', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Repository {self.full_name}>'
    
    def to_dict(self):
        """Convert repository to dictionary for API responses."""
        return {
            'id': self.id,
            'github_id': self.github_id,
            'name': self.name,
            'full_name': self.full_name,
            'description': self.description,
            'html_url': self.html_url,
            'language': self.language,
            'stars_count': self.stars_count,
            'forks_count': self.forks_count,
            'is_private': self.is_private,
            'auto_post_enabled': self.auto_post_enabled,
            'post_commits': self.post_commits,
            'post_issues': self.post_issues,
            'post_pull_requests': self.post_pull_requests,
            'post_releases': self.post_releases,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_commit_at': self.last_commit_at.isoformat() if self.last_commit_at else None
        }
