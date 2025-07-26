##  What is a blocking bounded queue and where is it used?

* A fixed-capacity thread-safe queue
* `enqueue` blocks if the queue is full
* `dequeue` blocks if the queue is empty
* Used in trading systems to buffer market data between IO and processing threads

##  What concurrency issues must be handled in a blocking bounded queue?

* Mutual exclusion when accessing shared queue
* Correct signaling when items are added/removed
* Avoiding race conditions (e.g., missed notifications)
* Preventing deadlocks when producers and consumers block

##  What is the high-level design for a blocking bounded queue?

* Circular buffer for storage
* Mutex to protect shared state
* Two condition variables:
  1. `not_full` for producers
  2. `not_empty` for consumers

##  What data members are in the BlockingBoundedQueue class?

* `std::vector<T> buffer`
* Indexes: `head`, `tail`, and `count`
* `capacity` for max size
* Synchronization:
  1. `std::mutex mtx`
  2. `std::condition_variable not_full`, `not_empty`

##  How is `enqueue` implemented in C++?

* Locks mutex
* Waits while full
* Adds item to `tail`, increments `count`
* Notifies one waiting consumer

##  How is `dequeue` implemented in C++?

* Locks mutex
* Waits while empty
* Retrieves item from `head`, decrements `count`
* Notifies one waiting producer

##  What happens with multiple producers/consumers waiting?

* Only one waiting thread is notified on each enqueue or dequeue
* Prevents thundering herd problem
* Maintains fairness and efficiency

##  What happens if you spin instead of block?

* Leads to busy-waiting
* Wastes CPU cycles
* Blocking is better for general use
* Spinning may be acceptable in ultra-low latency trading systems

##  How does `condition_variable::wait` avoid lost wakeups?

* Uses predicate in wait: `wait(lock, [this]{ condition })`
* Predicate re-checked after wakeup
* Prevents missed or spurious wakeups

##  How would you test this in a multithreaded environment?

* Multiple producers and consumers
* Verify queue size and order
* Block producers when full, block consumers when empty
* Stress test with random sleeps

##  Python Implementation of BlockingBoundedQueue

```python
import threading
from collections import deque

class BlockingBoundedQueue:
    def __init__(self, capacity):
        self.capacity = capacity
        self.queue = deque()
        self.lock = threading.Lock()
        self.not_full = threading.Condition(self.lock)
        self.not_empty = threading.Condition(self.lock)

    def enqueue(self, item):
        with self.not_full:
            while len(self.queue) >= self.capacity:
                self.not_full.wait()
            self.queue.append(item)
            self.not_empty.notify()

    def dequeue(self):
        with self.not_empty:
            while not self.queue:
                self.not_empty.wait()
            item = self.queue.popleft()
            self.not_full.notify()
            return item
```

##  Why is `notify_one()` preferred in this context?

* Only one producer or consumer can make progress at a time
* Reduces CPU contention
* Minimizes context switches
* Ideal for high-performance trading systems

##  When would you use `notify_all()` instead?

* When shutting down the system (all threads should wake up)
* When a condition unblocks many waiters
* Useful in barrier-like synchronization
