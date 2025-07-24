✅ **Real-Time Price Aggregator**
🏢 Target companies: **Two Sigma, IEX, Bloomberg, Nasdaq, Robinhood, Point72**
🧑‍💻 Simulation: **Interviewer (I)** and **Interviewee (C)**
💬 **10 back‑and‑forth interactions**

---

### 🎯 **Interview Problem**

**Prompt:**

> *Design and implement a **Real-Time Price Aggregator** that consumes trade or quote updates from multiple upstream sources (exchanges, dark pools, ECNs) and maintains the latest NBBO (National Best Bid and Offer). The aggregator should expose a thread-safe API to:*
>
> * *Publish updates from various sources (symbol, bid, ask, timestamp).*
> * *Get the current best bid/ask for a symbol at any time.*
> * *Handle out‑of‑order updates (ignore stale timestamps).*
> * *Scale for thousands of symbols and high throughput (≈50k updates/sec).*
>
> **Bonus:** discuss persistence or fault-tolerance strategies.

---

### 💬 **Simulated Interview Q\&A (10 interactions)**

**1️⃣ I:**
Can you restate the problem in your own words and outline the main components you’d design?

**C:**
Sure. We need a thread-safe service that receives streaming price updates from multiple venues. For each symbol, we track the best bid (highest bid) and best ask (lowest ask) using timestamps to ignore stale data. The components are:

* Ingestor (multi-threaded) for price updates.
* Core aggregator data structure (map symbol → best bid/ask).
* Concurrency control (locks or lock-free).
* API to query current NBBO.

---

**2️⃣ I:**
What data structure would you use to maintain the best bid/ask for each symbol efficiently?

**C:**
I’d use a `std::unordered_map<std::string, Quote>` where `Quote` holds `{bid, ask, bid_ts, ask_ts}`. For each update, compare timestamps and update only if newer. Hash map gives O(1) average lookups for high throughput.

---

**3️⃣ I:**
How would you handle concurrent reads and writes?

**C:**
Use a **read-write lock** per symbol bucket or a sharded lock approach. Most reads are frequent, so `std::shared_mutex` allows multiple readers and exclusive writers. For higher throughput, we could use lock-free structures like RCU (Read-Copy-Update), but I’d start with RW locks.

---

**4️⃣ I:**
Updates can arrive out of order. How do you ensure stale updates are ignored?

**C:**
Each update has a timestamp. When processing:

```cpp
if (update.ts > current.bid_ts) { current.bid = update.bid; current.bid_ts = update.ts; }
if (update.ts > current.ask_ts) { current.ask = update.ask; current.ask_ts = update.ts; }
```

Otherwise, ignore.

---

**5️⃣ I:**
Can you sketch the C++ class interface for this aggregator?

**C:**
Sure:

```cpp
struct Quote { double bid; double ask; long bid_ts; long ask_ts; };

class PriceAggregator {
public:
    void publish(const std::string& symbol, double bid, double ask, long ts);
    Quote getQuote(const std::string& symbol) const;
};
```

---

**6️⃣ I:**
Imagine 50k updates/sec across thousands of symbols. Any optimizations?

**C:**
Yes:

* Pre-shard the map by symbol hash into N buckets to reduce lock contention.
* Use a thread pool to process incoming updates.
* Avoid dynamic allocations by reusing objects.
* Optionally, use lock-free ring buffers per shard for ingestion.

---

**7️⃣ I:**
How would you test correctness of this design?

**C:**
Write unit tests:

* Publish updates with increasing timestamps, verify best bid/ask.
* Publish stale updates, verify no overwrite.
* Concurrent publish & getQuote threads, ensure no data race (TSan).
* Stress test with simulated 50k updates/sec.

---

**8️⃣ I:**
Can you show a sample implementation of `publish` with thread-safety?

**C:**
Yes:

```cpp
void PriceAggregator::publish(const std::string& sym, double bid, double ask, long ts) {
    auto& mtx = shardMutex(sym);
    std::unique_lock lock(mtx);
    auto& q = shardMap(sym)[sym];
    if (ts > q.bid_ts) { q.bid = bid; q.bid_ts = ts; }
    if (ts > q.ask_ts) { q.ask = ask; q.ask_ts = ts; }
}
```

