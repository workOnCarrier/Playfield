**Topic:** *Concurrent LRU Cache*
---

### 🎯 **Interview Problem**

> **Design and implement a thread-safe LRU (Least Recently Used) cache.**
> The cache should support concurrent `get(key)` and `put(key, value)` operations with the following guarantees:
>
> * **O(1)** average time complexity for both `get` and `put`.
> * Thread-safety under multiple readers/writers.
> * When capacity is exceeded, the least recently used entry should be evicted.

---

### 🗣️ **Simulated Interview**

**1. Interviewer:**
We’d like you to design a **concurrent LRU cache**. First, how would you design a single-threaded LRU cache?

**Interviewee:**
A classic LRU can be built using a combination of a **doubly-linked list** and a **hash map**.

* The hashmap maps keys to nodes in the list.
* The list maintains usage order, most recently used at the head, least at the tail.
  `get` moves accessed nodes to the head; `put` inserts at the head and removes from the tail when capacity is exceeded.

---

**2. Interviewer:**
Great. Now, if we have multiple threads accessing `get` and `put` concurrently, what issues might occur?

**Interviewee:**
Without synchronization, we might face:

* **Race conditions** on the linked list (two threads moving/removing nodes simultaneously).
* **Inconsistent map state** if one thread erases while another reads.
* **Evictions** might remove a node that another thread is currently moving.

---

**3. Interviewer:**
What’s your approach to make it thread-safe?

**Interviewee:**
Simplest way: use a **global mutex** around both `get` and `put`. But that limits concurrency heavily.
A more scalable approach:

* Use a **read–write lock** or finer-grained locks.
* Partition keys into buckets (sharding) each with its own LRU, then combine.

---

**4. Interviewer:**
Can you sketch the global-lock approach first?

**Interviewee:**
Sure.

```cpp
class LRUCache {
    std::mutex mtx;
    std::list<std::pair<int,int>> dll;
    std::unordered_map<int, std::list<std::pair<int,int>>::iterator> map;
    size_t capacity;
public:
    int get(int key) {
        std::lock_guard<std::mutex> lock(mtx);
        auto it = map.find(key);
        if(it == map.end()) return -1;
        dll.splice(dll.begin(), dll, it->second);
        return it->second->second;
    }
    void put(int key, int value) {
        std::lock_guard<std::mutex> lock(mtx);
        auto it = map.find(key);
        if(it != map.end()) {
            dll.erase(it->second);
        }
        dll.push_front({key,value});
        map[key] = dll.begin();
        if(map.size() > capacity) {
            auto last = dll.end(); --last;
            map.erase(last->first);
            dll.pop_back();
        }
    }
};
```

---

**5. Interviewer:**
Looks good. But as you said, a single global lock reduces throughput. How would you improve?

**Interviewee:**
We can use **segmented LRU**:

* Divide key space into N shards.
* Each shard has its own LRU (with its own lock).
* Hash the key to a shard.
  This allows multiple threads to operate on different shards concurrently.

---

**6. Interviewer:**
What’s the trade-off of a segmented LRU?

**Interviewee:**
Eviction is approximate — each shard evicts within itself, not truly global.
Also memory overhead increases (each shard keeps its own structures). But throughput improves significantly in high-concurrency scenarios.

---

**7. Interviewer:**
Suppose we stick to one shard. How would you handle a reader while a writer is evicting?

**Interviewee:**
With a `std::shared_mutex`:

* `get()` acquires a shared lock (many readers can proceed).
* `put()` acquires an exclusive lock (blocks others).
  This balances read-heavy workloads.

---

**8. Interviewer:**
If we use shared\_mutex, moving a node in the list during `get` also modifies state. Would shared lock be enough?

**Interviewee:**
Good catch! Even `get` modifies recency. So we’d need **exclusive lock for both** unless we separate metadata from data.
Alternatively, we can allow a relaxed design: don’t update recency on every get, or use lock-free queues, but that’s complex. Usually we accept `get` as a write-op for recency update.

---

**9. Interviewer:**
How would you test your implementation?

**Interviewee:**

* Unit tests for single-threaded correctness (insert, evict, get).
* Stress test with multiple threads calling random `get/put` operations and validating invariants:

  * Map size never exceeds capacity.
  * Evicted keys are never returned.
