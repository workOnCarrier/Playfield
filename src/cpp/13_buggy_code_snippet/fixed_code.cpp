// thread_pool_fixed.cpp
#include <thread>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <vector>
#include <iostream>
#include <atomic>

class TaskSystem {
public:
    TaskSystem(size_t workerCount = std::thread::hardware_concurrency())
        : done(false)
    {
        for (size_t i = 0; i < workerCount; ++i) {
            workers.emplace_back(&TaskSystem::workerLoop, this, i);
        }
    }

    ~TaskSystem() {
        shutdown();
    }

    void pushTask(int task) {
        {
            std::lock_guard<std::mutex> lock(mtx);
            taskQueue.push(task);
        }
        cv.notify_one();
    }

    void shutdown() {
        {
            std::lock_guard<std::mutex> lock(mtx);
            done = true;
        }
        cv.notify_all();
        for (auto &t : workers) {
            if (t.joinable()) t.join();
        }
        workers.clear();
    }

private:
    void workerLoop(int id) {
        while (true) {
            int task;
            {
                std::unique_lock<std::mutex> lock(mtx);
                cv.wait(lock, [this] {
                    return !taskQueue.empty() || done;
                });

                if (done && taskQueue.empty()) {
                    return;
                }

                task = taskQueue.front();
                taskQueue.pop();
            }
            // Process the task outside of lock
            std::cout << "[Worker " << id << "] processed task " << task << "\n";
        }
    }

    std::queue<int> taskQueue;
    std::mutex mtx;
    std::condition_variable cv;
    std::vector<std::thread> workers;
    std::atomic<bool> done;
};