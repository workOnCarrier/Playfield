### 📌 **Interview Problem**

**Design and implement a simplified Credit Risk Evaluator for a trading system.**

A trading desk wants to evaluate **credit exposure** for each counterparty intraday.

* You receive **trade events** in real-time (executions, modifications, cancellations).
* Each trade has: `counterpartyId`, `notional`, `direction (Buy/Sell)`, `instrument`, `timestamp`.
* Each counterparty has a `creditLimit`.
* You need to maintain the **net exposure** per counterparty in real-time and trigger an alert when exposure exceeds the limit.
* Exposure is defined as the sum of notionals for all **active trades** (executed but not cancelled/closed).
* The system should handle high throughput and low latency.

---

### 🎤 **Simulated Q\&A (10 Interactions)**

**Interviewer (I):**
Welcome! Let’s start. Imagine we’re building a **Credit Risk Evaluator** for intraday trading. How would you model the data?

**Interviewee (E):**
I’d create a `Trade` struct containing fields like `tradeId`, `counterpartyId`, `notional`, `direction`, `instrument`, and `isActive`. I’d also maintain a `unordered_map<counterpartyId, double>` to store running exposure, and a `unordered_map<tradeId, Trade>` to track individual trades.

---

**I:**
Good start. How would you handle new trade events arriving at high frequency?

**E:**
I’d process them in a single-threaded event loop or via a lock-free queue feeding a worker thread. Each new trade would be inserted into the trades map, and its notional would be added to the corresponding counterparty’s exposure.

---

**I:**
What about trade cancellations or modifications?

**E:**
For a cancellation, I’d look up the trade in the `trades` map, subtract its notional from the counterparty’s exposure, and mark it inactive or erase it. For a modification, I’d compute the delta (new notional minus old notional) and adjust the exposure accordingly.

---

**I:**
How would you enforce credit limits?

**E:**
Each counterparty would have a stored `creditLimit`. After every event update, I’d check `exposure[counterpartyId] > creditLimit[counterpartyId]`. If true, I’d trigger an alert—maybe log, publish to Kafka, or push to a dashboard.

---

**I:**
Can you discuss concurrency? What if multiple threads process events?

**E:**
If scaling out, I’d consider sharding by `counterpartyId` so each shard is handled by one thread to avoid locking. Alternatively, I could use lock-free data structures or atomic updates. But for simplicity, a single-threaded event loop suffices for many use cases.

---

**I:**
How do you handle replay scenarios, e.g., rebuilding exposure from a historical trade stream?

**E:**
I’d feed historical events into the same pipeline, resetting state beforehand. Since exposure is computed incrementally, replaying in order will rebuild exposure deterministically.

---

**I:**
What data structure would you use for fast lookup of active trades?

**E:**
A `std::unordered_map<tradeId, Trade>` in C++ would be ideal for O(1) lookup, with tradeId as key.

---

**I:**
How would you handle very large notionals or precision issues?

**E:**
I’d use a 64-bit integer if notionals are in smallest currency units (like cents), or a high-precision decimal type if fractional values are critical. Avoid floating-point for monetary values.

---

**I:**
Can you sketch a simple API for this evaluator?

**E:**
Sure:

```cpp
class CreditRiskEvaluator {
public:
  void onTradeAdd(const Trade& t);
  void onTradeCancel(const std::string& tradeId);
  void onTradeModify(const std::string& tradeId, double newNotional);
  double getExposure(const std::string& counterpartyId) const;
};
```

---

**I:**
Finally, how would you test it?

**E:**
I’d write unit tests feeding sequences of add/modify/cancel events and assert that exposure matches expectations and alerts fire correctly when limits are exceeded. I’d also test replay scenarios and high-volume stress tests.


✅ **Would you like me to now write the full C++ implementation with a separate test file?** Let me know!

---


### ✅ **credit\_risk\_evaluator.h**

