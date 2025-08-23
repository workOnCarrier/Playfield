#ifndef POOL_ALLOCATOR_H
#define POOL_ALLOCATOR_H

#include <atomic>
#include <cstddef>
#include <memory>
#include <new>
#include <stdexcept>

class LockFreePool {
    struct Node {
        Node* next;
    };

    std::atomic<Node*> head_;
    void* buffer_;
    size_t blockSize_;
    size_t capacity_;

public:
    LockFreePool(size_t blockSize, size_t capacity)
        : buffer_(nullptr), blockSize_(blockSize), capacity_(capacity) 
    {
        if (blockSize_ < sizeof(Node)) {
            blockSize_ = sizeof(Node);
        }

        buffer_ = ::operator new(blockSize_ * capacity_);
        char* start = static_cast<char*>(buffer_);
        Node* prev = nullptr;
        for (size_t i = 0; i < capacity_; ++i) {
            Node* node = reinterpret_cast<Node*>(start + i * blockSize_);
            node->next = prev;
            prev = node;
        }
        head_.store(prev, std::memory_order_release);
    }

    ~LockFreePool() {
        ::operator delete(buffer_);
    }

    void* allocate() {
        Node* oldHead = head_.load(std::memory_order_acquire);
        while (oldHead) {
            Node* next = oldHead->next;
            if (head_.compare_exchange_weak(oldHead, next,
                    std::memory_order_acq_rel, std::memory_order_acquire)) {
                return oldHead;
            }
        }
        throw std::bad_alloc();
    }

    void deallocate(void* p) {
        Node* node = reinterpret_cast<Node*>(p);
        Node* oldHead = head_.load(std::memory_order_relaxed);
        do {
            node->next = oldHead;
        } while (!head_.compare_exchange_weak(oldHead, node,
                    std::memory_order_release, std::memory_order_relaxed));
    }
};

// STL-compatible allocator
template <typename T>
class PoolAllocator {
public:
    using value_type = T;

    PoolAllocator(LockFreePool* pool = nullptr) noexcept : pool_(pool) {}

    template <class U>
    PoolAllocator(const PoolAllocator<U>& other) noexcept : pool_(other.pool_) {}

    T* allocate(std::size_t n) {
        if (n != 1) throw std::bad_alloc(); // fixed-size pool
        return static_cast<T*>(pool_->allocate());
    }

    void deallocate(T* p, std::size_t) noexcept {
        pool_->deallocate(p);
    }

    template <typename U>
    struct rebind {
        using other = PoolAllocator<U>;
    };

    LockFreePool* pool_;
};

template <class T, class U>
bool operator==(const PoolAllocator<T>& a, const PoolAllocator<U>& b) noexcept {
    return a.pool_ == b.pool_;
}
template <class T, class U>
bool operator!=(const PoolAllocator<T>& a, const PoolAllocator<U>& b) noexcept {
    return !(a == b);
}

#endif // POOL_ALLOCATOR_H
