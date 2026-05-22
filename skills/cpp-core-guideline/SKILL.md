---
trigger: glob
globs: "**/*.{cpp,hpp}"
---
> [!IMPORTANT]
> These guidelines are strictly for C++ development. ONLY apply these rules when modifying or reviewing `.cpp` or `.hpp` files. If the current task involves other file types, disregard this entire document.

# C++ Core Guidelines (Summary)
Derived from the official [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines).

## 1. Philosophy
- **P.1: Express ideas directly in code.** Code should be self-documenting (e.g., use `std::vector<int>` instead of raw arrays and manual count).
- **P.3: Express intent.** Use types and names that clearly indicate what the code is doing.
- **P.10: Prefer immutable data to mutable data.** Use `const` and `constexpr` by default.
- **P.8: Don't leak any resources.** Use RAII (Resource Acquisition Is Initialization).

## 2. Interfaces
- **I.2: Avoid non-const global variables.** They lead to hidden dependencies and side effects.
- **I.11: Never transfer ownership by a raw pointer (`T*`) or reference (`T&`).** Use smart pointers for ownership.
- **I.12: Declare a pointer that must not be null as `not_null`.**
- **I.23: Keep the number of function arguments low.** If necessary, group related arguments into a struct/class.

## 3. Functions
- **F.2: A function should perform a single logical operation.**
- **F.3: Keep functions short and simple.** Aim for functions that fit on one screen.
- **F.16: For "in" parameters, pass cheaply-copied types by value and others by reference to const.**
- **F.21: To return multiple "out" values, prefer returning a struct.** Avoid output parameters (`void f(int& out)`).
- **F.42: Return a `T*` to indicate a position (only).** Raw pointers should never imply ownership.

## 4. Classes and Hierarchies
- **C.2: Use `class` if the class has an invariant; use `struct` if the data members can vary independently.**
- **C.35: A base class destructor should be either public and virtual, or protected and non-virtual.**
- **C.41: A constructor should create a fully initialized object.**
- **C.45: Don't define a default constructor that only initializes data members; use default member initializers instead.**
- **C.47: Define and initialize member variables in the order of member declaration.**
- **C.128: Virtual functions should specify exactly one of `virtual`, `override`, or `final`.**

## 5. Resource Management (RAII)
- **R.1: Manage resources automatically using resource handles and RAII.**
- **R.11: Avoid calling `new` and `delete` explicitly.** Use `std::make_unique` or `std::make_shared`.
- **R.20: Use `unique_ptr` or `shared_ptr` to represent ownership.**
- **R.3: A raw pointer (`T*`) is non-owning.**

## 6. Expressions and Statements
- **ES.5: Keep scopes small.** Declare variables as late as possible.
- **ES.11: Use `auto` to avoid redundant repetition of type names.**
- **ES.20: Always initialize an object.** Never leave variables uninitialized.
- **ES.47: Use `nullptr` rather than `0` or `NULL`.**
- **ES.71: Prefer a range-for-statement to a `for`-statement when there is a choice.**

## 7. Performance & Concurrency
- **Per.1: Don't optimize without reason.**
- **Per.7: Design to enable optimization.**
- **CP.2: Avoid data races.**
- **CP.20: Use RAII for locking (e.g., `std::lock_guard`, `std::unique_lock`).**
- **CP.21: Capture by value in asynchronous callbacks.** Avoid capturing variables by reference (e.g., `[&]`, `[&var]`) in lambdas passed to async functions. Also, **never capture `this` as a raw pointer** (e.g., `[this]`). References and `this` may become dangling if the calling object's lifetime ends before the callback fires. Always use `weak_from_this()` or `shared_from_this()` (e.g., `[weakSelf = weak_from_this()]` or `[self = shared_from_this()]`) to ensure memory safety.

## 8. Error Handling
- **E.2: Throw an exception to signal that a function can't perform its assigned task.**
- **E.6: Use RAII to prevent leaks** in the presence of exceptions.
- **E.15: Throw by value, catch exceptions from a hierarchy by reference.**

## 9. Source Files
- **SF.7: Don't write `using namespace` at global scope in a header file.**
- **SF.8: Use `#include` guards or `#pragma once` for all header files.**
- **SF.11: Header files should be self-contained.**

## 10. Standard Library
- **SL.1: Use libraries wherever possible.** Don't reinvent the wheel.
- **SL.con.1: Prefer using `std::array` or `std::vector` instead of a C array.**
- **SL.str.1: Use `std::string` to own character sequences; use `std::string_view` to refer to them.**
