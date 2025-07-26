## What is the primary purpose of an LRU (Least Recently Used) cache?

* Evict the least recently accessed items when capacity is exceeded
* Maintain a fixed-size cache optimized for temporal locality
* Ensure most recently used items remain available
* Not to store items indefinitely or prioritize highest value

## Which data structures achieve O(1) time complexity for get and put in a single-threaded LRU cache?

* Hash map for O(1) key lookup
* Doubly-linked list for O(1) node movement and eviction
* Not binary search tree, array, or priority queue
* Enables efficient tracking of recency order

## What is a major challenge in making an LRU cache thread-safe?

* Preventing race conditions during concurrent get and put operations
* Avoiding inconsistent map or list states
* Not ensuring O(n) time complexity or sorted keys
* Managing simultaneous node movements or evictions

## What is the simplest way to ensure thread-safety in a concurrent LRU cache?

* Use a global mutex to lock all operations
* Serializes access to prevent race conditions
* Not lock-free structures or atomic operations alone
* Not read-write locks for all gets

## What is a key trade-off of using a global mutex in a concurrent LRU cache?

* Reduced throughput due to serialized access
* Limits concurrency in high-thread scenarios
* Not increased memory usage or deadlocks
* Not inability to evict items

## How does dividing a concurrent LRU cache into shards improve performance?

* Allows concurrent operations on different shards
* Reduces contention with separate locks per shard
* Not eliminating synchronization or reducing memory
* Not guaranteeing global LRU eviction

## What is a potential downside of a segmented LRU cache?

* Eviction is approximate, not globally least-recently-used
* Each shard evicts locally, not across all shards
* Not O(n) time complexity or less memory
* Not inability to support concurrent access

## Why might a shared lock for get operations be insufficient in a concurrent LRU cache?

* Get modifies recency order, requiring an exclusive lock
* Updates list by moving accessed item to front
* Not because gets don’t access state
* Not due to deadlocks or concurrency with puts

## What is the most effective testing strategy for validating thread-safety of a concurrent LRU cache?

* Stress tests with multiple threads and tools like ThreadSanitizer
* Simulates real-world concurrency to detect race conditions
* Not single-threaded unit tests alone
* Not checking eviction policy in isolation

## Which optimization improves performance of a concurrent LRU cache in a high-QPS trading system?

* Lock striping with multiple shards
* Reduces contention for high concurrency
* Not single global lock or disabling eviction
* Not storing keys in a sorted array

## How would you design a single-threaded LRU cache?

* Use a hash map to map keys to list nodes
* Use a doubly-linked list to track recency order
* Move accessed or inserted nodes to head
* Evict from tail when capacity is exceeded

## What concurrency issues arise in a concurrent LRU cache without synchronization?

* Race conditions on linked list node movements
* Inconsistent hash map state during reads/writes
* Evictions removing nodes being accessed
* Requires locks to ensure thread-safety

## How does a segmented LRU cache work?

* Divide key space into N shards
* Each shard has its own LRU with separate lock
* Hash keys to determine shard
* Enables concurrent operations across shards

## What is a Python implementation of a thread-safe concurrent LRU cache?

* Uses a global lock for thread-safety
* Combines dictionary and doubly-linked list for O(1) operations
* Supports get and put with eviction at capacity
* Below is a Python solution with example usage

<xaiArtifact artifact_id="fd69a91c-b69b-43a8-94d3-e5035b802764" artifact_version_id="cfa94c23-5e7b-4136-b16c-749a28c2cf2a" title="concurrent_lru_cache.py" contentType="text/python">
from threading import Lock
from collections import OrderedDict

class ConcurrentLRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = OrderedDict()  # Acts as both hash map and doubly-linked list
        self.lock = Lock()

    def get(self, key):
        with self.lock:
            if key not in self.cache:
                return None
            # Move to end (most recently used)
            value = self.cache.pop(key)
            self.cache[key] = value
            return value

    def put(self, key, value):
        with self.lock:
            if key in self.cache:
                # Update existing key
                self.cache.pop(key)
            else:
                # Evict least recently used if at capacity
                if len(self.cache) >= self.capacity:
                    self.cache.popitem(last=False)
            # Insert as most recently used
            self.cache[key] = value

# Example usage
if __name__ == "__main__":
    cache = ConcurrentLRUCache(3)
    cache.put(1, "one")
    cache.put(2, "two")
    cache.put(3, "three")
    print(cache.get(1))  # Output: one
    cache.put(4, "four")  # Evicts key 2
    print(cache.get(2))  # Output: None
    print(len(cache.cache))  # Output: 3

## How to create anki from this markdown file

* mdanki 03_concurrent_lru_cache_anki.md 03_concurrent_lru_cache_anki.apkg --deck "Nitin::CodeInterview::SystemDesign::ConcurrentLruCache"