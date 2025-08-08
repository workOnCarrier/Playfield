## What is the primary data structure used in an unordered map?

* Array of buckets with linked lists for collisions
* Uses hash function to map keys to buckets
* Not binary search tree or sorted array
* Enables O(1) average-case operations

## How does an unordered map handle hash collisions?

* Chaining with linked lists in each bucket
* Alternatively, open addressing with probing
* Not ignoring collisions or resizing
* Maintains correctness under high load

## What is the average time complexity for get and put operations in an unordered map?

* O(1) average case with good hash function
* O(n) worst case with many collisions
* Not O(log n) or O(n log n)
* Depends on load factor and hash quality

## What is the role of the load factor in an unordered map?

* Ratio of entries to buckets
* Triggers resize when exceeded (e.g., 0.75)
* Controls collision frequency
* Not for memory allocation or thread-safety

## How does resizing work in an unordered map?

* Allocate new bucket array (usually doubled size)
* Rehash all existing keys to new buckets
* Not incremental resizing or bucket merging
* Maintains low collision rate

## What is a key challenge in making an unordered map thread-safe?

* Synchronizing access to shared buckets
* Preventing race conditions on inserts/deletes
* Not maintaining key order or reducing memory
* Requires locks or lock-free techniques

## How can you make an unordered map thread-safe for concurrent reads and writes?

* Use a mutex to protect bucket operations
* Alternatively, read-write locks per bucket
* Not thread-local maps or no synchronization
* Balances concurrency and correctness

## What is a potential downside of using a global mutex in a thread-safe unordered map?

* Reduced concurrency due to serialized access
* Increases contention under high load
* Not memory overhead or incorrect results
* Impacts performance in trading systems

## How can you optimize an unordered map for a high-frequency trading system?

* Use high-quality hash function to minimize collisions
* Keep load factor low to reduce bucket conflicts
* Pre-allocate buckets for expected size
* Not sorted keys or dynamic arrays

## What is a common bug in a custom unordered map implementation?

* Poor hash function causing excessive collisions
* Leads to O(n) performance degradation
* Not memory leaks or incorrect ordering
* Requires uniform key distribution

## How would you test an unordered map implementation?

* Stress test with high insert/delete rates
* Verify correctness under concurrent access
* Measure performance with varying load factors
* Not single-threaded or small datasets

## What is the impact of a high load factor in an unordered map?

* Increased collisions and longer bucket chains
* Degrades performance to O(n) in worst case
* Not memory exhaustion or deadlocks
* Triggers earlier resizing

## How can you extend an unordered map to support custom key types?

* Define custom hash function for key type
* Ensure hash distributes keys uniformly
* Not modify bucket structure or use trees
* Maintains O(1) average performance

## What is a Python implementation of a simplified thread-safe unordered map?

* Uses array of buckets with chaining
* Thread-safe with a global mutex
* Supports get and put operations
* Below is a Python solution with example usage

<xaiArtifact artifact_id="6ec9903c-a184-4eaf-a309-520fb96541a4" artifact_version_id="be06926b-1445-4ebb-88a7-c602b582b004" title="unordered_map.py" contentType="text/python">

```python
import threading
from typing import Any, Optional

class UnorderedMap:
    class Node:
        def __init__(self, key: Any, value: Any, next=None):
            self.key = key
            self.value = value
            self.next = next

    def __init__(self, initial_size: int = 16, load_factor: float = 0.75):
        self.size = initial_size
        self.load_factor = load_factor
        self.buckets = [None] * initial_size
        self.count = 0
        self.lock = threading.Lock()

    def _hash(self, key: Any) -> int:
        # Simple hash function for demonstration
        return hash(key) % self.size

    def _resize(self):
        old_buckets = self.buckets
        self.size *= 2
        self.buckets = [None] * self.size
        self.count = 0
        for head in old_buckets:
            while head:
                self.put(head.key, head.value)
                head = head.next

    def put(self, key: Any, value: Any):
        with self.lock:
            if self.count / self.size >= self.load_factor:
                self._resize()
            index = self._hash(key)
            head = self.buckets[index]
            # Update existing key
            while head:
                if head.key == key:
                    head.value = value
                    return
                head = head.next
            # Insert new key
            self.buckets[index] = self.Node(key, value, self.buckets[index])
            self.count += 1

    def get(self, key: Any) -> Optional[Any]:
        with self.lock:
            index = self._hash(key)
            head = self.buckets[index]
            while head:
                if head.key == key:
                    return head.value
                head = head.next
            return None

# Example usage
if __name__ == "__main__":
    umap = UnorderedMap(initial_size=4)
    umap.put("symbol1", 150.0)
    umap.put("symbol2", 2800.0)
    umap.put("symbol1", 155.0)  # Update value
    print(umap.get("symbol1"))  # Output: 155.0
    print(umap.get("symbol3"))  # Output: None

    # Test concurrent access
    def worker(umap, key, value, iterations):
        for _ in range(iterations):
            umap.put(key, value)
            umap.get(key)

    threads = [
        threading.Thread(target=worker, args=(umap, f"key{i}", i, 100))
        for i in range(3)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(umap.get("key1"))  # Output: 1

```


## How to create anki from this markdown file

* mdanki 21_unordered_map_anki.md 21_unordered_map_anki.apkg --deck "Collaborated::CodeInterview::SystemDesign::21_UnorderedMap"
