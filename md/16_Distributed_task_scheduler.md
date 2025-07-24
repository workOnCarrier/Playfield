
### 🎯 **Interview Problem**

> **Design and implement a simplified Distributed Task Scheduler**
> Requirements:
>
> * Multiple worker nodes pull tasks from a central coordinator.
> * Tasks have priorities and execution deadlines.
> * The scheduler should support re-queuing failed tasks.
> * Workers should poll tasks efficiently without overloading the coordinator.
> * You can assume in-memory storage, but design in a way that can scale.
>
> **Follow-up will involve code sketches and reasoning about scaling and fault-tolerance.**

---

### 💬 **Simulation: 10 Interactions**

---

**1️⃣ Interviewer:**
Imagine you are tasked to design a distributed task scheduler for Uber’s finance infrastructure. Multiple worker nodes should be able to pull tasks, execute them, and report status back. How would you start approaching the problem?

**🧑‍💻 Interviewee:**
I’d start by decomposing the system into key components:

* **Task Coordinator Service** to manage task queues, priorities, and deadlines.
* **Worker Nodes** that poll tasks, execute them, and send results back.
* **Storage Layer** to persist tasks and statuses.
  At high-level: workers do **pull-based scheduling** to avoid coordinator overload. The coordinator exposes APIs: `GetNextTask()` and `ReportResult(taskId, status)`.

---

**2️⃣ Interviewer:**
Great. How would you handle **task prioritization** and **deadlines** in your design?

**🧑‍💻 Interviewee:**
I’d use a **priority queue** data structure in the coordinator. Each task entry has `(priority, deadline, taskId)`. The queue pops highest-priority, earliest-deadline tasks first. Internally, I might use a min-heap keyed by `(priority, deadline)` so we can efficiently fetch the next eligible task.

---

**3️⃣ Interviewer:**
Let’s talk about **fault tolerance**. If a worker picks up a task but crashes, how would you handle reassigning it?

**🧑‍💻 Interviewee:**
When a worker pulls a task, the coordinator marks it as **in-progress** with a lease time. If the worker doesn’t report completion before lease expiry, the coordinator re-enqueues the task back into the priority queue.
This requires:

* A `lastHeartbeat` timestamp or lease expiration per task.
* A background thread in the coordinator scanning for expired leases.

---

**4️⃣ Interviewer:**
How do you ensure that workers do not overwhelm the coordinator with requests when there are no tasks available?

**🧑‍💻 Interviewee:**
I’d implement **long polling** or **backoff strategies**:

* Worker calls `GetNextTask()` with a timeout. If no task is ready, the coordinator blocks or responds after a delay.
* Alternatively, use exponential backoff at the worker side to avoid hammering when the queue is empty.

---

**5️⃣ Interviewer:**
Can you sketch a basic interface in C++ for your coordinator’s main API?

**🧑‍💻 Interviewee:**
Sure, something like:

```cpp
struct Task {
    std::string id;
    int priority;
    std::chrono::steady_clock::time_point deadline;
    std::string payload;
};

class TaskCoordinator {
public:
    // Adds a new task
    void EnqueueTask(const Task& task);

    // Gets the next eligible task
    std::optional<Task> GetNextTask();

    // Worker reports result
    void ReportResult(const std::string& taskId, bool success);

private:
    // internal priority queue
};
```

---

**6️⃣ Interviewer:**
Good. Now assume you have **thousands of workers**. How would you scale the coordinator?

**🧑‍💻 Interviewee:**
I’d shard the task queues:

* Partition tasks by some key (e.g., task type or hash of ID) across multiple coordinator instances.
* Use a consistent hashing scheme so workers know which coordinator to query.
* A discovery service (like etcd or ZooKeeper) can maintain the mapping of shard → coordinator instance.

---

**7️⃣ Interviewer:**
What about **persistence**? If the coordinator crashes, how do we avoid losing tasks?

**🧑‍💻 Interviewee:**
Use a **durable backing store**:

* Write tasks to a persistent log (e.g., Kafka, or database) before acknowledging enqueue.
* Rebuild the in-memory priority queue on startup by replaying the log or reading the DB.
  This ensures durability and recovery from crashes.

---

**8️⃣ Interviewer:**
Can you show me a quick code snippet for using a priority queue in C++ with custom comparison for priority and deadline?

**🧑‍💻 Interviewee:**
Sure:

```cpp
struct TaskCompare {
    bool operator()(const Task& a, const Task& b) const {
        if (a.priority == b.priority)
            return a.deadline > b.deadline; // earlier deadline first
        return a.priority < b.priority; // higher priority first
    }
};

std::priority_queue<Task, std::vector<Task>, TaskCompare> pq;
```

