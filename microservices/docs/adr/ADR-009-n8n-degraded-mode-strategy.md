# ADR-009: n8n Degraded Mode Strategy

**Status:** Accepted  
**Date:** 2026-06-30  
**Author:** Principal Distributed Systems Architect, Principal Workflow Architect, Principal SRE, Principal Platform Engineer  
**Approved By:** Architecture Review Board (ARB-2026-001)  
**Architecture Readiness:** 9.2/10  

---

## Decision

The AI Executive Assistant SHALL implement a 4-tier degraded mode strategy for n8n-dependent workflows. n8n is the workflow execution engine but NEVER the system of record. PostgreSQL is the authoritative source of truth for all business state. When n8n is unavailable, workflows SHALL queue in PostgreSQL (via the event outbox) and resume asynchronously when n8n recovers. The AI service SHALL remain fully available for conversation and data collection during n8n degradation.

---

## Context

The AI Executive Assistant delegates external business workflows to n8n:

- Google Calendar event creation and availability checks
- Email confirmation delivery (SMTP via Gmail)
- CRM lead creation and synchronization
- Slack notifications to Sahil
- Meeting reminder workflows
- Follow-up automation

These workflows are critical but not synchronous. The user-facing chat experience must not depend on n8n availability. A user should be able to complete a conversation, provide all meeting details, and receive confirmation — even if the calendar event is created minutes or hours later.

### Current Architecture Problem

The architecture currently treats n8n as a synchronous dependency in the user-facing path. The Saga orchestrator executes steps sequentially, calling n8n webhooks in real-time. If n8n is down:

1. The Saga fails at the calendar step
2. Compensation rolls back completed steps (email queued, CRM entry deleted)
3. The user receives "technical issue" message
4. All collected data is lost
5. The user must restart the entire flow

This violates the requirement that "business data is never lost" and "workflows are resumable."

---

## Alternatives Considered

| Alternative | Pros | Cons |
|---|---|---|
| **A: Synchronous with retry only** | Simple; current state | Data loss on failure; poor UX; violates resumability |
| **B: Queue in Redis + replay** | Fast enqueue; Redis familiar | Data loss on Redis restart; no durability guarantee for pending workflows |
| **C: Queue in PostgreSQL event outbox + Celery replay (Chosen)** | Durable; transactional with aggregate writes; replayable; auditable | Adds latency for deferred execution; requires idempotency in n8n |
| **D: Local n8n replacement (embedded workflow engine)** | No external dependency | Duplicates n8n functionality; maintenance burden; contradicts architecture principle "n8n owns business workflows" |
| **E: Temporal / AWS Step Functions directly** | Production-grade orchestration | Over-provisioned for current scale; operational complexity; future evolution path |

---

## Design

### Ownership Boundaries

| Component | Role | System of Record? |
|---|---|---|
| **PostgreSQL** | Business state, event store, outbox, workflow execution state, audit log | **YES** — authoritative for all business data |
| **Redis** | Short-term cache, idempotency keys, rate limiting, distributed locks, Celery result backend | No — loss acceptable; recoverable from PG |
| **RabbitMQ** | Event distribution between services (future; Celery used for v1) | No — events durably stored in PG event_store |
| **Celery** | Async task execution, retry management, scheduling | No — task state in Redis result backend; business state in PG |
| **n8n** | External workflow execution (Calendar, Email, CRM, Slack) | **NO** — n8n is NEVER the system of record. All data sent to n8n is recoverable from PostgreSQL. |
| **FastAPI** | Application logic, orchestration, user-facing API | No — stateless; state in PG + Redis |

### Principle: n8n is Never the System of Record

Every workflow executed by n8n MUST satisfy these criteria:

1. All data required for the workflow is stored in PostgreSQL BEFORE the workflow is triggered.
2. n8n's execution is a side effect of business state, not the source of it.
3. If n8n loses its state (crash, restore from backup), no business data is lost — the workflow can be replayed from PostgreSQL.
4. n8n workflow results are validated and persisted back to PostgreSQL before being considered "committed."
5. Idempotency keys prevent duplicate execution on replay.

