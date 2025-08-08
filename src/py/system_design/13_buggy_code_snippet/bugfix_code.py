import threading
from collections import deque
import time
import sys
import random

class ThreadSafeEventProcessor:
    def __init__(self, event_handler):
        self.event_queue = deque()
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
        with self.lock:
            print(f"Processing Stopping")
            self.stop_flag = True
            self.condition.notify_all()  # Wake consumer to check stop
        self.event_queue.append(None)  # Signal to exit
        if self.consumer_thread:
            self.consumer_thread.join()

    def submit(self, event):
        with self.condition:
            if self.stop_flag:
                raise RuntimeError(f"Cannot submit event:{event} PROCESSOR STOPPED")
            self.event_queue.append(event)
            print(f"={self.stop_flag}, ", end="")
            self.condition.notify()  # Notify consumer of new event

    def _run(self):
        while True:
            with self.condition:
                while not self.stop_flag and len(self.event_queue) == 0:
                    self.condition.wait()  # Wait for events or stop
                if self.stop_flag and len(self.event_queue) == 0:
                    break
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
    sleep_time = sys.getswitchinterval()
    print(f"swith interval:{sleep_time}")
    def process_event(event):
        sys.getswitchinterval()
        time.sleep(0.01)  # Simulate processing
        processed_events.append(event)


    processor = ThreadSafeEventProcessor(process_event)
    processor.start()

    # Submit events from multiple threads
    def producer(id, count):
        try:
            for i in range(count):
                processor.submit(f"Event({id}):{id * count + i}")
                time.sleep(0.01)  # 
        except Exception as ex:
            print(f"stopping thread:{id} for exception:{ex}")
            return

    threads = [threading.Thread(target=producer, args=(i, 20)) for i in range(50)]
    for t in threads:
        t.start()
    time.sleep(0.1)  # Allow processing
    processor.stop()
    for t in threads:
        t.join()


    print(f"events: {processed_events}")
    print(f"Processed {len(processed_events)} events")

