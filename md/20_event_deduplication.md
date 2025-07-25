**Topic:** 🚦 **Logic + Bitwise – Event Deduplicator in Time Window**
**Target companies:** Robinhood, Stripe, Two Sigma, Goldman Sachs, Bloomberg
**Setting:** A live coding/whiteboard interview.
**Goal:** The candidate must design and implement an event deduplication system that efficiently deduplicates event IDs arriving in a stream, considering a rolling time window, while using logic & bitwise operations for memory efficiency.

---

#### 👩‍💻 **Interviewer (I)**

#### 👨‍💻 **Interviewee (E)**

---

**1️⃣ I:**
Imagine we’re ingesting billions of events per hour. Each event has a 64‑bit integer `eventID` and a timestamp in milliseconds. We want to deduplicate events in a **sliding 10‑second window**. Memory is tight, so we can’t just keep a giant hash set of all IDs.
How would you approach this problem?

**E:**
I would first define what deduplication means: for each new event, we should check if an identical `eventID` has appeared in the last 10,000ms. If yes, we discard it; otherwise, we mark it as seen.
Given memory constraints, I’d use a **bitset-like structure** combined with a time‑bucketed ring buffer, instead of a massive hash set.

---

**2️⃣ I:**
Interesting. But a naive bitset for 64-bit IDs is too huge. How can we reduce memory?

**E:**
We can hash the `eventID` to a smaller space, say `N` bits. This gives a probabilistic structure like a **Bloom filter** or a custom rotating bitmap. For example, we can use a 1‑million‑bit bitmap, where each bit position corresponds to `hash(eventID) % N`.

---

**3️⃣ I:**
Won’t hashing introduce false positives?

**E:**
Yes, but in practice we can tolerate a very low false positive rate if we size the bitmap properly. Alternatively, we could use two different hash functions and two bitmaps to reduce false positives.

---

**4️⃣ I:**
Now, how do you handle the sliding 10-second window?

**E:**
I’d partition time into, say, 100 buckets (each bucket = 100ms). For each bucket, maintain its own bitmap. When a new event arrives:

1. Compute `bucketIndex = (timestamp / 100ms) % 100`.
2. Check its bit in that bucket’s bitmap.
3. If not set, set it.
4. When time advances and we reuse an old bucket, we clear its bitmap before reusing.

---

**5️⃣ I:**
Sounds good. But clearing bitmaps might be expensive. Any tricks?

**E:**
Instead of physically clearing, we can store a **generation counter** per bucket. Each bucket stores a `currentEpoch`. When checking a bit, we also check if its stored epoch matches the bucket’s epoch. If not, we treat it as zero without clearing. This avoids expensive bulk clears.

---

**6️⃣ I:**
Nice. Let’s focus on **bitwise operations** now. How exactly do you set and test a bit?

**E:**
Suppose we have a `std::vector<uint64_t>` as a bitmap, size `Nbits`.

* To set:

```cpp
uint64_t idx = hash(eventID) % Nbits;
bitmap[idx >> 6] |= (1ULL << (idx & 63));
```

* To test:

```cpp
bool seen = bitmap[idx >> 6] & (1ULL << (idx & 63));
```

---

**7️⃣ I:**
How would you incorporate the per-bucket structure into this?

**E:**
We’d make `bitmap` a 2D array: `bitmap[bucketCount][Nbits/64]`.
Index by `bucketIndex` first, then use the same bitwise set/test.
When moving to a new epoch, we either clear or reset that bucket’s metadata.

---

**8️⃣ I:**
What if two events with the same hash arrive in different buckets within 10 seconds?

**E:**
Each bucket is independent. So, we must check **all active buckets in the window** for the bit. Alternatively, we keep a single rolling structure and rely on timestamps to expire.
But to optimize, we could maintain a **queue of bucket indices** representing the active window and probe only those.

---

**9️⃣ I:**
Let’s consider concurrency: this runs on multiple threads. How would you handle synchronization?

