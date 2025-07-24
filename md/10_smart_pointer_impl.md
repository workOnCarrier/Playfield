##  **Context**

> **Problem:**
> Implement a simplified `SharedPtr<T>` from scratch.
> Requirements:
>
> * Manage the lifetime of a heap‑allocated object of type `T`.
> * Reference counting (thread‑safe not required, but you must justify trade‑offs).
> * Implement `operator*`, `operator->`, copy constructor, assignment, destructor.
> * Show how you would handle `use_count()`, `reset()`, and edge cases (self‑assignment, nullptr).
> * You are **not allowed to use `std::shared_ptr` or `std::unique_ptr` internally.**

---

### **Interaction**
**Interviewer (I)** and **Candidate (C)**
---

**1. I:**
At Jane Street or Morgan Stanley, we care about controlling object lifetimes under load.
Can you explain what a smart pointer is and why we need one instead of raw `T*`?

**C:**
Sure. A smart pointer is a C++ class that wraps a raw pointer and manages the resource’s lifecycle automatically—most commonly by reference counting or unique ownership.
Instead of manually `delete`‑ing memory, the smart pointer deletes the managed object when it’s no longer referenced, avoiding leaks and double‑frees.

---

**2. I:**
Good. Let’s say we need our own `SharedPtr<T>`. What’s the minimal data members you’d include?

**C:**
We’d need:

* A `T* ptr_` to hold the raw pointer,
* An `int* refCount_` to keep track of how many `SharedPtr` objects share ownership.

---

**3. I:**
Walk me through your copy constructor logic.

**C:**
When copying, I’d:

* Copy `ptr_` and `refCount_` from the source,
* Increment `(*refCount_)` since we have an additional owner.

---

**4. I:**
And destructor?

**C:**
On destruction:

* Decrement `(*refCount_)`,
* If it reaches zero, `delete ptr_` and `delete refCount_`.

---

**5. I:**
How about assignment operator? Any traps?

**C:**
Yes:

* Check for self‑assignment,
* Decrement the old ref count (and free if needed),
* Copy `ptr_` and `refCount_` from the right‑hand side,
* Increment the new `refCount_`.

---

**6. I:**
What about `reset()`? How would you implement that?

**C:**
`reset()` would:

* Decrement the current ref count (delete if zero),
* Point `ptr_` to `nullptr` and `refCount_` to a fresh count if we want to manage a new object, otherwise leave them null.

---

**7. I:**
Can your design handle `SharedPtr<int> p(nullptr);`?

**C:**
Yes, I’d initialize `ptr_` to `nullptr` and `refCount_` to a valid `new int(1)` or simply set `refCount_ = nullptr` and guard operations (like dereference) accordingly.

---

**8. I:**
Suppose two `SharedPtr` instances manage the same raw pointer but with different control blocks. What happens?

**C:**
That’s undefined behavior and breaks the design. A smart pointer must **always share the same control block** (i.e., `refCount_`). My implementation only shares ownership when constructed or assigned from another `SharedPtr`, not arbitrary raw pointers.

---

**9. I:**
Can you sketch the core implementation for me?

**C:**
Sure, here’s the skeleton:

```cpp
template<typename T>
class SharedPtr {
    T* ptr_;
    int* refCount_;
public:
    explicit SharedPtr(T* p = nullptr)
        : ptr_(p), refCount_(p ? new int(1) : nullptr) {}

    SharedPtr(const SharedPtr& other)
        : ptr_(other.ptr_), refCount_(other.refCount_) {
        if (refCount_) ++(*refCount_);
    }

    SharedPtr& operator=(const SharedPtr& other) {
        if (this != &other) {
            release();
            ptr_ = other.ptr_;
            refCount_ = other.refCount_;
            if (refCount_) ++(*refCount_);
        }
        return *this;
    }

    ~SharedPtr() { release(); }

    void release() {
        if (refCount_ && --(*refCount_) == 0) {
            delete ptr_;
            delete refCount_;
        }
    }

    T& operator*() const { return *ptr_; }
    T* operator->() const { return ptr_; }
    int use_count() const { return refCount_ ? *refCount_ : 0; }
};
```

---

**10. I:**
Nice! What would you improve if this were production code at Bloomberg or Jump Trading?

