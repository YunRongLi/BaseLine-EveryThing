# Data Validation, Neutralization, and Processing (CWE-699 Reference)

This reference module covers software weaknesses related to untrusted input validation, injection vulnerabilities, data integrity, data leakage, file handling, and communication channels.

---

## CWE-1215: Data Validation Issues

Weaknesses in this category relate to improper, insufficient, or missing validation of input received from external, untrusted sources.

### Key Weakness Identifiers
* CWE-20: Improper Input Validation
* CWE-1284: Improper Validation of Specified Quantity in Input
* CWE-1285: Improper Validation of Specified Index, Position, or Offset in Input
* CWE-1287: Improper Validation of Specified Type of Input
* CWE-1288: Improper Validation of Consistency within Input

### Audit and Review Checklist
* Allowlist Validation: Validate all input data (parameters, headers, filenames, network payloads) against strict allowlists (allowed characters, ranges, types, and lengths) rather than relying on blocklists.
* Boundary and Offset Bounds: Verify that indices, offsets, and length parameters transmitted within packets or payloads are strictly checked against physical buffer limits before use.
* Structural Integrity: Validate self-describing protocols (such as TLV, JSON, Protobuf, XML) for schema compliance and element consistency before decoding payload bodies.

---

## CWE-137: Data Neutralization Issues

Weaknesses in this category relate to failures in sanitizing, escaping, encoding, or parameterizing untrusted input before passing it into downstream interpreters, commands, or data stores (Injection flaws).

### Key Weakness Identifiers
* CWE-78: Improper Neutralization of Special Elements used in an OS Command ('OS Command Injection')
* CWE-79: Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting')
* CWE-89: Improper Neutralization of Special Elements used in an SQL Command ('SQL Injection')
* CWE-90: Improper Neutralization of Special Elements used in an LDAP Query
* CWE-94: Improper Control of Generation of Code ('Code Injection')
* CWE-918: Server-Side Request Forgery (SSRF)

### Audit and Review Checklist
* Parameterization and Prepared Statements: Always use parameterized queries and prepared statements for SQL, LDAP, and database interactions. Never concatenate untrusted strings into queries.
* Avoid Shell Invocation: Avoid executing shell interpreters (`system()`, `popen()`, `exec("sh -c ...")`). Instead, use direct execution APIs (e.g., `execve`, `posix_spawn`) with explicit, distinct argument vectors.
* Output Encoding: Ensure contextual output encoding (HTML entity encoding, JavaScript escaping, URL encoding) is applied before embedding data in web responses or UI contexts.
* Target URL Validation: When making outgoing network requests from user-provided URLs (SSRF risk), restrict targets to an allowlist of approved domains and block loopback (`127.0.0.1`), link-local (`169.254.0.0/16`), and private RFC 1918 addresses.

---

## CWE-1214: Data Integrity Issues

Weaknesses in this category involve unauthorized modification, tampering, or corruption of data during storage, transit, or processing.

### Key Weakness Identifiers
* CWE-353: Missing Support for Integrity Check
* CWE-354: Improper Validation of Integrity Check Value
* CWE-565: Reliance on Cookies without Validation and Integrity Checking

### Audit and Review Checklist
* Cryptographic Signatures and Hashes: Ensure firmware images, software updates, critical configuration blocks, and IPC messages include cryptographic signatures (e.g., RSA-PSS, ECDSA) or HMACs, rather than non-cryptographic checksums like CRC32.
* Constant-Time Integrity Comparison: Use constant-time comparison functions (e.g., `CRYPTO_memcmp`) when validating MACs or signature hashes to prevent timing attacks.

---

## CWE-19: Data Processing Errors

Weaknesses in this category occur during data parsing, extraction, serialization, or translation.

### Key Weakness Identifiers
* CWE-130: Improper Handling of Length Parameter Inconsistency
* CWE-178: Improper Handling of Case Sensitivity
* CWE-182: Collapse of Data into Unsafe Value
* CWE-502: Deserialization of Untrusted Data

### Audit and Review Checklist
* Safe Deserialization: Never deserialize untrusted binary streams into executable code objects. Use strict, schema-validated serialization formats (e.g., JSON, Protocol Buffers).
* Parsing Ambiguities: When protocol messages carry duplicate headers or contradictory length fields, reject the message outright rather than making speculative parsing assumptions.

---

## CWE-199: Information Management Errors

Weaknesses in this category relate to the unintentional disclosure, leakage, or exposure of sensitive data to unauthorized parties.

### Key Weakness Identifiers
* CWE-200: Exposure of Sensitive Information to an Unauthorized Actor
* CWE-209: Generation of Error Message Containing Sensitive Information
* CWE-532: Insertion of Sensitive Information into Log File
* CWE-214: Invocation of Process Using Visible Sensitive Information

### Audit and Review Checklist
* Log Sanitization: Verify that passwords, private keys, session tokens, and personal identifiable information (PII) are never written to log files, crash dumps, or console output.
* Generic Error Responses: In production environments, return generic error messages to clients; never expose internal stack traces, database schema details, or system file paths.
* Zeroing Sensitive Memory: Overwrite memory containing encryption keys, credentials, or private keys with zero before freeing (`explicit_bzero`, `memset_s`).

---

## CWE-1219: File Handling Issues

Weaknesses in this category relate to improper manipulation of file paths, file system permissions, and link resolution.

### Key Weakness Identifiers
* CWE-22: Improper Limitation of a Pathname to a Restricted Directory ('Path Traversal')
* CWE-59: Improper Link Resolution Before File Access ('Link Following')
* CWE-377: Insecure Temporary File
* CWE-732: Incorrect Permission Assignment for Critical Resource

### Audit and Review Checklist
* Path Canonicalization and Sanitization: Resolve and verify canonical paths (`realpath()`) before opening files. Ensure the canonicalized path starts with the allowed base directory.
* Symbolic Link Attacks: In shared or temporary directories (`/tmp`), avoid following untrusted symlinks. Use `O_NOFOLLOW` and secure temporary file creators (`mkstemp()`).
* File Permissions: Explicitly set restrictive umasks and file permissions (e.g., `0600` or `0640` for configuration and secret files) at creation time.

---

## CWE-417: Communication Channel Errors

Weaknesses in this category relate to the creation, configuration, and security of network or IPC communication paths.

### Key Weakness Identifiers
* CWE-319: Cleartext Transmission of Sensitive Information
* CWE-295: Improper Certificate Validation
* CWE-300: Channel Accessible by Non-Endpoint

### Audit and Review Checklist
* Encryption in Transit: Use authenticated encryption (e.g., TLS 1.3, SSHv2, IPsec) for all network communications carrying sensitive or management traffic.
* Strict Certificate Validation: Ensure full validation of TLS certificates, including chain of trust verification, expiration checks, revocation status, and hostname verification. Never disable certificate verification.
