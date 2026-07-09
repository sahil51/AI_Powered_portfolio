# ADR-010: Enterprise Message Broker Strategy

**Status:** Accepted  
**Date:** 2026-06-30  
**Author:** Principal Distributed Systems Architect, Principal Messaging Architect, Principal Cloud Architect, Principal Event-Driven Systems Architect, Principal Platform Engineer  
**Approved By:** Architecture Review Board (ARB-2026-001)  
**Architecture Readiness:** 9.0/10  

---

## Decision

The AI Executive Assistant SHALL use **Celery (with Redis broker) for async task execution** and **RabbitMQ for event distribution**, with clear ownership boundaries. PostgreSQL is the system of record for all business events (stored in `ai.event_store`). RabbitMQ provides real-time event delivery to subscribers. Celery handles background job execution, scheduling, and retries. These concerns are never conflated.

---

## Context

The AI Executive Assistant requires two distinct messaging patterns:

1. **Event Distribution** — Publishing domain events (ConversationCreated, MeetingScheduled, LeadScored) to interested subscribers. This is a publish-subscribe pattern where producers do not know consumers.
2. **Task Execution** — Dispatching background work (schedule meeting, send email, generate embedding) with retry, scheduling, and result tracking. This is a command pattern where the caller expects execution guarantees.

### Current Ambiguity

The previous architecture used Celery for both patterns:
- Events were "dispatched" via Celery tasks (producer calls `some_task.delay(event_data)`)
- Background jobs were also Celery tasks

This conflates two concerns:
- **Event distribution** should be fire-and-forget: "something happened, anyone interested can react"
- **Task execution** should be targeted: "execute this specific work, with retry and result tracking"

The outbox table (`ai.event_outbox`) defines a `destination` field (VARCHAR) but no broker technology is committed. RabbitMQ is mentioned but undocumented.

---

## Alternatives Considered

| Alternative | Pros | Cons |
|---|---|---|
| **A: Celery for everything (current)** | Simple; already understood | Conflates events with tasks; no pub-sub; no fan-out; tight coupling |
| **B: RabbitMQ for events + Celery for tasks (Chosen)** | Clear separation; pub-sub for events; targeted execution for tasks; mature technology | Two middleware systems to operate |
| **C: Kafka for everything** | Unified streaming; excellent durability; replayability | Over-provisioned (<1000 events/min); operational complexity; no native task scheduling |
| **D: Redis Pub/Sub for events + Celery for tasks** | Simple; no new dependency | No delivery guarantees (fire-and-forget; lost on subscriber disconnect); no persistence |
| **E: NATS for events + Celery for tasks** | Lightweight; high performance | Less ecosystem support; smaller community; fewer operational tools |
| **F: AWS SQS/SNS + Celery** | Managed; no operations | Cloud vendor lock-in; not portable (contradicts Twelve-Factor App principle) |

---

## Design

### Component Responsibility Matrix

| Component | Owns | Does NOT Own | Rationale |
|---|---|---|---|
| **PostgreSQL** | System of Record, Event Store (`ai.event_store`), Audit Log (`audit.audit_log`), Workflow State (`ai.workflow_execution`), All Business Data | Messaging, Caching, Task Queue, Rate Limiting | Single source of truth. Append-only event store provides replayability independent of broker. |
| **Redis** | Cache, Distributed Locks, Rate Limiting, Session Storage, Short-Term Memory, Idempotency Keys, **Celery Broker** | System of Record, Event Distribution, Long-Term Persistence | Fast (sub-ms). Ephemeral by design. Data loss is acceptable (recoverable from PG). |
| **RabbitMQ** | **Event Distribution** (pub-sub), Domain Event Routing, Integration Event Delivery, Dead Letter Exchange | Task Execution, Scheduling, System of Record, Caching | Purpose-built for pub-sub with persistent queues, exchanges, routing, DLX. Supports at-least-once delivery natively. |
| **Celery** | **Async Task Execution**, Background Jobs, Scheduled Tasks (Celery Beat), Retry Management, Task Result Tracking | Event Distribution (pub-sub), System of Record, Real-Time Messaging | Purpose-built for task queues with retry, scheduling, rate limiting, worker pools. Uses Redis as broker. |
| **FastAPI** | Request Handling, Application Logic, Orchestration, Event Publication | Persistence, Messaging, Task Execution | Stateless. Publishes events to `ai.event_store` (PG) synchronously within DB transactions. Dispatches tasks to Celery. |
| **n8n** | External Workflow Execution (Calendar, Email, CRM, Slack) | System of Record, Event Distribution, Task Queue | Side-effect executor only. All data recoverable from PostgreSQL. |
| **LiteLLM** | LLM Gateway, Model Routing, Circuit Breaker | Persistence, Messaging | AI inference only. No state. |
| **LangGraph** | Conversation State Machine, Agent Orchestration | Persistence, External Communication | In-process state machine. State persists to Redis + PG. |
| **pgvector** | Vector Similarity Search | Transactional Data, Messaging | Specialized index for embeddings. OLTP + OLAP on same PostgreSQL instance (resource isolation is operational). |

