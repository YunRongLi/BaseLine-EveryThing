---
name: c-programming-guideline
trigger: glob
globs: "**/*.{c,h}"
description: Guidelines for C programming. Focuses on architecture, interfaces, resource management, and error handling for C development.
---
> [!IMPORTANT]
> These guidelines are strictly for C development. ONLY apply these rules when modifying or reviewing `.c` or `.h` files. If the current task involves other file types, disregard this entire document.

# C Language Programming Guidelines (Summary)
Including the C Coding Standard and Project ACRN guidelines.

## 1. Philosophy
- **P.1: Make names fit the system.** Names should be the result of a deep thought process. If the name is appropriate, relationships and meaning are naturally derivable.
- **P.2: Use layering to manage complexity.** Divide the system into layers communicating through well-defined interfaces. Avoid layering violations.
- **P.3: Comments should tell a story.** Ensure class, signature, argument, and implementation comments weave together. Document the "why" behind decisions.

## 2. Interfaces
- **I.1: Use header file guards.** Protect all header files against multiple inclusion using `#ifndef`, `#define`, and `#endif`.
- **I.2: Do not put data definitions in header files.** Define variables once in a `.c` file and use `extern` in the header.
- **I.3: Limit function size.** Functions should achieve a single objective and ideally fit on a single page of code.
- **I.4: Document interfaces explicitly.** Use Doxygen-style comments (`@brief`, `@param`, `@return`) immediately before the function definition or declaration.

## 3. Functions
- **F.1: Handle all return values.** Non-void functions must return a value on all possible paths. Explicitly cast to `(void)` if discarding a return value.
- **F.2: Never return a pointer to a local object.** Automatic variables have their lifetime end with the function block; pointers to them will be invalid.
- **F.3: Protect parameters.** Parameters passed by pointer should not be reassigned; parameters passed by value should not be modified directly.
- **F.4: Limit the number of parameters.** Aim for at most 6 parameters to maintain clean function signatures.
- **F.5: Declare non-static functions in headers.** Functions with external linkage should be declared in a header file. Static functions must be used within the file where declared.

## 4. Resource Management
- **R.1: Always initialize variables.** Initialize variables at declaration to avoid unpredictable operations on uninitialized values. Fully initialize arrays.
- **R.2: Manage dynamic memory carefully.** Check every call to `malloc` or `realloc` for success.
- **R.3: Favor static allocation in constrained environments.** In embedded or hypervisor environments, replace dynamic allocation with static memory where possible.
- **R.4: Avoid overlapping memory operations.** Do not perform functions like `memcpy` on objects with overlapping storage to prevent data corruption.

## 5. Error Handling
- **E.1: Check system call error returns.** Always check system calls for error returns and include the system error text in error messages.
- **E.2: Use explicit boolean tests.** Avoid defaulting tests for non-zero. Use explicit comparisons (e.g., `if (0 == status)`).
- **E.3: Provide a label for error states.** In enumerations, include a specific label for uninitialized or error states, ideally as the first entry.
- **E.4: Avoid magic numbers.** Replace bare numbers with `#define` macros, constants, or enumerations that indicate their meaning.

## 6. Source Files
- **S.1: Use appropriate file extensions.** Use `.h` for header files and `.c` for source files.
- **S.2: Use `#if 0` for commenting out code blocks.** Do not use nested comments `/* ... */`. Use `#if 0` and explain why the code is disabled.
- **S.3: Use `#if` instead of `#ifdef`.** Use `#if MACRO` to correctly handle scenarios where a macro might be undefined.
- **S.4: Document `#include` statements.** Comment on why a particular file is being included.

## 7. Expressions and Statements
- **ES.1: One statement and variable per line.** Maintain one statement per line and define only one variable per line for clarity and documentation.
- **ES.2: Be "Const Correct."** Use the `const` keyword for parameters and objects that should not be modified.
- **ES.3: Use consistent, descriptive naming.** Use lowercase with underscores for stack variables; use all uppercase with underscores for macros and `#defines`.

## 8. Coding Style (Project Specific)
- **Use Allman style for opening braces.** The opening brace `{` must be on a new line and aligned with the start of the control statement (if, while, etc.) or function signature.
- **Always use braces.** All `if`, `while`, and `do` statements require braces, even for single-line blocks.
- **Limit line lengths.** Lines should not exceed a reasonable width (e.g., 80 or 120 characters) to ensure readability and printability.
- **Avoid `goto` and disguised jumps.** Use `goto`, `continue`, and `break` sparingly to avoid jumping to undocumented or confusing locations.