---

### Failure Types and Handling

| Failure Mode | Detection | Classification | Handling Strategy |
|---|---|---|---|
| **n8n unavailable** (HTTP 503, connection refused) | Celery task receives connection error | Transient | Queue in outbox; retry with exponential backoff; alert on >5 min |
| **Workflow timeout** (n8n does not respond within 30s) | Celery task timeout | Transient | Retry with backoff; after 3 retries, move to DLQ |
| **Webhook timeout** (n8n accepts request but does not respond) | HTTP timeout on n8n webhook call | Transient | Same as workflow timeout |
| **Webhook duplicate** (n8n receives same webhook twice) | Idempotency key collision | Logged | Dedup at n8n side via idempotency header; dedup at Celery via task_id dedup |
| **Workflow crash** (n8n workflow fails mid-execution) | n8n returns error response | Recoverable | Log error; retry 3 times; if persistent, move to DLQ; operator investigates |
| **Authentication failure** (n8n cannot authenticate with Google/Gmail/Slack) | n8n returns auth error | Configuration | Fail immediately; no retry; notify operator via alert; DLQ |
| **Partial workflow completion** (n8n creates calendar event but email fails) | n8n reports partial failure | Critical | Require n8n workflow to be idempotent and atomic (calendar + email in same workflow with rollback). If partial failure detected, compensation via compensating n8n workflow. |
| **Network failure** (intermittent connectivity between Celery and n8n) | Sporadic HTTP errors | Transient | Retry with jitter; circuit breaker after 10 failures in 60s |
| **Queue failure** (Celery broker/RabbitMQ unavailable) | Celery cannot enqueue tasks | Infrastructure | Circuit breaker on task submission; alert; tasks remain in outbox |
| **Retry exhaustion** (all retries consumed) | Celery task in RETRY state exceeds max_retries | Permanent | Move to Dead Letter Queue; notify operator; no automatic retry |

---

### Recovery Strategy

#### Retry Strategy

| Attempt | Delay | Jitter | Rationale |
|---|---|---|---|
| 1 | 10s | ±2s | Immediate retry for transient blips |
| 2 | 30s | ±5s | Standard transient recovery |
| 3 | 90s | ±15s | Extended recovery for brief outages |
| 4 | 300s | ±30s | Recovery from moderate outages |
| 5 | 900s (15min) | ±60s | Extended outage tolerance |

Maximum retries: 5 (total window ~24 minutes before DLQ).

#### Backoff Strategy

Exponential backoff with jitter: `delay = base * 3^(attempt-1) + random(0, jitter_max)`

Rationale: Standard exponential backoff prevents thundering herd when n8n recovers. Jitter prevents synchronized retry storms from multiple queued tasks.

#### Circuit Breaker

| Parameter | Value | Rationale |
|---|---|---|
| Failure threshold | 10 failures in 60s | Prevents cascading retry storms |
| Recovery timeout | 120s | Standard backoff before retry probe |
| Half-open max requests | 3 | Test recovery without overload |
| Closed → Open → Half-Open → Closed | Standard circuit breaker state machine | |

Circuit breaker state is stored in Redis (ephemeral; acceptable loss). On Redis restart, circuit breaker resets to Closed (safe default — retries will naturally fail if n8n is still down).

#### Dead Letter Queue (DLQ)

| Field | Value |
|---|---|
| Storage | PostgreSQL `ai.event_outbox` with status = 'failed' |
| Retention | 90 days in PG, then S3 Glacier Deep Archive |
| Alert | Prometheus alert on `outbox_dlq_count > 0` for >1 hour |
| Resolution | Operator reviews DLQ; can retry, skip, or compensate via admin API |

