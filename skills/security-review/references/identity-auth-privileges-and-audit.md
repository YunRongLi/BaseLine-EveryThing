# Identity, Access Control, Audit, and Business Logic (CWE-699 Reference)

This reference module covers software weaknesses related to credentials, authentication, authorization, privileges, permissions, session management, auditing, business logic, and UI security.

---

## CWE-255: Credentials Management Errors

Weaknesses in this category relate to how authentication credentials (passwords, tokens, API keys) are stored, transmitted, or managed.

### Key Weakness Identifiers
* CWE-798: Use of Hard-coded Credentials
* CWE-259: Use of Hard-coded Password
* CWE-522: Insufficiently Protected Credentials
* CWE-256: Plaintext Storage of a Password

### Audit and Review Checklist
* Zero Hard-coded Credentials: Never hardcode default credentials, test passwords, or backdoor keys in source code, build scripts, or firmware images.
* Secure Storage: Store stored credentials with salted, memory-hard hashing functions (Argon2id, PBKDF2), or leverage dedicated OS credential stores / secure vaults.

---

## CWE-1211: Authentication Errors

Weaknesses in this category relate to improper verification of an actor's claimed identity.

### Key Weakness Identifiers
* CWE-287: Improper Authentication
* CWE-308: Use of Single-factor Authentication
* CWE-290: Authentication Bypass by Spoofing
* CWE-304: Missing Critical Step in Authentication

### Audit and Review Checklist
* Complete Authentication Flows: Ensure that all authentication checks are executed fully and cannot be bypassed by omitting parameters, headers, or manipulation of response codes.
* Spoofing Prevention: Do not authenticate requests based solely on easily spoofed metadata such as IP source addresses, HTTP referrers, or unverified client headers.

---

## CWE-1212: Authorization Errors

Weaknesses in this category relate to failures in verifying that an authenticated actor has sufficient rights to perform an action or access a resource.

### Key Weakness Identifiers
* CWE-285: Improper Authorization
* CWE-862: Missing Authorization
* CWE-863: Incorrect Authorization
* CWE-639: Authorization Bypass Through User-Controlled Key ('IDOR')

### Audit and Review Checklist
* Server-Side Authorization: Perform all authorization decisions on the trusted server/backend. Never rely on client-side state or hidden UI elements for access control.
* Contextual Ownership Checks: Whenever accessing an object by an ID or index, verify that the authenticated identity owns or has explicit permission to that specific resource object.

---

## CWE-265: Privilege Issues

Weaknesses in this category relate to improper assignment, drop, or separation of process or user privileges.

### Key Weakness Identifiers
* CWE-250: Execution with Unnecessary Privileges
* CWE-269: Improper Privilege Management
* CWE-272: Least Privilege Violation
* CWE-274: Improper Handling of Insufficient Privileges

### Audit and Review Checklist
* Principle of Least Privilege: Run daemons and worker processes with the minimal privileges required. Drop elevated root/admin privileges immediately after completing privileged initializations (e.g., binding low ports).
* Secure Setuid / Cap Drop: When dropping privileges (`setuid`, `setgid`, Linux capabilities), verify the return values and confirm that privileges cannot be restored or re-acquired.

---

## CWE-275: Permission Issues

Weaknesses in this category relate to incorrect discretionary access control (DAC) permissions on system objects.

### Key Weakness Identifiers
* CWE-732: Incorrect Permission Assignment for Critical Resource
* CWE-276: Incorrect Default Permissions
* CWE-281: Improper Preservation of Permissions

### Audit and Review Checklist
* Restrictive Default Permissions: Ensure newly created files, sockets, and shared memory segments default to private access (`0600` or `0700`).
* Safe Permission Inheritance: Do not inherit overly permissive file creation masks or inherited open file descriptors across `exec` boundaries (`O_CLOEXEC` must be set).

---

## CWE-1216: Lockout Mechanism Errors

Weaknesses in this category relate to mechanisms intended to limit rapid authentication attempts and prevent brute-force attacks.

