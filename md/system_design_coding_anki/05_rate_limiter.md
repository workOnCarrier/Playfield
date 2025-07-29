##  What is a Rate Limiter and where is it used?
* A rate limiter used to control rate of the requests from client or service
* limits amount of traffic per time period.
* Example - 2 posts per user per day
* Example - Create 5 accounts from an ip address.

## What is the use of rate limiter ?
* Denial of Service
* Provide resource key API by reducing
* Client side rate limiter helps with preventing unexpected cost by using paid services.

## What is the expectation of rate limiter?
* Accurately limit excessive requests.
* Low latency - should not slowdown HTTP requests.
* Use less resource like memory and cpu cycle.
* Distributed rate limitor, used accross multiple systems.
* Exception handling - show exact error for the clients.

## What are the different algorithms used in Rate limiter?
* Token bucket
* Leaky bucket
* Fixed Window counter
* Sliding window log
* Sliding window counter.

## Python program for Token buckets
[Understanding Rate Limiting with Token Bucket Algorithm (Medium)](https://medium.com/@mdfirozmia321/understanding-rate-limiting-with-token-bucket-algorithm-a-practical-implementation-in-go-3c44719d7dd2)

```
python
import time
import threading

class TokenBucket:
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity  # max tokens in the bucket
        self.tokens = capacity    # current tokens in the bucket
        self.refill_rate = refill_rate  # tokens per second
        self.last_checked = time.time()
        self.lock = threading.Lock()

    def _refill(self):
        now = time.time()
        elapsed = now - self.last_checked
        added_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + added_tokens)
        self.last_checked = now

    def allow_request(self):
        with self.lock:
            self._refill()
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            else:
                return False

# --- Simulating requests ---
def simulate_requests(bucket, total_requests, interval):
    for i in range(total_requests):
        allowed = bucket.allow_request()
        print(f"Request {i+1}: {'Allowed' if allowed else 'Rate Limited'} | Tokens left: {bucket.tokens:.2f}")
        time.sleep(interval)

# --- Example usage ---
if __name__ == "__main__":
    bucket = TokenBucket(capacity=5, refill_rate=1)  # 5 max tokens, 1 token added per second
    simulate_requests(bucket, total_requests=10, interval=0.5)
```

## python program for leaky bucket

```
import threading
import time
import random

class LeakyBucketRateLimiter:
    def __init__(self, capacity, leak_rate_per_second):
        self.capacity = capacity                # Maximum bucket size
        self.leak_rate = leak_rate_per_second   # Leak rate (requests/second)
        self.current_water = 0                  # Current water level (number of requests)
        self.lock = threading.Lock()

        # Start a background thread to leak requests
        leak_thread = threading.Thread(target=self._leak, daemon=True)
        leak_thread.start()

    def _leak(self):
        while True:
            time.sleep(1 / self.leak_rate)
            with self.lock:
                if self.current_water > 0:
                    self.current_water -= 1
                    print(f"Leaked 1 request. Remaining in bucket: {self.current_water}")

    def allow_request(self):
        with self.lock:
            if self.current_water < self.capacity:
                self.current_water += 1
                print(f"Accepted request. Bucket: {self.current_water}/{self.capacity}")
                return True
            else:
                print(f"Rejected request. Bucket is full: {self.current_water}/{self.capacity}")
                return False

# Simulating random incoming requests
def simulate_requests(rate_limiter):
    while True:
        time.sleep(random.uniform(0.1, 0.5))  # Random interval between requests
        rate_limiter.allow_request()

if __name__ == "__main__":
    limiter = LeakyBucketRateLimiter(capacity=5, leak_rate_per_second=1)
    simulate_thread = threading.Thread(target=simulate_requests, args=(limiter,))
    simulate_thread.start()

    # Let it run for 15 seconds
    time.sleep(15)
```