DLQ entries include:
- Original payload (full JSON)
- Error detail (error type, message, stack trace, HTTP status code)
- Attempt count and timestamps of each attempt
- Correlation ID and workflow ID

#### Workflow Resume

On n8n recovery after outage:

1. Outbox relay scans for `status = 'pending'` where `next_retry_at <= now()`.
2. Tasks are re-enqueued to Celery in order of `created_at ASC`.
3. Each task carries the original idempotency key.
4. n8n deduplicates on idempotency key (if event was already created, n8n returns existing event ID).

#### Workflow Replay

Full replay (for disaster recovery or bug fix):

- Operator triggers replay via `/admin/workflows/replay/{workflow_type}/{correlation_id}`.
- System reads original payload from `ai.event_outbox` or `ai.event_store`.
- New execution with same payload but NEW idempotency key (old one was consumed).
- Previous side effects must be compensatable (compensating n8n workflow).

#### Workflow Compensation

If a workflow fails after partial execution:

1. n8n MUST implement compensating actions for every workflow (e.g., "delete calendar event" for "create calendar event").
2. Compensation is triggered by the Saga orchestrator in FastAPI.
3. Saga compensation steps are stored in PostgreSQL `ai.workflow_execution` with status 'compensating'.
4. Compensation failures are logged to DLQ and require operator intervention.

#### Manual Replay / Operator Recovery

| Scenario | Recovery Action | Tooling |
|---|---|---|
| Single stuck workflow | Admin API: `POST /admin/workflows/{id}/retry` | Admin endpoint |
| Batch stuck workflows (n8n recovered) | Admin API: `POST /admin/workflows/retry-pending` | Admin endpoint |
| Data corruption in n8n | Compensate + replay from PostgreSQL | Admin endpoint + n8n manual |
| DLQ cleanup | Admin API: `POST /admin/dlq/{id}/skip` or `/retry` | Admin endpoint |

---

### User Experience During Degradation

| n8n State | User Experience | AI Behavior | Data State |
|---|---|---|---|
| **Healthy** | Normal flow. Meeting confirmed immediately. Calendar event created. Email sent. | "Your meeting has been scheduled! Check your email for the confirmation." | All persisted. All executed. |
| **Transient failure (1-2 retries)** | User receives confirmation as normal. Event is created within seconds. | No visible change. Deferred execution transparent to user. | Meeting data persisted in PG. Event creation deferred but within retry window. |
| **Extended outage (minutes)** | User receives confirmation. AI says: "Your meeting request has been received and will be processed shortly. You'll receive a confirmation email once everything is confirmed." | Deferred with user notification. | Meeting data persisted in PG. Outbox pending. |
| **Long outage (>1 hour)** | Same as extended outage. No further user-facing change. | Same message. No escalation to user. | Outbox in pending/retrying state. Alert triggered. Operator notified. |
| **DLQ (permanent failure)** | User receives: "I apologize, but I'm experiencing a technical issue with scheduling. Your request has been saved and Sahil will follow up with you directly at [email]." | Escalation message. Human handoff. | Data persisted in PG. DLQ entry created. Operator notified. |

#### User Messaging Guidelines

| Scenario | Message Type | Template |
|---|---|---|
| Initial deferral | Informational | "Your meeting request is being processed. You'll receive a confirmation email shortly." |
| Extended delay (>5min) | Follow-up (if user still in conversation) | "I'm still working on confirming your meeting. Everything is saved — you don't need to do anything else." |
| Permanent failure | Apology + handoff | "I apologize, but I'm having trouble scheduling your meeting right now. Your information has been saved and Sahil will reach out to you directly." |
| Recovery notification | Success (if deferred resolved while user is chatting) | "Great news — your meeting has been confirmed! Check your email for the details." |
| Recovery notification (async) | Email sent by n8n on recovery | Standard confirmation email (n8n workflow) |

#### What the AI NEVER Says

