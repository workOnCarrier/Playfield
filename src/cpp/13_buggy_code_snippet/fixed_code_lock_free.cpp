#include <atomic>
#include <thread>
#include <vector>
#include <iostream>
#include <cassert>

constexpr int MAX_THREADS = 16; // adjust as needed

// Simple hazard pointer implementation
struct HazardPointer {
    std::atomic<void*> ptr;
};
HazardPointer hazard_pointers[MAX_THREADS];

int get_hazard_index() {
    thread_local static int idx = -1;
    if (idx == -1) {
        static std::atomic<int> next{0};
        idx = next++;
        assert(idx < MAX_THREADS);
    }
    return idx;
}

template<typename T>
struct Node {
    T value;
    std::atomic<Node*> next;
    Node(T v) : value(v), next(nullptr) {}
};

template<typename T>
class LockFreeQueue {
public:
    LockFreeQueue() {
        Node<T>* dummy = new Node<T>(T());
        head.store(dummy);
        tail.store(dummy);
    }

    ~LockFreeQueue() {
        while (dequeue());
        delete head.load();
    }

    void enqueue(const T& value) {
        Node<T>* new_node = new Node<T>(value);
        while (true) {
            Node<T>* last = tail.load();
            Node<T>* next = last->next.load();
            if (last == tail.load()) {
                if (next == nullptr) {
                    if (last->next.compare_exchange_weak(next, new_node)) {
                        tail.compare_exchange_weak(last, new_node);
                        return;
                    }
                } else {
                    tail.compare_exchange_weak(last, next);
                }
            }
        }
    }

    bool dequeue(T* result = nullptr) {
        int hidx = get_hazard_index();
        while (true) {
            Node<T>* first = head.load();
            hazard_pointers[hidx].ptr.store(first);
            Node<T>* last = tail.load();
            Node<T>* next = first->next.load();
            if (first == head.load()) {
                if (first == last) {
                    if (next == nullptr) return false;
                    tail.compare_exchange_weak(last, next);
                } else {
                    if (result && next) *result = next->value;
                    if (head.compare_exchange_weak(first, next)) {
                        retire_node(first);
                        return true;
                    }
                }
            }
        }
    }

private:
    std::atomic<Node<T>*> head;
    std::atomic<Node<T>*> tail;

    void retire_node(Node<T>* node) {
        // Check if any hazard pointer points to this node
        for (int i = 0; i < MAX_THREADS; ++i) {
            if (hazard_pointers[i].ptr.load() == node) {
                // Defer deletion
                std::this_thread::yield();
                return;
            }
        }
        delete node;
    }
};

// Example usage:
int main() {
    LockFreeQueue<int> q;
    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back([&q, i] {
            for (int j = 0; j < 100; ++j) q.enqueue(i * 100 + j);
        });
    }
    for (auto& t : threads) t.join();

    int value;
    int count = 0;
    while (q.dequeue(&value)) {
        std::cout << value << " ";
        ++count;
    }
    std::cout << "\nTotal dequeued: " << count << std::endl;
}