**E:**
For high throughput, I’d use **atomic bitwise operations** (`std::atomic<uint64_t>` with `fetch_or`) to set bits. For per-bucket metadata, we can use double-buffering or lock-free structures. Each bucket update is independent, so contention is low.

---

**🔟 I:**
Great! Final question: what’s the time and space complexity?

**E:**

* **Time:** O(1) per event for hashing and bit manipulation, plus O(windowBucketCount) if we check multiple buckets.
* **Space:** O(bucketCount × Nbits) bits. With 100 buckets and 1 million bits per bucket, that’s \~12.5MB.
  We trade off some false positives for significant memory savings.

---

If you’d like, I can now:
✅ Provide a **C++ reference implementation** with a test file.
✅ Or extend this into a **realistic coding challenge**.

---

**Event Deduplicator in a Sliding Time Window** with bitwise logic.

### 📄 **EventDeduplicator.cpp**

```cpp
#include <bits/stdc++.h>
#include <atomic>
#include <shared_mutex>
#include <chrono>

class EventDeduplicator {
public:
    // total bits in each bitmap
    static constexpr size_t BITMAP_BITS = 1 << 20; // ~1M bits
    static constexpr size_t WORDS = BITMAP_BITS / 64;
    // window parameters
    static constexpr size_t BUCKET_COUNT = 100; // 100 buckets
    static constexpr uint64_t BUCKET_WIDTH_MS = 100; // each covers 100 ms
    static constexpr uint64_t WINDOW_MS = BUCKET_COUNT * BUCKET_WIDTH_MS;

    EventDeduplicator() {
        for (size_t b = 0; b < BUCKET_COUNT; ++b) {
            epoch[b].store(0, std::memory_order_relaxed);
            for (size_t w = 0; w < WORDS; ++w) {
                bitmaps[b][w].store(0ULL, std::memory_order_relaxed);
            }
        }
    }

    bool shouldProcess(uint64_t eventID, uint64_t timestampMs) {
        // Determine target bucket
        uint64_t bucketIndex = (timestampMs / BUCKET_WIDTH_MS) % BUCKET_COUNT;
        uint64_t bucketEpoch = timestampMs / BUCKET_WIDTH_MS;

        // Check bucket epoch and reset if stale
        uint64_t currentEpoch = epoch[bucketIndex].load(std::memory_order_acquire);
        if (currentEpoch != bucketEpoch) {
            // Reset this bucket
            resetBucket(bucketIndex, bucketEpoch);
        }

        // Hash eventID into bitmap index
        uint64_t idx = cheapHash(eventID) % BITMAP_BITS;
        uint64_t wordIndex = idx >> 6;
        uint64_t bitMask = (1ULL << (idx & 63));

        // Check & set atomically
        uint64_t oldVal = bitmaps[bucketIndex][wordIndex].fetch_or(bitMask, std::memory_order_acq_rel);
        bool seenInThisBucket = (oldVal & bitMask) != 0ULL;
        if (seenInThisBucket) {
            // already seen in this bucket (within same 100ms chunk)
            return false;
        }

        // else, might still be duplicate in other buckets within window
        // we must check the rest of the buckets in the window
        for (size_t i = 0; i < BUCKET_COUNT; ++i) {
            if (i == bucketIndex) continue;
            uint64_t otherEpoch = epoch[i].load(std::memory_order_acquire);
            // skip buckets outside window
            if ((bucketEpoch > otherEpoch) && (bucketEpoch - otherEpoch) * BUCKET_WIDTH_MS > WINDOW_MS)
                continue;
            if ((otherEpoch > bucketEpoch) && (otherEpoch - bucketEpoch) * BUCKET_WIDTH_MS > WINDOW_MS)
                continue;

            uint64_t wordVal = bitmaps[i][wordIndex].load(std::memory_order_acquire);
            if (wordVal & bitMask) {
                // found in another active bucket
                return false;
            }
        }

        // not seen anywhere in active window
        return true;
    }

private:
    // Bitmap: bucketCount x WORDS of atomic 64-bit
    std::array<std::array<std::atomic<uint64_t>, WORDS>, BUCKET_COUNT> bitmaps;
    std::array<std::atomic<uint64_t>, BUCKET_COUNT> epoch; // generation counter per bucket
    std::shared_mutex resetMutex[BUCKET_COUNT]; // to guard resets

    static inline uint64_t cheapHash(uint64_t x) {
        // A simple 64-bit mix hash
        x ^= x >> 33;
        x *= 0xff51afd7ed558ccdULL;
        x ^= x >> 33;
        x *= 0xc4ceb9fe1a85ec53ULL;
        x ^= x >> 33;
        return x;
    }

    void resetBucket(size_t bucketIndex, uint64_t newEpoch) {
        std::unique_lock lock(resetMutex[bucketIndex]);
        // Double check epoch after locking
        uint64_t curEpoch = epoch[bucketIndex].load(std::memory_order_acquire);
        if (curEpoch == newEpoch) return;
        for (size_t w = 0; w < WORDS; ++w) {
            bitmaps[bucketIndex][w].store(0ULL, std::memory_order_release);
        }
        epoch[bucketIndex].store(newEpoch, std::memory_order_release);
    }
};
```

