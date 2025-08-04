import threading
import hashlib
import time
from collections import deque

class EventDeduplicator:
    def __init__(self, window_seconds=60):
        self.window_seconds = window_seconds
        self.signatures = deque()  # (timestamp, signature) pairs
        self.signature_set = set()  # For O(1) lookup
        self.lock = threading.Lock()

    def _generate_signature(self, event):
        # Hash relevant event fields (e.g., symbol, price, timestamp)
        event_str = f"{event.get('symbol', '')}:{event.get('price', '')}:{event.get('timestamp', '')}"
        return hashlib.sha256(event_str.encode()).hexdigest()

    def is_duplicate(self, event):
        with self.lock:
            current_time = time.time()
            signature = self._generate_signature(event)
            
            # Remove expired signatures
            while self.signatures and current_time - self.signatures[0][0] > self.window_seconds:
                _, old_signature = self.signatures.popleft()
                self.signature_set.discard(old_signature)
            
            # Check for duplicate
            if signature in self.signature_set:
                return True
            
            # Add new signature
            self.signatures.append((current_time, signature))
            self.signature_set.add(signature)
            return False

# Example usage
if __name__ == "__main__":
    deduplicator = EventDeduplicator(window_seconds=1)
    event1 = {"symbol": "AAPL", "price": 150.0, "timestamp": 1000}
    event2 = {"symbol": "AAPL", "price": 150.0, "timestamp": 1000}
    event3 = {"symbol": "GOOG", "price": 2800.0, "timestamp": 1001}

    print(deduplicator.is_duplicate(event1))  # False
    print(deduplicator.is_duplicate(event2))  # True (duplicate)
    print(deduplicator.is_duplicate(event3))  # False
    time.sleep(1.5)  # Wait for window to expire
    print(deduplicator.is_duplicate(event1))  # False (window expired)

