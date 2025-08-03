import hashlib
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DuplicateDetector:
    def __init__(self, time_window_hours=24):
        self.processed_urls = {}  # In-memory dictionary
        self.time_window = timedelta(hours=time_window_hours)
        self.last_cleanup = datetime.now()
    
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
        # Use a simple URL cleaner to make sure a, b, c in query params don't change hash
        # e.g., https://amzn.to/abc?tag=123 -> https://amzn.to/abc
        clean_url = url.split('?')[0].split('#')[0]
        return hashlib.md5(clean_url.encode()).hexdigest()

    def is_duplicate(self, url):
        """Checks if a URL has been processed recently."""
        self._cleanup_old_entries()
        url_hash = self._generate_url_hash(url)
        
        if url_hash in self.processed_urls:
            logger.info(f"🔄 DUPLICATE URL found: {url[:50]}...")
            return True
        
        self.processed_urls[url_hash] = datetime.now()
        logger.info(f"✅ NEW URL marked as processed: {url[:50]}...")
        return False
