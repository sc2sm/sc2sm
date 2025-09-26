"""
Helper functions for common operations.
"""
import re
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs

def generate_secret_key(length: int = 32) -> str:
    """Generate a secure random secret key."""
    return secrets.token_urlsafe(length)

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(password) == hashed

def clean_commit_message(message: str) -> str:
    """Clean and format a commit message."""
    if not message:
        return ""
    
    # Remove common prefixes
    prefixes_to_remove = [
        'feat:', 'fix:', 'docs:', 'style:', 'refactor:', 'test:', 'chore:',
        'feature:', 'bugfix:', 'hotfix:', 'merge:', 'revert:'
    ]
    
    clean_message = message.strip()
    for prefix in prefixes_to_remove:
        if clean_message.lower().startswith(prefix):
            clean_message = clean_message[len(prefix):].strip()
            break
    
    # Remove extra whitespace
    clean_message = re.sub(r'\s+', ' ', clean_message)
    
    return clean_message

def extract_hashtags(text: str) -> List[str]:
    """Extract hashtags from text."""
    hashtag_pattern = r'#\w+'
    hashtags = re.findall(hashtag_pattern, text)
    return list(set(hashtags))  # Remove duplicates

def extract_mentions(text: str) -> List[str]:
    """Extract mentions from text."""
    mention_pattern = r'@\w+'
    mentions = re.findall(mention_pattern, text)
    return list(set(mentions))  # Remove duplicates

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to a maximum length."""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def format_duration(seconds: int) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m {seconds % 60}s"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"

def parse_github_url(url: str) -> Optional[Dict[str, str]]:
    """Parse GitHub URL to extract owner and repository."""
    if not url:
        return None
    
    # Handle different GitHub URL formats
    patterns = [
        r'github\.com/([^/]+)/([^/]+)',
        r'github\.com/([^/]+)/([^/]+)\.git',
        r'git@github\.com:([^/]+)/([^/]+)\.git'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return {
                'owner': match.group(1),
                'repo': match.group(2).replace('.git', '')
            }
    
    return None

def is_valid_github_url(url: str) -> bool:
    """Check if URL is a valid GitHub repository URL."""
    return parse_github_url(url) is not None

def generate_webhook_secret() -> str:
    """Generate a secure webhook secret."""
    return secrets.token_urlsafe(32)

def validate_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Validate webhook signature."""
    import hmac
    
    if not signature.startswith('sha256='):
        return False
    
    expected_signature = 'sha256=' + hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:255-len(ext)-1] + ('.' + ext if ext else '')
    
    return filename

def format_commit_stats(additions: int, deletions: int) -> str:
    """Format commit statistics."""
    if additions == 0 and deletions == 0:
        return "No changes"
    
    stats = []
    if additions > 0:
        stats.append(f"+{additions}")
    if deletions > 0:
        stats.append(f"-{deletions}")
    
    return " ".join(stats)

def calculate_commit_score(commit: Dict[str, Any]) -> int:
    """Calculate a score for commit importance."""
    score = 0
    
    # Base score
    score += 1
    
    # Message length (longer messages are often more important)
    message_length = len(commit.get('message', ''))
    if message_length > 50:
        score += 1
    if message_length > 100:
        score += 1
    
    # File changes
    changed_files = commit.get('changed_files', 0)
    if changed_files > 5:
        score += 1
    if changed_files > 10:
        score += 1
    
    # Code changes
    additions = commit.get('additions', 0)
    deletions = commit.get('deletions', 0)
    total_changes = additions + deletions
    
    if total_changes > 100:
        score += 1
    if total_changes > 500:
        score += 1
    
    # Keywords that indicate importance
    important_keywords = ['fix', 'feature', 'refactor', 'security', 'performance', 'breaking']
    message_lower = commit.get('message', '').lower()
    
    for keyword in important_keywords:
        if keyword in message_lower:
            score += 1
    
    return min(score, 10)  # Cap at 10

def get_time_ago(dt: datetime) -> str:
    """Get human-readable time ago string."""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"

def is_business_hours(dt: datetime = None) -> bool:
    """Check if datetime is during business hours (9 AM - 5 PM, Monday-Friday)."""
    if dt is None:
        dt = datetime.utcnow()
    
    # Check if it's a weekday
    if dt.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    # Check if it's between 9 AM and 5 PM
    hour = dt.hour
    return 9 <= hour < 17

def get_optimal_post_time(user_timezone: str = 'UTC') -> datetime:
    """Get optimal time for posting based on timezone."""
    # This is a simplified version - in production, you'd use a proper timezone library
    now = datetime.utcnow()
    
    # Add some logic to determine optimal posting times
    # For now, just return current time
    return now

def clean_html(html: str) -> str:
    """Remove HTML tags from text."""
    if not html:
        return ""
    
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', html)
    
    # Decode HTML entities
    import html
    clean = html.unescape(clean)
    
    return clean.strip()

def extract_urls(text: str) -> List[str]:
    """Extract URLs from text."""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    return list(set(urls))  # Remove duplicates

def is_valid_url(url: str) -> bool:
    """Check if URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def generate_random_string(length: int = 8) -> str:
    """Generate a random string of specified length."""
    import string
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))

def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Mask sensitive data, showing only the last few characters."""
    if len(data) <= visible_chars:
        return '*' * len(data)
    
    return '*' * (len(data) - visible_chars) + data[-visible_chars:]

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries."""
    result = {}
    for d in dicts:
        result.update(d)
    return result

def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result