---

**9️⃣ Interviewer:**
Imagine a worker crashes mid-task. How would you detect that without the worker explicitly telling you?

**🧑‍💻 Interviewee:**
Each worker should periodically send **heartbeats** while holding a task lease. The coordinator maintains a lease expiry time. If the current time > lease expiry without a heartbeat, the task is considered lost and re-queued.

---

**🔟 Interviewer:**
Finally, what additional metrics or observability would you add for operating this system in production?

**🧑‍💻 Interviewee:**
I’d track:

* Task queue length by priority.
* Average wait time before a task is picked.
* Task success/failure rate.
* Worker heartbeat health metrics.
* Lease expirations and task re-queues.
  These can feed into Prometheus/Grafana dashboards and alerting.

---

✅ **End of Interview Simulation (10 Interactions)**

If you want, I can also provide:
✅ A **C++ reference implementation** (coordinator + worker simulation)
✅ Separate **unit tests**
✅ A **scaling/fault-tolerance deep dive**
---

## 📌 **File 1: `TaskScheduler.h`**

```cpp
#pragma once
#include <string>
#include <queue>
#include <unordered_map>
#include <optional>
#include <chrono>
#include <mutex>
#include <condition_variable>

struct Task {
    std::string id;
    int priority;
    std::chrono::steady_clock::time_point deadline;
    std::string payload;
};

struct TaskCompare {
    bool operator()(const Task& a, const Task& b) const {
        if (a.priority == b.priority)
            return a.deadline > b.deadline; // earlier deadline first
        return a.priority < b.priority;      // higher priority first
    }
};

enum class TaskStatus {
    PENDING,
    IN_PROGRESS,
    COMPLETED,
    FAILED
};

class TaskScheduler {
public:
    TaskScheduler(std::chrono::milliseconds leaseDuration = std::chrono::milliseconds(5000))
        : leaseDuration_(leaseDuration) {}

    void EnqueueTask(const Task& task) {
        std::lock_guard<std::mutex> lock(m_);
        tasks_.push(task);
        status_[task.id] = TaskStatus::PENDING;
        cv_.notify_one();
    }

    std::optional<Task> GetNextTask() {
        std::unique_lock<std::mutex> lock(m_);
        // wait until task is available
        cv_.wait(lock, [&] { return !tasks_.empty(); });
        Task t = tasks_.top();
        tasks_.pop();
        status_[t.id] = TaskStatus::IN_PROGRESS;
        leaseExpiry_[t.id] = std::chrono::steady_clock::now() + leaseDuration_;
        return t;
    }

    void ReportResult(const std::string& taskId, bool success) {
        std::lock_guard<std::mutex> lock(m_);
        if (status_.find(taskId) == status_.end()) return;
        status_[taskId] = success ? TaskStatus::COMPLETED : TaskStatus::FAILED;
        leaseExpiry_.erase(taskId);
    }

    // Call periodically to requeue expired leases
    void RequeueExpiredLeases() {
        std::lock_guard<std::mutex> lock(m_);
        auto now = std::chrono::steady_clock::now();
        std::vector<std::string> expired;
        for (auto &kv : leaseExpiry_) {
            if (kv.second < now && status_[kv.first] == TaskStatus::IN_PROGRESS) {
                expired.push_back(kv.first);
            }
        }
        for (auto &id : expired) {
            // For simplicity, re-enqueue with same priority/payload
            Task t;
            t.id = id;
            t.priority = 1;
            t.deadline = std::chrono::steady_clock::now() + std::chrono::seconds(10);
            t.payload = "[requeued]";
            tasks_.push(t);
            status_[id] = TaskStatus::PENDING;
            leaseExpiry_.erase(id);
        }
        if (!expired.empty()) {
            cv_.notify_all();
        }
    }

    TaskStatus GetStatus(const std::string &id) {
        std::lock_guard<std::mutex> lock(m_);
        auto it = status_.find(id);
        if (it == status_.end()) return TaskStatus::FAILED;
        return it->second;
    }

private:
    std::priority_queue<Task, std::vector<Task>, TaskCompare> tasks_;
    std::unordered_map<std::string, TaskStatus> status_;
    std::unordered_map<std::string, std::chrono::steady_clock::time_point> leaseExpiry_;
    std::chrono::milliseconds leaseDuration_;
    std::mutex m_;
    std::condition_variable cv_;
};
```

---

## 📌 **File 2: `main.cpp`** (Example usage)