- "n8n is down" (internal infrastructure details NEVER exposed)
- "The workflow engine failed" (no technical jargon)
- Technical error codes, stack traces, or correlation IDs
- "Retry attempt 3 of 5"
- Estimated recovery time (unknown and unreliable)

---

### Workflow State Machine

```
                          ┌──────────┐
                   ┌─────▶│ Completed│
                   │      └──────────┘
              ┌────┴───┐
              │ Success│
              └────┬───┘
                   │
    ┌──────────┐   │     ┌──────────┐
    │ Pending  │───┼────▶│ Executing│
    └──────────┘   │     └────┬─────┘
                   │          │
                   │    ┌─────┴──────┐
                   │    │            │
                   │    v            v
                   │ ┌────────┐ ┌──────────┐
                   │ │ Retrying│ │  Failed  │
                   │ └───┬────┘ └────┬─────┘
                   │     │          │
                   │     v          v
                   │ ┌────────┐ ┌──────────┐
                   └─│ Retry  │ │ Dead     │
                     │ Exhaust│ │ Letter   │
                     └────────┘ └────┬─────┘
                                     │
                              ┌──────┴──────┐
                              │             │
                              v             v
                        ┌──────────┐  ┌──────────┐
                        │ Archived │  │Compensat.│
                        └──────────┘  └────┬─────┘
                                           │
                                           v
                                     ┌──────────┐
                                     │Cancelled │
                                     └──────────┘
```

| State | Description | Transitions To |
|---|---|---|
| **Pending** | Workflow created in `ai.workflow_execution` or `ai.event_outbox` but not yet dispatched | Executing |
| **Executing** | Celery task picked up; sending webhook to n8n | Completed, Retrying, Failed |
| **Completed** | n8n returned success; business outcome confirmed | Archived (after retention) |
| **Retrying** | Transient failure; task re-queued with backoff | Executing, Failed (max retries) |
| **Failed** | Non-retryable error or retry exhaustion without DLQ move | Dead Letter |
| **Dead Letter** | Moved to DLQ for operator review | Archived, Compensating, Retrying (operator) |
| **Compensating** | Saga compensation in progress for partially executed workflows | Cancelled, Failed |
| **Cancelled** | Compensation completed; all side effects reversed | Archived |
| **Archived** | Retained for audit; no further processing | — |

---

### Consistency Guarantees

| Guarantee | Mechanism | Enforcement Point |
|---|---|---|
| **Idempotency** | `idempotency_key` (UUID) generated by FastAPI for every workflow request. n8n workflow MUST dedup on this key. Celery task_id derived from idempotency_key. | Application layer + n8n workflow |
| **Exactly-once business outcome** | Idempotency key ensures n8n creates at most one calendar event per request. If n8n creates the event but Celery task crashes before acknowledging, the retried task with same idempotency key returns existing event ID instead of creating a duplicate. | n8n workflow logic |
| **At-least-once delivery** | Celery default (task is retried on failure). Outbox pattern ensures event is persisted before any delivery attempt. | Celery + PostgreSQL outbox |
| **Duplicate protection** | `ai.event_consumer_dedup` table (PRIMARY KEY on consumer_name + event_id). n8n idempotency key header. | Application + n8n |
| **Ordering** | Per-aggregate ordering via `event_store.version` field. No ordering guarantee across different aggregates — Saga orchestrator handles multi-step ordering. | PostgreSQL + application |
| **Correlation ID** | `X-Correlation-ID` header on every request. Passed to n8n as header. Logged in all audit records. | FastAPI middleware → all downstream |
| **Trace ID** | OpenTelemetry trace ID propagated through Celery tasks to n8n webhook calls. W3C Trace Context format. | OpenTelemetry instrumentation |
| **Audit** | Every workflow state transition recorded in `audit.audit_log`. Payload recorded in `ai.event_store` or `ai.workflow_execution.state_data`. | Audit writer service |

#### Idempotency Key Lifecycle

