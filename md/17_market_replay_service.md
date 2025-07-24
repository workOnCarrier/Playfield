### 🎯 **Interview Problem**

> **Design and implement a Market Replay Engine** that can replay historical order events (trades, quotes, cancels) from a data file at a configurable speed (e.g., 2x, 5x, or real time). The engine should support:
>
> * Ingesting a sequence of time‑stamped market events.
> * Maintaining an in‑memory order book during replay.
> * Allowing consumers (e.g., strategy simulators) to subscribe and receive events in correct chronological order.
> * Pausing/resuming replay.
> * Fast‑forward to a given timestamp.
> * Handling millions of events efficiently.

---

### 🗣 **Interview Q\&A (10 Interactions)**

#### **1️⃣ Interaction**

**Interviewer:**
Suppose we give you a binary file of historical market events (quotes, trades) with timestamps. How would you design a system to replay them at a configurable speed?

**Candidate:**
I’d parse the file into a chronological sequence of events, store them in memory or stream them in batches, then run a replay loop that emits events based on their timestamps scaled by the configured speed. For example, if speed=2x and event gaps are 500 ms apart, I’d emit them every 250 ms.

---

#### **2️⃣ Interaction**

**Interviewer:**
How would you model an event in this system?

**Candidate:**
I’d define a struct like:

```cpp
struct MarketEvent {
    enum Type { QUOTE, TRADE, CANCEL } type;
    uint64_t timestamp_ns;
    std::string symbol;
    double price;
    uint32_t quantity;
    // optional fields like side, orderId
};
```

This makes it easy to sort and handle generically.

---

#### **3️⃣ Interaction**

**Interviewer:**
How do you maintain the order book state during replay?

**Candidate:**
I’d implement a standard in‑memory order book with two maps: `bidLevels` and `askLevels` keyed by price, each storing aggregated quantities. When a QUOTE arrives, update the respective level. On TRADE, reduce size from the correct side. On CANCEL, reduce size or remove level. This book updates as replay proceeds.

---

#### **4️⃣ Interaction**

**Interviewer:**
What data structure would you use to ensure chronological order and fast access?

**Candidate:**
Since the file is already timestamp‑sorted, I can process sequentially without sorting. I’d load chunks into a `std::vector<MarketEvent>` and iterate. For fast forward, I’d binary search in that vector for the target timestamp to jump.

---

#### **5️⃣ Interaction**

**Interviewer:**
How would you implement configurable speed?

**Candidate:**
I’d track the timestamp of the first event as `t0` and the wall‑clock start as `startWallTime`. For each event with timestamp `te`, compute:

```
elapsedReplay = (te - t0) / speed
expectedWallTime = startWallTime + elapsedReplay
sleepUntil(expectedWallTime)
emit(event)
```

---

#### **6️⃣ Interaction**

**Interviewer:**
What’s your approach to pausing and resuming replay?

**Candidate:**
On pause, I record `pauseTimeWall` and stop emitting events. On resume, I adjust `startWallTime` by the duration paused so that calculations remain consistent. The event iterator remains where it was.

---

#### **7️⃣ Interaction**

**Interviewer:**
Suppose we want to support subscribers that can register/unregister during replay. How would you handle this?

**Candidate:**
I’d implement a publisher‑subscriber pattern. The replay loop publishes events to a thread‑safe list of subscribers:

```cpp
std::vector<std::shared_ptr<IEventConsumer>> subscribers;
```

Each event is dispatched:

```cpp
for (auto& s : subscribers) s->onEvent(event);
```

Registration/unregistration can be protected by a mutex.

---

#### **8️⃣ Interaction**

**Interviewer:**
Let’s say the file has 50 million events. How do you handle memory and performance?

**Candidate:**
I’d use memory‑mapped I/O (mmap) or stream in blocks, instead of loading all at once. Keep the order book lightweight and avoid heavy locking. Possibly use a producer‑consumer model with one thread reading/parsing and another thread replaying.

---

#### **9️⃣ Interaction**

**Interviewer:**
How would you test that your replay engine is correct?

**Candidate:**
I’d write unit tests feeding a small synthetic event sequence and verify:

* Emitted order matches chronological order.
* Replay speed timing is respected.
* Order book state matches expected after replay.
  For large data, compare a checksum of emitted events with a known reference.

---

