* `unordered_map` internals (hash table, buckets, load factor)
* How it compares to `map` (red-black tree)
* Complexity trade-offs
* Iterator invalidation
* Thread-safety issues
* A small **C++ coding exercise** at the end with separate test cases

---

## **Interview Simulation – 20 Interactions**

**\[1]**
**Interviewer:** Can you explain what `unordered_map` in C++ is and how it stores data internally?
**Interviewee:** `unordered_map` is an associative container that stores key-value pairs in no particular order. Internally, it typically uses a **hash table** with **separate chaining** via linked lists or vectors in buckets to handle collisions.

---

**\[2]**
**Interviewer:** What’s the difference between separate chaining and open addressing in hash tables?
**Interviewee:**

* **Separate chaining:** Each bucket stores a list of key-value pairs that hash to the same index. Collisions are resolved by adding to the bucket's list.
* **Open addressing:** All elements are stored directly in the table array, and collisions are resolved by probing for the next available slot.

---

**\[3]**
**Interviewer:** How does `unordered_map` determine where to store a key-value pair?
**Interviewee:** It uses the key's **hash function** to compute a hash code, then applies `hash % bucket_count` to get the bucket index.

---

**\[4]**
**Interviewer:** What is the default hash function used for built-in types?
**Interviewee:** It’s `std::hash<T>`, which is specialized for built-in types like `int`, `std::string`, etc.

---

**\[5]**
**Interviewer:** Can you explain what the load factor is?
**Interviewee:** The load factor is **`size / bucket_count`**, where `size` is the number of elements. It measures how full the hash table is.

---

**\[6]**
**Interviewer:** What happens if the load factor exceeds the maximum load factor?
**Interviewee:** The `unordered_map` automatically **rehashes**—it increases the number of buckets and redistributes the elements, which is an expensive operation.

---

**\[7]**
**Interviewer:** How does `unordered_map` compare to `map` in terms of time complexity?
**Interviewee:**

* `unordered_map`: Average **O(1)** lookup, insert, erase; worst-case **O(n)** due to collisions.
* `map`: Always **O(log n)** due to its red-black tree implementation.

---

**\[8]**
**Interviewer:** And in terms of ordering?
**Interviewee:** `map` stores elements in **sorted key order**, while `unordered_map` stores them in **arbitrary bucket order**.

---

**\[9]**
**Interviewer:** Which one generally uses more memory?
**Interviewee:** `unordered_map` usually uses **more memory** because of the bucket array and extra collision-handling structures.

---

**\[10]**
**Interviewer:** What about iterator invalidation rules for `unordered_map`?
**Interviewee:**

* Inserting a new element **does not** invalidate iterators unless a rehash occurs.
* Erasing an element invalidates only iterators to that element.
* Rehashing invalidates **all** iterators.

---

**\[11]**
**Interviewer:** Can you control when rehashing happens?
**Interviewee:** Yes, by calling `reserve(n)` or `rehash(n)`, you can set the minimum number of buckets to avoid frequent rehashing.

---

**\[12]**
**Interviewer:** How thread-safe is `unordered_map`?
**Interviewee:** Reads are safe only if **no other thread modifies the container** concurrently. Any write operation must be externally synchronized.

---

**\[13]**
**Interviewer:** Suppose you have many hash collisions. What’s the impact?
**Interviewee:** Performance degrades toward **O(n)** for lookups and inserts, because all elements in the same bucket must be traversed sequentially.

---

**\[14]**
**Interviewer:** How can you improve hash performance?
**Interviewee:**

* Choose a good hash function that distributes keys evenly.
* Increase bucket count early.
* Avoid hash functions with patterns matching the data distribution.

---

**\[15]**
**Interviewer:** Can `unordered_map` store duplicate keys?
**Interviewee:** No, it enforces unique keys. For duplicates, you’d use `unordered_multimap`.

---

**\[16]**
**Interviewer:** How would you iterate over all buckets in an `unordered_map`?
**Interviewee:** You can use `bucket_count()` and `begin(bucket_index)` / `end(bucket_index)` to iterate bucket-wise.

---

