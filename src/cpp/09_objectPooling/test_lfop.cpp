#include "objectPoolLockFree.h"
#include <thread>
#include <vector>
#include <chrono>
#include <iostream>
#include <cassert>

struct MyRes {
    int value = 0;
    void display(){
        std::cout << "\t" << value ;
    }
};

void benchmark(size_t poolSize, size_t threads, size_t iterationsPerThread) {
    LockFreeObjectPool<MyRes> pool(poolSize);
    std::cout << "Capacity: " << pool.capacity() << "\n";

    auto start = std::chrono::high_resolution_clock::now();

    if(true) {std::vector<std::thread> workers;
    for (size_t t = 1; t <= threads; ++t) {
        workers.emplace_back([&pool, iterationsPerThread, t, poolSize] {
            for (size_t i = 0; i < iterationsPerThread; ++i) {
                auto obj = pool.acquire();
                if (obj) {
                    obj->value = static_cast<int>(t * poolSize + i);
                    // simulate small work
                    // no sleep for pure throughput
                } else {
                    // pool exhausted: this is okay if threads > pool size
                }
            }
        });
    }
    for (auto& th : workers) th.join();
    }

    auto end = std::chrono::high_resolution_clock::now();
    double seconds = std::chrono::duration<double>(end - start).count();

    size_t totalOps = threads * iterationsPerThread;
    std::cout << "Total operations: " << totalOps << "\n";
    std::cout << "Time: " << seconds << "s\n";
    std::cout << "Throughput: " << (totalOps / seconds) << " ops/sec\n";
    std::cout << "Approx available after run: " << pool.approximateAvailable() << "\n";
}

int main() {
    // Single-thread sanity test
    {
        LockFreeObjectPool<MyRes> pool(4);
        auto a = pool.acquire();
        auto b = pool.acquire();
        assert(pool.approximateAvailable() == 2);
        a.reset();
        b.reset();
        assert(pool.approximateAvailable() == 4);
        std::cout << "[PASS] basic sanity\n";
    }

    // Benchmark with heavy multithreading
    benchmark(1000, 8, 500000);
    // benchmark(1000, 10, 201);

    return 0;
}
