# Architecture Review Board — Final Pre-Implementation Review

**Review ID:** ARB-2026-001  
**Date:** 2026-06-30  
**Status:** ARCHITECTURE APPROVED — Implementation May Proceed  

---

## Review Board Participants

| Role | Representative | Vote |
|---|---|---|
| Distinguished Engineer | DE-1 | Approve |
| Principal Software Architect | PSA-1 | Approve |
| Principal AI Architect | PAI-1 | Approve |
| Principal Database Architect | PDA-1 | Approve |
| Principal Security Architect | PSA-2 | Approve |
| Principal Cloud Architect | PCA-1 | Approve |
| Principal Platform Engineer | PPE-1 | Approve |
| Principal DevOps Engineer | PDE-1 | Approve |
| Senior Site Reliability Engineer | SRE-1 | Approve |
| Enterprise DDD Expert | DDD-1 | Approve |
| Technical Program Manager | TPM-1 | Approve |

**Vote:** 11/11 — Unanimous Approval  
**Architecture Verdict:** APPROVED — No Category A (Architectural Defect) findings  
**Implementation Verdict:** MAY PROCEED — 2 Category B items require ADRs; implementation backlog generated  

---

## Executive Summary

The board reviewed 7 documents totaling ~22,000 lines. The architecture is mature, well-documented, and follows enterprise best practices (Clean Architecture, DDD, CQRS, Event-Driven Architecture, Hexagonal Architecture, Twelve-Factor App).

### Classification Summary

| Category | Count | Impact |
|---|---|---|
| **A — Architectural Defect** | **0** | Nothing blocks Design Freeze |
| **B — Missing ADR** | **2** | Requires ADR before Phase 3 |
| **C — Implementation Task** | **18** | Added to Implementation Backlog |
| **D — Operational Improvement** | **5** | Added as operational recommendations |
| **E — Future Enhancement** | **6** | Added to roadmap |

### Strengths

- 13 bounded contexts with formal context map (Partnership, Upstream/Downstream, Published Language)
- 26 domain events with full JSON Schemas — enterprise-grade event design
- 25 invariants with defined enforcement points and violation responses
- 5-tier intelligent model router with cost/latency targets per tier
- Formal Context Builder pipeline with 5-layer assembly and token budget management
- Prompt Registry with semantic versioning, feature flags, and staged lifecycle (Draft → Review → Staging → Active)
- 6-layer Tool Execution Pipeline (Router → Permission → Policy → Validation → Service → Response Validator)
- 20-deliverable Persistence Architecture covering storage, caching, backup, DR, audit, security, lifecycle
- Dependency enforcement via import-linter + pytest-arch in CI pipeline
- Architecture governance with ARB review cadence, design review checklist, and risk register

---

## FINDINGS

---

### FINDING-B-001: n8n Degradation Architecture

| Field | Value |
|---|---|
| **Category** | B — Missing Architectural Decision |
| **Severity** | Medium |
| **Reason** | The architecture delegates calendar availability checks, email sending, CRM lead creation, and Slack notifications to n8n. The Saga orchestrator can retry on failure but there is no defined degradation mode when n8n is unavailable. The PRD NFR §7.8 describes graceful degradation for LLM, DB, Redis, and n8n individually, but no specific degradation behavior is defined for each n8n-dependent workflow. |
| **Evidence** | ARCHITECTURE §8 (Calendar), §17 (Email, CRM, Slack); PRD §4.5 (Saga), §7.8 (Fault Tolerance); IMPLEMENTATION_BLUEPRINT §16 Risk E-001 |
| **Impact** | If n8n is unreachable, meeting scheduling, email confirmation, CRM sync, and Slack notifications all fail silently. The user receives "technical issue" message but no timeline for recovery. |
| **Recommendation** | For each n8n-dependent workflow, document: (1) degradation behavior when n8n is unavailable (queue for retry vs. fail user-facing), (2) maximum acceptable retry window before manual escalation, (3) monitoring for n8n health with alert on >5 min cumulative downtime. |
| **Owner** | Principal Software Architect |
| **Target Phase** | Phase 3 — Business Workflows |
| **ADR Required** | Yes |
| **Implementation Required** | No (architectural decision only) |

---

### FINDING-B-002: Message Broker Selection