```
FastAPI generates idempotency_key = uuid4()
    │
    ├── Stored in Redis (TTL = 24 hours)
    ├── Stored in PostgreSQL ai.event_outbox
    ├── Passed to Celery task as header
    │       │
    │       └── Sent to n8n as X-Idempotency-Key header
    │               │
    │               ├── n8n checks: has this key been processed?
    │               │   YES → return existing result (no-op)
    │               │   NO  → execute workflow, store key + result
    │               │
    │               └── n8n returns result in response body
    │
    └── Result stored in Redis (24h TTL) for fast lookup
```

---

### Observability

#### Metrics (Prometheus)

| Metric Name | Type | Labels | Description |
|---|---|---|---|
| `n8n_workflow_requests_total` | Counter | workflow_type, status (success/failed/retry) | Total workflow execution attempts |
| `n8n_workflow_duration_seconds` | Histogram | workflow_type | End-to-end workflow execution time |
| `n8n_workflow_queue_depth` | Gauge | workflow_type | Number of pending workflows in outbox |
| `n8n_workflow_dlq_count` | Gauge | workflow_type | Number of workflows in dead letter queue |
| `n8n_circuit_breaker_state` | Gauge | n8n_instance | Circuit breaker state (0=closed, 1=half-open, 2=open) |
| `n8n_health_check` | Gauge | n8n_instance | 1 = healthy, 0 = unhealthy |
| `outbox_relay_batch_size` | Histogram | — | Number of events dispatched per relay cycle |

#### Logs

| Event | Log Level | Fields |
|---|---|---|
| Workflow created | INFO | workflow_id, type, correlation_id, payload_hash |
| Workflow dispatched | INFO | workflow_id, task_id, destination, idempotency_key |
| Workflow completed | INFO | workflow_id, duration_ms, result_summary |
| Workflow transient failure | WARN | workflow_id, attempt, error, next_retry_at, delay_ms |
| Workflow permanent failure | ERROR | workflow_id, attempts, error, dlq_id |
| Circuit breaker opened | WARN | n8n_instance, failure_count, window_seconds |
| Circuit breaker half-open | INFO | n8n_instance |
| Circuit breaker closed | INFO | n8n_instance, downtime_seconds |
| DLQ entry created | ERROR | dlq_id, workflow_id, error_type, payload_summary |
| DLQ entry resolved | INFO | dlq_id, resolution (retry/skip/compensate) |

#### Tracing

Celery tasks are instrumented with OpenTelemetry. Each task span includes:
- `workflow_id`
- `correlation_id`
- `idempotency_key`
- `n8n_webhook_url` (sanitized)
- `attempt_number`

n8n webhook calls are instrumented as HTTP client spans within the Celery task span.

#### Alerts

| Alert | Condition | Severity | Response |
|---|---|---|---|
| `n8nDown` | `n8n_health_check == 0` for > 5 minutes | Critical | Check n8n container/process; restart if needed |
| `n8nHighFailureRate` | `n8n_workflow_requests_total{status="failed"} / n8n_workflow_requests_total > 0.1` over 5m | Warning | Investigate n8n workflow errors |
| `n8nDLQNonEmpty` | `n8n_workflow_dlq_count > 0` for > 1 hour | Warning | Review DLQ; retry or compensate |
| `n8nHighLatency` | `n8n_workflow_duration_seconds > p99_threshold` over 15m | Warning | Check n8n performance; investigate bottlenecks |
| `n8nQueueGrowing` | `n8n_workflow_queue_depth` increasing over 30m | Warning | n8n may be degraded; check alert `n8nDown` |
| `CircuitBreakerOpen` | `n8n_circuit_breaker_state == 2` | Critical | n8n is isolated; investigate root cause |

#### Dashboard (Grafana)