**I can also enhance by:
* Adding move semantics to avoid unnecessary increments,
* Useing a separate control block struct with deleter and allocator support,
* thread safety if shared across threads,
* Adding custom deleter support,
* Useing `std::atomic<int>` for ref count in multithreaded environments.
* A **full compilable implementation**,
* A **test driver file**,
* Or an **enhanced version with move semantics and custom deleters**.

---
## **clean, compilable C++17 solution**:

✅ A header/source file implementing `SharedPtr<T>`
✅ A separate test file with some example usage.

You can compile below files together with:

```bash
g++ -std=c++17 -Wall -Wextra -O2 shared_ptr.hpp test_shared_ptr.cpp -o test_shared_ptr
./test_shared_ptr
```

---

### 📌 **shared\_ptr.hpp** (implementation)

```cpp
#ifndef SHARED_PTR_HPP
#define SHARED_PTR_HPP

#include <iostream>

template<typename T>
class SharedPtr {
private:
    T* ptr_;         // managed object
    int* refCount_;  // reference counter

    void release() {
        if (refCount_) {
            --(*refCount_);
            if (*refCount_ == 0) {
                delete ptr_;
                delete refCount_;
            }
        }
    }

public:
    // default / explicit constructor
    explicit SharedPtr(T* ptr = nullptr)
        : ptr_(ptr), refCount_(ptr ? new int(1) : nullptr) {}

    // copy constructor
    SharedPtr(const SharedPtr& other)
        : ptr_(other.ptr_), refCount_(other.refCount_) {
        if (refCount_) {
            ++(*refCount_);
        }
    }

    // move constructor
    SharedPtr(SharedPtr&& other) noexcept
        : ptr_(other.ptr_), refCount_(other.refCount_) {
        other.ptr_ = nullptr;
        other.refCount_ = nullptr;
    }

    // copy assignment
    SharedPtr& operator=(const SharedPtr& other) {
        if (this != &other) {
            release();
            ptr_ = other.ptr_;
            refCount_ = other.refCount_;
            if (refCount_) {
                ++(*refCount_);
            }
        }
        return *this;
    }

    // move assignment
    SharedPtr& operator=(SharedPtr&& other) noexcept {
        if (this != &other) {
            release();
            ptr_ = other.ptr_;
            refCount_ = other.refCount_;
            other.ptr_ = nullptr;
            other.refCount_ = nullptr;
        }
        return *this;
    }

    // destructor
    ~SharedPtr() {
        release();
    }

    // modifiers
    void reset(T* newPtr = nullptr) {
        release();
        if (newPtr) {
            ptr_ = newPtr;
            refCount_ = new int(1);
        } else {
            ptr_ = nullptr;
            refCount_ = nullptr;
        }
    }

    // observers
    T* get() const { return ptr_; }
    int use_count() const { return refCount_ ? *refCount_ : 0; }
    T& operator*() const { return *ptr_; }
    T* operator->() const { return ptr_; }
    explicit operator bool() const { return ptr_ != nullptr; }
};

#endif // SHARED_PTR_HPP
```

---

###  **test\_shared\_ptr.cpp** (test cases)

```cpp
#include "shared_ptr.hpp"
#include <cassert>
#include <string>

struct Foo {
    int x;
    Foo(int v) : x(v) { std::cout << "Foo(" << v << ") constructed\n"; }
    ~Foo() { std::cout << "Foo(" << x << ") destroyed\n"; }
    void hello() { std::cout << "Hello from Foo(" << x << ")\n"; }
};

int main() {
    {
        // basic construction
        SharedPtr<Foo> sp1(new Foo(42));
        assert(sp1.use_count() == 1);
        sp1->hello();

        // copy constructor
        SharedPtr<Foo> sp2 = sp1;
        assert(sp1.use_count() == 2);
        assert(sp2.use_count() == 2);

        // move constructor
        SharedPtr<Foo> sp3 = std::move(sp2);
        assert(sp3.use_count() == 2);
        assert(sp1.use_count() == 2);

        // assignment
        SharedPtr<Foo> sp4;
        sp4 = sp1;
        assert(sp1.use_count() == 3);

        // reset
        sp4.reset();
        assert(sp1.use_count() == 2);
        assert(sp4.use_count() == 0);
        assert(!sp4);

        // reset to a new object
        sp4.reset(new Foo(99));
        assert(sp4.use_count() == 1);
        sp4->hello();
    }
    // all objects should be destroyed here
    std::cout << "All tests passed.\n";
    return 0;
}
```

