"""
Commit model for tracking GitHub commits.
"""
from datetime import datetime
from app import db

class Commit(db.Model):
    """Commit model for tracking GitHub commits."""
    
    __tablename__ = 'commits'
    
    id = db.Column(db.Integer, primary_key=True)
    github_id = db.Column(db.String(40), unique=True, nullable=False)  # SHA hash
    message = db.Column(db.Text, nullable=False)
    author_name = db.Column(db.String(200), nullable=False)
    author_email = db.Column(db.String(200), nullable=False)
    committer_name = db.Column(db.String(200), nullable=False)
    committer_email = db.Column(db.String(200), nullable=False)
    html_url = db.Column(db.String(200), nullable=False)
    
    # Commit statistics
    additions = db.Column(db.Integer, default=0)
    deletions = db.Column(db.Integer, default=0)
    changed_files = db.Column(db.Integer, default=0)
    
    # Processing status
    processed = db.Column(db.Boolean, default=False)
    post_generated = db.Column(db.Boolean, default=False)
    post_published = db.Column(db.Boolean, default=False)
    processing_error = db.Column(db.Text, nullable=True)
    
    # Foreign keys
    repository_id = db.Column(db.Integer, db.ForeignKey('repositories.id'), nullable=False)
    
    # Timestamps
    committed_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    posts = db.relationship('Post', backref='commit', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Commit {self.github_id[:8]}: {self.message[:50]}...>'
    
    def to_dict(self):
        """Convert commit to dictionary for API responses."""
        return {
            'id': self.id,
            'github_id': self.github_id,
            'message': self.message,
            'author_name': self.author_name,
            'author_email': self.author_email,
            'html_url': self.html_url,
            'additions': self.additions,
            'deletions': self.deletions,
            'changed_files': self.changed_files,
            'processed': self.processed,
            'post_generated': self.post_generated,
            'post_published': self.post_published,
            'committed_at': self.committed_at.isoformat() if self.committed_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
    
    @property
    def net_changes(self):
        """Calculate net changes (additions - deletions)."""
        return self.additions - self.deletions
    
    @property
    def is_significant(self):
        """Determine if commit is significant enough to post about."""
        return (
            len(self.message.strip()) >= 10 and
            (self.additions + self.deletions) > 0 and
            not self.message.lower().startswith(('merge', 'fix typo', 'update readme'))
        )
