import threading
from collections import deque
import time
import random

class BuggyEventProcessor:
    def __init__(self, event_handler):
        self.event_queue = deque()
        self.event_handler = event_handler
        self.stop_flag = False
        self.consumer_thread = None

    def start(self):
        self.stop_flag = False
        self.consumer_thread = threading.Thread(target=self._run)
        self.consumer_thread.start()

    def stop(self):
        self.stop_flag = True
        self.event_queue.append(None)  # Signal to exit
        print(f"\nProcessing Stopping\n")
        if self.consumer_thread:
            self.consumer_thread.join()

    def submit(self, event):
        if self.stop_flag:
            raise RuntimeError(f"Cannot submit event:{event} PROCESSOR STOPPED")
        self.event_queue.append(event)
        print(f"={self.stop_flag}, ", end="")

    def _run(self):
        while True:
            if not self.event_queue:
                continue
            event = self.event_queue.popleft()
            if event is None and self.stop_flag:
                break
            try:
                if event is not None:
                    self.event_handler(event)
            except Exception as e:
                print(f"Exception in event handler: {e}")
        print(f" __ EOP __ ")

# Example usage
if __name__ == "__main__":
    processed_events = []
    expected_events = []
    def process_event(event):
        processed_events.append(event)
        time.sleep(random.uniform(0.01, 0.02))  # Simulate processing

    processor = BuggyEventProcessor(process_event)
    processor.start()

    # Submit events from multiple threads
    def producer(id, count):
        try:
            for i in range(count):
                event = f"Event({id}):{id * count + i}"
                processor.submit(event)
                time.sleep(0.05)  # Simulate processing
                expected_events.append(event)
        except Exception as ex:
            print(f"stopping thread:{id} for exception:{ex}")
            return

    threads = [threading.Thread(target=producer, args=(i, 20)) for i in range(50)]
    for t in threads:
        t.start()
    time.sleep(0.5)  # Allow processing
    processor.stop()
    for t in threads:
        t.join()

    print(f"events: {processed_events}")
    print(f"\nProcessed {len(processed_events)} events")
    if len(expected_events) != len(processed_events):
        print(f"BUG: events lost")

