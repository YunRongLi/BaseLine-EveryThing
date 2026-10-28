# Memory Safety and Pointer Operations (CWE-699 Reference)

This reference module covers software weaknesses related to memory buffer operations, pointer manipulation, string formatting, and type confusion.

---

## CWE-1218: Memory Buffer Errors

Weaknesses in this category relate to the manipulation of memory buffers where bounds, sizing, and allocation calculations are improperly verified.

### Key Weakness Identifiers
* CWE-119: Improper Restriction of Operations within the Bounds of a Memory Buffer
* CWE-120: Buffer Copy without Checking Size of Input ('Classic Buffer Overflow')
* CWE-121: Stack-based Buffer Overflow
* CWE-122: Heap-based Buffer Overflow
* CWE-125: Out-of-bounds Read
* CWE-787: Out-of-bounds Write
* CWE-131: Incorrect Calculation of Buffer Size
* CWE-135: Incorrect Calculation of Multi-Byte String Length

### Audit and Review Checklist
* Bound Checks: Ensure every read, write, or copy operation on arrays and buffers enforces explicit destination boundary checks before execution.
* Dangerous Functions: Prohibit unbounded legacy functions such as `strcpy`, `strcat`, `sprintf`, `gets`, and `scanf("%s")`. Use bounded alternatives such as `snprintf`, `strlcpy`, or modern standard container methods.
* Off-by-One Hazards: Inspect all loop termination conditions, index computations, and buffer terminator allocations (`+ 1` for null terminator).
* Dynamic Buffer Sizing: Verify that allocation sizes account for exact element sizes (`sizeof(*ptr)` or `sizeof(T)`), rather than assuming fixed architecture widths.

---

## CWE-465: Pointer Issues

Weaknesses in this category relate to the creation, dereferencing, assignment, and destruction of pointers.

### Key Weakness Identifiers
* CWE-416: Use After Free (UAF)
* CWE-476: NULL Pointer Dereference
* CWE-824: Access of Uninitialized Pointer
* CWE-415: Double Free
* CWE-763: Release of Invalid Pointer or Memory Not on Heap
* CWE-587: Assignment of Fixed Address to Pointer

### Audit and Review Checklist
* Pointer Lifecycle and Invalidation: Immediately assign freed pointers to `NULL` (or `nullptr`) or verify that pointers leave scope instantly upon deallocation.
* Null Verification: Check pointers for `NULL` before dereferencing, particularly when returned from memory allocation, system calls, or external library queries.
* Ownership Contracts: Explicitly define and verify object ownership across function boundaries. Avoid passing raw pointers where resource management is ambiguous; in C++, favor smart pointers (`std::unique_ptr`, `std::shared_ptr`).
* Struct Removals: When unregistering or tearing down complex data structures, unlink backpointers and active list nodes before freeing memory blocks to prevent dangling pointer references.

---

## CWE-133: String Errors

Weaknesses in this category involve string handling, formatting, parsing, and multi-byte encoding.

### Key Weakness Identifiers
* CWE-134: Use of Externally-Controlled Format String
* CWE-170: Improper Null-Termination
* CWE-241: Improper Handling of Unexpected Data Type in String Processing

### Audit and Review Checklist
* Format String Safety: Never pass external, untrusted, or user-supplied strings directly as the format argument in `printf`, `syslog`, `sprintf`, or related functions. Format strings must always be static string literals.
* Explicit Null-Termination: When using functions that do not guarantee null-termination (e.g., `strncpy`, `read`, `memcpy`), explicitly set the last byte `buf[sizeof(buf) - 1] = '\0'`.
* Multi-Byte and UTF-8 Parsing: Ensure byte offsets are not conflated with character offsets when processing UTF-8 or localized multi-byte string streams.

---

## CWE-136: Type Errors

Weaknesses in this category occur when data is processed using an incompatible or unexpected data type.

### Key Weakness Identifiers
* CWE-843: Access of Resource Using Incompatible Type ('Type Confusion')
* CWE-704: Incorrect Type Conversion or Cast
* CWE-588: Attempt to Access Child of a Non-Structure Pointer

### Audit and Review Checklist
* Type Casting: Scrutinize all pointer casts (e.g., `void*` or downcasting base pointers to derived structs/classes). Ensure verified type tagging or runtime validation (`dynamic_cast` in C++) precedes usage.
* Alignment Restrictions: Verify that memory addresses are properly aligned for the target data type before type punning or casting raw buffers into structured structs.
* Union Validation: When using C unions, verify that an active discriminator / tag is always validated before accessing union member fields.