```cpp
#ifndef CREDIT_RISK_EVALUATOR_H
#define CREDIT_RISK_EVALUATOR_H

#include <string>
#include <unordered_map>
#include <unordered_set>
#include <stdexcept>
#include <iostream>

struct Trade {
    std::string tradeId;
    std::string counterpartyId;
    double notional;
    bool active;
};

class CreditRiskEvaluator {
public:
    void setCreditLimit(const std::string& counterpartyId, double limit) {
        creditLimit[counterpartyId] = limit;
        if (exposure.find(counterpartyId) == exposure.end()) {
            exposure[counterpartyId] = 0.0;
        }
    }

    void onTradeAdd(const Trade& t) {
        if (trades.count(t.tradeId)) {
            throw std::runtime_error("Trade already exists: " + t.tradeId);
        }
        trades[t.tradeId] = t;
        trades[t.tradeId].active = true;
        exposure[t.counterpartyId] += t.notional;
        checkLimit(t.counterpartyId);
    }

    void onTradeCancel(const std::string& tradeId) {
        auto it = trades.find(tradeId);
        if (it == trades.end() || !it->second.active) return;
        Trade &t = it->second;
        exposure[t.counterpartyId] -= t.notional;
        t.active = false;
    }

    void onTradeModify(const std::string& tradeId, double newNotional) {
        auto it = trades.find(tradeId);
        if (it == trades.end() || !it->second.active) {
            throw std::runtime_error("Trade not active or not found: " + tradeId);
        }
        Trade &t = it->second;
        double delta = newNotional - t.notional;
        t.notional = newNotional;
        exposure[t.counterpartyId] += delta;
        checkLimit(t.counterpartyId);
    }

    double getExposure(const std::string& counterpartyId) const {
        auto it = exposure.find(counterpartyId);
        if (it == exposure.end()) return 0.0;
        return it->second;
    }

private:
    std::unordered_map<std::string, Trade> trades;
    std::unordered_map<std::string, double> exposure;
    std::unordered_map<std::string, double> creditLimit;

    void checkLimit(const std::string& counterpartyId) {
        if (creditLimit.count(counterpartyId) &&
            exposure[counterpartyId] > creditLimit[counterpartyId]) {
            std::cerr << "[ALERT] Counterparty " << counterpartyId
                      << " exceeds credit limit! Exposure=" << exposure[counterpartyId]
                      << " Limit=" << creditLimit[counterpartyId] << "\n";
        }
    }
};

#endif // CREDIT_RISK_EVALUATOR_H
```

---

### ✅ **main\_test.cpp**

```cpp
#include "credit_risk_evaluator.h"
#include <cassert>
#include <iostream>

int main() {
    CreditRiskEvaluator evaluator;
    evaluator.setCreditLimit("CP1", 1000000.0);
    evaluator.setCreditLimit("CP2", 500000.0);

    // Add trades
    evaluator.onTradeAdd({"T1", "CP1", 200000.0, true});
    evaluator.onTradeAdd({"T2", "CP1", 300000.0, true});
    evaluator.onTradeAdd({"T3", "CP2", 100000.0, true});

    // Check exposure after adds
    assert(evaluator.getExposure("CP1") == 500000.0);
    assert(evaluator.getExposure("CP2") == 100000.0);

    // Modify a trade
    evaluator.onTradeModify("T1", 400000.0);
    assert(evaluator.getExposure("CP1") == 700000.0);

    // Cancel a trade
    evaluator.onTradeCancel("T2");
    assert(evaluator.getExposure("CP1") == 400000.0);

    // Exceed limit
    evaluator.onTradeAdd({"T4", "CP1", 700000.0, true});
    // Should trigger alert (printed to stderr), exposure = 1.1M > 1M limit
    assert(evaluator.getExposure("CP1") == 1100000.0);

    std::cout << "All test cases passed!\n";
    return 0;
}
```

---

### 💡 **Build & Run**

```bash
g++ -std=c++17 -O2 -Wall main_test.cpp -o test_credit_risk
./test_credit_risk
```

Expected output:

```
[ALERT] Counterparty CP1 exceeds credit limit! Exposure=1100000 Limit=1000000
All test cases passed!
```

---

If you’d like, I can also provide:
✅ a **multi-threaded or lock‑free variant**,
✅ add **unit testing framework** (e.g., GoogleTest),
✅ or include **CSV/JSON ingestion** for trades.


