"""
Jinja2 filters for template rendering.
"""
from datetime import datetime
from typing import Any
import re

def format_datetime(value: datetime, format: str = '%Y-%m-%d %H:%M') -> str:
    """Format datetime for display."""
    if not value:
        return ''
    return value.strftime(format)

def format_date(value: datetime, format: str = '%Y-%m-%d') -> str:
    """Format date for display."""
    if not value:
        return ''
    return value.strftime(format)

def format_time(value: datetime, format: str = '%H:%M') -> str:
    """Format time for display."""
    if not value:
        return ''
    return value.strftime(format)

def time_ago(value: datetime) -> str:
    """Get human-readable time ago string."""
    if not value:
        return ''
    
    now = datetime.utcnow()
    diff = now - value
    
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

def truncate_text(value: str, length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    if not value:
        return ''
    
    if len(value) <= length:
        return value
    
    return value[:length - len(suffix)] + suffix

def format_number(value: int) -> str:
    """Format number with commas."""
    if not value:
        return '0'
    return f"{value:,}"

def format_file_size(value: int) -> str:
    """Format file size in human-readable format."""
    if not value:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while value >= 1024 and i < len(size_names) - 1:
        value /= 1024.0
        i += 1
    
    return f"{value:.1f} {size_names[i]}"

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

def clean_commit_message(value: str) -> str:
    """Clean commit message by removing common prefixes."""
    if not value:
        return ''
    
    # Remove common prefixes
    prefixes_to_remove = [
        'feat:', 'fix:', 'docs:', 'style:', 'refactor:', 'test:', 'chore:',
        'feature:', 'bugfix:', 'hotfix:', 'merge:', 'revert:'
    ]
    
    clean_message = value.strip()
    for prefix in prefixes_to_remove:
        if clean_message.lower().startswith(prefix):
            clean_message = clean_message[len(prefix):].strip()
            break
    
    # Remove extra whitespace
    clean_message = re.sub(r'\s+', ' ', clean_message)
    
    return clean_message

def extract_hashtags(value: str) -> list:
    """Extract hashtags from text."""
    if not value:
        return []
    
    hashtag_pattern = r'#\w+'
    hashtags = re.findall(hashtag_pattern, value)
    return list(set(hashtags))  # Remove duplicates

def extract_mentions(value: str) -> list:
    """Extract mentions from text."""
    if not value:
        return []
    
    mention_pattern = r'@\w+'
    mentions = re.findall(mention_pattern, value)
    return list(set(mentions))  # Remove duplicates

def status_badge_class(value: str) -> str:
    """Get Bootstrap badge class for status."""
    status_classes = {
        'published': 'bg-success',
        'scheduled': 'bg-warning',
        'draft': 'bg-secondary',
        'failed': 'bg-danger',
        'processing': 'bg-info'
    }
    return status_classes.get(value, 'bg-secondary')

def platform_icon(value: str) -> str:
    """Get Font Awesome icon for platform."""
    platform_icons = {
        'twitter': 'fab fa-twitter',
        'linkedin': 'fab fa-linkedin',
        'facebook': 'fab fa-facebook',
        'instagram': 'fab fa-instagram',
        'github': 'fab fa-github'
    }
    return platform_icons.get(value, 'fas fa-share-alt')

def platform_color(value: str) -> str:
    """Get color class for platform."""
    platform_colors = {
        'twitter': 'text-primary',
        'linkedin': 'text-info',
        'facebook': 'text-primary',
        'instagram': 'text-danger',
        'github': 'text-dark'
    }
    return platform_colors.get(value, 'text-secondary')

def format_duration(value: int) -> str:
    """Format duration in human-readable format."""
    if not value:
        return "0s"
    
    if value < 60:
        return f"{value}s"
    elif value < 3600:
        minutes = value // 60
        return f"{minutes}m {value % 60}s"
    elif value < 86400:
        hours = value // 3600
        minutes = (value % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = value // 86400
        hours = (value % 86400) // 3600
        return f"{days}d {hours}h"

def format_percentage(value: float, decimals: int = 1) -> str:
    """Format percentage with specified decimal places."""
    if value is None:
        return '0%'
    return f"{value:.{decimals}f}%"

def format_currency(value: float, currency: str = 'USD') -> str:
    """Format currency value."""
    if value is None:
        return f'$0.00'
    
    currency_symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'JPY': '¥'
    }
    
    symbol = currency_symbols.get(currency, '$')
    return f"{symbol}{value:,.2f}"

def mask_email(value: str) -> str:
    """Mask email address for privacy."""
    if not value or '@' not in value:
        return value
    
    local, domain = value.split('@', 1)
    if len(local) <= 2:
        masked_local = local[0] + '*'
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    
    return f"{masked_local}@{domain}"

def mask_username(value: str) -> str:
    """Mask username for privacy."""
    if not value:
        return value
    
    if len(value) <= 2:
        return value[0] + '*'
    else:
        return value[0] + '*' * (len(value) - 2) + value[-1]

def clean_html(value: str) -> str:
    """Remove HTML tags from text."""
    if not value:
        return ''
    
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', value)
    
    # Decode HTML entities
    import html
    clean = html.unescape(clean)
    
    return clean.strip()

def format_json(value: Any) -> str:
    """Format value as JSON string."""
    import json
    return json.dumps(value, indent=2, default=str)

def format_list(value: list, separator: str = ', ') -> str:
    """Format list as string with separator."""
    if not value:
        return ''
    return separator.join(str(item) for item in value)

def format_dict(value: dict, key_value_separator: str = ': ', item_separator: str = ', ') -> str:
    """Format dictionary as string."""
    if not value:
        return ''
    
    items = []
    for key, val in value.items():
        items.append(f"{key}{key_value_separator}{val}")
    
    return item_separator.join(items)

def capitalize_words(value: str) -> str:
    """Capitalize each word in string."""
    if not value:
        return ''
    return ' '.join(word.capitalize() for word in value.split())

def snake_case(value: str) -> str:
    """Convert string to snake_case."""
    if not value:
        return ''
    
    # Insert underscore before uppercase letters
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', value)
    # Insert underscore before uppercase letters that follow lowercase
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    
    return s2.lower()

def camel_case(value: str) -> str:
    """Convert string to camelCase."""
    if not value:
        return ''
    
    # Split by underscores and capitalize each word except the first
    words = value.split('_')
    if not words:
        return ''
    
    return words[0].lower() + ''.join(word.capitalize() for word in words[1:])

def pascal_case(value: str) -> str:
    """Convert string to PascalCase."""
    if not value:
        return ''
    
    # Split by underscores and capitalize each word
    words = value.split('_')
    return ''.join(word.capitalize() for word in words)

def pluralize(value: str, count: int) -> str:
    """Pluralize string based on count."""
    if not value:
        return ''
    
    if count == 1:
        return value
    else:
        # Simple pluralization rules
        if value.endswith('y'):
            return value[:-1] + 'ies'
        elif value.endswith(('s', 'sh', 'ch', 'x', 'z')):
            return value + 'es'
        else:
            return value + 's'

def ordinal(value: int) -> str:
    """Convert number to ordinal (1st, 2nd, 3rd, etc.)."""
    if not value:
        return '0th'
    
    if 10 <= value % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th')
    
    return f"{value}{suffix}"

def format_phone(value: str) -> str:
    """Format phone number."""
    if not value:
        return ''
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', value)
    
    # Format based on length
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return value

def format_ssn(value: str) -> str:
    """Format Social Security Number."""
    if not value:
        return ''
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', value)
    
    # Format as XXX-XX-XXXX
    if len(digits) == 9:
        return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
    else:
        return value