```cpp
#include "TaskScheduler.h"
#include <thread>
#include <iostream>
#include <vector>

void worker(TaskScheduler &sched, int workerId) {
    while (true) {
        auto taskOpt = sched.GetNextTask();
        if (!taskOpt.has_value()) continue;
        Task t = taskOpt.value();
        std::cout << "[Worker " << workerId << "] got task: " << t.id << "\n";
        // Simulate work
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        bool success = true; // simulate always success
        sched.ReportResult(t.id, success);
        std::cout << "[Worker " << workerId << "] finished task: " << t.id << "\n";
    }
}

int main() {
    TaskScheduler scheduler;

    // Launch some workers
    std::vector<std::thread> workers;
    for (int i = 0; i < 3; ++i) {
        workers.emplace_back(worker, std::ref(scheduler), i);
    }

    // Enqueue some tasks
    for (int i = 0; i < 5; ++i) {
        Task t;
        t.id = "task-" + std::to_string(i);
        t.priority = i % 3;
        t.deadline = std::chrono::steady_clock::now() + std::chrono::seconds(30);
        t.payload = "payload-" + std::to_string(i);
        scheduler.EnqueueTask(t);
    }

    // Run requeue checker periodically in main thread
    for (int i = 0; i < 3; ++i) {
        std::this_thread::sleep_for(std::chrono::seconds(1));
        scheduler.RequeueExpiredLeases();
    }

    for (auto &w : workers) {
        w.detach(); // In production you'd handle graceful shutdown
    }

    return 0;
}
```

---

## 📌 **File 3: `test_scheduler.cpp`** (Simple test cases)

```cpp
#include "TaskScheduler.h"
#include <cassert>
#include <iostream>

int main() {
    TaskScheduler scheduler;

    Task t1{"t1", 5, std::chrono::steady_clock::now() + std::chrono::seconds(5), "payload"};
    scheduler.EnqueueTask(t1);

    auto task = scheduler.GetNextTask();
    assert(task.has_value());
    assert(task->id == "t1");
    scheduler.ReportResult("t1", true);

    assert(scheduler.GetStatus("t1") == TaskStatus::COMPLETED);

    // Test requeue
    Task t2{"t2", 1, std::chrono::steady_clock::now() + std::chrono::seconds(1), "payload2"};
    scheduler.EnqueueTask(t2);

    auto task2 = scheduler.GetNextTask();
    assert(task2.has_value());
    assert(task2->id == "t2");
    // Do not report result, simulate lease expiry
    std::this_thread::sleep_for(std::chrono::milliseconds(6000));
    scheduler.RequeueExpiredLeases();
    auto task3 = scheduler.GetNextTask();
    assert(task3.has_value());
    std::cout << "Requeue test passed for task: " << task3->id << "\n";

    std::cout << "All tests passed.\n";
    return 0;
}
```

---

### ✅ **How to Build & Run**

```bash
g++ -std=c++17 -pthread main.cpp -o scheduler
./scheduler    # runs demo

g++ -std=c++17 -pthread test_scheduler.cpp -o test_scheduler
./test_scheduler    # runs unit tests
```

---

 I can also:
✅ Add gRPC or REST interfaces for real distributed deployment.
✅ Add persistent storage simulation (SQLite or RocksDB).
✅ Add metrics and logging.

---
### Multiple-Choice Questions

**1. What is the primary advantage of using a pull-based scheduling model in a distributed task scheduler?**  
a) It reduces the latency of task assignment.  
b) It prevents the coordinator from being overwhelmed by worker requests.  
c) It ensures tasks are executed in strict priority order.  
d) It eliminates the need for a priority queue.  

**2. In a distributed task scheduler, why is a lease mechanism used for task assignment?**  
a) To prioritize tasks based on their deadlines.  
b) To ensure tasks are not lost if a worker crashes.  
c) To reduce the number of tasks in the queue.  
d) To increase the throughput of the coordinator.  

**3. When implementing a priority queue for tasks with both priority and deadline, what data structure is most efficient?**  
a) Linked List  
b) Min-Heap  
c) Binary Search Tree  
d) Array with linear scan  

**4. How does long polling help in reducing coordinator overload in a task scheduler?**  
a) It increases the frequency of worker requests.  
b) It allows workers to wait for tasks without repeated requests.  
c) It ensures tasks are assigned in a round-robin fashion.  
d) It eliminates the need for a lease mechanism.  

**5. In a sharded task scheduler, what is the role of consistent hashing?**  
a) To encrypt task data for secure transmission.  
b) To distribute tasks evenly across coordinator instances.  
c) To prioritize tasks based on their hash value.  
d) To reduce the memory footprint of the priority queue.  

