---
trigger: manual
---

# Code Formatting and Style
* Kernel code must use tabs for indentation (8-wide). Mixed tabs/spaces, trailing whitespace, or leading spaces before tabs are strictly prohibited. Maintain consistent indentation in macro definitions using tabs.
* The preferred limit on the length of a single line is 80 columns, but do not break user-visible strings (like printk messages) as it breaks grep.
* Structs, if, switch, for, while, do must use K&R style braces (opening brace on the same line, closing brace on its own line). Functions are the exception: opening brace goes on the beginning of the next line.
* Use a space after most keywords (if, switch, case, for, do, while). Do not use spaces around sizeof, typeof, alignof, or __attribute__.
* Use one space around binary and ternary operators, but no space after unary operators.
* Do not use the `extern` keyword with function declarations in headers.

# Naming and Typedefs
* Global variables and functions must have descriptive names; local variables should be short and to the point.
* Avoid Hungarian notation.
* Avoid 'master / slave' and 'blacklist / whitelist' terminology; use 'primary / secondary' and 'denylist / allowlist' instead.
* NEVER use a typedef for structures or pointers unless they are totally opaque objects (e.g., `pte_t`) or specific integer types (e.g., `u8`, `u32`).

# Functions and Control Flow
* Functions should be short and do just one thing well, generally keeping local variables to 5-10.
* For functions returning an error-code, returning 0 means success and a negative value means failure. Predicates should return a boolean.
* Use `goto` for centralized exiting of functions to handle common cleanup tasks and avoid deep nesting. Choose label names that clarify what the `goto` does (e.g., `out_free_buffer:`).
* Error paths must only clean up resources that were successfully initialized (avoid ida_free on unallocated IDs, kfree on unallocated memory, etc.).
* Inline functions should be reserved for small functions (typically 3 lines or less) or when parameters are compile-time constants.

# Memory, Allocation, and Resources
* Resources obtained via managed APIs (devm_*) must NOT be explicitly freed using the non-managed counterparts (e.g., gpiod_put, kfree) in error or removal paths.
* When allocating memory for a struct, use `sizeof(*p)` instead of `sizeof(struct type)`.
* Do not cast the return value of memory allocation functions (kmalloc, kcalloc, etc.). Use `kmalloc_array` or `kcalloc` for arrays.
* When using `krealloc()`, always assign to a temporary pointer first to avoid leaking the original pointer if the allocation fails.
* In unregister/remove paths, systematically unlink any backpointers to avoid dangling pointer dereferences on hot-removal.

# Preprocessor and Macros
* Macros with multiple statements must be enclosed in a `do { ... } while (0)` block.
* Avoid macros that affect control flow or depend on magic local variables.
* Enclose expressions in parenthesis when defining constants using macros.
* Prefer `IS_ENABLED(CONFIG_SOMETHING)` in normal C conditionals over `#ifdef` in `.c` files wherever possible.
* Avoid duplicate macro definitions for shared register addresses; use descriptive, shared names.

# Concurrency and State
* State variables accessed or modified across different execution contexts (e.g., IRQ vs. process/softirq) must use `atomic_t` or proper locking to prevent data races.

# Error Handling and System State
* Do not use `BUG()` or `BUG_ON()`. Use `WARN_ON_ONCE()` or `WARN()` and handle the error gracefully if possible.
* Crashing the kernel using `panic()` should be strictly avoided unless there is no way for the system to continue.
* LINUX_VERSION_CODE / KERNEL_VERSION checks are prohibited in in-tree code; target the specific kernel version directly.

# APIs and Frameworks
* Modules must include `MODULE_LICENSE()`, `MODULE_AUTHOR()`, and `MODULE_DESCRIPTION()`.
* Use `sysfs_emit()` instead of `sprintf()` for sysfs show callbacks.
* UAPI headers must use fixed-width types (`__u32`, `__s32`, etc.) instead of architecture-dependent types like `int` or `unsigned int` to ensure stable binary ABIs.
* Prefer helper macros like `module_platform_driver()` over manually declaring `module_init` and `module_exit` functions.
* Avoid deprecated APIs (e.g., prefer `ida_alloc`/`ida_free` over `ida_simple_get`/`ida_simple_remove`).

# Build System and Device Tree
* Do not use `$(wildcard ...)` in Kbuild Makefiles; source files must be listed explicitly.
* Custom Device Tree compatible strings must include a valid vendor prefix.
* In DT schema bindings composing schemas with `allOf`, use `unevaluatedProperties: false` rather than `additionalProperties: false`.
* Fields parsed from Device Tree (e.g., `label`, `status`) must be actively utilized in the driver logic (e.g., for attribute visibility or descriptive names).

# Miscellaneous
* Copyright headers must NOT contain "Confidential" or "All rights reserved".
* Files must use SPDX-License-Identifier: GPL-2.0.
* Comments should explain WHAT the code does, not HOW. Avoid excessive commenting inside function bodies.
