import threading
import bisect
from typing import Optional, Tuple
from collections import namedtuple

Point = namedtuple('Point', ['timestamp', 'value'])

class TimeSeriesStore:
    def __init__(self):
        self._active = []  # Writer's buffer
        self._frozen = []  # Reader's snapshot
        self._lock = threading.Lock()
        self._last_timestamp = -float('inf')

    def insert(self, timestamp: int, value: float) -> None:
        """Insert a (timestamp, value) pair, optimized for mostly monotonic timestamps."""
        with self._lock:
            if timestamp >= self._last_timestamp:
                self._active.append(Point(timestamp, value))
                self._last_timestamp = timestamp
            else:
                # Out-of-order: insert into active list at correct position
                bisect.insort(self._active, Point(timestamp, value))
            # Periodically swap buffers to update readers
            if len(self._active) > 1000:  # Arbitrary threshold for swapping
                self._frozen = self._active
                self._active = self._frozen[:]
                self._active.clear()

    def get_latest_before_or_equal(self, timestamp: int) -> Optional[Point]:
        """Get the latest point before or equal to the given timestamp."""
        # Read from frozen snapshot, no lock needed
        if not self._frozen:
            return None
        idx = bisect.bisect_right([p.timestamp for p in self._frozen], timestamp)
        if idx == 0:
            return None
        return self._frozen[idx - 1]

    def get_range(self, start: int, end: int) -> List[Point]:
        """Get all points with timestamps in [start, end] (inclusive), including active buffer up to end."""
        with self._lock:
            if not self._frozen and not self._active:
                return []
            # Get points from frozen in [start, end]
            frozen_timestamps = [p.timestamp for p in self._frozen]
            frozen_start_idx = bisect.bisect_left(frozen_timestamps, start)
            frozen_end_idx = bisect.bisect_right(frozen_timestamps, end)
            result = self._frozen[frozen_start_idx:frozen_end_idx]
            # Get points from active up to end
            active_timestamps = [p.timestamp for p in self._active]
            active_start_idx = bisect.bisect_left(active_timestamps, start)
            active_end_idx = bisect.bisect_right(active_timestamps, end)
            result.extend(self._active[active_start_idx:active_end_idx])
            # Sort to ensure order (in case active points overlap with frozen)
            return sorted(result, key=lambda p: p.timestamp)

    def expire_before(self, cutoff: int) -> None:
        """Remove all points with timestamp < cutoff."""
        with self._lock:
            # Update both active and frozen buffers
            self._active = [p for p in self._active if p.timestamp >= cutoff]
            self._frozen = [p for p in self._frozen if p.timestamp >= cutoff]
            self._last_timestamp = min((p.timestamp for p in self._active), default=-float('inf'))

    def size(self) -> int:
        """Return the number of points in the frozen buffer."""
        return len(self._frozen)

# Example usage and test
if __name__ == "__main__":
    store = TimeSeriesStore()
    
    # Insert points
    store.insert(1000, 10.5)
    store.insert(2000, 11.0)
    store.insert(1500, 10.8)  # Out-of-order
    store.insert(3000, 12.0)
    
    # Query
    point = store.get_latest_before_or_equal(1600)
    print(f"Latest <= 1600: {point}")  # Should print Point(timestamp=1500, value=10.8)
    
    # Expire old data
    store.expire_before(1500)
    print(f"Size after expiry: {store.size()}")
    
    # Concurrent test (basic)
    def writer():
        for i in range(100):
            store.insert(4000 + i, 20.0 + i)
    
    def reader():
        for _ in range(100):
            point = store.get_latest_before_or_equal(5000)
            if point:
                print(f"Reader got: {point}")
    
    import threading
    writer_thread = threading.Thread(target=writer)
    reader_thread = threading.Thread(target=reader)
    writer_thread.start()
    reader_thread.start()
    writer_thread.join()
    reader_thread.join()