* Use tools like ThreadSanitizer or Helgrind to detect race conditions.

---

**10. Interviewer:**
If you were implementing this for a trading system with very high QPS, any further optimizations?

**Interviewee:**

* Consider **lock striping** (more shards).
* Use **concurrent hash maps** like Folly’s `ConcurrentHashMap`.
* Preallocate nodes to reduce malloc/free overhead.
* Use **hazard pointers** or RCU for advanced lock-free recency lists.
* Profile and tune eviction policies if workload patterns are skewed.

---

### 📌 **File 1: `ConcurrentLRUCache.h`**

```cpp
#ifndef CONCURRENT_LRU_CACHE_H
#define CONCURRENT_LRU_CACHE_H

#include <unordered_map>
#include <list>
#include <mutex>
#include <optional>

template<typename Key, typename Value>
class ConcurrentLRUCache {
public:
    explicit ConcurrentLRUCache(size_t capacity) : capacity_(capacity) {}

    // Non-copyable
    ConcurrentLRUCache(const ConcurrentLRUCache&) = delete;
    ConcurrentLRUCache& operator=(const ConcurrentLRUCache&) = delete;

    // Thread-safe get
    std::optional<Value> get(const Key& key) {
        std::lock_guard<std::mutex> lock(mtx_);
        auto it = map_.find(key);
        if (it == map_.end()) {
            return std::nullopt;
        }
        // Move accessed item to front
        lru_.splice(lru_.begin(), lru_, it->second);
        return it->second->second;
    }

    // Thread-safe put
    void put(const Key& key, const Value& value) {
        std::lock_guard<std::mutex> lock(mtx_);
        auto it = map_.find(key);
        if (it != map_.end()) {
            // Update existing
            it->second->second = value;
            lru_.splice(lru_.begin(), lru_, it->second);
            return;
        }
        // Insert new
        lru_.emplace_front(key, value);
        map_[key] = lru_.begin();

        if (map_.size() > capacity_) {
            // Remove least recently used
            auto last = lru_.end();
            --last;
            map_.erase(last->first);
            lru_.pop_back();
        }
    }

    size_t size() const {
        std::lock_guard<std::mutex> lock(mtx_);
        return map_.size();
    }

private:
    mutable std::mutex mtx_;
    size_t capacity_;
    std::list<std::pair<Key, Value>> lru_;
    std::unordered_map<Key, typename std::list<std::pair<Key, Value>>::iterator> map_;
};

#endif // CONCURRENT_LRU_CACHE_H
```

---

### 📌 **File 2: `test_concurrent_lru.cpp`**

Compile with `g++ -std=c++17 -pthread test_concurrent_lru.cpp -o test_lru`

```cpp
#include <iostream>
#include <thread>
#include <vector>
#include "ConcurrentLRUCache.h"

void basicTest() {
    ConcurrentLRUCache<int, std::string> cache(3);
    cache.put(1, "one");
    cache.put(2, "two");
    cache.put(3, "three");

    // Access some keys
    auto v = cache.get(1);
    if (v) std::cout << "Key 1 = " << *v << "\n";

    cache.put(4, "four"); // should evict key 2 (least recently used)

    std::cout << "Size after put: " << cache.size() << "\n";
    auto v2 = cache.get(2);
    std::cout << "Key 2 present? " << (v2.has_value() ? "yes" : "no") << "\n";
}

void concurrentTest() {
    ConcurrentLRUCache<int, int> cache(100);

    auto writer = [&cache]() {
        for (int i = 0; i < 1000; ++i) {
            cache.put(i % 200, i);
        }
    };
    auto reader = [&cache]() {
        for (int i = 0; i < 1000; ++i) {
            cache.get(i % 200);
        }
    };

    std::thread t1(writer);
    std::thread t2(reader);
    std::thread t3(writer);
    std::thread t4(reader);

    t1.join();
    t2.join();
    t3.join();
    t4.join();

    std::cout << "Concurrent test size: " << cache.size() << "\n";
}

int main() {
    std::cout << "=== Basic Test ===\n";
    basicTest();
    std::cout << "\n=== Concurrent Test ===\n";
    concurrentTest();
    return 0;
}
```