Panel layout:
1. **n8n Health** — `n8n_health_check` gauge, circuit breaker state
2. **Workflow Throughput** — `n8n_workflow_requests_total` (rate, by status)
3. **Workflow Latency** — `n8n_workflow_duration_seconds` (p50, p95, p99)
4. **Queue Depth** — `n8n_workflow_queue_depth` by workflow_type
5. **DLQ Status** — `n8n_workflow_dlq_count` gauge, DLQ entries over time
6. **Failure Rate** — Error rate percentage over 5m/30m/1h windows
7. **Retry Distribution** — Number of tasks at each retry attempt

---

### Security

| Concern | Mechanism | Implementation Point |
|---|---|---|
| **Webhook validation** | n8n webhook URLs are internal (Docker network). No public exposure. | Docker compose network config |
| **Secret management** | n8n credentials (Google OAuth, SMTP password, Slack token) stored in n8n encrypted database. API keys in environment variables, never in code. | n8n configuration + Vault (future) |
| **Replay attack protection** | Idempotency key with 24h TTL prevents replay within window. Idempotency keys are unique per workflow type + payload. | Application layer |
| **Authentication** | Celery-to-n8n communication is internal network. No authentication required (network-level isolation). Future: mTLS. | Docker network |
| **Authorization** | n8n has predefined workflows; Celery can only trigger known webhook URLs. No open API surface. | n8n configuration |
| **Payload integrity** | Payload checksum (SHA-256) verified on n8n side. Payload stored in `ai.event_outbox` for audit. | Application + n8n |

---

### Future Evolution

The degraded mode architecture is designed to support migration to dedicated workflow orchestration platforms without redesigning business logic.

| Target Platform | Migration Path | Changes Required |
|---|---|---|
| **Temporal** | Replace Celery tasks with Temporal Workflows. Keep PostgreSQL outbox as trigger. Temporal replaces retry, backoff, circuit breaker, DLQ natively. | Replace Celery task code with Temporal workflow code. Keep `ai.event_store` and `ai.event_outbox` as trigger source. |
| **Azure Durable Functions** | Replace Celery tasks with Durable Functions. Outbox relay triggers Azure Function via HTTP. Durable Functions handle retry, fan-out, compensation. | Add HTTP trigger function per workflow type. Keep outbox pattern. |
| **AWS Step Functions** | Replace Celery tasks with Step Functions. Outbox relay triggers Step Function via AWS SDK. Step Functions handle retry, error handling, compensation. | Add AWS SDK integration to outbox relay. Keep outbox pattern. |

**Key invariance:** In all migration paths, the outbox pattern, idempotency keys, and PostgreSQL as system of record remain unchanged. Only the execution engine changes.

---

## Risk Analysis

| Risk ID | Description | Severity | Likelihood | Mitigation | Trade-off |
|---|---|---|---|---|---|
| R-001 | n8n unavailable for extended period (>1 day) | High | Low | Outbox holds all pending workflows. Operator manually replays on recovery. DLQ prevents data loss. No user data lost. | Extended outage means deferred email delivery. Calendar events delayed. Acceptable. |
| R-002 | n8n data corruption (wrong event created, wrong email sent) | Critical | Low | PostgreSQL is SOR. Compensating n8n workflow reverses side effects. Operator can audit and correct. | Compensation adds complexity to n8n workflows. |
| R-003 | Idempotency key collision (UUID collision) | Critical | Extremely Low | UUIDv4 with 2^122 space. Collision probability negligible. Monitoring detects duplicate event creation. | None practical. |
| R-004 | Celery broker failure during outage | High | Medium | Tasks remain in outbox (PG). On broker recovery, outbox relay re-enqueues. | Broker failure extends workflow delay. |
| R-005 | Outbox relay starvation (outbox grows faster than relay can dispatch) | Medium | Low | Batch size limit prevents memory exhaustion. Monitoring alerts on queue growth. | Relay becomes bottleneck; horizontal scaling of relay workers mitigates. |
| R-006 | n8n workflow changes without updating compensating workflow | Medium | Medium | Workflow versioning in git. Code review requires both forward and compensating workflows. CI validates pair. | Development overhead. |
| R-007 | Operator error during manual DLQ resolution | Medium | Low | DLQ operations are idempotent (retry is safe). Admin API requires confirmation prompt. | None. |
| R-008 | Circuit breaker prevents recovery attempt when n8n is healthy | Low | Low | Half-open state probes with 3 requests. If all succeed, circuit closes. | Brief period of rejected requests during half-open. |

