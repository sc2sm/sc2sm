"""
Post model for tracking social media posts.
"""
from datetime import datetime
from app import db

class Post(db.Model):
    """Post model for tracking social media posts."""
    
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    platform = db.Column(db.String(50), nullable=False)  # twitter, linkedin, facebook, etc.
    platform_post_id = db.Column(db.String(200), nullable=True)  # ID from social media platform
    
    # Post status
    status = db.Column(db.String(20), default='draft')  # draft, scheduled, published, failed
    scheduled_at = db.Column(db.DateTime, nullable=True)
    published_at = db.Column(db.DateTime, nullable=True)
    
    # Post metadata
    hashtags = db.Column(db.Text, nullable=True)  # JSON string of hashtags
    mentions = db.Column(db.Text, nullable=True)  # JSON string of mentions
    media_urls = db.Column(db.Text, nullable=True)  # JSON string of media URLs
    
    # Engagement metrics (updated after posting)
    likes_count = db.Column(db.Integer, default=0)
    retweets_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    
    # Error handling
    error_message = db.Column(db.Text, nullable=True)
    retry_count = db.Column(db.Integer, default=0)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    repository_id = db.Column(db.Integer, db.ForeignKey('repositories.id'), nullable=True)
    commit_id = db.Column(db.Integer, db.ForeignKey('commits.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Post {self.id}: {self.content[:50]}...>'
    
    def to_dict(self):
        """Convert post to dictionary for API responses."""
        return {
            'id': self.id,
            'content': self.content,
            'platform': self.platform,
            'platform_post_id': self.platform_post_id,
            'status': self.status,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'hashtags': self.hashtags,
            'mentions': self.mentions,
            'likes_count': self.likes_count,
            'retweets_count': self.retweets_count,
            'comments_count': self.comments_count,
            'views_count': self.views_count,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @property
    def is_published(self):
        """Check if post has been published."""
        return self.status == 'published' and self.published_at is not None
    
    @property
    def is_scheduled(self):
        """Check if post is scheduled for future publishing."""
        return self.status == 'scheduled' and self.scheduled_at is not None
    
    @property
    def total_engagement(self):
        """Calculate total engagement metrics."""
        return self.likes_count + self.retweets_count + self.comments_count
