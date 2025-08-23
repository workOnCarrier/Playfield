#include "objectPool.h"
#include <iostream>
#include <thread>
#include <vector>
#include <chrono>
#include <cassert>

// Example class to pool
struct MyResource {
    int value = 0;
    void reset() { value = 0; }
};

void singleThreadTest() {
    ObjectPool<MyResource> pool(3);
    assert(pool.available() == 3);
    {
        auto r1 = pool.acquire();
        auto r2 = pool.acquire();
        assert(pool.available() == 1);
        r1->value = 42;
        r2->value = 99;
    }
    // r1 and r2 returned automatically
    assert(pool.available() == 3);
    std::cout << "[PASS] singleThreadTest\n";
}

void multiThreadTest() {
    ObjectPool<MyResource> pool(5);
    const int threads = 10;
    std::vector<std::thread> workers;

    for (int i = 0; i < threads; ++i) {
        workers.emplace_back([&pool, i] {
            for (int j = 0; j < 50; ++j) {
                auto obj = pool.acquire();
                obj->value = i * 100 + j;
                std::this_thread::sleep_for(std::chrono::microseconds(100));
            }
        });
    }

    for (auto &t : workers) t.join();

    assert(pool.available() == pool.capacity());
    std::cout << "[PASS] multiThreadTest\n";
}

int main() {
    singleThreadTest();
    multiThreadTest();
    std::cout << "All tests passed!\n";
    return 0;
}
