# Concurrency, Signals, and State Issues (CWE-699 Reference)

This reference module covers software weaknesses related to multithreading, asynchronous interrupts, signal handling, race conditions, and inconsistent state synchronization.

---

## CWE-557: Concurrency Issues

Weaknesses in this category relate to multiple threads, processes, or asynchronous agents accessing shared resources without adequate synchronization, leading to nondeterministic or corrupted execution states.

### Key Weakness Identifiers
* CWE-362: Concurrent Execution using Shared Resource with Improper Synchronization ('Race Condition')
* CWE-366: Race Condition within a Thread
* CWE-367: Time-of-check Time-of-use (TOCTOU) Race Condition
* CWE-364: Signal Handler Race Condition
* CWE-820: Missing Synchronization for Thread Shared Attribute
* CWE-821: Incorrect Synchronization

### Audit and Review Checklist
* Shared State Protection: Ensure all variables, shared structures, and hardware registers accessed by multiple execution threads or interrupt contexts are protected by appropriate synchronization primitives (mutex, spinlock, atomic operations, or memory barriers).
* TOCTOU Guardrails: Prevent separate check-and-operate sequences on external resources (such as file existence checks with `stat` or `access` followed by `open`). Use atomic system calls (such as `open(..., O_CREAT | O_EXCL)` or file-descriptor-relative variants like `openat`).
* Lock-Free Correctness: If lock-free algorithms or compiler atomics (`std::atomic`, `atomic_t`) are used, verify memory ordering semantics (`acquire`, `release`, `seq_cst`) and memory barriers to ensure visibility across CPU cores.
* Reentrancy: Ensure shared functions or callbacks called concurrently are reentrant and do not rely on static local storage without synchronization.

---

## CWE-387: Signal Errors

Weaknesses in this category relate to the handling of asynchronous signals and interrupts, where execution flow is interrupted unpredictably.

### Key Weakness Identifiers
* CWE-831: Signal Handler Function Associated with Multiple Signals
* CWE-479: Signal Handler Use of a Non-reentrant Function
* CWE-828: Signal Handler with Functionality that Concludes in Non-reentrant API

### Audit and Review Checklist
* Async-Signal-Safe Operations: Verify that signal handler routines only call async-signal-safe functions (as defined in POSIX.1-2008 or kernel atomic guidelines). Never invoke memory allocators (`malloc`, `free`), I/O streaming (`printf`), or standard mutex locking inside signal handlers.
* Minimalist Signal Handlers: Signal handlers should strictly set a volatile flag of type `sig_atomic_t` (or an atomic boolean/eventfd) and exit immediately, deferring processing logic to the main event loop.
* Signal Masking: Protect non-reentrant state manipulation in normal code paths by blocking or masking signals (`sigprocmask`, `pthread_sigmask`) during sensitive operations.

---

## CWE-371: State Issues

Weaknesses in this category occur when a system maintains, transitions, or persists state inconsistently or fails to invalidate state across transactions.

### Key Weakness Identifiers
* CWE-372: Incomplete State Transition
* CWE-374: Passing Mutable Objects to an Untrusted Method
* CWE-375: Returning a Mutable Object to an Untrusted Caller
* CWE-662: Improper Synchronization of Concurrent State
* CWE-488: Exposure of Data Element to Wrong Session

### Audit and Review Checklist
* State Machine Atomicity: Ensure transitions between finite states (e.g., disconnected, authenticating, authorized, revoked) are atomic and cannot be interrupted midway.
* Defensive Copying: When passing internal state objects across trust boundaries or returning references to sensitive internal structures, create defensive copies or return immutable views.
* Stale State Invalidation: Verify that state caches, credentials, and session tokens are invalidated completely across resets, disconnections, or permission changes.
