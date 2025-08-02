import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def clean_url(url):
    """Clean and normalize URL"""
    # Remove extra spaces and characters
    url = url.strip()
    
    # Remove query parameters that might interfere
    unwanted_params = ['ref_', 'tag', 'psc', 'qid']
    
    # Basic cleaning for logging/comparison
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