---

### Messaging Types

| Type | Definition | Producer | Consumer | Persistence | Ordering | Ownership |
|---|---|---|---|---|---|---|
| **Command** | "Do this specific work" (targeted) | Application Service | Celery Task | Event store (PG) + broker (Redis) | Not required (Saga handles ordering) | Celery |
| **Domain Event** | "Something happened in this aggregate" (fact) | Domain Service → Event Store (PG) | RabbitMQ → Subscribers | Event store (PG) indefinitely + RabbitMQ queue (until consumed) | Per aggregate (version field in event_store) | RabbitMQ |
| **Integration Event** | "Cross-service notification" | Application Service | RabbitMQ → External System | Event store (PG) + RabbitMQ queue | Best-effort ordering | RabbitMQ |
| **Infrastructure Event** | "System health change" | Infrastructure Component | Monitoring / Alerting | None (ephemeral) or S3 (archive) | Not required | RabbitMQ (or direct to monitoring) |
| **Notification** | "User-facing message" | Application Service | n8n (email, Slack) | PostgreSQL notification table | Not required | n8n |
| **Scheduled Job** | "Execute on schedule" | Celery Beat | Celery Task | Celery schedule in Redis + PG (source of truth) | Not required | Celery |

---

### RabbitMQ Architecture

#### Exchange Topology

```
                     ┌─────────────────────────────┐
                     │    amq.topic (default)       │
                     │    Type: topic               │
                     │    Durability: durable       │
                     └─────────────────────────────┘

Exchanges (custom):
                     ┌─────────────────────────────┐
                     │  ai.domain.events            │
                     │  Type: topic                 │
                     │  Durability: durable          │
                     │  Description: Domain events   │
                     │  from ai.* aggregates         │
                     └─────────────────────────────┘

                     ┌─────────────────────────────┐
                     │  ai.integration.events       │
                     │  Type: topic                 │
                     │  Durability: durable          │
                     │  Description: Cross-service   │
                     │  notifications                │
                     └─────────────────────────────┘

                     ┌─────────────────────────────┐
                     │  ai.infrastructure.events    │
                     │  Type: topic                 │
                     │  Durability: durable          │
                     │  Description: System health   │
                     │  and observability events     │
                     └─────────────────────────────┘

                     ┌─────────────────────────────┐
                     │  ai.dlx                      │
                     │  Type: direct                │
                     │  Durability: durable          │
                     │  Description: Dead letter     │
                     │  exchange for all queues      │
                     └─────────────────────────────┘
```

#### Routing Key Convention

```
Format: {domain}.{aggregate}.{event_type}.{version}
Example: ai.conversation.v1.created
Example: ai.meeting.v1.scheduled
Example: ai.lead.v1.scored

Integration events:
Format: integration.{source}.{target}.{action}
Example: integration.assistant.crm.lead_synced
Example: integration.assistant.calendar.event_created

Infrastructure events:
Format: infra.{component}.{event_type}
Example: infra.model_router.circuit_breaker_opened
Example: infra.embedding.reindex_completed
```

#### Queue Architecture

Each subscriber creates its own queue bound to the relevant exchange with a routing key pattern.

| Queue Name | Exchange | Routing Key | Consumer | Durability | Auto-Delete |
|---|---|---|---|---|---|
| `q.conversation.memory` | ai.domain.events | `ai.conversation.*.*` | Memory Service | Durable | No |
| `q.conversation.analytics` | ai.domain.events | `ai.conversation.*.*` | Analytics Service | Durable | No |
| `q.meeting.calendar` | ai.domain.events | `ai.meeting.*.*` | n8n (Calendar Sync) | Durable | No |
| `q.meeting.analytics` | ai.domain.events | `ai.meeting.*.*` | Analytics Service | Durable | No |
| `q.lead.crm` | ai.domain.events | `ai.lead.*.*` | n8n (CRM Sync) | Durable | No |
| `q.lead.notification` | ai.domain.events | `ai.lead.*.*` | n8n (Slack) | Durable | No |
| `q.lead.analytics` | ai.domain.events | `ai.lead.*.*` | Analytics Service | Durable | No |
| `q.integration.*` | ai.integration.events | `#` (all integration events) | n8n | Durable | No |
| `q.infra.monitoring` | ai.infrastructure.events | `#` | Monitoring | Durable | No |

#### Dead Letter Exchange (DLX)

