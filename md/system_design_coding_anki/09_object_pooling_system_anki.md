## What is the primary purpose of an object pool in a high-performance system?

* To pre-allocate a set of reusable objects to avoid frequent allocations/deallocations
* To prevent heap fragmentation
* To reduce allocator overhead, ensuring predictable performance
* Critical in low-latency environments like high-frequency trading

## What data structure would you use to store objects in a C++ object pool?

* Pre-constructed objects wrapped in a structure tracking whether they’re free or in use
* A freelist (e.g., std::stack) or concurrent queue to manage available objects

## How would you reset an object’s state when it is released back to the pool?

* Call a reset method on the object or reassign default values
* Ensures no stale state leaks to the next user
* Destroying and reconstructing in place is possible but more expensive

## How would you handle concurrency in a thread-safe object pool?

* Use a lock (e.g., std::mutex) around the freelist for simplicity
* For lower contention, use a lock-free structure like std::atomic stack or concurrent_queue
* Alternatively, use per-thread sub-pools with occasional balancing

## What happens if all objects in the pool are in use when acquire() is called?

* The call may block until an object is released
* Alternatively, return nullptr or throw an exception to signal exhaustion
* In trading systems, size the pool large enough to avoid exhaustion under normal load

## How do you prevent memory leaks when returning objects to the pool?

* Expose objects via a custom smart pointer (e.g., std::shared_ptr)
* Use a custom deleter that calls release() instead of delete
* Ensures automatic return to the pool when the smart pointer goes out of scope

## What is a basic class template interface for an object pool in C++?

* template<typename T> class ObjectPool {
* public:
*     explicit ObjectPool(size_t size);
*     std::shared_ptr<T> acquire();
*     void release(T* obj);
* private:
*     std::vector<std::unique_ptr<T>> storage_;
*     std::stack<T*> freeList_;
*     std::mutex mtx_;
* };
* Acquire pops from freeList, release pushes back

## How does a custom deleter ensure automatic return in an object pool?

* Use a lambda: auto deleter = [this](T* obj) { this->release(obj); };
* Return std::shared_ptr<T>(obj, deleter);
* When refcount drops to zero, release() is called instead of freeing memory

## What is a concern with contention in a thread-safe object pool?

* A single global mutex can become a bottleneck under high contention
* Mitigate with lock-free stacks or pool-per-thread strategy with periodic transfer
* Prioritize correctness, then optimize for performance

## How would you test a thread-safe object pool, including a Python sample test implementation?

* Unit test single-thread acquire/release
* Stress test with multiple threads acquiring/releasing simultaneously
* Assert never exceeding capacity and all objects return to free state
* Test exception safety and object state reset

## Provide a Python sample implementation of an object pool.

```python
import threading
import unittest
class TestObject:
    def __init__(self): self.value = 0
    def reset(self): self.value = 0
class ObjectPool:
    def __init__(self, size, obj_type):
        self.storage = [obj_type() for _ in range(size)]
        self.free_list = list(range(size))
        self.in_use = set()
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
    def acquire(self):
        with self.condition:
            while not self.free_list:
                self.condition.wait()
            idx = self.free_list.pop()
            self.in_use.add(idx)
            return self.storage[idx]
    def release(self, obj):
        with self.condition:
            idx = next(i for i, o in enumerate(self.storage) if o is obj)
            if idx in self.in_use:
                self.in_use.remove(idx)
                self.free_list.append(idx)
                self.condition.notify()
    def available(self):
        with self.lock:
            return len(self.free_list)
    def capacity(self):
        return len(self.storage)

class TestObjectPool(unittest.TestCase):
    def setUp(self):
        self.pool = ObjectPool(3, TestObject)
    def test_single_thread_acquire_release(self):
        obj1 = self.pool.acquire()
        self.assertEqual(self.pool.available(), 2)
        self.assertEqual(self.pool.capacity(), 3)
        self.pool.release(obj1)
        self.assertEqual(self.pool.available(), 3)
    def test_exhaustion(self):
        objs = [self.pool.acquire() for _ in range(3)]
        self.assertEqual(self.pool.available(), 0)
        for obj in objs:
            self.pool.release(obj)
        self.assertEqual(self.pool.available(), 3)
    def test_concurrent_access(self):
        def worker(pool, results):
            for _ in range(10):
                obj = pool.acquire()
                obj.value += 1
                pool.release(obj)
        threads = [threading.Thread(target=worker, args=(self.pool, [])) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(self.pool.available(), 3)
        for obj in self.pool.storage:
            self.assertEqual(obj.value, 50)  # 5 threads * 10 increments each
    def test_blocking_on_empty(self):
        objs = [self.pool.acquire() for _ in range(3)]
        def try_acquire():
            self.pool.acquire()
        t = threading.Thread(target=try_acquire)
        t.start()
        self.pool.release(objs[0])
        t.join(timeout=1)
        self.assertFalse(t.is_alive())
        self.assertEqual(self.pool.available(), 2)

if __name__ == '__main__':
    unittest.main()
```

## How to create anki from this markdown file

* mdanki 09_object_pooling_system_anki.md 09_object_pooling_system_anki.apkg --deck "Collaborated::CodeInterview::SystemDesign::09_ObjectPooling"