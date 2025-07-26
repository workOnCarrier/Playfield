import threading
import time
from typing import Dict, List
import numpy as np

class DeadlockDetectedException(Exception):
    pass

class Bank:
    def __init__(self, accounts: Dict[int, int], max_threads: int = 10):
        """Initialize accounts, locks, and deadlock detection matrix."""
        self.accounts: Dict[int, int] = accounts  # Account ID -> Balance
        self.locks: Dict[int, threading.Lock] = {acc: threading.Lock() for acc in accounts}
        self.max_threads = max_threads  # Maximum number of threads for matrix size
        self.thread_ids = {}  # Map thread_id to matrix index
        self.next_index = 0  # Next available matrix index
        self.matrix_lock = threading.Lock()  # Protects thread_ids and matrix
        self.wait_matrix = np.zeros((max_threads, max_threads), dtype=int)  # Adjacency matrix for wait-for graph

    def _get_thread_index(self, thread_id: int) -> int:
        """Assign a matrix index to a thread ID."""
        with self.matrix_lock:
            if thread_id not in self.thread_ids:
                if self.next_index >= self.max_threads:
                    raise ValueError("Too many threads for matrix size")
                self.thread_ids[thread_id] = self.next_index
                self.next_index += 1
            return self.thread_ids[thread_id]

    def _detect_cycle(self) -> bool:
        """Detect cycles in the wait-for matrix using transitive closure."""
        n = self.next_index
        if n == 0:
            return False
        
        # Compute transitive closure using Warshall's algorithm
        closure = self.wait_matrix[:n, :n].copy()
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    closure[i][j] |= (closure[i][k] and closure[k][j])
        
        # Check for cycles (diagonal elements indicate a thread can reach itself)
        for i in range(n):
            if closure[i][i]:
                return True
        return False

    def _check_deadlock(self, current_thread_id: int, target_thread_id: int) -> bool:
        """Check if adding a wait-for edge causes a deadlock."""
        with self.matrix_lock:
            current_idx = self._get_thread_index(current_thread_id)
            target_idx = self._get_thread_index(target_thread_id)
            
            # Add edge to wait-for matrix
            self.wait_matrix[current_idx][target_idx] = 1
            
            # Check for cycle
            cycle_exists = self._detect_cycle()
            
            # Remove edge after checking
            self.wait_matrix[current_idx][target_idx] = 0
            
            # Clean up if no outgoing edges
            if not any(self.wait_matrix[current_idx]):
                del self.thread_ids[current_thread_id]
                self.next_index = max(self.thread_ids.values(), default=-1) + 1
            
            return cycle_exists

    def transfer(self, from_account: int, to_account: int, amount: int) -> bool:
        """Transfer money between accounts with matrix-based deadlock detection."""
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
                # Check for deadlock with other threads
                for other_thread_id in self.thread_ids:
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

def main():
    # Initialize bank with two accounts
    bank = Bank({1: 1000, 2: 1000}, max_threads=10)
    
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