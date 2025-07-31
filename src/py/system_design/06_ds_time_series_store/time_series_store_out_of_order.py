
import threading
import bisect
from sortedcontainers import SortedDict

class TimeSeriesStore:
    def __init__(self):
        self.points = []  # List of (timestamp, value) tuples
        self.buffer = SortedDict()  # Buffer for out-of-order inserts
        self.lock = threading.Lock()

    def insert(self, timestamp, value):
        with self.lock:
            if not self.points or timestamp >= self.points[-1][0]:
                self.points.append((timestamp, value))
            else:
                self.buffer[timestamp] = value
                if len(self.buffer) > 100:
                    self._merge_buffer()
    def _merge_buffer(self):
        for ts, value in self.buffer.items():
            index = bisect.bisect_left([p[0] for p in self.points], ts)
            self.points.insert(index, (ts, value))
        self.buffer.clear()

    def get_latest_before_or_equal(self, timestamp):
        with self.lock:
            self._merge_buffer()
            if not self.points:
                return None
            index = bisect.bisect_right([p[0] for p in self.points], timestamp) - 1
            if index < 0:
                return None
            return self.points[index]

    def expire_before(self, cutoff):
        with self.lock:
            index = bisect.bisect_left([p[0] for p in self.points], cutoff)
            self.points = self.points[index:]

    def size(self):
        with self.lock:
            return len(self.points)

if __name__ == "__main__":
    store = TimeSeriesStore()
    store.insert(1000, 10.5)
    store.insert(2000, 11.0)
    store.insert(1500, 10.8)  # Out-of-order

    result = store.get_latest_before_or_equal(1600)
    print(f"Latest <= 1600: ts={result[0]}, value={result[1]}") if result else print("None")

    store.expire_before(1500)
    print(f"Size after expiry: {store.size()}")
    

