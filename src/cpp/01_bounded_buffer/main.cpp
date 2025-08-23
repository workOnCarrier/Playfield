#include <iostream>
#include <thread>
#include <vector>
#include <chrono>
#include "blockingBoundedQueue.h"

void producer(BlockingBoundedQueue<int>& q, int id, int count) {
    for (int i = 0; i < count; ++i) {
        auto item = id * 1000 + i;
        q.enqueue(item); // unique value
        std::cout << "\t[Producer " << id << "] got: " << item << "\n";
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
}

void consumer(BlockingBoundedQueue<int>& q, int id, int totalToConsume) {
    for (int i = 0; i < totalToConsume; ++i) {
        int item = q.dequeue();
        // For demonstration, print consumed item
        std::cout << "[Consumer " << id << "] got: " << item << "\n";
        std::this_thread::sleep_for(std::chrono::milliseconds(15));
    }
}

int main() {
    const size_t capacity = 5;
    BlockingBoundedQueue<int> q(capacity);

    const int itemsPerProducer = 10;
    const int producerCount = 2;
    const int consumerCount = 2;

    std::vector<std::thread> producers;
    std::vector<std::thread> consumers;

    // Start producers
    for (int i = 1; i <= producerCount; ++i) {
        producers.emplace_back(producer, std::ref(q), i, itemsPerProducer);
    }

    // Start consumers
    for (int j = 1; j <= consumerCount; ++j) {
        consumers.emplace_back(consumer, std::ref(q), j, (itemsPerProducer * producerCount) / consumerCount);
    }

    // Join all threads
    for (auto& t : producers) t.join();
    for (auto& t : consumers) t.join();

    std::cout << "All done. Final queue size: " << q.size() << "\n";
    return 0;
}