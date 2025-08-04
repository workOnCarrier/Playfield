from tdigest import TDigest
from collections import deque
import time
import random

class SlidingWindowTDigest:
    def __init__(self, window_secs=60, interval_secs=1):
        self.window_secs = window_secs
        self.interval_secs = interval_secs
        self.num_slots = window_secs // interval_secs

        # Ring buffer of (timestamp, t-digest)
        self.buffer = deque(maxlen=self.num_slots)
        self.current_digest = TDigest()
        self.last_flush_time = int(time.time())

    def _flush(self):
        now = int(time.time())
        if now == self.last_flush_time:
            return
        # If time has advanced, finalize this slot and start a new digest
        for _ in range(now - self.last_flush_time):
            self.buffer.append((self.last_flush_time, self.current_digest))
            self.current_digest = TDigest()
            self.last_flush_time += 1

    def add(self, latency_us):
        self._flush()
        self.current_digest.update(latency_us)

    def percentile(self, p):
        self._flush()
        # Merge digests in the current window
        merged = TDigest()
        for _, d in self.buffer:
            merged = TDigest.merge(merged, d)
        merged = TDigest.merge(merged, self.current_digest)
        if merged.n == 0:
            return 0.0
        return merged.percentile(p)

    def stats(self):
        return {
            "p50": self.percentile(50),
            "p90": self.percentile(90),
            "p99": self.percentile(99)
        }

if __name__ == "__main__":
    analyzer = SlidingWindowTDigest(window_secs=60, interval_secs=1)

    # Simulate 2 minutes of data (random latencies between 50us and 2000us)
    start = time.time()
    for step in range(120):
        for _ in range(1000):  # simulate 1000 latencies/sec
            latency = random.randint(50, 2000)
            analyzer.add(latency)

        if step % 5 == 0:  # print stats every 5 seconds
            stats = analyzer.stats()
            print(f"[t={step}s] p50={stats['p50']:.2f}us, "
                f"p90={stats['p90']:.2f}us, "
                f"p99={stats['p99']:.2f}us")

        time.sleep(1.0)  # simulate real-time
