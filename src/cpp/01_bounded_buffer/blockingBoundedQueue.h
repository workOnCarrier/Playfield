#ifndef BLOCKING_BOUNDED_QUEUE_H
#define BLOCKING_BOUNDED_QUEUE_H

#include <vector>
#include <mutex>
#include <condition_variable>

template<typename T>
class BlockingBoundedQueue {
public:
    explicit BlockingBoundedQueue(size_t cap)
        : buffer(cap), capacity(cap), head(0), tail(0), count(0) {}

    void enqueue(const T& item);
    T dequeue();
    size_t size();

private:
    std::vector<T> buffer;
    size_t capacity;
    size_t head;
    size_t tail;
    size_t count;

    std::mutex mtx;
    std::condition_variable not_full;
    std::condition_variable not_empty;
};

template<typename T>
void BlockingBoundedQueue<T>::enqueue(const T& item) {
    std::unique_lock<std::mutex> lock(mtx);
    not_full.wait(lock, [this]{ return count < capacity; });

    buffer[tail] = item;
    tail = (tail + 1) % capacity;
    ++count;

    not_empty.notify_one();
}

template<typename T>
T BlockingBoundedQueue<T>::dequeue() {
    std::unique_lock<std::mutex> lock(mtx);
    not_empty.wait(lock, [this]{ return count > 0; });

    T item = buffer[head];
    head = (head + 1) % capacity;
    --count;

    not_full.notify_one();
    return item;
}

template<typename T>
size_t BlockingBoundedQueue<T>::size() {
    std::lock_guard<std::mutex> lock(mtx);
    return count;
}

#endif // BLOCKING_BOUNDED_QUEUE_H