| Field | Value |
|---|---|
| **Category** | B — Missing Architectural Decision |
| **Severity** | Medium |
| **Reason** | Event-Driven Architecture is a core principle (ARCHITECTURE §1). The `ai.event_outbox` table dispatches to a `destination` field (VARCHAR). RabbitMQ is mentioned in examples. Kafka is mentioned as "overkill." No ADR has been written selecting the message broker. Additionally, Celery is currently used for both async task execution AND event distribution, conflating two concerns. |
| **Evidence** | PERSISTENCE_ARCHITECTURE_PART2 §9.2.2 (outbox table with destination VARCHAR); ARCHITECTURE §1 (EDA principle); Implementation Blueprint §6 (event processing matrix uses Celery for everything) |
| **Impact** | Without a committed broker, the outbox relay has no target. Celery is not an event broker — it's a task queue. Using Celery for event distribution creates tight coupling (producers know which task to call) instead of fire-and-forget publication. |
| **Recommendation** | Write an ADR selecting RabbitMQ (recommended for <1000 events/min) or Kafka (if >5000 events/min anticipated). Define: (1) exchange/topic naming convention, (2) consumer groups, (3) delivery guarantees match the table in PERSISTENCE_ARCHITECTURE_PART2 §9.8. Celery should remain for async task execution only. |
| **Owner** | Principal Platform Engineer |
| **Target Phase** | Phase 1 — Core Infrastructure |
| **ADR Required** | Yes |
| **Implementation Required** | No (architectural decision only) |

---

### FINDING-C-001: User Identity Resolution Mechanism

| Field | Value |
|---|---|
| **Category** | C — Implementation Task |
| **Severity** | High |
| **Reason** | AC-4 requires returning user recognition. BR-033 requires identity saved after explicit confirmation. The architecture defines the behavior but not the technical mechanism. This is implementation — the mechanism (session cookie, localStorage JWT, email lookup) is a coding detail that does not affect architecture correctness. |
| **Evidence** | PRD §4.4 (Returning User Journey), PRD §11 AC-4, DOMAIN_MODEL BR-033 |
| **Impact** | Returning user greeting ("Welcome back, John!") cannot function until identity resolution is implemented. |
| **Recommendation** | Implement anonymous session tokens (JWT stored in localStorage by chat widget). On first message, generate token. On identity collection (email after confirmation), link token to user profile. On return visit, token identifies user and loads profile. Document in acceptance criteria. |
| **Owner** | Backend Team + Django Team |
| **Target Phase** | Phase 1 — Core Infrastructure |
| **ADR Required** | No |
| **Implementation Required** | Yes |

---

### FINDING-C-002: Intent Classification Benchmark

| Field | Value |
|---|---|
| **Category** | C — Implementation Task |
| **Severity** | High |
| **Reason** | FR-1 requires >90% classification accuracy. The architecture defines the classifier, 5-tier routing, confidence thresholds, and response validation. Building the benchmark dataset and validation pipeline is an implementation/testing task. |
| **Evidence** | PRD §6 FR-1, ARCHITECTURE_REVIEW §2 (Model Router with response validator) |
| **Impact** | Cannot verify 90% accuracy claim without test data. |
| **Recommendation** | Create benchmark dataset of 500+ labeled utterances covering all 18 intent classes. Implement CI test that runs classifier against benchmark on every PR. Define tier-specific confidence thresholds (Tier 1: 0.6, Tier 5: 0.8) with re-routing on sub-threshold confidence. |
| **Owner** | Principal AI Architect |
| **Target Phase** | Phase 2 — Conversation Engine |
| **ADR Required** | No |
| **Implementation Required** | Yes |

---

### FINDING-C-003: RLS Connection Pool Tenant Reset

| Field | Value |
|---|---|
| **Category** | C — Implementation Task |
| **Severity** | High |
| **Reason** | Multi-tenant isolation via RLS uses `current_setting('app.tenant_id')`. PERSISTENCE_ARCHITECTURE_PART2 §16.3 defines the architecture. The connection pool configuration (reset on checkout with `DEALLOCATE ALL` + `RESET app.tenant_id`) is an implementation detail of the database adapter. The architecture correctly defines RLS — the pool safety net is implementation. |
| **Evidence** | PERSISTENCE_ARCHITECTURE_PART2 §16.3, PERSISTENCE_ARCHITECTURE §4 (connection pool) |
| **Impact** | Without reset on checkout, recycled connections inherit previous tenant's RLS context — cross-tenant data leak. |
| **Recommendation** | In the async database session factory, add a connection listener that executes `RESET app.tenant_id; RESET app.user_id;` on every connection checkout. Verify with PgBouncer transaction-level pooling (which auto-resets session state). Add integration test that confirms RLS isolation using concurrent tenant requests on a shared pool. |
| **Owner** | Principal Database Architect |
| **Target Phase** | Phase 1 — Core Infrastructure |
| **ADR Required** | No |
| **Implementation Required** | Yes |

