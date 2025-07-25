
### **Interview Problem: Sliding Window Aggregator**

#### **Scenario:**

> You're tasked with designing a component for a **high-frequency time-series data pipeline**. This component must efficiently compute aggregates (sum, average, min, max, etc.) over a **moving/sliding time window**, like “last 5 minutes” or “last 1000 events”.

---


#### **1. Interviewer:**

Let's start simple. Suppose you're receiving a stream of `(timestamp, value)` pairs. How would you design a system that computes the **sum of values in the last T seconds**, given that timestamps are strictly increasing?

---

#### **2. Interviewee:**

I'd use a double-ended queue (deque) to store the pairs in the order they arrive. For each new entry, I’d evict old elements from the front whose timestamp is outside the `current_timestamp - T`. I'd also maintain a running sum as elements are added/removed for efficient O(1) access.

---

#### **3. Interviewer:**

What would the time and space complexity be per operation?

---

#### **4. Interviewee:**

* **Time complexity**: amortized O(1) per insert/remove.
* **Space complexity**: O(N), where N is the number of elements within the time window T.

---

#### **5. Interviewer:**

Great. Now, let’s say you also want to support **max()** over the sliding window. How would you implement that efficiently?

---

#### **6. Interviewee:**

I’d maintain a second deque for the max values. For each new element, I’d:

* Remove elements from the back of the deque that are less than the current value.
* Add the new value to the back.
* Evict the front element if it's outside the time window.

The max at any time is at the front of this deque.

---

#### **7. Interviewer:**

That’s clever. Let’s make it more realistic. Suppose the stream is arriving concurrently from multiple producers. How would you make this thread-safe?

---

#### **8. Interviewee:**

I’d wrap the entire structure in a mutex or use a `std::shared_mutex` if reads vastly outnumber writes. Alternatively, I can shard the time window by hash of timestamps or thread ID and then aggregate shard results periodically, depending on contention.

---

#### **9. Interviewer:**

Good. Now say we want to switch from time-based to **count-based windowing**, i.e., compute sum/max over the last **K events**. How would you adapt your design?

---

#### **10. Interviewee:**

Instead of using timestamps for eviction, I’d only maintain the last K events in the deque. I’d push new values to the back and pop from the front when size exceeds K. The logic for maintaining running sum or max remains similar, but eviction is based on size, not time.

---

### ✅ Real Constraints Observed:

* O(1) aggregation
* Memory bounded to recent window
* Support for sum/max
* Concurrency
* Time-window vs count-window logic

---

### 📌 **File 1: `SlidingWindowAggregator.h` (and .cpp combined for simplicity)**

```cpp
// SlidingWindowAggregator.h
#pragma once
#include <deque>
#include <mutex>
#include <chrono>

struct DataPoint {
    long long timestampMs; // epoch millis
    long long value;
};

class SlidingWindowAggregator {
public:
    explicit SlidingWindowAggregator(long long windowSizeMs)
        : windowSizeMs_(windowSizeMs), runningSum_(0) {}

    // Thread-safe add
    void add(long long timestampMs, long long value) {
        std::lock_guard<std::mutex> lock(mtx_);

        DataPoint p{timestampMs, value};
        dq_.push_back(p);
        runningSum_ += value;

        // maintain maxDeque
        while (!maxDeque_.empty() && maxDeque_.back().value <= value) {
            maxDeque_.pop_back();
        }
        maxDeque_.push_back(p);

        // evict old points
        evictOld(timestampMs);
    }

    long long getSum(long long currentTimestampMs) {
        std::lock_guard<std::mutex> lock(mtx_);
        evictOld(currentTimestampMs);
        return runningSum_;
    }

    long long getMax(long long currentTimestampMs) {
        std::lock_guard<std::mutex> lock(mtx_);
        evictOld(currentTimestampMs);
        if (maxDeque_.empty()) return 0;
        return maxDeque_.front().value;
    }

private:
    void evictOld(long long nowMs) {
        while (!dq_.empty() && dq_.front().timestampMs <= nowMs - windowSizeMs_) {
            // remove from sum
            runningSum_ -= dq_.front().value;
            // remove from dq
            if (!maxDeque_.empty() && maxDeque_.front().timestampMs == dq_.front().timestampMs) {
                maxDeque_.pop_front();
            }
            dq_.pop_front();
        }
    }

    long long windowSizeMs_;
    std::deque<DataPoint> dq_;
    std::deque<DataPoint> maxDeque_;
    long long runningSum_;
    std::mutex mtx_;
};
```

---

### 📌 **File 2: `test_sliding_window.cpp`**

