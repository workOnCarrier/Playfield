### 🎯 **Interview Problem:**

> **Design and implement a thread-safe Rate Limiter that allows at most `N` requests per `T` milliseconds.**
> Discuss trade‑offs, concurrency control, and how to handle high contention.

---

### 💬 **Simulation – 10 Interactions**

**Interviewer (Q1):**
Suppose our trading gateway must not process more than 100 requests per second from any single client. How would you design a **rate limiter** for this?

**Interviewee (A1):**
I’d start with a **token bucket** or **leaky bucket** algorithm. For example, a token bucket refills tokens at a constant rate (100 per second), and each incoming request consumes one token. If no tokens are available, the request is rejected or delayed. This naturally enforces the rate.

---

**Interviewer (Q2):**
Good. How would you implement that in a **multithreaded environment** where multiple threads may call `allowRequest()` concurrently?

**Interviewee (A2):**
I’d protect the shared state (current token count and last refill timestamp) with a **mutex** or an atomic compare‑and‑swap loop. Each `allowRequest()` would lock, recalculate available tokens, update state, and return. Alternatively, I could use lock‑free techniques with atomics and time calculations.

---

**Interviewer (Q3):**
Let’s say you use a mutex. Isn’t that a potential bottleneck under high load?

**Interviewee (A3):**
Yes, a single global mutex can serialize all requests. To reduce contention, we can:

* Use **sharding**: each client has its own bucket and lock.
* Or use **Read‑Write locks** if many reads and fewer writes.
* Or implement a **lock-free token update** with atomics and double‑checked logic.

---

**Interviewer (Q4):**
Imagine this bucket needs to reset tokens every second. How do you handle that without spawning a dedicated timer thread?

**Interviewee (A4):**
I’d handle it lazily: every time `allowRequest()` is called, I compute the elapsed time since the last update, calculate how many tokens to add (based on refill rate), and update the state before checking tokens. No timer thread needed.

---

**Interviewer (Q5):**
How do you ensure **thread safety** for that lazy refill logic?

**Interviewee (A5):**
When doing lazy refill, I wrap the “read timestamp, compute new tokens, update state” sequence in a critical section (mutex lock or atomic CAS) so that only one thread updates the refill at a time. Others will see the updated state after.

---

**Interviewer (Q6):**
Suppose we need a **non-blocking** solution. Any ideas?

**Interviewee (A6):**
I could use an **atomic variable** for tokens and a **timestamp**. In a loop, each thread would:

* Read current tokens and time.
* Compute expected new token count.
* Use `compare_exchange_weak` to update state.
* If CAS fails, retry.
  This avoids a blocking lock but is trickier to get right.

---

**Interviewer (Q7):**
What about **fairness**? Suppose many threads are waiting—how do you ensure no thread starves?

**Interviewee (A7):**
A token bucket doesn’t inherently guarantee fairness; fast threads may grab tokens first. To improve fairness, we could:

* Queue requests (like a semaphore with FIFO).
* Or use a **blocking bounded queue** behind the limiter so requests are served in arrival order.

---

**Interviewer (Q8):**
If you had to implement this in C++ for production, what libraries or primitives would you use?

**Interviewee (A8):**
I’d use `std::mutex` and `std::chrono` for a first version. For higher performance, consider `std::atomic` for token count and `std::steady_clock` for timestamps. I might also wrap the logic in a reusable class `RateLimiter`.

---

**Interviewer (Q9):**
Let’s say the rate changes dynamically (e.g., 100 req/s → 500 req/s). How would you handle that without stopping the system?

**Interviewee (A9):**
I’d store `maxTokens` and `refillRate` in atomics so they can be updated safely at runtime. On each `allowRequest()`, use the current atomic values to compute refill and capacity.

---

**Interviewer (Q10):**
Finally, what tests would you run to ensure your implementation works under concurrency?

**Interviewee (A10):**
I’d write:

* **Unit tests** for single-thread correctness (edge cases like full bucket, empty bucket).
* **Stress tests** with many threads calling `allowRequest()` concurrently to ensure no more than N requests are allowed.
* **Latency tests** to verify minimal overhead.
* **Dynamic config tests** for rate changes at runtime.

---


### 📄 **rate\_limiter.h**