#### **🔟 Interaction**

**Interviewer:**
If you had to extend this to multiple symbols and parallel replay, what would you do?

**Candidate:**
Partition events by symbol and assign each partition to a dedicated replay thread, each maintaining its own order book. Synchronize timestamps globally if needed (e.g., use a priority queue across threads to ensure inter-symbol ordering if required).

---


**enhancements:**
* 📄 A **C++ implementation skeleton** of the replay engine.
* 🧪 A **test case file** to verify replay behavior.

---
Below is a **clean C++ solution** for a simplified **Market Replay Engine** with:

✅ A core replay engine (`MarketReplayEngine.cpp` with a header).
✅ An in‑memory order book.
✅ Subscriber interface and a sample subscriber.
✅ A test harness in a **separate file** (`test_MarketReplayEngine.cpp`).

This is designed to be self‑contained and easy to extend.
---

### 📌 **MarketReplayEngine.h**

```cpp
#pragma once
#include <vector>
#include <string>
#include <map>
#include <thread>
#include <atomic>
#include <chrono>
#include <mutex>
#include <condition_variable>
#include <memory>
#include <functional>

struct MarketEvent {
    enum class Type { QUOTE, TRADE, CANCEL };
    Type type;
    uint64_t timestamp_ns;  // nanoseconds since epoch
    std::string symbol;
    double price;
    uint32_t qty;
    bool isBid; // for quotes/cancels
};

struct IEventConsumer {
    virtual ~IEventConsumer() = default;
    virtual void onEvent(const MarketEvent& ev) = 0;
};

// Simple order book state for testing
struct OrderBook {
    std::map<double, uint32_t, std::greater<double>> bids;
    std::map<double, uint32_t> asks;
    void apply(const MarketEvent& ev);
};

class MarketReplayEngine {
public:
    MarketReplayEngine();
    ~MarketReplayEngine();

    void loadEvents(const std::vector<MarketEvent>& events); // preloaded for simplicity
    void addSubscriber(std::shared_ptr<IEventConsumer> sub);
    void removeAllSubscribers();

    void start(double speed = 1.0);
    void pause();
    void resume();
    void stop();
    void fastForward(uint64_t timestamp_ns);

    OrderBook& getOrderBook() { return book_; }

private:
    void replayLoop(double speed);

    std::vector<MarketEvent> events_;
    std::vector<std::shared_ptr<IEventConsumer>> subs_;
    OrderBook book_;

    std::atomic<bool> running_{false};
    std::atomic<bool> paused_{false};
    std::atomic<size_t> cursor_{0};
    std::thread worker_;
    std::mutex mtx_;
    std::condition_variable cv_;
    uint64_t fastForwardTarget_ = 0;
};
```

---

### 📌 **MarketReplayEngine.cpp**

