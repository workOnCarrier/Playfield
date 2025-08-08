#include <thread>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <vector>
#include <iostream>

std::queue<int> taskQueue;
std::mutex mtx;
std::condition_variable cv;
bool done = false;

void worker(int id) {
    while (!done) {
        if (!taskQueue.empty()) {
            int task = taskQueue.front();
            taskQueue.pop();
            std::cout << "Thread " << id << " processed task " << task << "\n";
        } else {
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
    }
}

int main() {
    std::vector<std::thread> threads;
    for (int i = 0; i < 4; i++) {
        threads.emplace_back(worker, i);
    }

    // Push some tasks
    for (int i = 0; i < 100; i++) {
        taskQueue.push(i);
    }

    std::this_thread::sleep_for(std::chrono::seconds(1));
    done = true;

    for (auto &t : threads) t.join();
}