```cpp
#pragma once
#include <chrono>
#include <mutex>

class RateLimiter {
public:
    RateLimiter(size_t maxTokens, std::chrono::milliseconds refillInterval)
        : maxTokens_(maxTokens),
          refillInterval_(refillInterval),
          availableTokens_(maxTokens),
          lastRefillTime_(std::chrono::steady_clock::now()) {}

    // Returns true if request is allowed, false if rate limited
    bool allowRequest() {
        using Clock = std::chrono::steady_clock;
        std::lock_guard<std::mutex> lock(mutex_);

        auto now = Clock::now();
        refillTokens(now);

        if (availableTokens_ > 0) {
            --availableTokens_;
            return true;
        }
        return false;
    }

private:
    void refillTokens(std::chrono::steady_clock::time_point now) {
        auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(now - lastRefillTime_);
        if (elapsed >= refillInterval_) {
            size_t tokensToAdd = (elapsed.count() / refillInterval_.count()) * maxTokens_;
            availableTokens_ = std::min(maxTokens_, availableTokens_ + tokensToAdd);
            // Advance lastRefillTime_ by multiples of interval
            lastRefillTime_ += std::chrono::milliseconds((elapsed.count() / refillInterval_.count()) * refillInterval_.count());
        }
    }

    const size_t maxTokens_;
    const std::chrono::milliseconds refillInterval_;

    size_t availableTokens_;
    std::chrono::steady_clock::time_point lastRefillTime_;
    std::mutex mutex_;
};
```

---

### 📄 **main.cpp** (Test cases)

```cpp
#include "rate_limiter.h"
#include <iostream>
#include <thread>
#include <vector>
#include <atomic>

void singleThreadTest() {
    std::cout << "[Single Thread Test]\n";
    RateLimiter rl(5, std::chrono::milliseconds(1000)); // 5 requests per second
    for (int i = 0; i < 7; ++i) {
        bool allowed = rl.allowRequest();
        std::cout << "Request " << i << " -> " << (allowed ? "ALLOWED" : "BLOCKED") << "\n";
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(1100));
    std::cout << "After refill...\n";
    for (int i = 0; i < 3; ++i) {
        bool allowed = rl.allowRequest();
        std::cout << "Request " << i << " -> " << (allowed ? "ALLOWED" : "BLOCKED") << "\n";
    }
}

void multiThreadTest() {
    std::cout << "\n[Multi Thread Stress Test]\n";
    RateLimiter rl(10, std::chrono::milliseconds(1000)); // 10 requests per second
    std::atomic<int> allowedCount{0};
    const int numThreads = 20;
    std::vector<std::thread> threads;

    for (int i = 0; i < numThreads; ++i) {
        threads.emplace_back([&]() {
            if (rl.allowRequest()) {
                allowedCount.fetch_add(1);
            }
        });
    }

    for (auto &t : threads) t.join();

    std::cout << "Allowed count = " << allowedCount.load() << " (should be ≤ 10)\n";
}

int main() {
    singleThreadTest();
    multiThreadTest();
    return 0;
}
```

---

### ✅ **Build & Run**

```bash
g++ -std=c++17 -O2 -pthread main.cpp -o rate_limiter_test
./rate_limiter_test
```

---

### ✅ **Sample Output**

```
[Single Thread Test]
Request 0 -> ALLOWED
Request 1 -> ALLOWED
Request 2 -> ALLOWED
Request 3 -> ALLOWED
Request 4 -> ALLOWED
Request 5 -> BLOCKED
Request 6 -> BLOCKED
After refill...
Request 0 -> ALLOWED
Request 1 -> ALLOWED
Request 2 -> ALLOWED

[Multi Thread Stress Test]
Allowed count = 10 (should be ≤ 10)
```

---

can also provide:
✅ A lock‑free version with atomics,
✅ Or a gtest‑based unit test file.

----


### Multiple-Choice Questions

**Q1: What is the primary purpose of a Rate Limiter in a system like a trading gateway?**  
a) To ensure all requests are processed immediately  
b) To limit the number of requests processed within a time window  
c) To prioritize certain clients over others  
d) To encrypt requests for security  

**Q2: Which algorithm is commonly used for implementing a Rate Limiter, as mentioned in the context?**  
a) Round-robin scheduling  
b) Token bucket or leaky bucket  
c) First-come, first-served queue  
d) Priority queue  

**Q3: In a multithreaded environment, how can you protect shared state (e.g., token count) in a Rate Limiter?**  
a) Use a global variable without synchronization  
b) Use a mutex or atomic operations  
c) Avoid sharing state entirely  
d) Use a database to store the state  

**Q4: Why might a single global mutex in a Rate Limiter cause performance issues under high load?**  
a) It increases memory usage  
b) It serializes all requests, creating a bottleneck  
c) It prevents token refills  
d) It causes thread starvation  

**Q5: What is a key benefit of using a lazy refill strategy in the Rate Limiter, as described in the context?**  
a) It eliminates the need for thread synchronization  
b) It avoids the need for a dedicated timer thread  
c) It guarantees fairness among threads  
d) It reduces the number of tokens needed  

**Q6: Which C++ standard library component is suitable for ensuring thread safety in the provided Rate Limiter implementation?**  
a) std::vector  
b) std::mutex  
c) std::shared_ptr  
d) std::chrono::duration  