```cpp
#include "MarketReplayEngine.h"
#include <iostream>
#include <algorithm>

void OrderBook::apply(const MarketEvent& ev) {
    auto& levels = ev.isBid ? bids : asks;
    if (ev.type == MarketEvent::Type::QUOTE) {
        levels[ev.price] = ev.qty;
    } else if (ev.type == MarketEvent::Type::CANCEL) {
        auto it = levels.find(ev.price);
        if (it != levels.end()) {
            if (ev.qty >= it->second) levels.erase(it);
            else it->second -= ev.qty;
        }
    } else if (ev.type == MarketEvent::Type::TRADE) {
        // reduce from best price
        auto &lvl = ev.isBid ? bids : asks;
        if (!lvl.empty()) {
            auto it = lvl.begin();
            if (ev.qty >= it->second) lvl.erase(it);
            else it->second -= ev.qty;
        }
    }
}

MarketReplayEngine::MarketReplayEngine() {}
MarketReplayEngine::~MarketReplayEngine() {
    stop();
}

void MarketReplayEngine::loadEvents(const std::vector<MarketEvent>& evs) {
    events_ = evs;
    std::sort(events_.begin(), events_.end(), [](auto&a, auto&b){
        return a.timestamp_ns < b.timestamp_ns;
    });
}

void MarketReplayEngine::addSubscriber(std::shared_ptr<IEventConsumer> sub) {
    subs_.push_back(sub);
}

void MarketReplayEngine::removeAllSubscribers() {
    subs_.clear();
}

void MarketReplayEngine::start(double speed) {
    if (running_) return;
    running_ = true;
    paused_ = false;
    cursor_ = 0;
    worker_ = std::thread(&MarketReplayEngine::replayLoop, this, speed);
}

void MarketReplayEngine::pause() {
    paused_ = true;
}

void MarketReplayEngine::resume() {
    if (!running_) return;
    {
        std::lock_guard<std::mutex> lk(mtx_);
        paused_ = false;
    }
    cv_.notify_all();
}

void MarketReplayEngine::stop() {
    running_ = false;
    resume();
    if (worker_.joinable()) worker_.join();
}

void MarketReplayEngine::fastForward(uint64_t timestamp_ns) {
    fastForwardTarget_ = timestamp_ns;
    // binary search
    auto it = std::lower_bound(events_.begin(), events_.end(), timestamp_ns,
        [](const MarketEvent& ev, uint64_t ts){ return ev.timestamp_ns < ts; });
    cursor_ = std::distance(events_.begin(), it);
}

void MarketReplayEngine::replayLoop(double speed) {
    if (events_.empty()) return;
    uint64_t startTime = events_[cursor_].timestamp_ns;
    auto startWall = std::chrono::steady_clock::now();

    for (; running_ && cursor_ < events_.size(); ++cursor_) {
        const auto& ev = events_[cursor_];
        if (fastForwardTarget_ && ev.timestamp_ns < fastForwardTarget_) {
            book_.apply(ev);
            continue;
        }

        uint64_t delta = ev.timestamp_ns - startTime;
        auto targetWall = startWall + std::chrono::nanoseconds((long long)(delta / speed));

        std::unique_lock<std::mutex> lk(mtx_);
        cv_.wait(lk, [&]{ return !paused_.load(); });
        lk.unlock();

        std::this_thread::sleep_until(targetWall);
        book_.apply(ev);
        for (auto& s : subs_) {
            s->onEvent(ev);
        }
    }
}
```

---

### 📌 **test\_MarketReplayEngine.cpp**

```cpp
#include "MarketReplayEngine.h"
#include <iostream>
#include <cassert>

// A simple subscriber that logs events
struct LoggerSubscriber : public IEventConsumer {
    void onEvent(const MarketEvent& ev) override {
        std::cout << "[EVENT] "
                  << (ev.isBid ? "BID " : "ASK ")
                  << (ev.type == MarketEvent::Type::QUOTE ? "QUOTE " :
                      ev.type == MarketEvent::Type::TRADE ? "TRADE " : "CANCEL ")
                  << ev.price << " x" << ev.qty
                  << " @" << ev.timestamp_ns << "\n";
    }
};

int main() {
    // Create a few sample events
    std::vector<MarketEvent> sampleEvents = {
        {MarketEvent::Type::QUOTE, 1000000000ULL, "AAPL", 100.5, 10, true},
        {MarketEvent::Type::QUOTE, 1000005000ULL, "AAPL", 100.6, 5, false},
        {MarketEvent::Type::TRADE, 1000010000ULL, "AAPL", 100.5, 3, true},
        {MarketEvent::Type::CANCEL,1000015000ULL, "AAPL", 100.6, 2, false}
    };

    MarketReplayEngine engine;
    engine.loadEvents(sampleEvents);

    auto logger = std::make_shared<LoggerSubscriber>();
    engine.addSubscriber(logger);

    std::cout << "Starting replay at 2x speed...\n";
    engine.start(2.0);

    // Let it run for a short while
    std::this_thread::sleep_for(std::chrono::milliseconds(20));
    std::cout << "Pausing...\n";
    engine.pause();

    // Check order book state after partial replay
    OrderBook& book = engine.getOrderBook();
    // For example, we expect first quote applied
    assert(book.bids.count(100.5) == 1);

    std::cout << "Resuming...\n";
    engine.resume();

    // Let finish
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    engine.stop();

    // Final order book sanity check
    assert(book.bids[100.5] == 7); // 10 quoted - 3 traded
    std::cout << "All tests passed!\n";
    return 0;
}
```

---

### 🛠 **How to build & run**

```bash
g++ -std=c++17 -pthread MarketReplayEngine.cpp test_MarketReplayEngine.cpp -o test_replay
./test_replay
```

✅ You’ll see event logs and final test assertions.
✅ Easy to extend with real file parsing or more complex order book logic.