----
### Multiple-Choice Questions

#### 1. **Data Modeling**
What is the most appropriate data structure for storing and quickly accessing trade details by tradeId in a real-time Credit Risk Evaluator system?
- A) std::vector
- B) std::list
- C) std::unordered_map
- D) std::set

#### 2. **Real-Time Processing**
To handle high-frequency trade events with low latency, which approach is most effective for processing incoming events?
- A) Store events in a database and query them periodically
- B) Use a single-threaded event loop with an in-memory data structure
- C) Write events to a file and process them in batches
- D) Use a separate thread for each trade event

#### 3. **Exposure Calculation**
How should the net exposure for a counterparty be calculated in the system?
- A) Sum of all trade notionals, including cancelled trades
- B) Sum of notionals for active trades only
- C) Average of all trade notionals for the counterparty
- D) Maximum notional of any single trade for the counterparty

#### 4. **Concurrency**
If the system needs to scale to handle multiple threads processing trade events, what is a good strategy to avoid race conditions?
- A) Use a global lock for all data access
- B) Shard data by counterpartyId and assign each shard to a single thread
- C) Allow all threads to update shared data without synchronization
- D) Store all data in a database with transactional guarantees

#### 5. **Credit Limit Enforcement**
What is the most efficient way to check if a counterparty’s exposure exceeds its credit limit after each trade event?
- A) Recalculate total exposure by iterating over all trades for the counterparty
- B) Maintain a running sum of exposure and check after each update
- C) Query an external service for the latest exposure value
- D) Only check exposure at the end of the trading day

#### 6. **Event Handling**
When a trade modification event occurs, how should the system update the exposure for the associated counterparty?
- A) Add the new notional to the existing exposure
- B) Subtract the old notional and add the new notional
- C) Ignore the modification and keep the original exposure
- D) Recalculate exposure from all trades for the counterparty

#### 7. **Precision Handling**
Why is it recommended to avoid floating-point types for storing notional values in financial systems?
- A) Floating-point types are too slow for real-time systems
- B) Floating-point types can introduce rounding errors
- C) Floating-point types cannot handle negative values
- D) Floating-point types are not supported in C++

#### 8. **Replay Scenarios**
To rebuild exposure from a historical stream of trade events, what is the best approach?
- A) Process events in random order and adjust exposure
- B) Process events in chronological order using the same event-handling logic
- C) Aggregate all events into a summary before processing
- D) Only process the most recent event for each trade

#### 9. **Testing**
Which of the following is a critical test case for the Credit Risk Evaluator?
- A) Test that inactive trades are included in exposure calculations
- B) Test that an alert is triggered when exposure exceeds the credit limit
- C) Test that trades with zero notional are rejected
- D) Test that the system can process trades without a counterpartyId

#### 10. **Scalability**
To improve the system’s throughput for handling millions of trades per second, what design choice would be most effective?
- A) Use a single-threaded system with a relational database
- B) Implement a distributed system with sharding by counterpartyId
- C) Store all trades in memory without any indexing
- D) Process all trades in a single batch at the end of the day

---

Thank you for providing your answers! Below, I’ll review each of your responses, confirm whether they are correct, and provide explanations where needed to clarify the concepts related to the **Credit Risk Evaluator** system. I’ll keep it concise while ensuring clarity.

---

### Review of Your Answers

#### 1. **Data Modeling**
**Question**: What is the most appropriate data structure for storing and quickly accessing trade details by tradeId?  
**Your Answer**: C) std::unordered_map  
**Correct?**: ✅ **Yes**  
**Explanation**: `std::unordered_map` provides O(1) average-case lookup time, making it ideal for quickly accessing trade details by `tradeId`. `std::vector` and `std::list` have linear search times (O(n)), and `std::set` is slower for lookups (O(log n)) and unnecessary for this use case since ordering isn’t required.

---

#### 2. **Real-Time Processing**
**Question**: To handle high-frequency trade events with low latency, which approach is most effective?  
**Your Answer**: B) Use a single-threaded event loop with an in-memory data structure  
**Correct?**: ✅ **Yes**  
**Explanation**: A single-threaded event loop with in-memory data structures minimizes overhead and ensures low latency for real-time processing. Databases (A) or file-based processing (C) introduce I/O bottlenecks, and creating a thread per event (D) is inefficient due to thread overhead.