(`shardMutex` and `shardMap` choose bucket by hash.)

---

**9️⃣ I:**
If we want fault tolerance, how would you persist state?

**C:**

* Append each update to a durable log (e.g., Kafka or local write-ahead log).
* On restart, replay log to rebuild state.
* For low latency, do async persistence so it doesn’t block.

---

**🔟 I:**
Final question: what’s a reasonable latency target and how would you measure it?

**C:**
For real-time quotes, sub-millisecond update propagation is ideal. I’d instrument `publish` and `getQuote` with high-resolution timestamps, collect percentiles (p50, p99), and benchmark under load using a synthetic update generator.

---
***Also can further***
* Provide **full C++ implementation** (with thread-safe shards),
* Provide **unit test code**,
* Or add **benchmarking harness**.

----

### 📂 **File 1: `PriceAggregator.h`**

```cpp
#pragma once
#include <string>
#include <unordered_map>
#include <shared_mutex>
#include <vector>
#include <mutex>
#include <optional>
#include <atomic>

struct Quote {
    double bid = 0.0;
    double ask = 0.0;
    long bid_ts = -1;
    long ask_ts = -1;
};

class PriceAggregator {
public:
    PriceAggregator(size_t numShards = 64)
        : shardCount(numShards), maps(numShards), mutexes(numShards) {}

    void publish(const std::string &symbol, double bid, double ask, long ts);
    std::optional<Quote> getQuote(const std::string &symbol) const;

private:
    size_t shardCount;
    mutable std::vector<std::shared_mutex> mutexes;
    mutable std::vector<std::unordered_map<std::string, Quote>> maps;

    size_t shardFor(const std::string &symbol) const {
        return std::hash<std::string>{}(symbol) % shardCount;
    }
};
```

---

### 📂 **File 2: `PriceAggregator.cpp`**

```cpp
#include "PriceAggregator.h"

void PriceAggregator::publish(const std::string &symbol, double bid, double ask, long ts) {
    size_t shardIdx = shardFor(symbol);
    auto &mtx = mutexes[shardIdx];
    auto &map = maps[shardIdx];

    std::unique_lock lock(mtx);
    Quote &q = map[symbol]; // default-construct if not present
    if (ts > q.bid_ts) {
        q.bid = bid;
        q.bid_ts = ts;
    }
    if (ts > q.ask_ts) {
        q.ask = ask;
        q.ask_ts = ts;
    }
}

std::optional<Quote> PriceAggregator::getQuote(const std::string &symbol) const {
    size_t shardIdx = shardFor(symbol);
    auto &mtx = mutexes[shardIdx];
    auto &map = maps[shardIdx];

    std::shared_lock lock(mtx);
    auto it = map.find(symbol);
    if (it == map.end()) {
        return std::nullopt;
    }
    return it->second;
}
```

---

### 📂 **File 3: `test_price_aggregator.cpp`**

Compile with `-pthread -std=c++17`
(For example: `g++ -std=c++17 -pthread PriceAggregator.cpp test_price_aggregator.cpp -o test`)

```cpp
#include "PriceAggregator.h"
#include <iostream>
#include <thread>
#include <vector>
#include <cassert>

void basicTests() {
    PriceAggregator agg;

    // publish initial quote
    agg.publish("AAPL", 100.5, 101.0, 1);
    auto q = agg.getQuote("AAPL");
    assert(q.has_value());
    assert(q->bid == 100.5);
    assert(q->ask == 101.0);

    // publish newer bid
    agg.publish("AAPL", 102.0, 101.0, 2);
    q = agg.getQuote("AAPL");
    assert(q->bid == 102.0);
    assert(q->ask == 101.0);

    // stale update (ts=1) should be ignored
    agg.publish("AAPL", 50.0, 50.0, 1);
    q = agg.getQuote("AAPL");
    assert(q->bid == 102.0); // unchanged
    assert(q->ask == 101.0);

    std::cout << "[basicTests] passed\n";
}

void concurrentTests() {
    PriceAggregator agg;
    constexpr int N = 1000;

    auto writer = [&agg](int id) {
        for (int i = 0; i < 100; ++i) {
            agg.publish("SYM" + std::to_string(id), i * 1.0, i * 1.0 + 0.5, i);
        }
    };

    std::vector<std::thread> threads;
    for (int t = 0; t < 8; ++t) {
        threads.emplace_back(writer, t);
    }
    for (auto &th : threads) th.join();

    // validate
    for (int t = 0; t < 8; ++t) {
        auto q = agg.getQuote("SYM" + std::to_string(t));
        assert(q.has_value());
        assert(q->bid == 99.0);
        assert(q->ask == 99.5);
    }

    std::cout << "[concurrentTests] passed\n";
}

int main() {
    basicTests();
    concurrentTests();
    std::cout << "All tests passed ✅\n";
    return 0;
}
```