---

### ✅ **Output Example**

When you run `./test_shared_ptr` you should see:

```
Foo(42) constructed
Hello from Foo(42)
Foo(99) constructed
Hello from Foo(99)
Foo(99) destroyed
Foo(42) destroyed
All tests passed.
```

further enhancements can be to:
* Add **thread-safe ref counting** with `std::atomic<int>`,
* Add **custom deleters**,
* Add **weak pointer support**.

---


### Multiple Choice Questions

**1. What is the primary purpose of a `SharedPtr<T>` smart pointer?**  
a) To ensure exclusive ownership of a resource  
b) To automatically manage the lifetime of a heap-allocated object via reference counting  
c) To prevent copying of the managed object  
d) To provide thread-safe memory allocation  

**2. Why is a separate `int* refCount_` used instead of an `int refCount_` in the `SharedPtr` implementation?**  
a) To allow multiple `SharedPtr` instances to share the same reference count  
b) To reduce memory usage  
c) To make the reference count thread-safe  
d) To store the reference count on the stack  

**3. What happens if a `SharedPtr` is copied without incrementing the reference count?**  
a) The program will crash immediately  
b) The managed object may be deleted prematurely, causing undefined behavior  
c) The copy will point to a different object  
d) The reference count will become negative  

**4. In the `SharedPtr` destructor, why is it critical to check if `refCount_` is non-null before decrementing?**  
a) To avoid dereferencing a null pointer  
b) To prevent memory leaks  
c) To ensure thread safety  
d) To allow custom deleters to function  

**5. What is the role of the `release()` function in the provided `SharedPtr` implementation?**  
a) It increments the reference count for new owners  
b) It safely decrements the reference count and deletes the managed object if necessary  
c) It resets the pointer to a new object  
d) It copies the managed object to a new memory location  

**6. How does the `SharedPtr` handle self-assignment in the copy assignment operator?**  
a) It ignores the operation and returns immediately  
b) It decrements the reference count and reassigns the pointer  
c) It creates a new reference count for the same object  
d) It throws an exception to prevent self-assignment  

**7. What is the effect of calling `reset()` with no arguments on a `SharedPtr`?**  
a) It increments the reference count  
b) It sets the managed pointer and reference count to null, potentially deleting the object  
c) It creates a new object with a default constructor  
d) It copies the current object to a new `SharedPtr`  

**8. Why might the `SharedPtr` implementation include a move constructor?**  
a) To prevent unnecessary reference count increments and improve performance  
b) To ensure thread-safe ownership transfer  
c) To allow the `SharedPtr` to manage stack-allocated objects  
d) To enable custom deleters  

**9. What would happen if two `SharedPtr` instances were created with the same raw pointer but different control blocks?**  
a) The program would function correctly with independent reference counts  
b) The object would be deleted multiple times, leading to undefined behavior  
c) The reference counts would automatically merge  
d) The second `SharedPtr` would be set to null  

**10. What is a key limitation of the provided `SharedPtr` implementation for production use?**  
a) It lacks support for stack-allocated objects  
b) It is not thread-safe for shared ownership across threads  
c) It cannot handle null pointers  
d) It does not support copy construction  

---

### Verification of Answers

**1. What is the primary purpose of a `SharedPtr<T>` smart pointer?**  
**Your Answer:** b) To automatically manage the lifetime of a heap-allocated object via reference counting  
**Correct?** ✅ **Yes**  
**Explanation:** A `SharedPtr` manages the lifetime of a heap-allocated object by using reference counting to track how many pointers share ownership. When the reference count reaches zero, the object is deleted, preventing memory leaks. Option a is incorrect because exclusive ownership is the role of `unique_ptr`. Option c is unrelated, and option d is not guaranteed without specific thread-safety mechanisms.

**2. Why is a separate `int* refCount_` used instead of an `int refCount_` in the `SharedPtr` implementation?**  
**Your Answer:** a) To allow multiple `SharedPtr` instances to share the same reference count  
**Correct?** ✅ **Yes**  
**Explanation:** The `int* refCount_` is a pointer to a shared integer that all `SharedPtr` instances managing the same object point to. This ensures that all instances update the same reference count, maintaining correct ownership semantics. Option b is incorrect because a pointer doesn’t inherently reduce memory usage. Option c is irrelevant without atomic operations, and option d is incorrect because the reference count is heap-allocated.