---

#### 3. **Exposure Calculation**
**Question**: How should the net exposure for a counterparty be calculated?  
**Your Answer**: A) Sum of all trade notionals, including cancelled trades  
**Correct?**: ❌ **No** (Correct Answer: B) Sum of notionals for active trades only)  
**Explanation**: Net exposure should only include active trades (executed but not cancelled/closed), as specified in the problem. Including cancelled trades (A) would inflate exposure inaccurately. Averaging (C) or taking the maximum (D) doesn’t align with the definition of exposure as the sum of notionals.

---

#### 4. **Concurrency**
**Question**: What is a good strategy to avoid race conditions in a multi-threaded system?  
**Your Answer**: B) Shard data by counterpartyId and assign each shard to a single thread  
**Correct?**: ✅ **Yes**  
**Explanation**: Sharding by `counterpartyId` ensures each thread handles a disjoint subset of data, eliminating race conditions without locks. A global lock (A) would create contention, unsynchronized access (C) causes data corruption, and relying on a database (D) adds latency unsuitable for real-time systems.

---

#### 5. **Credit Limit Enforcement**
**Question**: What is the most efficient way to check if exposure exceeds the credit limit?  
**Your Answer**: B) Maintain a running sum of exposure and check after each update  
**Correct?**: ✅ **Yes**  
**Explanation**: Maintaining a running sum of exposure in memory allows O(1) checks after each event. Recalculating exposure from all trades (A) is O(n) and inefficient. External services (C) add latency, and end-of-day checks (D) don’t meet real-time requirements.

---

#### 6. **Event Handling**
**Question**: How should the system update exposure for a trade modification event?  
**Your Answer**: B) Subtract the old notional and add the new notional  
**Correct?**: ✅ **Yes**  
**Explanation**: For a modification, the exposure delta is `newNotional - oldNotional`. This adjusts the running exposure correctly. Adding only the new notional (A) would double-count, ignoring modifications (C) is incorrect, and recalculating from all trades (D) is inefficient.

---

#### 7. **Precision Handling**
**Question**: Why avoid floating-point types for notional values in financial systems?  
**Your Answer**: B) Floating-point types can introduce rounding errors  
**Correct?**: ✅ **Yes**  
**Explanation**: Floating-point types can cause precision errors in financial calculations due to their binary representation (e.g., 0.1 may not be exact). They aren’t inherently slow (A), can handle negatives (C), and are supported in C++ (D), but rounding errors make them unsuitable for monetary values.

---

#### 8. **Replay Scenarios**
**Question**: What is the best approach to rebuild exposure from a historical trade stream?  
**Your Answer**: B) Process events in chronological order using the same event-handling logic  
**Correct?**: ✅ **Yes**  
**Explanation**: Processing events in chronological order using the same logic ensures deterministic and accurate exposure reconstruction. Random order (A) could produce incorrect results, aggregating first (C) loses event-specific logic, and using only the latest event (D) misses historical context.

---

#### 9. **Testing**
**Question**: Which is a critical test case for the Credit Risk Evaluator?  
**Your Answer**: B) Test that an alert is triggered when exposure exceeds the credit limit  
**Correct?**: ✅ **Yes**  
**Explanation**: Testing the alert mechanism for exceeding credit limits is critical, as it’s a core system requirement. Inactive trades shouldn’t be included (A), zero-notional trades aren’t specified as invalid (C), and trades require a `counterpartyId` (D), making B the best choice.

---

#### 10. **Scalability**
**Question**: What design choice improves throughput for millions of trades per second?  
**Your Answer**: B) Implement a distributed system with sharding by counterpartyId  
**Correct?**: ✅ **Yes**  
**Explanation**: A distributed system with sharding by `counterpartyId` allows parallel processing, maximizing throughput. Single-threaded systems with databases (A) are too slow, unindexed in-memory storage (C) is inefficient for lookups, and batch processing (D) doesn’t meet real-time needs.

---
