from datetime import datetime
from flask import current_app
from babel.dates import format_datetime

def datetimeformat(value, format='medium'):
    """Format a datetime object using Babel's format_datetime."""
    if value is None:
        return ""
    return format_datetime(value, format=format, locale='en')

def time_ago(timestamp):
    """Format a datetime object as a relative time string."""
    now = datetime.utcnow()
    diff = now - timestamp
    
    seconds = diff.total_seconds()
    minutes = int(seconds // 60)
    hours = int(minutes // 60)
    days = diff.days
    
    if days > 7:
        return timestamp.strftime('%b %d, %Y')
    elif days > 0:
        return f"{days} day{'s' if days > 1 else ''} ago"
    elif hours > 0:
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif minutes > 0:
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"