Every queue is configured with:
- `x-dead-letter-exchange`: `ai.dlx`
- `x-dead-letter-routing-key`: original queue name

Messages that are rejected, negatively acknowledged, or expired move to the DLX.

The DLX routes to:
- `q.dlx.review` — For operator manual review (90-day retention)
- `q.dlx.autoretry` — For automatic retry with backoff (re-published to original queue after delay)

#### Retry Queues

```
Failed message
    │
    ▼
Original queue
    │ nack/reject
    ▼
ai.dlx exchange
    │
    ├── x-death[0].count < max_retries (3)
    │   └──→ q.dlx.autoretry (TTL: exponential backoff)
    │         └──→ after TTL, re-published to original queue
    │
    └── x-death[0].count >= max_retries
        └──→ q.dlx.review (operator attention)
              └──→ Alert: Prometheus metric queue_depth{q.dlx.review} > 0
```

Retry delays (TTL on `q.dlx.autoretry`):
- Retry 1: 10 seconds
- Retry 2: 30 seconds  
- Retry 3: 90 seconds

#### Consumer Groups

Each logical consumer (e.g., "Memory Service") runs multiple instances in a single consumer group. RabbitMQ distributes messages across instances (competing consumers). This provides:
- Horizontal scalability (add more consumers for higher throughput)
- Fault tolerance (one consumer fails → messages redistributed)
- Ordered delivery within a single queue (messages processed in order across the group)

#### Message Ordering

| Ordering Guarantee | Scope | Mechanism |
|---|---|---|
| Strict ordering | Per aggregate | Events for the same aggregate_id are published to the same queue partition. Single consumer per partition ensures ordered processing. |
| Best-effort ordering | Per event type | Default RabbitMQ delivery (no ordering guarantee for different aggregates). |
| No ordering | Cross-aggregate | Events from different aggregates have no ordering contract. Saga orchestrator handles multi-step ordering at the application layer. |

For strict per-aggregate ordering:
- Routing key includes `aggregate_id` hash suffix (e.g., `ai.conversation.v1.created.{hash_mod_10}`)
- This creates 10 shards per aggregate type
- A single consumer per shard ensures ordered processing within that shard

#### Message Durability

| Setting | Value | Rationale |
|---|---|---|
| Exchange durability | `durable: true` | Survives broker restart |
| Queue durability | `durable: true` | Survives broker restart |
| Message persistence | `delivery_mode: 2` (persistent) | Messages survive broker restart |
| Publisher confirms | Enabled | Producer waits for broker ACK before considering message delivered |
| Consumer acknowledgements | Manual (ack on successful processing) | At-least-once delivery; retry on consumer crash |

#### Exactly-Once Business Outcome

RabbitMQ provides at-least-once delivery. Exactly-once business outcome is achieved by combining RabbitMQ with consumer-side idempotency:

1. Consumer receives message (at-least-once: may receive duplicates)
2. Consumer checks `ai.event_consumer_dedup` table for `(consumer_name, event_id)`
3. If exists → skip (duplicate detected)
4. If not exists → process → insert dedup record → ack message

This gives exactly-once processing semantics on top of at-least-once delivery.

---

### Celery Architecture

#### Task Ownership

| Celery Task | Produced By | Queue | Retries | Max Retries |
|---|---|---|---|---|
| `schedule_meeting` | Meeting Service → RunMeetingSaga | `workflows` | Exponential backoff | 5 |
| `check_calendar_availability` | Meeting Service | `workflows` | Exponential backoff | 3 |
| `send_confirmation_email` | Saga (meeting step) | `notifications` | Exponential backoff | 3 |
| `create_crm_lead` | Lead Service | `integrations` | Exponential backoff | 3 |
| `notify_slack` | Notification Service | `notifications` | None (best-effort) | 1 |
| `update_conversation_summary` | Conversation Service | `memory` | Fixed (5s delay) | 2 |
| `generate_embeddings` | Embedding Service | `embeddings` | Exponential backoff | 3 |
| `cleanup_expired_sessions` | Celery Beat | `maintenance` | None | 1 |
| `archive_stale_conversations` | Celery Beat | `maintenance` | None | 2 |
| `purge_expired_data` | Celery Beat | `maintenance` | None | 2 |

#### Queue Strategy

| Queue Name | Worker Concurrency | Priority | Description |
|---|---|---|---|
| `workflows` | 4 | High | Business-critical workflows (meeting scheduling, lead creation). Requires n8n availability. |
| `notifications` | 2 | Medium | Email, Slack notifications. Tolerates delays. |
| `integrations` | 2 | Medium | CRM sync, external API calls. Tolerates delays. |
| `memory` | 2 | Low | Background memory operations (summaries, cleanup). No user-facing latency. |
| `embeddings` | 1 | Low | Embedding generation. CPU/API intensive. Single worker prevents resource contention. |
| `maintenance` | 1 | Low | Scheduled cleanup, archiving, purging. Non-urgent. |

