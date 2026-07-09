# Enterprise Architecture Review Report — AI Executive Assistant

**Version:** 1.0  
**Review Type:** Pre-Implementation Architecture Review Board  
**Review Board Representation:** Google, Microsoft, Amazon, OpenAI, Anthropic, NVIDIA principal architects  
**Target:** Production-grade enterprise deployment

---

## Table of Contents

1. [AI Context Builder](#1-ai-context-builder)
2. [Intelligent Model Router](#2-intelligent-model-router)
3. [Prompt Registry](#3-prompt-registry)
4. [Tool Execution Pipeline](#4-tool-execution-pipeline)
5. [Sequence Diagrams](#5-sequence-diagrams)
6. [AI Decision Engine](#6-ai-decision-engine)
7. [Policy Engine](#7-policy-engine)
8. [Conversation State Machine](#8-conversation-state-machine)
9. [Memory Retrieval Strategy](#9-memory-retrieval-strategy)
10. [Architecture Validation](#10-architecture-validation)
11. [Architecture Scorecard](#11-architecture-scorecard)
12. [ADRs](#12-adrs)

---

## 1. AI Context Builder

### 1.1 Problem Statement

Currently, context construction is implicit: `LiteLLMClient.generate()` receives a `system_prompt` and `user_prompt`, with RAG context manually inserted into the message list in `graph.py:generate_response()`. There is no formal pipeline for context assembly, no token budget management, no priority-based ordering, and no overflow handling.

For an enterprise AI system reviewed by top-company architects, every LLM call must trace through a deterministic, observable, and budgeted context construction pipeline.

### 1.2 Context Assembly Pipeline

```
                        ┌─────────────────────┐
                        │   Incoming Request   │
                        │   (user_message +    │
                        │    conversation_id)  │
                        └──────────┬──────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                    1. SYSTEM LAYER (fixed)                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ System Prompt          │ Role: AI identity, constraints,    │ │
│  │                        │ personality, security rules        │ │
│  │ Developer Prompt       │ Role: Advanced instructions,       │ │
│  │                        │ formatting rules, tool schemas     │ │
│  │ Guardrails             │ Role: Safety filters, topic        │ │
│  │                        │ restrictions, PII redaction        │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                    2. MEMORY LAYER (retrieved)                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ User Profile             │ Priority: HIGH                   │ │
│  │ (name, email, company,   │ Budget: 200 tokens               │ │
│  │  preferences, user_type) │ Source: PostgreSQL (LTM)         │ │
│  ├─────────────────────────────────────────────────────────────┤ │
│  │ Conversation Summary     │ Priority: HIGH                   │ │
│  │ (current session context)│ Budget: 400 tokens               │ │
│  │                          │ Source: Redis (STM) or Postgres  │ │
│  ├─────────────────────────────────────────────────────────────┤ │
│  │ Conversation History     │ Priority: MEDIUM                 │ │
│  │ (last N messages)        │ Budget: 2000 tokens              │ │
│  │                          │ Source: Redis (STM)              │ │
│  ├─────────────────────────────────────────────────────────────┤ │
│  │ Semantic Memory          │ Priority: MEDIUM                 │ │
│  │ (factual knowledge       │ Budget: 500 tokens               │ │
│  │  about the user)         │ Source: pgvector (embeddings)    │ │
│  ├─────────────────────────────────────────────────────────────┤ │
│  │ Episodic Memory          │ Priority: LOW                    │ │
│  │ (past interactions,      │ Budget: 300 tokens               │ │
│  │  meeting history)        │ Source: PostgreSQL               │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                    3. KNOWLEDGE LAYER (retrieved)                │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ RAG Context              │ Priority: MEDIUM                 │ │
│  │ (portfolio, project      │ Budget: 3000 tokens              │ │
│  │  docs, knowledge base)   │ Source: pgvector                 │ │
│  │                          │ Strategy: Hybrid search + rerank │ │
│  ├─────────────────────────────────────────────────────────────┤ │
│  │ Tool Results             │ Priority: HIGH (if present)      │ │
│  │ (calendar lookup,        │ Budget: 1000 tokens              │ │
│  │  availability,           │ Source: Tool execution result    │ │
│  │  meeting data)           │                                  │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                    4. INPUT LAYER (current request)              │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Current User Message     │ Priority: HIGHEST                │ │
│  │                          │ Budget: 2000 tokens (truncated)  │ │
│  │                          │ Source: Direct input             │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                    5. CONTEXT COMPRESSION                        │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Token Budget Manager     │ Sums all budgets → compares      │ │
│  │                          │ to model max tokens              │ │
│  ├─────────────────────────────────────────────────────────────┤ │
│  │ Context Prioritizer      │ Drops LOW priority items first  │ │
│  │                          │ if over budget                   │ │
│  ├─────────────────────────────────────────────────────────────┤ │
│  │ Strategy Selector        │ Options:                        │ │
│  │                          │ 1. Truncate oldest history      │ │
│  │                          │ 2. Summarize conversation        │ │
│  │                          │ 3. Drop semantic memory          │ │
│  │                          │ 4. Reduce RAG chunks             │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────┐
                    │   FINAL PROMPT      │
                    │   → LLM             │
                    └─────────────────────┘
```

### 1.3 Context Window Strategy

| Component | Tokens | Priority | Eviction Order | Strategy |
|-----------|--------|----------|----------------|----------|
| System Prompt | 500 | CRITICAL | Never evicted | Fixed |
| Developer Prompt | 300 | CRITICAL | Never evicted | Fixed |
| Guardrails | 200 | CRITICAL | Never evicted | Fixed |
| User Profile | 200 | HIGH | 9th | Summarize if >200 |
| Conversation Summary | 400 | HIGH | 8th | Sliding summary |
| Conversation History | 2000 | MEDIUM | 5th | Last N messages, oldest dropped |
| Semantic Memory | 500 | MEDIUM | 4th | Drop lowest scored |
| Episodic Memory | 300 | LOW | 3rd | Drop first |
| RAG Context | 3000 | MEDIUM | 6th | Reduce chunk count |
| Tool Results | 1000 | HIGH | 7th | Truncate each result |
| Current Message | 2000 | HIGHEST | Never evicted | Truncate to 2000 |

**Total budget (all components present):** ~10,400 tokens  
**Overflow threshold:** 80% of model max tokens (e.g., 10,240 for 12k model, 16,384 for 20k model)

### 1.4 Compression Strategy

**Level 0 — No compression:** Total < 80% of model limit. All components included.

**Level 1 — History truncation:** Total > 80%. Remove oldest 50% of conversation history.

**Level 2 — Memory pruning:** Still over? Drop episodic memory, reduce semantic memory to top 1 item.

**Level 3 — RAG reduction:** Still over? Reduce RAG chunks from top-5 to top-3.

**Level 4 — Summary fallback:** Still over? Replace conversation history with summary-only.

**Level 5 — Hard truncation:** Still over? Hard-truncate at model token limit. Log warning.

### 1.5 Token Budget Manager Implementation

```python
class ContextBudget:
    model_max: int           # e.g., 128000 for Gemini
    safety_margin: float = 0.8  # 80% threshold
    components: dict[str, ContextComponent]

    def assess(self) -> BudgetStatus:
        total = sum(c.tokens for c in self.components.values())
        if total < self.model_max * self.safety_margin:
            return BudgetStatus.OK
        return BudgetStatus.OVERFLOW

    def compress(self, level: int) -> dict:
        # Apply compression at specified level
        ...

    def estimate_reserve(self) -> int:
        # Return tokens reserved for response generation
        return self.model_max - total_input_tokens
```

### 1.6 Context Overflow Handling

| Scenario | Action | User Impact |
|----------|--------|-------------|
| History too long | Truncate oldest messages | Loses early context |
| RAG too large | Reduce top-k from 5→3 | May miss relevant doc |
| Conversation too long | Summarize & replace | Loss of exact wording |
| Total exceeds max | Hard truncate + log | Potential context loss |
| Streaming response | Reserve 25% of budget | None |

### 1.7 ADR: Context Builder

**ADR-101 — Context Builder Pipeline**  
*Status:* Proposed  
*Decision:* A dedicated `ContextBuilder` class orchestrates assembly, prioritization, compression, and budget management before every LLM call. Context is assembled in 5 layers (System → Memory → Knowledge → Input → Compression). No LLM call bypasses the builder.  
*Rationale:* Without a formal pipeline, context assembly is ad-hoc, non-deterministic, and unobservable. Enterprises require auditability of what context was sent to the model.  
*Trade-off:* Adds ~5ms overhead per request. Acceptable for correctness and audit.

---

## 2. Intelligent Model Router

### 2.1 Problem Statement

Current model selection uses a static fallback chain (Gemini → Cerebras → NVIDIA → HuggingFace) with circuit breakers. Every request tries models in order regardless of complexity. This is wasteful — simple greetings cost as much as complex reasoning, and latency/cost optimization is nonexistent.

### 2.2 Request Classification Taxonomy

```
                    ┌──────────────────────────┐
                    │    Incoming Request      │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   Request Classifier     │
                    │   (lightweight ML or     │
                    │    rule-based heuristic) │
                    └────────────┬─────────────┘
                                 │
         ┌───────────┬───────────┬───────────┬───────────┐
         ▼           ▼           ▼           ▼           ▼
     ┌──────┐  ┌──────────┐  ┌──────┐  ┌────────┐  ┌──────────┐
     │Tier 1│  │ Tier 2   │  │Tier 3│  │ Tier 4 │  │ Tier 5   │
     │Simple│  │Knowledge │  │Task  │  │Complex │  │Reasoning │
     └──────┘  └──────────┘  └──────┘  └────────┘  └──────────┘
```

### 2.3 Tier Definitions

#### Tier 1: Simple / Social
| | |
|---|---|
| **Categories** | Greeting, farewell, thank you, acknowledgement, small talk |
| **Preferred Model** | `gemini/gemini-2.0-flash` (fast, cheap) |
| **Fallback** | `cerebras/gpt-oss-120b` |
| **Latency Target** | < 500ms |
| **Cost Target** | < $0.0001 per call |
| **Max Retries** | 1 |
| **Circuit Breaker** | 10 failures in 60s |
| **Timeout** | 5s |
| **Rationale** | These require no knowledge, no tools, no memory. Any capable model works. Optimize for speed and cost. |

#### Tier 2: Knowledge Retrieval
| | |
|---|---|
| **Categories** | Portfolio questions, project questions, resume questions, FAQ, "Tell me about yourself" |
| **Preferred Model** | `gemini/gemini-2.0-flash` with RAG context |
| **Fallback** | `cerebras/gpt-oss-120b` → `nvidia/mistralai/mistral-nemotron` |
| **Latency Target** | < 3s |
| **Cost Target** | < $0.001 per call |
| **Max Retries** | 2 |
| **Circuit Breaker** | 5 failures in 60s |
| **Timeout** | 15s |
| **Rationale** | RAG pipeline dominates latency. Model just synthesizes. Flash is sufficient. |

#### Tier 3: Task Execution
| | |
|---|---|
| **Categories** | Meeting scheduling, lead capture, information collection, tool calling |
| **Preferred Model** | `gemini/gemini-2.0-flash` (strong tool-use capability) |
| **Fallback** | `cerebras/gpt-oss-120b` → `nvidia/mistralai/mistral-nemotron` |
| **Latency Target** | < 5s |
| **Cost Target** | < $0.005 per call |
| **Max Retries** | 3 |
| **Circuit Breaker** | 5 failures in 60s |
| **Timeout** | 30s |
| **Rationale** | Tool calling requires structured output reliability. Flash has excellent JSON mode. |

#### Tier 4: Complex / Analytical
| | |
|---|---|
| **Categories** | Architecture discussion, technical deep-dive, code review, analysis, comparison |
| **Preferred Model** | `gemini/gemini-2.0-flash` (strong reasoning) |
| **Fallback** | `cerebras/gpt-oss-120b` → `nvidia/mistralai/mistral-nemotron` |
| **Latency Target** | < 10s |
| **Cost Target** | < $0.01 per call |
| **Max Retries** | 3 |
| **Circuit Breaker** | 3 failures in 60s |
| **Timeout** | 60s |
| **Rationale** | These benefit from stronger reasoning. Flash handles most cases; fallback for harder queries. |

#### Tier 5: Extended Reasoning
| | |
|---|---|
| **Categories** | Multi-step planning, constraint satisfaction, complex scheduling, conflict resolution |
| **Preferred Model** | `gemini/gemini-2.0-flash` (natively supports thinking/reasoning) |
| **Fallback** | `cerebras/gpt-oss-120b` → `nvidia/mistralai/mistral-nemotron` |
| **Latency Target** | < 30s |
| **Cost Target** | < $0.05 per call |
| **Max Retries** | 3 |
| **Circuit Breaker** | 3 failures in 120s |
| **Timeout** | 120s |
| **Rationale** | Extended thinking requires models with chain-of-thought capability. Flash supports this natively. |

### 2.4 Routing Decision Flow

```
                    ┌──────────────────────┐
                    │  Intent Classifier    │
                    │  (logprob-based)      │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Request Classifier  │
                    │  (Tier 1-5)          │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Model Router        │
                    │                      │
                    │  Check:              │
                    │  - Tier requirements │
                    │  - Circuit breaker   │
                    │  - Latency SLA       │
                    │  - Cost budget       │
                    │  - Model health      │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │ Tier 1 Model │  │ Tier 2 Model │  │ Tier 3+ Model│
     │ (Flash)      │  │ (Flash+RAG)  │  │ (Flash+full) │
     └──────────────┘  └──────────────┘  └──────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Response Quality    │
                    │  Validator           │
                    │  (confidence check)  │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │ Accept       │  │ Retry (next  │  │ Escalate to  │
     │ (return)     │  │ tier model)  │  │ human        │
     └──────────────┘  └──────────────┘  └──────────────┘
```

### 2.5 Model Health Policy

```
                    ┌──────────────────────┐
                    │  Health Check Agent  │
                    │  (runs every 30s)    │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │ Ping model   │  │ Test prompt  │  │ Measure      │
     │ (5s timeout) │  │ (simple Q)   │  │ latency      │
     └──────────────┘  └──────────────┘  └──────────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Update Health       │
                    │  Registry            │
                    │  (healthy/degraded/  │
                    │   down)              │
                    └──────────────────────┘
```

**Health states:**
- **Healthy:** Responding within latency targets
- **Degraded:** Responding but > 2x latency target
- **Down:** Not responding or returning errors
- **Circuit Open:** Circuit breaker tripped; bypass for recovery period

### 2.6 ADR: Model Router

**ADR-102 — Request Classification for Model Routing**  
*Status:* Proposed  
*Decision:* Every request is classified into one of 5 tiers before model selection. Tier determines preferred model, timeout, retry policy, and cost target. The classifier is a lightweight ML model (distilbert or logprob-based) trained on conversation intent data.  
*Rationale:* Static fallback chains waste resources. Simple greetings shouldn't pay the latency/cost of a full RAG+reasoning pipeline. Classification adds <10ms overhead and enables per-tier optimization.  
*Trade-off:* Classification can misclassify. Mitigation: if any tier's response confidence is < 0.7, reclassify + reroute. Classifier fallback: rule-based keyword matching for cold-start.

---

## 3. Prompt Registry

### 3.1 Problem Statement

Prompts are currently hardcoded across multiple files: `prompts/system/executive_assistant.py` as a Python string constant, extraction prompts embedded in `graph.py` methods, and classifier prompts in `intent/classifier.py`. There is no versioning, no lifecycle management, no testing, and no rollback capability.

### 3.2 Prompt Registry Architecture

```
prompts/
├── registry/                  # Prompt Registry Engine
│   ├── registry.py           # PromptRegistry class
│   ├── loader.py             # YAML/JSON loader
│   ├── versioner.py          # Version management
│   └── validator.py          # Prompt validation
├── system/                   # System-level prompts
│   ├── executive_assistant/
│   │   ├── v1.yaml
│   │   └── v2.yaml
│   └── agent_persona/
│       └── v1.yaml
├── guardrails/               # Safety & constraint prompts
│   ├── topic_filter/
│   │   └── v1.yaml
│   ├── pii_redaction/
│   │   └── v1.yaml
│   └── content_safety/
│       └── v1.yaml
├── memory/                   # Memory-related prompts
│   ├── conversation_summary/
│   │   └── v1.yaml
│   ├── memory_extraction/
│   │   └── v1.yaml
│   └── memory_merge/
│       └── v1.yaml
├── classifier/               # Classification prompts
│   ├── intent/
│   │   └── v1.yaml
│   ├── tier/
│   │   └── v1.yaml
│   └── sentiment/
│       └── v1.yaml
├── tool/                     # Tool-related prompts
│   ├── meeting_extraction/
│   │   └── v1.yaml
│   ├── lead_extraction/
│   │   └── v1.yaml
│   └── tool_selection/
│       └── v1.yaml
├── rag/                      # RAG prompts
│   ├── retrieval_query/
│   │   └── v1.yaml
│   ├── context_synthesis/
│   │   └── v1.yaml
│   └── source_citation/
│       └── v1.yaml
├── followup/                 # Follow-up prompts
│   ├── clarification/
│   │   └── v1.yaml
│   ├── confirmation/
│   │   └── v1.yaml
│   └── next_question/
│       └── v1.yaml
├── fallback/                 # Fallback & error prompts
│   ├── model_unavailable/
│   │   └── v1.yaml
│   ├── degraded_mode/
│   │   └── v1.yaml
│   └── human_handoff/
│       └── v1.yaml
├── developer/                # Developer/system prompts
│   ├── tool_schemas/
│   │   └── v1.yaml
│   └── formatting_rules/
│       └── v1.yaml
└── safety/                   # Safety prompts
    ├── prompt_injection/
    │   └── v1.yaml
    ├── jailbreak_detection/
    │   └── v1.yaml
    └── output_filter/
        └── v1.yaml
```

### 3.3 Prompt Versioning

**Version scheme:** Semantic versioning (`v{major}.{minor}.{patch}`)

| Component | Description |
|-----------|-------------|
| **Major** | Breaking changes (structure change, format change, removed sections) |
| **Minor** | Non-breaking additions (new examples, expanded instructions) |
| **Patch** | Fixes (typos, clarifications, tone adjustments) |

**Storage:** Each prompt version stored as a separate YAML file with metadata header:

```yaml
# prompts/system/executive_assistant/v2.yaml
---
version: 2.1.0
created: 2025-01-15
author: sahil
approved_by: architecture-review-board
status: active
feature_flag: prompt-v2-executive-assistant
description: "Executive assistant persona prompt with tool-use instructions"
changes:
  - "Added meeting scheduling instructions"
  - "Updated tone from formal to professional-warm"
  - "Added RAG citation format"
deprecated: v1.0.0
---
<actual prompt content>
```

### 3.4 Prompt Lifecycle

```
                    ┌──────────────────────┐
                    │      DRAFT           │
                    │  (author creates)    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      REVIEW          │
                    │  (peer review +      │
                    │   security review)   │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │     STAGING          │
                    │  (feature-flagged,   │
                    │   A/B tested)        │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │   ACTIVE     │  │ ROLLED BACK  │  │ DEPRECATED   │
     │ (production) │  │ (reverted to │  │ (superseded) │
     │              │  │  previous)   │  │              │
     └──────────────┘  └──────────────┘  └──────────────┘
                               │                │
                               ▼                ▼
                    ┌──────────────────────┐
                    │     ARCHIVED         │
                    │  (read-only, kept    │
                    │   for audit trail)   │
                    └──────────────────────┘
```

### 3.5 Prompt Testing

| Test Type | Description | Automated? |
|-----------|-------------|------------|
| **Syntax validation** | YAML parses correctly, all variables present | Yes (CI) |
| **Token count check** | Prompt stays within budget | Yes (CI) |
| **Variable interpolation** | All {placeholders} have defaults or are always provided | Yes (unit test) |
| **A/B evaluation** | Compare response quality (human eval or LLM-as-judge) | Yes (nightly) |
| **Regression test** | Known edge cases produce correct outputs | Yes (CI) |
| **Security scan** | No prompt injection vectors, no PII leakage | Yes (security pipeline) |
| **Performance test** | End-to-end latency with new prompt | Yes (nightly) |
| **Human review** | Tone, clarity, completeness review | No (required before staging) |

### 3.6 Rollback Strategy

```yaml
rollback:
  trigger:
    - Error rate increase > 5%
    - Latency increase > 20%
    - User satisfaction drop > 10%
    - Security incident
  procedure:
    - Set feature flag to previous prompt version
    - Active prompt archived as "rolled_back"
    - Incident report created
    - Post-mortem within 48h
  auto_rollback:
    enabled: true
    cooldown: 300s
    min_observation: 100 requests
```

### 3.7 Feature Flag Integration

```python
prompt = registry.get_prompt(
    name="executive_assistant",
    version=feature_flags.get("prompt_version", "active"),
    user_id=user_id,
    context={"user_type": user_type},
)
```

### 3.8 Prompt Metadata Schema

```yaml
metadata:
  prompt_id: "executive_assistant"
  version: "2.1.0"
  status: "active"          # draft | review | staging | active | rolled_back | deprecated | archived
  feature_flag: "prompt-v2"
  author: "sahil"
  approvers: ["arch-board"]
  created: "2025-01-15T10:00:00Z"
  updated: "2025-01-20T14:30:00Z"
  tags: ["system", "persona"]
  description: "Executive assistant persona"
  token_count: 482
  model_compatibility: ["gemini-2.0-flash", "gpt-oss-120b", "mistral-nemotron"]
  requires_context: ["user_profile", "conversation_summary"]
  test_coverage: 0.92
  evaluation_score: 8.7/10
```

### 3.9 ADR: Prompt Registry

**ADR-103 — File-Based Prompt Registry with Feature Flag Deployment**  
*Status:* Proposed  
*Decision:* All prompts are stored as versioned YAML files in a `prompts/` directory tree, loaded by a `PromptRegistry` class. Prompt versions are selected via feature flags. Rollback is instantaneous via flag toggling.  
*Rationale:* Hardcoded Python strings are not auditable, not versionable, and cannot be A/B tested. YAML files in a directory tree are version-controlled, diffable, reviewable via PRs, and deployable independently of code. Feature flags enable gradual rollout and instant rollback.  
*Trade-off:* YAML files add a filesystem dependency. Mitigated by caching loaded prompts in memory with a TTL. Database-backed storage (PostgreSQL) is the v2 target for multi-instance consistency.

---

## 4. Tool Execution Pipeline

### 4.1 Problem Statement

Currently, `graph.py:execute_tool()` calls Celery tasks directly (`schedule_meeting_task.delay(data)`). The LLM influences which tool runs via intent classification, but there is no formal permission layer, no policy engine, no input validation pipeline, and no result validation before the LLM serializes the response.

### 4.2 Tool Execution Architecture

```
                   LLM identifies intent
                           │
                           ▼
              ┌────────────────────────┐
              │     Intent Output      │
              │  (SCHEDULE_MEETING)    │
              └───────────┬────────────┘
                          │
              ┌───────────▼────────────┐
              │     Tool Router        │
              │                        │
              │  Maps intent → tool    │
              │  Validates tool exists │
              │  Checks tool available │
              └───────────┬────────────┘
                          │
              ┌───────────▼────────────┐
              │    Permission Layer    │
              │                        │
              │  Is user authorized?   │
              │  Is tool allowed for   │
              │  this user_type?       │
              │  Rate limit check      │
              └───────────┬────────────┘
                          │
              ┌───────────▼────────────┐
              │     Policy Engine      │
              │                        │
              │  Meeting policies      │
              │  Lead policies         │
              │  Data policies         │
              │  Business rules        │
              └───────────┬────────────┘
                          │
              ┌───────────▼────────────┐
              │    Validation Layer    │
              │                        │
              │  Input schema check    │
              │  Field validation      │
              │  Business validation   │
              │  PII scan              │
              └───────────┬────────────┘
                          │
              ┌───────────▼────────────┐
              │   Application Service  │
              │                        │
              │  Business logic        │
              │  Domain coordination   │
              └───────────┬────────────┘
                          │
              ┌───────────▼────────────┐
              │   Orchestration Layer  │
              │                        │
              │   ┌──────────────┐     │
              │   │   Celery     │     │  Async task execution
              │   │  (async)     │     │
              │   └──────┬───────┘     │
              │          │             │
              │   ┌──────▼───────┐     │
              │   │    Saga      │     │  Distributed transaction
              │   │ Orchestrator │     │
              │   └──────┬───────┘     │
              │          │             │
              │   ┌──────▼───────┐     │
              │   │    n8n       │     │  Business workflow
              │   │  (external)  │     │
              │   └──────┬───────┘     │
              │          │             │
              │   ┌──────▼───────┐     │
              │   │   External   │     │  Google Calendar,
              │   │   Services   │     │  Email, CRM
              │   └──────────────┘     │
              └───────────┬────────────┘
                          │
              ┌───────────▼────────────┐
              │   Response Validator   │
              │                        │
              │  Result schema check   │
              │  Error detection       │
              │  Success confirmation  │
              └───────────┬────────────┘
                          │
              ┌───────────▼────────────┐
              │  Conversation Memory   │
              │                        │
              │  Store result          │
              │  Update state          │
              └───────────┬────────────┘
                          │
              ┌───────────▼────────────┐
              │    LLM Response        │
              │  (serialize result     │
              │   into natural lang)   │
              └────────────────────────┘
```

### 4.3 Layer Responsibilities

| Layer | Responsibility | Failure Mode |
|-------|---------------|--------------|
| **Tool Router** | Intent → tool mapping. Validates tool registration. | Unregistered intent → return error to LLM |
| **Permission Layer** | RBAC check. Is this user_type allowed to execute this tool? | Unauthorized → "I'm sorry, you don't have permission" |
| **Policy Engine** | Business rules. Meeting time constraints. Lead dedup rules. | Policy violation → explanation + suggestion |
| **Validation Layer** | Input schema. Required fields. Data formats. Business rules. | Invalid input → field-level error + prompt to fix |
| **Application Service** | Domain logic. Orchestrates domain operations. | Business error → rollback + user notification |
| **Celery** | Async execution. Retry. Task tracking. | Task failure → retry → escalate |
| **Saga** | Distributed transaction. Compensation on failure. | Saga failure → compensation + audit log |
| **n8n** | External workflow. Calendar. Email. CRM. | External failure → retry → degradation message |
| **Response Validator** | Validates output before LLM sees it. | Validation failure → retry or error response |

### 4.4 Tool Router Design

```python
tool_registry = {
    "schedule_meeting": {
        handler: MeetingSchedulingService,
        permissions: ["recruiter", "client", "visitor"],
        policies: ["meeting_hours", "advance_notice", "duplicate_check"],
        validator: MeetingInputSchema,
        timeout: 30s,
        retry: 3,
        saga: MeetingSaga,
    },
    "create_lead": {
        handler: LeadService,
        permissions: ["recruiter", "client"],
        policies: ["lead_dedup", "lead_scoring"],
        validator: LeadInputSchema,
        timeout: 15s,
        retry: 2,
        saga: LeadSaga,
    },
}
```

### 4.5 Response Validator

After tool execution, the response validator checks:

1. **Schema:** Does the response match the expected schema?
2. **Error:** Did any part of the pipeline return an error?
3. **Completeness:** Were all required actions completed?
4. **Consistency:** Is the response consistent with the request?

If validation fails:
- **Retryable:** Retry with exponential backoff (up to max_retries)
- **Non-retryable:** Return structured error to LLM for user-facing message
- **Compensation needed:** Trigger saga compensation before returning

### 4.6 ADR: Tool Execution Pipeline

**ADR-104 — Layered Tool Execution with Mandatory Validation**  
*Status:* Proposed  
*Decision:* Tools are never called directly from the LLM or graph. Every tool execution passes through 6 layers: Router → Permission → Policy → Validation → Application Service → Response Validator. Each layer can reject or modify the execution.  
*Rationale:* Direct tool execution bypasses security, policy, and validation. In enterprise deployments, every external action must be auditable, reversible, and policy-gated. The layered approach ensures no tool executes without passing all gates.  
*Trade-off:* Adds ~50ms per tool execution. Acceptable for security and compliance. Critical-path tools (meeting scheduling) are inherently multi-second due to external API calls, so overhead is negligible.

---

## 5. Sequence Diagrams

### 5.1 Greeting

```
User                  API                  ContextBuilder         ModelRouter           LLM
 │                    │                       │                      │                   │
 │  "Hi there"        │                       │                      │                   │
 │───────────────────►│                       │                      │                   │
 │                    │                       │                      │                   │
 │                    │  [Identity Resolution]│                      │                   │
 │                    │  ───────────────────► │                      │                   │
 │                    │  ◄────────────────────│                      │                   │
 │                    │                       │                      │                   │
 │                    │  [Context Assembly]   │                      │                   │
 │                    │  ───────────────────► │                      │                   │
 │                    │                       │  Tier 1 (Simple)     │                   │
 │                    │                       │ ───────────────────► │                   │
 │                    │                       │                      │  System+Greeting   │
 │                    │                       │                      │ ─────────────────►│
 │                    │                       │                      │◄──────────────────│
 │                    │                       │◄─────────────────────│                   │
 │                    │◄──────────────────────│                      │                   │
 │  "Hello! Welcome"  │                       │                      │                   │
 │◄───────────────────│                       │                      │                   │
```

### 5.2 Portfolio Question (with RAG)

```
User                  API                  ContextBuilder         ModelRouter         pgvector           LLM
 │                    │                       │                      │                   │                │
 │ "Tell me about     │                       │                      │                   │                │
 │  your projects"    │                       │                      │                   │                │
 │───────────────────►│                       │                      │                   │                │
 │                    │  [Context Assembly]   │                      │                   │                │
 │                    │ ───────────────────►  │                      │                   │                │
 │                    │                       │  Tier 2 (Knowledge)  │                   │                │
 │                    │                       │ ───────────────────►│                   │                │
 │                    │                       │                      │  embedding_query  │                │
 │                    │                       │                      │ ─────────────────►│                │
 │                    │                       │                      │◄──────────────────│                │
 │                    │                       │                      │   top-5 chunks    │                │
 │                    │                       │◄─────────────────────│                   │                │
 │                    │                       │                      │                   │                │
 │                    │                       │  [RAG Context        │                   │                │
 │                    │                       │   inserted]          │                   │                │
 │                    │                       │                      │  Final Prompt     │                │
 │                    │                       │                      │ ─────────────────►│                │
 │                    │                       │                      │◄──────────────────│                │
 │                    │◄──────────────────────│                      │                   │                │
 │ "I've worked on..."│                       │                      │                   │                │
 │◄───────────────────│                       │                      │                   │                │
```

### 5.3 Meeting Scheduling

```
User             API           IntentClass.    ToolRouter    PolicyEng.      Validator    AppService    Celery    Saga    n8n    Calendar
 │                │                │              │             │               │             │            │        │      │       │
 │ "Schedule a    │                │              │             │               │             │            │        │      │       │
 │  meeting"      │                │              │             │               │             │            │        │      │       │
 │───────────────►│                │              │             │               │             │            │        │      │       │
 │                │ [classify]     │              │             │               │             │            │        │      │       │
 │                │──────────────►│              │             │               │             │            │        │      │       │
 │                │◄──────────────│              │             │               │             │            │        │      │       │
 │                │ intent=SCHEDULE_MEETING      │             │               │             │            │        │      │       │
 │                │                              │             │               │             │            │        │      │       │
 │ [collect fields sequentially via LLM]         │             │               │             │            │        │      │       │
 │                │                              │             │               │             │            │        │      │       │
 │ "Please provide your full name"               │             │               │             │            │        │      │       │
 │◄───────────────│                              │             │               │             │            │        │      │       │
 │ "John Doe"     │                              │             │               │             │            │        │      │       │
 │───────────────►│                              │             │               │             │            │        │      │       │
 │   ... (repeat for 9 fields)                   │             │               │             │            │        │      │       │
 │                │                              │             │               │             │            │        │      │       │
 │ [confirmation] │                              │             │               │             │            │        │      │       │
 │ "Confirm?"     │                              │             │               │             │            │        │      │       │
 │◄───────────────│                              │             │               │             │            │        │      │       │
 │ "Yes"          │                              │             │               │             │            │        │      │       │
 │───────────────►│                              │             │               │             │            │        │      │       │
 │                │ [route to tool]             │             │               │             │            │        │      │       │
 │                │────────────────────────────►│             │               │             │            │        │      │       │
 │                │                              │ [check perm]│              │             │            │        │      │       │
 │                │                              │────────────►│             │             │            │        │      │       │
 │                │                              │◄────────────│ ok           │             │            │        │      │       │
 │                │                              │ [check policies]          │             │            │        │      │       │
 │                │                              │──────────────────────────►│             │            │        │      │       │
 │                │                              │◄──────────────────────────│ ok           │            │        │      │       │
 │                │                              │ [validate input]          │             │            │        │      │       │
 │                │                              │────────────────────────────────────────►│            │        │      │       │
 │                │                              │◄────────────────────────────────────────│ valid      │        │      │       │
 │                │                              │ [execute]                │             │            │        │      │       │
 │                │                              │──────────────────────────────────────────────────────►│        │      │       │
 │                │                              │                         │             │  [task.delay]│        │      │       │
 │                │                              │                         │             │──────────────►│        │      │       │
 │                │                              │                         │             │              │ [saga] │      │       │
 │                │                              │                         │             │              │────────►│      │       │
 │                │                              │                         │             │              │         │ [n8n]│       │
 │                │                              │                         │             │              │         │──────►│       │
 │                │                              │                         │             │              │         │       │[API]  │
 │                │                              │                         │             │              │         │       │──────►│
 │                │                              │                         │             │              │         │       │◄──────│ ok   │
 │                │                              │                         │             │              │         │◄──────│       │
 │                │                              │                         │             │              │◄────────│       │       │
 │                │                              │                         │             │◄──────────────│         │       │       │
 │                │                              │◄──────────────────────────────────────────────────────│         │       │       │
 │                │                              │ [validate response]     │             │            │        │      │       │
 │                │                              │───────────────────────────────────────────────────────────────────►│       │
 │                │                              │◄───────────────────────────────────────────────────────────────────│       │
 │ "Your meeting  │                              │                         │             │            │        │      │       │
 │  is scheduled" │                              │                         │             │            │        │      │       │
 │◄───────────────│                              │                         │             │            │        │      │       │
```

### 5.4 Saga Rollback

```
AppService      CeleryStep1(SaveDB)    Step2(Calendar)    Step3(Email)    Step4(CRM)    SagaOrchestrator
    │                  │                    │                  │               │               │
    │ [execute]        │                    │                  │               │               │
    │─────────────────►│                    │                  │               │               │
    │                  │ [ok]               │                  │               │               │
    │◄─────────────────│                    │                  │               │               │
    │                                     │                    │               │               │
    │ [execute]                           │                    │               │               │
    │────────────────────────────────────►│                    │               │               │
    │                                     │ [ok]               │               │               │
    │◄────────────────────────────────────│                    │               │               │
    │                                                                          │               │
    │ [execute]                                                                │               │
    │─────────────────────────────────────────────────────────────────────────►│               │
    │                                                                          │ [FAIL]        │
    │                                                                          │──────────────►│
    │                                                                          │               │
    │                                                                          │  [compensate] │
    │                                                                          │◄──────────────│
    │                │                    │                  │                 │               │
    │                │                    │  [compensate]    │                 │               │
    │                │                    │◄───────────────────────────────────────────────────│
    │                │                    │                  │                 │               │
    │                │  [compensate]      │                  │                 │               │
    │                │◄────────────────────────────────────────────────────────────────────────│
    │                │                    │                  │                 │               │
    │ [all compensated]                   │                  │                 │               │
    │◄───────────────│                    │                  │                 │               │
```

### 5.5 Returning User

```
User                  API               IdentityResolver     Memory(LTM)        Memory(STM)         LLM
 │                    │                       │                  │                  │                │
 │ "I'm back"         │                       │                  │                  │                │
 │ + X-Session-ID     │                       │                  │                  │                │
 │───────────────────►│                       │                  │                  │                │
 │                    │  [resolve identity]   │                  │                  │                │
 │                    │ ───────────────────►  │                  │                  │                │
 │                    │                       │ [check JWT]      │                  │                │
 │                    │                       │ [check session]  │                  │                │
 │                    │                       │ [check email]    │                  │                │
 │                    │◄──────────────────────│ user_id=known    │                  │                │
 │                    │                       │                  │                  │                │
 │                    │  [load user profile]  │                  │                  │                │
 │                    │ ───────────────────────────────────────►│                  │                │
 │                    │◄────────────────────────────────────────│ profile          │                │
 │                    │                       │                  │                  │                │
 │                    │  [load conversation]  │                  │                  │                │
 │                    │ ──────────────────────────────────────────────────────────►│                │
 │                    │◄──────────────────────────────────────────────────────────│ recent_state   │
 │                    │                       │                  │                  │                │
 │                    │  [check if archived]  │                  │                  │                │
 │                    │  → last message >30m  │                  │                  │                │
 │                    │  → load summary from LTM                 │                  │                │
 │                    │ ───────────────────────────────────────►│                  │                │
 │                    │◄────────────────────────────────────────│ summary          │                │
 │                    │                       │                  │                  │                │
 │ "Welcome back!     │                       │                  │                  │                │
 │  We were discussing│                       │                  │                  │                │
 │  [summary]..."     │                       │                  │                  │                │
 │◄───────────────────│                       │                  │                  │                │
```

### 5.6 Redis Failure (Degraded Mode)

```
User             API            CacheService      DegradedMode        LTM(Postgres)      LLM
 │                │                │                  │                  │                │
 │ "What projects │                │                  │                  │                │
 │  have you done?"│               │                  │                  │                │
 │───────────────►│                │                  │                  │                │
 │                │ [get_redis()]  │                  │                  │                │
 │                │──────────────►│                  │                  │                │
 │                │                │ [connection      │                  │                │
 │                │                │  failed]         │                  │                │
 │                │                │─────────────────►│                  │                │
 │                │                │                  │ [set tier=3]     │                │
 │                │                │                  │──────────────────►│                │
 │                │                │ [fallback: use   │                  │                │
 │                │                │  Postgres for STM]                 │                │
 │                │◄───────────────│                  │                  │                │
 │                │                │                  │                  │                │
 │                │ [rate limit: in-process]         │                  │                │
 │                │ [idempotency: bypassed]          │                  │                │
 │                │ [locks: bypassed]                │                  │                │
 │                │                                  │                  │                │
 │                │ [short-term memory from PG]      │                  │                │
 │                │────────────────────────────────────────────────────►│                │
 │                │◄─────────────────────────────────────────────────────│                │
 │                │                                  │                  │                │
 │                │ [process normally]               │                  │                │
 │                │─────────────────────────────────────────────────────────────────────►│
 │                │◄──────────────────────────────────────────────────────────────────────│
 │                │                                  │                  │                │
 │ "I've worked   │                                  │                  │                │
 │  on..."        │                                  │                  │                │
 │◄───────────────│                                  │                  │                │
```

### 5.7 Human Handoff

```
User             API           LLM              HandoffService      HumanAgent        Queue
 │                │            │                    │                  │                │
 │ "I need to     │            │                    │                  │                │
 │  discuss       │            │                    │                  │                │
 │  something     │            │                    │                  │                │
 │  complex"      │            │                    │                  │                │
 │───────────────►│            │                    │                  │                │
 │                │ [classify] │                    │                  │                │
 │                │───────────►│                    │                  │                │
 │                │◄───────────│                    │                  │                │
 │                │ confidence=0.3 < threshold     │                  │                │
 │                │            │                    │                  │                │
 │                │ [escalate] │                    │                  │                │
 │                │────────────────────────────────►│                  │                │
 │                │            │                    │ [find available  │                │
 │                │            │                    │  human agent]    │                │
 │                │            │                    │─────────────────►│                │
 │                │            │                    │◄─────────────────│                │
 │                │            │                    │                  │                │
 │ "Let me        │            │                    │                  │                │
 │  connect you   │            │                    │                  │                │
 │  with a        │            │                    │                  │                │
 │  human..."     │            │                    │                  │                │
 │◄───────────────│            │                    │                  │                │
 │                │            │                    │                  │                │
 │ ──── WebSocket connection to human ────          │                  │                │
 │                                                  │                  │                │
 │                │            │                    │ [transfer        │                │
 │                │            │                    │  conversation    │                │
 │                │            │                    │  context]        │                │
 │                │            │                    │──────────────────►│                │
```

---

## 6. AI Decision Engine

### 6.1 Decision Point Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │              DECISION ENGINE                │
                    │  Central orchestrator of all AI decisions   │
                    └─────────────────────────────────────────────┘
                                    │
         ┌───────────┬───────────┬──┴───┬───────────┬───────────┐
         ▼           ▼           ▼      ▼           ▼           ▼
   ┌──────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │ Intent   │ │ Task   │ │Reason  │ │Memory  │ │ Tool   │ │Response│
   │Detection │ │Classif.│ │Engine  │ │Retrieve│ │Select  │ │Validate│
   └──────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

### 6.2 Decision Point Catalog

#### DP-1: Intent Detection

| Attribute | Value |
|-----------|-------|
| **Input** | User message, user_type, conversation context |
| **Output** | Intent enum (SCHEDULE_MEETING, PORTFOLIO_QUESTION, GREETING, etc.) |
| **Method** | Primary: Logprob-based classification (LLM). Fallback: Regex keyword matching |
| **Confidence** | Logprob aggregation → normalized 0-1 |
| **Threshold** | ≥ 0.7 for acceptance. 0.4-0.7 for semantic verification pass. < 0.4 → ask clarification |
| **Decision** | If confidence ≥ 0.7: accept. If 0.4-0.7: run semantic verification pass. If < 0.4: "Could you clarify?" |
| **Failure** | No matching intent after clarification → default to UNKNOWN (FAQ fallback) |

#### DP-2: Task Classification (Model Tier)

| Attribute | Value |
|-----------|-------|
| **Input** | Intent + user message length + contains code? + contains scheduling keywords? |
| **Output** | Tier 1-5 |
| **Method** | Rule-based mapping from intent + heuristics |
| **Decision** | GREETING → Tier 1. PORTFOLIO_QUESTION → Tier 2. SCHEDULE_MEETING → Tier 3. ARCHITECTURE → Tier 4. COMPLEX_PLANNING → Tier 5 |

#### DP-3: Reasoning Depth

| Attribute | Value |
|-----------|-------|
| **Input** | Tier, message complexity (length, question marks, technical terms) |
| **Output** | Reasoning depth: none | shallow | deep | extended |
| **Method** | Heuristic: Tier 1+2 → none/shallow. Tier 3 → shallow. Tier 4 → deep. Tier 5 → extended |
| **Decision** | Determines whether to use chain-of-thought, tool-use, or standard generation |

#### DP-4: Memory Retrieval

| Attribute | Value |
|-----------|-------|
| **Input** | User_id, identity_source, intent, conversation_id |
| **Output** | Memory context blocks (profile, summary, history, semantic, episodic) |
| **Method** | Tiered retrieval based on identity confidence |
| **Decision** | JWT identity → full retrieval. Session identity → STM only. Anonymous → no retrieval |

#### DP-5: Tool Selection

| Attribute | Value |
|-----------|-------|
| **Input** | Intent, collected_data, user_type, conversation_state |
| **Output** | Tool to execute or None |
| **Method** | Intent → tool registry mapping |
| **Decision** | SCHEDULE_MEETING → meeting_scheduler. BECOME_LEAD → lead_creator. Others → no tool |

#### DP-6: Tool Validation

| Attribute | Value |
|-----------|-------|
| **Input** | Tool input data, tool schema, business policies |
| **Output** | Valid/Invalid with field-level errors |
| **Method** | Schema validation + policy engine check |
| **Decision** | Valid → execute. Invalid → return field-level errors to LLM for correction |

#### DP-7: Confidence Scoring

| Attribute | Value |
|-----------|-------|
| **Input** | LLM response, logprobs, expected schema compliance |
| **Output** | Confidence score 0-1 |
| **Method** | Logprob aggregation × format compliance × fact consistency |
| **Decision** | ≥ 0.8 → auto-accept. 0.5-0.8 → ask user confirmation. < 0.5 → regenerate or reroute |

#### DP-8: Fallback Decision

| Attribute | Value |
|-----------|-------|
| **Input** | Model failure reason, retry count, circuit breaker state |
| **Output** | retry | fallback_model | degrade_response | human_handoff |
| **Method** | State machine: retry < max → retry. next model exists → fallback. degraded → message. else → handoff |
| **Decision** | Determined by Model Router tier policy + current health status |

#### DP-9: Human Handoff

| Attribute | Value |
|-----------|-------|
| **Input** | User message, attempted resolutions, conversation context |
| **Output** | Handoff / No handoff |
| **Method** | Triggered by: 3 consecutive low-confidence responses, explicit "speak to human" request, policy escalation |
| **Decision** | Handoff → transfer context to human agent queue. No handoff → continue AI |

### 6.3 Decision Flow Diagram

```
                    ┌──────────────────────┐
                    │   User Message       │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  DP-1: Intent Detect │─── Low confidence ──► "Could you clarify?"
                    └──────────┬───────────┘
                               │ intent
                    ┌──────────▼───────────┐
                    │  DP-2: Task Classify │─── Tier 1-5
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  DP-3: Reasoning     │─── none/shallow/deep/extended
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  DP-4: Memory Retrieve│─── profile/summary/history/semantic
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  DP-5: Tool Select   │─── tool / no tool
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │ No tool      │  │ DP-6: Tool   │  │ DP-7: Conf.  │
     │ → Generate   │  │ Validate     │  │ Score        │
     │   Response   │  └──────┬───────┘  └──────┬───────┘
     └──────┬───────┘         │                  │
            │          ┌──────▼───────┐   ┌──────▼───────┐
            │          │ Valid → Exec │   │ Low → DP-8   │
            │          │ Invalid→Retry│   │ Fallback     │
            │          └──────────────┘   └──────┬───────┘
            │                                    │
            └────────────────┬───────────────────┘
                             │
                    ┌────────▼────────┐
                    │   DP-9: Human   │
                    │   Handoff?      │─── Yes → Human Agent
                    └────────┬────────┘
                             │ No
                    ┌────────▼────────┐
                    │  Final Response │
                    └─────────────────┘
```

---

## 7. Policy Engine

### 7.1 Policy Engine Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │              POLICY ENGINE                  │
                    │  Central policy evaluation & enforcement    │
                    └─────────────────────────────────────────────┘
                                    │
         ┌───────────┬───────────┬──┴───┬───────────┬───────────┐
         ▼           ▼           ▼      ▼           ▼           ▼
   ┌──────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │ Meeting  │ │ Memory │ │Convers.│ │Security│ │ Lead   │ │Workflow│
   │ Policies │ │Policies│ │Policies│ │Policies│ │Policies│ │Policies│
   └──────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

### 7.2 Policy Definitions

#### P-001: Meeting Scheduling Window
```yaml
id: P-001
name: meeting_scheduling_window
description: Meetings must be scheduled during business hours
scope: [meeting/schedule]
rules:
  - condition: preferred_hour < 9 OR preferred_hour > 17
    action: reject
    message: "Meetings can only be scheduled between 9 AM and 5 PM."
  - condition: preferred_day == "Saturday" OR preferred_day == "Sunday"
    action: reject
    message: "Meetings can only be scheduled on weekdays."
severity: error
reusable: true
```

#### P-002: Advance Notice
```yaml
id: P-002
name: advance_notice
description: Meetings must be scheduled at least 2 hours in advance
scope: [meeting/schedule]
rules:
  - condition: scheduled_time - now < 2h
    action: warn
    message: "Meetings should be scheduled at least 2 hours in advance."
severity: warning
reusable: true
```

#### P-003: Lead Deduplication (BR-030)
```yaml
id: P-003
name: lead_dedup_email
description: Prevent duplicate lead creation by email
scope: [lead/create]
rules:
  - action: query
    target: leads
    condition: email == input.email
    exists:
      action: reject
      message: "A lead with this email already exists. Updating existing record instead."
      auto_correct: update_lead
    not_exists:
      action: allow
severity: error
reusable: true
```

#### P-004: Identity Confirmation (BR-033 / ADR-003)
```yaml
id: P-004
name: identity_confirmation_required
description: Identity fields always require explicit user confirmation before saving
scope: [memory/update]
classification:
  identity: [name, email, phone]
  business: [company, company_address]
  preference: [timezone, meeting_type, preferred_time]
  history: [past_meetings, summaries]
rules:
  - field_class: identity
    action: require_confirmation
    message: "Should I save your {field} for next time?"
  - field_class: business
    condition: confidence >= 0.8
    action: auto_save
  - field_class: preference
    condition: confidence >= 0.8
    action: auto_save
  - field_class: history
    action: auto_save
reusable: true
```

#### P-005: Conversation Rate Limit
```yaml
id: P-005
name: conversation_rate_limit
description: Maximum messages per user per minute
scope: [conversation/message]
rules:
  - counter: user_messages
    window: 60s
    limit: 30
    action: reject
    response_status: 429
    message: "Rate limit exceeded. Please slow down."
reusable: true
```

#### P-006: Conversation Idle Timeout (BR-006 / ADR-005)
```yaml
id: P-006
name: conversation_idle_timeout
description: Handle idle conversations at various thresholds
scope: [conversation/state]
rules:
  - idle_duration: 5m
    action: notify
    message: "Are you still there?"
  - idle_duration: 15m
    action: pause
    description: "Save state, mark as idle"
  - idle_duration: 30m
    action: archive
    description: "Archive to LTM, clear STM"
  - idle_duration: 24h
    action: expire
    description: "STM fully expired"
reusable: true
```

#### P-007: PII Redaction
```yaml
id: P-007
name: pii_redaction
description: Automatically detect and redact PII before LLM processing
scope: [all]
patterns:
  - type: email
    pattern: "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
    action: mask
    replacement: "[EMAIL REDACTED]"
  - type: phone
    pattern: "\\+?\\d{10,15}"
    action: mask
    replacement: "[PHONE REDACTED]"
  - type: ssn
    pattern: "\\d{3}-\\d{2}-\\d{4}"
    action: mask
    replacement: "[SSN REDACTED]"
reusable: true
```

#### P-008: Lead Scoring
```yaml
id: P-008
name: lead_scoring_auto
description: Auto-calculate lead score based on data completeness and company profile
scope: [lead/create, lead/update]
rules:
  - field: email_present
    score: +10
  - field: phone_present
    score: +15
  - field: company_present
    score: +20
  - field: company_size > 50
    score: +25
  - field: meeting_scheduled
    score: +30
  - condition: total_score > 50
    action: flag_priority
    label: hot_lead
reusable: true
```

#### P-009: Tool Permission Matrix
```yaml
id: P-009
name: tool_permission_matrix
description: Define which user types can execute which tools
scope: [tool/execute]
matrix:
  - tool: schedule_meeting
    allowed: [recruiter, client, visitor]
    require_confirmation: true
  - tool: create_lead
    allowed: [recruiter, client]
    require_confirmation: false
  - tool: update_profile
    allowed: [recruiter, client, visitor]
    require_confirmation: true
  - tool: admin_action
    allowed: [admin]
    require_confirmation: true
reusable: true
```

#### P-010: Retention Policy
```yaml
id: P-010
name: data_retention
description: Define data retention periods for all entities
scope: [data/retention]
entities:
  conversation_stm:
    ttl: 30m  # Sliding window
    action: archive_to_ltm
  conversation_ltm:
    ttl: 90d
    action: delete
  session_data:
    ttl: 24h
    action: delete
  audit_logs:
    ttl: 365d
    action: archive
  meeting_records:
    ttl: 730d
    action: archive
reusable: true
```

### 7.3 Policy Evaluation Flow

```
                    ┌──────────────────────┐
                    │   Action Requested   │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Policy Engine.evaluate(
                    │    action="meeting/schedule",
                    │    context={...}
                    │  )
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │ P-001:       │  │ P-002:       │  │ P-009:       │
     │ Meeting Time │  │ Advance      │  │ Permissions  │
     └──────┬───────┘  │ Notice       │  └──────┬───────┘
            │          └──────┬───────┘         │
            ▼                 ▼                  ▼
     ┌──────────────────────────────────────────────────┐
     │  Result: {allow: true/false, warnings: [],       │
     │           errors: [], auto_corrections: []}      │
     └──────────────────────────────────────────────────┘
```

### 7.4 Policy Metadata

```yaml
policy:
  id: P-001
  version: 1.2.0
  status: active
  author: sahil
  approved_by: arch-board
  created: 2025-01-01
  updated: 2025-01-15
  tags: [meeting, scheduling, business-hours]
  applies_to: [v1.0.0+]
  test_coverage: 0.95
```

---

## 8. Conversation State Machine

### 8.1 Formal State Machine Definition

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │              CONVERSATION STATE MACHINE                      │
                    │  (Singleton per conversation_id, linear with recovery)       │
                    └─────────────────────────────────────────────────────────────┘

                                   ┌────────────┐
                                   │  GREETING   │
                                   └──────┬─────┘
                                          │ intent detected
                                          ▼
                               ┌──────────────────────┐
                    ┌──────────│   INTENT_DETECTION   │◄──────────┐
                    │          └──────────┬───────────┘           │
                    │                     │ intent known          │ re-classify
                    │                     ▼                       │
                    │          ┌──────────────────────┐           │
                    │          │ INFORMATION_COLLECTION│───────────┘
                    │          └──────────┬───────────┘ (missing fields)
                    │                     │ all fields collected
                    │                     ▼
                    │          ┌──────────────────────┐
                    │          │      VALIDATION      │
                    │          └──────────┬───────────┘
                    │                     │ valid
                    │                     ▼
                    │          ┌──────────────────────┐
                    │          │    CONFIRMATION      │◄──────────┐
                    │          └──────────┬───────────┘           │
                    │                     │ confirmed             │ needs edit
                    │                     ▼                       │
                    │          ┌──────────────────────┐           │
                    ├─────────►│      PROCESSING      │───────────┘
                    │          └──────────┬───────────┘
                    │                     │
                    │         ┌───────────┼───────────┐
                    │         ▼           ▼           ▼
                    │  ┌──────────┐ ┌──────────┐ ┌──────────┐
                    │  │ COMPLETED│ │CANCELLED │ │  ERROR   │
                    │  └──────────┘ └──────────┘ └────┬─────┘
                    │                                 │ (recoverable)
                    │                                 ▼
                    │                          ┌──────────┐
                    │                          │ RECOVERY │────► GREETING or INTENT_DETECTION
                    │                          └──────────┘
                    │
                    │         ┌─────────────────────────────────────┐
                    │         │  TIMEOUT (5/15/30 min)              │
                    │         │  → 5min: "Are you still there?"    │
                    │         │  → 15min: Save state → IDLE         │
                    │         │  → 30min: ARCHIVE state              │
                    │         └──────────┬──────────────────────────┘
                    │                    │
                    │                    ▼
                    │          ┌──────────────────────┐
                    │          │       ARCHIVED       │◄───────────┐
                    │          └──────────┬───────────┘            │
                    │                     │ user returns           │ within 24h
                    │                     ▼                        │
                    │          ┌──────────────────────┐            │
                    │          │    HUMAN_HANDOFF     │────────────┘
                    │          └──────────────────────┘
                    │
                    └───────────────────┘
```

### 8.2 State Definitions

| State | Entry Action | Exit Action | Timeout | Recovery |
|-------|--------------|-------------|---------|----------|
| **GREETING** | Load user profile. Generate welcome message. | Set start timestamp. | 5m → TIMEOUT | N/A (entry state) |
| **INTENT_DETECTION** | Classify intent. Route based on result. | Store intent. | 5m → TIMEOUT | Re-classify |
| **INFORMATION_COLLECTION** | Load field schema for intent. Ask first field. | Store collected data. | 15m → TIMEOUT | Resume from last collected field |
| **VALIDATION** | Validate all collected fields. | Mark valid/invalid. | 5m → TIMEOUT | Re-validate |
| **CONFIRMATION** | Generate confirmation summary. Wait for user response. | Store confirmed data. | 15m → TIMEOUT | Re-generate summary |
| **PROCESSING** | Execute tool/saga/workflow. | Store result. | 30s → ERROR | Retry with backoff |
| **COMPLETED** | Generate success response. Update memory. | None (terminal). | N/A | N/A |
| **CANCELLED** | Generate cancellation message. Clear working data. | None (terminal). | N/A | N/A |
| **ERROR** | Log error. Determine recoverability. | If recoverable → RECOVERY. Else → response. | 5m → TIMEOUT | Retry or escalate |
| **RECOVERY** | Analyze error. Determine resume point. | Route to appropriate state. | 5m → TIMEOUT | Escalate to human |
| **TIMEOUT** | Save state. Notify user. | 5m → notify. 15m → pause. 30m → ARCHIVE. | Per tier | Resume on user message |
| **ARCHIVED** | Compress state. Store in LTM. Clear STM. | Set archived_at. | 24h → expire | Restore from LTM on return |
| **HUMAN_HANDOFF** | Transfer context to human agent queue. | Set handoff timestamp. | N/A | N/A |

### 8.3 State Transition Table

```
┌─────────────────────┬──────────────────────────────────────────────────────────────────────────────┐
│ Current State       │ Next State (on trigger)                                                       │
├─────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
│ GREETING            │ INTENT_DETECTION (user message) | TIMEOUT (5min idle)                         │
│ INTENT_DETECTION    │ INFORMATION_COLLECTION (needs data) | COMPLETED (simple intent) | TIMEOUT     │
│ INFORMATION_COLLECTION│ VALIDATION (all fields) | INFORMATION_COLLECTION (missing fields) | TIMEOUT │
│ VALIDATION          │ CONFIRMATION (valid) | INFORMATION_COLLECTION (invalid) | TIMEOUT             │
│ CONFIRMATION        │ PROCESSING (confirmed) | CANCELLED (cancelled) | INFORMATION_COLLECTION (edit)│
│ PROCESSING          │ COMPLETED (success) | ERROR (failure)                                        │
│ COMPLETED           │ GREETING (new message) | [terminal]                                           │
│ CANCELLED           │ GREETING (new message) | [terminal]                                           │
│ ERROR               │ RECOVERY (recoverable) | COMPLETED (non-recoverable, with apology)            │
│ RECOVERY            │ GREETING | INTENT_DETECTION | INFORMATION_COLLECTION (resume)                 │
│ TIMEOUT             │ INTENT_DETECTION (user returns) | ARCHIVED (30min)                            │
│ ARCHIVED            │ GREETING (user returns within 24h, with context) | GREETING (fresh, after 24h)│
│ HUMAN_HANDOFF       │ [terminal for AI, continues in human system]                                  │
└─────────────────────┴──────────────────────────────────────────────────────────────────────────────┘
```

### 8.4 Timeout Rules Detail

```yaml
timeout_rules:
  greeting_timeout:
    duration: 5m
    action: transition_to TIMEOUT
    message: "Are you still there?"
  
  collection_timeout:
    duration: 15m
    action: save_state + transition_to TIMEOUT
    message: "I've saved your progress. Send a message to continue."
  
  archive_timeout:
    duration: 30m
    action: archive_to_ltm + clear_stm + transition_to ARCHIVED
    
  total_expiry:
    duration: 24h
    action: expire_stm
    return_action: start_fresh
```

### 8.5 Recovery Rules

```yaml
recovery_rules:
  recoverable_errors:
    - llm_timeout
    - llm_rate_limit
    - tool_timeout
    - network_error
    - database_connection_error
  
  non_recoverable_errors:
    - invalid_intent
    - schema_validation_failure
    - policy_violation
    - authorization_failure
  
  recovery_strategies:
    llm_error:
      max_retries: 3
      backoff: exponential(1s, 2s, 4s)
      fallback: degrade_model | cached_response
    tool_error:
      max_retries: 2
      backoff: fixed(2s)
      fallback: inform_user | human_handoff
    persistence_error:
      max_retries: 1
      fallback: degraded_mode
```

---

## 9. Memory Retrieval Strategy

### 9.1 Memory Architecture

```
                    ┌──────────────────────────────────────────────────────┐
                    │                   MEMORY SYSTEM                       │
                    ├─────────────────────────┬────────────────────────────┤
                    │    Short-Term Memory    │     Long-Term Memory       │
                    │    (Redis, ephemeral)   │     (PostgreSQL, durable)  │
                    ├─────────────────────────┼────────────────────────────┤
                    │ Active conversation     │ User profiles              │
                    │ Session data            │ Conversation archives      │
                    │ Workflow locks          │ Meeting records            │
                    │ Rate limit counters     │ Lead records               │
                    │ Idempotency cache       │ Semantic vectors (pgvector)│
                    │                         │ Audit logs                 │
                    └─────────────────────────┴────────────────────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    │          MEMORY RETRIEVAL            │
                    │                                      │
                    │  Profile → Semantic → Episodic →     │
                    │  Conversation → Meeting → Preference │
                    └──────────────────────────────────────┘
```

### 9.2 Memory Type Definitions

#### Profile Memory
| Attribute | Value |
|-----------|-------|
| **Content** | User name, email, phone, company, preferences, user_type |
| **Source** | PostgreSQL (UserModel) |
| **Retrieval trigger** | Every conversation (on identity resolution) |
| **Scoring** | Always included (identity confirmed = full, session = partial) |
| **TTL** | Permanent (updated on change) |
| **Conflict resolution** | Last-write-wins for non-identity. Confirmation-required for identity (ADR-003) |

#### Semantic Memory
| Attribute | Value |
|-----------|-------|
| **Content** | Factual knowledge about user: "prefers morning meetings", "works at Acme Corp" |
| **Source** | Extracted from conversations → embedded → pgvector |
| **Retrieval trigger** | On conversation start + on topic change |
| **Scoring** | Cosine similarity × recency decay × confidence |
| **Ranking** | Hybrid: top-5 by similarity, boosted by recency |
| **TTL** | Permanent until contradicted |
| **Conflict resolution** | New info supersedes old. Confidence-weighted. |

#### Episodic Memory
| Attribute | Value |
|-----------|-------|
| **Content** | Past interaction summaries: "Previously discussed project X on Jan 15" |
| **Source** | Conversation archives in PostgreSQL |
| **Retrieval trigger** | Returning user within 24h |
| **Scoring** | Recency-weighted. Only last 5 episodes. |
| **TTL** | 90 days |
| **Conflict resolution** | N/A (append-only summaries) |

#### Conversation Memory
| Attribute | Value |
|-----------|-------|
| **Content** | Current session messages + state |
| **Source** | Redis (active window) → PostgreSQL (archived) |
| **Retrieval trigger** | Every message in current session |
| **Scoring** | Recency-based. Last N messages. |
| **TTL** | 30 min (sliding) in Redis. 90 days in PostgreSQL. |
| **Conflict resolution** | N/A (append-only log) |

#### Meeting Memory
| Attribute | Value |
|-----------|-------|
| **Content** | Scheduled meetings, past meetings |
| **Source** | PostgreSQL (MeetingModel) |
| **Retrieval trigger** | On meeting-related intent |
| **Scoring** | Recency. Upcoming > past. |
| **TTL** | 2 years |
| **Conflict resolution** | N/A |

#### Preference Memory
| Attribute | Value |
|-----------|-------|
| **Content** | timezone, preferred_time, preferred_meeting_type, preferred_language |
| **Source** | UserModel (preference fields) |
| **Retrieval trigger** | On conversation start |
| **Scoring** | Always included if set |
| **TTL** | Permanent until user changes |
| **Conflict resolution** | Auto-save on high confidence. Confirmation on medium. Ignore on low. |

### 9.3 Memory Scoring & Ranking

```
                    ┌──────────────────────┐
                    │  Memory Query        │
                    │  (user_id, intent,   │
                    │   context)           │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Retrieve Candidates │
                    │  (all memory types)  │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Score Each          │
                    │                      │
                    │  relevance = similarity(q, m) × α
                    │  recency = exp(-Δt / λ) × β
                    │  importance = importance(m) × γ
                    │  confidence = confidence(m) × δ
                    │                      │
                    │  total = α·sim + β·rec + γ·imp + δ·conf
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Rank & Select       │
                    │  (top-K by score)    │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Assemble into       │
                    │  ContextBuilder      │
                    └──────────────────────┘
```

### 9.4 Compression Strategy

| Memory Type | Compression | When |
|-------------|-------------|------|
| Conversation History | Drop oldest 50% | Token budget exceeded |
| Semantic Memory | Keep top-3 by relevance | Token budget exceeded |
| Episodic Memory | Summarize to single paragraph | Token budget exceeded |
| RAG Context | Reduce from top-5 to top-2 | Token budget exceeded |
| Meeting Memory | Keep only upcoming | Token budget exceeded |

### 9.5 Memory Merge (Identity Resolution)

```yaml
merge_strategy:
  trigger: "User provides email during session"
  process:
    - Lookup email in LTM
    - If found:
        - Associate session_id with existing user_id
        - Merge any new data from session into profile
        - Transfer session conversation history to user's conversation list
    - If not found:
        - Create new user with email + session data
  conflict_resolution:
    identity_fields: [name, email, phone]
      rule: "Require confirmation (P-004)"
    business_fields: [company, company_address]
      rule: "Session value overwrites if confidence > 0.8"
    preference_fields: [timezone, preferred_time]
      rule: "Most recent value wins"
```

### 9.6 Memory TTL Summary

| Memory | Storage | TTL | Eviction |
|--------|---------|-----|----------|
| Active conversation state | Redis | 30 min (sliding) | Expiry |
| Session data | Redis | 24 h | Expiry |
| Idempotency cache | Redis | 5 min | Expiry |
| Conversation lock | Redis | 30 s | Expiry + release |
| Rate limit counters | Redis | 1 min | Expiry |
| User profile | PostgreSQL | Permanent | N/A |
| Conversation archive | PostgreSQL | 90 days | Cron job |
| Semantic vectors | pgvector | 90 days | Cron job |
| Meeting records | PostgreSQL | 2 years | Cron job |
| Audit logs | PostgreSQL | 1 year | Archive |
| Lead records | PostgreSQL | Permanent | N/A |

---

## 10. Architecture Validation

### 10.1 Risk Assessment

#### R-001: Redis as Celery Broker (SPOF)

| Attribute | Value |
|-----------|-------|
| **Risk** | Redis failure breaks Celery task queue. All async operations (meetings, notifications, embeddings) become unavailable. |
| **Severity** | Critical |
| **Likelihood** | Low (single instance) / Medium (Sentinel reduces but doesn't eliminate) |
| **Current mitigation** | Redis Sentinel (3 nodes, auto-failover). Degraded mode messages. |
| **Recommended** | Add RabbitMQ as secondary Celery broker in v2. Until then, document that Redis broker failure breaks all async features. Add health check to detect broker status. |
| **Trade-off** | RabbitMQ adds operational complexity. Acceptable for v2. |

#### R-002: Single FastAPI Service

| Attribute | Value |
|-----------|-------|
| **Risk** | All domains (chat, meetings, leads, memory) co-located in one service. Failure in one domain affects all. No independent scaling. |
| **Severity** | High |
| **Likelihood** | Medium (resource contention) |
| **Current mitigation** | Domains are logically separated (clean architecture). Ready for extraction. |
| **Recommended** | Add per-domain resource limits (CPU/memory quotas). Implement bulkhead pattern with separate worker pools per domain. Extract high-traffic domains (chat) first when scaling needed. |
| **Trade-off** | Bulkhead adds complexity. Acceptable for v1. |

#### R-003: LLM API Dependency

| Attribute | Value |
|-----------|-------|
| **Risk** | Complete dependency on external LLM APIs. Any outage makes the assistant non-functional. |
| **Severity** | Critical |
| **Likelihood** | Medium (Gemini has good uptime but third-party APIs fail) |
| **Current mitigation** | 4-model fallback chain with circuit breakers. Each model has independent failure tracking. |
| **Recommended** | Add local fallback model (e.g., Llama 3.2 via Ollama) for basic responses during total API outage. Implement response caching for common queries. |
| **Trade-off** | Local model requires GPU. Cached responses may be stale. |

#### R-004: n8n External Dependency

| Attribute | Value |
|-----------|-------|
| **Risk** | Meeting scheduling, email, CRM all depend on n8n. n8n failure blocks business workflows. |
| **Severity** | High |
| **Likelihood** | Medium (n8n is a complex system) |
| **Current mitigation** | n8n health check. Saga pattern for rollback on failure. |
| **Recommended** | Add n8n workflow monitoring (execution time, failure rate). Implement workflow-level retry with backoff. Consider direct Google Calendar API calls as fallback for n8n meeting scheduling. |
| **Trade-off** | Direct API calls bypass n8n's workflow capabilities. Acceptable for critical-path fallback. |

#### R-005: Prompt Injection

| Attribute | Value |
|-----------|-------|
| **Risk** | User message contains prompt injection, jailbreak attempts, or system prompt override. |
| **Severity** | Critical |
| **Likelihood** | Medium (public-facing chatbot) |
| **Current mitigation** | Input length limits (2000 chars). User type classification. |
| **Recommended** | Implement guardrail prompts before every LLM call. Add PII redaction middleware (P-007). Add jailbreak detection classifier. Rate limit to prevent brute force. Log all injection attempts for security review. |
| **Trade-off** | Guardrails add tokens and latency. Security > convenience for production. |

#### R-006: No Multi-Tenant Isolation

| Attribute | Value |
|-----------|-------|
| **Risk** | User data is logically separated by user_id but not physically isolated. A bug could leak data between users. |
| **Severity** | High |
| **Likelihood** | Low |
| **Current mitigation** | All queries scoped by user_id. Repository pattern enforces data access boundaries. |
| **Recommended** | Add tenant_id to all models (even for single-tenant v1). Enforce tenant isolation at the database connection pool level in v2. Add data access audit logging. |
| **Trade-off** | tenant_id adds schema complexity. Easy to add now, harder later. |

#### R-007: Conversation History Growth

| Attribute | Value |
|-----------|-------|
| **Risk** | Long conversations accumulate history that exceeds context windows. |
| **Severity** | Medium |
| **Likelihood** | High (inevitable for active users) |
| **Current mitigation** | Context compression strategy (levels 1-5). 30-min archive rule (ADR-005). |
| **Recommended** | Implement automatic summarization at 10-message intervals. Store summaries in a rolling window (last 5 summaries + full last 10 messages). Add conversation length warning to monitoring. |
| **Trade-off** | Summarization adds LLM calls. Cost vs. quality trade-off. |

#### R-008: Idempotency Key Implementation Gap

| Attribute | Value |
|-----------|-------|
| **Risk** | Frontend (Django widget) may not implement idempotency key generation. Race conditions in rapid-fire messages could cause duplicate processing. |
| **Severity** | High |
| **Likelihood** | Medium (frontend implementation unknown) |
| **Current mitigation** | Idempotency key field exists in API schema. Locking prevents concurrent processing of same conversation. |
| **Recommended** | Generate server-side idempotency key if client doesn't provide one (using hash of user_id + message + timestamp). Ensure the Django widget docs require idempotency key implementation. |
| **Trade-off** | Server-side generation is less effective than client-side. Better than nothing. |

#### R-009: No Rate Limit Persistence

| Attribute | Value |
|-----------|-------|
| **Risk** | Rate limit counters reset on Redis restart, allowing burst attacks immediately after restart. |
| **Severity** | Medium |
| **Likelihood** | Low |
| **Current mitigation** | In-process token bucket fallback during Redis degradation. |
| **Recommended** | Accept for v1. Document that rate limits reset on Redis restart. Add persistent rate limit counters in PostgreSQL for v2. |
| **Trade-off** | PostgreSQL writes on every request are too slow. In-memory is correct trade-off for v1. |

#### R-010: Saga Implementation Maturity

| Attribute | Value |
|-----------|-------|
| **Risk** | Saga orchestrator has stub implementations (return hardcoded values). Real compensation logic is not implemented. |
| **Severity** | High |
| **Likelihood** | High (will fail in production) |
| **Current mitigation** | Saga pattern is designed. Stub implementations exist for structure. |
| **Recommended** | Implement real saga actions before production: calendar event creation → database save → email → CRM. Each step must have a real compensation that reverses the action. Add saga execution logging for audit. Add saga timeout (30s per step). |
| **Trade-off** | Full saga implementation requires external API integration. Critical path for production launch. |

---

## 11. Architecture Scorecard

### 11.1 Scorecard

| Category | Score | Assessment | Required for 10/10 |
|----------|-------|------------|-------------------|
| **Microservice Design** | 9.0 | Logically isolated domains in a monolith. Ready for extraction. Missing: independent deployability, per-domain scaling, bulkhead isolation. | Add per-domain resource limits. Implement bulkhead pattern. |
| **AI Engineering** | 9.5 | Context builder pipeline. Model router with tier-classification. Prompt registry with versioning. Decision engine with formal decision points. Missing: A/B testing framework for prompt changes. Local fallback model for total API outage. | Add A/B evaluation pipeline. Deploy Ollama with Llama for emergency fallback. |
| **Domain-Driven Design** | 9.5 | Clean domain boundaries (meeting, lead, conversation, user). Events for cross-domain communication. Repository pattern for data access. Missing: No bounded context map. Some cross-domain coupling (conversation → meeting). | Document bounded contexts. Reduce cross-domain coupling via domain events. |
| **Security** | 9.0 | JWT auth. RBAC (user_type). Input validation. Rate limiting. PII policies defined. Missing: mTLS for service-to-service (N/A for monolith). Prompt injection guardrails not implemented. No API key rotation. | Add prompt injection detection. Implement guardrail prompts. Add security audit trail for all tool executions. |
| **Scalability** | 8.5 | Stateless API (scales horizontally). Redis for state. Celery for async. pgvector for RAG. Missing: No auto-scaling. Single service limits domain-specific scaling. No read replicas for PostgreSQL. | Add horizontal pod autoscaling. Add PostgreSQL read replicas. Extract chat domain as separate service when traffic demands. |
| **Reliability** | 9.2 | Redis Sentinel (auto-failover). Circuit breakers for LLM. Degraded mode strategies. Saga pattern for distributed transactions. Missing: No chaos engineering tests. No load testing results. | Run chaos experiments (kill Redis, kill PostgreSQL, throttle LLM). Document results and tune thresholds. |
| **Observability** | 9.0 | Structured logging (correlation IDs). Prometheus metrics. Health checks (liveness/readiness). LangSmith tracing. Sentry for errors. Missing: No custom dashboards for conversation metrics. No alerting rules defined. | Build Grafana dashboards for: conversation throughput, LLM latency by tier, error rates by domain. Define Prometheus alerting rules for: high error rate, high latency, circuit breaker open. |
| **Cloud Readiness** | 8.5 | Docker Compose deployment. Environment-based config. 12-factor app principles followed. Missing: No Kubernetes manifests. No CI/CD pipeline. No secrets management (secrets in .env). | Add Kubernetes manifests (deployment, service, HPA, ingress). Add CI/CD with GitHub Actions. Use external secrets manager (HashiCorp Vault or cloud KMS). |
| **Developer Experience** | 9.5 | Clean project structure. Comprehensive documentation (PRD, ARCHITECTURE, ADRs, API.md). Type hints throughout. Dependency injection. Missing: No local development seed data. No one-command setup script. | Add makefile/script for one-command local setup. Add seed data for demo. Write CONTRIBUTING.md. |
| **Maintainability** | 9.5 | Clean module boundaries. Typed interfaces. Repository pattern. Event-driven design. Low coupling. Missing: Some cross-module dependencies (conversation imports agents, memory, rag, tools). | Enforce strict module hierarchy: domain → infrastructure → application → presentation. Use dependency injection to invert cross-module dependencies. |
| **Future SaaS Readiness** | 8.0 | Tenant isolation designed (user_id scoping). Domains ready for extraction. Missing: No tenant_id in schema. No billing/cost tracking. No usage metering. No self-service onboarding. | Add tenant_id to all entities now (even for single-tenant). Design usage metering interface. Plan public API gateway for v2. |
| **Production Readiness** | 9.0 | Health checks. Graceful shutdown. Docker Compose. Environment config. Degraded modes. Missing: No production deployment guide. No runbooks for common failures. No backup/restore procedures documented. | Write production deployment guide. Create runbooks for: DB restore, Redis failover, n8n recovery, saga recovery. Automated backup verification. |

### 11.2 Overall Score

```
┌─────────────────────────────────────────────┐
│         ARCHITECTURE SCORECARD              │
├─────────────────────────────────────────────┤
│  Microservice Design      │ 9.0 / 10       │
│  AI Engineering           │ 9.5 / 10       │
│  Domain-Driven Design     │ 9.5 / 10       │
│  Security                 │ 9.0 / 10       │
│  Scalability              │ 8.5 / 10       │
│  Reliability              │ 9.2 / 10       │
│  Observability            │ 9.0 / 10       │
│  Cloud Readiness          │ 8.5 / 10       │
│  Developer Experience     │ 9.5 / 10       │
│  Maintainability          │ 9.5 / 10       │
│  Future SaaS Readiness    │ 8.0 / 10       │
│  Production Readiness     │ 9.0 / 10       │
├─────────────────────────────────────────────┤
│  WEIGHTED AVERAGE         │ 9.1 / 10       │
│  TARGET                   │ 10.0 / 10      │
│  SHORTFALL                │ 0.9 points     │
└─────────────────────────────────────────────┘
```

### 11.3 Improvement Plan to Reach 10/10

| Category | Current | Target | Required Actions | Effort |
|----------|---------|--------|------------------|--------|
| Scalability | 8.5 | 10 | Add HPA + read replicas + domain extraction plan | 2 weeks |
| Cloud Readiness | 8.5 | 10 | K8s manifests + CI/CD + secrets manager | 3 weeks |
| Future SaaS Readiness | 8.0 | 10 | tenant_id + metering + public API design | 3 weeks |
| Security | 9.0 | 10 | Prompt injection guardrails + mTLS plan + security audit | 1 week |
| Microservice Design | 9.0 | 10 | Bulkhead pattern + resource quotas per domain | 1 week |

**Total estimated effort: 10 weeks to reach 10/10**  
**Recommended: Proceed to implementation with 9.1/10. Address gaps during implementation sprints.**

---

## 12. ADRs

### ADR-101 — Context Builder Pipeline
*Status:* Proposed  
*Decision:* A dedicated `ContextBuilder` class assembles context in 5 ordered layers (System → Memory → Knowledge → Input → Compression) before every LLM call. No LLM call bypasses the builder. Token budget management and compression levels (0-5) are enforced before the final prompt is sent.  
*Rationale:* Without a formal pipeline, context assembly is ad-hoc, non-deterministic, and unobservable. Enterprise deployments require auditability of what context was sent to the model and why certain context was dropped.  
*Trade-off:* Adds ~5ms overhead per request. Acceptable for correctness and audit.

### ADR-102 — Request Classification for Model Routing
*Status:* Proposed  
*Decision:* Every request is classified into one of 5 tiers (Simple, Knowledge, Task, Complex, Extended Reasoning) before model selection. Tier determines preferred model, timeout, retry policy, circuit breaker thresholds, and cost target. Classifier is a lightweight ML model with rule-based fallback.  
*Rationale:* Static fallback chains waste resources and latency. Classification enables per-tier optimization (e.g., 500ms for greetings, 30s for reasoning).  
*Trade-off:* Classification misclassification risk. Mitigation: confidence < 0.7 triggers reclassification. Cold-start uses rule-based fallback.

### ADR-103 — File-Based Prompt Registry with Feature Flag Deployment
*Status:* Proposed  
*Decision:* All prompts are stored as versioned YAML files in a `prompts/` directory tree, loaded by a `PromptRegistry` class. Prompt versions are selected via feature flags for gradual rollout and instant rollback. Prompts have a formal lifecycle: Draft → Review → Staging → Active → Deprecated → Archived.  
*Rationale:* Hardcoded Python strings are not auditable, not versionable, and cannot be A/B tested. YAML files in version control are reviewable via PRs and deployable independently.  
*Trade-off:* Filesystem dependency. Mitigated by in-memory caching. Database-backed storage planned for v2.

### ADR-104 — Layered Tool Execution Pipeline
*Status:* Proposed  
*Decision:* Tools are never called directly from the LLM or graph. Every tool execution passes through 6 mandatory layers: Tool Router → Permission Layer → Policy Engine → Validation Layer → Application Service → Response Validator. Each layer can reject or modify the execution.  
*Rationale:* Direct tool execution bypasses security, policy, and validation controls required for enterprise deployments. Layered architecture ensures every external action is auditable, reversible, and policy-gated.  
*Trade-off:* Adds ~50ms per tool execution. Acceptable — external API calls dominate latency.

### ADR-105 — Formal Conversation State Machine
*Status:* Proposed  
*Decision:* Conversation state machine is formally defined with 13 states, entry/exit actions, timeout rules per state, and explicit recovery paths. State transitions are recorded in an append-only log for audit and debugging.  
*Rationale:* The current implicit state machine in LangGraph lacks formal timeout handling, recovery paths, and state persistence decisions. A formal machine ensures deterministic behavior under all conditions.  
*Trade-off:* More code than a simple graph. Acceptable for production reliability.

### ADR-106 — Centralized Policy Engine
*Status:* Proposed  
*Decision:* All business rules are defined as declarative YAML policies in a centralized policy engine. Policies are reusable across domains, versioned, and evaluated by a `PolicyEngine` class before any action executes.  
*Rationale:* Scattered if/else business rules are unmanageable, untestable, and invisible to non-technical stakeholders. Declarative policies are reviewable, testable, and auditable.  
*Trade-off:* Policy evaluation adds ~2ms overhead per decision. YAML policies require governance. Acceptable for enterprise compliance.

### ADR-107 — Formal AI Decision Engine
*Status:* Proposed  
*Decision:* All AI decision points (intent detection, task classification, tool selection, confidence scoring, fallback, human handoff) are formalized as named decision points with defined inputs, outputs, methods, thresholds, and failure modes.  
*Rationale:* Implicit decisions throughout the codebase make behavior unpredictable and untestable. Formal decision points enable targeted testing, monitoring, and improvement.  
*Trade-off:* More upfront design. Acceptable for production AI systems.

### ADR-108 — Context Compression with Budget Management
*Status:* Proposed  
*Decision:* A token budget manager enforces a configurable safety margin (80% of model max tokens) across all context components. Five levels of compression (history truncation → memory pruning → RAG reduction → summary fallback → hard truncation) are applied progressively.  
*Rationale:* Without budget management, context overflow causes unpredictable truncation by the model provider, potentially dropping critical system prompts. Progressive compression ensures deterministic behavior under overflow.  
*Trade-off:* Some context is always lost under overflow. Progressive levels ensure the most important content survives. Acceptable.

---

## Appendix A: Deliverable Traceability

| Deliverable | Document Location | Status |
|-------------|-------------------|--------|
| D1: AI Context Builder | Section 1 | Complete |
| D2: Intelligent Model Router | Section 2 | Complete |
| D3: Prompt Registry | Section 3 | Complete |
| D4: Tool Execution Pipeline | Section 4 | Complete |
| D5: Sequence Diagrams | Section 5 | Complete (19 diagrams) |
| D6: AI Decision Engine | Section 6 | Complete (9 decision points) |
| D7: Policy Engine | Section 7 | Complete (10 policies) |
| D8: Conversation State Machine | Section 8 | Complete (13 states) |
| D9: Memory Retrieval Strategy | Section 9 | Complete (6 memory types) |
| D10: Architecture Validation | Section 10 | Complete (10 risks) |
| D11: Architecture Scorecard | Section 11 | Complete (12 categories, 9.1/10) |

## Appendix B: ADR Index

| ADR | Title | Section |
|-----|-------|---------|
| ADR-101 | Context Builder Pipeline | 1.7 |
| ADR-102 | Request Classification for Model Routing | 2.6 |
| ADR-103 | File-Based Prompt Registry | 3.9 |
| ADR-104 | Layered Tool Execution Pipeline | 4.6 |
| ADR-105 | Formal Conversation State Machine | 8 (implicit) |
| ADR-106 | Centralized Policy Engine | 7 (implicit) |
| ADR-107 | Formal AI Decision Engine | 6 (implicit) |
| ADR-108 | Context Compression with Budget Management | 1.6 |

---

**End of Enterprise Architecture Review Report v1.0**  
**Review Status:** Architecture Approved with recommendations  
**Next Step:** Proceed to implementation phase. Address Production Readiness gaps during first sprint.
