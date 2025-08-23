#ifndef OBJECT_POOL_H
#define OBJECT_POOL_H

#include <vector>
#include <stack>
#include <memory>
#include <mutex>
#include <condition_variable>
#include <stdexcept>

template <typename T>
class ObjectPool {
public:
    explicit ObjectPool(size_t size) {
        storage_.reserve(size);
        for (size_t i = 0; i < size; ++i) {
            storage_.emplace_back(std::make_unique<T>());
            freeStack_.push(storage_.back().get());
        }
    }

    // non-copyable
    ObjectPool(const ObjectPool&) = delete;
    ObjectPool& operator=(const ObjectPool&) = delete;

    // Acquire an object (blocks if none available)
    std::shared_ptr<T> acquire() {
        std::unique_lock<std::mutex> lock(mtx_);
        cv_.wait(lock, [this] { return !freeStack_.empty(); });

        T* obj = freeStack_.top();
        freeStack_.pop();

        // custom deleter will return object to pool
        auto deleter = [this](T* ptr) { this->release(ptr); };
        return std::shared_ptr<T>(obj, deleter);
    }

    size_t available() const {
        std::lock_guard<std::mutex> lock(mtx_);
        return freeStack_.size();
    }

    size_t capacity() const {
        return storage_.size();
    }

private:
    void release(T* obj) {
        // reset object state if needed
        // *obj = T(); // optional reinit if T has operator=

        std::lock_guard<std::mutex> lock(mtx_);
        freeStack_.push(obj);
        cv_.notify_one();
    }

    std::vector<std::unique_ptr<T>> storage_;
    std::stack<T*> freeStack_;
    mutable std::mutex mtx_;
    std::condition_variable cv_;
};

// STL-compatible allocator
template <typename T>
class PoolAllocator {
public:
    using value_type = T;

    PoolAllocator(ObjectPool<T>* pool = nullptr) noexcept : pool_(pool) {}

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

    ObjectPool<T>* pool_;
};

template <class T, class U>
bool operator==(const PoolAllocator<T>& a, const PoolAllocator<U>& b) noexcept {
    return a.pool_ == b.pool_;
}
template <class T, class U>
bool operator!=(const PoolAllocator<T>& a, const PoolAllocator<U>& b) noexcept {
    return !(a == b);
}

#endif // OBJECT_POOL_H