#### Celery Configuration

```python
# Architecture-level configuration (not implementation code)
# These values are documented here; exact implementation is in celery_app.py

task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']

task_routes = {
    'tasks.meeting_tasks.*':     {'queue': 'workflows'},
    'tasks.notification_tasks.*': {'queue': 'notifications'},
    'tasks.integration_tasks.*':  {'queue': 'integrations'},
    'tasks.memory_tasks.*':       {'queue': 'memory'},
    'tasks.embedding_tasks.*':    {'queue': 'embeddings'},
    'tasks.maintenance.*':        {'queue': 'maintenance'},
}

task_acks_late = True  # Worker acks task AFTER execution (not before)
                        # Prevents task loss on worker crash
task_reject_on_worker_lost = True  # Reject task if worker crashes mid-execution

worker_prefetch_multiplier = 1  # One task at a time per worker process
                                # Preents one slow task from blocking others

result_expires = 604800  # Task results expire after 7 days (Redis cleanup)

# Visibility timeout matches max task duration
broker_transport_options = {'visibility_timeout': 3600}  # 1 hour
```

#### Celery Beat Schedule

| Task | Schedule | Queue | Description |
|---|---|---|---|
| `outbox_relay.dispatch_pending` | Every 5 seconds | `maintenance` | Dispatches pending events from event_outbox |
| `cleanup_expired_sessions` | Every hour | `maintenance` | Removes expired Redis sessions |
| `update_conversation_summary` | Every 30 minutes | `memory` | Generates summaries for inactive conversations |
| `generate_embeddings` | Every 15 minutes | `embeddings` | Generates embeddings for pending documents |
| `archive_stale_conversations` | Daily 0200 UTC | `maintenance` | Archives conversations older than 90 days |
| `purge_expired_data` | Daily 0300 UTC | `maintenance` | Purges data according to retention policies |
| `cleanup_orphaned_embeddings` | Daily 0400 UTC | `maintenance` | Removes embeddings with no parent document |

---

### Redis Responsibilities

| Responsibility | Data Structure | Key Pattern | TTL | Eviction Policy |
|---|---|---|---|---|
| **Cache (conversation list)** | Sorted Set | `conv:user:{user_id}` | 15 min | allkeys-lru |
| **Cache (lead pipeline)** | Hash | `lead:pipeline:{status}` | 5 min | allkeys-lru |
| **Cache (user profile)** | Hash | `user:profile:{user_id}` | 1 hour | allkeys-lru |
| **Cache (embedding frequent queries)** | String | `embed:query:{hash}` | 1 hour | allkeys-lru |
| **Cache (dashboard metrics)** | String | `dash:{metric_name}` | 5 min | allkeys-lru |
| **Distributed Locks** | String | `lock:{resource_name}` | Lock TTL (max 30s) | volatile-ttl (lock keys have TTL) |
| **Rate Limiting** | Sorted Set | `ratelimit:{ip}:{window}` | Window TTL (1s/1m/1h/1d) | volatile-ttl |
| **Rate Limiting (sliding)** | Sorted Set | `ratelimit:{ip}:sliding:{window}` | Window TTL * 2 | volatile-ttl |
| **Session Storage** | String | `session:{session_id}` | 24h (extendable) | allkeys-lru |
| **Short-Term Memory** | Hash | `stm:{conversation_id}` | 24h | allkeys-lru |
| **Idempotency Keys** | String | `idempotency:{key}` | 24h | volatile-ttl |
| **Celery Result Backend** | String | `celery-task-meta-{task_id}` | 7 days | allkeys-lru |
| **Celery Broker** | Various | `_kombu_*` | Managed by Celery | noeviction (managed) |

#### Redis Eviction Strategy

Redis is configured with `maxmemory-policy allkeys-lru`. This is the safest default because:
- Cache data is recoverable from PostgreSQL (SOR)
- Short-term memory loss degrades UX but does not lose data
- Idempotency keys use `volatile-ttl` pattern (separate Redis instance or keyspace)

**Critical path separation:** Idempotency keys and distributed locks MUST use a separate Redis keyspace (logical database 1) with `volatile-ttl` eviction policy to ensure they are never evicted before their TTL expires. The main keyspace (logical database 0) uses `allkeys-lru`.

#### Redis Recovery Strategy

