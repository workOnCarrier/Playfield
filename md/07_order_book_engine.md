### 📌 **Interview Problem**

> **Design and implement a simplified in‑memory order book engine.**
>
> The engine supports:
>
> * `AddOrder(orderId, side, price, quantity)`
> * `CancelOrder(orderId)`
> * `Match()` → matches best bid and best ask while possible.
>
> **Constraints:**
>
> * `orderId` is unique.
> * Matching happens at the best price (highest bid with lowest ask).
> * Matching reduces quantities; if an order is fully matched, it is removed.
> * The data structure must allow:
>
>   * O(log n) insert
>   * O(log n) cancel
>   * O(1) query for best bid/ask
>
> **Discuss tradeoffs and implement core methods.**

---

### 🎭 **Simulation: Interviewer (I) vs Interviewee (E)**

#### Interaction 1

**I:** Let’s start simple. How would you model the data structures for an order book that supports add, cancel, and best-price match?
**E:** I’d maintain two maps: a bid book (price → list of orders) and an ask book (price → list of orders). For fast best-price access, I’d use `std::map` in C++ (red‑black tree), where `begin()` gives the lowest price for asks, and `rbegin()` gives the highest price for bids.

---

#### Interaction 2

**I:** Why a `map` instead of a `unordered_map`?
**E:** Because we need price levels sorted for best-price queries. A balanced BST (`std::map`) gives O(log n) insert/erase and ordered traversal. `unordered_map` would not maintain sorted order, so best bid/ask would require O(n).

---

#### Interaction 3

**I:** What’s your plan to store individual orders at each price level?
**E:** Each price level can have a FIFO queue of orders (e.g., `std::list`). I’d also maintain an auxiliary `unordered_map<orderId, (side, price, iterator_in_list)>` for O(1) cancel by directly accessing the list node.

---

#### Interaction 4

**I:** Suppose I cancel an order. Walk me through the steps.
**E:**

1. Look up `orderId` in the hash map → get side, price, and iterator.
2. Erase it from the price-level list in O(1).
3. If that list becomes empty, erase the price level from the map in O(log n).
4. Remove entry from hash map.

---

#### Interaction 5

**I:** How would you implement `Match()` to match best bid and ask?
**E:**

* While best bid price ≥ best ask price:

  * Take front of bid queue and ask queue.
  * Determine trade quantity = `min(bid_qty, ask_qty)`.
  * Reduce both; pop if fully matched.
  * If queue empty → remove price level.

---

#### Interaction 6

**I:** Sounds good. What are the complexities for each operation?
**E:**

* **Add:** O(log n) to insert in map + O(1) push to list.
* **Cancel:** O(1) to find in hash + O(1) erase from list + O(log n) erase price level if needed.
* **Best bid/ask:** O(1) using `map::begin` or `map::rbegin`.
* **Match:** Each match is proportional to number of matched orders.

---

#### Interaction 7

**I:** Can you think of memory tradeoffs or optimizations?
**E:** The hash map duplicates references but gives O(1) cancel. Alternatively, we could store iterators directly in a custom intrusive list to reduce overhead. Also, we could pool allocate orders to avoid fragmentation.

---

#### Interaction 8

**I:** Suppose we scale to millions of orders. Any bottlenecks?
**E:** The `std::map` operations (log n) may become costly; we could consider a specialized skip list or a flat hash map with a separate heap to track best prices. We’d also need to ensure our locking strategy is efficient if multi-threaded.

---

#### Interaction 9

**I:** How would you handle partial matching on `AddOrder` itself?
**E:** On `AddOrder`, before adding to the book, we can immediately try to match against the opposite side if price crosses the spread. That avoids storing orders that are instantly executable.

---

#### Interaction 10

**I:** Nice. Could you sketch the key C++ structures you’d use?
**E:**

```cpp
struct Order {
    int id;
    int qty;
    double price;
};

std::map<double, std::list<Order>> bids; // price → FIFO orders
std::map<double, std::list<Order>> asks;
std::unordered_map<int, std::pair<char, std::pair<double, std::list<Order>::iterator>>> orderIndex;
// char: 'B' or 'A'
```

Then implement `AddOrder`, `CancelOrder`, and `Match` using these.

---

### 📂 **File 1: OrderBook.h**

```cpp
#pragma once
#include <map>
#include <list>
#include <unordered_map>
#include <stdexcept>
#include <iostream>

enum class Side { BUY, SELL };

struct Order {
    int id;
    int qty;
    double price;
};

class OrderBook {
public:
    // Add order, returns remaining qty if not fully matched
    void AddOrder(int orderId, Side side, double price, int quantity);

    // Cancel existing order
    void CancelOrder(int orderId);

    // Match best bid and ask until no overlap
    void Match();

    // Debug print current book
    void PrintBook() const;

private:
    // price → FIFO queue
    std::map<double, std::list<Order>> bids; // highest price last
    std::map<double, std::list<Order>> asks; // lowest price first
    // orderId → (side, price, iterator)
    struct OrderRef {
        Side side;
        double price;
        std::list<Order>::iterator it;
    };
    std::unordered_map<int, OrderRef> index;

    void matchOne();
};
```