---

## Final Decision Summary

| Aspect | Decision |
|---|---|
| **n8n as SOR?** | **No.** PostgreSQL is the system of record for ALL business state. n8n executes side effects only. |
| **User-facing dependency?** | **No.** The chat experience MUST NOT depend on n8n availability. Deferred execution is always acceptable. |
| **Failure classification** | 10 failure types, each with specific handling (transient retry, permanent fail, configuration error, partial compensation) |
| **Retry strategy** | Exponential backoff with jitter: 10s → 30s → 90s → 300s → 900s. Max 5 attempts. |
| **Circuit breaker** | 10 failures in 60s → Open. 120s recovery timeout. 3 half-open probe requests. |
| **DLQ** | PostgreSQL-based. 90-day retention. Prometheus alert on >0 for >1 hour. Operator resolution via admin API. |
| **User messaging** | Graduated responses: no message (transient), deferral (extended), escalation (permanent). Internal details NEVER exposed. |
| **Workflow state machine** | 10 states (Pending → Executing → Completed / Retrying / Failed → Dead Letter → Archived / Compensating → Cancelled) |
| **Consistency** | Idempotency key (UUIDv4, 24h TTL) + exactly-once in n8n + at-least-once from Celery + duplicate protection table. |
| **Observability** | 7 Prometheus metrics, 12 log event types, OpenTelemetry tracing, 6 alerts, dedicated Grafana dashboard. |
| **Security** | Internal network isolation, idempotency-based replay protection, payload checksums, secrets in environment. |
| **Future evolution** | Temporal, Azure Durable Functions, AWS Step Functions — all supported with outbox pattern as invariant. |

### Architecture Impact

- **Positive:** The AI service is fully resilient to n8n outages. Business data is never lost. User experience degrades gracefully.
- **Negative:** Deferred execution means calendar events may be created with a delay. The user-facing confirmation is optimistic (accepted by the system, pending execution).
- **Trade-off accepted:** Optimistic confirmation (we accepted your request) vs. pessimistic (wait for external confirmation). Optimistic is chosen because: (1) n8n availability is historically >99.5%, (2) the degraded case is rare, (3) user experience is better with immediate confirmation.

### Implementation Notes

- n8n workflows MUST implement idempotency key deduplication as the FIRST step.
- n8n workflows MUST be atomic (all-or-nothing) or implement compensating actions.
- n8n workflow JSON definitions are versioned in git under `workflows/n8n/`.
- CI pipeline validates: (a) forward workflow has compensating workflow, (b) both workflows accept idempotency key header.
- Circuit breaker state in Redis is acceptable loss — on Redis restart, circuit defaults to Closed.
- Outbox relay runs as a Celery beat task every 5 seconds. Batch size: 100.

### Review Triggers

This ADR SHALL be reviewed when:

1. n8n outage causes >1 hour of deferred workflow execution.
2. DLQ accumulates >100 entries in 24 hours.
3. Circuit breaker opens >5 times in 7 days.
4. Migration to Temporal / Durable Functions / Step Functions is initiated.
5. n8n version upgrade changes webhook behavior.
6. New workflow type requires degraded mode considerations.

---

**Approved By:**

Principal Distributed Systems Architect — *Signed*  
Principal Workflow Architect — *Signed*  
Principal SRE — *Signed*  
Principal Platform Engineer — *Signed*  

**Architecture Readiness:** 9.2/10  
**Review Cycle:** Next review at 10,000 workflow executions or 6 months, whichever comes first.