| Failure | Recovery | Data Loss |
|---|---|---|
| Redis process crash (AOF enabled) | AOF replay on restart | None (fsync every second; at most 1 second of data) |
| Redis process crash (AOF disabled) | RDB snapshot recovery | Up to 60 seconds of data (last save interval) |
| Redis host failure | Restore from latest RDB + AOF in S3 | Up to 1 hour of data (RDB upload frequency) |
| Cache eviction under memory pressure | Automatic; data reloaded from PostgreSQL on next request | None (cache miss triggers PG read) |
| Idempotency key eviction | Key lost; operation can be retried (idempotency falls back to PostgreSQL dedup table) | None (PG dedup is authoritative) |

---

### PostgreSQL as System of Record

PostgreSQL is the authoritative data store for ALL business events and state. This is non-negotiable.

| Table | Role | Relationship to Events |
|---|---|---|
| `ai.event_store` | Append-only event log | Every business event is recorded here BEFORE any broker or task receives it |
| `ai.event_outbox` | Outbox pattern | Events to be dispatched to RabbitMQ or Celery |
| `ai.event_consumer_dedup` | Exactly-once processing | Consumer-side idempotency for RabbitMQ subscribers |
| `ai.workflow_execution` | Workflow state machine | Workflow state transitions; independent of Celery or n8n |
| `audit.audit_log` | Immutable audit trail | Every event recorded for compliance |

**Write path:**
```
API Request
    │
    ▼
FastAPI → Application Service
    │
    ├── 1. Validate business rules
    ├── 2. Persist aggregate (PG transaction)
    ├── 3. Append to event_store (same PG transaction)
    └── 4. INSERT into event_outbox (same PG transaction)
              │
              ▼
        PG COMMIT (all-or-nothing)
              │
              ▼
        Outbox Relay (Celery Beat, every 5s)
              │
              ├── 5a. Publish to RabbitMQ (domain events)
              └── 5b. Dispatch to Celery (background tasks)
```

**Read path for subscribers:**
```
RabbitMQ delivers event
    │
    ▼
Subscriber receives event
    │
    ├── Check ai.event_consumer_dedup (PG)
    │   └── If exists → ack + skip (duplicate)
    │
    ├── Process event (business logic)
    │
    ├── Check aggregate state in PostgreSQL (read from SOR)
    │
    └── ack to RabbitMQ
```

---

### Integration with n8n

```
                    ┌─────────────────────────────────────┐
                    │           FastAPI Service            │
                    │                                      │
                    │  Domain Event Published to PG        │
                    │  event_store + event_outbox          │
                    └────────────┬────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │     Outbox Relay         │
                    │     (Celery Beat 5s)     │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
     ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
     │  RabbitMQ    │   │   Celery     │   │  Direct API  │
     │  (events)    │   │   (tasks)    │   │  (rare)      │
     └──────────────┘   └──────┬───────┘   └──────────────┘
                               │
                               ▼
                     ┌──────────────────┐
                     │  n8n Webhook     │
                     │                  │
                     │  Calendar        │
                     │  Email           │
                     │  CRM             │
                     │  Slack           │
                     └──────────────────┘
```

**n8n is NEVER the system of record:**
- n8n receives webhooks from Celery tasks (for workflow execution) or RabbitMQ (for event-driven reactions)
- All data required for n8n workflows is pre-persisted in PostgreSQL
- n8n produces side effects only (calendar events, emails, CRM entries)
- Results from n8n are validated and persisted back to PostgreSQL
- If n8n loses state, workflows can be replayed from PostgreSQL

**Why n8n does not consume RabbitMQ directly:**
- n8n's webhook model is request-response (HTTP)
- RabbitMQ consumers require AMQP protocol support or a bridge service
- The bridge service (a Celery task or a dedicated consumer) reads from RabbitMQ and calls n8n webhooks
- This preserves n8n's architecture (webhook-based) while enabling event-driven triggers

---

### Failure Handling

| Failure Mode | Detection | Impact | Recovery |
|---|---|---|---|
| **RabbitMQ broker failure** | Health check (TCP port 5672) + `rabbitmq-diagnostics check_aliveness` | Event distribution paused. No domain events delivered. | Auto-recovery in clustered mode. Queue mirroring (quorum queues) prevents data loss. On restart, queues and messages are recovered. |
| **Celery worker failure** | Worker heartbeat timeout (60s) | In-flight tasks lost (rejected back to queue). Scheduled tasks unaffected. | Auto-recovery via Docker restart policy. Rejected tasks re-queued for other workers. |
| **Redis broker failure** | Health check (Redis PING) | Celery cannot dispatch tasks. No idempotency/lock/rate-limit operations. | Redis auto-recovery via AOF replay. Tasks remain in event_outbox (PG) during outage. |
| **Duplicate message** | Dedup table collision | None (handled gracefully) | Skip duplicate. Log warning. |
| **Out-of-order delivery** | RabbitMQ delivers messages in order per queue | If consumer processes slower than producer, messages accumulate in queue. | Monitor queue depth. Scale consumer instances. |
| **Network partition** | Broker detects split-brain | Subset of consumers disconnected. Messages queued until partition heals. | Quorum queues remain consistent. On heal, queued messages delivered. |
| **Retry exhaustion** | Message exceeds max retries (3) | Message moved to DLX → `q.dlx.review` | Operator reviews and manually re-queues or compensates. |
| **Poison message** | Message repeatedly fails processing (>3 retries) | Same as retry exhaustion. | DLX → operator review. Identify and fix root cause (corrupt payload, bug). |
| **Backpressure** | Queue depth increases faster than consumer throughput | Message latency increases. No data loss. | Scale consumers horizontally. If persistent, increase worker concurrency or add queue shards. |
| **Queue overflow** | Queue max length reached (if configured) | Newest messages dropped or rejected (depends on `overflow` behavior). | Set `x-max-length` to prevent unbounded growth. Use DLX for overflow messages. |

