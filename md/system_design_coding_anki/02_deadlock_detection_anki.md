## How would you model a system for deadlock detection with N processes and M resource types?

* Use an allocation matrix `Alloc[N][M]` to show how many instances of each resource each process holds
* Use a request matrix `Req[N][M]` to indicate resources each process is waiting for
* Use an available vector `Avail[M]` to track free resource instances
* This model captures resource allocation and requests for deadlock analysis

## How can you detect a deadlock using the system model?

* Initialize `Work = Avail` and a boolean array `Finish[N]` set to `false` for processes with requests
* Find a process `P` where `Finish[P] == false` and `Req[P] <= Work` (component-wise)
* Simulate P finishing by adding its allocated resources to `Work` and setting `Finish[P] = true`
* Repeat until no such process exists; processes with `Finish[i] = false` are deadlocked

## Why does the deadlock detection algorithm ensure safety?

* Checks if a process’s request can be met with available resources (`Req[P] ≤ Work`)
* Simulates process completion, releasing resources to `Work`
* Ensures all processes can complete if a valid sequence exists
* Identifies deadlocks when no sequence allows completion

## What does it mean if `Finish[2]` and `Finish[4]` are false after the deadlock detection algorithm?

* Processes 2 and 4 are in a deadlock cycle
* They hold resources while waiting for others’ resources
* No allocation sequence allows them to proceed
* Indicates a circular wait condition

## How frequently should deadlock detection run in a high-frequency trading system?

* Run on-demand when a process waits abnormally long to reduce latency overhead
* Alternatively, run periodically (e.g., every few seconds) if deadlocks are rare
* On-demand is preferred in trading systems for performance
* Balances detection cost with system responsiveness

## What actions can be taken after detecting a deadlock in a trading system?

* Log and alert the deadlock for monitoring
* Abort or preempt a deadlocked process to break the cycle
* Cancel non-critical operations in trading systems
* Restart a worker to resolve the deadlock

## What is the difference between deadlock prevention, avoidance, and detection?

* Prevention: Design system to eliminate deadlock conditions (e.g., global lock order)
* Avoidance: Use algorithms like Banker’s to ensure safe resource allocation
* Detection: Allow deadlocks, then identify and recover from them
* Trading systems often use prevention and detection together

## How do fine-grained locks affect deadlock likelihood in a trading system?

* Reduce contention by allowing granular resource access
* Lower the chance of circular wait conditions
* Decrease deadlock likelihood when combined with consistent lock order
* Improve concurrency in trading systems

## Which is NOT one of the four necessary conditions for a deadlock?

* Mutual exclusion: Resources are held exclusively
* Hold and wait: Processes hold resources while waiting
* No preemption: Resources cannot be forcibly taken
* First-come, first-serve scheduling: Not a deadlock condition

## What does it mean if `Finish[i]` remains false after the deadlock detection algorithm?

* Process i is part of a deadlock cycle
* Its resource requests cannot be satisfied
* Not due to completed execution or lack of resources
* Indicates involvement in a circular wait

## What does the `Request` matrix represent in the system model?

* Shows resources each process still needs to complete
* Not the resources currently held (that’s the allocation matrix)
* Not the total available resources (that’s the available vector)
* Not the maximum resources a process can hold

## Which strategy is an example of deadlock prevention?

* Enforcing a global lock acquisition order to eliminate circular wait
* Not running a detection algorithm periodically (that’s detection)
* Not aborting a process (that’s recovery)
* Not using Banker’s algorithm (that’s avoidance)

## What is the Banker’s algorithm primarily used for?

* Avoiding deadlocks by ensuring safe resource allocation
* Not for detecting deadlocks in a running system
* Not for preventing deadlocks via lock ordering
* Not for recovering by preempting resources

## What is a potential recovery action after detecting a deadlock in a trading system?