**6. What is a key benefit of using a durable backing store (e.g., Kafka or a database) in a task scheduler?**  
a) It reduces the latency of task execution.  
b) It ensures tasks are not lost during coordinator crashes.  
c) It eliminates the need for worker heartbeats.  
d) It simplifies task prioritization logic.  

**7. Why might exponential backoff be used by workers when polling for tasks?**  
a) To ensure tasks are processed in FIFO order.  
b) To reduce the frequency of requests when no tasks are available.  
c) To increase the priority of tasks in the queue.  
d) To detect worker crashes more quickly.  

**8. In a distributed task scheduler, what is the purpose of a discovery service (e.g., ZooKeeper)?**  
a) To execute tasks on behalf of workers.  
b) To maintain a mapping of task shards to coordinator instances.  
c) To store task execution results permanently.  
d) To monitor worker health in real-time.  

**9. What is a potential downside of requeuing failed tasks without a retry limit?**  
a) It can lead to infinite loops of task retries.  
b) It reduces the priority of other tasks.  
c) It increases the latency of task assignment.  
d) It eliminates the need for a lease mechanism.  

**10. Which metric would be most useful for monitoring the health of a distributed task scheduler in production?**  
a) Number of tasks executed per worker.  
b) Average CPU usage of the coordinator.  
c) Task queue length by priority.  
d) Number of HTTP requests to the discovery service.  

---

### Explanations for Each Question

**1. What is the primary advantage of using a pull-based scheduling model in a distributed task scheduler?**  
**Correct Answer: b) It prevents the coordinator from being overwhelmed by worker requests.**  
**Explanation:** In a pull-based model, workers request tasks from the coordinator when they are ready, allowing the coordinator to manage load efficiently. This contrasts with a push-based model, where the coordinator actively assigns tasks, potentially overwhelming itself if many workers are idle.

**2. In a distributed task scheduler, why is a lease mechanism used for task assignment?**  
**Correct Answer: b) To ensure tasks are not lost if a worker crashes.**  
**Explanation:** A lease mechanism assigns a task to a worker for a fixed duration. If the worker crashes and doesn’t report completion within the lease time, the coordinator reassigns the task, ensuring it isn’t lost.

**3. When implementing a priority queue for tasks with both priority and deadline, what data structure is most efficient?**  
**Correct Answer: b) Min-Heap**  
**Explanation:** A min-heap is ideal for a priority queue because it supports O(log n) insertion and removal of the highest-priority (or earliest-deadline) task. It efficiently handles custom comparisons, like prioritizing by (priority, deadline).

**4. How does long polling help in reducing coordinator overload in a task scheduler?**  
**Correct Answer: b) It allows workers to wait for tasks without repeated requests.**  
**Explanation:** Long polling lets workers wait for a response from the coordinator until a task is available or a timeout occurs, reducing the number of unnecessary requests compared to frequent polling.

**5. In a sharded task scheduler, what is the role of consistent hashing?**  
**Correct Answer: b) To distribute tasks evenly across coordinator instances.**  
**Explanation:** Consistent hashing maps tasks to coordinator instances based on a hash of task IDs, ensuring even distribution and minimal reassignment when coordinators are added or removed.

**6. What is a key benefit of using a durable backing store (e.g., Kafka or a database) in a task scheduler?**  
**Correct Answer: b) It ensures tasks are not lost during coordinator crashes.**  
**Explanation:** A durable backing store persists tasks, allowing the coordinator to rebuild its state (e.g., the priority queue) after a crash by replaying the log or reading the database.

**7. Why might exponential backoff be used by workers when polling for tasks?**  
**Correct Answer: b) To reduce the frequency of requests when no tasks are available.**  
**Explanation:** Exponential backoff increases the delay between retry attempts when no tasks are available, preventing workers from overwhelming the coordinator with frequent requests.

**8. In a distributed task scheduler, what is the purpose of a discovery service (e.g., ZooKeeper)?**  
**Correct Answer: b) To maintain a mapping of task shards to coordinator instances.**  
**Explanation:** A discovery service tracks which coordinator instance handles each shard, allowing workers to locate the correct coordinator for their task requests in a sharded system.

**9. What is a potential downside of requeuing failed tasks without a retry limit?**  
**Correct Answer: a) It can lead to infinite loops of task retries.**  
**Explanation:** Without a retry limit, a task that repeatedly fails (e.g., due to a bug) could be requeued indefinitely, consuming resources and potentially blocking other tasks.

**10. Which metric would be most useful for monitoring the health of a distributed task scheduler in production?**  
**Correct Answer: c) Task queue length by priority.**  
**Explanation:** Monitoring task queue length by priority helps identify bottlenecks, backlogs, or imbalances in task processing, providing critical insight into the system’s health and performance.

---