```cpp
#include "SlidingWindowAggregator.h"
#include <iostream>
#include <cassert>

int main() {
    SlidingWindowAggregator agg(5000); // 5 second window

    // Simulated timestamps in ms
    agg.add(1000, 5);  // t=1s
    agg.add(2000, 7);  // t=2s
    agg.add(3000, 3);  // t=3s

    // At t=4000
    assert(agg.getSum(4000) == 15);
    assert(agg.getMax(4000) == 7);

    // Add more, some old will be evicted later
    agg.add(7000, 10); // t=7s (evicts t=1s,2s)
    // Now valid window is [2000ms, 7000ms] but 2000,3000 are older than 2000ms behind 7000
    // Actually window is 7000-5000=2000 => include >=2000ms
    assert(agg.getSum(7000) == 3 + 10); // 3(from 3s) + 10(from 7s) = 13
    assert(agg.getMax(7000) == 10);

    agg.add(8000, 6); // t=8s
    assert(agg.getSum(8000) == 10 + 6); // evicts 3 (t=3s)
    assert(agg.getMax(8000) == 10);

    agg.add(13000, 2); // t=13s
    // evicts everything older than 8000ms (13000-5000=8000)
    assert(agg.getSum(13000) == 2);
    assert(agg.getMax(13000) == 2);

    std::cout << "All test cases passed!\n";
    return 0;
}
```

---

### ✅ **How to Build & Run**

**CMakeLists.txt**

```cmake
cmake_minimum_required(VERSION 3.10)
project(SlidingWindowAggregator)

set(CMAKE_CXX_STANDARD 17)

add_executable(test_sliding_window
    test_sliding_window.cpp
)
```

```bash
mkdir build && cd build
cmake ..
make
./test_sliding_window
```

Output:

```
All test cases passed!
```

---

### can also extend this to:

* support **count-based windows**,
* or add more **thread-safety or benchmarking**.

----


### **Multiple-Choice Questions**

**Question 1: Sliding Window Concept**  
What is the primary purpose of a sliding window in a data stream processing system?  
a) To store all historical data for analysis  
b) To compute aggregates over a fixed-size subset of recent data  
c) To sort incoming data by timestamp  
d) To compress the data stream for storage  

---

**Question 2: Data Structure Choice**  
Which data structure is most suitable for implementing a time-based sliding window that supports efficient insertion and eviction of old elements?  
a) ArrayList  
b) Double-ended queue (deque)  
c) Binary Search Tree  
d) Hash Map  

---

**Question 3: Time Complexity**  
When using a deque to maintain a sliding window with a running sum, what is the amortized time complexity for adding a new element and evicting old ones?  
a) O(1)  
b) O(log n)  
c) O(n)  
d) O(n log n)  

---

**Question 4: Maximum in Sliding Window**  
To efficiently compute the maximum value in a sliding window, what property must the auxiliary deque maintain?  
a) Elements are sorted in ascending order  
b) Elements are stored in descending order with valid timestamps  
c) Elements are stored in random order  
d) Elements are stored with their frequency counts  

---

**Question 5: Concurrency**  
What is a common strategy to make a sliding window aggregator thread-safe when multiple producers add data concurrently?  
a) Use a single global variable for all operations  
b) Wrap operations with a mutex lock  
c) Disable interrupts during updates  
d) Store data in a non-thread-safe queue  

---

**Question 6: Count-Based vs. Time-Based Window**  
How does a count-based sliding window differ from a time-based sliding window?  
a) Count-based windows evict based on timestamps, while time-based windows evict based on size  
b) Count-based windows maintain a fixed number of elements, while time-based windows use a time duration  
c) Count-based windows always use more memory than time-based windows  
d) Count-based windows require a sorted data structure, unlike time-based windows  

---

**Question 7: Space Complexity**  
What is the space complexity of a sliding window aggregator that stores elements in a deque for a time window of T seconds, where N is the number of elements in the window?  
a) O(1)  
b) O(log N)  
c) O(N)  
d) O(N log N)  

---

**Question 8: Eviction Logic**  
In a time-based sliding window, when should an element be evicted from the deque?  
a) When its value is smaller than the new element  
b) When its timestamp is outside the current time window  
c) When the deque reaches a fixed size limit  
d) When the aggregate value exceeds a threshold  

---

**Question 9: Supporting Additional Aggregates**  
To add support for computing the minimum value in a sliding window, what is the most efficient approach?  
a) Scan the entire deque for each query  
b) Maintain a second deque similar to the one used for maximum  
c) Store elements in a min-heap  
d) Sort the deque after each insertion  

---

**Question 10: Real-World Application**  
In which scenario would a sliding window aggregator be most useful?  
a) Calculating the total sum of all transactions ever recorded  
b) Monitoring the average CPU usage over the last 10 minutes  
c) Storing all user login events for audit purposes  
d) Sorting a dataset by timestamp  

---

Great job! Your answers are all correct. Below, I’ll provide a brief explanation for each question, confirming why your choice is correct and why the other options are not. This will reinforce the concepts and clarify any potential ambiguities.

---

### **Explanations for Each Question**

