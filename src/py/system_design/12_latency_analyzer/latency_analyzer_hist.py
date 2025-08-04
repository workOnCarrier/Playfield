import threading
import math

class LatencyAnalyzer:
    def __init__(self, bucket_size_ms=1, max_latency_ms=1000):
        self.bucket_width = bucket_size_ms
        self.num_buckets = math.ceil(max_latency_ms / bucket_size_ms)
        self.buckets = [0] * self.num_buckets
        self.total_samples = 0
        self.lock = threading.Lock()

    def record(self, latency_ms):
        with self.lock:
            bucket = min(int(latency_ms // self.bucket_width), self.num_buckets - 1)
            self.buckets[bucket] += 1
            self.total_samples += 1

    def get_percentile(self, percentile):
        if not 0 <= percentile <= 100:
            raise ValueError("Percentile must be between 0 and 100")
        with self.lock:
            if self.total_samples == 0:
                return None
            target = self.total_samples * (percentile / 100)
            print(f" aiming for values till we hit the count of samples:{target} vs total:{self.total_samples}")
            count = 0
            for i, bucket_count in enumerate(self.buckets):
                count += bucket_count
                if count >= target:
                    # Linear interpolation within bucket
                    lower_bound = i * self.bucket_width
                    if count == bucket_count:
                        return lower_bound
                    fraction = (target - (count - bucket_count)) / bucket_count
                    return lower_bound + fraction * self.bucket_width
            return self.num_buckets * self.bucket_width

    def reset(self):
        with self.lock:
            snapshot = self.buckets.copy()
            self.buckets = [0] * self.num_buckets
            self.total_samples = 0
        return snapshot

# Example usage
if __name__ == "__main__":
    analyzer = LatencyAnalyzer(bucket_size_ms=10, max_latency_ms=100)
    # Simulate latency samples
    import random
    import time

    def worker(analyzer, num_samples):
        for _ in range(num_samples):
            latency = random.uniform(0, 101)
            analyzer.record(latency)
            time.sleep(0.001)

    threads = [threading.Thread(target=worker, args=(analyzer, 1000)) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    p99 = analyzer.get_percentile(50)
    print(f"p99 latency: {p99:.2f} ms")
    snapshot = analyzer.reset()
    # print(f"Snapshot buckets (first 10): {snapshot[:10]}")
    print(f"Snapshot buckets (first 10): {snapshot}")