**Q7: In a non-blocking Rate Limiter implementation, what technique can replace a mutex to avoid contention?**  
a) Using a single-threaded event loop  
b) Using compare-and-swap with atomic variables  
c) Using a priority queue  
d) Using a sleep function  

**Q8: How can fairness be improved in a Rate Limiter when multiple threads compete for tokens?**  
a) Use a FIFO queue for requests  
b) Increase the token refill rate  
c) Disable thread synchronization  
d) Use a random token allocation strategy  

**Q9: In the context, how does the Rate Limiter handle dynamic changes to the rate (e.g., from 100 req/s to 500 req/s)?**  
a) By restarting the system with new parameters  
b) By using atomic variables for maxTokens and refillRate  
c) By pausing all threads temporarily  
d) By ignoring the new rate until the next refill  

**Q10: Which type of test is recommended to verify the Rate Limiter’s correctness under high concurrency?**  
a) A single-threaded latency test  
b) A stress test with many concurrent threads  
c) A memory usage test  
d) A test that disables thread synchronization  

---

### Review of Your Answers

**Q1: What is the primary purpose of a Rate Limiter in a system like a trading gateway?**  
- **Your Answer**: b) To limit the number of requests processed within a time window  
- **Correct Answer**: b  
- **Feedback**: Correct! A Rate Limiter’s primary role is to restrict the number of requests within a given time frame, as seen in the context (e.g., 100 requests per second).

**Q2: Which algorithm is commonly used for implementing a Rate Limiter, as mentioned in the context?**  
- **Your Answer**: b) Token bucket or leaky bucket  
- **Correct Answer**: b  
- **Feedback**: Spot on! The context explicitly mentions the token bucket and leaky bucket algorithms as suitable choices for implementing a Rate Limiter.

**Q3: In a multithreaded environment, how can you protect shared state (e.g., token count) in a Rate Limiter?**  
- **Your Answer**: b) Use a mutex or atomic operations  
- **Correct Answer**: b  
- **Feedback**: Correct! The context describes using a mutex or atomic operations (e.g., compare-and-swap) to protect shared state like token count and timestamps.

**Q4: Why might a single global mutex in a Rate Limiter cause performance issues under high load?**  
- **Your Answer**: b) It serializes all requests, creating a bottleneck  
- **Correct Answer**: b  
- **Feedback**: Exactly right! The context notes that a global mutex can serialize requests, causing contention and performance bottlenecks under high load.

**Q5: What is a key benefit of using a lazy refill strategy in the Rate Limiter, as described in the context?**  
- **Your Answer**: c) It guarantees fairness among threads  
- **Correct Answer**: b) It avoids the need for a dedicated timer thread  
- **Feedback**: Incorrect. The context explains that lazy refill recalculates tokens on each `allowRequest()` call, eliminating the need for a timer thread (A4). Fairness (option c) is not guaranteed by lazy refill, as discussed in A7, where additional mechanisms like FIFO queues are suggested for fairness.

**Q6: Which C++ standard library component is suitable for ensuring thread safety in the provided Rate Limiter implementation?**  
- **Your Answer**: b) std::mutex  
- **Correct Answer**: b  
- **Feedback**: Correct! The provided C++ implementation uses `std::mutex` to ensure thread safety, as seen in the `rate_limiter.h` code.

**Q7: In a non-blocking Rate Limiter implementation, what technique can replace a mutex to avoid contention?**  
- **Your Answer**: b) Using compare-and-swap with atomic variables  
- **Correct Answer**: b  
- **Feedback**: Well done! The context (A6) suggests using atomic variables with compare-and-swap (e.g., `compare_exchange_weak`) for a non-blocking implementation.

**Q8: How can fairness be improved in a Rate Limiter when multiple threads compete for tokens?**  
- **Your Answer**: a) Use a FIFO queue for requests  
- **Correct Answer**: a  
- **Feedback**: Correct! The context (A7) mentions using a FIFO queue or a blocking bounded queue to ensure requests are processed in arrival order, improving fairness.

**Q9: In the context, how does the Rate Limiter handle dynamic changes to the rate (e.g., from 100 req/s to 500 req/s)?**  
- **Your Answer**: b) By using atomic variables for maxTokens and refillRate  
- **Correct Answer**: b  
- **Feedback**: Right on! The context (A9) explains that atomic variables for `maxTokens` and `refillRate` allow safe runtime updates to the rate.

**Q10: Which type of test is recommended to verify the Rate Limiter’s correctness under high concurrency?**  
- **Your Answer**: b) A stress test with many concurrent threads  
- **Correct Answer**: b  
- **Feedback**: Perfect! The context (A10) recommends stress tests with many threads to ensure the Rate Limiter allows no more than the allowed number of requests under concurrency.

---