---

### 📂 **File 2: OrderBook.cpp**

```cpp
#include "OrderBook.h"

void OrderBook::AddOrder(int orderId, Side side, double price, int quantity) {
    if (index.count(orderId)) {
        throw std::runtime_error("Duplicate orderId");
    }

    // If crosses the spread, match immediately
    if (side == Side::BUY) {
        while (quantity > 0 && !asks.empty() && asks.begin()->first <= price) {
            auto &askList = asks.begin()->second;
            auto &ask = askList.front();
            int traded = std::min(quantity, ask.qty);
            quantity -= traded;
            ask.qty -= traded;
            if (ask.qty == 0) {
                index.erase(ask.id);
                askList.pop_front();
                if (askList.empty()) {
                    asks.erase(asks.begin());
                }
            }
        }
    } else { // SELL
        while (quantity > 0 && !bids.empty() && bids.rbegin()->first >= price) {
            auto bidIt = std::prev(bids.end());
            auto &bidList = bidIt->second;
            auto &bid = bidList.front();
            int traded = std::min(quantity, bid.qty);
            quantity -= traded;
            bid.qty -= traded;
            if (bid.qty == 0) {
                index.erase(bid.id);
                bidList.pop_front();
                if (bidList.empty()) {
                    bids.erase(bidIt);
                }
            }
        }
    }

    if (quantity > 0) {
        Order o{orderId, quantity, price};
        if (side == Side::BUY) {
            auto &lst = bids[price];
            lst.push_back(o);
            index[orderId] = {Side::BUY, price, std::prev(lst.end())};
        } else {
            auto &lst = asks[price];
            lst.push_back(o);
            index[orderId] = {Side::SELL, price, std::prev(lst.end())};
        }
    }
}

void OrderBook::CancelOrder(int orderId) {
    auto it = index.find(orderId);
    if (it == index.end()) return; // ignore unknown id
    auto ref = it->second;
    if (ref.side == Side::BUY) {
        auto mapIt = bids.find(ref.price);
        if (mapIt != bids.end()) {
            mapIt->second.erase(ref.it);
            if (mapIt->second.empty()) {
                bids.erase(mapIt);
            }
        }
    } else {
        auto mapIt = asks.find(ref.price);
        if (mapIt != asks.end()) {
            mapIt->second.erase(ref.it);
            if (mapIt->second.empty()) {
                asks.erase(mapIt);
            }
        }
    }
    index.erase(it);
}

void OrderBook::Match() {
    while (!bids.empty() && !asks.empty()) {
        auto bestBidPrice = bids.rbegin()->first;
        auto bestAskPrice = asks.begin()->first;
        if (bestBidPrice < bestAskPrice) break;
        matchOne();
    }
}

void OrderBook::matchOne() {
    auto bidIt = std::prev(bids.end());
    auto &bidList = bidIt->second;
    auto &bid = bidList.front();

    auto askIt = asks.begin();
    auto &askList = askIt->second;
    auto &ask = askList.front();

    int traded = std::min(bid.qty, ask.qty);
    bid.qty -= traded;
    ask.qty -= traded;
    std::cout << "TRADE: price=" << ask.price << " qty=" << traded << "\n";

    if (bid.qty == 0) {
        index.erase(bid.id);
        bidList.pop_front();
        if (bidList.empty()) {
            bids.erase(bidIt);
        }
    }
    if (ask.qty == 0) {
        index.erase(ask.id);
        askList.pop_front();
        if (askList.empty()) {
            asks.erase(askIt);
        }
    }
}

void OrderBook::PrintBook() const {
    std::cout << "--- BIDS ---\n";
    for (auto it = bids.rbegin(); it != bids.rend(); ++it) {
        for (auto &o : it->second) {
            std::cout << "id=" << o.id << " p=" << o.price << " q=" << o.qty << "\n";
        }
    }
    std::cout << "--- ASKS ---\n";
    for (auto it = asks.begin(); it != asks.end(); ++it) {
        for (auto &o : it->second) {
            std::cout << "id=" << o.id << " p=" << o.price << " q=" << o.qty << "\n";
        }
    }
}
```

---

### 📂 **File 3: main\_test.cpp**

