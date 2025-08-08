# file: services/duplicate_detector.py
import hashlib
from datetime import datetime, timedelta

class DuplicateDetector:
    def __init__(self, time_window_hours=48):
        self.processed_hashes = {} # Format: {hash: datetime}
        self.time_window = timedelta(hours=time_window_hours)

    def is_duplicate(self, unique_id):
        current_time = datetime.now()
        
        if unique_id in self.processed_hashes:
            processed_time = self.processed_hashes[unique_id]
            if (current_time - processed_time) < self.time_window:
                return True
        
        # Isay abhi process mark nahi karenge, woh main logic mein hoga
        return False

    def mark_as_processed(self, unique_id):
        """Ek ID ko processed mark karne ke liye naya function."""
        self.processed_hashes[unique_id] = datetime.now()