---

### 📄 **test\_EventDeduplicator.cpp**

```cpp
#include "EventDeduplicator.cpp"
#include <iostream>
#include <thread>
#include <vector>
#include <chrono>

int main() {
    EventDeduplicator dedup;

    uint64_t now = 1000000; // ms
    uint64_t id1 = 42;
    uint64_t id2 = 99;

    // First time seeing id1
    bool p1 = dedup.shouldProcess(id1, now);
    std::cout << "Event id1 first time: " << (p1 ? "process" : "duplicate") << "\n";

    // Duplicate within same window
    bool p2 = dedup.shouldProcess(id1, now + 50);
    std::cout << "Event id1 again within window: " << (p2 ? "process" : "duplicate") << "\n";

    // Different id, should process
    bool p3 = dedup.shouldProcess(id2, now + 70);
    std::cout << "Event id2 first time: " << (p3 ? "process" : "duplicate") << "\n";

    // Same id1 but after 11 seconds (outside window)
    bool p4 = dedup.shouldProcess(id1, now + 11000);
    std::cout << "Event id1 after window: " << (p4 ? "process" : "duplicate") << "\n";

    // Some random testing for collisions
    for (int i = 0; i < 5; ++i) {
        uint64_t eid = id1 + i * 123456789ULL;
        bool p = dedup.shouldProcess(eid, now + i * 10);
        std::cout << "Event " << eid << ": " << (p ? "process" : "duplicate") << "\n";
    }

    return 0;
}
```

---

### 💡 **Build & Run**

```bash
g++ -std=c++17 -O2 EventDeduplicator.cpp test_EventDeduplicator.cpp -o test_dedup
./test_dedup
```

---

### ✅ **Output Example**

```
Event id1 first time: process
Event id1 again within window: duplicate
Event id2 first time: process
Event id1 after window: process
Event 42: duplicate
Event 123456831: process
Event 246913620: process
Event 370370409: process
Event 493827198: process
```

---

If you’d like, I can also:

* Add unit tests with `gtest` or `Catch2`,
* Benchmark with synthetic load,
* Or show a **lock-free** variant.

---

### Multiple-Choice Questions

**Question 1: Bitwise Operations**  
What is the primary benefit of using bitwise operations in a deduplication system?  
a) They allow for faster arithmetic computations.  
b) They reduce memory usage by representing data compactly.  
c) They simplify thread synchronization.  
d) They eliminate the need for hash functions.  

**Question 2: Bloom Filter Concept**  
A Bloom filter is suggested for deduplication. What is a key characteristic of a Bloom filter?  
a) It guarantees no false positives.  
b) It uses a single hash function to map elements.  
c) It may return false positives but never false negatives.  
d) It requires O(n) space, where n is the number of elements stored.  