```cpp
#include "OrderBook.h"

int main() {
    OrderBook ob;

    ob.AddOrder(1, Side::BUY, 100.0, 50);
    ob.AddOrder(2, Side::BUY, 101.0, 30);
    ob.AddOrder(3, Side::SELL, 102.0, 40);
    ob.AddOrder(4, Side::SELL, 99.0, 20); // should match immediately with best bid

    ob.PrintBook();
    std::cout << "---- After first match ----\n";

    ob.Match(); // match remaining if any
    ob.PrintBook();

    std::cout << "Cancel order 1\n";
    ob.CancelOrder(1);
    ob.PrintBook();

    std::cout << "Add aggressive sell\n";
    ob.AddOrder(5, Side::SELL, 100.0, 50); // crosses bids
    ob.PrintBook();

    return 0;
}
```

---

### ✅ **How to Build & Run**

```bash
g++ -std=c++17 OrderBook.cpp main_test.cpp -o orderbook
./orderbook
```

---

I can also:
✅ add unit tests with a testing framework (like GoogleTest),
✅ add multithreading discussion (locks),
✅ or add more features (time priority, order types, etc.).

---

### Multiple-Choice Questions

**1. Why is a balanced binary search tree (like std::map in C++) suitable for storing price levels in an order book?**  
a) It provides O(1) insertion and deletion.  
b) It maintains sorted order for efficient best-price queries.  
c) It uses less memory than a hash map.  
d) It supports O(1) lookup by order ID.  

**2. What is the primary reason to use an auxiliary hash map for order cancellations?**  
a) To maintain sorted price levels.  
b) To enable O(1) lookup of order details by order ID.  
c) To store orders in FIFO order.  
d) To reduce memory usage for price levels.  

**3. In the context of an order book, what does "matching" refer to?**  
a) Adding a new order to the book.  
b) Pairing a bid and an ask order at compatible prices to execute a trade.  
c) Canceling an order from the book.  
d) Sorting orders by price and quantity.  

**4. Why is FIFO (First-In-First-Out) ordering important for orders at the same price level?**  
a) To ensure O(1) access to the best price.  
b) To maintain fairness by prioritizing earlier orders.  
c) To reduce memory overhead.  
d) To allow partial matching of orders.  

**5. What happens when an order is added that crosses the spread (e.g., a buy order with a price higher than the best ask)?**  
a) The order is rejected.  
b) The order is added to the book without matching.  
c) The order is partially or fully matched immediately with the opposite side.  
d) The order is stored in a separate queue for later matching.  

**6. What is the time complexity of querying the best bid or ask price in the described order book implementation?**  
a) O(1)  
b) O(log n)  
c) O(n)  
d) O(n log n)  

**7. If a price level becomes empty after canceling an order, what is the time complexity to remove it from a std::map?**  
a) O(1)  
b) O(log n)  
c) O(n)  
d) O(n log n)  

**8. What is a potential bottleneck when scaling an order book to handle millions of orders?**  
a) O(1) access to order details via hash map.  
b) O(log n) operations for inserting or removing price levels in a balanced tree.  
c) O(1) matching of orders at the best price.  
d) FIFO queue operations for same-price orders.  

**9. What is a possible optimization to reduce memory fragmentation in an order book?**  
a) Use a balanced binary search tree instead of a hash map.  
b) Store orders in a vector instead of a list.  
c) Use memory pooling for order objects.  
d) Replace FIFO queues with priority queues.  

**10. Why might immediate matching during AddOrder be beneficial?**  
a) It reduces the memory required for the order book.  
b) It prevents storing orders that can be executed immediately.  
c) It simplifies the cancellation process.  
d) It ensures all orders are sorted by time priority.  

---

### Review of Your Answers

**1. Why is a balanced binary search tree (like std::map in C++) suitable for storing price levels in an order book?**  
**Your Answer:** b) It maintains sorted order for efficient best-price queries.  
**Correct Answer:** b)  
**Explanation:** A balanced binary search tree (e.g., std::map in C++, implemented as a red-black tree) keeps price levels sorted, allowing O(1) access to the highest bid (via rbegin()) or lowest ask (via begin()). This is critical for efficient best-price queries in an order book. Option a) is incorrect because insertion and deletion are O(log n), not O(1). Option c) is false as memory usage depends on implementation, and option d) is irrelevant since order ID lookup is handled by a separate hash map.

**2. What is the primary reason to use an auxiliary hash map for order cancellations?**  
**Your Answer:** b) To enable O(1) lookup of order details by order ID.  
**Correct Answer:** b)  
**Explanation:** The auxiliary hash map (std::unordered_map) maps order IDs to their details (side, price, and iterator in the price-level list), enabling O(1) lookup for cancellations. This avoids searching through price levels, which would be O(n) or worse. Option a) is incorrect because sorting is handled by the tree, not the hash map. Option c) is unrelated to cancellations, and option d) is false as the hash map increases memory usage.

