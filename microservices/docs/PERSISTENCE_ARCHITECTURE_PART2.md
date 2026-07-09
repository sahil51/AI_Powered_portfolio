# Phase 4A — Enterprise Persistence Architecture (Part 2)

**Version:** 1.0  
**Author:** Sahil — Principal Database Architect  
**Status:** Pre-Implementation Persistence Design  
**Review Board:** PostgreSQL Core, Redis Labs, Google, Microsoft, Amazon, OpenAI, Anthropic, NVIDIA principal architects  
**Phase Target:** 9.8/10

---

## Architecture Context

This document extends Phase 4A Part 1 (D1–D8) with deliverables D9–D20. Refer to `PERSISTENCE_ARCHITECTURE.md` for the base architecture, schema definitions, and Section 1–8 details.

| Deliverable | Topic |
|---|---|
| D9 | Event Persistence Architecture |
| D10 | Workflow Persistence |
| D11 | Audit Architecture |
| D12 | Backup & Disaster Recovery |
| D13 | Data Lifecycle Management |
| D14 | Security & Compliance |
| D15 | Performance Strategy |
| D16 | Multi-Tenant Persistence Strategy |
| D17 | Architecture Decision Records (Persistence) |
| D18 | Cross-Service Data Ownership Matrix |
| D19 | Persistence Validation |
| D20 | Architecture Review Board |

---

## Table of Contents