---

If you’d like, I can also:

* Add **memory‑mapped file I/O** for loading events.
* Add **multithreaded symbol partitioning**.
* Provide a **benchmark harness** for millions of events.


----

### Multiple Choice Questions

**Question 1: Event Processing Order**  
To ensure events are replayed in the correct chronological order, what is the most critical property of the event data structure?  
a) Event type (QUOTE, TRADE, CANCEL)  
b) Timestamp  
c) Symbol identifier  
d) Price and quantity  

**Question 2: Order Book Maintenance**  
When maintaining an in-memory order book, what is the most efficient data structure for storing bid and ask levels, assuming frequent updates and lookups by price?  
a) Vector  
b) Hash Map  
c) Sorted Map (e.g., std::map)  
d) Priority Queue  

**Question 3: Configurable Replay Speed**  
To implement a configurable replay speed (e.g., 2x, 5x), what is the best approach to control the timing of event emissions?  
a) Scale the event timestamps by the speed factor and sleep accordingly  
b) Emit events at a fixed interval regardless of timestamps  
c) Use a priority queue to reorder events by speed  
d) Process all events instantly and buffer output  

**Question 4: Pause/Resume Functionality**  
When pausing a replay engine, what is a key consideration to ensure resuming works correctly?  
a) Resetting the event iterator to the start  
b) Adjusting the wall-clock time reference to account for pause duration  
c) Clearing the order book state  
d) Re-sorting the event queue  

**Question 5: Fast-Forward Mechanism**  
To fast-forward to a specific timestamp, what is the most efficient approach for finding the starting point in a sorted event sequence?  
a) Linear search through all events  
b) Binary search on timestamps  
c) Hash table lookup by timestamp  
d) Re-parsing the input file  

**Question 6: Subscriber Pattern**  
In a publisher-subscriber model for event distribution, what is a critical consideration for handling subscribers dynamically?  
a) Storing subscribers in a static array  
b) Using thread-safe mechanisms for registration/unregistration  
c) Requiring subscribers to process events synchronously  
d) Limiting the number of subscribers to one  

**Question 7: Memory Efficiency for Large Event Sets**  
When handling millions of events, what is an effective strategy to manage memory usage?  
a) Load all events into a vector in memory  
b) Use memory-mapped I/O or stream events in chunks  
c) Store events in a database and query them  
d) Compress events into a smaller data structure  

**Question 8: Order Book Updates**  
When a TRADE event is processed in the order book, what is the typical action taken?  
a) Add a new price level  
b) Reduce quantity from the best matching price level  
c) Remove all price levels on the opposite side  
d) Update the timestamp of the order book  

**Question 9: Testing Replay Accuracy**  
What is a robust way to verify that the replay engine emits events in the correct order?  
a) Compare the checksum of emitted events with a reference  
b) Check the final memory usage of the engine  
c) Verify the number of subscribers registered  
d) Count the total events processed  

**Question 10: Multi-Symbol Parallel Replay**  
To extend the engine for parallel replay of multiple symbols, what is a key challenge to address?  
a) Ensuring all threads process events at the same speed  
b) Maintaining global timestamp synchronization across symbols  
c) Combining all symbols into a single order book  
d) Storing all events in a single thread  

---


### Evaluation of Your Answers

**Question 1: Event Processing Order**  
**What is the most critical property of the event data structure to ensure events are replayed in the correct chronological order?**  
- **Your Answer**: b) Timestamp  
- **Correct Answer**: b) Timestamp  
- **Feedback**: Correct! The timestamp is critical for ensuring events are processed in chronological order, as it determines the sequence of market events during replay.

**Question 2: Order Book Maintenance**  
**What is the most efficient data structure for storing bid and ask levels, assuming frequent updates and lookups by price?**  
- **Your Answer**: d) Priority Queue  
- **Correct Answer**: c) Sorted Map (e.g., std::map)  
- **Feedback**: Incorrect. A sorted map (e.g., std::map) is ideal because it allows efficient lookups, insertions, and deletions by price, maintaining sorted order for bids (descending) and asks (ascending). A priority queue is less suitable since it’s designed for extracting min/max elements and doesn’t support direct price-level updates or lookups as efficiently.

