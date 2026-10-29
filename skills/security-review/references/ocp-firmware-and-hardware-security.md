# OCP Firmware and Hardware Security (OCP Security & SAFE Reference)

This reference module establishes security audit and design standards for data center hardware, firmware, and platform controllers (e.g., BMC, BIOS, microcontrollers, CPLDs, and accelerators) based on the Open Compute Project (OCP) Security Project and the OCP S.A.F.E. (Security Appraisal Framework and Enablement) program.

---

## 1. OCP Threat Modeling Framework

Under the OCP-SAFE framework, every device and firmware appraisal must be grounded in a formal threat model covering four mandatory components:

### 1.1 Security Objectives
* Define the primary security invariants that must hold under all operating conditions.
* Invariants include:
  * Immutability of the hardware Root of Trust (RoT).
  * Strict anti-rollback enforcement for all mutable firmware slots.
  * Integrity and authenticity guarantees for runtime firmware execution.
  * Confidentiality and non-exportability of platform private keys and eFuse secrets.

### 1.2 Adversarial Model
* Classify threat actors, their access vectors, and their operational capabilities:
  * Remote Network Adversary: Interacts strictly via network endpoints and host-BMC network interfaces.
  * Host-OS Compromised Adversary: Controls tenant operating systems, malicious drivers, and host PCIe/MMIO buses.
  * Local/Physical Opportunistic Adversary: Has temporary physical access to serial consoles, external SPI flash headers, or unauthenticated debug ports.
  * Advanced Persistent Hardware Adversary: Equipped with laboratory equipment capable of non-destructive glitching, voltage manipulation, and side-channel monitoring (Scope 3).

### 1.3 Attack Surface Enumeration
* Systematically catalogue all physical, logical, and bus interfaces:
  * Mailbox and IPC Interfaces: Shared memory, MMIO registers, and ring buffers between host CPU and management processors (BMC).
  * Inter-Chip Buses: I2C, SMBus, I3C, and SPI buses carrying telemetry, control commands, or firmware updates.
  * Diagnostic and Debug Ports: JTAG, SWD, UART serial consoles, and test points.
  * Non-Volatile Storage: External SPI Flash, eMMC, and NVRAM containing boot code, configuration variables, and credentials.

### 1.4 Critical Assets
* Inventory all high-value assets requiring Confidentiality, Integrity, or Availability (CIA) protection:
  * Cryptographic Material: Device identity private keys, attestation keys, HMAC secrets, and RNG entropy seeds.
  * Security State: Anti-rollback counters, eFuse configuration bits, boot stage flags, and lockdown registers.
  * Code Images: First-stage bootloaders (mask ROM), BMC firmware, host BIOS, and peripheral Option ROMs.

---

## 2. OCP-SAFE Three-Tier Review Scopes

The OCP-SAFE program classifies device assessments into three standardized scopes:

### Scope 1: Source Code and Architecture Assessment
A comprehensive whitebox security review of the device ROM and mutable firmware:
* Secure Boot Chain: Verify that the initial program load executes from immutable storage (mask ROM) and cryptographically validates downstream stages before execution.
* Memory Safety: Audit all parsers, network stacks, and inter-chip drivers for temporal and spatial memory safety (CWE-1218, CWE-465).
* Secrets Audit: Ensure complete absence of hardcoded passwords, default keys, test certificates, and factory seeds (CWE-798, CWE-321).
* Interface Lockdown: Verify that debug handlers, diagnostic shells, and development test hooks are stripped or permanently disabled in production builds (CWE-1256).
* Cryptographic Hygiene: Scrutinize algorithm selection (rejecting broken primitives), key derivation paths, and nonce/IV freshness (CWE-310, CWE-320).
* AI-Assisted Scanning: Enforce automated AI-augmented source code review alongside expert manual inspection.

### Scope 2: Complex Architecture and Application Cores
Expands assessment to multi-core interaction, virtualization boundaries, and complex interconnects:
* Inter-core memory isolation, memory protection unit (MPU) configurations, and hardware mailbox arbitration.
* Hypervisor / tenant separation and DMA protection mechanisms (IOMMU).

