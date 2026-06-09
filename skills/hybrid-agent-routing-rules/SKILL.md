---
name: hybrid-agent-routing-rules
description: Standard Operating Procedure (SOP) for Edge-Cloud Collaboration, Task Routing, and Privacy Management of Hybrid AI Agents
version: 1.0
related: "[[SplitAgent]], [[Intent-Based Routing]], [[Confidence Cascading]]"
---

# Hybrid AI Agent Work Routing and Collaboration Rules

This rule aims to define the task allocation logic in a multi-tier AI Agent system. By combining local Small Language Models (SLMs) with cloud Large Language Models (LLMs) through "Intelligent Routing", it achieves the optimal balance of **privacy compliance, ultra-low latency, and cost optimization**.

## 1. Foundation Inference Tier Definitions

All computing resources in the system are divided into three tiers, and the router must dispatch tasks based on this classification:

*   **Tier 1: Local / Edge Computing**
    *   **Configuration**: 1B~14B quantized models (such as Qwen3-8B, Llama 3.3-8B, etc.) running on endpoint devices.
    *   **Applicable Tasks**: High-frequency and well-defined tasks (such as text classification, entity extraction, formatting, intent detection), as well as all privacy-sensitive operations.
*   **Tier 2: Private Cloud / Organizational Intranet**
    *   **Configuration**: 14B~70B models deployed on internal enterprise GPU servers.
    *   **Applicable Tasks**: Tasks requiring longer context or moderate reasoning complexity, but where data is strictly forbidden from leaving the organization's firewall due to regulatory constraints.
*   **Tier 3: Frontier Cloud**
    *   **Configuration**: Calls to powerful cloud APIs (such as Claude Opus, GPT-4.5, Gemini 2.5 Pro, etc.).
    *   **Applicable Tasks**: Complex reasoning, deep comprehensive analysis of long documents, cross-domain planning, and novel open-ended problem solving.

---

## 2. Task Routing Rules

### Rule 1: Privacy-Tiered Routing
1. **Data Classification Scanning**: All requests must be scanned by a local PII (Personally Identifiable Information) and sensitive data classifier prior to routing.
2. **Mandatory Local Lock-in**: If internal confidential information, financial records, or regulated customer data is involved, the task is strictly locked to Tier 1 or Tier 2 for processing and is forbidden from being sent to the cloud.
3. **Context-Aware Dynamic Desensitization (SplitAgent Collaboration)**: If a complex task must leverage Tier 3 computing power, a local "Privacy Agent" must be triggered to perform dynamic data desensitization.
    *   *Contract Review*: Hide party names and monetary amounts, preserving the legal clause structure.
    *   *Code Review*: Remove password credentials and internal URLs, preserving syntax structure and API patterns.
    *   The Tier 3 "Reasoning Agent" is only allowed to receive these de-identified abstract details for logical computation.

### Rule 2: Complexity-Based Routing
1. **Static Rule Allocation**: Clear and narrow tasks (such as speech-to-text, vector embedding generation, simple JSON extraction) are always routed to Tier 1 by default to avoid wasting expensive cloud tokens.
2. **Complexity Assessment**: For ambiguous tasks, lightweight classifiers can be used to score the "degree of ambiguity" and "reasoning depth requirement". High-scoring requests are directly allocated to Tier 3.

### Rule 3: Confidence Cascading
To maximize the benefit of local computing power, a cascading escalation mechanism must be implemented:
1. **Local Priority Attempt**: All non-statically allocated requests are processed by the Tier 1 model by default.

## 5. Implementation Details

### Privacy‑Agent API
* **Provider**: OpenAI (e.g., `gpt‑4o‑mini` or `gpt‑4o`).  
* **Request format**: JSON payload containing the raw user request and a `metadata` object (`request_id`, `timestamp`).  
* **Response format**: JSON with the fields:
  ```json
  {
    "redacted_text": "<string>",
    "redaction_map": {
      "PII": ["<NAME_1>", "<NAME_2>"],
      "CREDENTIALS": ["<PASS_1>"]
    },
    "status": "success" | "error",
    "error_message": "<optional>"
  }
  ```
* **Error handling**: On `error` fallback to Tier‑1 processing with original text and log the incident.

### Complexity Classifier
* **Scope**: Deployed as a **single service** reachable by all three tiers.  
* **Inputs**: Raw request text, optional context size.  
* **Outputs**:
  - `ambiguity_score` (0 – 1)  
  - `reasoning_depth_score` (0 – 1)  
  - `tier_suggestion` (`1`, `2`, or `3`).  
* **Thresholds** (tune in production):
  - `ambiguity_score > 0.7` **or** `reasoning_depth_score > 0.8` ⇒ suggest Tier‑3.
  - Otherwise default to Tier‑1 unless privacy rules force higher tier.

### Confidence Cascading Threshold
* **Local confidence cutoff**: `0.75`. Below this value the request is escalated to Tier‑3.  
* **Circuit‑breaker**: If > 30 % of requests in the last 5 min exceed the cutoff, raise an alert and temporarily disable escalation (fallback to rule‑based routing).
2. **Dynamic Escalation**: If the "confidence score" output by the local model is below a safety threshold, exhibits high entropy (hesitation), or produces self-contradictions, the system should automatically discard the local result and seamlessly escalate the task to Tier 3.
3. **Circuit Breaker**: Continuously monitor the escalation ratio. If the proportion of tasks escalated to the cloud exceeds 30% (indicating potential quality degradation in the local model due to updates or VRAM pressure), the system should trigger an alert and temporarily disable confidence cascading, falling back to pure rule-based routing to prevent out-of-control costs.

---

## 3. High-Level Multi-Agent Collaboration Patterns

In a hybrid architecture, interactions between multiple Agents should follow these high-efficiency patterns:

1. **Advisor / Generator-Verifier Pattern**:
   * **Rule**: A Tier 1 local model (low cost) rapidly generates an initial draft or solution; the result is then handed to a Tier 3 frontier cloud model for "review, critique, or verification."
   * **Advantage**: The cloud model does not generate from scratch, but merely acts as a gatekeeper. This significantly saves token consumption while maintaining extremely high final output quality.

2. **Orchestrator-Subagent Pattern**:
   * **Rule**: A main Agent is responsible for receiving global tasks, breaking them down into subtasks, and dispatching them to dedicated subagents (e.g., assigning data lookup to a Search Agent, and analysis to a Financial Agent). Subagents report their results upon completion.
   * **Advantage**: Keeps the main Agent's context clean, avoiding hallucinations caused by pollution from massive amounts of irrelevant information.

---

## 4. State & Infrastructure Constraints

1. **Stateless Cloud Reasoning**: Cloud models (Tier 3) should merely be treated as stateless reasoning engines. The Agent's "long-term memory," "project state," and tool usage logs must be persistently stored locally (e.g., in a local SQLite database).
2. **Local Channel First**: If a cloud LLM needs to access the local file system or knowledge base, it must communicate via low-level standard input/output (STDIO) through a local Model Context Protocol (MCP) server, ensuring data is not directly exposed to the external internet.