**Question 3: Sliding Time Window**  
In a sliding time window of 10 seconds, why is partitioning time into buckets (e.g., 100ms each) useful?  
a) It eliminates the need for timestamp comparisons.  
b) It reduces the number of bits checked per event.  
c) It allows for efficient expiration of old events.  
d) It ensures no false positives occur.  

**Question 4: Memory Efficiency**  
Why is a bitmap preferred over a hash set for deduplication in a memory-constrained environment?  
a) Bitmaps are faster for lookups.  
b) Bitmaps use significantly less memory per event.  
c) Bitmaps support concurrent access without locks.  
d) Bitmaps eliminate the need for hashing.  

**Question 5: False Positives in Hashing**  
When hashing event IDs to a smaller bitmap, what can be done to reduce false positives?  
a) Increase the number of hash functions and bitmaps.  
b) Use a single, highly complex hash function.  
c) Store the full event ID in the bitmap.  
d) Decrease the size of the bitmap.  

**Question 6: Epoch-Based Bucket Reset**  
Using a generation counter (epoch) per bucket avoids physically clearing bitmaps. What is the main advantage of this approach?  
a) It reduces memory allocation overhead.  
b) It eliminates the need for atomic operations.  
c) It avoids costly bulk memory operations.  
d) It ensures thread safety without locks.  

**Question 7: Atomic Operations**  
Why are atomic bitwise operations (e.g., fetch_or) used in a multi-threaded deduplication system?  
a) They ensure thread-safe updates without locks.  
b) They reduce memory usage compared to regular bitwise operations.  
c) They guarantee no false positives.  
d) They simplify timestamp management.  

**Question 8: Time Complexity**  
What is the time complexity of checking for an event’s presence in a single bucket using a bitmap?  
a) O(1)  
b) O(log n)  
c) O(n)  
d) O(bucketCount)  

**Question 9: Space Complexity**  
For a deduplication system with 100 buckets and a 1-million-bit bitmap per bucket, what is the approximate space usage?  
a) ~1 MB  
b) ~12.5 MB  
c) ~100 MB  
d) ~1 GB  

**Question 10: Concurrency Optimization**  
In a multi-threaded deduplication system, why is per-bucket independence beneficial?  
a) It eliminates the need for hash functions.  
b) It reduces contention by allowing parallel updates to different buckets.  
c) It guarantees no false positives across threads.  
d) It simplifies the sliding window logic.  

---
### Evaluation of Your Answers

**Question 1: Bitwise Operations**  
**What is the primary benefit of using bitwise operations in a deduplication system?**  
- **Your answer**: b) They reduce memory usage by representing data compactly.  
- **Correct answer**: b) They reduce memory usage by representing data compactly.  
- **Explanation**: Bitwise operations allow efficient storage (e.g., using a single bit per hashed event ID in a bitmap), significantly reducing memory compared to storing full IDs or using a hash set.  
- **Result**: Correct ✅

**Question 2: Bloom Filter Concept**  
**A Bloom filter is suggested for deduplication. What is a key characteristic of a Bloom filter?**  
- **Your answer**: b) It uses a single hash function to map elements.  
- **Correct answer**: c) It may return false positives but never false negatives.  
- **Explanation**: A Bloom filter uses multiple hash functions to set/test bits in a bitmap, allowing compact storage but introducing a chance of false positives (indicating an event exists when it doesn’t). It never produces false negatives (if an event is present, it will always be detected). Your choice of b) is incorrect because Bloom filters typically use multiple hash functions, not a single one.  
- **Result**: Incorrect ❌

**Question 3: Sliding Time Window**  
**In a sliding time window of 10 seconds, why is partitioning time into buckets (e.g., 100ms each) useful?**  
- **Your answer**: c) It allows for efficient expiration of old events.  
- **Correct answer**: c) It allows for efficient expiration of old events.  
- **Explanation**: Partitioning time into buckets (e.g., 100ms) enables the system to manage the sliding window by clearing or reusing buckets as they fall outside the 10-second window, efficiently expiring old events.  
- **Result**: Correct ✅