**\[17]**
**Interviewer:** What’s the bucket interface useful for?
**Interviewee:** It allows analyzing distribution of elements among buckets—helpful for debugging poor hash distribution.

---

**\[18]**
**Interviewer:** Which operations might trigger rehashing?
**Interviewee:** Insertions that push load factor above the maximum, or explicit calls to `rehash` or `reserve`.

---

**\[19]**
**Interviewer:** Why might `map` be preferred over `unordered_map` in some cases?
**Interviewee:** If ordered traversal, predictable iteration order, or worst-case **O(log n)** performance is required, `map` is better.

---

**\[20]**
**Interviewer:** If you were to implement a minimal version of `unordered_map`, what’s the core data structure?
**Interviewee:** A **vector of buckets**, where each bucket is a linked list or vector of key-value pairs, along with a hash function and equality comparator.

---

## **C++ Example – Minimal Hash Table (`unordered_map`-like)**

**File:** `my_unordered_map.h`

```cpp
#pragma once
#include <vector>
#include <list>
#include <utility>
#include <functional>
#include <stdexcept>

template<typename Key, typename Value>
class MyUnorderedMap {
private:
    std::vector<std::list<std::pair<Key, Value>>> buckets;
    size_t num_elements;
    float max_load_factor;
    std::hash<Key> hasher;

    size_t get_bucket_index(const Key& key) const {
        return hasher(key) % buckets.size();
    }

    void rehash(size_t new_bucket_count) {
        std::vector<std::list<std::pair<Key, Value>>> new_buckets(new_bucket_count);
        for (auto &bucket : buckets) {
            for (auto &kv : bucket) {
                size_t idx = hasher(kv.first) % new_bucket_count;
                new_buckets[idx].push_back(kv);
            }
        }
        buckets.swap(new_buckets);
    }

    void check_load_factor_and_rehash() {
        float load_factor = static_cast<float>(num_elements) / buckets.size();
        if (load_factor > max_load_factor) {
            rehash(buckets.size() * 2);
        }
    }

public:
    MyUnorderedMap(size_t initial_buckets = 8, float max_load = 0.75f)
        : buckets(initial_buckets), num_elements(0), max_load_factor(max_load) {}

    void insert(const Key& key, const Value& value) {
        size_t idx = get_bucket_index(key);
        for (auto &kv : buckets[idx]) {
            if (kv.first == key) {
                kv.second = value; // update existing
                return;
            }
        }
        buckets[idx].push_back({key, value});
        ++num_elements;
        check_load_factor_and_rehash();
    }

    Value& at(const Key& key) {
        size_t idx = get_bucket_index(key);
        for (auto &kv : buckets[idx]) {
            if (kv.first == key) return kv.second;
        }
        throw std::out_of_range("Key not found");
    }

    bool contains(const Key& key) const {
        size_t idx = get_bucket_index(key);
        for (auto &kv : buckets[idx]) {
            if (kv.first == key) return true;
        }
        return false;
    }

    void erase(const Key& key) {
        size_t idx = get_bucket_index(key);
        for (auto it = buckets[idx].begin(); it != buckets[idx].end(); ++it) {
            if (it->first == key) {
                buckets[idx].erase(it);
                --num_elements;
                return;
            }
        }
    }

    size_t size() const { return num_elements; }
};
```

---

**File:** `test_my_unordered_map.cpp`

```cpp
#include "my_unordered_map.h"
#include <cassert>
#include <string>
#include <iostream>

int main() {
    MyUnorderedMap<std::string, int> map;

    // Insert and retrieve
    map.insert("apple", 3);
    map.insert("banana", 5);
    assert(map.at("apple") == 3);
    assert(map.at("banana") == 5);

    // Update value
    map.insert("apple", 10);
    assert(map.at("apple") == 10);

    // Contains check
    assert(map.contains("banana"));
    assert(!map.contains("cherry"));

    // Erase element
    map.erase("banana");
    assert(!map.contains("banana"));

    // Size check
    assert(map.size() == 1);

    // Stress test rehash
    for (int i = 0; i < 100; ++i) {
        map.insert("key" + std::to_string(i), i);
    }
    assert(map.size() == 101); // 100 + "apple"

    std::cout << "All tests passed.\n";
    return 0;
}
```

---