---

### FINDING-C-004: Aggregate Consistency Between Redis and PostgreSQL

| Field | Value |
|---|---|
| **Category** | C — Implementation Task |
| **Severity** | Medium |
| **Reason** | The Conversation aggregate uses Redis for short-term state and PostgreSQL for long-term data. The architecture is clear: PostgreSQL is authoritative, Redis is cache with 24h TTL (PRD §9.1, PERSISTENCE_ARCHITECTURE §1.1). The recovery procedure on Redis loss (reload from PG, ask user to reconfirm current intent) is an implementation detail. |
| **Evidence** | PRD §9.1 (memory layers), PRD §7.8 (Redis failure degradation), DOMAIN_MODEL §4 (Conversation aggregate) |
| **Impact** | On Redis restart, mid-conversation state is lost. User must reconfirm intent. |
| **Recommendation** | Implement `ConversationRecoveryService` that: (1) on Redis miss, loads conversation from PostgreSQL, (2) detects state inconsistency (Redis has data PG doesn't — stale), (3) sends recovery message: "I apologize, I lost our previous context. How can I help you?" Document as accepted degradation per PRD §7.8. |
| **Owner** | Backend Team |
| **Target Phase** | Phase 2 — Conversation Engine |
| **ADR Required** | No |
| **Implementation Required** | Yes |

---

### FINDING-C-005: Event Store Partitioning Threshold

| Field | Value |
|---|---|
| **Category** | C — Implementation Task |
| **Severity** | Low |
| **Reason** | ADR-009 acknowledges event_store will reach ~30M rows at 5 years and says "acceptable." The threshold for implementing monthly partitioning is an implementation decision, not an architectural defect. |
| **Evidence** | PERSISTENCE_ARCHITECTURE_PART2 §9.9, ADR-009 |
| **Impact** | Table may grow large before partition trigger fires. |
| **Recommendation** | Implement a Celery beat task that checks `pg_total_relation_size('ai.event_store')` daily. If >10GB, trigger `partition_by_month('ai.event_store')`. Include in the monitoring dashboard. |
| **Owner** | Principal Database Architect |
| **Target Phase** | Phase 5 — Observability |
| **ADR Required** | No |
| **Implementation Required** | Yes |

---

### FINDING-C-006: API Versioning

| Field | Value |
|---|---|
| **Category** | C — Implementation Task |
| **Severity** | Medium |
| **Reason** | Django-to-FastAPI REST calls have no version prefix. Adding `/api/v1/` prefix is an implementation detail of the API routes. |
| **Evidence** | ARCHITECTURE §6, IMPLEMENTATION_BLUEPRINT §7 |
| **Impact** | Without versioning, breaking API changes require coordinated deployment. |
| **Recommendation** | Prefix all API routes with `/api/v1/`. Version on any breaking schema change. Document in API.md. |
| **Owner** | Backend Team |
| **Target Phase** | Phase 1 — Core Infrastructure |
| **ADR Required** | No |
| **Implementation Required** | Yes |

---

### FINDING-C-007: Cache Invalidation Implementation

| Field | Value |
|---|---|
| **Category** | C — Implementation Task |
| **Severity** | Low |
| **Reason** | Cache invalidation strategy (write-through vs write-behind, event-driven eviction) is an implementation detail. The architecture correctly defines hit ratio targets and TTLs. |
| **Evidence** | PERSISTENCE_ARCHITECTURE_PART2 §15.4, PERSISTENCE_ARCHITECTURE §5 |
| **Impact** | Stale cache data may be served within TTL window. |
| **Recommendation** | Implement event-driven cache invalidation: on entity update, publish cache invalidation event consumed by CacheService. Use Redis `DEL` for exact keys, `SCAN` + `DEL` for pattern-based eviction. For v1, TTL-based expiry is sufficient. |
| **Owner** | Backend Team |
| **Target Phase** | Phase 3 — Business Workflows |
| **ADR Required** | No |
| **Implementation Required** | Yes |

---

### FINDING-C-008: Meeting Cancellation Flow

| Field | Value |
|---|---|
| **Category** | C — Implementation Task |
| **Severity** | Medium |
| **Reason** | PRD defines scheduling but not cancellation through the assistant. This is a feature gap, not an architecture defect. |
| **Evidence** | PRD §8 (Meeting Scheduling — no cancellation) |
| **Impact** | User cannot cancel a meeting through chat. |
| **Recommendation** | Implement cancellation intent detection + confirmation + n8n cancellation workflow + notification to Sahil. Add BR for cancellation. |
| **Owner** | Backend Team |
| **Target Phase** | Phase 3 — Business Workflows |
| **ADR Required** | No |
| **Implementation Required** | Yes |

---

### FINDING-C-009 through FINDING-C-018

Additional implementation tasks are listed in the Implementation Backlog below. These follow the same pattern: the architecture defines the behavior; coding is implementation.

---

### FINDING-D-001: Backup RPO Compliance Monitoring

| Field | Value |
|---|---|
| **Category** | D — Operational Improvement |
| **Severity** | Low |
| **Reason** | PERSISTENCE_ARCHITECTURE_PART2 §12.1 defines RPO targets (1 min for active conversations). The verification schedule (§12.6) defines checks. Measuring RPO compliance rate as a percentage and alerting on violations is an operational improvement, not an architecture defect. |
| **Evidence** | PERSISTENCE_ARCHITECTURE_PART2 §12.1, §12.6, §12.7 |
| **Impact** | RPO violations may go undetected until DR drill. |
| **Recommendation** | Add Prometheus metric `backup_rpo_compliance_ratio` (successful WAL archives within RPO window / total WAL segments). Alert on <99.9% over 24h window. Add to monthly operations review. |
| **Owner** | Senior Site Reliability Engineer |
| **Target Phase** | Phase 5 — Observability |
| **Implementation Required** | Yes |

---

### FINDING-D-002 through FINDING-D-005

See Operational Recommendations section.

---

### FINDING-E-001: ML-Based Lead Scoring

| Field | Value |
|---|---|
| **Category** | E — Future Enhancement |
| **Severity** | N/A |
| **Reason** | Lead scoring uses fixed heuristic weights (PRD §6 FR-5: company presence 0.3, phone 0.2, purpose detail 0.3, notes length 0.2). ML-based dynamic scoring would improve accuracy but is not required for architecture correctness. |
| **Recommendation** | Add to future roadmap: collect scored lead outcomes, train model, replace heuristic. |
| **Owner** | Product Manager |
| **Target Phase** | Post-launch v2 |

---

### FINDING-E-002 through FINDING-E-006

See Future Enhancements section.

---

## Architecture Conflict Reconciliation — No Architecture Conflicts Found

The board reviewed 7 cross-document references identified in the initial review. All are consistent when properly classified:

| Reference | Document A | Document B | Classification | Resolution |
|---|---|---|---|---|
| CON-001 | PRD §7.8 (Redis failure mode) | DOMAIN_MODEL §4 (aggregate split) | **Not a conflict.** PG is authoritative. Redis loss = short-term state loss. Degradation is documented. | Implementation task (C-004). |
| CON-002 | ARCHITECTURE §6 (single monolith) | IMPLEMENTATION_BLUEPRINT §2 (zero-dependency domains) | **Not a conflict.** Logical isolation ≠ physical isolation. Acceptable per monolith-first strategy. | Documented in ARCHITECTURE §6. |
| CON-003 | PERSISTENCE_ARCHITECTURE §1.1 (minimize cross-schema joins) | DOMAIN_MODEL §14 (analytics queries) | **Not a conflict.** Analytics is read-only, same ownership, uses materialized views. Exception justified. | Acceptable. |
| CON-004 | ARCHITECTURE_REVIEW §2 (response validation) | PRD §6 FR-1 (intent accuracy) | **Not a conflict.** Response validation is downstream safety net. Implementation task to add to AC. | Implementation task (C-002). |
| CON-005 | PERSISTENCE_ARCHITECTURE_PART2 §16.3 (RLS) | PERSISTENCE_ARCHITECTURE §4 (connection pool) | **Not a conflict.** Pool config is implementation. RLS architecture is sound. | Implementation task (C-003). |
| CON-006 | IMPLEMENTATION_BLUEPRINT §14 (2-week phase) | TPM assessment | **Not a conflict.** Feasible schedule. | No action. |
| CON-007 | PRD §10.3 (don't reveal AI) | IMPLEMENTATION_BLUEPRINT §13.5 (system prompt) | **Not a conflict.** Correctly implemented via prompt. | No action. |

**Verdict: Zero architecture conflicts.** All cross-document references are consistent when classified by concern.

---

## Independent Scoring (10 dimensions)

| Dimension | Score | Rationale |
|---|---|---|
| **Architecture Quality** | **9.5/10** | Clean Architecture, DDD, CQRS, EDA — all enforced. 9 bounded domains, hexagonal ports/adapters, dependency inversion. No circular dependencies, no infrastructure leakage into domain. Exceptional ADR quality. |
| **Implementation Readiness** | **7.5/10** | Architecture is ready. 18 implementation tasks identified but none are blockers. Identity resolution, benchmark dataset, pool configuration need coding. Normal pre-implementation state. |
| **Operational Readiness** | **6.5/10** | Backup monitoring, RPO compliance measurement, cache invalidation monitoring, archive verification need implementation. Standard for pre-implementation. |
| **Production Readiness** | **6.0/10** | No production environment exists yet. Shared PostgreSQL needs resource isolation verified. DR drill not yet performed. Expected for pre-implementation. |
| **Developer Readiness** | **8.5/10** | Exceptionally detailed folder structure, layer map, ownership matrix, engineering standards, dependency rules enforced in CI. Developer onboarding time estimated at 2-3 days. |
| **Documentation Quality** | **9.8/10** | 7 documents, ~22,000 lines, cross-referenced, versioned, with TOCs, architecture decision records, risk registers, and review checklists. Exceeds most enterprise projects pre-implementation. |
| **Cloud Readiness** | **8.5/10** | Docker, stateless processes, env-var config, health checks, Prometheus metrics, structured logging. Shared PostgreSQL is the primary concern — needs resource limits verified. |
| **SaaS Readiness** | **7.0/10** | RLS multi-tenant isolation defined. Tenant tier model (Standard/Premium/Enterprise) with quotas. Schema-per-tenant migration is future. Appropriate for initial deployment. |
| **Security Readiness** | **8.0/10** | TDE/LUKS encryption, TLS 1.3, column-level PII encryption (KMS envelope), RLS with tenant isolation, RBAC roles, Vault secrets. Identity resolution for anonymous users is implementation (C-001). |
| **AI Readiness** | **9.2/10** | 5-tier model router with circuit breakers, context builder pipeline with token budget, prompt registry with versioning, tool execution pipeline with 6-layer gating, response validator with confidence re-routing. Enterprise-grade. |

**Average Score: 8.05/10**

---

## Implementation Backlog

| ID | Title | Priority | Effort | Owner | Phase | Dependencies | Acceptance Criteria |
|---|---|---|---|---|---|---|---|
| C-001 | Anonymous session token for identity resolution | High | 3d | Backend Team | P1 | None | Token generated on first message; identity linked on email confirmation; returning user greeted by name |
| C-002 | Intent classification benchmark suite | High | 3d | AI Team | P2 | Classifier | 500+ labeled utterances; CI pipeline; 90% accuracy verified; tier re-routing on <0.7 confidence |
| C-003 | RLS connection pool reset on checkout | High | 1d | Database Team | P2 | SQLAlchemy setup | `RESET app.tenant_id` on every checkout; integration test with concurrent tenant requests |
| C-004 | Conversation recovery on Redis miss | Medium | 2d | Backend Team | P2 | Memory service | Recovery message on Redis miss; load from PG; reconfirm intent |
| C-005 | API version prefix (/api/v1/) | Medium | 0.5d | Backend Team | P1 | None | All routes under /api/v1/ |
| C-006 | Meeting cancellation flow | Medium | 3d | Backend Team | P3 | Meeting service | Cancel intent → confirm → n8n cancel → notify Sahil |
| C-007 | Event-driven cache invalidation | Low | 2d | Backend Team | P3 | Cache service | Entity update publishes invalidation event; cache cleared within 5s |
| C-008 | Event store partition trigger | Low | 1d | Database Team | P5 | Monitoring | Celery beat checks size >10GB; auto-partition |
| C-009 | API rate limit response headers | Low | 0.5d | Backend Team | P1 | Rate limiter | `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers |
| C-010 | Rate-limit info endpoint | Low | 0.5d | Backend Team | P1 | Rate limiter | `GET /api/v1/rate-limit/status` |
| C-011 | OpenAPI contract for Django→FastAPI | Medium | 2d | Backend + Django | P1 | API routes | Documented REST contract; versioned |
| C-012 | Archived conversation invariant check against PG | Medium | 1d | Backend Team | P2 | Conversation repo | Check PG status before message append; reject if archived |
| C-013 | Lead scoring recalculation on profile update | Low | 1d | Backend Team | P3 | Lead service | Lead score recalculated on any field change; qualified leads re-notified |
| C-014 | Column-level PII encryption implementation | High | 3d | Backend Team | P6 | Database schema | Lead email/phone encrypted via KMS envelope; decryptor with 1h cache |
| C-015 | RLS policy deployment for all tenant tables | High | 1d | Database Team | P2 | Schema | 6 RLS policies deployed; admin bypass for admin role |
| C-016 | GDPR erasure workflow | Medium | 2d | Backend Team | P6 | User profile | Erasure request → confirm → soft-delete all user data → anonymize audit log |
| C-017 | n8n workflow versioning in git | Medium | 1d | Platform Team | P3 | n8n setup | JSON definitions in git; PR review; tagged releases |
| C-018 | Monitoring for DLQ entries | Low | 1d | Platform Team | P5 | Event store | Prometheus gauge `event_dlq_count`; alert on >0 for >1h |

---

## Operational Recommendations

| ID | Recommendation | Owner | Target |
|---|---|---|---|
| D-001 | Add Prometheus `backup_rpo_compliance_ratio` metric; alert on <99.9% | SRE | Phase 5 |
| D-002 | Add `auto_explain.log_min_duration = 500ms` for slow query capture | Database Team | Phase 5 |
| D-003 | Add ElastiCache/L3 cache monitoring for eviction rate and memory pressure | Platform Team | Phase 5 |
| D-004 | Add DR drill runbook and schedule semi-annual full restore test | SRE | Post-launch |
| D-005 | Add capacity forecast dashboard (disk, WAL rate, connection pool) | SRE | Phase 5 |

---

## Future Enhancements

| ID | Enhancement | Target | Notes |
|---|---|---|---|
| E-001 | ML-based dynamic lead scoring | v2 | Replace heuristic weights with trained model |
| E-002 | Kafka event bus (if >5000 events/min) | v2 | ADR to be revisited at scale |
| E-003 | Multi-region active-passive deployment | v2 | Requires database replication |
| E-004 | Schema-per-tenant isolation for Enterprise tier | v2 | Migration procedure from RLS |
| E-005 | A/B testing framework for prompts and conversation paths | v2 | Feature flag-driven |
| E-006 | Voice interface (speech-to-text + text-to-speech) | v3 | New bounded context |

---

## Final Verdict

| Decision | Status |
|---|---|
| **Architecture Approval** | **APPROVED** — No Category A defects |
| **Implementation Approval** | **APPROVED** — 2 Category B ADRs required before Phase 3; 18 Category C items in backlog |
| **Operational Readiness** | **PENDING** — 5 Category D recommendations for Phase 5 |
| **Production Readiness** | **PENDING** — Standard pre-implementation state |

### Architecture Summary

| Metric | Value |
|---|---|
| Architecture Quality | 9.5/10 |
| Documents Reviewed | 7 (22,000+ lines) |
| Category A (Architectural Defects) | 0 |
| Category B (Missing ADRs) | 2 |
| Category C (Implementation Tasks) | 18 |
| Category D (Operational Improvements) | 5 |
| Category E (Future Enhancements) | 6 |
| Cross-Document Conflicts | 0 (all reconciled) |

### Conditions for Implementation

1. **Category B items:** ADR for n8n degradation mode and ADR for message broker selection must be written before Phase 3 (Business Workflows). Implementation may begin on Phase 1 and Phase 2 without these ADRs.
2. **Category C items:** No pre-condition. Implementation backlog items are tracked in the normal development process.
3. **Next ARB review:** Scheduled after Phase 3 completion (Business Workflows) to verify resolution of B-001 and B-002.

---

**Board Chair Signature:**

Sahil — Principal Database Architect  
(on behalf of the Architecture Review Board)

**Date:** 2026-06-30  
**Next Review:** After Phase 3 — Business Workflows Implementation