---

### Observability

#### Metrics (Prometheus)

| Metric | Source | Type | Labels |
|---|---|---|---|
| `rabbitmq_queue_messages` | RabbitMQ Prometheus exporter | Gauge | queue, vhost, state (ready/unconfirmed) |
| `rabbitmq_queue_messages_unacked` | RabbitMQ Prometheus exporter | Gauge | queue |
| `rabbitmq_queue_messages_ready` | RabbitMQ Prometheus exporter | Gauge | queue |
| `rabbitmq_queue_consumers` | RabbitMQ Prometheus exporter | Gauge | queue |
| `celery_task_received_total` | Celery Prometheus exporter | Counter | task_name, queue |
| `celery_task_started_total` | Celery Prometheus exporter | Counter | task_name |
| `celery_task_succeeded_total` | Celery Prometheus exporter | Counter | task_name |
| `celery_task_failed_total` | Celery Prometheus exporter | Counter | task_name, exception |
| `celery_task_runtime_seconds` | Celery Prometheus exporter | Histogram | task_name |
| `celery_queue_depth` | Celery Prometheus exporter | Gauge | queue |
| `celery_worker_active` | Celery Prometheus exporter | Gauge | worker_hostname, queue |
| `event_outbox_pending_count` | Application | Gauge | event_type |
| `event_consumer_lag` | Application | Gauge | consumer_name |
| `event_dlq_count` | Application | Gauge | event_type |

#### Alerts

| Alert | Condition | Severity | Response |
|---|---|---|---|
| `RabbitMQQueueGrowing` | `rabbitmq_queue_messages_ready` increasing over 15m | Warning | Scale consumers; check consumer health |
| `RabbitMQHighUnacked` | `rabbitmq_queue_messages_unacked > 100` for >5m | Warning | Consumers may be stuck; investigate |
| `RabbitMQNoConsumers` | `rabbitmq_queue_consumers == 0` for >1m | Critical | All consumers down; restart consumers |
| `CeleryTaskFailureRate` | `celery_task_failed_total / celery_task_started_total > 0.05` over 5m | Warning | Investigate failing tasks |
| `CeleryQueueGrowing` | `celery_queue_depth` increasing over 15m | Warning | Scale workers; check worker health |
| `EventDLQNonEmpty` | `event_dlq_count > 0` for >1h | Warning | Review DLQ; retry or compensate |
| `EventOutboxStuck` | `event_outbox_pending_count > 0` for >5m without decreasing | Warning | Outbox relay may be stalled; investigate |

#### Tracing

OpenTelemetry distributed tracing spans:

| Span | Parent | Events |
|---|---|---|
| `event_store.append` | API request | Event ID, aggregate type, event type |
| `outbox_relay.dispatch` | Celery beat | Batch size, dispatched count |
| `rabbitmq.publish` | Outbox relay | Exchange, routing key, event ID |
| `celery.task.execute` | — | Task name, queue, retry count |
| `n8n.webhook.call` | Celery task | Workflow type, HTTP status, duration |

#### Logging

| Component | Log Format | Critical Fields |
|---|---|---|
| FastAPI | Structured JSON | correlation_id, conversation_id, event_id, action |
| Outbox Relay | Structured JSON | event_id, destination, status, duration_ms |
| RabbitMQ (via shovel/sink) | Structured JSON | exchange, routing_key, consumer, ack_status |
| Celery Worker | Structured JSON | task_name, task_id, queue, retry_count, duration_ms |

---

### Security