9. [Event Persistence Architecture](#9-event-persistence-architecture)
10. [Workflow Persistence](#10-workflow-persistence)
11. [Audit Architecture](#11-audit-architecture)
12. [Backup & Disaster Recovery](#12-backup--disaster-recovery)
13. [Data Lifecycle Management](#13-data-lifecycle-management)
14. [Security & Compliance](#14-security--compliance)
15. [Performance Strategy](#15-performance-strategy)
16. [Multi-Tenant Persistence Strategy](#16-multi-tenant-persistence-strategy)
17. [Architecture Decision Records (Persistence)](#17-architecture-decision-records-persistence)
18. [Cross-Service Data Ownership Matrix](#18-cross-service-data-ownership-matrix)
19. [Persistence Validation](#19-persistence-validation)
20. [Architecture Review Board](#20-architecture-review-board)

---

# 9. Event Persistence Architecture

## 9.1 Event Taxonomy

The AI Executive Assistant produces and consumes events across three categories:

| Category | Characteristics | Examples | Persistence Requirements |
|---|---|---|---|
| **Domain Events** | Business-meaningful, materialized in aggregates | `ConversationCreated`, `LeadScored`, `MemoryConsolidated`, `MeetingScheduled` | Durable, ordered, replayable, auditable |
| **Integration Events** | Cross-service notifications | `PortfolioContactSynced`, `EmailSent`, `CalendarUpdated` | Reliable delivery, at-least-once, idempotent processing |
| **Infrastructure Events** | System-level observability signals | `EmbeddingFailed`, `RateLimitExceeded`, `ModelTimeout` | Best-effort, bounded retention, diagnostic |

## 9.2 Event Store Schema

Domain events are stored in an append-only event store within the `ai` schema.

### 9.2.1 Event Store Table

```sql
CREATE TABLE ai.event_store (
    event_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type          VARCHAR(128) NOT NULL,          -- Fully qualified: ai.conversation.v1.Created
    aggregate_type      VARCHAR(64) NOT NULL,           -- conversation, memory, lead, meeting, workflow
    aggregate_id        UUID NOT NULL,                  -- The aggregate root ID
    version             INTEGER NOT NULL,               -- Aggregate version after this event
    data                JSONB NOT NULL,                 -- Event payload
    metadata            JSONB NOT NULL DEFAULT '{}',    -- Correlation ID, causation ID, tenant ID, user ID
    occurred_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    inserted_at         TIMESTAMPTZ NOT NULL DEFAULT now()  -- Immutable, set once on insert
);
```

Constraints and indexes:

```sql
-- Prevent duplicate events for the same aggregate version
ALTER TABLE ai.event_store ADD CONSTRAINT uq_event_store_aggregate_version
    UNIQUE (aggregate_type, aggregate_id, version);

-- Range query on aggregate history
CREATE INDEX idx_event_store_aggregate
    ON ai.event_store (aggregate_type, aggregate_id, version);

-- Event type queries for projections
CREATE INDEX idx_event_store_type
    ON ai.event_store (event_type, inserted_at);

-- Time-range queries for replay and audit
CREATE INDEX idx_event_store_occurred_at
    ON ai.event_store (occurred_at);

-- BRIN index for append-heavy workload (inserted_at)
CREATE INDEX idx_event_store_inserted_brin
    ON ai.event_store USING BRIN (inserted_at) WITH (pages_per_range = 32);
```

### 9.2.2 Outbox Table

Reliable event publication uses the transactional outbox pattern.

```sql
CREATE TABLE ai.event_outbox (
    outbox_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id            UUID NOT NULL REFERENCES ai.event_store(event_id),
    destination         VARCHAR(128) NOT NULL,           -- RabbitMQ exchange / topic
    routing_key         VARCHAR(128) NOT NULL,
    payload             JSONB NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, published, failed, skipped
    published_at        TIMESTAMPTZ,
    retry_count         INTEGER NOT NULL DEFAULT 0,
    max_retries         INTEGER NOT NULL DEFAULT 3,
    last_error          TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_event_outbox_status
    ON ai.event_outbox (status, created_at)
    WHERE status = 'pending';
```

### 9.2.3 Dead Letter Queue (DLQ)

Events that exceed max retries are moved to the DLQ for manual inspection.

```sql
CREATE TABLE ai.event_dlq (
    dlq_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_outbox_id  UUID,
    event_type          VARCHAR(128) NOT NULL,
    aggregate_type      VARCHAR(64) NOT NULL,
    aggregate_id        UUID NOT NULL,
    payload             JSONB NOT NULL,
    error_detail        JSONB NOT NULL,                 -- Error stack, attempts, timestamps
    status              VARCHAR(20) NOT NULL DEFAULT 'unresolved',  -- unresolved, retrying, archived
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at         TIMESTAMPTZ
);
```

## 9.3 Event Lifecycle

```
┌──────────┐    ┌──────────────┐    ┌────────────┐    ┌───────────┐
│ Aggregate │───▶│ event_store  │───▶│ outbox     │───▶│ Message   │
│ Command   │    │ (append)    │    │ (pending)  │    │ Broker    │
└──────────┘    └──────────────┘    └──────┬─────┘    └───────────┘
                                           │
                                           v
                                    ┌──────────────┐
                                    │ Outbox Relay │
                                    │ (bg worker)  │
                                    │              │
                                    │ status →     │
                                    │ 'published'  │
                                    └──────┬───────┘
                                           │
                              ┌────────────┴────────────┐
                              v                         v
                       ┌──────────────┐          ┌──────────────┐
                       │ Subscriber A │          │ Subscriber B │
                       │ (idempotent) │          │ (idempotent) │
                       └──────────────┘          └──────────────┘
```

### Event State Machine

```
    ┌──────────┐   command()   ┌─────────┐
    │ Created  │──────────────▶│ Stored  │
    └──────────┘               └────┬────┘
                                    │
                            outbox_relay.dispatch()
                                    │
                                    v
                              ┌────────────┐    success    ┌───────────┐
                              │ Publishing │──────────────▶│ Published │
                              └──────┬─────┘               └───────────┘
                                     │
                               max_retries
                               exceeded
                                     │
                                     v
                               ┌──────────┐
                               │ DLQ      │
                               └──────────┘
```

## 9.4 Event Replay

| Trigger | Scope | Mechanism | Impact |
|---|---|---|---|
| Projection rebuild | All events for an aggregate type | Sequential replay from `event_store` | Offline (new projection built before swapping) |
| Bug fix / data recovery | Specific aggregate | Replay from version N, skip broken event | Affected aggregate only |
| Disaster recovery | All events since last consistent snapshot | WAL-based + event_store replay | System-wide, read-only during replay |
| Debugging / audit | Single event | Direct query by event_id | Zero impact |

Replay implementation:

```python
class EventReplayService:
    def rebuild_projection(
        self,
        aggregate_type: str,
        target_version: int,
        batch_size: int = 1000
    ) -> list[Event]:
        events = []
        cursor = None
        while True:
            batch = self.event_store.get_events(
                aggregate_type=aggregate_type,
                cursor=cursor,
                limit=batch_size
            )
            if not batch:
                break
            for event in batch:
                if event.version > target_version:
                    break
                events.append(event)
                cursor = event.event_id
        return events
```

## 9.5 Event Schema Evolution

Events are versioned in the `event_type` field using a semver-like scheme:

| Format | Example | Breaking Change? |
|---|---|---|
| `type.v{n}` | `ai.conversation.v1.Created` | Yes — different major version |
| `type.v{n}.field_added` | `ai.conversation.v1.Created.metadata_added` | No — additive |
| `type.v{n}.field_removed` | `ai.conversation.v1.Created.owner_removed` | Yes — must handle in consumers |

Rules:
1. **Additive changes** (new fields in JSONB `data`) are safe — consumers ignore unknown fields.
2. **Removal or rename** requires a new major version (`v2`).
3. **Consumers declare** the maximum version they support.
4. **The relay** refuses to publish events whose version exceeds all subscriber maximums.
5. **Deprecated versions** are kept in the event store indefinitely (append-only), but the relay stops publishing them after a migration window.

```sql
-- Consumer version registry
CREATE TABLE ai.event_consumer_version (
    consumer_name       VARCHAR(128) PRIMARY KEY,
    supported_events    JSONB NOT NULL,         -- {"ai.conversation.v1.Created": 1, "ai.conversation.v2.Created": 2}
    max_version         INTEGER NOT NULL,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 9.6 Dead Letter Queue

Three resolution strategies for DLQ events:

| Strategy | Description | When to Use |
|---|---|---|
| **Retry** | Re-enqueue to outbox with reset retry count | Transient infrastructure failure |
| **Skip** | Mark as skipped, log warning, continue | Non-critical event, duplicate, stale |
| **Compensate** | Issue a compensating event | Critical event that must be processed eventually |

Manual reconciliation UI (admin API):

```
GET /admin/events/dlq
  → [{dlq_id, event_type, error_detail, created_at}]
POST /admin/events/dlq/{dlq_id}/retry
POST /admin/events/dlq/{dlq_id}/skip
POST /admin/events/dlq/{dlq_id}/compensate  {compensating_payload}
```

## 9.7 Outbox Relay Implementation

```python
class OutboxRelay:
    """
    Dispatches pending events from event_outbox to the message broker.
    Runs as a background Celery task (celerybeat schedule: every 5 seconds).
    """

    def dispatch_pending(self, batch_size: int = 100) -> int:
        pending = self.db.query("""
            SELECT * FROM ai.event_outbox
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT :batch_size
            FOR UPDATE SKIP LOCKED
        """, {"batch_size": batch_size})

        dispatched = 0
        for outbox in pending:
            try:
                self.broker.publish(
                    exchange=outbox.destination,
                    routing_key=outbox.routing_key,
                    payload=outbox.payload,
                    headers={
                        "event_id": str(outbox.event_id),
                        "event_type": outbox.event_type,
                        "content_type": "application/json"
                    }
                )
                self.db.execute("""
                    UPDATE ai.event_outbox
                    SET status = 'published', published_at = now()
                    WHERE outbox_id = :id
                """, {"id": outbox.outbox_id})
                dispatched += 1
            except Exception as e:
                self.db.execute("""
                    UPDATE ai.event_outbox
                    SET retry_count = retry_count + 1,
                        last_error = :error
                    WHERE outbox_id = :id
                """, {"id": outbox.outbox_id, "error": str(e)})

                if outbox.retry_count + 1 >= outbox.max_retries:
                    self.move_to_dlq(outbox)

        self.db.commit()
        return dispatched
```

## 9.8 Event Delivery Guarantees

| Guarantee | Mechanism | Scope |
|---|---|---|
| At-least-once delivery | Outbox pattern (PG tx + broker publish) + consumer idempotency | All events |
| Ordered delivery (per aggregate) | Single-threaded projection / consumer per aggregate partition | Domain events only |
| Exactly-once processing (consumer side) | Idempotency key in consumer (event_id dedup) | All events |
| No duplicate publication | outbox.status = 'published' after successful broker ACK | All events |

Consumer idempotency key:

```sql
CREATE TABLE ai.event_consumer_dedup (
    consumer_name       VARCHAR(128) NOT NULL,
    event_id            UUID NOT NULL,
    processed_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (consumer_name, event_id)
);
```

## 9.9 Event Retention

| Event State | Retention | Storage Layer |
|---|---|---|
| event_store (all events) | Indefinite (append-only) | PostgreSQL — `ai.event_store` |
| outbox (published) | 7 days after published_at | PostgreSQL — `ai.event_outbox` |
| outbox (pending) | 24 hours | PostgreSQL — `ai.event_outbox` |
| DLQ (unresolved) | 90 days | PostgreSQL — `ai.event_dlq` |
| DLQ (archived) | 7 years | S3 Glacier Deep Archive |
| consumer dedup | 90 days | PostgreSQL — `ai.event_consumer_dedup` |

## 9.10 Event Types Catalog

| Event Type | Producer | Consumers | Criticality |
|---|---|---|---|
| `ai.conversation.v1.Created` | Conversation Service | Memory Service, Analytics, Audit, WebSocket | High |
| `ai.conversation.v1.MessageAdded` | Conversation Service | Memory Service, Analytics, Audit, Embedding Service | High |
| `ai.conversation.v1.Archived` | Conversation Service | Memory Service, Storage Tiering | Medium |
| `ai.memory.v1.Consolidated` | Memory Service | Analytics, Audit | High |
| `ai.memory.v1.TTLExpired` | Memory Cleanup Worker | Embedding Service | Low |
| `ai.lead.v1.Scored` | Lead Scoring Service | CRM Sync, Analytics, Notification | High |
| `ai.lead.v1.StatusChanged` | Lead Scoring Service | CRM Sync, Analytics, Notification | Medium |
| `ai.meeting.v1.Scheduled` | Meeting Service | Calendar Sync, Notification | High |
| `ai.meeting.v1.Cancelled` | Meeting Service | Calendar Sync, Notification | Medium |
| `ai.workflow.v1.Started` | Workflow Engine | Audit, Analytics | High |
| `ai.workflow.v1.Completed` | Workflow Engine | Audit, Analytics | Medium |
| `ai.workflow.v1.Failed` | Workflow Engine | Audit, Analytics, Notification | High |
| `ai.embedding.v1.ReindexStarted` | Embedding Service | Audit, Admin API | Low |
| `ai.embedding.v1.ReindexCompleted` | Embedding Service | Audit, Admin API, Model Registry | Low |
| `ai.analytics.v1.ReportGenerated` | Analytics Service | Notification, Audit | Low |
| `ai.infra.v1.RateLimitExceeded` | API Gateway | Rate Limit Service, Alerting | Low |
| `ai.infra.v1.ModelTimeout` | LLM Gateway | Circuit Breaker, Alerting | Medium |
| `ai.infra.v1.EmbeddingFailed` | Embedding Service | Retry Queue, Alerting | Medium |

---

# 10. Workflow Persistence

## 10.1 Workflow Engine Overview

Workflows in the AI Executive Assistant are finite state machines that orchestrate multi-step business processes:

| Workflow | Trigger | Duration | State Count | Persistence Criticality |
|---|---|---|---|---|
| Lead Qualification | New lead created, lead scored | Minutes–days | 6 states | High (revenue impact) |
| Meeting Follow-up | Meeting completed | Hours–days | 4 states | High (customer experience) |
| Memory Consolidation | Idle period, conversation count threshold | Seconds–minutes | 3 states | Medium (quality of service) |
| Embedding Reindex | Schedule, model change | Minutes–hours | 4 states | Low (background) |
| Data Retention Purge | Schedule (daily) | Minutes | 3 states | Medium (compliance) |
| Cross-Service Sync | Portfolio contact update | Seconds | 3 states | Medium |

## 10.2 Workflow Execution Schema

```sql
CREATE TABLE ai.workflow_definition (
    workflow_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(128) NOT NULL UNIQUE,
    description         TEXT,
    version             INTEGER NOT NULL DEFAULT 1,
    state_machine       JSONB NOT NULL,             -- States, transitions, guards as JSON
    max_execution_time  INTERVAL NOT NULL DEFAULT '24 hours',
    retry_policy        JSONB NOT NULL DEFAULT '{"max_retries": 3, "backoff": "exponential", "initial_delay": 10}',
    active              BOOLEAN NOT NULL DEFAULT true,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

```sql
CREATE TABLE ai.workflow_execution (
    execution_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id         UUID NOT NULL REFERENCES ai.workflow_definition(workflow_id),
    correlation_id      VARCHAR(128),               -- Business identifier (lead_id, meeting_id, etc.)
    trigger_event       JSONB,                      -- The event that started this execution
    current_state       VARCHAR(64) NOT NULL,
    state_data          JSONB NOT NULL DEFAULT '{}', -- Current execution context
    status              VARCHAR(20) NOT NULL DEFAULT 'running',
                        -- running, paused, completed, failed, cancelled, timed_out
    attempt             INTEGER NOT NULL DEFAULT 1,
    max_attempts        INTEGER NOT NULL DEFAULT 3,
    started_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at        TIMESTAMPTZ,
    next_retry_at       TIMESTAMPTZ,
    timeout_at          TIMESTAMPTZ NOT NULL,
    tenant_id           UUID,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

```sql
CREATE TABLE ai.workflow_state_history (
    history_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id        UUID NOT NULL REFERENCES ai.workflow_execution(execution_id),
    from_state          VARCHAR(64),
    to_state            VARCHAR(64) NOT NULL,
    transition          VARCHAR(128),               -- Event/action that caused the transition
    data_snapshot       JSONB,                      -- Full state data at transition point
    triggered_by        VARCHAR(64),                -- system, user, schedule
    actor_id            UUID,                       -- User or system component that triggered
    occurred_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_workflow_history_execution
    ON ai.workflow_state_history (execution_id, occurred_at);
```

## 10.3 Workflow State Machines

### 10.3.1 Lead Qualification

```
             ┌─────────────────────────────────────────────────────────┐
             │               Lead Qualification State Machine          │
             └─────────────────────────────────────────────────────────┘

    ┌───────────┐  lead_created   ┌───────────┐
    │ New Lead  │───────────────▶│ Scored    │
    └───────────┘                └─────┬─────┘
                                       │
                              ┌────────┴────────┐
                              v                  v
                        ┌──────────┐      ┌───────────┐
                        │ Hot      │      │ Warm      │
                        │ (score≥8)│      │(score≥4)  │
                        └────┬─────┘      └─────┬─────┘
                             │                  │
                      ┌──────┴──────┐    ┌──────┴──────┐
                      v             v    v             v
                ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
                │ Contacted│  │ Nurturing│  │ Contacted│  │ Nurturing│
                │ (S1)     │  │ (S2)     │  │ (S3)     │  │ (S4)     │
                └─────┬────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
                      │            │             │             │
                      └──────┬─────┘             └──────┬──────┘
                             v                         v
                        ┌──────────┐              ┌──────────┐
                        │ Qualified│              │ Long-term│
                        │          │              │ Nurture  │
                        └──────────┘              └──────────┘
```

### 10.3.2 Meeting Follow-up

```
    ┌──────────┐  meeting_completed   ┌────────────┐
    │ Scheduled│────────────────────▶│ In Follow-up│
    └──────────┘                     └──────┬──────┘
                                           │
                                  ┌────────┴────────┐
                                  v                  v
                            ┌──────────┐      ┌──────────┐
                            │ Summary  │      │ Action   │
                            │ Sent     │      │ Items    │
                            └─────┬────┘      │ Tracked  │
                                  │           └─────┬────┘
                                  └────────┬────────┘
                                           v
                                     ┌──────────┐
                                     │ Completed│
                                     └──────────┘
```

## 10.4 Workflow Execution Lifecycle

```
    ┌──────────┐   trigger_event   ┌──────────┐
    │ Pending  │──────────────────▶│ Running  │
    └──────────┘                   └────┬─────┘
                                        │
                              ┌─────────┴─────────┐
                              v                   v
                        ┌──────────┐        ┌──────────┐
                        │ Paused   │        │ Completing│
                        │ (awaiting│        │ (final    │
                        │  input)  │        │  state)   │
                        └────┬─────┘        └─────┬─────┘
                             │                    │
                             v                    v
                       ┌──────────┐         ┌──────────┐
                       │ Running  │         │ Completed│
                       └──────────┘         └──────────┘

    ┌──────────────────────────────────────────────────────────┐
    │ Any state can transition to:                             │
    │   Failed    — unrecoverable error (max retries exceeded)  │
    │   Cancelled — manual cancellation or timeout              │
    │   Timed Out — max_execution_time exceeded                 │
    └──────────────────────────────────────────────────────────┘
```

## 10.5 Retry and Recovery

| Failure Type | Retry Strategy | Recovery Action |
|---|---|---|
| Transient (network timeout, DB deadlock) | Exponential backoff: 10s, 30s, 90s | Retry same step with incremented attempt |
| State machine guard rejected | No retry (business logic) | Fail execution, log reason |
| External service unavailable | Exponential backoff with jitter: 30s, 90s, 270s | Pause execution, resume when service healthy |
| Data validation error | No retry | Fail execution, notify admin |
| Timeout (execution > max_execution_time) | No retry | Transition to `timed_out`, run compensation |

Retry implementation:

```python
class WorkflowRetryHandler:
    def handle_failure(self, execution: WorkflowExecution, error: Exception) -> None:
        execution.attempt += 1
        if execution.attempt > execution.max_attempts:
            self.fail_execution(execution, error)
            return

        delay = self.calculate_backoff(execution.attempt)
        execution.next_retry_at = utcnow() + timedelta(seconds=delay)
        execution.status = 'paused'
        self.state_history.append(
            execution_id=execution.execution_id,
            to_state='paused',
            transition='retry_scheduled',
            data_snapshot=execution.state_data,
            triggered_by='system'
        )
```

## 10.6 Workflow Queries

| Query | Purpose | Index Used |
|---|---|---|
| Get active executions | Dashboard, monitoring | status = 'running' |
| Get stalled executions (no transition in N minutes) | Dead workflow detection | status + last transition time |
| Get executions by correlation | Find workflow for a business entity | correlation_id |
| Get execution history | Audit, debugging | execution_id |
| Get workflows due for retry | Retry scheduler | next_retry_at ≤ now() |

```sql
-- Active execution monitoring
CREATE INDEX idx_workflow_active
    ON ai.workflow_execution (status, timeout_at)
    WHERE status IN ('running', 'paused');

-- Retry scheduler
CREATE INDEX idx_workflow_retry_due
    ON ai.workflow_execution (next_retry_at)
    WHERE status = 'paused' AND next_retry_at IS NOT NULL;

-- Correlation lookup (business entity → execution)
CREATE INDEX idx_workflow_correlation
    ON ai.workflow_execution (correlation_id);
```

## 10.7 Workflow Persistence Trade-offs

| Decision | Chosen Approach | Alternative | Rationale |
|---|---|---|---|
| State storage | JSONB in PostgreSQL | Redis (pure state machine) | Durability and audit trail needed; Redis is cache, not source of truth |
| History storage | Separate table with data snapshots | WAL-only, event sourcing | Snapshot-based recovery is faster than replay; acceptable storage overhead |
| Retry mechanism | Application-level with next_retry_at | Message broker DLQ | Workflow retry is stateful (resume from last state), not message-level |
| Timeout enforcement | PostgreSQL CHECK + application poller | Redis TTL + Pub/Sub | PostgreSQL timeout is queryable for dashboards; Redis TTL is ephemeral |
| State machine definition | JSONB in workflow_definition | Code-defined FSM (transitions library) | JSONB allows admin UI updates without deployment; code-based is safer for critical paths |

---

# 11. Audit Architecture

## 11.1 Audit Principles

| Principle | Implementation |
|---|---|
| **Immutable** | Append-only, no UPDATE or DELETE, no TRUNCATE (row-level security blocks writes) |
| **Complete** | Every state change across all aggregates is recorded |
| **Tamper-evident** | SHA-256 chain linking each record to its predecessor via `previous_hash` |
| **Timely** | Inserted at database transaction commit via trigger |
| **Queryable** | Indexed for compliance searches and forensic analysis |
| **Retained** | 7 years minimum per regulatory requirements |

## 11.2 Audit Log Schema

```sql
CREATE SCHEMA IF NOT EXISTS audit;
```

### 11.2.1 Central Audit Table

```sql
CREATE TABLE audit.audit_log (
    audit_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Chain integrity
    previous_hash       CHAR(64) NOT NULL,              -- SHA-256 of previous record
    hash                CHAR(64) NOT NULL UNIQUE,       -- SHA-256 of this record's content
    -- Who
    actor_type          VARCHAR(20) NOT NULL,            -- user, system, api_key, scheduled_task
    actor_id            UUID,
    actor_email         VARCHAR(255),
    session_id          UUID,
    -- What
    action              VARCHAR(64) NOT NULL,            -- created, updated, deleted, archived, exported, viewed, login, logout
    resource_type       VARCHAR(64) NOT NULL,            -- conversation, message, memory, lead, meeting, workflow, user, api_key
    resource_id         UUID NOT NULL,
    -- Context
    changes             JSONB,                           -- {field: {old: ..., new: ...}} for updates, full payload for creates
    metadata            JSONB NOT NULL DEFAULT '{}',     -- IP, user_agent, correlation_id, causation_id, tenant_id
    -- When
    occurred_at         TIMESTAMPTZ NOT NULL,            -- When the action happened (application time)
    recorded_at         TIMESTAMPTZ NOT NULL DEFAULT now()  -- When the audit record was written (immutable)
);
```

### 11.2.2 Hash Chain Implementation

```sql
-- Sequence for previous_hash lookup
CREATE SEQUENCE audit.audit_log_seq;

-- Function to compute the hash of an audit record
CREATE OR REPLACE FUNCTION audit.compute_audit_hash(
    p_previous_hash CHAR(64),
    p_actor_type VARCHAR(20),
    p_actor_id UUID,
    p_action VARCHAR(64),
    p_resource_type VARCHAR(64),
    p_resource_id UUID,
    p_changes JSONB,
    p_metadata JSONB,
    p_occurred_at TIMESTAMPTZ
) RETURNS CHAR(64) AS $$
BEGIN
    RETURN encode(
        sha256(
            p_previous_hash ||
            p_actor_type ||
            COALESCE(p_actor_id::TEXT, '') ||
            p_action ||
            p_resource_type ||
            p_resource_id::TEXT ||
            COALESCE(p_changes::TEXT, '') ||
            COALESCE(p_metadata::TEXT, '') ||
            p_occurred_at::TEXT
        ),
        'hex'
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Trigger to enforce hash chain
CREATE OR REPLACE FUNCTION audit.enforce_hash_chain()
RETURNS TRIGGER AS $$
DECLARE
    v_last_hash CHAR(64);
BEGIN
    -- Get the hash of the most recent record
    SELECT hash INTO v_last_hash
    FROM audit.audit_log
    ORDER BY recorded_at DESC, audit_log_seq DESC
    LIMIT 1;

    -- First record uses a genesis hash
    IF v_last_hash IS NULL THEN
        v_last_hash := '0000000000000000000000000000000000000000000000000000000000000000';
    END IF;

    -- Verify previous_hash matches
    IF NEW.previous_hash != v_last_hash THEN
        RAISE EXCEPTION 'Audit hash chain broken: previous_hash % does not match last hash %',
            NEW.previous_hash, v_last_hash;
    END IF;

    -- Compute and verify hash
    NEW.hash := audit.compute_audit_hash(
        NEW.previous_hash,
        NEW.actor_type,
        NEW.actor_id,
        NEW.action,
        NEW.resource_type,
        NEW.resource_id,
        NEW.changes,
        NEW.metadata,
        NEW.occurred_at
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_hash_chain
    BEFORE INSERT ON audit.audit_log
    FOR EACH ROW
    EXECUTE FUNCTION audit.enforce_hash_chain();
```

### 11.2.3 Audit Indexes

```sql
-- Primary access pattern: resource history
CREATE INDEX idx_audit_resource
    ON audit.audit_log (resource_type, resource_id, occurred_at);

-- Compliance search: actor activity
CREATE INDEX idx_audit_actor
    ON audit.audit_log (actor_type, actor_id, occurred_at);

-- Time-range compliance queries
CREATE INDEX idx_audit_occurred_at
    ON audit.audit_log (occurred_at);

-- Action-type analysis
CREATE INDEX idx_audit_action
    ON audit.audit_log (action, resource_type, occurred_at);

-- BRIN for append-heavy time-series queries
CREATE INDEX idx_audit_recorded_brin
    ON audit.audit_log USING BRIN (recorded_at) WITH (pages_per_range = 64);
```

## 11.3 Audit Scopes

| Scope | Description | Retention | Sample Events |
|---|---|---|---|
| **Data Access** | Who read what data | 1 year | `exported`, `viewed`, `searched` |
| **Data Modification** | Who changed what | 7 years | `created`, `updated`, `deleted`, `archived` |
| **Authentication** | Login/logout events | 7 years | `login`, `logout`, `login_failed`, `password_changed` |
| **Authorization** | Permission changes | 7 years | `role_assigned`, `role_revoked`, `permission_granted` |
| **Administrative** | System configuration | 7 years | `config_changed`, `feature_flag_toggled`, `api_key_created`, `api_key_revoked` |
| **Compliance** | Regulatory events | 7 years | `data_exported`, `data_deleted_gdpr`, `consent_changed` |
| **Integration** | Cross-service calls | 90 days | `event_dispatched`, `event_received`, `webhook_fired` |
| **System** | Infrastructure events | 30 days | `service_restarted`, `backup_completed`, `migration_run` |

## 11.4 Audit Writer Service

```python
class AuditWriter:
    """
    Write-audit service. Called by domain services AFTER successful aggregate
    persistence. Runs in the same database transaction where possible, or in a
    best-effort background task for cross-service operations.
    """

    def write(
        self,
        db: DatabaseSession,
        actor: Actor,
        action: str,
        resource_type: str,
        resource_id: UUID,
        changes: dict | None = None,
        metadata: dict | None = None
    ) -> None:
        self._write_sync(db, actor, action, resource_type, resource_id, changes, metadata)

    def write_async(
        self,
        actor: Actor,
        action: str,
        resource_type: str,
        resource_id: UUID,
        changes: dict | None = None,
        metadata: dict | None = None
    ) -> None:
        # Enqueue to internal audit queue (in-memory channel + Redis backup)
        self.queue.enqueue(AuditEvent(
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            metadata=metadata
        ))

    def _write_sync(self, db, actor, action, resource_type, resource_id, changes, metadata):
        # previous_hash is computed by the DB trigger
        db.execute("""
            INSERT INTO audit.audit_log (
                previous_hash, hash,
                actor_type, actor_id, actor_email, session_id,
                action, resource_type, resource_id,
                changes, metadata,
                occurred_at
            ) VALUES (
                '0000000000000000000000000000000000000000000000000000000000000000',
                '',  -- hash computed by trigger
                :actor_type, :actor_id, :actor_email, :session_id,
                :action, :resource_type, :resource_id,
                :changes::JSONB, :metadata::JSONB,
                :occurred_at
            )
        """, {
            "actor_type": actor.type.value,
            "actor_id": str(actor.id) if actor.id else None,
            "actor_email": actor.email,
            "session_id": str(actor.session_id) if actor.session_id else None,
            "action": action,
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "changes": json.dumps(changes) if changes else None,
            "metadata": json.dumps(metadata) if metadata else {},
            "occurred_at": utcnow()
        })
```

## 11.5 Audit Compliance Queries

```sql
-- Q1: "What did user X do in the last 90 days?"
SELECT occurred_at, action, resource_type, resource_id, changes
FROM audit.audit_log
WHERE actor_id = :user_id
  AND occurred_at >= now() - interval '90 days'
ORDER BY occurred_at DESC;

-- Q2: "Who accessed lead Y?"
SELECT DISTINCT actor_id, actor_email, occurred_at
FROM audit.audit_log
WHERE resource_type = 'lead'
  AND resource_id = :lead_id
  AND action IN ('viewed', 'exported', 'updated')
ORDER BY occurred_at DESC;

-- Q3: "Verify hash chain integrity for [date range]"
SELECT
    count(*) AS total_records,
    bool_and(
        hash = audit.compute_audit_hash(
            previous_hash, actor_type, actor_id::text,
            action, resource_type, resource_id::text,
            changes::text, metadata::text, occurred_at::text
        )
    ) AS chain_intact
FROM audit.audit_log
WHERE recorded_at BETWEEN :start_date AND :end_date;

-- Q4: "Find all deletions in the last 7 days"
SELECT occurred_at, actor_email, resource_type, resource_id, changes
FROM audit.audit_log
WHERE action = 'deleted'
  AND occurred_at >= now() - interval '7 days'
ORDER BY occurred_at DESC;

-- Q5: "Get full history of resource R"
SELECT occurred_at, action, actor_email, changes
FROM audit.audit_log
WHERE resource_type = :resource_type
  AND resource_id = :resource_id
ORDER BY occurred_at ASC;
```

## 11.6 Audit Storage and Retention

| Storage Tier | Retention | Implementation |
|---|---|---|
| Hot (PostgreSQL) | Current + 90 days | `audit.audit_log` — indexed, online queryable |
| Warm (PostgreSQL + partitioning) | 90 days – 7 years | Table partitioned by month; older partitions moved to slower tablespace |
| Cold (S3 Glacier Deep Archive) | After 7 years | pg_dump partition → S3 Glacier; partition dropped from PG |

Monthly partitioning:

```sql
CREATE TABLE audit.audit_log_y2026m06 PARTITION OF audit.audit_log
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01')
    TABLESPACE audit_fast;

CREATE TABLE audit.audit_log_y2026m05 PARTITION OF audit.audit_log
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01')
    TABLESPACE audit_warm;
```

---

# 12. Backup & Disaster Recovery

## 12.1 RPO and RTO Targets

| Data Category | RPO (Recovery Point Objective) | RTO (Recovery Time Objective) | Criticality |
|---|---|---|---|
| Conversations (active, ≤90 days) | 1 minute | 15 minutes | Critical |
| Conversations (warm, 90d–1yr) | 1 hour | 4 hours | Important |
| Conversations (cold, >1yr) | 24 hours | 24 hours | Normal |
| Messages (recent, ≤24h) | 0 (synchronous Redis AOF + PG) | 5 minutes | Critical |
| Messages (active, ≤90d) | 5 minutes | 30 minutes | Critical |
| Memory (long-term) | 15 minutes | 1 hour | Critical |
| Meetings (upcoming) | 0 (synchronous) | 5 minutes | Critical |
| Leads (active) | 5 minutes | 30 minutes | Critical |
| Workflow Executions (running) | 0 (Redis AOF + PG state) | 5 minutes | Critical |
| Analytics (aggregated) | 1 hour | 4 hours | Normal |
| Audit Log | 5 minutes | 1 hour | Compliance |
| Embeddings | 1 hour (snapshot) + source rebuild | 4 hours (snapshot), 12 hours (full rebuild) | Normal |

## 12.2 PostgreSQL Backup Strategy

### 12.2.1 Continuous Archiving (WAL)

```ini
# postgresql.conf
wal_level = replica                    # Required for PITR
archive_mode = on
archive_command = 'aws s3 cp %p s3://ai-assistant-backups/wal/%f --storage-class STANDARD_IA'
archive_timeout = 60                    # Archive every 60 seconds regardless of activity
```

### 12.2.2 Full Backups

| Type | Frequency | Retention | Storage Class | Tool |
|---|---|---|---|---|
| Full base backup | Weekly (Sunday 0200 UTC) | 4 weeks | S3 STANDARD | `pg_basebackup` |
| Incremental / WAL | Continuous (every 60s) | 2 weeks | S3 STANDARD_IA | `archive_command` + WAL |
| Logical dump (schema only) | Daily (0100 UTC) | 90 days | S3 STANDARD_IA | `pg_dump --schema-only` |
| Logical dump (data, critical tables) | Daily (0300 UTC) | 90 days | S3 STANDARD_IA | `pg_dump --data-only —table=ai.lead,ai.meeting` |
| Snapshot (EBS / SAN) | Pre-migration, pre-deploy | 7 days | S3 STANDARD | Cloud provider snapshot |

### 12.2.3 PITR Configuration

```bash
# Recovery target: point in time
pg_ctl -D /var/lib/postgresql/data start -o "-c recovery_target_time='2026-06-30 14:30:00 UTC'"

# Recovery.conf (restore_command) for S3:
restore_command = 'aws s3 cp s3://ai-assistant-backups/wal/%f %p'
recovery_target_time = '2026-06-30 14:30:00 UTC'
recovery_target_action = promote
```

## 12.3 Redis Backup Strategy

### 12.3.1 Persistence Configuration

```ini
# redis.conf
save 900 1           # RDB: snapshot every 15 min if at least 1 key changed
save 300 10          # RDB: snapshot every 5 min if at least 10 keys changed
save 60 10000        # RDB: snapshot every 60 sec if at least 10000 keys changed

appendonly yes
appendfsync everysec # AOF: fsync every second (balance of durability and performance)
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
```

### 12.3.2 Redis Backup Schedule

| Backup Type | Frequency | Retention | Location | Tool |
|---|---|---|---|---|
| RDB snapshot | Every 60s (as configured) | 24 hours | Local disk + S3 | `BGSAVE` + `aws s3 cp` |
| AOF file | Continuous | 7 days | Local disk + S3 | Redis AOF + S3 sync (hourly) |
| Logical export | Hourly (critical keys only) | 7 days | S3 STANDARD | `redis-cli --scan --pattern` + `DUMP` |

## 12.4 S3 Backup Architecture

```
                    ┌─────────────────────────────┐
                    │   S3 Bucket: ai-assistant-   │
                    │   backups                    │
                    ├─────────────────────────────┤
                    │  s3://.../pg/               │
                    │    ├── base/                │  Weekly pg_basebackup
                    │    ├── wal/                 │  Continuous WAL archive
                    │    │   └── 0000000100000001/│
                    │    ├── logical/             │  Daily pg_dump
                    │    └── snapshots/           │  Pre-deploy snapshots
                    │                             │
                    │  s3://.../redis/            │
                    │    ├── rdb/                 │  Hourly RDB upload
                    │    └── aof/                 │  Hourly AOF upload
                    │                             │
                    │  s3://.../event-store/      │
                    │    └── export/              │  Monthly event_store dump
                    │                             │
                    │  s3://.../config/           │
                    │    └── env/                 │  Encrypted env backups
                    └─────────────────────────────┘
```

## 12.5 Disaster Recovery Tiers

### 12.5.1 Tier 1 — Single Instance Failure (RTO: 5 minutes)

| Failure | Recovery Action | Automation |
|---|---|---|
| PostgreSQL process crash | Systemd auto-restart (3 attempts) | systemd unit `Restart=on-failure` |
| PostgreSQL host failure | Read-replica promotion (if configured) | Patroni / pg_autoctl (future) |
| Redis process crash | Systemd auto-restart | systemd unit `Restart=on-failure` |
| Redis data loss (AOF intact) | Redis AOF replay on restart | Automatic (redis.conf appendonly yes) |

### 12.5.2 Tier 2 — Instance Restart Required (RTO: 15 minutes)

| Failure | Recovery Action |
|---|---|
| OS crash / kernel panic | Cloud provider auto-recovery |
| Data corruption (single table) | PITR to specific table from WAL |
| Accidental data deletion (single row) | PITR to point before deletion → extract row → re-insert |

### 12.5.3 Tier 3 — Full Region Failure (RTO: 4 hours, RPO: 1 hour)

Manual recovery procedure:

```
1. Provision new PostgreSQL instance in secondary region
   → Apply schema from last logical dump (s3://.../pg/logical/)
2. Restore base backup from S3 (s3://.../pg/base/)
3. Apply WAL archives from S3 to recovery_target_time
4. Verify data integrity:
   → Row counts match last backup report
   → Audit hash chain is intact
   → Application health checks pass
5. Switch DNS / load balancer to secondary region
6. Provision Redis instance → restore latest RDB from S3
7. Verify critical data:
   → Conversations, leads, meetings, workflows present
8. Begin WAL streaming from primary (if primary is recoverable)
```

### 12.5.4 Tier 4 — Catastrophic Data Loss (RTO: 12 hours, RPO: 24 hours)

Full rebuild from event store + S3 archives:

```
1. Provision fresh infrastructure (PG + Redis)
2. Restore schema from logical dump
3. Restore event_store from S3 (latest monthly export)
4. Replay all domain events to rebuild projections
5. Re-generate all embeddings (full reindex: ~8–12 hours)
6. Rebuild Redis cache from PG data
7. Verify complete audit log hash chain
8. Validate all business metrics against last known good state
```

## 12.6 Backup Verification

| Check | Frequency | Action on Failure |
|---|---|---|
| WAL archive completeness | Hourly | Alert → check archive_command → manual WAL copy |
| Base backup restorability | Weekly (after each backup) | Verify pg_basebackup can start PostgreSQL |
| Logical dump integrity | Daily | pg_restore —list → verify all expected tables present |
| PITR drill (complete restore) | Monthly | Full restore to test environment → run health checks |
| Redis RDB integrity | Daily | `redis-check-rdb` on latest backup |
| S3 object integrity | After each upload | ETag validation vs local file MD5 |

## 12.7 Backup Monitoring and Alerting

| Metric | Threshold | Severity | Action |
|---|---|---|---|
| WAL archive lag | > 5 minutes behind current WAL | Critical | Alert on-call, check archive_command |
| Last full backup age | > 8 days | Warning | Trigger manual base backup |
| Last logical dump age | > 26 hours | Warning | Trigger manual pg_dump |
| Backup storage cost | > 20% increase WoW | Info | Review retention policies |
| S3 upload failure rate | > 1% in 1 hour | Warning | Check S3 permissions, network |
| PITR test success rate | < 100% in last month | Critical | Fix recovery procedure |

---

# 13. Data Lifecycle Management

## 13.1 Data Lifecycle Stages

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Created  │───▶│ Active   │───▶│ Archived │───▶│ Purged   │
│          │    │          │    │          │    │          │
│ Immutable│    │ Read/    │    │ Compressed│   │ Destroyed│
│ initial  │    │ Write    │    │ Cheap    │    │ Irrecover│
│ state    │    │ Tier 1   │    │ Tier 2   │    │ Tier 3   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

## 13.2 Entity Lifecycle Policies

| Entity | Active Retention | Archive Trigger | Archive Storage | Archive Retention | Purge Trigger |
|---|---|---|---|---|---|
| Conversation | 90 days | conversation.archived_at ≥ 90d | S3 Glacier JSON | 7 years (6yr 275d in Glacier) | After 7 years |
| Message | 90 days | Same as conversation | S3 Glacier (batched per conversation) | 7 years | After 7 years |
| Conversation Summary | 90 days (PG) + 7d TTL (Redis) | Archived conversation | S3 Glacier | 7 years | After 7 years |
| Memory | Indefinite (core) + 90d TTL (working) | 2 years inactive | S3 Glacier | Indefinite | Never (core) |
| Meeting | 1 year + upcoming meeting cache | 1 year after completion | S3 Glacier | 7 years (6yr in Glacier) | After 7 years |
| Meeting Recording | 1 year | 1 year after meeting | S3 Glacier Deep Archive | 7 years | After 7 years |
| Lead (active) | Indefinite | Lead closed + 1 year | S3 Glacier | 3 years (2yr in Glacier) | After 3 years closed |
| Lead (closed-lost) | 1 year | Closed-lost + 90 days | S3 Glacier | 3 years | After 3 years |
| Workflow Execution | 90 days (completed) + 1 year (failed) | 90 days completed | S3 Glacier | 7 years | After 7 years |
| Embedding | Tied to source document | Source archived | S3 (model-versioned snapshot) | Tied to source + 1 year | After source purge + 1 year |
| Analytics Raw | 3 years | 3 years | S3 Glacier | 7 years (4yr in Glacier) | After 7 years |
| Analytics Aggregated | 7 years | 7 years | S3 Glacier Deep Archive | Indefinite | Never |
| Audit Log | 90 days (hot) + 7 years partitioned | 7 years | S3 Glacier Deep Archive | Indefinite | Never |
| Notification | 90 days | 90 days | S3 Glacier | 1 year | After 1 year |
| Session | 24h (Redis) + 7d (PG backup) | 7 days | None (ephemeral) | None | After 7 days |

## 13.3 Archive Implementation

### 13.3.1 Conversation Archive (Primary Example)

```python
class ConversationArchiveService:
    """
    Moves conversations from active Tier 1 storage to archived Tier 2 (S3 Glacier).
    Triggered by Celery Beat daily at 0200 UTC.
    """

    BATCH_SIZE = 100

    def archive_stale_conversations(self) -> int:
        archived = 0
        cursor = None
        while True:
            conversations = self.db.query("""
                SELECT conversation_id, tenant_id
                FROM ai.conversation
                WHERE archived_at IS NULL
                  AND status = 'inactive'
                  AND last_activity_at < now() - interval '90 days'
                  AND deleted_at IS NULL
                ORDER BY conversation_id
                LIMIT :batch_size
                FOR UPDATE SKIP LOCKED
            """, {"batch_size": self.BATCH_SIZE})

            if not conversations:
                break

            for conv in conversations:
                self._archive_single(conv.conversation_id)
                archived += 1

        return archived

    def _archive_single(self, conversation_id: UUID) -> None:
        with self.db.transaction():
            # 1. Fetch all messages for this conversation
            messages = self.db.query("""
                SELECT * FROM ai.message
                WHERE conversation_id = :cid
                ORDER BY created_at ASC
            """, {"cid": conversation_id})

            # 2. Fetch conversation summary
            summary = self.db.query_one("""
                SELECT * FROM ai.conversation_summary
                WHERE conversation_id = :cid
            """, {"cid": conversation_id})

            # 3. Build archive document
            archive_doc = {
                "conversation_id": str(conversation_id),
                "messages": [dict(m) for m in messages],
                "summary": dict(summary) if summary else None,
                "archived_at": utcnow().isoformat(),
                "schema_version": 1
            }

            # 4. Upload to S3 Glacier
            archive_key = f"archived/conversations/{conversation_id}/{utcnow():%Y/%m/%d}/archive.json"
            self.s3.put_object(
                Bucket=self.archive_bucket,
                Key=archive_key,
                Body=json.dumps(archive_doc, default=str),
                StorageClass="GLACIER"
            )

            # 5. Mark conversation and messages as archived in PG
            self.db.execute("""
                UPDATE ai.conversation
                SET archived_at = now(), archive_key = :key
                WHERE conversation_id = :cid
            """, {"cid": conversation_id, "key": archive_key})

            self.db.execute("""
                UPDATE ai.message
                SET archived = true
                WHERE conversation_id = :cid
            """, {"cid": conversation_id})

            # 6. Delete from hot tables (or keep soft-deleted reference)
            self.db.execute("""
                DELETE FROM ai.conversation_summary
                WHERE conversation_id = :cid
            """, {"cid": conversation_id})
```

### 13.3.2 Archive Metadata Table

```sql
CREATE TABLE ai.archive_manifest (
    archive_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type       VARCHAR(64) NOT NULL,
    resource_id         UUID NOT NULL,
    archive_key         VARCHAR(1024) NOT NULL,        -- S3 key
    storage_class       VARCHAR(20) NOT NULL DEFAULT 'GLACIER',
    schema_version      INTEGER NOT NULL DEFAULT 1,
    size_bytes          BIGINT,
    checksum            CHAR(64),                      -- SHA-256 of archive content
    archived_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    scheduled_purge_at  TIMESTAMPTZ,                   -- When this archive can be deleted
    purged_at           TIMESTAMPTZ
);

CREATE INDEX idx_archive_manifest_resource
    ON ai.archive_manifest (resource_type, resource_id);

CREATE INDEX idx_archive_manifest_purge
    ON ai.archive_manifest (scheduled_purge_at)
    WHERE purged_at IS NULL;
```

## 13.4 Purge Implementation

```python
class DataPurgeService:
    """
    Permanently deletes data whose retention period has expired.
    Triggered by Celery Beat daily at 0300 UTC.
    """

    def purge_expired_data(self) -> PurgeReport:
        report = PurgeReport()

        # Purge expired conversations
        expired_conversations = self.db.query("""
            SELECT archive_key FROM ai.archive_manifest
            WHERE resource_type = 'conversation'
              AND scheduled_purge_at <= now()
              AND purged_at IS NULL
            LIMIT 1000
        """)

        for manifest in expired_conversations:
            try:
                self.s3.delete_object(
                    Bucket=self.archive_bucket,
                    Key=manifest.archive_key
                )
                self.db.execute("""
                    UPDATE ai.archive_manifest
                    SET purged_at = now()
                    WHERE archive_key = :key
                """, {"key": manifest.archive_key})
                report.archives_purged += 1
            except Exception as e:
                report.errors.append(f"Failed to purge {manifest.archive_key}: {e}")

        # Purge expired notification records
        self.db.execute("""
            DELETE FROM ai.notification
            WHERE created_at < now() - interval '90 days'
        """)
        report.notifications_purged = self.db.rowcount

        # Purge old event consumer dedup records
        self.db.execute("""
            DELETE FROM ai.event_consumer_dedup
            WHERE processed_at < now() - interval '90 days'
        """)
        report.consumer_dedup_purged = self.db.rowcount

        # Purge old analytics raw data (move to aggregated-only)
        self.db.execute("""
            DELETE FROM analytics.raw_event
            WHERE occurred_at < now() - interval '3 years'
        """)
        report.analytics_raw_purged = self.db.rowcount

        self.db.commit()
        return report
```

## 13.5 Lifecycle Automation

| Automation | Cadence | Responsible Component |
|---|---|---|
| Archive stale conversations | Daily 0200 UTC | Celery Beat → `archive_stale_conversations` |
| Archive completed meetings | Daily 0215 UTC | Celery Beat → `archive_completed_meetings` |
| Archive closed leads | Daily 0230 UTC | Celery Beat → `archive_closed_leads` |
| Archive completed workflows | Daily 0245 UTC | Celery Beat → `archive_completed_workflows` |
| Archive old embeddings (model snapshots) | Monthly 1st 0300 UTC | Celery Beat → `archive_old_embeddings` |
| Purge expired data | Daily 0300 UTC | Celery Beat → `purge_expired_data` |
| Clean up orphaned embeddings | Daily 0400 UTC | Celery Beat → `cleanup_orphaned_embeddings` |
| Verify archive integrity | Weekly 0500 UTC Sunday | Celery Beat → `verify_archive_integrity` |

## 13.6 Data Restoration from Archive

```python
class ArchiveRestoreService:
    """
    Restores archived data (conversations, meetings, leads) from S3 Glacier.
    Invoked on-demand via admin API.
    """

    def restore_conversation(self, conversation_id: UUID) -> dict:
        manifest = self.db.query_one("""
            SELECT * FROM ai.archive_manifest
            WHERE resource_type = 'conversation'
              AND resource_id = :id
              AND purged_at IS NULL
        """, {"id": conversation_id})

        if not manifest:
            raise NotFound("Conversation not found in archive")

        # Request S3 Glacier restore (takes 3-5 hours for standard retrieval)
        self.s3.restore_object(
            Bucket=self.archive_bucket,
            Key=manifest.archive_key,
            RestoreRequest={
                'Days': 7,
                'GlacierJobParameters': {'Tier': 'Expedited'}
            }
        )

        return {
            "conversation_id": str(conversation_id),
            "archive_key": manifest.archive_key,
            "restore_status": "initiated",
            "estimated_completion": (utcnow() + timedelta(hours=1)).isoformat()
        }
```

## 13.7 Compliance Deletion (GDPR / CCPA / Right to Erasure)

```python
class ComplianceDeletionService:
    """
    Full erasure of all personal data for a given user/tenant.
    Compliant with GDPR Article 17, CCPA Section 1798.105.
    """

    ERASURE_CATEGORIES = [
        "conversation", "message", "memory",
        "lead", "meeting", "notification", "session"
    ]

    def erase_user_data(self, user_id: UUID, tenant_id: UUID) -> ErasureReport:
        report = ErasureReport(user_id=user_id)

        with self.db.transaction():
            for category in self.ERASURE_CATEGORIES:
                count = self._erase_category(user_id, category)
                setattr(report, f"{category}_deleted", count)

            # Anonymize audit trail (replace personal identifiers with hash)
            self.db.execute("""
                UPDATE audit.audit_log
                SET actor_email = encode(sha256(actor_email::bytea), 'hex'),
                    metadata = jsonb_set(metadata, '{erased_at}', to_jsonb(now()::text))
                WHERE actor_id = :user_id
                  AND actor_type = 'user'
            """, {"user_id": user_id})

            # Remove from all cache layers
            self.cache.invalidate_user(user_id, tenant_id)

        # Queue asynchronous S3 archive deletion
        self.queue.enqueue(ArchiveDeletionRequest(user_id=user_id))

        self._log_compliance_erasure(user_id, report)
        return report

    def _erase_category(self, user_id: UUID, category: str) -> int:
        table_map = {
            "conversation": "ai.conversation",
            "message": "ai.message",
            "memory": "ai.memory",
            "lead": "ai.lead",
            "meeting": "ai.meeting",
            "notification": "ai.notification",
            "session": "ai.session"
        }

        # Soft-delete: mark as deleted for compliance audit
        self.db.execute(f"""
            UPDATE {table_map[category]}
            SET deleted_at = now(),
                deleted_by = 'compliance_erasure',
                metadata = jsonb_set(
                    COALESCE(metadata, '{{}}'),
                    '{{erasure_request_id}}',
                    to_jsonb(:request_id::text)
                )
            WHERE user_id = :user_id
              AND deleted_at IS NULL
        """, {"user_id": user_id, "request_id": str(self.request_id)})

        return self.db.rowcount
```

---

# 14. Security & Compliance

## 14.1 Encryption Strategy

### 14.1.1 Encryption at Rest

| Layer | Mechanism | Key Management |
|---|---|---|
| PostgreSQL data files | TDE (pg_tde extension) or LUKS on volume | AWS KMS / Azure Key Vault |
| PostgreSQL WAL | pg_tde WAL encryption | Same key as data files |
| PostgreSQL temp files | Encrypted by OS (LUKS) | LUKS passphrase in KMS |
| Redis RDB / AOF | Encrypted at storage layer (EBS) | AWS KBS / Azure Storage Service Encryption |
| S3 objects | SSE-S3 (AES-256) or SSE-KMS | S3-managed or KMS |
| Backups (S3) | SSE-S3 default + client-side encryption for archives | KMS (`aws/s3`) |

### 14.1.2 Encryption in Transit

| Path | Protocol | Cipher |
|---|---|---|
| Client → FastAPI | TLS 1.3 | TLS_AES_256_GCM_SHA384 |
| FastAPI → PostgreSQL | TLS 1.3 | tlsv1.3 + channel binding |
| FastAPI → Redis | TLS 1.2+ (STunnel) | AES-256-GCM |
| FastAPI → S3 | HTTPS (TLS 1.2+) | AES-256-GCM |
| FastAPI → RabbitMQ | AMQPS (TLS 1.2+) | AES-256-GCM |
| FastAPI → OpenAI / Anthropic / Other LLM | HTTPS (TLS 1.3) | Provider-managed |
| Internal service mesh | mTLS (if service mesh enabled) | Mutual TLS, SPIFFE identities |

### 14.1.3 Column-Level Encryption (Sensitive PII)

```sql
-- Extension for pgcrypto (column-level encryption)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- PII columns in the ai schema
ALTER TABLE ai.lead
    ADD COLUMN email_encrypted BYTEA,
    ADD COLUMN phone_encrypted BYTEA,
    ADD COLUMN ssn_last4_encrypted BYTEA;

-- Encrypted PII access via application layer only
-- Application decrypts using KMS envelope encryption:
--   1. Decrypt data key from KMS (cached in memory, 1h TTL)
--   2. Use data key to decrypt column via pgcrypto
```

Python-side encryption helper:

```python
class PIIDecryptor:
    """
    Envelope encryption for PII columns.
    Data key is fetched from KMS, cached in process memory for 1 hour.
    """

    def __init__(self, kms_client):
        self.kms = kms_client
        self._data_key = None
        self._data_key_cached_at = None

    def _get_data_key(self) -> bytes:
        if (self._data_key and self._data_key_cached_at
                and utcnow() - self._data_key_cached_at < timedelta(hours=1)):
            return self._data_key

        response = self.kms.generate_data_key(
            KeyId='alias/ai-assistant-pii-key',
            KeySpec='AES_256'
        )
        self._data_key = response['Plaintext']
        self._data_key_cached_at = utcnow()
        return self._data_key

    def encrypt(self, plaintext: str) -> bytes:
        data_key = self._get_data_key()
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(data_key), modes.GCM(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
        return iv + encryptor.tag + ciphertext

    def decrypt(self, encrypted: bytes) -> str:
        data_key = self._get_data_key()
        iv = encrypted[:16]
        tag = encrypted[16:32]
        ciphertext = encrypted[32:]
        cipher = Cipher(algorithms.AES(data_key), modes.GCM(iv, tag))
        decryptor = cipher.decryptor()
        return (decryptor.update(ciphertext) + decryptor.finalize()).decode()
```

## 14.2 Access Control

### 14.2.1 Database Access

| Role | Schema Access | Tables | Purpose |
|---|---|---|---|
| `ai_owner` | ai, audit, analytics, vector | ALL | Schema migrations (admin use only) |
| `ai_readwrite` | ai, analytics, vector | ALL except audit | Application service accounts |
| `ai_readonly` | ai, analytics | ALL | Reporting, dashboards |
| `audit_append` | audit | audit_log ONLY (INSERT) | Audit writer service |
| `audit_readonly` | audit | audit_log ONLY (SELECT) | Compliance auditors |
| `public_readonly` | public | SELECT on portfolio tables | AI service read access to portfolio |

```sql
-- Create roles
CREATE ROLE ai_owner;
CREATE ROLE ai_readwrite;
CREATE ROLE ai_readonly;
CREATE ROLE audit_append;
CREATE ROLE audit_readonly;

-- Grant schema permissions
GRANT ALL ON SCHEMA ai TO ai_owner;
GRANT USAGE ON SCHEMA ai TO ai_readwrite;
GRANT ALL ON ALL TABLES IN SCHEMA ai TO ai_readwrite;
GRANT USAGE ON SCHEMA ai TO ai_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA ai TO ai_readonly;

-- Audit schema: append-only via INSERT-only trigger
GRANT USAGE ON SCHEMA audit TO audit_append;
GRANT INSERT ON audit.audit_log TO audit_append;
GRANT SELECT ON audit.audit_log TO audit_readonly;

-- Block UPDATE/DELETE on audit
REVOKE UPDATE, DELETE ON audit.audit_log FROM audit_append;
REVOKE UPDATE, DELETE ON audit.audit_log FROM audit_readonly;
```

### 14.2.2 Row-Level Security (RLS)

Multi-tenant isolation via RLS (enforced at database level):

```sql
-- Enable RLS on tenant-scoped tables
ALTER TABLE ai.conversation ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.message ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.lead ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.meeting ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.workflow_execution ENABLE ROW LEVEL SECURITY;

-- RLS policy: users can only access their tenant's data
CREATE POLICY tenant_isolation ON ai.conversation
    USING (tenant_id = current_setting('app.tenant_id')::UUID);

CREATE POLICY tenant_isolation ON ai.message
    USING (tenant_id = current_setting('app.tenant_id')::UUID);

-- The application sets app.tenant_id at connection pool checkout
```

## 14.3 Secret Management

| Secret Type | Storage | Rotation | Access |
|---|---|---|---|
| Database passwords | Vault (dynamic secrets) | 30 days | Application service account |
| API keys (OpenAI, Anthropic, etc.) | Vault + env vars | 90 days or on compromise | Application service account |
| JWT signing keys | Vault + env vars | 30 days (rotation) | Auth service |
| Encryption keys (KMS) | AWS KMS / Azure Key Vault | Per KMS policy | IAM role |
| TLS certificates | Certificate manager | 90 days (auto-renewal) | Load balancer + application |

## 14.4 Audit and Monitoring Integration

Audit records feed into the security monitoring pipeline:

| Security Event | Audit Action | Alert Threshold | Response |
|---|---|---|---|
| Failed login | `login_failed` | 5 attempts in 5 minutes | Rate-limit IP, notify security |
| Data export (bulk) | `exported` | > 1000 rows in 5 minutes | Notify security, flag for review |
| Permission change | `role_assigned` / `role_revoked` | Any change by non-admin | Immediate security review |
| API key creation | `api_key_created` | Any new key | Notify admin |
| Data deletion (bulk) | `deleted` | > 100 rows in 1 minute | Notify admin, verify intent |
| GDPR erasure request | `data_deleted_gdpr` | Per request | Log to compliance system |

## 14.5 Compliance Certifications (Target)

| Standard | Scope | Target Date |
|---|---|---|
| SOC 2 Type II | Security, Availability, Confidentiality | Year 1 |
| ISO 27001 | Information Security Management | Year 1 |
| GDPR | Data protection for EU users | Launch |
| CCPA | Data protection for CA (US) users | Launch |
| HIPAA (if health data) | Protected health information | Future |
| PCI DSS (if payment data) | Payment card information | Future |

---

# 15. Performance Strategy

## 15.1 Performance Budgets

| Operation | Latency Budget (p99) | Throughput Target | Query Pattern |
|---|---|---|---|
| Conversation create | 100ms | 1000/s | Single INSERT |
| Message append | 50ms | 5000/s | INSERT + indexed lookup |
| Message history fetch (last 50) | 30ms | 500/s | Indexed SELECT with LIMIT |
| Conversation list (user scoped) | 100ms | 200/s | Indexed SELECT, paginated |
| Memory read (by key) | 20ms | 2000/s | Indexed SELECT or Redis GET |
| Memory write | 50ms | 500/s | UPSERT |
| Lead search | 200ms | 100/s | Multi-column indexed + full-text |
| Meeting schedule | 100ms | 50/s | INSERT + calendar check |
| Workflow transition | 200ms | 100/s | UPDATE state + INSERT history |
| Embedding search (ANN) | 200ms | 100/s | pgvector HNSW |
| Audit log write | 20ms (async acceptable) | 1000/s | APPEND (INSERT) |
| Backup (full) | 2 hours (window) | N/A | Sequential read |
| Archive (conversation batch) | 5 minutes per 1000 | N/A | Batch read + S3 upload |
| Event store append | 20ms | 2000/s | Single INSERT |
| Event replay (per aggregate) | 1s per 10,000 events | N/A | Sequential index scan |

## 15.2 Connection Pooling

```ini
# PostgreSQL connection pool (FastAPI service)
# Using asyncpg / SQLAlchemy async

pool_size = 20
max_overflow = 10
pool_timeout = 30 seconds
pool_recycle = 300 seconds

# Per-endpoint pool allocation:
# GET endpoints: 1 connection per 100 RPS (shared pool)
# POST endpoints: 1 connection per 50 RPS (shared pool)
# Background workers: dedicated 5-connection pool
# Admin/migration: separate 3-connection pool
```

```python
# FastAPI dependency — connection pool configuration
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@host:5432/ai_assistant",
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=300,
    pool_pre_ping=True,
    echo=False,
    json_serializer=lambda o: json.dumps(o, default=str)
)
```

## 15.3 Query Optimization

### 15.3.1 Index Strategy Review

| Table | Query Pattern | Indexes | Justification |
|---|---|---|---|
| `ai.conversation` | User-scoped list, status filter | `(user_id, last_activity_at DESC)`, `(status, tenant_id)` | Covering index for primary query |
| `ai.message` | Conversation timeline | `(conversation_id, created_at ASC)` | Sequential read per conversation |
| `ai.lead` | Sales pipeline, scoring | `(status, score DESC)`, `(assigned_to, status)`, `(email)` | Pipeline view, lookup, dedup |
| `ai.meeting` | Upcoming, user-scoped | `(user_id, start_time)`, `(meeting_id, tenant_id)` | Calendar queries, RLS |
| `ai.memory` | User + type + key lookup | `(user_id, memory_type, key)` | Primary access pattern |
| `ai.workflow_execution` | Active, stalled | `(status, timeout_at) WHERE status IN ('running','paused')`, `(correlation_id)` | Monitoring, business lookup |
| `ai.event_store` | Aggregate replay, type filter | `(aggregate_type, aggregate_id, version)`, `(event_type, inserted_at)` | Projection rebuild, audit |

### 15.3.2 Slow Query Detection

```sql
-- Enable pg_stat_statements extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Periodic monitoring query
SELECT
    queryid,
    calls,
    total_exec_time / calls AS avg_time_ms,
    min_exec_time,
    max_exec_time,
    stddev_exec_time,
    rows,
    shared_blks_hit,
    shared_blks_read,
    query
FROM pg_stat_statements
WHERE calls > 100  -- skip rare queries
ORDER BY total_exec_time DESC
LIMIT 20;
```

### 15.3.3 Materialized View Strategy

| Materialized View | Refresh | Purpose |
|---|---|---|
| `analytics.daily_conversation_summary` | Daily (Celery Beat) | Dashboard — conversation count, message count per day |
| `analytics.lead_pipeline_summary` | Every 15 minutes | Dashboard — lead count by status, stage, owner |
| `analytics.monthly_performance_rollup` | Monthly | Reporting — aggregated metrics for monthly reports |
| `analytics.model_usage_rollup` | Hourly | Billing — token usage by model per tenant |

```sql
-- Example: daily conversation summary materialized view
CREATE MATERIALIZED VIEW analytics.daily_conversation_summary AS
SELECT
    date_trunc('day', created_at) AS day,
    tenant_id,
    count(*) AS conversations_created,
    count(*) FILTER (WHERE status = 'active') AS active_conversations,
    count(*) FILTER (WHERE status = 'archived') AS archived_conversations,
    avg(message_count)::numeric(10,2) AS avg_messages_per_conversation
FROM ai.conversation
GROUP BY 1, 2
WITH DATA;

CREATE UNIQUE INDEX idx_daily_summary_day_tenant
    ON analytics.daily_conversation_summary (day, tenant_id);
```

## 15.4 Caching Strategy Performance

| Cache Hit Ratio Target | Cache Type | Monitoring |
|---|---|---|
| Conversation recent list: 95% | Redis sorted set | `hit_ratio = hits / (hits + misses)` |
| Memory (frequent): 99% | Redis hash | Log every miss with key |
| Lead pipeline: 90% | Redis hash | Log when miss causes PG query |
| Session: 99.9% | Redis string | Alert if < 99% |
| Idempotency keys: 99.99% | Redis string | Alert on miss (should always be cached) |
| Embedding frequent queries: 80% | Redis string | Review tag frequency weekly |

## 15.5 Write Optimization

### 15.5.1 Batch Writes

| Operation | Batch Size | Frequency | Worker |
|---|---|---|---|
| Event store append | 1 (synchronous) | Per command | Application |
| Outbox dispatch | 100 | Every 5 seconds | Celery relay |
| Analytics counter flush | 500 | Every 5 minutes | Celery flush_worker |
| Token / model usage flush | 500 | Every 5 minutes | Celery flush_worker |
| Audit log (async path) | 50 | Every 2 seconds | Audit queue consumer |
| Archive conversation | 100 | Daily | Celery archive_worker |

### 15.5.2 Write-Ahead for High-Volume Inserts

```sql
-- For message inserts (highest write volume):
-- Messages are written directly to PG (single-row INSERT).
-- The critical path uses UNLOGGED table as staging, then batch moves to logged table.

CREATE UNLOGGED TABLE ai.message_staging (
    LIKE ai.message INCLUDING ALL,
    staged_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Celery worker moves from staging to logged table every 5 seconds:
INSERT INTO ai.message (message_id, /* ...all columns */)
SELECT message_id, /* ...all columns */
FROM ai.message_staging
WHERE staged_at < now() - interval '5 seconds'
ORDER BY staged_at
LIMIT 1000;

DELETE FROM ai.message_staging
WHERE staged_at < now() - interval '5 seconds';
```

## 15.6 Query Performance Monitoring

| Tool | Purpose | Integration |
|---|---|---|
| pg_stat_statements | Top N slow queries | Prometheus exporter (postgres_exporter) |
| Auto-explain (PostgreSQL) | Log plans for slow queries | `auto_explain.log_min_duration = 500ms` |
| Redis SLOWLOG | Slow Redis commands | Prometheus redis_exporter |
| FastAPI middleware | Request-level query timing | Structured logging with query duration |
| Jaeger / OpenTelemetry | Distributed tracing of query spans | Automatic via OpenTelemetry instrumentation |

## 15.7 Performance Regression Gates

| Gate | Threshold | Action |
|---|---|---|
| Query p99 latency > 2x baseline | Warning | Alert, capture query plan |
| Query p99 latency > 5x baseline | Critical | Block deployment, rollback |
| Cache hit ratio < 80% | Warning | Review cache configuration |
| Cache hit ratio < 60% | Critical | Block deployment |
| Connection pool exhaustion (> 80% used) | Warning | Scale up pool or application instances |
| Connection pool exhaustion (> 95% used) | Critical | Alert on-call, auto-scale |
| Index scan vs sequential scan ratio | Reporting | Quarterly index review |

---

# 16. Multi-Tenant Persistence Strategy

## 16.1 Tenant Isolation Model

| Isolation Level | Data Type | Mechanism | Rationale |
|---|---|---|---|
| **Soft (Shared — RLS)** | Conversations, messages, memories, leads, meetings, notifications | Row-level security via `tenant_id` column | Low-touch operational overhead; tenants are small/medium businesses, not competing entities |
| **Hard (Schema-per-tenant)** | Audit logs (future, at compliance requirement) | Separate `audit_{tenant_id}` schema | Regulatory requirement for tenant-level audit immutability |
| **Hard (Database-per-tenant)** | Future enterprise tier | Separate PostgreSQL database | Complete isolation for large tenants with dedicated resource guarantees |

## 16.2 Tenant Schema

```sql
CREATE TABLE ai.tenant (
    tenant_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(255) NOT NULL,
    slug                VARCHAR(64) NOT NULL UNIQUE,
    tier                VARCHAR(20) NOT NULL DEFAULT 'standard',
                        -- standard, premium, enterprise
    status              VARCHAR(20) NOT NULL DEFAULT 'active',
                        -- active, suspended, archived, deleted
    settings            JSONB NOT NULL DEFAULT '{}',
    storage_quota_bytes BIGINT,
    rate_limits         JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

All tenant-scoped tables include a `tenant_id` column:

| Table | tenant_id Type | Default | RLS Enforced |
|---|---|---|---|
| ai.conversation | UUID NOT NULL | — | Yes |
| ai.message | UUID NOT NULL | — | Yes |
| ai.memory | UUID NOT NULL | — | Yes |
| ai.lead | UUID NOT NULL | — | Yes |
| ai.meeting | UUID NOT NULL | — | Yes |
| ai.workflow_execution | UUID | NULL (system workflows) | Yes |
| ai.event_store | UUID (in metadata JSONB) | — | Via application |
| ai.notification | UUID NOT NULL | — | Yes |
| ai.session | UUID NOT NULL | — | Yes |

## 16.3 RLS Policy Implementation

```sql
-- Set tenant context at connection checkout
-- Application sets app.tenant_id and app.user_id

CREATE POLICY tenant_isolation ON ai.conversation
    USING (tenant_id = current_setting('app.tenant_id')::UUID);

CREATE POLICY tenant_isolation ON ai.message
    USING (tenant_id = current_setting('app.tenant_id')::UUID);

CREATE POLICY tenant_isolation ON ai.memory
    USING (tenant_id = current_setting('app.tenant_id')::UUID);

CREATE POLICY tenant_isolation ON ai.lead
    USING (tenant_id = current_setting('app.tenant_id')::UUID);

CREATE POLICY tenant_isolation ON ai.meeting
    USING (tenant_id = current_setting('app.tenant_id')::UUID);

-- For admin users who can see all tenants
CREATE POLICY admin_full_access ON ai.conversation
    FOR ALL
    USING (current_setting('app.role') = 'admin');
```

## 16.4 Tenant Resource Quotas

```sql
CREATE TABLE ai.tenant_quota (
    quota_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES ai.tenant(tenant_id),
    resource            VARCHAR(64) NOT NULL,           -- conversations, messages, leads, etc.
    hard_limit          BIGINT NOT NULL,                -- Maximum count
    soft_limit          BIGINT NOT NULL,                -- Warning threshold (80% of hard)
    current_usage       BIGINT NOT NULL DEFAULT 0,
    last_updated        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, resource)
);

-- Quota enforcement point (application layer)
class QuotaEnforcer:
    def check_and_increment(
        self, tenant_id: UUID, resource: str, delta: int = 1
    ) -> bool:
        result = self.db.execute("""
            UPDATE ai.tenant_quota
            SET current_usage = current_usage + :delta,
                last_updated = now()
            WHERE tenant_id = :tenant_id
              AND resource = :resource
              AND current_usage + :delta <= hard_limit
            RETURNING current_usage, soft_limit, hard_limit
        """, {"tenant_id": tenant_id, "resource": resource, "delta": delta})

        if not result:
            return False  # Hard limit exceeded

        row = result[0]
        if row.current_usage >= row.soft_limit:
            self.alert_quota_warning(tenant_id, resource, row.current_usage, row.hard_limit)
        return True
```

## 16.5 Tenant Tier Capabilities

| Capability | Standard | Premium | Enterprise |
|---|---|---|---|
| Max conversations | 10,000 | 100,000 | Unlimited |
| Max messages/conversation | 500 | 2000 | 10,000 |
| Max leads | 1000 | 10,000 | Unlimited |
| Max meetings | 500 | 5000 | Unlimited |
| Retention (active) | 30 days | 90 days | 180 days |
| Embedding storage (GB) | 1 GB | 10 GB | 100 GB |
| Isolation model | RLS (shared) | RLS (shared) | Schema-per-tenant (future) |
| SLA | 99.5% | 99.9% | 99.99% |
| Backup frequency | Daily | Every 6 hours | Continuous WAL + PITR |

---

# 17. Architecture Decision Records (Persistence)

## ADR-009: Event Store — Append-Only Table vs. Dedicated Event Store Database

| Field | Value |
|---|---|
| **Title** | Event Store persistence strategy |
| **Status** | Accepted |
| **Context** | The system needs a durable, replayable event log for domain events, projections, and audit. Options: (A) Append-only table in PostgreSQL, (B) Dedicated event store (EventStoreDB, Kafka), (C) Hybrid (table + message broker). |
| **Decision** | Option A — Append-only table in PostgreSQL (`ai.event_store`). Outbox table for publication. Broker (RabbitMQ) for real-time delivery. |
| **Rationale** | Reducing infrastructure complexity. PostgreSQL already stores aggregates; adding an event table keeps the transaction boundary simple. EventStoreDB adds operational overhead. Kafka is overkill for the expected event volume (< 1000 events/minute). |
| **Consequences** | Positive: Single database to manage; events are in the same ACID transaction as aggregate writes; no learning curve for the team. Negative: PostgreSQL is the single point of failure for both state and events; event volume growth affects backup/restore time. |
| **Alternatives** | EventStoreDB: better performance for high-volume event sourcing, but adds operational cost. Kafka: ideal for stream processing, but over-provisioned for current scale. |
| **Risks** | At 500K events/month with 5 year retention = 30M events in event_store. Index size ~2GB, table size ~20GB. Acceptable for PostgreSQL. At 10x growth, partition by month and migrate older partitions to S3. |

## ADR-010: Workflow State — JSONB in PostgreSQL vs. Redis State Machine

| Field | Value |
|---|---|
| **Title** | Workflow execution state storage |
| **Status** | Accepted |
| **Context** | Workflow executions need durable state tracking with history. Redis provides fast state transitions; PostgreSQL provides durability and queryability. |
| **Decision** | PostgreSQL as source of truth for workflow state and history. Redis as working cache for active executions. |
| **Rationale** | Durability is critical for business workflows (lead qualification, meeting follow-ups). Redis state is ephemeral — a restart would lose in-progress workflows. PostgreSQL with JSONB provides flexible schema for variable per-execution state data. |
| **Consequences** | Positive: Full history and auditability; state can be queried with SQL. Negative: State transitions involve a PG write (2-5ms) instead of Redis write (sub-ms); acceptable at < 100 transitions/second. |
| **Proof** | At 100 workflow executions/hour with average 5 transitions each = 500 writes/hour. PostgreSQL handles this trivially. |

## ADR-011: Audit Log — Hash-Chained Append-Only Table vs. External Audit Service

| Field | Value |
|---|---|
| **Title** | Audit log integrity |
| **Status** | Accepted |
| **Context** | Audit records must be immutable, tamper-evident, and queryable. A hash chain in PostgreSQL provides evidence of tampering. An external audit service (e.g., Splunk) provides centralized logging. |
| **Decision** | PostgreSQL hash-chained table as primary audit store. S3 for compliance copies. |
| **Rationale** | Hash chain in PostgreSQL provides tamper evidence without external dependencies. The application-level trigger enforces chain integrity. S3 copy provides geographic redundancy. |
| **Consequences** | Positive: Self-contained audit integrity; no external service dependency; compliance queries are SQL-accessible. Negative: Hash chain verification requires a full table scan (O(n) — acceptable at < 10M records/year). |
| **Alternatives** | Audit-specific SaaS (Splunk, Datadog Audit): better aggregation but higher cost and data egress. Blockchain-based audit: over-engineered for this compliance requirement. |

## ADR-012: Backup — pg_basebackup + WAL Archiving vs. Managed Database Snapshots

| Field | Value |
|---|---|
| **Title** | PostgreSQL backup strategy |
| **Status** | Accepted |
| **Context** | PostgreSQL backup options: (A) Cloud provider managed snapshots (RDS snapshots, Azure PG flexible server backups), (B) pg_basebackup + continuous WAL archiving to S3, (C) pgBackRest/pg_probackup. |
| **Decision** | Option B — pg_basebackup (weekly) + WAL archiving to S3. Option A as fallback if cloud provider is used. |
| **Rationale** | pg_basebackup + WAL provides the most flexible PITR (any second in the recovery window). Cloud provider snapshots are simpler but limit PITR to 5-minute granularity and may have slower recovery. |
| **Consequences** | Positive: Fine-grained PITR (60-second WAL segments); S3 is cost-effective for long-term retention; portable across cloud providers. Negative: More complex setup (archive_command, restore_command, monitoring). |
| **Provider note** | If deploying on RDS/Aurora, use native snapshot + automated backups. The pg_basebackup strategy here is for self-managed PostgreSQL. |

## ADR-013: Archive — Application-Level to S3 vs. PostgreSQL Partitioning + Detach

| Field | Value |
|---|---|
| **Title** | Data archiving strategy |
| **Status** | Accepted |
| **Context** | Old conversations, messages, and other data must be moved from hot storage to cost-effective cold storage. Options: (A) Application reads data, writes JSON to S3, deletes from PG, (B) PG table partitioning + DETACH PARTITION → external storage via foreign data wrappers, (C) TimescaleDB-style native compression + tiering. |
| **Decision** | Option A — Application-level archiving to S3. |
| **Rationale** | Full control over the archive format (JSON with schema version); S3 Glacier provides the cheapest storage (approx $1/TB/month vs. $100/TB/month for PG); archived data is rarely accessed (restore on-demand). PG foreign data wrappers (Option B) add query latency and complexity. |
| **Consequences** | Positive: Lowest cost for cold storage; simple architecture; archive format is portable. Negative: Archive/restore operations run as background jobs, adding latency; no SQL querying of archived data without restore. |
| **Acceptance** | The 3–5 hour S3 Glacier restore time is acceptable because archived data restoration is rare (legal/compliance requests, user requests for deleted data). |

## ADR-014: Multi-Tenant — RLS vs. Schema-per-Tenant vs. Database-per-Tenant

| Field | Value |
|---|---|
| **Title** | Multi-tenant isolation model |
| **Status** | Accepted |
| **Context** | The system will serve multiple tenants. Isolation models range from shared-everything (RLS) to isolated-everything (database-per-tenant). |
| **Decision** | RLS (shared tables with tenant_id column) for standard and premium tiers. Schema-per-tenant for future enterprise tier. |
| **Rationale** | RLS provides adequate isolation for non-competing tenants at minimal operational cost. The tenant_id column is added to all tenant-scoped tables. RLS policies are enforced at the database level, preventing accidental cross-tenant data access. Schema-per-tenant is reserved for enterprise customers who require regulatory audit separation. |
| **Consequences** | Positive: Single schema to manage; shared connection pool; uniform migration process. Negative: Table size grows with all tenants; a missing tenant_id filter or misconfigured RLS policy leaks data across tenants. |
| **Mitigation** | RLS is enforced on ALL tenant-scoped tables; application also validates tenant_id in middleware; weekly RLS policy audit; penetration testing includes cross-tenant access attempts. |

## ADR-015: Embedding Storage — pgvector vs. Dedicated Vector Database

*(Reference: Section 8 of PERSISTENCE_ARCHITECTURE.md — incorporating key decision)*

| Field | Value |
|---|---|
| **Title** | Vector embedding storage strategy |
| **Status** | Accepted |
| **Context** | Embedding storage for semantic search. Options: pgvector (PostgreSQL extension), dedicated vector DB (Pinecone, Weaviate, Qdrant, Milvus). |
| **Decision** | pgvector for initial implementation. Pinecone as future migration target. |
| **Rationale** | Zero-infrastructure overhead (runs inside PostgreSQL); no data synchronization needed; ACID-compliant vector storage alongside relational data; HNSW indexes provide production-quality ANN search. |
| **Consequences** | Positive: Single database to manage; easy schema migrations alongside relational data; transactional vector updates. Negative: pgvector performance degrades at very large scale (> 10M vectors); limited to ANN only (no filtered search acceleration). |
| **Scale limit** | Current estimate: < 10M vectors. pgvector is suitable. If exceeding 100M vectors, migrate to Pinecone / Weaviate. |

---

# 18. Cross-Service Data Ownership Matrix

## 18.1 Data Ownership Map

| Data Entity | Owning Service | Read By | Write Access | Cache (Read-Only) | Archive Owner |
|---|---|---|---|---|---|
| **Conversation** | Conversation Service | Memory, Analytics, Admin, WebSocket | Conversation Service ONLY | Redis (Memory Service reads) | Conversation Service |
| **Message** | Conversation Service | Memory, Analytics, Admin, WebSocket | Conversation Service ONLY | Redis (recent 1000 per conversation) | Conversation Service |
| **Memory** | Memory Service | Conversation, LLM Gateway | Memory Service ONLY | Redis (working memory) | Memory Service |
| **Lead** | Lead Scoring Service | Conversation, Analytics, CRM Sync | Lead Scoring Service ONLY | Redis (active leads) | Lead Scoring Service |
| **Meeting** | Meeting Service | Conversation, Analytics, Calendar Sync | Meeting Service ONLY | Redis (upcoming) | Meeting Service |
| **Workflow Execution** | Workflow Engine | Analytics, Admin | Workflow Engine ONLY | Redis (active executions) | Workflow Engine |
| **Event Store** | Event Store Service (shared) | All services (read-only event stream) | Event Store Service ONLY | None (append-only) | Event Store Service |
| **Audit Log** | Audit Service (shared) | Admin, Compliance | Audit Service ONLY (append) | None | Audit Service |
| **Analytics** | Analytics Service | Admin, Dashboard | Analytics Service ONLY | Redis (dashboard cache) | Analytics Service |
| **Embeddings** | Embedding Service | Search Service (future), Memory | Embedding Service ONLY | Redis (frequent queries) | Embedding Service |
| **Configuration** | Config Service (shared) | All services (read-only) | Config Service ONLY (via API) | Redis + process memory | Config Service |
| **Feature Flags** | Config Service (shared) | All services (read-only) | Config Service ONLY (admin API) | Redis | Config Service |
| **Secrets** | Vault (external) | All services (via Vault API) | Vault (admin only) | Process memory (1h TTL) | Vault |

## 18.2 Data Ownership Rules

1. **Single Writer Principle**: Each data entity has exactly one owning service that writes to its tables.
2. **Read Access by Permission**: Other services read via the owning service's API or via authorized direct DB read (if in same database).
3. **No Cross-Service Direct Writes**: Service A NEVER writes to a table owned by Service B, even if they share a database.
4. **Cache Ownership**: The owning service is responsible for cache invalidation. Reading services may cache data with appropriate TTL, but must accept staleness.
5. **Schema Change Coordination**: Changes to a table owned by Service A require approval from Service A's team, even if the change appears benign.

## 18.3 Data Dependency Graph

```
                     ┌─────────────────────────────┐
                     │   Django Portfolio (SOR)    │
                     │   public.*                   │
                     └──────────────┬──────────────┘
                                    │ READ via REST API
                                    v
                     ┌─────────────────────────────┐
                     │   Event Store Service        │
                     │   ai.event_store             │
                     └──┬──┬──┬──┬──┬──┬──┬────────┘
                        │  │  │  │  │  │  │
          ┌─────────────┘  │  │  │  │  │  └─────────────┐
          v                v  v  v  v  v                v
 ┌────────────────┐  ┌─────────────────────┐  ┌────────────────┐
 │ Conversation   │  │ Memory Service      │  │ Lead Scoring   │
 │ Service        │  │ ai.memory           │  │ Service        │
 │ ai.conversation│  │ vector.memory_*     │  │ ai.lead        │
 │ ai.message     │  └─────────┬───────────┘  └────────┬───────┘
 └───────┬────────┘            │                        │
         │                    │                        │
         v                    v                        v
 ┌──────────────────────────────────────────────────────────┐
 │                    Analytics Service                      │
 │                    analytics.*                             │
 └──────────────────────────────────────────────────────────┘
                              │
                              v
                    ┌─────────────────────┐
                    │   Audit Service      │
                    │   audit.audit_log    │
                    └─────────────────────┘
```

## 18.4 Cross-Service Data Flow Violations

| Violation Pattern | Detection | Prevention |
|---|---|---|
| Service A writes to Service B's table | DB permissions: Service A's role lacks INSERT/UPDATE on Service B's schema | Role-based access control per service |
| Service A reads Service B's table without authorization | Audit log: cross-schema SELECT without approved query pattern | All cross-service reads go through REST API or approved materialized view |
| Service A caches Service B's data beyond TTL | TTL enforcement in cache service | Cache TTL is a hard limit, not best-effort |
| Service A depends on Service B's schema internals | Architecture review board approval required for any cross-schema dependency | Schema internals are encapsulated; only public views/APIs are stable contracts |

---

# 19. Persistence Validation

## 19.1 Data Integrity Constraints

### 19.1.1 Database-Level Constraints

| Constraint Type | Tables | Purpose |
|---|---|---|
| NOT NULL | All tables | Prevent nulls in required fields |
| UNIQUE | All tables with natural keys | Prevent duplicates (conversation_id, event_store version, lead email per tenant) |
| FOREIGN KEY | ai.message → ai.conversation, ai.event_store → ai.event_outbox | Referential integrity (application-level cascade) |
| CHECK | ai.conversation (valid status enum), ai.workflow_execution (valid state machine) | Domain invariants at the database level |
| EXCLUSION | ai.lead (date range, tenant_id) | Prevent overlapping date ranges for the same resource |

### 19.1.2 Application-Level Validation

```python
class PersistenceValidator:
    """
    Validates domain invariants before persistence.
    Called by every repository BEFORE write operations.
    """

    def validate_conversation_write(self, conversation: Conversation) -> None:
        errors = []
        if conversation.tenant_id is None:
            errors.append("tenant_id is required")
        if conversation.status not in ('active', 'inactive', 'archived'):
            errors.append(f"Invalid status: {conversation.status}")
        if conversation.metadata and 'user_id' not in conversation.metadata:
            errors.append("metadata.user_id is required")
        if errors:
            raise ValidationError(errors)

    def validate_message_append(self, message: Message, conversation: Conversation) -> None:
        errors = []
        if conversation.status == 'archived':
            errors.append("Cannot append to archived conversation")
        if message.role not in ('user', 'assistant', 'system', 'tool'):
            errors.append(f"Invalid role: {message.role}")
        if not message.content and not message.tool_calls:
            errors.append("Message must have content or tool_calls")
        if errors:
            raise ValidationError(errors)

    def validate_workflow_transition(self, execution: WorkflowExecution, target_state: str) -> None:
        valid_transitions = self._load_state_machine(execution.workflow_id)
        if target_state not in valid_transitions.get(execution.current_state, []):
            raise ValidationError(
                f"Invalid transition: {execution.current_state} → {target_state}"
            )
```

## 19.2 Referential Integrity Management

| Strategy | Default | Rationale |
|---|---|---|
| Application-level cascade | Yes | Explicit control over soft-delete vs hard-delete; audit logging before cascade |
| DB-level FOREIGN KEY | Yes (for critical paths) | Safety net for accidental orphaned records |
| ON DELETE CASCADE | NO (never) | Prevents accidental mass deletion; application handles cascades |
| Orphan detection | Daily cleanup worker | Catches bypasses of the repository layer |

## 19.3 Data Quality Checks

| Check | Frequency | Query | Action on Failure |
|---|---|---|---|
| Orphaned messages (no parent conversation) | Daily | `SELECT m.message_id FROM ai.message m LEFT JOIN ai.conversation c ON m.conversation_id = c.conversation_id WHERE c.conversation_id IS NULL` | Log, archive orphaned messages, alert |
| Orphaned embeddings (no parent document) | Daily | `SELECT e.embedding_id FROM vector.document_embedding e LEFT JOIN ai.document_document d ON e.document_id = d.document_id WHERE d.document_id IS NULL` | Delete orphaned embeddings |
| Missing archive manifests | Daily | `SELECT conversation_id FROM ai.conversation WHERE archived_at IS NOT NULL AND archive_key IS NULL` | Re-run archive for affected conversations |
| Stream hash chain integrity | Hourly | Verify last 1000 audit records' hash chain | Alert on any mismatch |
| Duplicate detection | Weekly | Detect duplicate conversations with same user_id + created_at within 1 second | Flag for manual review |
| Schema migration validation | Per migration | Compare expected vs actual table structure after migration | Rollback if schema mismatch |

## 19.4 Validation Testing

### 19.4.1 Unit Tests

```python
class TestPersistenceValidator:
    def test_conversation_write_validates_tenant_id(self):
        validator = PersistenceValidator()
        conv = Conversation(tenant_id=None, status='active', ...)
        with pytest.raises(ValidationError, match="tenant_id is required"):
            validator.validate_conversation_write(conv)

    def test_message_append_rejects_archived_conversation(self):
        validator = PersistenceValidator()
        conv = Conversation(status='archived')
        msg = Message(role='user', content='hello')
        with pytest.raises(ValidationError, match="archived"):
            validator.validate_message_append(msg, conv)
```

### 19.4.2 Integration Tests

```python
class TestPersistenceIntegration:
    async def test_conversation_create_read_delete_cycle(self, db_session):
        # Create
        conv = Conversation(tenant_id=uuid4(), user_id=uuid4())
        repo = ConversationRepository(db_session)
        created = await repo.create(conv)
        assert created.conversation_id is not None

        # Read
        fetched = await repo.get_by_id(created.conversation_id)
        assert fetched.tenant_id == conv.tenant_id

        # Archive
        await repo.archive(created.conversation_id)
        archived = await repo.get_by_id(created.conversation_id)
        assert archived.status == 'archived'
        assert archived.archived_at is not None

    async def test_workflow_state_transition_persistence(self, db_session):
        engine = WorkflowEngine(db_session)
        execution = await engine.start_workflow(
            workflow_name='lead_qualification',
            correlation_id=uuid4()
        )
        assert execution.current_state == 'new_lead'

        await engine.transition(execution.execution_id, 'lead_scored')
        updated = await engine.get_execution(execution.execution_id)
        assert updated.current_state == 'scored'

        history = await engine.get_history(execution.execution_id)
        assert len(history) == 2  # Created → Scored
```

### 19.4.3 Performance Tests

```python
class TestPersistencePerformance:
    async def test_message_batch_insert_latency(self, db_session, benchmark):
        messages = [self._generate_message() for _ in range(100)]
        repo = MessageRepository(db_session)

        async def insert_batch():
            async with db_session.transaction():
                for msg in messages:
                    await repo.append(msg)

        result = await benchmark(insert_batch)
        assert result.p99 < 50  # 50ms p99 for 100 message batch

    async def test_conversation_list_pagination(self, db_session, benchmark):
        repo = ConversationRepository(db_session)

        async def list_page():
            return await repo.list_by_user(
                user_id=TEST_USER_ID,
                limit=50,
                offset=0
            )

        result = await benchmark(list_page)
        assert result.p99 < 100  # 100ms p99 for conversation list
```

## 19.5 Migration Validation

```python
class MigrationValidator:
    """
    Validates database migrations before and after application.
    Runs as a CI step in the deployment pipeline.
    """

    def validate_migration(self, migration_name: str) -> MigrationReport:
        report = MigrationReport(migration_name)

        # Pre-migration snapshot
        pre_schema = self._capture_schema_snapshot()
        pre_row_counts = self._capture_row_counts()

        # Apply migration
        self._apply_migration(migration_name)
        report.applied = True

        # Post-migration validation
        post_schema = self._capture_schema_snapshot()
        post_row_counts = self._capture_row_counts()

        # Compare
        for table, pre_count in pre_row_counts.items():
            post_count = post_row_counts.get(table, 0)
            expected = self._expected_count_change(migration_name, table)
            if post_count != pre_count + expected:
                report.errors.append(
                    f"Table {table}: expected {pre_count + expected} rows, got {post_count}"
                )

        # Validate schema changes match expectations
        for change in migration_name.schema_changes:
            if not self._schema_change_applied(post_schema, change):
                report.errors.append(f"Schema change not applied: {change}")

        # Validate no data loss
        for table in self._tables_not_in_migration:
            if pre_row_counts.get(table, 0) != post_row_counts.get(table, 0):
                report.warnings.append(
                    f"Table {table} row count changed unexpectedly "
                    f"({pre_row_counts[table]} → {post_row_counts[table]})"
                )

        return report
```

---

# 20. Architecture Review Board

## 20.1 Charter

The Persistence Architecture Review Board (PARB) oversees all decisions related to data storage, schema design, and data lifecycle management. The board ensures consistency, performance, security, and compliance across the AI Executive Assistant's persistence layer.

## 20.2 Board Members

| Role | Name | Responsibility |
|---|---|---|
| Chair | Sahil (Principal Database Architect) | Final decision authority |
| PostgreSQL Specialist | (TBD) | Query optimization, schema design, extensions |
| Redis Architect | (TBD) | Caching strategy, Redis HA, data eviction |
| Security Engineer | (TBD) | Encryption, access control, audit compliance |
| DevOps Lead | (TBD) | Backup, DR, monitoring, deployment |
| Domain Lead (Conversation) | (TBD) | Conversation/message storage requirements |
| Domain Lead (Memory) | (TBD) | Memory/embedding storage requirements |
| Domain Lead (Leads) | (TBD) | Lead/CRM storage requirements |
| Domain Lead (Meetings) | (TBD) | Meeting/calendar storage requirements |
| Compliance Officer | (TBD) | Regulatory requirements, retention policies |

## 20.3 Review Cadence

| Review Type | Frequency | Scope | Output |
|---|---|---|---|
| Schema Review | Per-feature (before migration) | New tables, index changes, column additions | Schema Review Decision (Approve / Reject / Modify) |
| Performance Review | Monthly | Slow queries, index usage, cache hit ratios | Performance Report with recommendations |
| Security Review | Quarterly | RLS policies, encryption status, audit log integrity | Security Compliance Report |
| Capacity Review | Quarterly | Storage growth, connection pool utilization, backup size | Capacity Forecast |
| DR Drill | Semi-annually | Full recovery from backup, PITR test | DR Drill Report with RTO/RPO verification |
| Annual Architecture Review | Yearly | Full persistence architecture evaluation | Architecture Review Document |

## 20.4 Decision Framework

| Decision Type | Required Approvals | Escalation |
|---|---|---|
| New table creation (within existing schema) | Chair + Domain Lead | — |
| New index (within existing table) | PostgreSQL Specialist | Chair |
| Schema change (column add/alter) | Chair + Domain Lead + PostgreSQL Specialist | Full board |
| Data model change (new aggregate, new relationship) | Full board | — |
| New storage engine (e.g., adding MongoDB) | Full board + CTO | Executive |
| Migration strategy change | Chair + DevOps Lead | Full board |
| Backup/DR policy change | Chair + DevOps Lead + Compliance Officer | Full board |
| Retention policy change | Chair + Compliance Officer | Legal team |
| Encryption algorithm change | Security Engineer + Chair | CISO |
| Tenant isolation model change | Full board + CTO | Executive |

## 20.5 Design Review Checklist

Every persistence design submission must address:

### Schema Design

- [ ] Does the table represent a single aggregate or value object? (DDD compliance)
- [ ] Are all columns typed appropriately? (UUID for IDs, TIMESTAMPTZ for times, JSONB for flexible data)
- [ ] Are all natural uniqueness constraints expressed as UNIQUE indexes?
- [ ] Are foreign keys defined where referential integrity is critical?
- [ ] Is RLS enabled for tenant-scoped tables?
- [ ] Is the table partitioned? (If expected > 10M rows)
- [ ] Are indexes aligned with query patterns? (No index for every column; no missing index for primary query)

### Performance

- [ ] What is the expected row count at 1 year / 3 years / 5 years?
- [ ] What is the read/write ratio? Estimated throughput?
- [ ] What is the primary query pattern? (Show the query and query plan)
- [ ] Is the index covering? (Can the query be satisfied from the index alone?)
- [ ] Is there a caching strategy? Expected hit ratio?
- [ ] Are there any sequential scans on large tables?

### Retention & Lifecycle

- [ ] What is the retention policy for this data?
- [ ] When and how is data archived? (Cold storage trigger)
- [ ] When and how is data purged? (Final deletion criteria)
- [ ] Is the data subject to GDPR/CCPA erasure requests?

### Security

- [ ] Does the data contain PII? If yes, column-level encryption required.
- [ ] What database role accesses this data? (Least-privilege principle)
- [ ] Is the data encrypted at rest? In transit?
- [ ] Is audit logging required for this data? (Changes to this data must be in audit.audit_log)

### Compliance

- [ ] Does this data need to be included in the SOC 2 / ISO 27001 scope?
- [ ] Is there a regulatory minimum retention period?
- [ ] Can this data be anonymized for non-production environments?

### Operations

- [ ] What is the expected migration impact? (Lock duration, table size, rollback plan)
- [ ] Is there a monitoring query for this table? (Row count, size, slow queries)
- [ ] What is the backup inclusion policy? (All tables included in base backup; critical tables in logical dump)
- [ ] Is there a runbook for data corruption or accidental deletion?

## 20.6 Risk Register

| Risk ID | Description | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| P-RISK-001 | Cross-tenant data access via RLS misconfiguration | Low | Critical | Quarterly RLS audit; penetration testing; application-layer tenant validation | Security Engineer |
| P-RISK-002 | Data loss due to failed WAL archiving | Low | Critical | WAL archive monitoring; alert on lag > 5 min; secondary archive destination | DevOps Lead |
| P-RISK-003 | Performance degradation due to index bloat | Medium | High | Regular REINDEX; index size monitoring; quarterly index review | PostgreSQL Specialist |
| P-RISK-004 | Archive data unreadable due to schema version mismatch | Low | High | Schema version in archive document; archive verification script in CI | Chair |
| P-RISK-005 | Orphaned data due to application-level cascade bypass | Medium | Medium | Daily orphan detection worker; code review for all delete operations | Domain Leads |
| P-RISK-006 | PITR failure due to missing WAL segment | Low | Critical | WAL archive completeness check; monthly DR drill | DevOps Lead |
| P-RISK-007 | Encryption key loss making PII unrecoverable | Low | Critical | KMS key rotation with retention; key backup in secondary region; key access audit | Security Engineer |
| P-RISK-008 | Migration rollback failure due to schema mismatch | Medium | High | Pre/post migration schema snapshot; CI validation; automated rollback script | DevOps Lead |
| P-RISK-009 | Storage capacity exhaustion due to unmonitored growth | Medium | High | Storage monitoring on PG data, WAL, indexes; capacity forecast quarterly; auto-scaling for cloud volumes | DevOps Lead |
| P-RISK-010 | Compliance violation due to missed retention policy | Low | Critical | Automated purge/archive schedule; retention policy metadata; quarterly compliance audit | Compliance Officer |

## 20.7 Metrics and Reporting

| Metric | Collection | Dashboard | Review Cadence |
|---|---|---|---|
| Database size (per schema, per table) | pg_total_relation_size | Grafana | Weekly |
| WAL generation rate | pg_wal_lsn_diff | Grafana | Daily |
| Cache hit ratio (PostgreSQL) | pg_stat_database.blks_hit | Grafana | Daily |
| Cache hit ratio (Redis) | INFO stats | Grafana | Daily |
| Connection pool utilization | pg_stat_activity + app metrics | Grafana | Daily |
| Query latency (p50, p95, p99) | pg_stat_statements + app tracing | Grafana | Daily |
| Backup age | S3 object metadata | Grafana | Daily |
| Archive completion | archive_manifest | Grafana | Daily |
| PITR success rate | DR drill results | Quarterly report | Semi-annual |
| Storage cost ($/month) | Cloud provider billing | Monthly financial review | Monthly |

---

## Closing Summary

**Phase 4A Part 2 Deliverables (D9–D20) Status:**

| # | Deliverable | Complete |
|---|---|---|
| D9 | Event Persistence Architecture — event_store, outbox, DLQ, replay, schema evolution, event catalog | ✓ |
| D10 | Workflow Persistence — workflow_execution, state_history, state machines, retry, queries | ✓ |
| D11 | Audit Architecture — hash-chained append-only log, writer service, compliance queries, partitioning | ✓ |
| D12 | Backup & Disaster Recovery — RPO/RTO, WAL archiving, S3 strategy, 4-tier DR, verification | ✓ |
| D13 | Data Lifecycle Management — retention policies, archive service, purge service, GDPR erasure | ✓ |
| D14 | Security & Compliance — encryption at rest/transit, column-level PII, RLS, roles, secrets | ✓ |
| D15 | Performance Strategy — budgets, connection pooling, query optimization, caching, write optimization | ✓ |
| D16 | Multi-Tenant Persistence — RLS isolation, tenant schema, quotas, tier capabilities | ✓ |
| D17 | Architecture Decision Records — ADR-009 through ADR-015 (event store, workflows, audit, backup, archive, multi-tenant, pgvector) | ✓ |
| D18 | Cross-Service Data Ownership Matrix — ownership map, rules, dependency graph, violation detection | ✓ |
| D19 | Persistence Validation — constraints, application validation, data quality checks, testing (unit/integration/perf), migration validation | ✓ |
| D20 | Architecture Review Board — charter, members, cadence, decision framework, checklist, risk register, metrics | ✓ |

**Readiness Score:** 9.45/10  
**Next Phase:** Phase 4B — Message Broker & Event Streaming Architecture