**3. In the context of an order book, what does "matching" refer to?**  
**Your Answer:** b) Pairing a bid and an ask order at compatible prices to execute a trade.  
**Correct Answer:** b)  
**Explanation:** Matching involves pairing a buy order (bid) with a sell order (ask) when the bid price is greater than or equal to the ask price, executing a trade at the agreed price. Option a) refers to adding orders, option c) to canceling, and option d) to a different process not specific to matching.

**4. Why is FIFO (First-In-First-Out) ordering important for orders at the same price level?**  
**Your Answer:** b) To maintain fairness by prioritizing earlier orders.  
**Correct Answer:** b)  
**Explanation:** FIFO ensures that orders at the same price level are processed in the order they were received, maintaining fairness in trade execution. This is standard in financial order books. Option a) is incorrect because FIFO doesn’t affect best-price access speed. Option c) is unrelated to FIFO, and option d) is true but not the primary reason.

**5. What happens when an order is added that crosses the spread (e.g., a buy order with a price higher than the best ask)?**  
**Your Answer:** c) The order is partially or fully matched immediately with the opposite side.  
**Correct Answer:** c)  
**Explanation:** An order crossing the spread (e.g., a buy order with price ≥ best ask) can be executed immediately against existing orders on the opposite side, reducing or eliminating the need to add it to the book. Option a) is incorrect as such orders are typically valid. Option b) ignores immediate matching, and option d) is not a standard practice.

**6. What is the time complexity of querying the best bid or ask price in the described order book implementation?**  
**Your Answer:** a) O(1)  
**Correct Answer:** a)  
**Explanation:** In a std::map, the best bid (highest price) is accessed via rbegin() and the best ask (lowest price) via begin(), both O(1) operations in a balanced binary search tree. Options b), c), and d) overestimate the complexity.

**7. If a price level becomes empty after canceling an order, what is the time complexity to remove it from a std::map?**  
**Your Answer:** b) O(log n)  
**Correct Answer:** b)  
**Explanation:** Removing a price level from a std::map (a red-black tree) involves finding the price (O(log n)) and erasing it (O(log n)). Thus, the operation is O(log n). Options a), c), and d) do not reflect the tree’s complexity.

**8. What is a potential bottleneck when scaling an order book to handle millions of orders?**  
**Your Answer:** b) O(log n) operations for inserting or removing price levels in a balanced tree.  
**Correct Answer:** b)  
**Explanation:** For millions of orders, the O(log n) operations (insertions or deletions in std::map) can become costly, especially under high-frequency trading. Option a) is incorrect because O(1) hash map operations are fast. Option c) is misleading as matching complexity depends on the number of matches, not a bottleneck. Option d) is incorrect as FIFO queue operations (e.g., push/pop) are O(1).

**9. What is a possible optimization to reduce memory fragmentation in an order book?**  
**Your Answer:** b) Store orders in a vector instead of a list.  
**Correct Answer:** c) Use memory pooling for order objects.  
**Explanation:** Memory pooling allocates order objects in contiguous blocks, reducing fragmentation compared to dynamic allocations in a list or vector. Option b) (using a vector) could reduce overhead slightly but doesn’t address fragmentation as effectively, since vectors still require resizing or reallocation. Option a) is unrelated to fragmentation, and option d) changes the ordering logic, not memory management.  
**Feedback:** Your choice of b) is understandable, as vectors are more contiguous than lists, but memory pooling is a more targeted optimization for fragmentation in high-frequency systems.

**10. Why might immediate matching during AddOrder be beneficial?**  
**Your Answer:** b) It prevents storing orders that can be executed immediately.  
**Correct Answer:** b)  
**Explanation:** Immediate matching during AddOrder executes orders that cross the spread, avoiding unnecessary storage and reducing book size. Option a) is secondary, as memory savings are a byproduct. Option c) is unrelated, and option d) is incorrect as time priority is enforced by FIFO, not immediate matching.

---

### Summary
**Score:** 9/10  
**Correct Answers:** 1, 2, 3, 4, 5, 6, 7, 8, 10  
**Incorrect Answer:** 9  

**Feedback:** You demonstrated a strong understanding of the order book concepts, including data structures, time complexities, and matching logic. The only miss was on question 9, where memory pooling is the preferred optimization for fragmentation over using a vector. Vectors can help with locality but don’t address the dynamic allocation overhead as effectively as pooling in high-performance systems.

---

### Next Steps
- generate additional questions to test other aspects of order book design (e.g., multithreading, advanced matching rules, or edge cases)?  
-  provide a deeper explanation of memory pooling or other optimizations.