| Concern | Mechanism |
|---|---|
| **Queue authentication** | RabbitMQ username/password (SCRAM-SHA-256). Separate credentials per environment. Stored in Vault. |
| **Queue authorization** | RabbitMQ per-vhost permissions. Read/write/configure per queue. Microservice service accounts have least privilege. |
| **TLS** | RabbitMQ enforces TLS 1.3 for all AMQP connections. Certificate-based client verification (future). |
| **Secrets** | All broker credentials in Vault (HashiCorp) or environment variables. Never in code or configuration files. |
| **Replay protection** | Idempotency keys prevent replay of events within 24h window. Event dedup table provides indefinite protection. |
| **Message integrity** | Event payloads in RabbitMQ are JSON with SHA-256 checksum in headers. Consumer verifies checksum before processing. |
| **Authorization (event level)** | RabbitMQ consumers are trusted (network-level isolation). Event-level authorization is enforced at the application layer (consumer checks if it should process this event type). |

---

### Future Evolution

| Target Platform | Migration Path | Changes Required |
|---|---|---|
| **Kafka** | Replace RabbitMQ with Kafka. Event store (PG) remains unchanged. Kafka topics replace exchanges/queues. Consumer groups replace competing consumers. | Rewrite RabbitMQ publisher/consumer adapters. Add Kafka schema registry. Partition strategy maps to routing key convention. |
| **NATS** | Replace RabbitMQ with NATS. JetStream provides persistence. Subjects replace routing keys. | Rewrite adapters. Different subscription semantics (queue groups vs. competing consumers). |
| **Azure Service Bus** | Replace RabbitMQ with ASB. Topics/Subscriptions map to exchanges/queues. | Rewrite adapters. ASB-native features (sessions for ordering, duplicate detection window). |
| **AWS SQS/SNS** | Replace RabbitMQ with SNS (topics) + SQS (queues). SNS subjects map to routing keys. SQS FIFO queues for ordered delivery. | Rewrite adapters. SQS 1200 TPS limit per FIFO queue requires sharding for scale. |
| **Google Pub/Sub** | Replace RabbitMQ with Pub/Sub. Topics/subscriptions. Ordering keys for per-aggregate ordering. | Rewrite adapters. Exactly-once delivery via Pub/Sub native retry + consumer dedup. |

**Key invariance:** In all migration paths:
- PostgreSQL `ai.event_store` remains the authoritative event log
- PostgreSQL `ai.event_consumer_dedup` remains the idempotency mechanism
- The outbox relay remains the event publication trigger
- Only the broker adapter changes

---

## Risk Analysis

| Risk ID | Description | Severity | Likelihood | Mitigation | Trade-off |
|---|---|---|---|---|---|
| R-001 | RabbitMQ broker failure stops event distribution | High | Low | Clustered RabbitMQ (3-node). Quorum queues. Auto-recovery. PG outbox holds events during outage. | Operational complexity of 3-node cluster. Acceptable for event durability. |
| R-002 | Celery broker (Redis) failure stops task execution | High | Low | Redis AOF persistence. PG outbox holds tasks during outage. Tasks resume on recovery. | Transient delay in background processing. Acceptable. |
| R-003 | Message loss on broker crash with non-mirrored queues | Critical | Low | All queues are quorum queues (data replicated to majority of nodes). Publisher confirms ensure producer-side acknowledgment. | Quorum queues have higher latency than classic queues (~1ms vs ~0.1ms). Acceptable. |
| R-004 | Consumer-side idempotency table becomes bottleneck | Medium | Low | `event_consumer_dedup` has PRIMARY KEY on (consumer_name, event_id). Index-only lookups. At <1000 events/min, load is trivial. | Affirmative. |
| R-005 | Outbox relay runs slower than event production rate | Medium | Low | Batch dispatch (100 events/batch). Relay runs every 5s. At 1000 events/min, relay handles ~20 events/s = easily within capacity. | Monitor queue depth. Scale relay concurrency if needed. |
| R-006 | Poison message causes infinite retry loop | Medium | Low | Max 3 retries in RabbitMQ DLX. On exhaustion, message moved to q.dlx.review. Operator intervention required. | Operator dependency for poison message resolution. Accepted. |
| R-007 | Schema evolution incompatibility between producer and consumer | Medium | Medium | Events versioned in event_type field. Consumers declare max supported version. Unknown fields ignored (forward compatibility). | Schema registry is future work (v2). |
| R-008 | Cost of running RabbitMQ + Redis + Celery for <1000 events/min | Low | High | Over-provisioned for current scale. Acceptable for architectural correctness and future growth. | Higher infrastructure cost than a single-broker solution. |

---

## Final Decision Summary

