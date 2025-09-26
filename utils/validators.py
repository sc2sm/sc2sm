"""
Validation functions for data integrity.
"""
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from datetime import datetime

def validate_email(email: str) -> bool:
    """Validate email address format."""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_url(url: str) -> bool:
    """Validate URL format."""
    if not url:
        return False
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def validate_github_url(url: str) -> bool:
    """Validate GitHub repository URL."""
    if not url:
        return False
    
    # Check if it's a valid URL first
    if not validate_url(url):
        return False
    
    # Check if it's a GitHub URL
    github_patterns = [
        r'github\.com/[^/]+/[^/]+',
        r'github\.com/[^/]+/[^/]+\.git',
        r'git@github\.com:[^/]+/[^/]+\.git'
    ]
    
    for pattern in github_patterns:
        if re.search(pattern, url):
            return True
    
    return False

def validate_twitter_handle(handle: str) -> bool:
    """Validate Twitter handle format."""
    if not handle:
        return False
    
    # Remove @ if present
    handle = handle.lstrip('@')
    
    # Twitter handle rules: 1-15 characters, alphanumeric and underscore only
    pattern = r'^[a-zA-Z0-9_]{1,15}$'
    return re.match(pattern, handle) is not None

def validate_commit_message(message: str) -> bool:
    """Validate commit message format."""
    if not message:
        return False
    
    # Commit message should not be empty and should have reasonable length
    message = message.strip()
    return 1 <= len(message) <= 1000

def validate_post_content(content: str, platform: str = 'twitter') -> bool:
    """Validate social media post content."""
    if not content:
        return False
    
    content = content.strip()
    
    # Platform-specific length limits
    limits = {
        'twitter': 280,
        'linkedin': 3000,
        'facebook': 63206,
        'instagram': 2200
    }
    
    max_length = limits.get(platform, 280)
    return 1 <= len(content) <= max_length

def validate_hashtag(hashtag: str) -> bool:
    """Validate hashtag format."""
    if not hashtag:
        return False
    
    # Hashtag should start with # and contain only alphanumeric characters
    pattern = r'^#[a-zA-Z0-9_]+$'
    return re.match(pattern, hashtag) is not None

def validate_mention(mention: str) -> bool:
    """Validate mention format."""
    if not mention:
        return False
    
    # Mention should start with @ and contain only alphanumeric characters and underscore
    pattern = r'^@[a-zA-Z0-9_]+$'
    return re.match(pattern, mention) is not False

def validate_username(username: str) -> bool:
    """Validate username format."""
    if not username:
        return False
    
    # Username should be 3-30 characters, alphanumeric and underscore only
    pattern = r'^[a-zA-Z0-9_]{3,30}$'
    return re.match(pattern, username) is not None

def validate_password(password: str) -> Dict[str, Any]:
    """Validate password strength."""
    result = {
        'valid': False,
        'errors': [],
        'score': 0
    }
    
    if not password:
        result['errors'].append('Password is required')
        return result
    
    # Length check
    if len(password) < 8:
        result['errors'].append('Password must be at least 8 characters long')
    else:
        result['score'] += 1
    
    # Uppercase check
    if not re.search(r'[A-Z]', password):
        result['errors'].append('Password must contain at least one uppercase letter')
    else:
        result['score'] += 1
    
    # Lowercase check
    if not re.search(r'[a-z]', password):
        result['errors'].append('Password must contain at least one lowercase letter')
    else:
        result['score'] += 1
    
    # Number check
    if not re.search(r'\d', password):
        result['errors'].append('Password must contain at least one number')
    else:
        result['score'] += 1
    
    # Special character check
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result['errors'].append('Password must contain at least one special character')
    else:
        result['score'] += 1
    
    # Overall validation
    result['valid'] = len(result['errors']) == 0 and result['score'] >= 3
    
    return result

def validate_webhook_payload(payload: Dict[str, Any]) -> bool:
    """Validate GitHub webhook payload structure."""
    if not payload:
        return False
    
    # Check required fields
    required_fields = ['repository', 'commits']
    
    for field in required_fields:
        if field not in payload:
            return False
    
    # Validate repository structure
    repo = payload.get('repository', {})
    if not isinstance(repo, dict):
        return False
    
    required_repo_fields = ['id', 'name', 'full_name']
    for field in required_repo_fields:
        if field not in repo:
            return False
    
    # Validate commits structure
    commits = payload.get('commits', [])
    if not isinstance(commits, list):
        return False
    
    # Validate each commit
    for commit in commits:
        if not isinstance(commit, dict):
            return False
        
        required_commit_fields = ['id', 'message', 'author', 'committer']
        for field in required_commit_fields:
            if field not in commit:
                return False
    
    return True

