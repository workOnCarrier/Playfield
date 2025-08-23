#include "poolAllocator.h"
#include <map>
#include <chrono>
#include <iostream>
#include <random>

constexpr size_t N = 1'000'00; // 100k elements for demo

void benchmarkDefaultAllocator() {
    std::map<int,int> m;
    auto start = std::chrono::high_resolution_clock::now();
    for (size_t i = 0; i < N; ++i) {
        m.emplace(i, i*i);
    }
    auto end = std::chrono::high_resolution_clock::now();
    std::cout << "Default Allocator: "
              << std::chrono::duration<double, std::milli>(end-start).count()
              << " ms\n";
}

void benchmarkPoolAllocator() {
    // Preallocate enough for N nodes
    LockFreePool pool(sizeof(std::pair<const int,int>), N*2);

    using MapWithPool = std::map<int,int,std::less<int>,
        PoolAllocator<std::pair<const int,int>>>;

    MapWithPool m{std::less<int>(), PoolAllocator<std::pair<const int,int>>(&pool)};

    auto start = std::chrono::high_resolution_clock::now();
    for (size_t i = 0; i < N; ++i) {
        m.emplace(i, i*i);
    }
    auto end = std::chrono::high_resolution_clock::now();
    std::cout << "Pool Allocator: "
              << std::chrono::duration<double, std::milli>(end-start).count()
              << " ms\n";
}

int main() {
    benchmarkDefaultAllocator();
    benchmarkPoolAllocator();
}
