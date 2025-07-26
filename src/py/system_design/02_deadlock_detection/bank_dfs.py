import threading
import time
from typing import Dict, List, Set
from collections import defaultdict

class DeadlockDetectedException(Exception):
    pass

class Bank:
    def __init__(self, accounts: Dict[int, int]):
        """Initialize accounts with balances and locks."""
        self.accounts: Dict[int, int] = accounts  # Account ID -> Balance
        self.locks: Dict[int, threading.Lock] = {acc: threading.Lock() for acc in accounts}
        self.wait_graph: Dict[int, Set[int]] = defaultdict(set)  # Thread ID -> Set of thread IDs it waits for
        self.lock_graph_lock = threading.Lock()  # Protects wait_graph

    def _detect_cycle(self, thread_id: int, visited: Set[int], rec_stack: Set[int]) -> bool:
        """Detect cycles in wait-for graph using DFS."""
        visited.add(thread_id)
        rec_stack.add(thread_id)
        
        for neighbor in self.wait_graph[thread_id]:
            if neighbor not in visited:
                if self._detect_cycle(neighbor, visited, rec_stack):
                    return True
            elif neighbor in rec_stack:
                return True
        
        rec_stack.remove(thread_id)
        return False

    def _check_deadlock(self, current_thread_id: int, target_thread_id: int) -> bool:
        """Check if adding an edge to wait-for graph causes a deadlock."""
        with self.lock_graph_lock:
            # Add edge to wait-for graph
            self.wait_graph[current_thread_id].add(target_thread_id)
            
            # Check for cycle
            visited: Set[int] = set()
            rec_stack: Set[int] = set()
            cycle_exists = self._detect_cycle(current_thread_id, visited, rec_stack)
            
            # Remove edge after checking
            self.wait_graph[current_thread_id].discard(target_thread_id)
            if not self.wait_graph[current_thread_id]:
                del self.wait_graph[current_thread_id]
            
            return cycle_exists

    def transfer(self, from_account: int, to_account: int, amount: int) -> bool:
        """Transfer money between accounts with deadlock detection."""
        if from_account not in self.accounts or to_account not in self.accounts:
            return False
        if amount <= 0 or self.accounts[from_account] < amount:
            return False

        current_thread_id = threading.get_ident()
        
        # Try to acquire from_account lock
        if not self.locks[from_account].acquire(timeout=1.0):
            return False
        
        try:
            # Check if to_account lock is held by another thread
            if self.locks[to_account].locked():
                # Assume the lock is held by another thread (simplified)
                # In a real system, we'd need to know which thread holds it
                for other_thread_id in self.wait_graph:
                    if other_thread_id != current_thread_id:
                        if self._check_deadlock(current_thread_id, other_thread_id):
                            raise DeadlockDetectedException(
                                f"Deadlock detected: Thread {current_thread_id} waiting for {to_account}"
                            )
            
            # Try to acquire to_account lock
            if not self.locks[to_account].acquire(timeout=1.0):
                return False
            
            try:
                # Perform the transfer
                self.accounts[from_account] -= amount
                self.accounts[to_account] += amount
                return True
            finally:
                self.locks[to_account].release()
        finally:
            self.locks[from_account].release()
    
    def get_balance(self, account: int) -> int:
        """Return the balance of an account."""
        with self.locks[account]:
            return self.accounts[account]

def transfer_task(bank: Bank, from_account: int, to_account: int, amount: int, thread_name: str):
    """Thread task to perform a transfer."""
    print(f"{thread_name} attempting transfer: {from_account} -> {to_account}, amount: {amount}")
    try:
        success = bank.transfer(from_account, to_account, amount)
        if success:
            print(f"{thread_name} succeeded: Balance {from_account}: {bank.get_balance(from_account)}, "
                  f"{to_account}: {bank.get_balance(to_account)}")
        else:
            print(f"{thread_name} failed: Insufficient funds or invalid account")
    except DeadlockDetectedException as e:
        print(f"{thread_name} failed: {e}")

# Test harness
def main():
    # Initialize bank with two accounts
    bank = Bank({1: 1000, 2: 1000})
    
    # Create threads to simulate potential deadlock
    threads = [
        threading.Thread(target=transfer_task, args=(bank, 1, 2, 200, "Thread-1")),
        threading.Thread(target=transfer_task, args=(bank, 2, 1, 300, "Thread-2"))
    ]
    
    # Start threads
    for t in threads:
        t.start()
    
    # Wait for threads to complete
    for t in threads:
        t.join()
    
    # Print final balances
    print(f"Final balances: Account 1: {bank.get_balance(1)}, Account 2: {bank.get_balance(2)}")

if __name__ == "__main__":
    main()