def validate_repository_settings(settings: Dict[str, Any]) -> bool:
    """Validate repository settings."""
    if not settings:
        return False
    
    # Check required fields
    required_fields = ['auto_post_enabled', 'post_commits']
    
    for field in required_fields:
        if field not in settings:
            return False
    
    # Validate boolean fields
    boolean_fields = ['auto_post_enabled', 'post_commits', 'post_issues', 'post_pull_requests', 'post_releases']
    for field in boolean_fields:
        if field in settings and not isinstance(settings[field], bool):
            return False
    
    # Validate numeric fields
    if 'min_commit_message_length' in settings:
        value = settings['min_commit_message_length']
        if not isinstance(value, int) or value < 0 or value > 1000:
            return False
    
    return True

def validate_user_settings(settings: Dict[str, Any]) -> bool:
    """Validate user settings."""
    if not settings:
        return False
    
    # Validate boolean fields
    boolean_fields = ['auto_post_enabled', 'include_hashtags']
    for field in boolean_fields:
        if field in settings and not isinstance(settings[field], bool):
            return False
    
    # Validate post tone
    if 'post_tone' in settings:
        valid_tones = ['professional', 'casual', 'technical']
        if settings['post_tone'] not in valid_tones:
            return False
    
    # Validate max posts per day
    if 'max_posts_per_day' in settings:
        value = settings['max_posts_per_day']
        if not isinstance(value, int) or value < 1 or value > 100:
            return False
    
    return True

def validate_api_key(api_key: str, service: str = 'generic') -> bool:
    """Validate API key format."""
    if not api_key:
        return False
    
    # Basic validation - should not be empty and should have reasonable length
    if len(api_key) < 10 or len(api_key) > 200:
        return False
    
    # Service-specific validation
    if service == 'github':
        # GitHub tokens are typically 40 characters (classic) or longer (fine-grained)
        return len(api_key) >= 40
    elif service == 'twitter':
        # Twitter API keys are typically longer
        return len(api_key) >= 20
    elif service == 'openai':
        # OpenAI API keys start with 'sk-'
        return api_key.startswith('sk-')
    
    return True

def validate_webhook_secret(secret: str) -> bool:
    """Validate webhook secret format."""
    if not secret:
        return False
    
    # Webhook secrets should be reasonably long and secure
    return 16 <= len(secret) <= 100

def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """Validate date range."""
    if not start_date or not end_date:
        return False
    
    return start_date <= end_date

def validate_pagination_params(page: int, per_page: int) -> bool:
    """Validate pagination parameters."""
    if not isinstance(page, int) or page < 1:
        return False
    
    if not isinstance(per_page, int) or per_page < 1 or per_page > 100:
        return False
    
    return True

def validate_file_upload(filename: str, content_type: str, max_size: int = 16777216) -> Dict[str, Any]:
    """Validate file upload."""
    result = {
        'valid': False,
        'errors': []
    }
    
    if not filename:
        result['errors'].append('Filename is required')
        return result
    
    # Check file extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.txt', '.md']
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if f'.{file_ext}' not in allowed_extensions:
        result['errors'].append(f'File type .{file_ext} is not allowed')
    
    # Check content type
    allowed_types = [
        'image/jpeg', 'image/png', 'image/gif',
        'application/pdf', 'text/plain', 'text/markdown'
    ]
    
    if content_type not in allowed_types:
        result['errors'].append(f'Content type {content_type} is not allowed')
    
    # Check file size (assuming max_size is in bytes)
    # Note: This would need to be implemented with actual file size
    # For now, we'll just validate the parameters
    
    result['valid'] = len(result['errors']) == 0
    return result

def validate_oauth_callback(code: str, state: str = None) -> bool:
    """Validate OAuth callback parameters."""
    if not code:
        return False
    
    # OAuth code should be reasonably long
    if len(code) < 10 or len(code) > 200:
        return False
    
    # State parameter is optional but if provided, should be valid
    if state and (len(state) < 1 or len(state) > 100):
        return False
    
    return True

def validate_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Validate webhook signature."""
    import hmac
    import hashlib
    
    if not payload or not signature or not secret:
        return False
    
    if not signature.startswith('sha256='):
        return False
    
    expected_signature = 'sha256=' + hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

def validate_rate_limit(requests_count: int, limit: int, window_seconds: int) -> bool:
    """Validate rate limiting."""
    if not isinstance(requests_count, int) or requests_count < 0:
        return False
    
    if not isinstance(limit, int) or limit < 1:
        return False
    
    if not isinstance(window_seconds, int) or window_seconds < 1:
        return False
    
    return requests_count <= limit

def validate_commit_score(score: int) -> bool:
    """Validate commit score."""
    return isinstance(score, int) and 0 <= score <= 10

def validate_engagement_metrics(metrics: Dict[str, int]) -> bool:
    """Validate engagement metrics."""
    if not isinstance(metrics, dict):
        return False
    
    required_fields = ['likes_count', 'retweets_count', 'comments_count']
    
    for field in required_fields:
        if field not in metrics:
            return False
        
        if not isinstance(metrics[field], int) or metrics[field] < 0:
            return False
    
    return True
