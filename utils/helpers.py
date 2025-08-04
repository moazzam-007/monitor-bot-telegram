import re
import logging
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlunparse

logger = logging.getLogger(__name__)

def clean_url(url):
    """Clean and normalize URL"""
    try:
        # Remove extra spaces and characters
        url = url.strip()
        
        # Parse the URL
        parsed = urlparse(url)
        
        # Remove query parameters that might interfere
        # We'll keep only the path and remove the query and fragment
        cleaned = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            None,
            None,
            None
        ))
        
        return cleaned
        
    except Exception as e:
        logger.error(f"Error cleaning URL: {e}")
        return url

def extract_product_context(text, url):
    """Extract context around the product URL"""
    try:
        # Find text around the URL
        url_index = text.find(url)
        if url_index == -1:
            return text[:200]  # First 200 chars if URL not found in text
        
        # Extract 100 chars before and after URL
        start = max(0, url_index - 100)
        end = min(len(text), url_index + len(url) + 100)
        
        context = text[start:end]
        return context.strip()
        
    except Exception as e:
        logger.error(f"Error extracting context: {e}")
        return text[:200]

def log_processing_stats():
    """Log current processing statistics"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"📊 Monitor Bot Status - {current_time}")

def validate_channel_id(channel_id):
    """Validate if channel ID format is correct"""
    try:
        # Channel IDs should be negative integers
        channel_int = int(channel_id)
        return channel_int < 0
    except (ValueError, TypeError):
        return False

def extract_asin_from_url(url):
    """Extract ASIN from Amazon URL"""
    asin_pattern = r'/dp/([A-Z0-9]{10})'
    match = re.search(asin_pattern, url)
    return match.group(1) if match else None
