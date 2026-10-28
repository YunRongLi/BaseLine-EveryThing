# Cryptography, Keys, and Random Numbers (CWE-699 Reference)

This reference module covers software weaknesses related to cryptographic algorithm selection, key management, cryptographic entropy, and pseudorandom number generators.

---

## CWE-310: Cryptographic Issues

Weaknesses in this category relate to improper implementation or misuse of cryptographic primitives and algorithms.

### Key Weakness Identifiers
* CWE-327: Use of a Broken or Risky Cryptographic Algorithm
* CWE-328: Use of Weak Hash
* CWE-326: Inadequate Encryption Strength
* CWE-347: Improper Verification of Cryptographic Signature
* CWE-208: Observable Timing Discrepancy ('Timing Attack')
* CWE-329: Generation of Predictable IV with CBC Mode

### Audit and Review Checklist
* Strong Algorithms: Reject outdated or broken algorithms (MD5, SHA1, DES, 3DES, RC4). Enforce modern standards: SHA-256/SHA-512, SHA-3, AES-GCM (128/256), ChaCha20-Poly1305, RSA (>= 3072-bit), Ed25519, or ECDSA (P-256 or higher).
* Authenticated Encryption: Prefer AEAD modes (AES-GCM, ChaCha20-Poly1305). If unauthenticated modes like CBC are used, always pair with encrypt-then-MAC using HMAC.
* Nonce and IV Uniqueness: Ensure nonces and IVs are cryptographically generated and never reused across different encryption runs with the same key.
* Constant-Time Cryptographic Verification: Verify that all secret comparisons (MAC comparisons, password hashes, signatures) use constant-time comparison routines to prevent timing side channels.

---

## CWE-320: Key Management Errors

Weaknesses in this category relate to the generation, distribution, storage, lifetime, and destruction of cryptographic keys.

### Key Weakness Identifiers
* CWE-321: Use of Hard-coded Cryptographic Key
* CWE-324: Use of a Key Past its Expiration Date
* CWE-325: Missing Required Cryptographic Step
* CWE-916: Use of Password Hash With Insufficient Computational Effort

### Audit and Review Checklist
* No Hard-Coded Keys: Strictly prohibit embedding private keys, symmetric keys, or HMAC secrets in source code, firmware headers, or configuration files.
* Hardware Security Integration: Utilize hardware root of trust, TPM (Trusted Platform Module), HSM, or secure enclaves for key derivation, storage, and private key operations whenever supported by the platform.
* Password Hashing Schemes: Use memory-hard key derivation functions (Argon2id, scrypt, or PBKDF2 with high iteration counts and unique cryptographic salts) for password hashing.
* Key Zeroization: Securely wipe key material and derived session secrets from RAM when no longer needed using secure zeroing primitives (`explicit_bzero`).

---

## CWE-1213: Random Number Issues

Weaknesses in this category relate to using predictable, pseudo-random generators for security-sensitive contexts.

### Key Weakness Identifiers
* CWE-330: Use of Insufficiently Random Values
* CWE-338: Use of Cryptographically Weak Pseudo-Random Number Generator (PRNG)
* CWE-331: Insufficient Entropy
* CWE-335: Incorrect Usage of Seeds in Pseudo-Random Number Generator

### Audit and Review Checklist
* Cryptographic PRNG: For security tokens, cryptographic keys, IVs, salt generation, and session IDs, strictly use Cryptographically Secure PRNGs (CSPRNG, such as `/dev/urandom`, `getrandom()` system call, or OpenSSL `RAND_bytes()`).
* Forbid Weak PRNGs in Security Contexts: Forbid `rand()`, `random()`, `srand()`, `std::minstd_rand`, or `Math.random()` in any context involving security decisions, tokens, or cryptography.
* Entropy Seeding: Ensure the CSPRNG is seeded from a high-quality hardware entropy source, especially in embedded or virtualized environments during early boot.
