## What is a common concurrency bug in a multithreaded event processor?

* Race condition when accessing shared data
* Occurs without proper synchronization
* Leads to inconsistent state or data corruption

## How can a race condition manifest in a thread-safe queue used in a trading system?

* Multiple threads accessing queue without locks
* Causes missed or duplicate events
* Leads to incorrect trade processing

## What is a potential deadlock scenario in a buggy event processor?

* Two threads holding locks while waiting for each other
* E.g., producer locks queue, consumer locks handler
* Results in system freeze

## How can you identify a missing lock in a buggy code during review?

* Look for shared data access without synchronization
* Check for mutex or condition variable absence
* Leads to race conditions in multithreaded code

## What is a symptom of incorrect condition variable usage in a producer-consumer system?

* Missed notifications causing thread stalls
* Consumer not woken after producer adds event
* Requires proper notify_all or notify_one

## How can you fix a race condition in a shared counter used in a trading system?

* Protect counter with a mutex
* Use atomic operations for simple increments
* Ensures consistent updates across threads

## What is a common mistake when implementing a thread-safe shutdown?

* Leads to lost events or incomplete processing
* Requires stop flag and queue flush

## How can you detect concurrency bugs during code review?

* Check for unsynchronized shared data access
* Verify proper lock usage and scope
* Look for condition variable misuse

## What is a risk of overusing locks in a trading system?

* Increased contention reduces throughput
* Leads to latency spikes under high load
* Requires balanced synchronization

## How can you test for concurrency bugs in a multithreaded event processor?

* Stress test with multiple producers and consumers
* Use tools like ThreadSanitizer for race detection
* Simulate high-frequency trading loads

## What is a common bug in a thread-safe queue implementation?

* Incorrect signaling with condition variables
* Leads to missed wake-ups or infinite waits

## How can you prevent deadlocks in a multithreaded system?

* Enforce consistent lock acquisition order
* Avoid nested locks where possible
* Prevents circular wait conditions

## What is a Python implementation of a corrected thread-safe event processor?

* Fixes race conditions with proper locking
* Ensures correct condition variable usage
* Supports graceful shutdown
* Below is a Python solution with example usage

<xaiArtifact artifact_id="936afd4d-600d-4a51-b7ca-a23e14b39ef2" artifact_version_id="65da6d8e-2a34-45ec-8ad5-093b7ea0e40b" title="thread_safe_event_processor.py" contentType="text/python">

```python
import threading
import queue
import time

class ThreadSafeEventProcessor:
    def __init__(self, event_handler):
        self.event_queue = queue.Queue()
        self.event_handler = event_handler
        self.stop_flag = False
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.consumer_thread = None

    def start(self):
        with self.lock:
            self.stop_flag = False
        self.consumer_thread = threading.Thread(target=self._run)
        self.consumer_thread.start()

    def stop(self):
        with self.condition:
            self.stop_flag = True
            self.condition.notify_all()  # Wake consumer to check stop
        self.event_queue.put(None)  # Signal to exit
        if self.consumer_thread:
            self.consumer_thread.join()

    def submit(self, event):
        with self.condition:
            if self.stop_flag:
                raise RuntimeError("Cannot submit event after processor stopped")
            self.event_queue.put(event)
            self.condition.notify()  # Notify consumer of new event

    def _run(self):
        while True:
            with self.condition:
                while not self.stop_flag and self.event_queue.empty():
                    self.condition.wait()  # Wait for events or stop
                if self.stop_flag and self.event_queue.empty():
                    break
                event = self.event_queue.get()
                if event is None and self.stop_flag:
                    break
            try:
                if event is not None:
                    self.event_handler(event)
            except Exception as e:
                print(f"Exception in event handler: {e}")
            finally:
                self.event_queue.task_done()

# Example usage
if __name__ == "__main__":
    processed_events = []
    def process_event(event):
        time.sleep(0.01)  # Simulate processing
        processed_events.append(event)

    processor = ThreadSafeEventProcessor(process_event)
    processor.start()

    # Submit events from multiple threads
    def producer(id, count):
        for i in range(count):
            processor.submit(f"Event {id * count + i}")

    threads = [threading.Thread(target=producer, args=(i, 5)) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    time.sleep(0.5)  # Allow processing
    processor.stop()
    print(f"Processed {len(processed_events)} events")
    print(f"First few events: {processed_events[:5]}")

```
## How to create anki from this markdown file

* mdanki 13_buggy_code_review_anki.md 13_buggy_code_review_anki.apkg --deck "Collaborated::CodeInterview::SystemDesign::13_BuggyCodeReview"

