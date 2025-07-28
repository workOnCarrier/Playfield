## What data structure is most suitable for a time-series store with mostly monotonic timestamps?

* Sorted vector with binary search
* Efficient for appends (O(1)) and queries (O(log n))
* Offers excellent cache locality
* Not hash table, linked list, or heap

## How can you optimize query latency to meet a 50-microsecond budget with millions of points?

* Store data in a contiguous array for cache efficiency
* Use lock-free reads with versioned arrays
* Pre-allocate memory to avoid malloc overhead
* Not hash table or parallel threads

## How can you handle slightly out-of-order timestamps in a time-series store?

* Use a vector for monotonic appends
* Small balanced tree buffer for out-of-order inserts
* Periodically merge tree into vector
* Not full tree or hash table

## What is the most effective concurrency technique for a time-series store?

* Single-writer thread with read-only snapshots
* Minimizes contention for readers
* Not locking entire structure or fine-grained locks
* Not serializing all operations

## How can you store 100 million points within a 512 MB memory limit?

* Delta encoding for timestamps
* Quantization for values
* Use 32-bit types if ranges allow
* Not 64-bit types or linked list

## Which data structure supports efficient deletion of old data in a sliding window?

* Ring buffer for efficient head advancement
* Not hash table or priority queue
* Not unsorted vector
* Ideal for 24-hour window

## How can you implement `get_latest_before_or_equal(timestamp)` efficiently?

* Binary search with `upper_bound` and step back
* O(log n) with good locality
* Not linear search or hash table
* Not linked list traversal

## Why is a contiguous array preferred over a balanced tree for frequent queries?

* Better cache locality due to sequential access
* Not O(1) insertions or automatic out-of-order handling
* Not less memory usage
* Reduces cache misses

## Which compression technique suits a time-series store with mostly increasing timestamps?

* Delta encoding for timestamps
* Stores differences, not full values
* Not run-length or Huffman encoding
* Not Lempel-Ziv for entire dataset

## How can you test a time-series store under trading-like load?

* Generate mostly increasing timestamps with slight out-of-order
* Insert at high rate and measure query latency
* Test sliding window deletion and concurrency
* Not random timestamps or single-threaded

## How would you design a time-series store for fast insertions and queries?

* Use a sorted vector with binary search
* Append for monotonic timestamps
* Binary insert for out-of-order
* Optimize for cache efficiency

## How can you support deletion of old data in a sliding window?

* Use a ring buffer to advance head pointer
* Maintain moving start index in array
* Erase old keys in balanced tree
* Efficient for 24-hour retention

## How would you handle multiple fields per timestamp (e.g., OHLC, volume)?

* Use a struct of arrays for each field
* Keep columns contiguous for cache efficiency
* Query index returns all fields
* Not a single array or tree

## What is a Python implementation of a time-series store?

* Uses a sorted list with binary search
* Supports insert, query, and expiry
* Thread-safe with a lock
* Below is a Python solution with example usage

<xaiArtifact artifact_id="731abb8f-5760-464c-b145-426474684b37" artifact_version_id="e0672bf9-8178-4f4d-a6a3-6b318bb3df65" title="time_series_store.py" contentType="text/python">

```python

import threading
import bisect

class TimeSeriesStore:
    def __init__(self):
        self.points = []  # List of (timestamp, value) tuples
        self.lock = threading.Lock()

    def insert(self, timestamp, value):
        with self.lock:
            if not self.points or timestamp >= self.points[-1][0]:
                self.points.append((timestamp, value))
            else:
                # Binary insert for out-of-order
                index = bisect.bisect_left([p[0] for p in self.points], timestamp)
                self.points.insert(index, (timestamp, value))

    def get_latest_before_or_equal(self, timestamp):
        with self.lock:
            if not self.points:
                return None
            index = bisect.bisect_right([p[0] for p in self.points], timestamp) - 1
            if index < 0:
                return None
            return self.points[index]

    def expire_before(self, cutoff):
        with self.lock:
            index = bisect.bisect_left([p[0] for p in self.points], cutoff)
            self.points = self.points[index:]

    def size(self):
        with self.lock:
            return len(self.points)
```

# Example usage

```python
if __name__ == "__main__":
    store = TimeSeriesStore()
    store.insert(1000, 10.5)
    store.insert(2000, 11.0)
    store.insert(1500, 10.8)  # Out-of-order

    result = store.get_latest_before_or_equal(1600)
    print(f"Latest <= 1600: ts={result[0]}, value={result[1]}") if result else print("None")

    store.expire_before(1500)
    print(f"Size after expiry: {store.size()}")
    
```


## How to create anki from this markdown file

* mdanki 06_distributed_ts_store_anki.md 06_distributed_ts_store_anki.apkg --deck "Collaborated::CodeInterview::SystemDesign::06_DistributedTsStore"