---

### ✅ **How to run**

```bash
g++ -std=c++17 -pthread test_concurrent_lru.cpp -o test_lru
./test_lru
```

**Expected output (approx):**

```
=== Basic Test ===
Key 1 = one
Size after put: 3
Key 2 present? no

=== Concurrent Test ===
Concurrent test size: 100
```

---

### 🔧 **Notes**

✅ Thread-safety guaranteed by global `std::mutex`
✅ Easy to extend to `shared_mutex` or segmented design
✅ Unit test demonstrates both basic correctness and concurrency stress.

---

---

### Multiple Choice Questions

1. **What is the primary purpose of an LRU (Least Recently Used) cache?**  
   a) To store the most frequently used items indefinitely  
   b) To evict the least recently accessed items when the cache reaches capacity  
   c) To ensure all items are accessed in a round-robin fashion  
   d) To prioritize items with the highest value in the cache  

2. **Which data structure combination is most commonly used to achieve O(1) time complexity for both get and put operations in a single-threaded LRU cache?**  
   a) Binary search tree and array  
   b) Hash map and doubly-linked list  
   c) Priority queue and hash map  
   d) Array and singly-linked list  

3. **What is a major challenge when making an LRU cache thread-safe?**  
   a) Ensuring O(n) time complexity for operations  
   b) Preventing race conditions during concurrent get and put operations  
   c) Avoiding memory leaks in single-threaded access  
   d) Maintaining a sorted order of keys in the cache  

4. **What is the simplest way to ensure thread-safety in a concurrent LRU cache?**  
   a) Use a global mutex to lock all operations  
   b) Implement lock-free data structures for all operations  
   c) Use a read-write lock for all get operations  
   d) Avoid synchronization entirely by using atomic operations  

5. **What is a key trade-off of using a global mutex in a concurrent LRU cache?**  
   a) Increased memory usage due to multiple locks  
   b) Reduced throughput due to serialized access  
   c) Higher risk of deadlocks in read-heavy workloads  
   d) Inability to evict items when capacity is exceeded  

6. **In a segmented LRU cache, how does dividing the cache into shards improve performance?**  
   a) It eliminates the need for any synchronization mechanism  
   b) It allows concurrent operations on different shards  
   c) It guarantees global LRU eviction across all shards  
   d) It reduces the memory footprint of the cache  

7. **What is a potential downside of a segmented LRU cache compared to a single LRU cache?**  
   a) It requires O(n) time complexity for get operations  
   b) Eviction is approximate and not globally least-recently-used  
   c) It cannot support concurrent access to the cache  
   d) It uses less memory due to fewer data structures  

8. **When using a read-write lock (std::shared_mutex) in a concurrent LRU cache, why might a shared lock for get operations be insufficient?**  
   a) get operations do not access the cache’s internal state  
   b) get operations modify the recency order, requiring an exclusive lock  
   c) Shared locks always cause deadlocks in concurrent systems  
   d) get operations cannot run concurrently with put operations  

9. **Which testing strategy is most effective for validating the thread-safety of a concurrent LRU cache?**  
   a) Running single-threaded unit tests to verify cache size  
   b) Using stress tests with multiple threads and tools like ThreadSanitizer  
   c) Checking only the eviction policy in isolation  
   d) Simulating cache operations without synchronization  

10. **For a high-QPS trading system, which optimization would likely improve the performance of a concurrent LRU cache?**  
    a) Using a single global lock for all operations  
    b) Implementing lock striping with multiple shards  
    c) Disabling eviction to reduce overhead  
    d) Storing all keys in a sorted array  

---
Great job providing your answers! Below, I'll give feedback on each of your choices, explaining whether they are correct and providing reasoning to clarify the concepts. I'll keep it concise but thorough to ensure you understand the rationale behind each answer.

---

### Feedback on Your Answers

**1. What is the primary purpose of an LRU (Least Recently Used) cache?**  
**Your Answer**: b) To evict the least recently accessed items when the cache reaches capacity  
**Feedback**: **Correct!** The primary purpose of an LRU cache is to maintain a fixed-size cache by evicting the least recently used items when the capacity is exceeded. This ensures that the most recently accessed items remain available, optimizing for temporal locality.  

---