**Question 1: Sliding Window Concept**  
**Correct Answer: b) To compute aggregates over a fixed-size subset of recent data**  
- **Why b?** A sliding window focuses on processing a subset of recent data (e.g., last T seconds or K events) to compute aggregates like sum, max, or average, making it ideal for real-time analytics.  
- **Why not others?**  
  - a) Storing all historical data defeats the purpose of a sliding window, which is memory-efficient.  
  - c) Sorting by timestamp isn’t the goal; the window maintains recent data regardless of order.  
  - d) Compression is unrelated to the sliding window’s purpose.  

**Question 2: Data Structure Choice**  
**Correct Answer: b) Double-ended queue (deque)**  
- **Why b?** A deque allows O(1) insertions at the back and evictions from the front, which is ideal for maintaining a sliding window where old elements are removed, and new ones are added.  
- **Why not others?**  
  - a) ArrayList has O(n) complexity for removing elements from the front.  
  - c) Binary Search Tree is overkill for sequential access and evictions.  
  - d) Hash Map doesn’t maintain order, making eviction logic inefficient.  

**Question 3: Time Complexity**  
**Correct Answer: a) O(1)**  
- **Why a?** Adding a new element and updating the running sum is O(1). Evicting old elements from the front of the deque is amortized O(1) since each element is added and removed at most once.  
- **Why not others?**  
  - b) O(log n) applies to tree-based structures, not deques.  
  - c) O(n) would occur if we scanned the entire deque for each operation.  
  - d) O(n log n) is relevant for sorting, not sliding window operations.  

**Question 4: Maximum in Sliding Window**  
**Correct Answer: b) Elements are stored in descending order with valid timestamps**  
- **Why b?** The auxiliary deque for max maintains elements in descending order, ensuring the maximum is always at the front. Timestamps are tracked to evict elements outside the window.  
- **Why not others?**  
  - a) Ascending order would make finding the max inefficient.  
  - c) Random order doesn’t help track the maximum.  
  - d) Frequency counts are irrelevant to finding the max.  

**Question 5: Concurrency**  
**Correct Answer: b) Wrap operations with a mutex lock**  
- **Why b?** A mutex ensures thread-safe access to the shared deque and aggregates, preventing race conditions during concurrent updates.  
- **Why not others?**  
  - a) A single global variable without synchronization causes data races.  
  - c) Disabling interrupts is impractical and not portable in user-space applications.  
  - d) A non-thread-safe queue would lead to undefined behavior under concurrency.  

**Question 6: Count-Based vs. Time-Based Window**  
**Correct Answer: b) Count-based windows maintain a fixed number of elements, while time-based windows use a time duration**  
- **Why b?** Count-based windows track the last K events, evicting based on size, while time-based windows evict based on timestamps relative to a time duration T.  
- **Why not others?**  
  - a) Reverses the definitions of count-based and time-based windows.  
  - c) Memory usage depends on data rate, not inherently higher for count-based.  
  - d) Neither typically requires a sorted structure; deques suffice.  

**Question 7: Space Complexity**  
**Correct Answer: c) O(N)**  
- **Why c?** The deque stores N elements within the time window, where N depends on the data rate and window size T. Additional deques (e.g., for max) also scale with N.  
- **Why not others?**  
  - a) O(1) is impossible since we store multiple elements.  
  - b) O(log N) applies to balanced trees, not deques.  
  - d) O(N log N) is unrelated to linear storage in a deque.  

**Question 8: Eviction Logic**  
**Correct Answer: b) When its timestamp is outside the current time window**  
- **Why b?** In a time-based sliding window, elements are evicted when their timestamp falls outside the window (e.g., older than current_time - T).  
- **Why not others?**  
  - a) Value-based eviction is unrelated to time windows.  
  - c) Size-based eviction applies to count-based windows, not time-based.  
  - d) Aggregate thresholds are not part of sliding window logic.  

**Question 9: Supporting Additional Aggregates**  
**Correct Answer: b) Maintain a second deque similar to the one used for maximum**  
- **Why b?** A second deque for minimum, maintaining elements in ascending order, allows O(1) access to the minimum, mirroring the max deque’s logic.  
- **Why not others?**  
  - a) Scanning the deque is O(n) and inefficient.  
  - c) A min-heap has O(log n) insertion/removal, less efficient than a deque.  
  - d) Sorting the deque repeatedly is O(n log n) and impractical.  

**Question 10: Real-World Application**  
**Correct Answer: b) Monitoring the average CPU usage over the last 10 minutes**  
- **Why b?** Sliding windows are ideal for real-time monitoring of recent data, like CPU usage over a fixed time window, as they focus on aggregates over recent data.  
- **Why not others?**  
  - a) Total sum of all transactions requires historical data, not a sliding window.  
  - c) Storing all login events is for auditing, not aggregation.  
  - d) Sorting datasets isn’t the purpose of a sliding window.  

---

### **Summary**  
You got **10/10 correct**, demonstrating a strong understanding of sliding window concepts, data structures, complexity, concurrency, and real-world applications.