**Question 4: Memory Efficiency**  
**Why is a bitmap preferred over a hash set for deduplication in a memory-constrained environment?**  
- **Your answer**: b) Bitmaps use significantly less memory per event.  
- **Correct answer**: b) Bitmaps use significantly less memory per event.  
- **Explanation**: A bitmap uses one bit per hashed event ID, whereas a hash set stores full keys and metadata, consuming much more memory. This makes bitmaps ideal for memory-constrained environments.  
- **Result**: Correct ✅

**Question 5: False Positives in Hashing**  
**When hashing event IDs to a smaller bitmap, what can be done to reduce false positives?**  
- **Your answer**: a) Increase the number of hash functions and bitmaps.  
- **Correct answer**: a) Increase the number of hash functions and bitmaps.  
- **Explanation**: Using multiple hash functions (as in a Bloom filter) and larger or multiple bitmaps reduces the likelihood of collisions, lowering the false positive rate.  
- **Result**: Correct ✅

**Question 6: Epoch-Based Bucket Reset**  
**Using a generation counter (epoch) per bucket avoids physically clearing bitmaps. What is the main advantage of this approach?**  
- **Your answer**: c) It avoids costly bulk memory operations.  
- **Correct answer**: c) It avoids costly bulk memory operations.  
- **Explanation**: By tracking an epoch per bucket, the system can logically invalidate a bucket’s contents without physically clearing the bitmap, avoiding expensive memory operations.  
- **Result**: Correct ✅

**Question 7: Atomic Operations**  
**Why are atomic bitwise operations (e.g., fetch_or) used in a multi-threaded deduplication system?**  
- **Your answer**: b) They reduce memory usage compared to regular bitwise operations.  
- **Correct answer**: a) They ensure thread-safe updates without locks.  
- **Explanation**: Atomic operations like `fetch_or` allow thread-safe updates to the bitmap without requiring locks, ensuring correctness in a multi-threaded environment. They don’t reduce memory usage compared to regular bitwise operations (both operate on the same data).  
- **Result**: Incorrect ❌

**Question 8: Time Complexity**  
**What is the time complexity of checking for an event’s presence in a single bucket using a bitmap?**  
- **Your answer**: a) O(1)  
- **Correct answer**: a) O(1)  
- **Explanation**: Checking a bit in a bitmap involves hashing the event ID (O(1)), calculating the bit index (O(1)), and performing a single bitwise operation (O(1)), resulting in constant-time complexity.  
- **Result**: Correct ✅

**Question 9: Space Complexity**  
**For a deduplication system with 100 buckets and a 1-million-bit bitmap per bucket, what is the approximate space usage?**  
- **Your answer**: b) ~12.5 MB  
- **Correct answer**: b) ~12.5 MB  
- **Explanation**: Each bucket has a 1-million-bit bitmap = 1,000,000 bits. With 100 buckets: 100 × 1,000,000 bits = 100,000,000 bits. Since 8 bits = 1 byte, this is 100,000,000 / 8 = 12,500,000 bytes ≈ 12.5 MB.  
- **Result**: Correct ✅

**Question 10: Concurrency Optimization**  
**In a multi-threaded deduplication system, why is per-bucket independence beneficial?**  
- **Your answer**: b) It reduces contention by allowing parallel updates to different buckets.  
- **Correct answer**: b) It reduces contention by allowing parallel updates to different buckets.  
- **Explanation**: Independent buckets allow different threads to update different buckets concurrently without contention, improving performance in a multi-threaded system.  
- **Result**: Correct ✅

---

### Summary  
- **Correct**: 8/10 (Questions 1, 3, 4, 5, 6, 8, 9, 10)  
- **Incorrect**: 2/10 (Questions 2, 7)  
- **Score**: 80%  

### Feedback  
- **Question 2**: Bloom filters rely on multiple hash functions, and their key feature is allowing false positives but not false negatives. This is critical for understanding probabilistic data structures.  
- **Question 7**: Atomic operations are about thread safety, not memory reduction. This is a subtle but important distinction in concurrent programming.  