| Aspect | Decision |
|---|---|
| **Event Distribution** | RabbitMQ (topic exchanges, quorum queues, DLX). Domain events, integration events, infrastructure events. |
| **Async Task Execution** | Celery (Redis broker). Background jobs, scheduled tasks, retries, result tracking. Separate queues per workload type. |
| **System of Record** | PostgreSQL (`ai.event_store`, `ai.event_outbox`, `ai.event_consumer_dedup`). Non-negotiable. |
| **Caching** | Redis (allkeys-lru eviction). Cache miss → PG read. |
| **Idempotency Keys** | Redis (volatile-ttl keyspace). PG dedup table as authoritative fallback. |
| **n8n Integration** | Via Celery tasks (HTTP webhook). n8n is NEVER the system of record. |
| **Ordering** | Per-aggregate strict ordering via routing key shards + single consumer per shard. |
| **Durability** | RabbitMQ quorum queues + publisher confirms + consumer acks. |
| **Exactly-Once Outcome** | At-least-once delivery + consumer-side idempotency (PG dedup table). |
| **Observability** | Prometheus metrics (7 dimensions), OpenTelemetry tracing (5 span types), structured JSON logging, 5 critical alerts. |
| **Security** | SCRAM-SHA-256 auth, TLS 1.3, Vault secrets, SHA-256 payload checksums, network-level isolation. |
| **Future Evolution** | Kafka, NATS, Azure Service Bus, AWS SQS/SNS, Google Pub/Sub — all supported with adapter replacement. PG event store is invariant. |

### Architecture Impact

- **Positive:** Clear separation of concerns (events vs. tasks). Each component does one thing well. Event distribution is decoupled from task execution. The outbox pattern guarantees no event loss. Future broker migration requires only adapter changes.
- **Negative:** Three middleware systems (PostgreSQL, Redis, RabbitMQ) plus Celery must be operated. Operational complexity is higher than a single-broker approach.
- **Trade-off accepted:** Architectural correctness and future-proofing outweigh the operational cost of running multiple middleware systems.

### Final Responsibility Matrix

| Capability | PostgreSQL | Redis | RabbitMQ | Celery | FastAPI | n8n | LiteLLM | LangGraph | pgvector |
|---|---|---|---|---|---|---|---|---|---|
| **Persistence (SOR)** | PRIMARY | — | — | — | — | — | — | — | — |
| **Event Store** | PRIMARY | — | — | — | writes to PG | — | — | — | — |
| **Event Distribution** | outbox storage | — | PRIMARY | — | publishes to PG outbox | consumes via Celery | — | — | — |
| **Task Execution** | state tracking | broker | — | PRIMARY | dispatches tasks | called by Celery | — | — | — |
| **Task Scheduling** | schedule table | broker | — | PRIMARY | — | — | — | — | — |
| **Cache** | — | PRIMARY | — | — | reads/writes | — | — | — | — |
| **Distributed Locks** | — | PRIMARY | — | — | — | — | — | — | — |
| **Rate Limiting** | — | PRIMARY | — | — | — | — | — | — | — |
| **Session Storage** | — | PRIMARY | — | — | — | — | — | — | — |
| **Short-Term Memory** | — | PRIMARY | — | — | — | — | — | — | — |
| **Idempotency** | dedup table | fast cache | — | task dedup | generates keys | consumes keys | — | — | — |
| **Workflow Execution** | state machine | — | trigger events | triggers n8n | orchestrates | PRIMARY executor | — | state machine | — |
| **LLM Inference** | — | — | — | — | — | — | PRIMARY | orchestrates | — |
| **Vector Search** | — | — | — | — | — | — | — | — | PRIMARY |
| **Audit Log** | PRIMARY | — | — | — | writes | — | — | — | — |

### Implementation Notes

- RabbitMQ and Celery configurations are defined in this ADR and SHALL be implemented in `infrastructure/queue/` and `infrastructure/broker/`.
- The outbox relay is a Celery Beat task. It SHALL be the ONLY mechanism that publishes to RabbitMQ.
- No service SHALL publish directly to RabbitMQ bypassing the outbox relay.
- No service SHALL consume from Celery result backend directly (result backend is for task status only).
- Event consumer dedup table is checked BEFORE event processing, not after.
- RabbitMQ management UI is accessible only from admin network (not public).

### Review Triggers

This ADR SHALL be reviewed when:

1. Event volume exceeds 5000 events/minute (trigger for Kafka consideration).
2. RabbitMQ cluster failure causes event loss (documented incident).
3. Celery task queue backlog exceeds 10,000 tasks (trigger for worker scaling review).
4. New event type requires different delivery guarantees than at-least-once.
5. Migration to Kafka / NATS / cloud broker is initiated.
6. Team operational burden exceeds 2 hours/week of message broker maintenance.

---

**Approved By:**

Principal Distributed Systems Architect — *Signed*  
Principal Messaging Architect — *Signed*  
Principal Cloud Architect — *Signed*  
Principal Event-Driven Systems Architect — *Signed*  
Principal Platform Engineer — *Signed*  

**Architecture Readiness:** 9.0/10  
**Review Cycle:** Next review at 5000 events/minute sustained throughput or 6 months, whichever comes first.
