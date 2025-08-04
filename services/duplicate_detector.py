import hashlib
from datetime import datetime, timedelta
import logging
from utils.helpers import clean_url

logger = logging.getLogger(__name__)

class DuplicateDetector:
    def __init__(self, time_window_hours=24):
        self.processed_urls = {}  # In-memory dictionary
        self.time_window = timedelta(hours=time_window_hours)
        self.last_cleanup = datetime.now()
        self.stats = {
            'total_checked': 0,
            'duplicates_found': 0,
            'new_urls': 0
        }
    
    def _cleanup_old_entries(self):
        """Removes old entries from memory to save space."""
        current_time = datetime.now()
        if current_time - self.last_cleanup > self.time_window:
            old_entries = [
                url_hash for url_hash, timestamp in self.processed_urls.items() 
                if current_time - timestamp > self.time_window
            ]
            for url_hash in old_entries:
                del self.processed_urls[url_hash]
            self.last_cleanup = current_time
            logger.info(f"🧹 Cleaned up {len(old_entries)} old entries. {len(self.processed_urls)} left.")
    
    def _generate_url_hash(self, url):
        """Generates a consistent hash for a given URL."""
        # Clean the URL before hashing
        clean_url_str = clean_url(url)
        return hashlib.md5(clean_url_str.encode()).hexdigest()
    
    def is_duplicate(self, url):
        """Checks if a URL has been processed recently."""
        self._cleanup_old_entries()
        self.stats['total_checked'] += 1
        
        url_hash = self._generate_url_hash(url)
        
        if url_hash in self.processed_urls:
            self.stats['duplicates_found'] += 1
            logger.info(f"🔄 DUPLICATE URL found: {url[:50]}...")
            return True
        
        self.processed_urls[url_hash] = datetime.now()
        self.stats['new_urls'] += 1
        logger.info(f"✅ NEW URL marked as processed: {url[:50]}...")
        
        # Log stats every 100 URLs
        if self.stats['total_checked'] % 100 == 0:
            logger.info(f"📊 Duplicate Detection Stats: {self.stats}")
            
        return False
    
    def get_stats(self):
        """Get current statistics"""
        return self.stats.copy()