**2. Which data structure combination is most commonly used to achieve O(1) time complexity for both get and put operations in a single-threaded LRU cache?**  
**Your Answer**: b) Hash map and doubly-linked list  
**Feedback**: **Correct!** A hash map provides O(1) lookup for keys, while a doubly-linked list allows O(1) updates for moving nodes (to track recency) and removing the least recently used item. This combination ensures both get and put operations are O(1) on average.  

---

**3. What is a major challenge when making an LRU cache thread-safe?**  
**Your Answer**: b) Preventing race conditions during concurrent get and put operations  
**Feedback**: **Correct!** Concurrent access to the cache’s data structures (hash map and linked list) can lead to race conditions, such as multiple threads modifying the same node or accessing inconsistent states, which is a primary challenge in ensuring thread-safety.  

---

**4. What is the simplest way to ensure thread-safety in a concurrent LRU cache?**  
**Your Answer**: a) Use a global mutex to lock all operations  
**Feedback**: **Correct!** A global mutex serializes all get and put operations, preventing race conditions by ensuring only one thread accesses the cache at a time. While simple, it may reduce concurrency, but it’s the most straightforward approach.  

---

**5. What is a key trade-off of using a global mutex in a concurrent LRU cache?**  
**Your Answer**: b) Reduced throughput due to serialized access  
**Feedback**: **Correct!** A global mutex forces all operations to wait for the lock, serializing access and reducing throughput, especially in high-concurrency scenarios where multiple threads could otherwise operate simultaneously.  

---

**6. In a segmented LRU cache, how does dividing the cache into shards improve performance?**  
**Your Answer**: b) It allows concurrent operations on different shards  
**Feedback**: **Correct!** By dividing the cache into shards, each with its own lock, threads can access different shards concurrently, improving throughput compared to a single global lock. This reduces contention and enhances scalability.  

---

**7. What is a potential downside of a segmented LRU cache compared to a single LRU cache?**  
**Your Answer**: b) Eviction is approximate and not globally least-recently-used  
**Feedback**: **Correct!** In a segmented LRU cache, each shard manages its own LRU list, so evictions occur locally within a shard. This means the evicted item may not be the globally least recently used, leading to approximate LRU behavior.  

---

**8. When using a read-write lock (std::shared_mutex) in a concurrent LRU cache, why might a shared lock for get operations be insufficient?**  
**Your Answer**: d) get operations cannot run concurrently with put operations  
**Feedback**: **Incorrect.** The correct answer is **b) get operations modify the recency order, requiring an exclusive lock**. In an LRU cache, a get operation updates the recency order by moving the accessed item to the front of the list, which modifies the cache’s state. A shared lock allows multiple readers but doesn’t protect against concurrent modifications, so an exclusive lock is needed for get operations to avoid race conditions when updating the list. Option d is incorrect because get and put operations *can* run concurrently with proper locking (e.g., shared locks for reads and exclusive locks for writes), but the issue here is the modification caused by get.  

---

**9. Which testing strategy is most effective for validating the thread-safety of a concurrent LRU cache?**  
**Your Answer**: b) Using stress tests with multiple threads and tools like ThreadSanitizer  
**Feedback**: **Correct!** Stress testing with multiple threads simulates real-world concurrency, and tools like ThreadSanitizer or Helgrind can detect race conditions or other threading issues, making this the most effective way to validate thread-safety.  

---

**10. For a high-QPS trading system, which optimization would likely improve the performance of a concurrent LRU cache?**  
**Your Answer**: b) Implementing lock striping with multiple shards  
**Feedback**: **Correct!** Lock striping (using multiple shards with separate locks) reduces contention by allowing concurrent access to different parts of the cache, significantly improving performance in high-QPS (queries per second) systems like trading platforms.  

---

### Summary
**Score**: 9/10  
You did an excellent job, getting 9 out of 10 questions correct! Your understanding of LRU cache design, thread-safety mechanisms, and their trade-offs is strong. The only misstep was on question 8, where the key insight is that get operations in an LRU cache modify the recency order, requiring an exclusive lock even with a read-write lock. This is a subtle but important detail in concurrent LRU cache design.  

If you’d like further clarification on question 8 or any other topic, or if you want additional practice questions, let me know!