**Question 3: Configurable Replay Speed**  
**What is the best approach to control the timing of event emissions for configurable replay speed?**  
- **Your Answer**: a) Scale the event timestamps by the speed factor and sleep accordingly  
- **Correct Answer**: a) Scale the event timestamps by the speed factor and sleep accordingly  
- **Feedback**: Correct! Scaling timestamps by the speed factor (e.g., dividing time deltas by speed) and sleeping until the calculated wall-clock time ensures accurate replay speed.

**Question 4: Pause/Resume Functionality**  
**What is a key consideration to ensure resuming works correctly after pausing?**  
- **Your Answer**: b) Adjusting the wall-clock time reference to account for pause duration  
- **Correct Answer**: b) Adjusting the wall-clock time reference to account for pause duration  
- **Feedback**: Correct! Adjusting the wall-clock time reference (e.g., updating startWallTime) ensures that the replay timing remains consistent after resuming, accounting for the pause duration.

**Question 5: Fast-Forward Mechanism**  
**What is the most efficient approach for finding the starting point in a sorted event sequence for fast-forward?**  
- **Your Answer**: b) Binary search on timestamps  
- **Correct Answer**: b) Binary search on timestamps  
- **Feedback**: Correct! Since events are sorted by timestamp, a binary search is the most efficient way to find the first event at or after the target timestamp, with O(log n) complexity.

**Question 6: Subscriber Pattern**  
**What is a critical consideration for handling subscribers dynamically in a publisher-subscriber model?**  
- **Your Answer**: b) Using thread-safe mechanisms for registration/unregistration  
- **Correct Answer**: b) Using thread-safe mechanisms for registration/unregistration  
- **Feedback**: Correct! Dynamic registration/unregistration during replay requires thread-safe mechanisms (e.g., mutex) to prevent race conditions when modifying the subscriber list.

**Question 7: Memory Efficiency for Large Event Sets**  
**When handling millions of events, what is an effective strategy to manage memory usage?**  
- **Your Answer**: b) Use memory-mapped I/O or stream events in chunks  
- **Correct Answer**: b) Use memory-mapped I/O or stream events in chunks  
- **Feedback**: Correct! Memory-mapped I/O or streaming events in chunks avoids loading millions of events into memory at once, improving scalability and memory efficiency.

**Question 8: Order Book Updates**  
**What is the typical action taken when a TRADE event is processed in the order book?**  
- **Your Answer**: b) Reduce quantity from the best matching price level  
- **Correct Answer**: b) Reduce quantity from the best matching price level  
- **Feedback**: Correct! A TRADE event typically reduces the quantity at the best matching price level (highest bid or lowest ask), reflecting the executed trade.

**Question 9: Testing Replay Accuracy**  
**What is a robust way to verify that the replay engine emits events in the correct order?**  
- **Your Answer**: b) Check the final memory usage of the engine  
- **Correct Answer**: a) Compare the checksum of emitted events with a reference  
- **Feedback**: Incorrect. Checking memory usage doesn’t verify event order. Comparing a checksum (or sequence) of emitted events with a known reference ensures that events are emitted in the correct chronological order and content.

**Question 10: Multi-Symbol Parallel Replay**  
**What is a key challenge to address when extending the engine for parallel replay of multiple symbols?**  
- **Your Answer**: b) Maintaining global timestamp synchronization across symbols  
- **Correct Answer**: b) Maintaining global timestamp synchronization across symbols  
- **Feedback**: Correct! When replaying multiple symbols in parallel threads, ensuring global timestamp synchronization (e.g., via a priority queue or coordinator) is critical to maintain the correct chronological order of events across symbols.

---

### Summary
- **Correct Answers**: 8/10 (Questions 1, 3, 4, 5, 6, 7, 8, 10)  
- **Incorrect Answers**: 2, 9  
- **Score**: 80%

### Feedback and Recommendations
You demonstrated a strong understanding of the core concepts, particularly in event processing, replay timing, and scalability considerations. The two incorrect answers are worth reviewing:

- **Question 2**: Consider why a sorted map (std::map) is better than a priority queue for order book maintenance. A priority queue is optimized for extracting the top element but doesn’t allow efficient updates or lookups by arbitrary price levels, which is common in order book operations.
- **Question 9**: For testing replay accuracy, focus on methods that directly validate the output sequence (e.g., checksums or event logs) rather than indirect metrics like memory usage, which don’t confirm correctness of event ordering.