### Scope 3: Hardware Attack Resistance
Evaluates physical device resilience against non-invasive and semi-invasive hardware attacks:
* Fault Injection Resistance: Resistance against clock glitches, voltage fluctuations, and electromagnetic fault injection (EMFI) during cryptographic signature checks or key decryptions.
* Side-Channel Analysis: Power analysis (DPA/CPA) and electromagnetic analysis (EMA) resistance during private key operations.
* Evaluation Metrics: Scored using the Joint Interpretation Library (JIL) Hardware Attack Potential ratings.

---

## 3. OCP Hardware and Firmware Baseline Controls

### 3.1 Hardware Root of Trust (RoT) and Platform Resiliency
* NIST SP 800-193 Compliance: Implement the three pillars of platform firmware resiliency:
  * Protection: Ensure mutable firmware code cannot be overwritten by unauthorized host software or rogue firmware.
  * Detection: Verify firmware authenticity and integrity cryptographically prior to execution.
  * Recovery: Automatically restore corrupted or maliciously modified firmware to a known good, cryptographically validated recovery image without external intervention.
* Measured Boot & Attestation: Implement DMTF SPDM (Security Protocol and Data Model) to allow remote attestation of hardware identity and measured boot state.

### 3.2 Anti-Rollback Protection
* Monotonic Hardware Counters: Enforce firmware security version numbers (SVN) anchored in hardware eFuses or tamper-proof non-volatile storage.
* Revocation Enforcement: Prevent downgrades to earlier firmware versions containing known security vulnerabilities, even if the older images possess valid cryptographic signatures.

### 3.3 Device Identity Provisioning
* Silicon-Anchored Identity: Leverage DICE (Device Identifier Composition Engine) or IEEE 802.1AR Secure Device Identifiers.
* Key Generation: Derive unique device secrets directly from hardware physical unclonable functions (PUF) or factory-injected root keys that never leave silicon boundaries.

### 3.4 Reproducible Builds and Signing Pipeline
* Deterministic Compilation: Ensure that firmware binaries can be deterministically reproduced bit-for-bit from source to verify supply chain integrity.
* Segregated Signing HSM: Firmware signing keys must reside inside air-gapped or network-isolated Hardware Security Modules (HSM); developers must never possess raw private signing keys.

---

## 4. OCP Controls to CWE Mapping

The following matrix maps OCP firmware and hardware security requirements directly to MITRE CWE identifiers:

| OCP Security Focus Area | Primary CWE IDs | Vulnerability Description |
|---|---|---|
| Hardware Root of Trust | CWE-1274, CWE-1283 | Failure of hardware root of trust; failure to meet minimum hardware security requirements |
| Secure Boot Verification | CWE-347, CWE-353 | Improper verification of cryptographic signature; missing support for integrity check |
| Firmware Anti-Rollback | CWE-1188, CWE-1284 | Insecure default initialization of version counters; improper validation of firmware version |
| Hardware Access Control | CWE-1338, CWE-1256 | Insufficient access control granularity to hardware endpoints; improper interface restriction |
| Physical Debug Lockdown | CWE-1191, CWE-1256 | On-chip debug and test interfaces (JTAG/SWD) left accessible in production |
| Firmware Memory Safety | CWE-1218, CWE-465 | Stack/heap buffer overflows and use-after-free in low-level drivers, parsers, and option ROMs |
| Flash Reading TOCTOU | CWE-367 | Time-of-check time-of-use race condition when copying external SPI flash into SRAM/DRAM |
| Secrets Management | CWE-798, CWE-321 | Use of hardcoded credentials or encryption keys embedded in firmware binaries or ROM |
| Inter-Chip Bus Security | CWE-319, CWE-300 | Cleartext transmission of sensitive commands/keys across I2C/SMBus/SPI interconnects |
| Hardware Fault Resistance | CWE-1294, CWE-1300 | Insecure security hardware cores vulnerable to physical fault injection or power analysis |

---

## 5. OCP-SAFE Reporting Standards (Short-Form Report)

When documenting security findings for data center firmware and hardware components:
* Finding Attribution: Every finding must include an explicit CWE identifier and a CVSS v3.1/v4.0 vector (or JIL score for Scope 3 hardware findings).
* Vulnerability Summaries: Summaries must detail the attack scenario, required attacker access, and impact on the Cloud Service Provider (CSP) infrastructure.
* Remediation Verification: Specify verifiable firmware or hardware mitigations (e.g., eFuse blowing, parser rewrite, input bounds enforcement).