---

### ✅ **Features**

* **Thread‑safe** via per‑shard `std::shared_mutex`.
* Handles **out‑of‑order updates** via timestamp comparison.
* **O(1)** average symbol lookup.
* Scales with configurable shard count.

---

### Multiple-Choice Questions

**Question 1: Data Structure Selection**  
Which data structure is most suitable for storing symbol-to-quote mappings in a high-throughput Real-Time Price Aggregator?  
a) std::vector  
b) std::map  
c) std::unordered_map  
d) std::list  

**Question 2: Concurrency Control**  
What is the primary advantage of using a read-write lock (e.g., std::shared_mutex) over a regular mutex in this system?  
a) It prevents all concurrent access.  
b) It allows multiple readers to access data simultaneously.  
c) It eliminates the need for locking entirely.  
d) It guarantees write operations are faster.  

**Question 3: Handling Out-of-Order Updates**  
To handle out-of-order updates, the system compares timestamps. What happens if an update’s timestamp is older than the current stored timestamp?  
a) The update overwrites the current quote.  
b) The update is ignored.  
c) The system throws an exception.  
d) The update is queued for later processing.  

**Question 4: Scalability**  
To handle 50k updates/sec, sharding the data structure by symbol is proposed. What is the main benefit of sharding in this context?  
a) It reduces memory usage for each symbol.  
b) It eliminates the need for timestamps.  
c) It reduces lock contention by distributing writes across buckets.  
d) It simplifies the API design.  

**Question 5: Thread-Safety**  
Which approach would NOT ensure thread-safety in the PriceAggregator’s publish method?  
a) Using a std::shared_mutex with shared locks for reads and exclusive locks for writes.  
b) Using a lock-free data structure like a concurrent hash map.  
c) Accessing the data structure without any synchronization mechanism.  
d) Sharding the data structure and using per-shard mutexes.  

**Question 6: Fault Tolerance**  
What is a benefit of using a write-ahead log (WAL) for fault tolerance in this system?  
a) It reduces the latency of publishing updates.  
b) It allows the system to rebuild state after a crash by replaying logged updates.  
c) It eliminates the need for in-memory data structures.  
d) It guarantees zero data loss without any overhead.  

**Question 7: Testing**  
When testing the PriceAggregator for correctness, what is a critical scenario to include?  
a) Testing with only one symbol and one update.  
b) Testing concurrent publishes and reads to detect data races.  
c) Testing with invalid symbol names only.  
d) Testing with zero timestamps only.  

**Question 8: Performance Optimization**  
Which optimization would most effectively reduce latency in the publish method for high-throughput scenarios?  
a) Using a single global lock for all operations.  
b) Pre-allocating memory for the hash map to avoid dynamic resizing.  
c) Storing updates in a database before processing.  
d) Increasing the number of shards to one per symbol.  

**Question 9: API Design**  
Why is returning std::optional<Quote> in the getQuote method a good design choice?  
a) It allows returning multiple quotes for a single symbol.  
b) It indicates whether a quote exists for the requested symbol.  
c) It reduces the memory footprint of the Quote structure.  
d) It simplifies thread-safety requirements.  

**Question 10: Latency Measurement**  
To measure the latency of the publish method, which metric would provide the most insight into performance under load?  
a) Average latency across all updates.  
b) p99 (99th percentile) latency for updates.  
c) Total number of updates processed.  
d) Memory usage of the aggregator.  

---

### Answer Evaluation

**Question 1: Data Structure Selection**  
**Correct Answer: c) std::unordered_map**  
**Your Answer: C** (Correct)  
**Explanation**: `std::unordered_map` provides O(1) average-case lookup and update time, ideal for high-throughput symbol-to-quote mappings. `std::vector` and `std::list` are unsuitable for key-based lookups, and `std::map` (a red-black tree) has O(log n) complexity, which is slower.

