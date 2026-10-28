# API, Error Handling, and Code Architecture (CWE-699 Reference)

This reference module covers software weaknesses related to API misuse, ignored return values, exception handling, encapsulation violations, code complexity, and bad coding practices.

---

## CWE-1228: API / Function Errors

Weaknesses in this category relate to the incorrect selection, invocation, or contract violation of built-in or external APIs.

### Key Weakness Identifiers
* CWE-242: Use of Inherently Dangerous Function
* CWE-474: Use of Function with Inconsistent Implementations
* CWE-676: Use of Potentially Dangerous Function
* CWE-1256: Improper Restriction of Software Interfaces to Authorized Actors

### Audit and Review Checklist
* Dangerous Functions: Forbid inherently dangerous functions like `gets()` that cannot be safely bounded.
* Contract Adherence: Verify that all preconditions and postconditions of library and system APIs (e.g., buffer length guarantees, alignment, nullability contracts) are strictly honored.
* Platform Variance: In cross-platform code, avoid relying on platform-specific side effects or non-standard API extensions.

---

## CWE-389: Error Conditions, Return Values, Status Codes

Weaknesses in this category relate to ignoring, misinterpreting, or mishandling error codes and unexpected execution outcomes.

### Key Weakness Identifiers
* CWE-252: Unchecked Return Value
* CWE-391: Unchecked Error Condition
* CWE-392: Missing Report of Error Condition
* CWE-754: Improper Check for Unusual or Exceptional Conditions
* CWE-755: Improper Handling of Exceptional Conditions

### Audit and Review Checklist
* Mandatory Return Checks: Verify that the return values of all security-sensitive or fallible operations (memory allocations, system calls, cryptography operations, file operations) are explicitly checked.
* Fail-Closed Defaults: System logic must fail closed. When an error or unexpected status code occurs, default to rejecting access, invalidating tokens, and aborting transactions.
* Meaningful Error Propagation: Ensure low-level error codes are translated and propagated properly rather than swallowed silently.

---

## CWE-429: Handler Errors

Weaknesses in this category relate to faulty exception handlers, interrupt service routines, or signal handlers.

### Key Weakness Identifiers
* CWE-396: Declaration of Catch for Generic Exception
* CWE-397: Declaration of Throws for Generic Exception
* CWE-703: Improper Check or Handling of Exceptional Conditions

### Audit and Review Checklist
* Specific Exception Handling: In C++ and high-level languages, avoid catching broad generic exceptions (e.g., `catch (...)`) without rethrowing, which can mask critical memory or logic failures.
* Complete Handler Scenarios: Ensure handlers adequately reset shared resources, release held locks, and clean up intermediate objects before exiting.

---

## CWE-1006: Bad Coding Practices

Weaknesses in this category violate sound software engineering conventions, diminishing maintainability and obscuring security flaws.

### Key Weakness Identifiers
* CWE-561: Dead Code
* CWE-563: Assignment to Variable without Use ('Unused Variable')
* CWE-1164: Irrelevant Code
* CWE-484: Omitted Break Statement in Switch

### Audit and Review Checklist
* Compiler Diagnostics: Enforce high compiler warning levels (`-Wall -Wextra -Werror -Wformat-security`). Zero warnings must be tolerated.
* Switch Case Fallthrough: Every switch case must end with a `break`, `return`, or an explicit fallthrough attribute (`[[fallthrough]]` / `fallthrough;`).
* Dead and Debug Code: Remove all debug backdoors, test stubs, and unreachable dead code before release.

---

## CWE-1226: Complexity Issues

Weaknesses in this category occur when high cyclomatic complexity, deeply nested logic, or tangled control flow obscures security analysis and introduces subtle bugs.

### Key Weakness Identifiers
* CWE-1120: Excessive Cyclomatic Complexity
* CWE-1047: Modules with High Coupling

### Audit and Review Checklist
* Refactoring Deep Nesting: Refactor functions with more than 3-4 levels of indentation using early returns, centralized `goto` cleanup blocks (in C), or helper routines.
* Single Responsibility: Decompose monolithic functions into single-purpose functions to ensure security-critical logic can be reasoned about and audited in isolation.

---

## CWE-1227: Encapsulation Issues

Weaknesses in this category relate to leaking internal implementation details or exposing critical internal data structures directly to callers.

### Key Weakness Identifiers
* CWE-485: Insufficient Encapsulation of Critical State
* CWE-497: Exposure of Sensitive System Information to an Unauthorized Control Sphere
* CWE-766: Critical Data Element Declared with Overly Broad Scope

### Audit and Review Checklist
* Scope Minimization: Restrict variable and function scope to the minimum necessary (`static` in C for translation-unit local functions; `private` / `protected` in C++).
* Immutable Public Interfaces: Do not expose raw internal pointers or mutable references to internal state without synchronization or copy protection.
