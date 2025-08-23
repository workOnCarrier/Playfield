#ifndef LOCKFREE_OBJECT_POOL_H
#define LOCKFREE_OBJECT_POOL_H

#include <atomic>
#include <memory>
#include <vector>
#include <cstddef>
#include <iostream>
#include <set>

template <typename T>
class LockFreeObjectPool {
private:
    struct Node {
        T obj;
        Node* next = nullptr;
    };

    std::vector<std::unique_ptr<Node>> storage_;
    std::atomic<Node*> head_;
    std::set<T*>     acquire_addresses_;
    std::set<T*>     release_addresses_;
    int                 exhaust_count_;

public:
    explicit LockFreeObjectPool(size_t size) : storage_(size) {
        for (size_t i = 0; i < size; ++i) {
            storage_[i] = std::make_unique<Node>();
        }
        // link them
        for (size_t i = 0; i < size - 1; ++i) {
            storage_[i]->next = storage_[i+1].get();
        }
        storage_[size-1]->next = nullptr;
        head_.store(storage_[0].get(), std::memory_order_relaxed);
    }

    // noncopyable
    LockFreeObjectPool(const LockFreeObjectPool&) = delete;
    LockFreeObjectPool& operator=(const LockFreeObjectPool&) = delete;

    std::shared_ptr<T> acquire() {
        Node* node = head_.load(std::memory_order_acquire);
        while (node) {
            Node* next = node->next;
            if (head_.compare_exchange_weak(node, next,
                    std::memory_order_acquire, std::memory_order_relaxed)) {
                // got a node
                auto deleter = [this](T* obj) { this->release(obj); };
                auto obj_add = &node->obj;
                if ( acquire_addresses_.find(obj_add) == acquire_addresses_.end()){
                    acquire_addresses_.insert(obj_add);
                }// else{ cout << }

                return std::shared_ptr<T>(obj_add, deleter);
            }
            // otherwise retry with updated node
        }
        std::cout << "\t pool exhausted" << ++exhaust_count_ << std::endl;
        return nullptr; // pool exhausted
    }

    size_t capacity() const { return storage_.size(); }

    size_t approximateAvailable() const {
        // Non‑atomic traversal for rough stats
        size_t count = 0;
        Node* curr = head_.load(std::memory_order_acquire);
        while (curr) { 
            ++count;
            curr = curr->next;
             // std::cout << count << " "; 
            }
        return count;
    }

private:
    void release(T* obj) {
        // find node from obj pointer (compute offset)
        Node* node = reinterpret_cast<Node*>(reinterpret_cast<char*>(obj) - offsetof(Node, obj));
            // obj->display();

        Node* oldHead = head_.load(std::memory_order_relaxed);
        if (oldHead == nullptr){std::cout  << "\tstarting from empty" << std::endl;}
        do {
            node->next = oldHead;
        } while (!head_.compare_exchange_weak(oldHead, node,
                    std::memory_order_release, std::memory_order_relaxed));
    }
};

#endif // LOCKFREE_OBJECT_POOL_H