**Question 2: Concurrency Control**  
**Correct Answer: b) It allows multiple readers to access data simultaneously.**  
**Your Answer: B** (Correct)  
**Explanation**: A read-write lock (`std::shared_mutex`) allows multiple readers to access data concurrently while ensuring exclusive access for writers, improving performance for read-heavy workloads like querying NBBO.

**Question 3: Handling Out-of-Order Updates**  
**Correct Answer: b) The update is ignored.**  
**Your Answer: B** (Correct)  
**Explanation**: The system compares the update’s timestamp with the stored timestamp and ignores the update if it’s older, ensuring only the latest data is kept.

**Question 4: Scalability**  
**Correct Answer: c) It reduces lock contention by distributing writes across buckets.**  
**Your Answer: C** (Correct)  
**Explanation**: Sharding distributes symbols across multiple buckets, each with its own lock, reducing contention in high-throughput scenarios. It doesn’t directly reduce memory usage, eliminate timestamps, or simplify the API.

**Question 5: Thread-Safety**  
**Correct Answer: c) Accessing the data structure without any synchronization mechanism.**  
**Your Answer: B** (Incorrect)  
**Explanation**: Using a lock-free data structure (like a concurrent hash map) *does* ensure thread-safety by avoiding locks while maintaining data integrity. The correct answer is `c`, as accessing the data structure without synchronization (e.g., no locks or atomic operations) leads to data races and undefined behavior in a multi-threaded environment.

**Question 6: Fault Tolerance**  
**Correct Answer: b) It allows the system to rebuild state after a crash by replaying logged updates.**  
**Your Answer: A** (Incorrect)  
**Explanation**: A write-ahead log (WAL) ensures fault tolerance by persisting updates durably, allowing state reconstruction after a crash. It doesn’t inherently reduce latency (option `a`); in fact, synchronous logging may increase latency unless done asynchronously.

**Question 7: Testing**  
**Correct Answer: b) Testing concurrent publishes and reads to detect data races.**  
**Your Answer: B** (Correct)  
**Explanation**: Testing concurrent operations is critical to ensure thread-safety and detect issues like data races, especially in a high-throughput system. Other options are less comprehensive for validating correctness.

**Question 8: Performance Optimization**  
**Correct Answer: b) Pre-allocating memory for the hash map to avoid dynamic resizing.**  
**Your Answer: D** (Incorrect)  
**Explanation**: Pre-allocating memory (e.g., via `reserve`) avoids costly dynamic resizing in hash maps, improving latency. Using one shard per symbol (`d`) is impractical for thousands of symbols, as it increases overhead (e.g., too many mutexes) without clear benefits over moderate sharding.

**Question 9: API Design**  
**Correct Answer: b) It indicates whether a quote exists for the requested symbol.**  
**Your Answer: B** (Correct)  
**Explanation**: `std::optional<Quote>` signals whether a quote exists for a symbol (e.g., returning `std::nullopt` if not found), making the API robust and clear. It doesn’t support multiple quotes, reduce memory, or directly affect thread-safety.

**Question 10: Latency Measurement**  
**Correct Answer: b) p99 (99th percentile) latency for updates.**  
**Your Answer: B** (Correct)  
**Explanation**: p99 latency captures worst-case performance under load, critical for real-time systems where tail latency matters. Average latency (`a`) may hide outliers, and other metrics are less relevant for latency.

### Score
You got **7 out of 10** correct! Well done! Here's a summary of the incorrect answers with key takeaways:

- **Question 5**: Lock-free data structures (e.g., concurrent hash maps) are thread-safe, as they use atomic operations to manage concurrency without locks. Be cautious about assuming lock-free implies non-thread-safe.
- **Question 6**: Write-ahead logs are primarily for recovering state after failures, not for reducing latency. Asynchronous logging can mitigate latency impact, but it’s not the primary benefit.
- **Question 8**: Pre-allocating memory is a standard optimization for hash maps to avoid resizing, which can cause significant latency spikes. Over-sharding (one shard per symbol) is inefficient for large symbol sets.

### Next Steps
- Provide a deeper explanation for any question.
