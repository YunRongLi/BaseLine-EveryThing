# Numeric Errors and Computation (CWE-699 Reference)

This reference module covers software weaknesses related to arithmetic calculations, integer representations, precision loss, and mathematical expressions.

---

## CWE-189: Numeric Errors

Weaknesses in this category relate to improper calculation, comparison, conversion, or representation of numbers.

### Key Weakness Identifiers
* CWE-190: Integer Overflow or Wraparound
* CWE-191: Integer Underflow (Wrap or Loss of Significance)
* CWE-192: Integer Coercion Error
* CWE-197: Numeric Truncation Error
* CWE-369: Divide By Zero
* CWE-839: Similar Reality / Array Index Negative Offset
* CWE-128: Wrap-around Error

### Audit and Review Checklist
* Arithmetic Boundary Validation: Validate arithmetic operations involving untrusted input against integer limits (`INT_MAX`, `SIZE_MAX`, `UINT32_MAX`) prior to execution (e.g., check `a > SIZE_MAX - b` before performing `a + b`).
* Allocation Sizing Arithmetic: When computing allocation sizes (`count * element_size`), verify that multiplication does not overflow before passing the result to `malloc` or `kmalloc`. Use overflow-checked helpers such as `calloc`, `kmalloc_array`, or compiler built-ins (e.g., `__builtin_mul_overflow`).
* Sign Confusion and Signed/Unsigned Comparisons: Verify that signed and unsigned integers are not mixed in comparison expressions (e.g., comparing signed `int len` against `size_t max_len`), which can lead to negative values bypassing upper-bound checks.
* Division and Modulo Operations: Ensure denominator or divisor variables are checked for zero before performing `/` or `%`.
* Integer Truncation: Check assignments from larger bit-width types (e.g., `uint64_t`, `size_t`) to smaller bit-width variables (e.g., `uint16_t`, `int`) for unintended high-bit truncation.

---

## CWE-569: Expression Issues

Weaknesses in this category relate to flawed mathematical expressions, operator precedence misunderstandings, or side-effects within evaluations.

### Key Weakness Identifiers
* CWE-480: Use of Incorrect Operator (e.g., bitwise `&` vs. logical `&&`, assignment `=` vs. equality `==`)
* CWE-481: Assigning instead of Comparing
* CWE-482: Comparing instead of Assigning
* CWE-783: Operator Precedence Logic Error

### Audit and Review Checklist
* Operator Precedence Clarification: Use explicit parentheses in complex logical, bitwise, and arithmetic expressions, particularly when combining shift (`<<`, `>>`), bitwise (`&`, `|`, `^`), and relational operators.
* Side-Effects in Macro Expansions: Ensure macro parameters are never evaluated more than once if they may have side-effects (e.g., `MIN(i++, j)`), and always enclose macro parameters in parentheses.
* Assignment in Conditions: Avoid variable assignment inside conditional predicates (`if (ret = func())`), or enclose explicitly with additional parentheses if intentional, adhering to compiler warning flags like `-Wparentheses`.