### Key Weakness Identifiers
* CWE-307: Improper Restriction of Excessive Authentication Attempts
* CWE-645: Overly Restrictive Account Lockout Mechanism

### Audit and Review Checklist
* Rate Limiting & Throttling: Enforce progressive delays or rate-limiting on failed authentication attempts to prevent brute-force attacks.
* Anti-Denial of Service: Ensure account lockout mechanisms cannot be abused by unauthenticated attackers to lock out administrative accounts globally.

---

## CWE-1217: User Session Errors

Weaknesses in this category relate to managing sessions, session identifiers, and user state transitions.

### Key Weakness Identifiers
* CWE-384: Session Fixation
* CWE-613: Insufficient Session Expiration
* CWE-539: Use of Persistent Cookies Containing Sensitive Information

### Audit and Review Checklist
* Session Regeneration: Regenerate session identifiers immediately upon successful authentication to defeat session fixation.
* Session Timeout & Revocation: Enforce both idle and absolute session expiration timers. Provide explicit logout endpoints that invalidate the server-side session state.

---

## CWE-1210: Audit / Logging Errors

Weaknesses in this category relate to inadequate logging of security events or vulnerable logging mechanisms.

### Key Weakness Identifiers
* CWE-778: Insufficient Logging
* CWE-117: Improper Output Neutralization for Logs ('Log Injection')
* CWE-532: Insertion of Sensitive Information into Log File

### Audit and Review Checklist
* Security Audit Events: Record all authentication successes, failures, privilege changes, and critical resource accesses with accurate timestamps and actor identities.
* Log Injection Neutralization: Sanitize log entries by stripping or escaping carriage return (`\r`) and newline (`\n`) characters to prevent log forging.

---

## CWE-840: Business Logic Errors

Weaknesses in this category relate to flaws in the application design where functional workflows can be subverted by unexpected ordering or state sequences.

### Key Weakness Identifiers
* CWE-841: Improper Enforcement of Behavioral Workflow
* CWE-835: Loop with Unreachable Exit Condition ('Infinite Loop')

### Audit and Review Checklist
* Workflow Enforcement: Enforce strict step validation on multi-stage workflows (e.g., checkout, password reset, firmware flashing). Never assume step N can only be reached after step N-1 without verifying state.
* Invariant Verification: Formulate and assert business invariants at both entry and exit points of critical business transactions.

---

## CWE-438: Behavioral Problems

Weaknesses in this category occur when unexpected runtime conditions or external environment states alter application behavior unpredictably.

### Key Weakness Identifiers
* CWE-440: Expected Behavior Violation
* CWE-670: Always-Incorrect Control Flow Implementation

### Audit and Review Checklist
* Predictable Failure Paths: Ensure unexpected signals, interrupts, or hardware faults lead to predictable, safe system shutdowns or fallbacks.

---

## CWE-355: User Interface Security Issues

Weaknesses in this category relate to deceptive, confusing, or vulnerable user interfaces.

### Key Weakness Identifiers
* CWE-1021: Improper Restriction of Rendered UI Layers or Frames ('Clickjacking')
* CWE-451: User Interface (UI) Misrepresentation of Critical Information

### Audit and Review Checklist
* Frame Busting: Use `Content-Security-Policy: frame-ancestors 'none'` or `X-Frame-Options: DENY` on sensitive web interfaces.
* Clarity of Critical Actions: Ensure critical administrative and safety operations display unambiguous confirmation dialogs.

---

## CWE-1225: Documentation Issues

Weaknesses in this category occur when inaccurate, misleading, or missing documentation causes developers or administrators to introduce security vulnerabilities.

### Key Weakness Identifiers
* CWE-1113: Inappropriate Comment Style
* CWE-1053: Missing or Incomplete Documentation of Security Assumptions

### Audit and Review Checklist
* Document Security Assumptions: Explicitly document all assumptions regarding caller privilege, memory ownership, thread-safety, and input constraints in header files and API contracts.
* Avoid Exposing Secrets in Comments: Ensure design comments and TODO notes do not leak architecture secrets or credential defaults.