**3. What happens if a `SharedPtr` is copied without incrementing the reference count?**  
**Your Answer:** b) The managed object may be deleted prematurely, causing undefined behavior  
**Correct?** ✅ **Yes**  
**Explanation:** Failing to increment the reference count during copying means the new `SharedPtr` isn’t accounted for in the ownership model. If another `SharedPtr` destructs and decrements the count to zero, the object is deleted, leaving the copied `SharedPtr` with a dangling pointer, leading to undefined behavior. Option a is too specific, option c is incorrect, and option d is not a typical outcome.

**4. In the `SharedPtr` destructor, why is it critical to check if `refCount_` is non-null before decrementing?**  
**Your Answer:** a) To avoid dereferencing a null pointer  
**Correct?** ✅ **Yes**  
**Explanation:** If `refCount_` is null (e.g., for a null `SharedPtr` or after a move/reset), attempting to decrement `*refCount_` would dereference a null pointer, causing undefined behavior. Checking `refCount_` ensures safe operation. Option b is a consequence, not the reason. Option c is unrelated, and option d is irrelevant.

**5. What is the role of the `release()` function in the provided `SharedPtr` implementation?**  
**Your Answer:** b) It safely decrements the reference count and deletes the managed object if necessary  
**Correct?** ✅ **Yes**  
**Explanation:** The `release()` function decrements the reference count and, if it reaches zero, deletes both the managed object (`ptr_`) and the reference count (`refCount_`). This ensures proper cleanup. Option a is incorrect (it’s the opposite), option c is the role of `reset()`, and option d is unrelated.

**6. How does the `SharedPtr` handle self-assignment in the copy assignment operator?**  
**Your Answer:** a) It ignores the operation and returns immediately  
**Correct?** ✅ **Yes**  
**Explanation:** The copy assignment operator checks `if (this != &other)` to detect self-assignment. If true, it returns immediately to avoid unnecessarily releasing and reassigning the same resources, which could lead to errors like deleting the object prematurely. Option b is incorrect because it describes incorrect behavior. Option c is not how it works, and option d is not typical.

**7. What is the effect of calling `reset()` with no arguments on a `SharedPtr`?**  
**Your Answer:** b) It sets the managed pointer and reference count to null, potentially deleting the object  
**Correct?** ✅ **Yes**  
**Explanation:** Calling `reset()` with no arguments calls `release()`, which decrements the reference count and deletes the object if the count reaches zero. It then sets `ptr_` and `refCount_` to `nullptr`. Option a is incorrect, option c is unrelated, and option d is wrong.

**8. Why might the `SharedPtr` implementation include a move constructor?**  
**Your Answer:** a) To prevent unnecessary reference count increments and improve performance  
**Correct?** ✅ **Yes**  
**Explanation:** The move constructor transfers ownership by taking the `ptr_` and `refCount_` from the source `SharedPtr` and setting the source’s pointers to null, avoiding the need to increment the reference count as in copying. This improves performance. Option b is incorrect without thread-safety mechanisms, option c is invalid, and option d is unrelated.

**9. What would happen if two `SharedPtr` instances were created with the same raw pointer but different control blocks?**  
**Your Answer:** b) The object would be deleted multiple times, leading to undefined behavior  
**Correct?** ✅ **Yes**  
**Explanation:** If two `SharedPtr` instances manage the same raw pointer with different control blocks (i.e., separate `refCount_` pointers), each will independently decrement its count and delete the object when it reaches zero, leading to multiple deletions and undefined behavior. Option a is incorrect, option c is not possible, and option d is wrong.

**10. What is a key limitation of the provided `SharedPtr` implementation for production use?**  
**Your Answer:** b) It is not thread-safe for shared ownership across threads  
**Correct?** ✅ **Yes**  
**Explanation:** The provided `SharedPtr` uses a plain `int*` for `refCount_`, which is not thread-safe. In a multithreaded environment, concurrent access could lead to race conditions. Option a is not a limitation (smart pointers are for heap objects), option c is handled correctly, and option d is supported.

---

### Summary
**Score:** 10/10 ✅  