* Abort one of the deadlocked processes to release resources
* Not increasing available resources (often not feasible)
* Not changing to priority-based scheduling
* Not merging processes into a single thread

## How do fine-grained locks affect deadlock likelihood?

* Decrease deadlock likelihood by reducing contention
* Do not increase deadlocks despite more locks
* Do not eliminate deadlocks entirely
* Have a significant effect, unlike no impact

## Why prefer on-demand deadlock detection in a high-frequency trading system?

* Uses fewer resources by running only when needed
* Not because periodic detection is too slow
* Not due to avoiding false positives
* Not because periodic detection requires more locks

## Why do processes P1, P2, P3, and P4 form a deadlock in the example?

* They form a circular wait for resources
* Not because they have no allocated resources
* Not because requests exceed total resources
* Not due to using fine-grained locks

## Which approach complements deadlock detection to minimize deadlocks in a trading system?

* Implementing a timeout mechanism for resource requests
* Not using a single global lock (increases contention)
* Not increasing resource types (adds complexity)
* Not running detection more frequently (doesn’t prevent)

## What is a Python implementation of the deadlock detection algorithm?

* Implements the matrix-based deadlock detection algorithm
* Uses allocation, request matrices, and available vector
* Simulates process completion to identify deadlocked processes
* Example matches the test case with 5 processes and 3 resources

<xaiArtifact artifact_id="c66e958f-38ef-441f-bde3-cd0f8ba316d4" artifact_version_id="8dc530a0-635d-4e48-af02-240fb29f2a4e" title="deadlock_detector.py" contentType="text/python">
class DeadlockDetector:
    def __init__(self, n, m):
        self.N = n  # Number of processes
        self.M = m  # Number of resource types
        self.allocation = [[0] * m for _ in range(n)]
        self.request = [[0] * m for _ in range(n)]
        self.available = [0] * m

    def set_allocation(self, pid, rid, val):
        self.allocation[pid][rid] = val

    def set_request(self, pid, rid, val):
        self.request[pid][rid] = val

    def set_available(self, rid, val):
        self.available[rid] = val

    def detect(self):
        work = self.available.copy()
        finish = [False] * self.N

        # Mark processes with no allocation and no requests as finished
        for i in range(self.N):
            no_alloc = all(self.allocation[i][j] == 0 for j in range(self.M))
            no_req = all(self.request[i][j] == 0 for j in range(self.M))
            if no_alloc and no_req:
                finish[i] = True

        # Run detection loop
        progress = True
        while progress:
            progress = False
            for i in range(self.N):
                if not finish[i] and self._can_proceed(i, work):
                    for j in range(self.M):
                        work[j] += self.allocation[i][j]
                    finish[i] = True
                    progress = True

        # Collect deadlocked processes
        deadlocked = [i for i in range(self.N) if not finish[i]]
        return deadlocked

    def _can_proceed(self, pid, work):
        return all(self.request[pid][j] <= work[j] for j in range(self.M))

# Example usage
if __name__ == "__main__":
    detector = DeadlockDetector(5, 3)

    # Allocation Matrix
    alloc = [
        [0, 1, 0],
        [2, 0, 0],
        [3, 0, 3],
        [2, 1, 1],
        [0, 0, 2]
    ]

    # Request Matrix
    req = [
        [0, 0, 0],
        [2, 0, 2],
        [0, 0, 1],
        [1, 0, 0],
        [0, 0, 2]
    ]

    # Available Vector
    avail = [0, 0, 0]

    # Set data
    for i in range(5):
        for j in range(3):
            detector.set_allocation(i, j, alloc[i][j])
            detector.set_request(i, j, req[i][j])
    for j in range(3):
        detector.set_available(j, avail[j])

    # Run detection
    deadlocked = detector.detect()
    if not deadlocked:
        print("✅ No deadlock detected.")
    else:
        print(f"⚠️ Deadlock detected! Processes: {' '.join(f'P{pid}' for pid in deadlocked)}")