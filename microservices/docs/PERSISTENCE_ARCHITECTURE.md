# Phase 4A — Enterprise Persistence Architecture (Part 1)

**Version:** 1.0  
**Author:** Sahil — Principal Database Architect  
**Status:** Pre-Implementation Persistence Design  
**Review Board:** PostgreSQL Core, Redis Labs, Google, Microsoft, Amazon, OpenAI, Anthropic, NVIDIA principal architects  
**Phase Target:** 9.8/10

---

## Architecture Context

The AI Executive Assistant is an independent FastAPI microservice. The portfolio website is Django-based. Both share one PostgreSQL instance but own separate schemas:

| Schema | Owner | Purpose |
|--------|-------|---------|
| `public` | Django Portfolio | Portfolio, projects, resume, skills, blog, auth, contacts |
| `ai` | AI Microservice | Conversations, messages, memory, meetings, leads, workflows, prompts |
| `analytics` | AI Microservice | Aggregated analytics, rollups, dashboards |
| `audit` | AI Microservice | Immutable audit trail, compliance records |
| `vector` | AI Microservice | pgvector embeddings for semantic search |
| `tenant` (future) | AI Microservice | Multi-tenant isolation layer |

## System of Record vs System of Engagement

| Aspect | Django Portfolio (SOR) | AI Executive Assistant (SOE) |
|--------|----------------------|---------------------------|
| Role | Authoritative data owner | Engagement and enrichment layer |
| Schema | `public` | `ai`, `analytics`, `audit`, `vector` |
| Write Access | Django ORM only | FastAPI repositories only |
| Read Access | Django ORM + AI service (read-only via REST/events) | AI service repositories |
| Communication | REST API (Django views) | REST, events, webhooks |
| Migration Path | Schema-per-service → Database-per-service | Schema-per-service → Database-per-service |

## Cross-Schema Communication Rules

1. AI service reads portfolio data ONLY through approved REST APIs or change-data-capture events
2. AI service NEVER writes to `public` schema directly
3. Portfolio data modifications requested by AI use REST API calls to Django endpoints
4. Cross-schema joins are MINIMIZED — data is cached or synchronized via events
5. The shared database is a DEPLOYMENT OPTIMIZATION, not an architectural coupling

---

## Table of Contents

1. [Enterprise Storage Strategy](#1-enterprise-storage-strategy)
2. [Data Classification Matrix](#2-data-classification-matrix)
3. [Aggregate Persistence Mapping](#3-aggregate-persistence-mapping)
4. [PostgreSQL Persistence Strategy](#4-postgresql-persistence-strategy)
5. [Redis Strategy](#5-redis-strategy)
6. [Conversation Persistence](#6-conversation-persistence)
7. [Memory Persistence](#7-memory-persistence)
8. [pgvector Strategy](#8-pgvector-strategy)

---




# 1. Enterprise Storage Strategy

## 1.1 Data Storage Matrix

| Category | Owner | Storage Engine | Consistency Model | Schema | Retention | Archive | Recovery | Caching |
|---|---|---|---|---|---|---|---|---|
| Portfolio (public schema) | Django Portfolio | PostgreSQL | Strong (ACID) | public (relational) | Indefinite (system of record) | Cold storage after 2 years inactive | PITR + logical backups | Redis (read-only cache, 5 min TTL) |
| Conversation | AI Microservice | PostgreSQL (primary) + Redis (active) + S3 (cold) | Eventual (read-replicas), Strong (primary writes) | ai (normalized) + Redis (JSON) | Active: 90 days; Warm: 1 year; Cold: 7 years | S3 Glacier after 90 days inactivity | PITR + WAL + S3 restore | Redis (active conversations, 24h TTL) |
| Message | AI Microservice | PostgreSQL + Redis (recent) | Strong (write), Eventual (read) | ai.message | Active: 90 days; Cold: 7 years | S3 Glacier after 90d | PITR + WAL + S3 restore | Redis (last 1000 messages per conversation) |
| Conversation Summary | AI Microservice | PostgreSQL + Redis | Eventual | ai.conversation_summary | 90 days TTL (Redis), Indefinite (PG) | S3 Glacier (PG records after 1 year) | PITR + Redis RDB | Redis (hot summaries, 7d TTL) |
| Memory (long-term) | AI Microservice | PostgreSQL (pgvector) + Redis (working) | Strong (pgvector), Eventual (Redis) | ai.memory + vector.memory_embedding | Indefinite (core), 90d TTL (working) | Cold storage for unused memories after 2 years | PITR + vector index rebuild | Redis (working memory, session-scoped) |
| Meeting | AI Microservice | PostgreSQL | Strong (ACID) | ai.meeting | 7 years (compliance) | S3 Glacier after 1 year | PITR + WAL | Redis (upcoming meetings, 1h TTL) |
| Meeting History | AI Microservice | PostgreSQL + S3 (recordings) | Strong | ai.meeting_history | 7 years | S3 Glacier Deep Archive after 2 years | PITR + S3 versioning | Redis (recent meetings, 1h TTL) |
| Lead | AI Microservice | PostgreSQL | Strong (ACID) | ai.lead | Indefinite (active), 3 years (closed) | S3 Glacier after 1 year closed | PITR + WAL | Redis (active leads, 15 min TTL) |
| Workflow Execution | AI Microservice | PostgreSQL + Redis (state machine) | Strong (state transitions) | ai.workflow_execution | 90 days (completed), 1 year (failed) | S3 Glacier after 90 days | PITR + Redis AOF + replay | Redis (active executions, TTL = execution timeout) |
| Prompt Version | AI Microservice | PostgreSQL | Strong (ACID) | ai.prompt_version | Indefinite (audit trail) | S3 Glacier after 2 years | PITR + WAL | None (schema-fetched on load) |
| Embedding (vector) | AI Microservice | PostgreSQL (pgvector) + Pinecone (future) | Eventual (index rebuild tolerance) | vector.embeddings | Tied to source data retention | Model-versioned snapshots to S3 | Full index rebuild from source + S3 snapshots | Redis (frequent query embeddings, 1h TTL) |
| Analytics (aggregated) | AI Microservice | PostgreSQL (materialized views) + ClickHouse (future) | Snapshot isolation (materialized views) | analytics.* | 3 years (raw), 7 years (aggregated) | S3 Glacier after 1 year | Materialized view refresh + WAL | Redis (dashboard cache, 5 min TTL) |
| Audit Log | AI Microservice | PostgreSQL (append-only) + S3 (compliance copies) | Strong (immutable WORM on insert) | audit.audit_log | 7 years (regulatory) | S3 Glacier Deep Archive after 7 years | PITR + S3 versioning + immutable snapshots | None (audit logs bypass cache) |
| Notification | AI Microservice | PostgreSQL + Redis (outbox) | Eventual (outbox pattern) | ai.notification | 90 days | S3 Glacier after 90 days | Replay from outbox + PITR | Redis (pending delivery, TTL = delivery window) |
| Configuration | AI Microservice | Environment variables + Redis (runtime override) + PostgreSQL (canonical) | Eventual (Redis -> env override chain) | ai.configuration | Indefinite (env), active (Redis with TTL) | PITR for PostgreSQL config records | Env restore + Redis snapshot + PG restore | Local process memory (hot reload) |
| Feature Flags | AI Microservice | PostgreSQL (canonical) + Redis (runtime) | Eventual | ai.feature_flag | Indefinite | None (flag state is ephemeral) | PostgreSQL PITR | Redis (flag cache, TTL = flag TTL or 5 min) |
| Secrets | AI Microservice | Vault (HashiCorp) + Environment variables | Strong (Vault) | Vault KV store | Indefinite (rotated per policy) | Vault disaster recovery replica | Vault DR + unseal procedure | None (fetched per request from Vault) |
| Temporary Upload | AI Microservice | Local filesystem / S3 (presigned) | None (ephemeral) | S3 bucket (temp) | 24 hours (auto-cleanup) | None (ephemeral by design) | None (ephemeral) | None |
| Rate Limits | AI Microservice | Redis | Eventual (sliding window) | Redis sorted sets | Window duration (1s / 1m / 1h / 1d sliding) | None | Rebuilt on Redis restart | In-memory (server-level, sub-ms) |
| Distributed Locks | AI Microservice | Redis (Redlock) | Strong (mutual exclusion) | Redis keys | Lock TTL (lease duration) | None | Automatic TTL expiry + lock release handlers | None |
| Sessions | AI Microservice | Redis (primary) + PostgreSQL (cold backup) | Eventual (Redis -> PG async persist) | Redis hash + ai.session | 24 hours (active), 7 days (max session TTL) | PostgreSQL (cold archive after 7 days) | Redis RDB + PG restore; forced re-login after disaster | Hot Redis (every request) |
| Idempotency Keys | AI Microservice | Redis + PostgreSQL (fallback) | Strong (Redis: check-and-set, PG: unique constraint) | Redis key + ai.idempotency_key | 24 hours (idempotency window) | None | Rebuilt from PG after Redis loss | Redis (sub-ms read) |
| Health Status | AI Microservice | In-memory (process) + Redis (cluster view) | Eventual | Redis pub/sub | Ephemeral (heartbeat interval) | None | Health check regeneration | Local process (zero-latency) |
| Metrics | AI Microservice | Prometheus (time-series) + PostgreSQL (long-term) | Eventual | Prometheus TSDB + ai.metrics_history | Prometheus: 15 days; PG: 2 years | S3 Glacier after 2 years | Prometheus snapshot + PG PITR | Prometheus in-memory (recent window) |
| Tracing Metadata | AI Microservice | OpenTelemetry collector + Jaeger + S3 | Eventual | OTLP / Jaeger spans | 7 days (hot), 30 days (warm) | S3 Glacier after 30 days | Replay from S3 trace archives | Jaeger in-memory (recent traces) |
| Model Usage | AI Microservice | PostgreSQL + Redis (counters) | Eventual (Redis counter -> PG batch flush) | ai.model_usage | 2 years (aggregated), 7 years (billing) | S3 Glacier after 2 years | PG PITR + Redis counter replay | Redis (hot counters, 5 min flush) |
| Token Usage | AI Microservice | PostgreSQL + Redis (counters) | Eventual (Redis counter -> PG batch flush) | ai.token_usage | 2 years (aggregated), 7 years (billing) | S3 Glacier after 2 years | PG PITR + Redis counter replay | Redis (hot counters, 5 min flush) |
| Cost Tracking | AI Microservice | PostgreSQL + Redis (counters) | Eventual (Redis counter -> PG batch flush) | ai.cost_tracking | 2 years (aggregated), 7 years (billing) | S3 Glacier after 2 years | PG PITR + Redis counter replay | Redis (hot counters, 5 min flush) |

## 1.2 Critical Category Deep Dives

### 1.2.1 Conversation — Highest-Volume, Multi-Engine, TTL Lifecycle

Conversations are the highest-volume entity in the system, spanning three tiers of storage:

    PostgreSQL (System of Record)
    - Normalized schema in the ai schema with conversation, message, and
      conversation_summary tables.
    - Strong ACID guarantees for message writes to prevent data loss.
    - Partitioned by created_at (monthly) for query performance and
      efficient archive operations.
    - Indexes on conversation_id, user_id, created_at, and status.

    Redis (Active Hot Tier)
    - Active conversations (ongoing user sessions) are loaded as JSON
      documents into Redis keyed by conversation_id.
    - Messages are appended in real-time; the full conversation context
      is available in sub-millisecond reads.
    - TTL: 24 hours since last activity. At expiry, the conversation is
      flushed to PostgreSQL if dirty and evicted.

    S3 Glacier (Cold Archive)
    - Conversations inactive for 90 days are serialized to JSON/Parquet
      and archived to S3 Glacier.
    - Upon user re-engagement, the archived conversation is lazily
      restored — a stub remains in PostgreSQL pointing to the S3 location.
    - Restore takes 1-12 hours (Glacier retrieval time).

    Lifecycle Flow
    Active (Redis, 24h TTL) -> Warm (PostgreSQL, 90d) -> Cold (S3, 7yr) -> Delete
    - A background job (Conversation Archiver) runs daily, moving
      conversations through the lifecycle.
    - Recovery: PostgreSQL PITR for warm data, S3 restore for cold data.
    - Caching: Redis for all active conversations; no application-level
      cache to avoid staleness in real-time exchanges.

### 1.2.2 Embedding — Vector Storage, Model Versioning, Refresh Strategy

Embeddings power semantic search, memory retrieval, and context injection.

    Storage Engine: PostgreSQL pgvector (HNSW index) as primary;
    Pinecone evaluated for future horizontal scaling.
    Schema: vector.embeddings with columns:
    - id (UUID)
    - source_type (conversation, memory, document, etc.)
    - source_id (UUID)
    - model_id (reference to ai.embedding_model)
    - embedding (vector(1536) for text-embedding-3-large)
    - created_at, updated_at

    Model Versioning:
    - Each embedding model version is tracked in ai.embedding_model
      (provider, model_name, version, dimensions, status).
    - Embeddings are tagged with model_id so queries always use
      dimensionally consistent vectors.
    - When a model is deprecated, a migration job re-embeds all records
      for the new model.

    Refresh Strategy:
    - Inline: On conversation/memory save, the embedding is generated
      and stored synchronously (or async via Celery for batch contexts).
    - Periodic: Stale or low-confidence embeddings are re-computed via
      a weekly background job.
    - Full rebuild: On model upgrade, all embeddings are regenerated
      and the HNSW index is rebuilt. This is an offline operation with
      a read-only fallback to the previous index.

    Recovery: pgvector index is rebuilt from the source data (messages,
    memories, documents). S3 snapshots of the index are taken nightly
    for faster recovery. Vector dimensions are immutable per model
    version, ensuring index consistency.

### 1.2.3 Audit Log — Immutable WORM, Compliance, 7-Year Retention

The audit log is a write-once, read-many (WORM) store with strict
immutability guarantees for regulatory compliance (SOC 2, GDPR, HIPAA).

    Storage: PostgreSQL audit.audit_log table, append-only.
    All application-level mutations are captured via SQLAlchemy event
    listeners at the repository layer.
    Immutability:
    - INSERT-only. UPDATE and DELETE are prohibited at the database
      level via triggers and restricted GRANTs.
    - Each row carries a SHA-256 hash of the previous row's hash,
      forming a blockchain-style integrity chain.
    - tamper_detected flag is computed on read by re-verifying the
      hash chain. If a mismatch is found, an alert fires immediately.
    Schema: event_id, event_type, actor_id, target_type, target_id,
    old_values (JSONB), new_values (JSONB), ip_address, user_agent,
    checksum, previous_checksum, created_at.
    Retention: 7 years (regulatory minimum). After 7 years, records
    are moved to S3 Glacier Deep Archive with a WORM bucket policy
    (S3 Object Lock in compliance mode). Deletion requires a legal hold
    override.
    Archive: Monthly partition export to Parquet -> S3 Glacier Deep
    Archive. Partition is DETACHed, not deleted, for 90 days before
    final removal.
    Recovery: PITR to any point within 7 years. For post-7-year data,
    S3 Glacier Deep Archive retrieval (12-48 hours). The hash chain
    is verified post-restore to prove immutability.
    Caching: None. Every audit read MUST go to the database to ensure
    the hash chain validation is current.

### 1.2.4 Sessions — Redis + PostgreSQL Dual-Write, TTL-Based, Security-Critical

Sessions are the security perimeter of the AI Assistant. They must be
fast (every request reads the session) and durable (no data loss on
Redis restart).

    Dual-Write Strategy
    1. Redis (primary):
       - Session data (user_id, roles, scopes, metadata, expiry) stored
         as a Redis Hash with key session:{session_id}.
       - Every API request reads from Redis. If found and valid, the
         request proceeds.
       - TTL: 24 hours sliding (reset on each authenticated request).
         Maximum session lifetime: 7 days (absolute TTL enforced).
    2. PostgreSQL (cold backup):
       - On session creation, the full session payload is written to
         ai.session asynchronously.
       - Session rotations, invalidation, and expiry are also persisted.
       - If Redis is unavailable (cache miss), the session is loaded
         from PostgreSQL and re-populated into Redis. This is a degraded
         mode — latency increases by ~50ms but the system remains
         operational.

    Security Properties
    - Session IDs are cryptographically random (256-bit, os.urandom).
    - Refresh token rotation: each session refresh issues a new
      session ID; the old one is invalidated.
    - Compromised session detection: concurrent sessions from disparate
      geographic regions trigger an alert and forced invalidation.

    Recovery
    - Redis RDB snapshots are taken every 5 minutes. On Redis restart,
      the RDB is loaded. Any sessions created between the last snapshot
      and the crash are recovered from PostgreSQL.
    - In catastrophic Redis loss, sessions are rehydrated from
      PostgreSQL for active (non-expired) sessions.
    - Worst case: forced re-login for all users (last resort).

### 1.2.5 Configuration — Env + Redis Override + Feature Flags, Eventual Consistency

Configuration is managed as a three-layer stack with increasing
precedence:

    Layer 1: Environment Variables (base)
    - DATABASE_URL, REDIS_URL, JWT_SECRET, S3_BUCKET, etc.
    - Loaded at process start and immutable for the process lifetime.
    - Source of truth for infrastructure topology and secrets locations.
    - Graceful restart required to change (deployment cycle).

    Layer 2: PostgreSQL (canonical runtime config)
    - Table: ai.configuration (key, value, value_type, updated_by,
      updated_at, version).
    - Stores ALL runtime configuration parameters with full audit trail.
    - Each change is versioned (ai.configuration_history) for rollback.
    - Polled by a background ConfigWatcher thread every 30 seconds
      (or triggered via Redis pub/sub for instant propagation).

    Layer 3: Redis (hot override)
    - Keys: config:{key} — overrides PG values at runtime with no
      deployment.
    - TTL: optional. A config can have a fixed TTL (temporary override)
      or no TTL (permanent override until deletion).
    - Redis pub/sub channel config:updated notifies all service
      instances of changes.

    Feature Flags
    - Stored similarly (pg: ai.feature_flag, redis: flag:{flag_name}).
    - Flags support percentage-based rollouts, user/tenant targeting,
      and gradual ramp.
    - Flag evaluation checks Redis first (microsecond), falls back to
      PG (millisecond), and caches locally for 30 seconds.

    Consistency Model
    - Eventual consistency is deliberate: configuration changes take
      up to 30 seconds to propagate to all instances.
    - For urgent config changes (kill switch, rate limit adjustment),
      Redis pub/sub forces near-instant propagation (< 1 second).
    - Write ordering: user-facing API writes to PG first, then publishes
      to Redis. This ensures the canonical store is always consistent
      and Redis is the hot cache.

    Recovery
    - Full config is reloaded from PG on process restart.
    - Redis config keys are re-populated from PG on Redis restart
      (ConfigWatcher detects empty Redis and bulk-loads).
    - Feature flag evaluation degrades to PG-only if Redis is
      unavailable.



# 2. Data Classification Matrix

## 2.1 Classification Definitions

| Classification | Definition | Examples |
|---------------|-----------|---------|
| Transactional | CRUD operations requiring real-time consistency | Conversations, Messages, Memory |
| Reference | Lookup data that rarely changes | Portfolio, Prompt Versions |
| Configuration | System settings and feature flags | Configuration, Feature Flags |
| Analytical | Aggregated metrics and reports | Analytics, Metrics, Cost Tracking |
| Operational | System operations | Rate Limits, Distributed Locks, Health |
| Temporary | Ephemeral data with TTL | Temporary Upload, Idempotency Keys |
| Cache | Derived, recomputable data | Conversation Summary |
| Vector | Embedding vectors for similarity search | Embedding |
| Audit | Immutable records for compliance | Audit Log, Meeting History |
| Security | Authentication, authorization, secrets | Sessions |
| Sensitive | PII, personal data | Messages (content), Memory (user facts) |
| Secret | API keys, credentials, tokens | Secrets |

## 2.2 Data Classification Table

| Category | Classification | Confidentiality | Integrity | Availability | Retention | Encryption at Rest | Encryption in Transit | Backup Frequency | RPO | RTO | Recovery Priority |
|----------|---------------|----------------|-----------|-------------|-----------|-------------------|----------------------|-----------------|-----|-----|------------------|
| Portfolio | Reference | Medium | Medium | Medium | Lifetime | AES-256 | TLS 1.3 | Daily | 24h | 4h | Medium |
| Conversation | Transactional | High | High | High | 90d, then summary | AES-256 | TLS 1.3 | Continuous WAL | 5min | 15min | Critical |
| Message | Transactional | High | High | High | 90d, then summary | AES-256 | TLS 1.3 | Continuous WAL | 5min | 15min | Critical |
| Conversation Summary | Cache | Medium | Medium | Medium | Conversation TTL + 30d | AES-256 | TLS 1.3 | Daily | 24h | 4h | Medium |
| Memory | Transactional | High | High | High | Until user deletion | AES-256 | TLS 1.3 | Continuous WAL | 5min | 15min | Critical |
| Meeting | Transactional | High | High | High | 1 year | AES-256 | TLS 1.3 | Daily | 1h | 1h | High |
| Meeting History | Audit | High | Critical | Medium | 7 years | AES-256 | TLS 1.3 | Daily | 24h | 4h | Medium |
| Lead | Transactional | Medium | High | High | 2 years | AES-256 | TLS 1.3 | Daily | 1h | 1h | High |
| Workflow Execution | Operational | Medium | Critical | High | 90 days | AES-256 | TLS 1.3 | Continuous WAL | 5min | 15min | High |
| Prompt Version | Reference | Medium | Critical | Medium | Lifetime | AES-256 | TLS 1.3 | Daily | 24h | 4h | Medium |
| Embedding | Vector | Medium | Medium | High | Until source deletion | AES-256 | TLS 1.3 | Daily | 24h | 2h | Medium |
| Analytics | Analytical | Low | High | Medium | 3 years | AES-256 | TLS 1.3 | Daily | 24h | 8h | Low |
| Audit Log | Audit | High | Critical | Medium | 7 years | AES-256 | TLS 1.3 | Daily | 24h | 4h | Medium |
| Notification | Temporary | Low | Medium | Medium | 30 days | AES-256 | TLS 1.3 | Daily | 24h | 4h | Low |
| Configuration | Configuration | Low | High | High | Lifetime | Column-level | TLS 1.3 | Daily | 24h | 1h | High |
| Feature Flags | Configuration | Low | High | High | Lifetime | N/A (in-memory/Redis) | TLS 1.3 | Daily | 24h | 1h | High |
| Secrets | Secret | Critical | Critical | Critical | Until rotation | Vault AES-256-GCM | TLS 1.3 | Vault replication | 0 | 5min | Critical |
| Temporary Upload | Temporary | Medium | Medium | Low | 24 hours | AES-256 | TLS 1.3 | None | N/A | N/A | Low |
| Rate Limits | Operational | Low | Medium | High | TTL (minutes) | N/A (Redis) | TLS 1.3 | None (Redis AOF) | N/A | N/A | Low |
| Distributed Locks | Operational | Low | Critical | Critical | TTL (seconds) | N/A (Redis) | TLS 1.3 | None | N/A | N/A | Low |
| Sessions | Operational | High | Critical | High | Session lifetime | AES-256 | TLS 1.3 | Daily | 24h | 15min | High |
| Idempotency Keys | Operational | Low | Critical | Medium | 24 hours | AES-256 | TLS 1.3 | None | N/A | N/A | Low |
| Health | Operational | Low | Medium | Low | 7 days | N/A | TLS 1.3 | None | N/A | N/A | Low |
| Metrics | Analytical | Low | Medium | Medium | 90d raw, 3y aggregated | AES-256 | TLS 1.3 | Daily | 24h | 8h | Low |
| Tracing Metadata | Operational | Low | Medium | Low | 30 days | AES-256 | TLS 1.3 | Daily | 24h | 8h | Low |
| Model Usage | Analytical | Medium | Critical | High | 3 years | AES-256 | TLS 1.3 | Daily | 1h | 2h | High |
| Token Usage | Analytical | Medium | Critical | High | 3 years | AES-256 | TLS 1.3 | Daily | 1h | 2h | High |
| Cost Tracking | Analytical | Medium | Critical | High | 7 years | AES-256 | TLS 1.3 | Daily | 1h | 2h | High |

## 2.3 PII Identification and Handling Strategy

### PII Fields by Data Category

| Data Category | PII Fields | PII Classification | Handling Strategy |
|---------------|-----------|-------------------|-------------------|
| Conversation | message.content, user_id, metadata.ip_address | Sensitive | Content redacted in exports; encrypted at rest; masked in analytics |
| Message | content, sender_id, metadata | Sensitive | Full encryption at rest; content redacted from audit logs; masked in UI previews |
| Memory | facts containing names, locations, contacts, preferences | Sensitive | Column-level encryption for personal fields; user-controlled deletion; opt-out export |
| Meeting | title, participants, transcript, notes | Sensitive | Transcripts encrypted with tenant key; participant list redacted in exports; 1-year retention limit |
| Meeting History | meeting_id, participants, timestamps | Sensitive | PII stripped before archival; anonymized for compliance; 7-year immutable retention |
| Lead | name, email, phone, company, notes | Sensitive | Email and phone encrypted at column level; consent flag required; GDPR export supported |
| Sessions | user_id, ip_address, user_agent | Sensitive | Session tokens hashed in DB; IP masked in logs; automatic expiry enforced |
| Portfolio | name, email, contact form submissions | Sensitive | PII stored in Django schema only; AI service never stores portfolio PII locally |

### PII Redaction and Masking Rules

1. **Automatic Redaction**: All message.content fields are scanned at write time by the PII detection pipeline. Matched patterns (email, phone, SSN, credit card) are replaced with placeholder tokens before storage.
2. **Masking for Analytics**: Aggregated analytics never contain raw PII. User identifiers are hashed with a rotating salt before metric ingestion.
3. **Encryption for Compliance**: Columns tagged as `pii_sensitive` use PostgreSQL column-level encryption with AES-256-GCM and a rotation-enabled master key.
4. **Right to Deletion**: The `DELETE /users/{id}/data` endpoint executes a cascading purge across all schemas. Hard delete is used for PII fields; soft delete for referential integrity records.
5. **Export Readiness**: All PII-bearing tables support GDPR Article 20 data portability exports in JSON format within 72 hours of request.

### PII Detection Pipeline

    PII Detection Pipeline:
    ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
    │ Ingress     │────>│ PII Scanner  │────>│ Redaction    │
    │ (REST/WS)   │     │ (presidio)   │     │ Engine       │
    └─────────────┘     └──────────────┘     └──────────────┘
                              │
                              v
                       ┌──────────────┐
                       │ Encrypted    │
                       │ Storage      │
                       └──────────────┘

## 2.4 Secrets Management Approach

### Secret Storage by Environment

| Environment | Secrets Engine | Storage Location | Access Control |
|-------------|---------------|------------------|---------------|
| Local Development | .env file (never committed) | .env (gitignored) | Developer workstation |
| Staging | HashiCorp Vault (transit engine) | Vault cluster | IAM roles + Vault policies |
| Production | HashiCorp Vault (K/V v2 with automatic rotation) | Vault cluster + HSM | Kubernetes service accounts + Vault Agent Sidecar |

### Secret Categories

| Secret Type | Examples | Rotation Policy | Audit Requirement |
|-------------|---------|-----------------|-------------------|
| API Keys | OpenAI, Anthropic, Google AI, SerpAPI | Every 90 days | All access logged to audit schema |
| Database Credentials | PostgreSQL user passwords, Redis AUTH | Every 30 days | Credential checkout/check-in logged |
| Encryption Keys | Master encryption key, column-level KEK | Every 365 days (KEK); data re-encryption on rotation | Key usage logged to CloudTrail + vault audit |
| JWT Secrets | Token signing keys, refresh secrets | Every 90 days | Grace period for overlapping keys |
| OAuth Tokens | Google, Microsoft, Slack integration tokens | On revocation or every 7 days | Token lifecycle events emitted to audit log |

### Rotation Policy

1. **Automated Rotation**: Secrets with a rotation period of 90 days or less are rotated automatically by a cron-based scheduler that calls the Vault API.
2. **Zero-Downtime Rotation**: Each secret has a current and previous version. Applications read using a version-wildcard resolver that prefers the current secret and falls back to the previous version during rotation windows.
3. **Rotation Audit**: Every rotation event is logged with before/after version metadata, timestamp, and initiator identity to the audit_log table.
4. **Emergency Rotate**: A `POST /admin/secrets/rotate/emergency` endpoint triggers immediate rotation of all secrets, invalidates all active sessions, and forces service restart.
5. **Local Development**: Secrets are loaded from `.env` files via Pydantic Settings. The `.env` file is never committed to version control. A `.env.example` template with placeholder values is provided in the repository.

### Vault Architecture (Production)

    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
    │ Application  │────>│ Vault Agent  │────>│ Vault        │
    │ Pod          │     │ Sidecar      │     │ Cluster      │
    └──────────────┘     └──────────────┘     └──────────────┘
                              │                      │
                              v                      v
                       ┌──────────────┐     ┌──────────────┐
                       │ Temp Token   │     │ HSM Key Store│
                       │ (60s TTL)    │     │ (AWS CloudHSM)│
                       └──────────────┘     └──────────────┘

## 2.5 Data Sovereignty Considerations

### Regulatory Compliance Matrix

| Regulation | Scope | Key Requirements | Implementation |
|------------|-------|-----------------|----------------|
| GDPR | EU data subjects | Right to access, rectification, erasure, portability | User data export API; cascading delete; consent management |
| CCPA | California residents | Right to know, delete, opt-out of sale | Data inventory API; deletion endpoint; no data selling (attestation) |
| LGPD | Brazil | Similar to GDPR with consent emphasis | Consent audit trail; data processing register |
| PIPEDA | Canada | Consent, purpose limitation, safeguards | Purpose-tagged data classification; privacy policy enforcement |
| HIPAA (if applicable) | US healthcare | BAA, encryption, audit controls | BA agreement; minimum necessary access; 6-year audit retention |

### Data Residency Controls

1. **Data Localization**: All production data is stored in US East (N. Virginia) with cross-region backup to US West (Oregon). EU customer data may be restricted to EU regions (Frankfurt or Ireland) via tenant-level routing.
2. **Cross-Border Transfer**: Data transfer between regions uses AWS PrivateLink with TLS 1.3 encryption. Standard Contractual Clauses (SCCs) govern EU-to-US transfers.
3. **Data Classification by Geography**: The `tenant` schema includes a `data_residency` column that tags each record with its governing jurisdiction. Backup and restore operations respect these tags.

### Right to Deletion Implementation

The deletion process follows a multi-step protocol for each data category:

| Category | Deletion Type | Cascade Behavior | SLA |
|----------|-------------|-----------------|-----|
| Conversations | Hard delete | All messages, summaries, embeddings | 24 hours |
| Memory | Hard delete | All memory entries for user | 24 hours |
| Meetings | Hard delete | Meeting history, transcripts, recordings | 48 hours |
| Audit Logs | Anonymization (retention period must be honored) | Replace PII fields with NULL | 7 days |
| Analytics | Anonymization (aggregate integrity must be preserved) | Zero out user-contributable values | 7 days |
| Secrets | Immediate revocation + deletion | Rotate all tokens issued to user | 1 hour |
| Sessions | Immediate invalidation | Delete all active sessions | 15 minutes |

### Data Portability (GDPR Article 20)

1. **Export Format**: All user data is exported as a single JSON archive structured by data category. Each category file follows a published JSON Schema.
2. **Export Trigger**: The `GET /users/{id}/export` endpoint generates the archive asynchronously and notifies the user via email when ready.
3. **Export SLA**: Complete export within 72 hours of request. Large datasets (>1GB) are chunked into 100MB parts with a manifest file.
4. **Supported Categories for Export**: Conversations, Messages, Memory, Meetings, Leads, User Configuration, Notification Preferences.

### Data Retention Overrides by Jurisdiction

| Jurisdiction | Conversation Retention | Audit Log Retention | Meeting Retention | Lead Retention |
|-------------|----------------------|-------------------|------------------|---------------|
| Default (US) | 90 days | 7 years | 1 year | 2 years |
| EU (GDPR) | 30 days (unless consent renewed) | 7 years | 6 months | 18 months |
| California (CCPA) | 90 days | 7 years | 1 year | 2 years |
| Brazil (LGPD) | 60 days | 5 years | 6 months | 18 months |




# 3. Aggregate Persistence Mapping

This section defines the complete persistence landscape for each DDD aggregate. Every aggregate is mapped across all storage engines with explicit ownership, caching, read/write models, audit, archive, and recovery strategies.

## 3.1 Aggregate Persistence Table

| Aggregate | Persistence Owner | Primary Storage (PostgreSQL schema+table) | Cache (Redis key pattern) | Read Model | Write Model | Vector Storage | Analytics Storage | Audit Storage | Archive Strategy | Recovery Strategy |
|---|---|---|---|---|---|---|---|---|---|---|
| Conversation | Conversation Aggregate | ai.conversation, ai.conversation_message | conversation:{id}:state, conversation:{id}:recent | analytics.mv_daily_conversation_stats | ai.conversation | vector.embeddings (source_type='conversation') | analytics.daily_conversation_stats | audit.audit_log + ai.conversation_history | Monthly partition detach → S3 Glacier after 90d inactivity | PITR + WAL; S3 Glacier restore for cold; Redis RDB for hot cache |
| Meeting | Meeting Aggregate | ai.meeting, ai.meeting_participant | meeting-lock:{id}, meeting:availability:{date} | analytics.mv_monthly_meeting_metrics | ai.meeting | — | analytics.meeting_stats | audit.audit_log + ai.meeting_history | S3 Glacier after 1 yr; recordings → Glacier Deep Archive | PITR + WAL; S3 versioning for recordings |
| Lead | Lead Aggregate | ai.lead, ai.lead_note | lead:{id}:state | analytics.mv_weekly_lead_funnel | ai.lead | — | analytics.lead_funnel_stats | audit.audit_log + ai.lead_history | S3 Glacier after 1 yr closed | PITR + WAL |
| UserProfile | UserProfile Aggregate | ai.user_profile | user:{id}:profile | analytics.mv_active_users | ai.user_profile | — | analytics.user_stats | audit.audit_log | N/A (indefinite retention) | PITR + WAL |
| KnowledgeDocument | KnowledgeDocument Aggregate | ai.knowledge_document | knowledge:search:{query_hash} | — | ai.knowledge_document | vector.embeddings (source_type='document') | analytics.knowledge_stats | audit.audit_log | S3 Glacier after 1 yr | PITR + vector index rebuild from source |
| WorkflowExecution | WorkflowExecution Aggregate | ai.workflow_execution | wf:exec:{id}:state | analytics.mv_workflow_stats | ai.workflow_execution | — | analytics.workflow_stats | audit.audit_log | S3 Glacier after 90d completed, 1 yr failed | PITR + Redis AOF + replay |
| Notification | Notification Aggregate | ai.notification | notification:{id}:pending | analytics.mv_notification_stats | ai.notification | — | analytics.notification_stats | audit.audit_log | Monthly partition detach → S3 Glacier after 90d | Replay from outbox + PITR |
| PromptVersion | PromptVersion Aggregate | ai.prompt_version | prompt:active:{prompt_id} | — | ai.prompt_version | — | — | audit.audit_log + ai.prompt_version_history | S3 Glacier after 2 yr | PITR + WAL |
| Memory | Memory Aggregate | ai.long_term_memory | memory:{user_id}:context, memory:{user_id}:confirmations | — | ai.long_term_memory | vector.memory_embedding | analytics.memory_usage_stats | audit.audit_log | Cold storage for unused memories after 2 yr | PITR + vector index rebuild from source |
| ConversationSummary | ConversationSummary Aggregate | ai.conversation_summary | summary:{conversation_id} | — | ai.conversation_summary | vector.embeddings (source_type='summary') | — | audit.audit_log | S3 Glacier (PG records after 1 yr) | PITR + Redis RDB; regenerate from messages on loss |
| ModelUsage | ModelUsage Aggregate | ai.model_usage | model:{provider}:status, usage:{user_id}:counter | analytics.mv_daily_model_usage | ai.model_usage | — | analytics.model_usage_stats | audit.audit_log | S3 Glacier after 2 yr | PG PITR + Redis counter replay |

---

## 3.2 Conversation — Lifecycle Deep Dive

Conversation spans the widest storage landscape of any aggregate, touching PostgreSQL, Redis, pgvector, analytics, and audit stores simultaneously.

    Storage Layout:
    ┌─────────────────────────────────────────────────────────────────┐
    │  Primary (PostgreSQL)         ai.conversation (root)            │
    │                               ai.conversation_message (child)   │
    │  Cache (Redis)                conversation:{id}:state (Hash)   │
    │                               conversation:{id}:recent (List)  │
    │  Vector (pgvector)            vector.embeddings                 │
    │  Analytics                    analytics.daily_conversation_stats│
    │  Audit                        audit.audit_log                   │
    │                               ai.conversation_history           │
    └─────────────────────────────────────────────────────────────────┘

    Lifecycle:
    Active (Redis, 24h TTL) → Warm (PostgreSQL, 90d) → Summarized → Archived (S3 Glacier, 7yr) → Cold (Glacier Deep Archive)

    1. Active Phase: Ongoing conversations live in Redis as JSON hashes
       (conversation:{id}:state) with the last 50 messages cached in a
       capped list (conversation:{id}:recent). Every message append extends
       the TTL. AOF persistence ensures no data loss on Redis restart.
    2. Warm Phase: After 24h of inactivity, the conversation is evicted from
       Redis and lives exclusively in PostgreSQL (ai.conversation + monthly
       partitioned ai.conversation_message). The conversation remains fully
       queryable via SQL and is eligible for LLM context retrieval.
    3. Summarized Phase: At 30d of inactivity, a background job generates a
       conversation summary (stored in ai.conversation_summary and cached in
       Redis as summary:{conversation_id}). The full message content becomes
       eligible for archival. Summaries power the conversation history
       feature without requiring full message retrieval.
    4. Archived Phase: At 90d of inactivity, the conversation partition is
       detached from the live table. An archive job serializes messages to
       Parquet and uploads to S3 Glacier. A stub record remains in
       ai.conversation with archive_location pointing to the S3 key.
    5. Cold Phase: After 7 years, data moves from S3 Glacier to S3 Glacier
       Deep Archive for cost optimization. Retrieval takes 12-48 hours.

    Recovery Path:
    - Hot (Redis loss): Rehydrate from PostgreSQL; last 50 messages
      reconstructed via query with LIMIT 50.
    - Warm (PostgreSQL corruption): PITR to any point within 90d using
      continuous WAL archiving. RPO: 5 minutes.
    - Cold (S3 corruption): S3 versioning enables point-in-time restore.
      Glacier retrieval initiates within 1-12 hours.

## 3.3 Memory — Confirmation Workflow and Staging

Memory is a first-class aggregate responsible for long-term user context, preference learning, and personalization. It implements a confirmation workflow to ensure only user-validated facts influence LLM behavior.

    Storage Layout:
    ┌─────────────────────────────────────────────────────────────────┐
    │  Primary (PostgreSQL)         ai.long_term_memory               │
    │  Cache (Redis)                memory:{user_id}:context         │
    │                               memory:{user_id}:confirmations   │
    │  Vector (pgvector)            vector.memory_embedding           │
    │  Analytics                    analytics.memory_usage_stats      │
    │  Audit                        audit.audit_log                   │
    └─────────────────────────────────────────────────────────────────┘

    Confirmation Workflow (Staging):
    Memory entries pass through a three-stage pipeline before becoming
    active context for LLM interactions.

    Stage 1 — Proposed (Unconfirmed):
    An AI-inferred fact (e.g., "user prefers concise responses") is
    written to ai.long_term_memory with status='proposed'. A pending
    confirmation record appears in Redis at
    memory:{user_id}:confirmations (a Set of memory entry IDs). The
    fact is NOT included in the LLM context prompt.

    Stage 2 — Confirmed (User-Approved):
    The user accepts the proposed memory via UI or API. The status
    transitions to 'confirmed'. The entry is added to the active
    memory context in Redis at memory:{user_id}:context (a JSON
    serialized array of active memory entries). A confirmation event
    is emitted to the audit log. The embedding is generated and stored
    in vector.memory_embedding for semantic retrieval.

    Stage 3 — Active (Context-Ready):
    Confirmed memories are included in the LLM context prompt on every
    interaction. Periodic re-embedding ensures consistency. If a user
    rejects a proposed memory, it transitions to status='rejected' and
    is excluded from future proposals. Rejected memories are archived
    after 90 days.

    Redis Cache Invariants:
    - memory:{user_id}:confirmations TTL: 7 days. If the user does not
      respond within 7 days, proposed memories auto-reject.
    - memory:{user_id}:context TTL: 2 hours, extended on each user
      interaction. On cache miss, the context is rebuilt from
      ai.long_term_memory WHERE status='confirmed'.

    Recovery:
    - Cache loss: Rebuild memory:{user_id}:context from PostgreSQL by
      querying confirmed entries. Rebuild memory:{user_id}:confirmations
      from proposed entries with created_at within the last 7 days.
    - PostgreSQL loss: PITR. The vector index is rebuilt from
      ai.long_term_memory entries by regenerating embeddings via the
      embedding API.
    - Analytics rebuild: analytics.memory_usage_stats is refreshed from
      the memory table via the nightly materialized view refresh.

## 3.4 Meeting — Webhook Integration and Availability

Meeting scheduling spans PostgreSQL, Redis, analytics, and integrates with external calendar providers via n8n webhooks for bi-directional sync.

    Storage Layout:
    ┌─────────────────────────────────────────────────────────────────┐
    │  Primary (PostgreSQL)         ai.meeting (root)                 │
    │                               ai.meeting_participant (child)    │
    │  Cache (Redis)                meeting-lock:{id} (distributed    │
    │                                 lock for double-booking prev.) │
    │                               meeting:availability:{date}      │
    │                                 (Sorted Set of time slots)     │
    │  Analytics                    analytics.meeting_stats           │
    │  Audit                        audit.audit_log                   │
    │                               ai.meeting_history                │
    │  External                     n8n webhook (calendar sync)       │
    └─────────────────────────────────────────────────────────────────┘

    n8n Webhook Integration:
    Meeting lifecycle events (created, rescheduled, cancelled) emit
    webhook payloads to n8n, which handles bi-directional calendar sync
    with Google Calendar, Microsoft Outlook, and Calendly.

    Flow:
    1. Meeting is created via the AI Assistant API.
    2. A domain event MeetingCreated is raised.
    3. The webhook publisher serializes the event and POSTs to the n8n
       webhook endpoint.
    4. n8n transforms the payload into calendar-specific API calls
       (Google Calendar API, Microsoft Graph API).
    5. n8n responds with the external calendar event ID, which is
       stored in ai.meeting.external_event_id.
    6. On incoming calendar events (e.g., Calendly booking), n8n POSTs
       back to the AI Assistant's webhook receiver, which creates or
       updates the meeting record.

    Distributed Locking (Double-Booking Prevention):
    - meeting-lock:{id}: A Redlock distributed lock acquired before
      creating or modifying a meeting. TTL: 10 seconds. Prevents
      concurrent booking of the same time slot.
    - meeting:availability:{date}: A Redis Sorted Set where members are
      time slots (HH:MM) and scores are Unix timestamps. Locked slots
      have a TTL of 60 seconds (safety margin for booking completion).
      If the booking transaction fails, the lock auto-releases.

    Availability Cache:
    - meeting:availability:{date} is populated by querying
      ai.meeting for the given date and computing free slots based
      on existing bookings and the user's configured availability
      windows.
    - TTL: 1 hour. Extended on each availability query.
    - On cache miss, the availability is recomputed from PostgreSQL
      and re-cached.

    Recovery:
    - Cache loss: meeting:availability:{date} is recomputed from
      ai.meeting. Meeting locks are ephemeral and auto-release.
    - PostgreSQL loss: PITR. External calendar events can be re-synced
      from calendar providers via n8n webhook replay.
    - n8n failure: Webhook delivery uses an outbox pattern — failed
      deliveries are retried with exponential backoff (max 3 retries).
      After max retries, the event is logged to a dead-letter queue
      for manual intervention.




# 4. PostgreSQL Persistence Strategy

---

## 4.1 Schema Organization

The PostgreSQL instance is shared between the Django Portfolio (public schema) and the AI Executive
Assistant (ai, analytics, audit, vector, tenant schemas). Each schema has a single owning service.

    ┌──────────────────────────────────────────────────────┐
    │              PostgreSQL Instance                     │
    │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐  │
    │  │ public   │ │ ai       │ │analytics │ │audit │  │
    │  │(Django)  │ │(FastAPI) │ │(FastAPI) │ │(FAPI)│  │
    │  └──────────┘ └──────────┘ └──────────┘ └──────┘  │
    │  ┌──────────┐ ┌──────────┐                          │
    │  │ vector   │ │ tenant   │                          │
    │  │(FastAPI) │ │ (future) │                          │
    │  └──────────┘ └──────────┘                          │
    └──────────────────────────────────────────────────────┘

    Legend:
    ┌──────────────┐
    │ Solid border │ = schema owned by a single service
    └──────────────┘
    Dotted future schemas are planned but not implemented.

Rationale:

- Schema-per-service is chosen over database-per-service at this stage because both services are
  small enough to share a single instance, reducing operational overhead (backups, monitoring,
  connection management) while maintaining logical isolation.
- The shared database is a DEPLOYMENT OPTIMIZATION, not an architectural coupling. When either
  service grows to require independent scaling, migrating a schema to its own database requires
  zero application code changes because repositories abstract storage behind an interface.
- Cross-schema access is strictly controlled: the AI service reads public data through REST APIs
  or event streams, never through direct SQL joins. This prevents coupling and keeps the migration
  path clean.

---

## 4.2 Naming Convention

All database objects follow a strict naming convention for consistency and self-documentation.

    ┌─────────────────────┬─────────────────────────────────────┐
    │ Element             │ Convention                          │
    ├─────────────────────┼─────────────────────────────────────┤
    │ Tables              │ snake_case, singular, schema-prefix │
    │                     │ e.g. ai.conversation                │
    │                     │ e.g. ai.conversation_message        │
    ├─────────────────────┼─────────────────────────────────────┤
    │ Columns             │ snake_case                          │
    │                     │ e.g. created_at, is_active          │
    ├─────────────────────┼─────────────────────────────────────┤
    │ Primary keys        │ UUID v4, column named {table}_id    │
    │                     │ e.g. conversation_id                │
    ├─────────────────────┼─────────────────────────────────────┤
    │ Foreign keys        │ {referenced_table}_id               │
    │                     │ e.g. conversation_id in message     │
    ├─────────────────────┼─────────────────────────────────────┤
    │ Indexes             │ ix_{table}_{column}                 │
    │                     │ e.g. ix_conversation_created_at     │
    ├─────────────────────┼─────────────────────────────────────┤
    │ Unique constraints  │ uq_{table}_{columns}                │
    │                     │ e.g. uq_user_email                  │
    └─────────────────────┴─────────────────────────────────────┘

Example:

    CREATE TABLE ai.conversation (
        conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        title TEXT NOT NULL,
        user_id UUID NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        version BIGINT DEFAULT 1,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        deleted_at TIMESTAMPTZ
    );

    CREATE INDEX ix_conversation_created_at
        ON ai.conversation (created_at);

    CREATE UNIQUE INDEX uq_conversation_external_id
        ON ai.conversation (external_id)
        WHERE external_id IS NOT NULL;

Rationale:

- Singular table names match the domain entity name (conversation, not conversations) and make SQL
  read naturally (SELECT * FROM ai.conversation).
- Snake_case is the idiomatic PostgreSQL convention and avoids quoting issues.
- UUID v4 primary keys avoid sequential ID guessing, enable offline generation, and simplify
  distributed/sharded deployments.
- Explicit {table}_id PK naming avoids ambiguity in joins and foreign keys.
- Prefix conventions (ix_, uq_) make object types identifiable at a glance in pg_catalog.

---

## 4.3 Versioning Strategy

Three complementary mechanisms handle different versioning concerns:

    ┌──────────────────────┬──────────────────┬─────────────────────┐
    │ Concern              │ Mechanism        │ Location            │
    ├──────────────────────┼──────────────────┼─────────────────────┤
    │ Optimistic locking   │ version integer  │ Application layer   │
    │                      │ (incremented)    │ (repository.save()) │
    ├──────────────────────┼──────────────────┼─────────────────────┤
    │ Event-sourced change │ Domain events    │ Application layer   │
    │ tracking             │ (outbox table)   │ (command handlers)  │
    ├──────────────────────┼──────────────────┼─────────────────────┤
    │ Temporal/audit       │ History tables   │ Application layer   │
    │ records              │ ({table}_history)│ (domain events)     │
    └──────────────────────┴──────────────────┴─────────────────────┘

Rationale:

- Optimistic concurrency via version column is the standard pattern for aggregate-based systems.
  It is simple, performant, and works well with MVCC.
- No pessimistic locks (SELECT ... FOR UPDATE) are used in PostgreSQL. Pessimistic locking is
  delegated to Redis (distributed locks) because PostgreSQL row locks do not scale across
  services and would create a single-instance bottleneck.
- DB triggers are explicitly avoided for change tracking. Domain events generated by the
  application layer provide a richer semantic model (what changed, why, by whom) and are
  essential for event-driven communication with other services.
- History tables (not temporal table extensions) are used for audit-critical entities because
  they give explicit control over what is captured and make querying historical state simple.

---

## 4.4 Soft Delete Strategy

    ┌────────────────────────────┬──────────────────────────────┐
    │ User-facing data           │ Transient data               │
    │ (soft delete)              │ (hard delete)                │
    ├────────────────────────────┼──────────────────────────────┤
    │ conversations              │ temporary uploads            │
    │ meetings                   │ expired sessions             │
    │ leads                      │ cache entries                │
    │ contacts                   │ event logs (after TTL)       │
    │ user accounts              │ processing tokens            │
    └────────────────────────────┴──────────────────────────────┘

Soft delete implementation:

    ALTER TABLE ai.conversation ADD COLUMN deleted_at TIMESTAMPTZ;
    ALTER TABLE ai.conversation ADD COLUMN deleted_by UUID;

    -- Repository filter applied to all read queries:
    SELECT * FROM ai.conversation
    WHERE deleted_at IS NULL;

Model classes include an is_deleted property:

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

Rationale:

- Soft delete is reserved for user-facing data where accidental deletion must be reversible.
  A recovery window (30 days by default) allows administrators to restore deleted records.
- Hard delete for transient data avoids table bloat and keeps the WHERE deleted_at IS NULL
  filter performant. Temporary uploads and expired sessions have zero business value after
  their TTL and should be removed entirely.
- The deleted_by column (UUID of the user who performed the delete) provides audit trail
  without requiring a join to a separate audit table for basic queries.
- The deleted_at IS NULL pattern is enforced at the repository level, not via views, because
  repositories are the single point of data access and the filter is trivial.

---

## 4.5 Optimistic Locking

Every aggregate table includes a version column used for optimistic concurrency control.

    ┌─────────────────────────────────────────────────────────┐
    │  Aggregate Root Table                                   │
    │  ┌──────────────────────────────────────────────────┐  │
    │  │ id           UUID PRIMARY KEY                   │  │
    │  │ ...          (business columns)                 │  │
    │  │ version      BIGINT DEFAULT 1                   │  │
    │  │ created_at   TIMESTAMPTZ                        │  │
    │  │ updated_at   TIMESTAMPTZ                        │  │
    │  └──────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘

Save flow:

    def save(aggregate: Aggregate) -> None:
        result = db.execute("""
            UPDATE ai.conversation
            SET title = :title,
                status = :status,
                version = version + 1,
                updated_at = now()
            WHERE conversation_id = :id
              AND version = :current_version
        """, {
            "id": aggregate.id,
            "current_version": aggregate.version,
            "title": aggregate.title,
            "status": aggregate.status,
        })
        if result.rowcount == 0:
            raise ConcurrentModificationError(
                f"Aggregate {aggregate.id} was modified by another transaction"
            )
        aggregate.version += 1

Recovery:

    try:
        repository.save(aggregate)
    except ConcurrentModificationError:
        aggregate = repository.load(aggregate.id)  # re-read latest state
        # Re-apply command logic on fresh aggregate
        aggregate.apply(command)
        repository.save(aggregate)

Rationale:

- Version-based optimistic locking avoids database-level locks entirely, aligning with the
  stateless, horizontally-scaled nature of the FastAPI service.
- BIGINT is chosen to avoid any risk of overflow even under high write volumes.
- The rowcount check is atomic because UPDATE with the version WHERE clause is executed as a
  single statement under MVCC. No race condition is possible.
- The client retry pattern (re-read, re-apply, re-save) keeps the conflict resolution logic
  in the application where it can be tailored to the specific aggregate.

---

## 4.6 Concurrency Model

PostgreSQL handles row-level concurrency through its MVCC (Multiversion Concurrency Control)
implementation. Each transaction sees a snapshot of data as of the start of the transaction.

    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │ Command     │     │ Repository  │     │ PostgreSQL  │
    │ Handler     │────▶│ save()      │────▶│ UPDATE ...  │
    │             │     │             │     │ WHERE id=:id│
    │ 1. Open TX  │     │ 1. Check    │     │ AND ver=:v  │
    │ 2. Execute  │     │    version  │     │             │
    │ 3. Save     │     │ 2. Execute  │     │ MVCC snap   │
    │ 4. Close TX │     │    UPDATE   │     │ prevents    │
    └─────────────┘     └─────────────┘     │ phantom rds │
                                             └─────────────┘

Key rules:

1. Aggregates are the consistency boundary. No transaction spans multiple aggregates.
2. Each command handler opens exactly one database transaction per aggregate operation.
3. Saga compensations operate in separate transactions. If a saga step fails, the
   compensation logic runs in its own transaction to undo the previous step.

Rationale:

- MVCC eliminates reader-writer blocking: reads never wait for writes, writes never block
  reads. This is critical for a conversational AI system where long-running chat sessions
  must not block analytics queries.
- The aggregate-as-consistency-boundary rule prevents distributed transaction problems
  (two-phase commit, coordinator failure) and keeps the system scalable.
- Saga compensations in separate transactions implement the Saga pattern correctly: each
  step is an independent transaction with its own compensation, avoiding long-lived
  transactions and distributed locks.

---

## 4.7 Foreign Keys and Referential Integrity

    ┌─────────────────────────────────────────────────────────┐
    │ Within-Schema FKs: ENFORCED                             │
    │                                                         │
    │  ai.conversation  ◄── ai.conversation_message          │
    │       │                  (FK enforced)                  │
    │       │                                                 │
    │  ai.lead  ◄── ai.lead_note                             │
    │             (FK enforced)                               │
    ├─────────────────────────────────────────────────────────┤
    │ Cross-Schema FKs: AVOIDED                               │
    │                                                         │
    │  ai.conversation ──??── public.auth_user  ✗ NOT OK     │
    │                                                         │
    │  Instead: application-level integrity check via API     │
    │  AI service calls Django REST API to verify user exists │
    └─────────────────────────────────────────────────────────┘

Rationale:

- Foreign keys within the same schema are enforced at the database level because they provide
  guaranteed referential integrity with zero application code. The cost is negligible for
  tables in the same schema.
- Cross-schema foreign keys are deliberately avoided. A cross-schema FK would couple the AI
  schema to the public schema, making the future database-per-service migration impossible
  (PostgreSQL does not support foreign keys across databases).
- Instead, cross-schema referential integrity is enforced at the application layer. The AI
  service validates foreign references (e.g., user_id exists) by calling the Django REST API.
  This is marginally slower but keeps the schemas independent and the migration path clean.

---

## 4.8 Historical Records

For audit-critical entities, a separate history table records every change.

    ┌─────────────────────────────────────┐
    │ ai.conversation                      │
    ├─────────────────────────────────────┤
    │ conversation_id  UUID               │
    │ title            TEXT               │
    │ version          BIGINT             │
    └─────────────────────────────────────┘
                     │
                     │  domain event on every change
                     ▼
    ┌─────────────────────────────────────────────┐
    │ ai.conversation_history                      │
    ├─────────────────────────────────────────────┤
    │ history_id        UUID PRIMARY KEY          │
    │ conversation_id   UUID (FK to conversation) │
    │ title             TEXT                      │
    │ version           BIGINT                    │
    │ valid_from        TIMESTAMPTZ               │
    │ valid_to          TIMESTAMPTZ               │
    │ changed_by        UUID                      │
    │ change_type       TEXT -- 'created',        │
    │                   │       'updated',        │
    │                   │       'deleted'         │
    └─────────────────────────────────────────────┘

History is populated by the application layer:

    class ConversationHistory:
        """Written by domain event handler, not DB trigger."""

        @staticmethod
        def record_change(
            conversation: Conversation,
            change_type: str,
            changed_by: UUID,
        ) -> None:
            db.execute("""
                INSERT INTO ai.conversation_history (
                    conversation_id, title, version,
                    valid_from, valid_to, changed_by, change_type
                ) VALUES (
                    :id, :title, :version,
                    :valid_from, :valid_to, :changed_by, :change_type
                )
            """, {
                "id": conversation.id,
                "title": conversation.title,
                "version": conversation.version,
                "valid_from": conversation.updated_at,
                "valid_to": "9999-12-31 23:59:59 UTC",
                "changed_by": changed_by,
                "change_type": change_type,
            })

Entities that require history tables:

    ai.conversation
    ai.conversation_message
    ai.meeting
    ai.lead
    ai.workflow_definition

Rationale:

- History tables are simpler, more portable, and more queryable than PostgreSQL's built-in
  temporal table extensions. A simple query (WHERE :point_in_time BETWEEN valid_from AND
  valid_to) returns the state as of any point in time.
- Populating history from the application layer (domain events) keeps all business logic in
  the application where it is testable, version-controlled, and language-native. DB triggers
  are opaque, hard to test, and difficult to include in deployment pipelines.
- The valid_from / valid_to columns implement a type-2 slowly changing dimension pattern,
  standard for audit and compliance requirements.

---

## 4.9 Read Models vs Write Models

CQRS separation is enforced at the schema level.

    ┌──────────────────────────────────────────────────────────┐
    │                        Command Path                      │
    │  ┌──────────┐    ┌──────────┐    ┌──────────────────┐   │
    │  │ Command  │───▶│Aggregate │───▶│ ai.conversation  │   │
    │  │ Handler  │    │   Root   │    │ (write model)    │   │
    │  └──────────┘    └──────────┘    └──────────────────┘   │
    │                                                          │
    │                        Query Path                        │
    │  ┌──────────┐    ┌──────────────────┐                   │
    │  │ Query    │───▶│ analytics schema │                   │
    │  │ Handler  │    │ (read models)    │                   │
    │  └──────────┘    │ or Redis cache   │                   │
    │                  └──────────────────┘                   │
    │                                                          │
    │                        Event Flow                        │
    │  Write model ──domain event──▶ Event Handler             │
    │                                    │                     │
    │                                    ▼                     │
    │                           ┌──────────────────┐          │
    │                           │ Build/update     │          │
    │                           │ read model       │          │
    │                           └──────────────────┘          │
    └──────────────────────────────────────────────────────────┘

Write models: owned by aggregates, stored in the ai schema, highly normalized (3NF/BCNF).

Read models: denormalized for query performance, stored in the analytics schema or Redis.
Never written by commands. Built and maintained by event handlers.

Examples:

    -- Write model (ai schema, normalized)
    CREATE TABLE ai.conversation_message (
        conversation_message_id UUID PRIMARY KEY,
        conversation_id UUID NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        token_count INTEGER,
        created_at TIMESTAMPTZ NOT NULL
    );

    -- Read model (analytics schema, denormalized for dashboard query)
    CREATE TABLE analytics.daily_conversation_stats (
        date DATE PRIMARY KEY,
        total_conversations INTEGER,
        total_messages INTEGER,
        total_tokens INTEGER,
        avg_messages_per_conversation FLOAT,
        avg_tokens_per_message FLOAT,
        updated_at TIMESTAMPTZ
    );

Rationale:

- CQRS separation allows write-optimized schemas (normalized for consistency) and
  read-optimized schemas (denormalized for speed) to coexist without compromise.
- Read models are updated asynchronously via event handlers, so they are eventually
  consistent. This is acceptable for analytics dashboards and non-critical queries.
- Commands never write to read models, enforcing a unidirectional data flow that prevents
  circular dependencies and makes the system easier to reason about.

---

## 4.10 Archive Tables

Time-series data is partitioned by month using PostgreSQL declarative partitioning.

    CREATE TABLE ai.conversation_message (
        conversation_message_id UUID NOT NULL,
        conversation_id UUID NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL
    ) PARTITION BY RANGE (created_at);

    CREATE TABLE ai.conversation_message_2026_01
        PARTITION OF ai.conversation_message
        FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

    CREATE TABLE ai.conversation_message_2026_02
        PARTITION OF ai.conversation_message
        FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

Monthly partitions for high-volume tables:

    ai.conversation_message
    analytics.analytics_events
    audit.audit_log
    ai.notification

Partition lifecycle:

    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Active   │───▶│ Warm     │───▶│ Cold     │───▶│ Detached │
    │ (hot)    │    │ (read    │    │ (seldom  │    │ (archive │
    │ current  │    │ rarely)  │    │  read)   │    │  storage)│
    │ month    │    │ 1-6 mo   │    │ 6-12 mo  │    │ >12 mo   │
    └──────────┘    └──────────┘    └──────────┘    └──────────┘

After retention period expires:

    ALTER TABLE ai.conversation_message
        DETACH PARTITION ai.conversation_message_2025_01;

    -- Move detached partition data to cold storage (S3/Glacier)
    -- Schema-only table kept for query compatibility

Rationale:

- PostgreSQL declarative partitioning (v10+) pushes partition pruning to the query planner.
  Queries filtered by created_at automatically scan only the relevant partitions.
- Monthly granularity balances partition count (not too many) against partition size (small
  enough for fast maintenance operations like VACUUM, CLUSTER, DETACH).
- Detach-and-archive avoids expensive DELETE operations. Detaching is a metadata-only
  operation that completes instantly, and the data file can then be moved to cold storage
  without affecting the live table.

---

## 4.11 Materialized Views

Analytics dashboards use materialized views for pre-computed aggregations.

    ┌──────────────────────────────────────────────────────────┐
    │  Celery Beat Task Scheduler                              │
    │                                                          │
    │  ┌─────────────────────┐                                 │
    │  │ refresh_mv_daily    │──── 01:00 UTC daily ──────▶    │
    │  └─────────────────────┘     refresh concurrently       │
    │  ┌─────────────────────┐                                 │
    │  │ refresh_mv_weekly   │──── Sunday 02:00 UTC ────▶    │
    │  └─────────────────────┘     refresh concurrently       │
    │  ┌─────────────────────┐                                 │
    │  │ refresh_mv_monthly  │──── 1st 03:00 UTC ──────▶     │
    │  └─────────────────────┘     full refresh               │
    └──────────────────────────────────────────────────────────┘

Defined materialized views:

    -- User-facing dashboards (concurrently refreshed, no downtime)
    CREATE MATERIALIZED VIEW analytics.mv_daily_conversation_stats
    AS SELECT
        DATE(created_at) AS date,
        COUNT(*) AS total_conversations,
        COUNT(DISTINCT user_id) AS active_users,
        SUM(message_count) AS total_messages
    FROM ai.conversation
    GROUP BY DATE(created_at)
    WITH DATA;

    CREATE UNIQUE INDEX ON analytics.mv_daily_conversation_stats (date);

    CREATE MATERIALIZED VIEW analytics.mv_weekly_lead_funnel
    AS SELECT ...  -- lead source, stage, conversion rate
    WITH DATA;

    CREATE MATERIALIZED VIEW analytics.mv_monthly_meeting_metrics
    AS SELECT ...  -- meetings by type, duration, outcome
    WITH DATA;

Refresh strategy:

    -- User-facing dashboards: non-blocking refresh
    REFRESH MATERIALIZED VIEW CONCURRENTLY
        analytics.mv_daily_conversation_stats;

    -- Background reports: full refresh (faster, blocks reads briefly)
    REFRESH MATERIALIZED VIEW
        analytics.mv_monthly_meeting_metrics;

Rationale:

- Materialized views avoid expensive aggregation queries on every dashboard load. For a
  dashboard with daily active users, the aggregation would scan millions of rows; the
  materialized view stores the result in a few hundred rows.
- CONCURRENTLY refresh (requires a unique index) allows reads during refresh, critical for
  user-facing dashboards that must be available 24/7.
- Full refresh is reserved for background reports where a brief read lock is acceptable and
  the faster refresh time is preferred.
- Celery Beat provides a simple, reliable scheduler that runs in-process with the FastAPI
  application, avoiding external cron infrastructure.

---

## 4.12 Partition Strategy

Two partitioning schemes are used depending on the data access pattern.

    ┌──────────────────────────────────────────────────────────┐
    │  Partition Scheme Selection                              │
    │                                                          │
    │  Time-series data          Multi-tenant data (future)    │
    │  ─────────────────────     ─────────────────────         │
    │  RANGE BY created_at       LIST BY tenant_id             │
    │                                                          │
    │  Examples:                 Examples:                     │
    │  conversation_message      tenant_config                 │
    │  analytics_events          tenant_billing                │
    │  audit_log                                              │
    │  notification                                           │
    │                                                          │
    │  High-volume future: Sub-partitioning                    │
    │  RANGE BY created_at                                     │
    │  SUB-PARTITION BY LIST tenant_id                        │
    └──────────────────────────────────────────────────────────┘

RANGE partitioning (current):

    CREATE TABLE ai.conversation_message (
        conversation_message_id UUID NOT NULL,
        conversation_id UUID NOT NULL,
        tenant_id UUID,  -- nullable until multi-tenant active
        created_at TIMESTAMPTZ NOT NULL
    ) PARTITION BY RANGE (created_at);

LIST partitioning (future, when tenant schema is active):

    CREATE TABLE ai.tenant_config (
        tenant_id UUID NOT NULL,
        config_key TEXT NOT NULL,
        config_value JSONB NOT NULL
    ) PARTITION BY LIST (tenant_id);

Sub-partitioning (future, for highest-volume tables):

    CREATE TABLE ai.conversation_message (
        conversation_message_id UUID NOT NULL,
        conversation_id UUID NOT NULL,
        tenant_id UUID NOT NULL,
        created_at TIMESTAMPTZ NOT NULL
    ) PARTITION BY RANGE (created_at);

    -- Each monthly partition is sub-partitioned by tenant
    CREATE TABLE ai.conversation_message_2026_01
        PARTITION OF ai.conversation_message
        FOR VALUES FROM ('2026-01-01') TO ('2026-02-01')
        PARTITION BY LIST (tenant_id);

Partition maintenance:

    -- Option A: pg_partman (automated)
    SELECT partman.create_parent(
        p_parent_table := 'ai.conversation_message',
        p_control := 'created_at',
        p_type := 'native',
        p_interval := '1 month',
        p_premake := 3
    );

    -- Option B: Custom Celery task (more control)
    @celery.task(name="maintain_partitions")
    def maintain_partitions():
        """Create next month's partition, detach expired ones."""
        ...

Rationale:

- RANGE partitioning is the natural fit for append-heavy time-series data where queries
  almost always filter by time range (show me last week's conversations).
- LIST partitioning by tenant_id provides full isolation for multi-tenant data without
  separate table creation. Each tenant's data is physically separated.
- Sub-partitioning (RANGE + LIST) combines the benefits for the highest-volume tables:
  time-based retention management and tenant-based query pruning.
- pg_partman is the preferred automation tool for partition maintenance, but a custom
  Celery task is kept as a fallback to avoid an external extension dependency.

---

## 4.13 Future Sharding Strategy

The migration path from schema-per-service to database-per-service is designed to require
zero application code changes.

    ┌──────────────────────────────────────────────────────────┐
    │  Phase 1: Schema-per-service (current)                   │
    │                                                          │
    │  ┌─────────────────────────────────────────┐             │
    │  │  PostgreSQL Instance                    │             │
    │  │  ├─ public (Django)                     │             │
    │  │  ├─ ai      (FastAPI)                   │             │
    │  │  ├─ analytics                           │             │
    │  │  ├─ audit                               │             │
    │  │  ├─ vector                              │             │
    │  │  └─ tenant (future)                     │             │
    │  └─────────────────────────────────────────┘             │
    │                                                          │
    │  Phase 2: Database-per-service                           │
    │                                                          │
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
    │  │ PostgreSQL│  │ PostgreSQL│  │ PostgreSQL│              │
    │  │ Instance │  │ Instance │  │ Instance │               │
    │  │ AI       │  │ Analytics│  │ Audit    │               │
    │  └──────────┘  └──────────┘  └──────────┘               │
    │                                                          │
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
    │  │ PostgreSQL│  │ PostgreSQL│  │ PostgreSQL│              │
    │  │ Instance │  │ Instance │  │ Instance │               │
    │  │ Vector   │  │ Django   │  │ Tenant   │               │
    │  └──────────┘  └──────────┘  └──────────┘               │
    │                                                          │
    │  Phase 3: Cross-database communication                   │
    │                                                          │
    │  AI Instance ◄──REST/events──► Django Instance           │
    │  AI Instance ◄──REST/events──► Analytics Instance         │
    └──────────────────────────────────────────────────────────┘

Migration steps:

    1. Create new PostgreSQL instances (one per schema).
    2. Dump each schema from the shared instance and restore into its dedicated instance.
    3. Update connection strings in the service configuration
       (e.g., AI_DATABASE_URL -> points to AI instance).
    4. Replace direct SQL cross-schema access with REST API calls or event streams.
    5. Verify the AI service functions identically — no code changes should be needed
       because repositories abstract storage behind a Repository interface.

Why this works:

    ┌──────────────────────────────────────────────┐
    │  Before:                                     │
    │                                              │
    │  class ConversationRepository:               │
    │      def __init__(self, db: Database):       │
    │          self.db = db                        │
    │                                              │
    │      def save(self, conv):                   │
    │          self.db.execute(                    │
    │              "UPDATE ai.conversation ..."    │
    │          )                                   │
    │                                              │
    │  After (only connection string changes):     │
    │                                              │
    │  DB_CONNECTION_STR = "postgresql://..."      │
    │  # One connection string per database        │
    │  # Database is injected at startup           │
    └──────────────────────────────────────────────┘

Rationale:

- Repository abstraction is the key enabler. Because all database access goes through
  repository classes, changing the target database is a configuration-only change.
- Cross-database communication shifts from direct SQL joins to REST/events, which is the
  same pattern already used for cross-schema communication (see section 4.7). No new
  patterns need to be introduced.
- The migration can be done incrementally: migrate one schema at a time, keeping others
  on the shared instance. Rollback is as simple as reverting the connection string.
- No distributed transaction coordination is needed because aggregates are the consistency
  boundary and no transaction spans schemas (established in section 4.6).



# 5. Redis Strategy

Design Redis as an enterprise-grade cache and real-time data layer. Redis provides sub-millisecond access patterns for hot data, distributed locking, rate limiting, and ephemeral state management. The PostgreSQL database remains the authoritative system of record; Redis is a read-optimized cache that may be rebuilt from PostgreSQL at any time.

### 5.1 Conversation State

| Attribute | Detail |
|-----------|--------|
| Purpose | Hot cache for conversation metadata |
| Ownership | Conversation Aggregate |
| Key Pattern | conversation:{id}:state |
| Data Type | Hash |
| TTL | 1h (extended on activity) |
| Expiration | Lazy expiration on read/write + active expiry cycle |
| Eviction Policy | volatile-lru |
| Consistency | Eventual — PostgreSQL is source of truth, Redis is read-only cache populated after DB write |
| Recovery | On miss, load from PostgreSQL and re-populate |
| Rebuild Strategy | Background job scans conversations table, re-populates hashes |

### 5.2 Session Cache

| Attribute | Detail |
|-----------|--------|
| Purpose | Avoid DB session lookup per request |
| Ownership | Auth Domain |
| Key Pattern | session:{token} |
| Data Type | Hash |
| TTL | 24h (extended on request) |
| Expiration | Extended on every authenticated request via EXPIRE |
| Eviction Policy | volatile-ttl |
| Consistency | Strong within TTL window — sessions are write-through to Redis |
| Security | session data includes user_id, roles, tenant_id |
| Recovery | On Redis failure, fall back to DB (degraded auth) |
| Rebuild Strategy | Session created in Redis on login; rehydrated from DB on miss |

### 5.3 Distributed Lock

| Attribute | Detail |
|-----------|--------|
| Purpose | Pessimistic locking for critical sections (conversation append, meeting booking, saga execution) |
| Ownership | Infrastructure |
| Key Pattern | lock:{resource} |
| Data Type | String (SET NX + EX) |
| TTL | Configurable (10-60s) |
| Expiration | Auto-released via TTL; explicit DEL on unlock |
| Eviction Policy | No eviction (TTL-based auto-release) |
| Consistency | Strong via Redlock (requires 3 of 5 nodes) |
| Recovery | Lock auto-releases on TTL expiry; client retry with backoff |
| Rebuild Strategy | N/A — locks are ephemeral |

### 5.4 Rate Limiting

| Attribute | Detail |
|-----------|--------|
| Purpose | Sliding window rate counters per user/IP/tenant |
| Ownership | API Gateway / Middleware |
| Key Pattern | rate-limit:{scope}:{identifier}:{endpoint} |
| Data Type | Sorted set or counter (INCR + EXPIRE) |
| TTL | Window-dependent (1s-1h) |
| Expiration | Keys expire at window end |
| Eviction Policy | volatile-ttl |
| Consistency | Best-effort — bypass on Redis failure |
| Recovery | In-memory approximate counters during Redis outage |
| Rebuild Strategy | Fresh window starts on next request after expiry |

### 5.5 Conversation Cache

| Attribute | Detail |
|-----------|--------|
| Purpose | Last N messages for fast conversation hydration |
| Ownership | Conversation Aggregate |
| Key Pattern | conversation:{id}:recent |
| Data Type | List (capped at 50 with LTRIM) |
| TTL | 1h (extended on append) |
| Expiration | Extended on every message append |
| Eviction Policy | allkeys-lru |
| Consistency | Eventual — reconstructed from PostgreSQL on miss |
| Recovery | Fallback: PostgreSQL with LIMIT 50 |
| Rebuild Strategy | LPUSH latest 50 messages from PostgreSQL on cache miss |

### 5.6 Memory Cache

| Attribute | Detail |
|-----------|--------|
| Purpose | Cached memory context for LLM personalization |
| Ownership | Memory Aggregate |
| Key Pattern | memory:{user_id}:context |
| Data Type | String (JSON serialized) |
| TTL | 2h |
| Expiration | Passive expiry on read |
| Eviction Policy | volatile-lru |
| Consistency | Eventual — rebuilt from PostgreSQL long-term memory on miss |
| Recovery | On miss, rehydrate from PostgreSQL long-term memory store |
| Rebuild Strategy | Async job re-computes memory context and caches to Redis |

### 5.7 Prompt Cache

| Attribute | Detail |
|-----------|--------|
| Purpose | Active prompt version for sub-ms LLM context resolution |
| Ownership | Prompt Domain |
| Key Pattern | prompt:active:{prompt_id} |
| Data Type | String |
| TTL | Infinite (invalidated on promote) |
| Expiration | Manual invalidation when a new prompt version is promoted |
| Eviction Policy | Manual invalidation only |
| Consistency | Strong — single writer on promotion |
| Recovery | On miss, load from PostgreSQL prompt versions table |
| Rebuild Strategy | Re-populate on promote event |

### 5.8 Knowledge Cache

| Attribute | Detail |
|-----------|--------|
| Purpose | Cache vector search results to avoid expensive re-ranking |
| Ownership | Knowledge Domain |
| Key Pattern | knowledge:search:{query_hash} |
| Data Type | String (JSON serialized results) |
| TTL | 5min / 30s filtered |
| Expiration | Short TTL to balance freshness vs performance |
| Eviction Policy | allkeys-lru |
| Consistency | Best-effort — stale results acceptable for short window |
| Recovery | On miss, execute vector search against pgvector |
| Rebuild Strategy | Results cached on each vector search completion |

### 5.9 Embedding Cache

| Attribute | Detail |
|-----------|--------|
| Purpose | Cache embedding API results for identical text (cost-saving, avoids redundant API calls) |
| Ownership | Embedding Service |
| Key Pattern | embedding:{model}:{text_hash} |
| Data Type | String (JSON embedding vector) |
| TTL | 24h |
| Expiration | Fixed TTL from creation |
| Eviction Policy | allkeys-lru |
| Consistency | Strong — identical text + model always produces same vector |
| Recovery | On miss, call embedding API and cache result |
| Rebuild Strategy | Re-populated on embedding request miss |

### 5.10 Model Cache

| Attribute | Detail |
|-----------|--------|
| Purpose | Model provider health and rate-limit status for router decisions |
| Ownership | LLM Router |
| Key Pattern | model:{provider}:status |
| Data Type | Hash |
| TTL | 30s |
| Expiration | Refreshed on each health check cycle |
| Eviction Policy | volatile-ttl |
| Consistency | Best-effort — stale status causes sub-optimal routing |
| Recovery | On miss, execute live health check against provider |
| Rebuild Strategy | Background health check worker updates Redis |

### 5.11 Workflow Cache

| Attribute | Detail |
|-----------|--------|
| Purpose | Workflow execution state for fast status checks |
| Ownership | Workflow Engine |
| Key Pattern | wf:exec:{id}:state |
| Data Type | Hash |
| TTL | 24h |
| Expiration | Retained for workflow lifetime, cleaned up after completion |
| Eviction Policy | volatile-ttl |
| Consistency | Eventual — PostgreSQL is authoritative for workflow state |
| Recovery | On miss, load workflow state from PostgreSQL |
| Rebuild Strategy | Repopulated on workflow state transitions |

### 5.12 Health Cache

| Attribute | Detail |
|-----------|--------|
| Purpose | Cached health check results to avoid hammering downstream services |
| Ownership | Monitoring |
| Key Pattern | health:{component} |
| Data Type | String (JSON health report) |
| TTL | 10s |
| Expiration | Aggressive short TTL for near-real-time health data |
| Eviction Policy | volatile-ttl |
| Consistency | Best-effort — 10s staleness acceptable for health dashboards |
| Recovery | On miss, run health check against component |
| Rebuild Strategy | Each health check cycle updates the cache |

### 5.13 Configuration Cache

| Attribute | Detail |
|-----------|--------|
| Purpose | Feature flag cache, togglable without deploy |
| Ownership | Configuration Service |
| Key Pattern | config:runtime:feature-flags |
| Data Type | Hash |
| TTL | 5min (invalidated on flag change) |
| Expiration | Polling interval; invalidated on flag update event |
| Eviction Policy | volatile-lru |
| Consistency | Eventual — up to 5min propagation delay on flag changes |
| Recovery | On miss, load from PostgreSQL configuration store |
| Rebuild Strategy | Repopulated on flag change event + scheduled refresh |

### 5.14 Tool Cache

| Attribute | Detail |
|-----------|--------|
| Purpose | Cache deterministic tool execution results |
| Ownership | Tool Execution Engine |
| Key Pattern | tool-cache:{tool}:{arg_hash} |
| Data Type | String |
| TTL | 30min |
| Expiration | Fixed TTL from creation |
| Eviction Policy | allkeys-lru |
| Consistency | Strong for deterministic tools; invalidated by explicit TTL |
| Recovery | On miss, execute tool and cache result |
| Rebuild Strategy | Re-populated on tool execution miss |

### 5.15 Summary Cache

| Attribute | Detail |
|-----------|--------|
| Purpose | Cached LLM-generated conversation summary |
| Ownership | Conversation Aggregate |
| Key Pattern | summary:{conversation_id} |
| Data Type | String |
| TTL | 1h |
| Expiration | Extended on conversation activity |
| Eviction Policy | volatile-lru |
| Consistency | Eventual — summary regenerated from full conversation on miss |
| Recovery | On miss, regenerate summary via LLM from PostgreSQL messages |
| Rebuild Strategy | Async regeneration on cache miss or conversation update |

### 5.16 Temporary Upload Cache

| Attribute | Detail |
|-----------|--------|
| Purpose | Temporary upload metadata before processing |
| Ownership | File Service |
| Key Pattern | upload:{upload_id} |
| Data Type | String |
| TTL | 1h |
| Expiration | Fixed TTL; upload must be processed before expiry |
| Eviction Policy | volatile-ttl |
| Consistency | Strong — single writer, single reader |
| Recovery | On miss, upload is considered expired/stale; client must re-upload |
| Rebuild Strategy | N/A — uploads are ephemeral; re-upload on expiry |

### 5.17 Key Naming Convention

    {domain}:{identifier}:{sub-resource}

Colon-delimited namespaces with hierarchical structure for logical grouping and efficient key scanning.

    Examples:
      conversation:abc123:lock
      rate-limit:user:user_xyz:chat
      prompt:active:greeting-v2
      embedding:text-embedding-3-small:a1b2c3d4e5f6
      model:openai:status
      wf:exec:uuid-1234:state
      tool-cache:web_search:hash7890
      health:postgresql:status
      config:runtime:feature-flags
      summary:conv-uuid:summary
      upload:upload-uuid:metadata

### 5.18 Redis Cluster Topology

    3 master / 3 replica nodes minimum.
    Dedicated Redis instance for Celery broker (isolates queue throughput).
    Persistence: AOF (fsync every 1s) + RDB (every 5 min).
    Sentinel for auto-failover.
    Redlock for distributed locks (requires 3 of 5 nodes).

    Node Layout:
      +------------------+     +------------------+     +------------------+
      |   Master A       |<--->|   Replica A'     |     |   Master B       |
      | slot 0-5460      |     | failover standby |     | slot 5461-10922  |
      +------------------+     +------------------+     +------------------+
              |                                               |
              +------------------+     +------------------+   |
              |   Replica B'     |     |   Master C       |<--+
              | failover standby |     | slot 10923-16383 |
              +------------------+     +------------------+
                                               |
                                        +------------------+
                                        |   Replica C'     |
                                        | failover standby |
                                        +------------------+

    Sentinel Cluster (3 nodes minimum):
      - Monitors all master/replica pairs
      - Auto-promotes replica on master failure
      - Updates client connection info on failover

    Client Connection Strategy:
      - Use RedisCluster client with automatic slot routing
      - Retry with exponential backoff on MOVED/ASK redirects
      - Connection pooling: min 10, max 50 connections per instance

### 5.19 Degradation Strategy

| Tier | Condition | Behavior |
|------|-----------|----------|
| Tier 1 | Redis down | Fall back to PostgreSQL for all reads; disable rate limiting (in-memory approximate); sessions validated from DB |
| Tier 2 | High latency (>50ms p99) | Local in-memory cache with short TTL (5s); reduce lock TTL; circuit-breaker on cache writes |
| Tier 3 | Partial outage | Gracefully disable non-critical features (tool cache, knowledge cache, embedding cache); prioritize conversation, session, and lock operations |

    Degradation Decision Flow:

        Is Redis available?
          +--> YES: Normal operation (serve from Redis)
          +--> NO:  Enter Tier 1 degradation
                       |
                       +--> PostgreSQL fallback for all reads
                       +--> Disable rate limiting (in-memory approx)
                       +--> DB-backed session validation
                       |
                       Is latency > 50ms p99?
                         +--> YES: Enter Tier 2 degradation
                         |          +--> Activate local in-memory cache (TTL 5s)
                         |          +--> Reduce distributed lock TTL
                         |          +--> Enable write circuit-breaker
                         |
                         Is partial failure detected?
                           +--> YES: Enter Tier 3 degradation
                                    +--> Disable tool-cache
                                    +--> Disable knowledge-cache
                                    +--> Disable embedding-cache
                                    +--> Keep conversation, session, lock operational




# 6. Conversation Persistence

---

## 6.1 Conversation Storage Architecture

    Conversation Data Flow:
    
      ┌─────────────────────────────────────────────────────────────────────────┐
      │                         Conversation Storage Tiers                       │
      │                                                                           │
      │  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐               │
      │  │  Redis        │     │  PostgreSQL  │     │  Cold Archive │              │
      │  │  (Tier 1)     │────>│  (Tier 2)    │────>│  S3 Glacier   │              │
      │  │  Active state │     │  Full conv + │     │  (Tier 4)     │              │
      │  │  Recent msgs  │     │  messages    │     │  After 365d   │              │
      │  └──────────────┘     └──────────────┘     └──────────────┘               │
      │        │                     │                      │                      │
      │        │                     │                      │                      │
      │        ▼                     ▼                      ▼                      │
      │  ┌──────────────┐     ┌──────────────┐                                    │
      │  │ conversation  │     │ LLM Summary  │                                    │
      │  │ :{id}:recent  │     │ Generation   │                                    │
      │  │ List (50 msg) │────>│ (Tier 3)     │                                    │
      │  └──────────────┘     │ ai.conversat │                                    │
      │                       │ ion_summary  │                                    │
      │                       └──────────────┘                                    │
      └─────────────────────────────────────────────────────────────────────────┘
    
    Lifecycle:
      User sends message -> Append to Redis conversation:{id}:recent (List, LTRIM 50)
                         -> Async flush to PostgreSQL ai.conversation_message
                         -> Update conversation state in Redis conversation:{id}:state
    
      Active (Redis, TTL 24h sliding) -> Warm (PostgreSQL, up to 365d)
        -> Summary generated (LLM, every 10 messages)
        -> Cold archive (S3 Glacier, after 365d inactivity)

Trade-off: Redis-first writes provide sub-millisecond response for the user, but introduce a
window of data loss (up to 1 second) if Redis crashes before the async flush. We accept this
because the async flush is configured with fsync=always for the conversation key space, and
PostgreSQL remains the system of record for all completed message exchanges.

---

## 6.2 Conversation Table Design

    CREATE TABLE ai.conversation (
        conversation_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id            UUID NOT NULL,
        title              TEXT NOT NULL DEFAULT 'New Conversation',
        status             TEXT NOT NULL DEFAULT 'new',
                             -- state machine: new, awaiting_identity,
                             -- classifying_intent, active,
                             -- waiting_for_confirmation, executing_tool,
                             -- waiting_for_human, summarizing, paused,
                             -- resuming, idle, timeout, archived,
                             -- failed, terminated
        participant_ids    UUID[] NOT NULL DEFAULT '{}',
        created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
        last_activity_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
        message_count      INTEGER NOT NULL DEFAULT 0,
        metadata           JSONB NOT NULL DEFAULT '{}',
        version            BIGINT NOT NULL DEFAULT 1
    );

    CREATE INDEX ix_conversation_user_id_status
        ON ai.conversation (user_id, status);
    CREATE INDEX ix_conversation_last_activity_at
        ON ai.conversation (last_activity_at);
    CREATE INDEX ix_conversation_participants
        ON ai.conversation USING GIN (participant_ids);

Columns:

    conversation_id (UUID PK)     - UUID v4, generated application-side or by
                                    gen_random_uuid(). Avoids sequential guessing.
    user_id (UUID FK)             - Owner of the conversation. Foreign key to
                                    the identity service (application-enforced,
                                    not a DB FK to avoid cross-schema coupling).
    title                          - User-facing title. Auto-generated from first
                                    message by LLM if not provided.
    status                         - State machine enum (see section 6.6). Stored
                                    as TEXT to allow future state additions without
                                    ALTER TYPE.
    participant_ids (UUID[])       - Denormalized array of participant user IDs
                                    for fast lookup (GIN index). Source of truth
                                    is ai.conversation_participant table.
    created_at, updated_at         - Standard audit timestamps. updated_at managed
                                    by application or trigger.
    last_activity_at               - Drives archive decisions (365d inactivity
                                    threshold). Updated on every message append.
    message_count                  - Denormalized counter for fast display without
                                    COUNT query. Updated atomically on message
                                    insert. Eventual consistency with
                                    ai.conversation_message count is acceptable.
    metadata (JSONB)               - Flexible key-value storage for extensible
                                    conversation attributes (see section 6.5).
    version (BIGINT)               - Optimistic locking counter. Incremented on
                                    every conversation-level update (see section
                                    6.14).

Why JSONB for metadata instead of separate columns or EAV:

    - JSONB is flexible: new attributes (e.g., source, timezone, language) can be
      added without schema migration. This is critical for a rapidly evolving AI
      assistant where conversation attributes change frequently.
    - JSONB supports indexing (GIN) for querying into metadata fields when needed.
    - JSONB avoids the EAV (Entity-Attribute-Value) anti-pattern which produces
      terrible query performance and complex join logic.
    - Trade-off: JSONB has ~10% storage overhead vs a fixed column, but the
      flexibility gain far outweighs the storage cost for a hot-path table.
    - Trade-off: Type safety is lost — validation moves to the application layer.
      Mitigated by Pydantic models that validate metadata on ingress.

---

## 6.3 Messages Table Design

    CREATE TABLE ai.conversation_message (
        message_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        conversation_id     UUID NOT NULL REFERENCES ai.conversation(conversation_id),
        role                TEXT NOT NULL,
                              -- CHECK (role IN ('user','assistant','system','tool'))
        content             TEXT NOT NULL,
        content_hash        TEXT,
        tokens              INTEGER,
        model               VARCHAR(255),
        tool_calls          JSONB,
        tool_results        JSONB,
        metadata            JSONB NOT NULL DEFAULT '{}',
        created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
        version             BIGINT NOT NULL DEFAULT 1
    ) PARTITION BY RANGE (created_at);

    CREATE INDEX ix_conversation_message_conv_id_created_at
        ON ai.conversation_message (conversation_id, created_at);
    CREATE UNIQUE INDEX uq_conversation_message_content_hash
        ON ai.conversation_message (conversation_id, content_hash)
        WHERE content_hash IS NOT NULL;

Columns:

    message_id (UUID PK)         - Unique identifier for the message.
    conversation_id (UUID FK)    - Owning conversation. Foreign key enforced
                                   within the ai schema.
    role (enum: user, assistant,  - Who generated the message. Stored as TEXT
           system, tool)           with CHECK constraint rather than a native
                                   enum to avoid ALTER TYPE on role addition.
    content (TEXT)               - The message body. Can be very large (LLM
                                   generations up to hundreds of KB).
    content_hash (TEXT)          - SHA-256 hash of content for deduplication.
                                   Used with the unique index (conversation_id,
                                   content_hash) to prevent duplicate messages
                                   from retry logic.
    tokens (INT)                 - Token count for cost tracking and context
                                   window management. Populated by LLM response.
    model (VARCHAR)              - Model identifier (e.g., gpt-4o, claude-3-opus).
                                   Null for user messages.
    tool_calls (JSONB)           - Structured representation of tool invocation
                                   requests from the assistant.
    tool_results (JSONB)         - Structured results returned by tool executions.
    metadata (JSONB)             - Per-message flexible metadata (see section 6.5).
    created_at                   - Immutable timestamp. Messages are append-only,
                                   never updated.
    version (BIGINT)             - Optimistic locking. Typically 1 because messages
                                   are append-only, but included for consistency
                                   with the aggregate pattern.

Why TEXT not JSONB for content:

    - LLM content can be extremely long (100K+ tokens, 500K+ characters). JSONB adds
      ~10-20% storage overhead for parsing and decompression overhead on every read.
      TEXT storage is raw and efficiently compressed by PostgreSQL's TOAST system.
    - TEXT supports full-text search (GIN tsvector index) for semantic searches
      without loading the JSONB parse tree.
    - LLM content is unstructured text, not structured data. JSONB would provide
      no benefit — there are no keys to index or query into within content.
    - TOAST (The Oversized-Attribute Storage Technique) handles TEXT > ~2KB by
      moving it out-of-line into a separate compressed storage area. This keeps
      the main table rows small and index scans fast.
    - Trade-off: If content were structured (e.g., tool_call arguments), JSONB
      would be appropriate. Those cases use separate tool_calls/tool_results columns.

---

## 6.4 Attachments

    CREATE TABLE ai.conversation_attachment (
        attachment_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        message_id       UUID NOT NULL REFERENCES ai.conversation_message(message_id),
        file_name        TEXT NOT NULL,
        file_type        TEXT NOT NULL,
        file_size        BIGINT NOT NULL,
        storage_url      TEXT NOT NULL,
        storage_provider TEXT NOT NULL DEFAULT 's3',
                           -- 's3', 'azure_blob', 'gcs'
        uploaded_at      TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE INDEX ix_conversation_attachment_message_id
        ON ai.conversation_attachment (message_id);

Design decisions:

    - Actual file content is stored in blob storage (S3, Azure Blob, GCS), not in
      the database. The database stores only metadata and a URL pointer.
    - file_size in bytes allows the application to enforce per-message and
      per-conversation attachment size limits without reading blob storage.
    - storage_provider enables multi-cloud attachment storage without schema
      changes. The application selects provider based on tenant/region policy.
    - storage_url includes a presigned URL with TTL for temporary direct access,
      or a canonical S3 key (s3://bucket/key) that requires the service to
      generate a presigned URL on demand.
    - No foreign key to a file/upload table: attachments are scoped to messages
      and archived with them.

Trade-off: Blob storage introduces latency (50-200ms) for attachment retrieval
vs 1-5ms for DB storage. However, DB storage of binary files causes table bloat,
slows backups, and makes partition detach/archive operations expensive (multi-GB
data files must be moved). Blob storage is the correct choice for files > 1KB.

---

## 6.5 Conversation Metadata

Conversation-level metadata is stored in the `metadata` JSONB column of
ai.conversation. This is a flexible, schema-less structure that can contain any
key-value pairs without requiring a migration.

Standard metadata keys (documented convention, enforced by Pydantic):

    {
        "source": "web",
        "timezone": "America/New_York",
        "language": "en",
        "tags": ["support", "billing"],
        "custom_fields": {
            "company_id": "comp_123",
            "ticket_id": "TKT-456"
        },
        "client_info": {
            "ip_address": "203.0.113.42",
            "user_agent": "Mozilla/5.0 ...",
            "platform": "desktop"
        },
        "referrer": "direct",
        "campaign": "spring_promo_2026",
        "satisfaction_score": 4.5
    }

Why JSONB for metadata:

    - Zero-migration extensibility: new attributes can be added at any time by
      any client without schema changes. In a multi-tenant SaaS with diverse
      customer requirements, this is essential.
    - GIN indexes on JSONB paths allow efficient querying:
        CREATE INDEX ix_conversation_metadata_source
            ON ai.conversation USING GIN ((metadata -> 'source'));
    - The metadata column is not used in WHERE clauses on the hot path (message
      append, conversation load). It is loaded only when needed (analytics,
      admin UI, export).
    - Trade-off: Data validation moves to the application layer. Pydantic models
      on write enforce the documented structure. Ad-hoc keys are allowed but
      warned in logs for governance.

Migration path if JSONB proves insufficient:

    If a metadata key becomes query-critical (e.g., source is filtered on every
    request), it can be promoted to a first-class column:
        ALTER TABLE ai.conversation ADD COLUMN source TEXT;
        UPDATE ai.conversation SET source = metadata->>'source';
    The JSONB column remains for backward compatibility during migration.

---

## 6.6 Conversation Status State Machine

The conversation status follows a rigorously defined state machine with 15
states and explicit transition rules.

States:

    1.  New                  - Conversation created, no messages yet
    2.  AwaitingIdentity     - Waiting for user identification (anonymous users)
    3.  ClassifyingIntent    - LLM classifying user intent
    4.  Active               - Normal conversation flow
    5.  WaitingForConfirmation - Waiting for user to confirm an action
    6.  ExecutingTool        - Tool execution in progress
    7.  WaitingForHuman      - Escalated to human agent
    8.  Summarizing          - LLM generating conversation summary
    9.  Paused               - User explicitly paused conversation
    10. Resuming              - Transitioning from paused to active
    11. Idle                  - No activity within timeout (configurable, default 5min)
    12. Timeout              - Idle for > 30 minutes
    13. Archived             - Conversation archived (read-only)
    14. Failed               - Irrecoverable error state
    15. Terminated           - Explicit termination by user or system

Allowed Transitions:

    New -> AwaitingIdentity | ClassifyingIntent | Active | Terminated
    AwaitingIdentity -> ClassifyingIntent | Active | Terminated
    ClassifyingIntent -> Active | WaitingForConfirmation | WaitingForHuman | Failed
    Active -> WaitingForConfirmation | ExecutingTool | WaitingForHuman | Idle |
              Paused | Summarizing | Failed | Terminated
    WaitingForConfirmation -> Active | Timeout | Failed | Terminated
    ExecutingTool -> Active | Failed | Terminated
    WaitingForHuman -> Active | Timeout | Failed | Terminated
    Summarizing -> Active | Archived | Failed
    Paused -> Resuming | Timeout | Terminated
    Resuming -> Active | Failed
    Idle -> Active | Timeout | Archived
    Timeout -> Archived | Terminated
    Archived -> (no transitions — read-only, only recoverable via restore)
    Failed -> Terminated | (retry logic may transition to Active)
    Terminated -> (terminal state)

Storage Implications by State:

    Redis-only states (not persisted to PostgreSQL until transition out):
        ClassifyingIntent   - Transient, exists only during LLM call
        ExecutingTool       - Transient, exists only during tool execution
        Summarizing         - Transient, exists only during summary generation
        Resuming            - Transient, exists only during resume operation
    
    Redis + PostgreSQL (persisted on every state change):
        New
        AwaitingIdentity
        Active
        WaitingForConfirmation
        WaitingForHuman
        Paused
        Idle
        Timeout
        Archived
        Failed
        Terminated

    Rationale: Transient states are held only in Redis because they are
    short-lived (milliseconds to seconds). Persisting them to PostgreSQL would
    generate excessive writes for states that have no long-term value. The
    PostgreSQL conversation record transitions directly from the entry state
    to the exit state of a transient operation.

State transition enforcement:

    State transitions are enforced by the Conversation aggregate. An invalid
    transition (e.g., Archived -> Active) raises a StateTransitionError. This
    logic is in the application layer, not in a DB trigger, to keep it
    testable and version-controlled.

---

## 6.7 Participants

    CREATE TABLE ai.conversation_participant (
        conversation_id  UUID NOT NULL REFERENCES ai.conversation(conversation_id),
        user_id          UUID NOT NULL,
        role             TEXT NOT NULL DEFAULT 'participant',
                           -- 'owner', 'participant', 'observer'
        joined_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
        left_at          TIMESTAMPTZ,
        is_active        BOOLEAN NOT NULL DEFAULT true,
        PRIMARY KEY (conversation_id, user_id)
    );

    CREATE INDEX ix_conversation_participant_user_active
        ON ai.conversation_participant (user_id, is_active);

Design decisions:

    - The denormalized participant_ids array on ai.conversation enables fast
      queries: "find all conversations for user X" without a join. The GIN
      index on participant_ids makes this a bitmap index scan.
    - The normalized ai.conversation_participant table is the source of truth
      for role, join/leave times, and active status.
    - is_active distinguishes active participants from those who have left.
      When all participants leave, the conversation transitions to Idle ->
      Timeout.
    - role determines permissions:
        owner:       can delete, archive, manage participants
        participant: can send messages, view history
        observer:    read-only, cannot send messages

Sync between denormalized array and normalized table:

    -- On participant add:
    INSERT INTO ai.conversation_participant (conversation_id, user_id, role)
    VALUES (:conv_id, :user_id, :role);
    
    UPDATE ai.conversation
    SET participant_ids = array_append(participant_ids, :user_id),
        version = version + 1
    WHERE conversation_id = :conv_id;

    -- On participant remove:
    UPDATE ai.conversation_participant
    SET left_at = now(), is_active = false
    WHERE conversation_id = :conv_id AND user_id = :user_id;
    
    UPDATE ai.conversation
    SET participant_ids = array_remove(participant_ids, :user_id),
        version = version + 1
    WHERE conversation_id = :conv_id;

Trade-off: The denormalized array introduces a consistency window where the
array may be out of sync with the participant table (if the UPDATE fails after
the INSERT). Mitigation: both operations run in the same DB transaction. If the
UPDATE fails, the INSERT is rolled back.

---

## 6.8 Memory References

Conversations reference long-term memory entries via a link table.

    CREATE TABLE ai.conversation_memory (
        conversation_id  UUID NOT NULL REFERENCES ai.conversation(conversation_id),
        memory_id        UUID NOT NULL REFERENCES ai.memory(memory_id),
        reference_type   TEXT NOT NULL,
                           -- 'created', 'updated', 'read'
        created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
        PRIMARY KEY (conversation_id, memory_id, reference_type)
    );

    CREATE INDEX ix_conversation_memory_memory_id
        ON ai.conversation_memory (memory_id);
    CREATE INDEX ix_conversation_memory_conversation_id
        ON ai.conversation_memory (conversation_id);

Purpose:

    - Tracks which memories were accessed or modified during a conversation.
    - Enables audit: "which conversation created/updated/read this memory entry?"
    - Enables context injection optimizer: pre-fetch memories that are frequently
      referenced in similar conversations.
    - reference_type distinguishes the nature of the interaction:
        created: conversation created a new memory
        updated: conversation modified an existing memory
        read:    conversation accessed (read) a memory for context

This is a pure link table with no additional payload. Performance is critical:
lookups are by conversation_id (to list memories referenced in a conversation)
or by memory_id (to find which conversations touched a memory).

---

## 6.9 Meeting References

Conversations reference meetings (scheduled or past) via a link table.

    CREATE TABLE ai.conversation_meeting (
        conversation_id  UUID NOT NULL REFERENCES ai.conversation(conversation_id),
        meeting_id       UUID NOT NULL REFERENCES ai.meeting(meeting_id),
        reference_type   TEXT NOT NULL,
                           -- 'scheduled_from_conversation',
                           -- 'discussed_in_meeting'
        created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
        PRIMARY KEY (conversation_id, meeting_id)
    );

    CREATE INDEX ix_conversation_meeting_meeting_id
        ON ai.conversation_meeting (meeting_id);

reference_type values:

    scheduled_from_conversation - The conversation led to scheduling a meeting.
                                  The meeting was created by the AI assistant
                                  during the conversation.
    discussed_in_meeting        - The conversation was referenced/discussed
                                  during a meeting. The meeting summary or
                                  transcript may contain relevant information.

This link table enables the system to answer questions like:
    - "Which meetings have been scheduled from this conversation?"
    - "What conversations were discussed in meeting X?"

---

## 6.10 Workflow References

Conversations reference workflow executions via a link table.

    CREATE TABLE ai.conversation_workflow (
        conversation_id   UUID NOT NULL REFERENCES ai.conversation(conversation_id),
        execution_id      UUID NOT NULL REFERENCES ai.workflow_execution(execution_id),
        trigger_type      TEXT NOT NULL,
                            -- 'automatic', 'manual', 'scheduled'
        created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
        PRIMARY KEY (conversation_id, execution_id)
    );

    CREATE INDEX ix_conversation_workflow_execution_id
        ON ai.conversation_workflow (execution_id);

trigger_type:

    automatic - Workflow triggered by the AI during conversation processing
                (e.g., send_summary_email workflow fires automatically when
                conversation reaches Summarizing state).
    manual    - Workflow triggered by explicit user request
                (e.g., user says "send this to my team").
    scheduled - Workflow triggered by a schedule that references this
                conversation (e.g., weekly status report workflow).

This enables traceability: for any workflow execution, you can find the
originating conversation, and for any conversation, you can list all workflows
that were executed.

---

## 6.11 Conversation Archive

Archive strategy moves cold conversations from PostgreSQL to cost-optimized
cold storage.

    Archive Trigger:
    After 365 days of inactivity (last_activity_at < now() - interval '365 days'),
    the conversation is eligible for archiving.

    Archive Process (Celery cleanup_worker):

        1. Celery beat schedules cleanup_worker.archive_expired() daily.
        2. Query identifies conversations with last_activity_at < 365 days ago
           AND status NOT IN ('archived', 'terminated', 'failed').
        3. For each conversation:
           a. Serialize full conversation + all messages + metadata + summaries
              into a compressed JSON document (gzip, compression ratio ~5:1 for
              text-heavy content).
           b. Upload compressed JSON to S3 Glacier (or Azure Archive, depending
              on cloud provider) with key format:
                  conversations/{year}/{month}/{conversation_id}.json.gz
           c. Insert pointer record into ai.conversation_archive.
           d. Update conversation status to 'archived'.
           e. Optionally delete or truncate messages from
              ai.conversation_message (after a grace period).

    CREATE TABLE ai.conversation_archive (
        archive_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        conversation_id    UUID NOT NULL REFERENCES ai.conversation(conversation_id),
        storage_url        TEXT NOT NULL,
                             -- s3://bucket/conversations/2026/01/uuid.json.gz
        storage_provider   TEXT NOT NULL DEFAULT 's3_glacier',
        archive_size_bytes BIGINT,
        checksum           TEXT NOT NULL,
                             -- SHA-256 of the archive file
        message_count      INTEGER,
        token_count        BIGINT,
        original_created_at TIMESTAMPTZ,
        archived_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
        restored_at        TIMESTAMPTZ,
        UNIQUE (conversation_id)
    );

    Archive Format (compressed JSON):

        {
            "version": "1.0",
            "conversation_id": "uuid",
            "archived_at": "2026-06-30T00:00:00Z",
            "conversation": { ... full ai.conversation row ... },
            "messages": [
                { ... full ai.conversation_message row ... },
                ...
            ],
            "summaries": [
                { ... full ai.conversation_summary row ... },
                ...
            ],
            "participants": [
                { ... full ai.conversation_participant row ... },
                ...
            ],
            "metadata": {
                "memory_references": [...],
                "meeting_references": [...],
                "workflow_references": [...]
            }
        }

Trade-off: 365 days is an aggressive archive threshold. The alternative (90 days
from the earlier data storage matrix) would reduce PG storage costs but increase
archive/restore operations. The 365-day threshold is chosen because:
    1. PG storage is relatively cheap ($0.115/GB/month on AWS RDS).
    2. Active conversations are typically short-lived (hours to days). A
       conversation still referenced after 365 days is exceptionally rare.
    3. Longer in-PG retention reduces archive/restore operations and provides
       a better user experience for the rare case of revisiting old data.
    4. S3 Glacier Deep Archive costs $0.00099/GB/month — 100x cheaper than PG
       — so archiving is purely cost optimization, not capacity management.

---

## 6.12 Conversation Recovery

Recovery restores an archived conversation to active storage on user request.

    Recovery Process:

        User requests archived conversation
            -> API endpoint: GET /conversations/{id}/restore
            -> Celery task: restore_archived_conversation.delay(conversation_id)
            -> Task reads compressed JSON from S3 Glacier storage_url
               (Glacier restore: 1-12 hours for standard, 5 minutes for expedited)
            -> Reconstructs conversation in PostgreSQL:
               1. INSERT or UPDATE ai.conversation (with restored_at flag)
               2. INSERT all messages to ai.conversation_message
               3. INSERT participant records to ai.conversation_participant
               4. INSERT summary records to ai.conversation_summary
               5. Update ai.conversation_archive.restored_at
               6. Set conversation status to 'archived' (read-only)
            -> Notify user via WebSocket/webhook when restore completes

    SLA: Restore complete within 5 minutes (expedited retrieval).

    Recovery states exposed via API:

        GET /conversations/{id}/recovery-status
        {
            "conversation_id": "uuid",
            "status": "archived",
            "archive_location": "s3://bucket/conversations/2026/01/uuid.json.gz",
            "recovery_status": "not_requested" | "in_progress" | "completed" | "failed",
            "recovery_requested_at": null,
            "recovery_completed_at": null,
            "estimated_completion": null
        }

Trade-off: Expedited retrieval costs more ($0.03/GB vs $0.00099/GB for standard).
We default to expedited for user-facing restore requests (5-minute SLA) and use
standard retrieval for internal prefetch or batch operations. The cost is
negligible because archive sizes are small (typically < 10MB per conversation).

---

## 6.13 Conversation Replay

Conversation replay is used for debugging, model evaluation, and training data
generation. It replays messages through the agent pipeline without side effects.

    Replay Process:

        1. Replay is triggered with a conversation_id and an optional
           replay_mode flag.
        2. Messages are read from ai.conversation_message in chronological order.
        3. Each message is fed through the agent pipeline (intent classification,
           context assembly, LLM call, tool execution) with side-effect isolation:
               - Tool executions are mocked or run in dry-run mode
               - LLM calls use a replay-optimized model (same temperature, seed)
               - No messages are written to the database
               - No external API calls (webhooks, emails) are executed
        4. Replay output (intermediate states, final response, latency, token
           usage) is stored in ai.conversation_replay_result.

    CREATE TABLE ai.conversation_replay_result (
        replay_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        conversation_id   UUID NOT NULL,
        replay_mode       TEXT NOT NULL,
                            -- 'debug', 'evaluation', 'training'
        replay_version    TEXT NOT NULL,
                            -- system version at time of replay
        input_messages    JSONB NOT NULL,
                            -- snapshot of messages replayed
        output            JSONB NOT NULL,
                            -- full replay output pipeline
        metrics           JSONB NOT NULL,
                            -- latency, tokens, cost per step
        status            TEXT NOT NULL DEFAULT 'completed',
        error             TEXT,
        created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE INDEX ix_conversation_replay_conv_id
        ON ai.conversation_replay_result (conversation_id);

replay_mode:

    debug      - Triggered by developer in admin UI. Full pipeline trace output.
    evaluation - Batch evaluation of model behavior. Aggregated metrics only.
    training   - Training data generation. Output is converted to training
                 format and stored separately.

Trade-off: Replay stores the full input and output as JSONB snapshots, which
can be large (multi-MB per replay). This is acceptable because:
    1. Replay is an infrequent operation (developer/debug tool).
    2. The data is invaluable for debugging regressions and improving models.
    3. Old replay results are pruned after 90 days.

---

## 6.14 Conversation Versioning

Conversation versioning follows an append-only immutable message log pattern
with optimistic concurrency at the aggregate level.

    Message Level (immutable append-only):
        Messages are NEVER updated or deleted. Once written, a message is
        immutable. This preserves the conversation history as an accurate
        record of what was said.
        
        If a message needs to be retracted (e.g., PII detected post-hoc):
            - A new message with role='system' is appended, referencing the
              original message_id in metadata.retracts_message_id.
            - The original message remains in the database, flagged in a
              separate mechanism for read-time filtering.

    Aggregate Level (optimistic concurrency):
        The conversation row uses a version column (BIGINT) for optimistic
        locking (see section 4.5). This protects against concurrent state
        transitions (e.g., two messages appended simultaneously to the same
        conversation).

    State Transition Audit:
        ai.conversation_state_history tracks every state transition with
        before/after snapshots for full audit trail.

    CREATE TABLE ai.conversation_state_history (
        history_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        conversation_id   UUID NOT NULL REFERENCES ai.conversation(conversation_id),
        before_status     TEXT NOT NULL,
        after_status      TEXT NOT NULL,
        before_snapshot   JSONB,
                            -- snapshot of relevant conversation columns
        after_snapshot    JSONB,
        triggered_by      TEXT NOT NULL,
                            -- 'system', 'user:{id}', 'timeout', 'admin:{id}'
        metadata          JSONB,
        created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE INDEX ix_conversation_state_history_conv_id
        ON ai.conversation_state_history (conversation_id, created_at);

Rationale for no explicit message versioning:

    - Messages are append-only, so there is no version to track. Each message
      is a unique, immutable row.
    - If message editing is required in the future, a new message_type
      (e.g., 'edited') can be introduced with a references_message_id field.
      The original message remains unmodified.
    - This is the event-sourcing pattern applied at the message level: the
      message log is the source of truth, and current state is derived by
      replaying the log.

---

## 6.15 Long Conversation Strategy

When a conversation exceeds the model's context window, we use a sliding window
with compressed summaries.

    Strategy:

        For a model with context window C tokens:
            - Keep last N messages in full detail (N configurable per model,
              default 20). These are the messages that fit within the context
              window with room for system prompt and tool definitions.
            - Compress earlier messages into an LLM-generated summary.
            - Strategy: truncate middle, preserve first + last messages.
        
        Example with N=20:
            Messages: [1, 2, 3, ..., 50]
                     ^--- First 3 messages preserved (greeting, intent, first response)
                              ^--- Messages 4-30 compressed into summary
                                        ^--- Last 20 messages kept in full (indices 31-50)

    Why preserve first messages:
        - The first messages establish the conversation's goal and context.
        - Greetings and intent classification are important for understanding
          what the user wanted.
        - The middle of the conversation typically contains back-and-forth
          clarification that can be effectively summarized.

    Summary Storage:

    CREATE TABLE ai.conversation_summary (
        summary_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        conversation_id    UUID NOT NULL REFERENCES ai.conversation(conversation_id),
        summary_text       TEXT NOT NULL,
        covered_message_ids UUID[] NOT NULL,
                             -- which messages this summary covers
        model              VARCHAR(255) NOT NULL,
        tokens             INTEGER NOT NULL,
        version            INTEGER NOT NULL DEFAULT 1,
        is_active          BOOLEAN NOT NULL DEFAULT true,
        created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE INDEX ix_conversation_summary_conv_id_active
        ON ai.conversation_summary (conversation_id, is_active);

    Regeneration Trigger:
        Summary is regenerated when the conversation grows by M messages
        (default 10) since the last summary. The new summary replaces the
        previous one (is_active = false on old, true on new).

    Context Assembly for LLM:

        {system_prompt}
        {tool_definitions}
        
        [Previous Conversation Context]
        {summary_text}     -- compressed summary of messages 1..N-M-1
        
        [Recent Messages]
        user: ...
        assistant: ...
        ... (last N messages in full)

    N and M Configuration:

        Model              Context Window   N    M
        ───────────────────────────────────────────
        gpt-4o             128K tokens     20   10
        claude-3-opus      200K tokens     30   15
        claude-3-haiku     48K tokens      15    8
        gemini-1.5-pro     1M tokens       50   25

Trade-off: Summary compression loses fidelity. The LLM may miss subtle details
in the summarized portion. We mitigate this by:
    1. Keeping the last N messages intact (high recency).
    2. Preserving the first messages (high importance).
    3. Regenerating summaries frequently (every M messages), so the compressed
       portion is never very large.
    4. Allowing the user to request the full conversation (from PG storage)
       if context from earlier messages is needed.

---

## 6.16 Compression Strategy

Four-tier compression strategy for conversation data, each tier optimized for
its access pattern.

    Compression Tiers:

      Tier 1: In-Memory (Redis)
      ┌─────────────────────────────────────────────────────────┐
      │  Redis key: conversation:{id}:recent                      │
      │  Type: List (capped, LTRIM)                               │
      │  Capacity: last 20 messages (configurable)                │
      │  TTL: 1h sliding (extended on every message append)       │
      │  Purpose: sub-millisecond context hydration for active    │
      │  conversations                                             │
      │  Trade-off: Ephemeral — lost on Redis restart if not     │
      │  flushed. Acceptable because PG is the system of record. │
      └─────────────────────────────────────────────────────────┘
                            │
                            │ Async flush (batched, < 1s latency)
                            ▼
      Tier 2: PostgreSQL (Warm)
      ┌─────────────────────────────────────────────────────────┐
      │  Table: ai.conversation_message                           │
      │  Partitioned BY RANGE (created_at) — monthly partitions   │
      │  Retention: up to 365 days of full message history        │
      │  Purpose: full-text search, replay, re-summarization,    │
      │  compliance export                                         │
      │  Trade-off: Write-amplification from indexes. Acceptable │
      │  because partition pruning keeps index maintenance local.│
      └─────────────────────────────────────────────────────────┘
                            │
                            │ LLM summary generation (every M=10 messages)
                            ▼
      Tier 3: LLM Summary (Hot)
      ┌─────────────────────────────────────────────────────────┐
      │  Table: ai.conversation_summary                           │
      │  Capacity: one active summary per conversation            │
      │  Also cached in Redis: summary:{id} (1h TTL)             │
      │  Purpose: context window optimization — compressed       │
      │  representation of older messages                         │
      │  Trade-off: Lossy compression. LLM summarization may     │
      │  miss details. Frequent regeneration limits data loss.   │
      └─────────────────────────────────────────────────────────┘
                            │
                            │ Celery cleanup_worker (after 365d inactive)
                            ▼
      Tier 4: Cold Archive (S3 Glacier)
      ┌─────────────────────────────────────────────────────────┐
      │  Storage: S3 Glacier / Azure Archive Blob                │
      │  Format: gzipped JSON (archive format in 6.11)           │
      │  Cost: ~$0.00099/GB/month (vs ~$0.115/GB/month for PG)  │
      │  Retrieval: 1-12 hours standard, 5 min expedited        │
      │  Purpose: compliance retention, regulatory access        │
      │  Trade-off: High latency to access. Acceptable because   │
      │  archived conversations are rarely accessed (< 1% rate). │
      └─────────────────────────────────────────────────────────┘

    Compression Flow Diagram:

        ┌──────────────┐
        │ User sends   │
        │ message      │
        └──────┬───────┘
               │
               ▼
        ┌───────────────────────────────────────────────────┐
        │ 1. Append to Redis List (Tier 1)                   │
        │    LPUSH conversation:{id}:recent {message_json}  │
        │    LTRIM conversation:{id}:recent 0 19            │
        │    EXPIRE conversation:{id}:recent 3600           │
        └──────────────────────┬────────────────────────────┘
               │
               ├──────────────── Async ────────────────►
               │                                          │
               ▼                                          ▼
        ┌──────────────────┐                     ┌──────────────────────┐
        │ 2a. Insert to PG │                     │ 2b. Check summary    │
        │    (immediate    │                     │     threshold        │
        │     for ack)     │                     │     msg_count % 10  │
        └──────────────────┘                     │     == 0?            │
                                                 └──────────┬───────────┘
                                                            │
                                                            ▼
                                                 ┌──────────────────────┐
                                                 │ 3. Generate new      │
                                                 │    LLM summary       │
                                                 │    (Tier 3)          │
                                                 │    INSERT to         │
                                                 │    conversation_     │
                                                 │    summary           │
                                                 │    SET old           │
                                                 │    is_active=false   │
                                                 │    SET Redis         │
                                                 │    summary:{id}      │
                                                 └──────────────────────┘

    Celery cleanup_worker:
        Daily, queries conversations with last_activity_at < 365 days
        -> Serialize to compressed JSON
        -> Upload to S3 Glacier (Tier 4)
        -> Update status to 'archived'
        -> Record in ai.conversation_archive

    Cost Comparison (per conversation, estimated):

        Tier     Storage    Cost/GB/mo    Size/conversation    Cost/conversation/mo
        ──────────────────────────────────────────────────────────────────────────
        Redis    Memory     $1.50/GB      ~50KB (20 msgs)      $0.000075
        PG       SSD        $0.115/GB     ~500KB (500 msgs)    $0.0000575
        PG       SSD        $0.115/GB     ~5KB (summary)       $0.000000575
        Glacier  Tape       $0.00099/GB   ~100KB (compressed)  $0.000000099

    At 100,000 conversations/month:
        Redis:   $7.50/mo
        PG:      $5.75/mo (messages + summaries)
        Glacier: $0.01/mo
        Total:   ~$13.26/mo

Trade-off summary across all four tiers:

    - Redis (Tier 1) is the most expensive per-GB but provides the latency
      (sub-ms) required for real-time conversation. We minimize cost by keeping
      only the last 20 messages and using a 1h TTL.
    - PostgreSQL (Tier 2) is the most flexible and queryable. Full-text search,
      replay, and analytics all depend on complete PG data. The cost is
      moderate and justified by the query capabilities.
    - LLM Summary (Tier 3) is a novel compression layer unique to LLM
      applications. It enables context window management that would otherwise
      be impossible. The compression ratio is extreme (500 messages -> 1
      summary of ~200 tokens, a 100:1+ compression ratio), but lossy.
    - S3 Glacier (Tier 4) is the cheapest option by far but has the highest
      latency and no query capability. It is only used for compliance-driven
      retention where access frequency is near zero.





# 7. Memory Persistence

## 7.1 Memory Architecture Overview

Memory persistence is a multi-tier pipeline: raw conversation content is processed by the LLM to extract structured facts, staged in short-term Redis cache, confirmed by policy (auto-commit or user-approval), stored durably in PostgreSQL, embedded for vector search, and finally assembled into context for future LLM calls.

    Memory Architecture Flow:

        User Message
            |
            v
        LLM Extraction Pipeline
        (prompt: extract facts from conversation)
            |
            v
        Short-Term Memory (Redis)
        key: memory:{user_id}:session:{session_id}
        TTL: 24h
            |
            v
        Confirmation Policy
        +-- confidence > 0.9  --> auto-commit
        +-- confidence 0.7-0.9 --> stage for user confirmation
        +-- confidence < 0.7  --> prompt user or discard
            |
            v
        Long-Term Memory (PostgreSQL)
        table: ai.long_term_memory
        columns: memory_id, user_id, conversation_id,
                 field_name, field_value, confidence,
                 source, context, version, status, timestamps
            |
            v
        Embedding Generation (Celery task)
        model: text-embedding-3-large (1536d)
        target: vector.memory_embedding
            |
            v
        Vector Search (pgvector, HNSW index)
        query: cosine similarity to current conversation
            |
            v
        Context Assembly
        MemoryService.assemble_context(user_id, query)
        ranks memories by recency, confidence, relevance, priority
            |
            v
        LLM Call with Enriched Context

## 7.2 Profile Memory

Stores explicit user-provided information that rarely changes. This is the user's identity and static attributes.

| Attribute | Detail |
|-----------|--------|
| Storage | ai.user_profile (part of UserProfile aggregate) |
| Content | Name, timezone, language, contact info, avatar |
| Source | User profile settings page or explicit "remember this" commands |
| Cache | Redis key: identity:{user_id} |
| Cache TTL | 6 hours (invalidated on profile update) |
| Lifespan | Permanent (never expires) |
| Mutation | Rare — only on explicit user edit |
| Read path | Identity middleware reads from Redis, falls back to PG |
| Consistency | Strong (write-through to PG, async cache invalidation) |

## 7.3 Preference Memory

Stores dynamic user settings and preferences that control service behavior.

| Attribute | Detail |
|-----------|--------|
| Storage | ai.user_preference (key-value pairs with JSON schema validation) |
| Content | Notification prefs, theme, communication style, meeting availability windows |
| Source | Preference management UI or LLM-initiated updates with user confirmation |
| Cache | Redis key: user:{id}:preferences |
| Cache TTL | 1 hour (invalidated on preference change) |
| Schema | preference_key TEXT, preference_value JSONB, schema_version INT |
| Validation | JSON Schema per key (enforced at repository layer) |
| Mutation | Moderate frequency — updated via UI or confirmed LLM suggestions |

## 7.4 Semantic Memory (Learned Facts)

The core of the AI's learning capability. Facts are extracted from conversations and stored with confidence scores, versioning, and lifecycle management.

Table: ai.long_term_memory

| Column | Type | Description |
|--------|------|-------------|
| memory_id | UUID PK | Unique identifier |
| user_id | UUID NOT NULL FK | Owner of this memory |
| conversation_id | UUID | Source conversation where fact was extracted |
| field_name | TEXT NOT NULL | Semantic field (e.g., job_title, company, goal) |
| field_value | TEXT NOT NULL | Extracted value |
| confidence | FLOAT NOT NULL DEFAULT 0.5 | LLM-assigned confidence 0.0-1.0 |
| source | TEXT | Extraction method (llm_extract, user_provided, import) |
| context | TEXT | Surrounding conversation context (why this was learned) |
| version | INT NOT NULL DEFAULT 1 | Incremented on merge or update |
| status | TEXT NOT NULL DEFAULT 'pending' | pending, confirmed, rejected, expired, superseded |
| tenant_id | UUID | Multi-tenant isolation (future) |
| created_at | TIMESTAMPTZ NOT NULL | When fact was first recorded |
| updated_at | TIMESTAMPTZ NOT NULL | Last modification timestamp |

Memory Extraction and Commitment Flow:

    Conversation Message
        |
        v
    MemoryExtractionService.extract(message)
        |  -- calls LLM with structured extraction prompt
        |  -- returns list of {field_name, field_value, confidence, context}
        v
    MemoryStagingService.stage(extracted_facts)
        |  -- writes to Redis staging area: memory:{user_id}:staging
        |  -- sets short TTL (15 minutes) awaiting confirmation
        v
    ConfirmationPolicy.evaluate(fact)
        |
        +-- confidence > 0.9  --> auto-commit
        |       v
        |   MemoryCommitService.commit(fact)
        |       |  -- INSERT or UPDATE in ai.long_term_memory
        |       |  -- trigger embedding generation
        |       v
        |   EmbeddingWorker.generate(memory_id)
        |
        +-- confidence 0.7-0.9 --> stage for confirmation
        |       v
        |   NotificationService.ask_user(fact)
        |       |  -- "I noticed you mentioned working at Acme Corp.
        |       |     Should I remember that?"
        |       v
        |   User response: yes --> commit
        |   User response: no  --> discard (status=rejected)
        |
        +-- confidence < 0.7 --> prompt or discard
                v
            if field_policy requires_high_confidence:
                discard silently
            else:
                prompt user with low-confidence indicator

## 7.5 Conversation Summary

LLM-generated summary of each conversation stored separately from raw messages. Feeds into context assembly for future conversations.

Table: ai.conversation_summary

| Column | Type | Description |
|--------|------|-------------|
| summary_id | UUID PK | Unique identifier |
| conversation_id | UUID NOT NULL FK | Source conversation |
| summary_text | TEXT | LLM-generated natural language summary |
| key_points | JSONB | Array of extracted key points as structured objects |
| token_count | INT | Total tokens in the summary |
| model_used | TEXT | LLM model that generated the summary |
| created_at | TIMESTAMPTZ | Generation timestamp |

| Attribute | Detail |
|-----------|--------|
| Generation trigger | On conversation close or periodic (every 50 messages) |
| Retention | 365 days in PG, then archived to S3 Glacier |
| Cache | Redis key: summary:{conversation_id} (TTL: 7 days) |
| Regeneration | On demand or when conversation is reopened after summary expiry |

## 7.6 Meeting History

Meetings are not stored as separate memory entries. They are referenced via meeting_id in conversation context. Relevant outcomes and decisions are extracted into semantic memory.

| Attribute | Detail |
|-----------|--------|
| Storage | ai.meeting aggregate (see domain model) |
| Memory extraction | On meeting close, MemoryExtractionService extracts decisions |
| Context assembly | Meeting title, date, participants, and outcomes injected via meeting_id lookup |
| Example extraction | "User decided to use Stripe for payments" -> memory field: decision_payment_processor |

## 7.7 Lead History

Similar to Meeting History. Leads are referenced by lead_id. Key attributes extracted into semantic memory.

| Attribute | Detail |
|-----------|--------|
| Storage | ai.lead aggregate |
| Memory extraction | On lead stage change, key attributes extracted |
| Context assembly | Lead name, company, stage, notes injected via lead_id lookup |
| Example extraction | "User is negotiating with John from Acme Corp" -> memory: relationship:acme_corp |

## 7.8 Memory Confidence

Confidence scores govern the auto-commit and staging behavior. Scores are recalculated by the Celery memory_worker.

| Score Range | Policy | Action |
|-------------|--------|--------|
| > 0.9 | High confidence | Auto-commit without user prompt |
| 0.7 - 0.9 | Medium confidence | Stage for user confirmation |
| < 0.7 | Low confidence | Prompt user or discard per field policy |

Confidence Adjustment Rules:

| Event | Adjustment |
|-------|------------|
| Corroboration from another source | +0.1 (max 1.0) |
| Contradiction from another source | -0.2 (min 0.0) |
| User explicitly confirms | +0.2 (max 1.0) |
| User explicitly rejects | Reset to 0.0, status=rejected |
| LLM re-evaluation (periodic) | Recalculated by extraction pipeline |
| Time decay (no corroboration in 90 days) | -0.05 per 30 days |

Recalculation is handled by Celery task:

    @celery.task(name="recalculate_confidence")
    def recalculate_confidence(memory_id: UUID) -> None:
        memory = MemoryRepository.load(memory_id)
        corroborations = MemoryRepository.count_corroborations(
            user_id=memory.user_id,
            field_name=memory.field_name,
            field_value=memory.field_value,
            exclude_memory_id=memory.memory_id
        )
        contradictions = MemoryRepository.count_contradictions(
            user_id=memory.user_id,
            field_name=memory.field_name,
            field_value=memory.field_value,
            exclude_memory_id=memory.memory_id
        )
        adjustment = (corroborations * 0.1) - (contradictions * 0.2)
        memory.confidence = min(1.0, max(0.0, memory.confidence + adjustment))
        MemoryRepository.save(memory)

## 7.9 Memory Ranking

When assembling context for the LLM, memories are ranked to select the most relevant subset. Ranking is done at query time in the application layer.

Ranking Criteria (weighted scoring):

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Recency | 0.25 | Newer memories ranked higher. Score = days_since_update / 365 |
| Confidence | 0.30 | Higher confidence ranked higher. Score = confidence |
| Relevance | 0.35 | Vector cosine similarity to current query. Score = similarity(embedding, query_embedding) |
| Field Priority | 0.10 | Configured per field type (e.g., name: 1.0, timezone: 0.9, preference: 0.5) |

    class MemoryService:
        def rank_memories(
            self,
            memories: List[LongTermMemory],
            query: str,
            field_priorities: Dict[str, float]
        ) -> List[ScoredMemory]:
            query_embedding = self.embedding_service.embed(query)
            scored = []
            for m in memories:
                recency_score = 1.0 - (
                    (datetime.utcnow() - m.updated_at).days / 365.0
                )
                relevance_score = cosine_similarity(
                    m.embedding, query_embedding
                )
                priority_score = field_priorities.get(
                    m.field_name, 0.5
                )
                total = (
                    0.25 * recency_score +
                    0.30 * m.confidence +
                    0.35 * relevance_score +
                    0.10 * priority_score
                )
                scored.append(ScoredMemory(memory=m, score=total))
            return sorted(scored, key=lambda x: x.score, reverse=True)[:20]

Selection: Top 20 scored memories are included in the LLM context window.

## 7.10 Memory Merge

When two memory entries exist for the same field (e.g., "company" extracted from two different conversations), the merge service resolves the conflict.

| Condition | Resolution |
|-----------|------------|
| Confidence difference < 0.2 | Newer timestamp wins |
| Confidence difference > 0.2 | Higher confidence wins |
| User explicitly corrected | User value wins (confidence set to 1.0) |
| Both from same conversation | First extraction kept, second discarded as duplicate |

Merge is a domain service, not a DB operation:

    class MemoryMergeService:
        def merge(
            self,
            existing: LongTermMemory,
            incoming: LongTermMemory
        ) -> MergeResult:
            if abs(existing.confidence - incoming.confidence) < 0.2:
                winner = max(existing, incoming, key=lambda m: m.updated_at)
            else:
                winner = max(existing, incoming, key=lambda m: m.confidence)
            loser = incoming if winner == existing else existing
            loser.status = MemoryStatus.SUPERSEDED
            winner.version += 1
            return MergeResult(winner=winner, loser=loser)

## 7.11 Memory Compression

For users with extensive memory profiles (default threshold: 50 entries), low-confidence or old memories are compressed into a single "historical context" entry.

| Attribute | Detail |
|-----------|--------|
| Trigger | memory_worker Celery task, runs daily |
| Threshold | 50 entries per user (configurable per tenant) |
| Selection | Entries with confidence < 0.3 OR updated_at > 180 days |
| Compression | LLM summarizes selected entries into a single JSON context block |
| Storage | Single entry in ai.long_term_memory with field_name='historical_context' |
| Traceability | Compressed entry links to original memory_ids via JSONB reference list |
| Original entries | Soft-deleted (status=superseded) after compression |

## 7.12 Memory Expiration

Memory entries expire based on field type classification. Expiration is a domain policy enforced by the Celery cleanup_worker.

| Classification | Field Types | TTL | Example |
|----------------|-------------|-----|---------|
| Permanent | name, timezone, language | Never | name = "Alice" |
| Long-term | preferences, goals, important_facts | 1 year | goal = "Raise Series A" |
| Medium | contextual_facts, interests | 90 days | interest = "learning Rust" |
| Short-term | transient_context, session_state | 7 days | current_project = "debugging X" |
| Session | conversation_context | 24h (Redis only) | last_topic = "meeting scheduling" |

Cleanup Worker Flow:

    @celery.task(name="expire_memories")
    def expire_memories():
        policies = ExpirationPolicyRepository.load_all()
        for policy in policies:
            cutoff = datetime.utcnow() - timedelta(days=policy.ttl_days)
            expired = MemoryRepository.find_expired(
                field_classification=policy.classification,
                cutoff=cutoff
            )
            for memory in expired:
                memory.status = MemoryStatus.EXPIRED
                MemoryRepository.save(memory)

Safety window: Expired entries are retained for 30 days after status=expired before archiving. During this window, an admin can restore the entry.

## 7.13 Memory Archive

After the expiration safety window elapses, entries are moved to cold storage.

| Attribute | Detail |
|-----------|--------|
| Target table | ai.memory_archive |
| Archive format | JSON blob per user containing all expired memory entries with metadata |
| Trigger | cleanup_worker Celery task, runs monthly |
| Source deletion | After archive confirmed, source rows are hard-deleted from ai.long_term_memory |
| Recovery | Full profile restore or selective field-type restore |

Archive table: ai.memory_archive

| Column | Type | Description |
|--------|------|-------------|
| archive_id | UUID PK | Unique archive batch identifier |
| user_id | UUID NOT NULL | Owner of archived memories |
| tenant_id | UUID | Tenant isolation (future) |
| archive_data | JSONB | Complete memory entries for this user |
| entry_count | INT | Number of memory entries in this archive |
| archived_at | TIMESTAMPTZ | Archive creation timestamp |
| retention_until | TIMESTAMPTZ | After this date, archive may be deleted |

## 7.14 Memory Recovery

Full or partial restoration of archived memory entries.

| Recovery Type | Description | Trigger |
|---------------|-------------|---------|
| Full recovery | Load all archived entries, reassign memory_ids, reset confidence to 0, set status=pending | User returns after > 1 year absence |
| Partial recovery | Load specific field types only | Admin API request |

Recovery behavior:

    Status transition: archived -> pending (all entries)
    Confidence reset: all entries set to 0.0 (requires re-confirmation)
    memory_id reassignment: new UUIDs generated
    version reset: set to 1
    source annotation: original_archive_id stored in context field

## 7.15 Memory Ownership

| Principle | Implementation |
|-----------|----------------|
| Ownership | Every memory entry is owned by user_id (FK to user) |
| Multi-tenant | tenant_id column on every memory entry (future enforcement) |
| Cross-user sharing | Not supported. Privacy-first design |
| User deletion | DELETE /users/{id}/memory cascades all user memory (GDPR) |
| Admin deletion | DELETE /admin/users/{id}/memory for abuse handling |
| Audit | All deletion events logged to audit.audit_log |

## 7.16 Conflict Resolution

When extracted facts contradict existing memory, a domain service evaluates and resolves the conflict.

    class MemoryConflictResolver:
        def resolve(
            self,
            existing: LongTermMemory,
            incoming: LongTermMemory
        ) -> ConflictResolution:
            if incoming.confidence > existing.confidence + 0.15:
                # Incoming is significantly more confident
                return ConflictResolution(
                    action=ResolutionAction.REPLACE,
                    winner=incoming,
                    reason="incoming_confidence_higher"
                )
            elif existing.confidence > incoming.confidence + 0.15:
                # Existing is significantly more confident
                return ConflictResolution(
                    action=ResolutionAction.KEEP,
                    winner=existing,
                    reason="existing_confidence_higher"
                )
            else:
                # Close confidence — defer to user
                return ConflictResolution(
                    action=ResolutionAction.DEFER_TO_USER,
                    winner=None,
                    reason="confidence_tie"
                )

Conflict Log: ai.memory_conflict_log

| Column | Type | Description |
|--------|------|-------------|
| conflict_id | UUID PK | Unique identifier |
| user_id | UUID | Owner |
| existing_memory_id | UUID | Existing memory entry |
| incoming_memory_id | UUID | New memory entry that triggered conflict |
| resolution | TEXT | replace, keep, user_resolved |
| resolved_by | UUID | User or admin who resolved (NULL if automatic) |
| resolved_at | TIMESTAMPTZ | Resolution timestamp |

## 7.17 Long-Term Memory vs Redis Session Memory

| Aspect | Redis Session Memory | PostgreSQL Long-Term Memory |
|--------|----------------------|-----------------------------|
| Role | Working set (hot cache) | Permanent store (source of truth) |
| Key/Table | memory:{user_id}:context | ai.long_term_memory |
| Data type | JSON string (serialized) | Normalized rows |
| TTL | 2 hours (extended on activity) | Per retention policy (permanent to 90 days) |
| Populated | Rebuilt from PG on conversation start | Written by MemoryCommitService |
| Expiration | After 2h inactivity: auto-evicted | Per field-type expiration policy |
| Consistency | Eventual (rebuildable from PG) | Strong (ACID) |
| Indexing | None (full read on load) | B-tree + pgvector (HNSW) |
| Versioning | No (current snapshot only) | Full version history (version column) |
| Search | Key lookup only | Vector similarity, field queries |
| Recovery | Rebuild from PG | PITR, WAL, archive restore |
| Capacity | Limited to hot working set (~1MB per user) | Unlimited (partitioned, archived) |

Rebuild flow on conversation start:

    def rebuild_redis_context(user_id: UUID) -> None:
        active_memories = MemoryRepository.find_active(user_id)
        ranked = MemoryService.rank_memories(
            active_memories,
            query="",
            field_priorities=DEFAULT_PRIORITIES
        )
        serialized = MemorySerializer.serialize_context(ranked[:50])
        redis.setex(
            f"memory:{user_id}:context",
            7200,  # 2 hour TTL
            serialized
        )




# 8. pgvector Strategy

## 8.1 Embedding Ownership

Three embedding types exist in the system, each owned by a different aggregate:

| Embedding Type | Owner Aggregate | Table | Persistence |
|---|---|---|---|
| Document embedding | KnowledgeDocument | ai.document_embedding | Persistent |
| Memory embedding | Memory | ai.memory_embedding | Persistent |
| Query embedding | SearchService (transient) | None | In-memory only |

Design rationale — embedding ownership follows aggregate boundaries because:

- Knowledge documents and memories have fundamentally different lifecycles. Documents are
  uploaded once, updated occasionally, and retained indefinitely. Memories are written and
  rewritten frequently and expire via TTL. If embeddings were stored in a single polymorphic
  table (source_type + source_id), retention policies, indexing strategies, and access
  patterns would conflate two unrelated concerns into one table.
- Documents are searched across a tenant (all documents visible to all users in the
  organization). Memories are searched per user (my memories only). A shared embeddings
  table would require source_type + source_id + user_id filtering on every query, while
  separate tables allow table-level security (RLS) tailored to each access pattern.
- Document chunks have different embedding granularity (multiple chunks per document with
  overlap) vs memories (one embedding per memory field). A shared table would need nullable
  chunk_id and flexible metadata, compromising schema clarity.
- Query embeddings are never persisted because they are ephemeral search artifacts. Storing
  them would create unbounded storage growth with zero reuse value (queries are unique or
  cached at the application level). The embedding API result is cached by text hash in Redis
  (embedding cache, section 5.9) to avoid redundant API calls for identical query text.

Trade-off: Separate tables means duplicate schema for columns (model, dimension, vector,
metadata, created_at, version). This duplication is acceptable because:
- It avoids a polymorphic source_type discriminator that would complicate foreign keys and
  constraint enforcement.
- It enables table-level RLS policies: documents are tenant-scoped, memories are user-scoped.
- It allows independent index tuning: document embeddings benefit from larger HNSW
  ef_construction for higher recall; memory embeddings prioritize smaller index size for
  faster writes.
- The schemas are small enough (approximately 10 columns each) that maintenance cost is
  negligible.

## 8.2 Embedding Storage

Table: ai.document_embedding

    CREATE TABLE ai.document_embedding (
        embedding_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        document_id     UUID NOT NULL REFERENCES ai.document_document(document_id),
        chunk_id        UUID NOT NULL REFERENCES ai.document_chunk(chunk_id),
        model           VARCHAR(64) NOT NULL DEFAULT 'text-embedding-3-large',
        dimension       INTEGER NOT NULL DEFAULT 1536,
        vector          vector(3072),              -- max dimension across all models
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
        version         INTEGER NOT NULL DEFAULT 1
    );

    CREATE INDEX idx_document_embedding_document ON ai.document_embedding (document_id);
    CREATE INDEX idx_document_embedding_chunk ON ai.document_embedding (chunk_id);
    CREATE INDEX idx_document_embedding_model ON ai.document_embedding (model);
    CREATE INDEX idx_document_embedding_metadata ON ai.document_embedding USING GIN (metadata);

Table: ai.memory_embedding

    CREATE TABLE ai.memory_embedding (
        embedding_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        memory_id       UUID NOT NULL REFERENCES ai.memory(memory_id),
        model           VARCHAR(64) NOT NULL DEFAULT 'text-embedding-3-large',
        dimension       INTEGER NOT NULL DEFAULT 1536,
        vector          vector(3072),
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
        version         INTEGER NOT NULL DEFAULT 1
    );

    CREATE INDEX idx_memory_embedding_memory ON ai.memory_embedding (memory_id);
    CREATE INDEX idx_memory_embedding_model ON ai.memory_embedding (model);
    CREATE INDEX idx_memory_embedding_metadata ON ai.memory_embedding USING GIN (metadata);

Comparison of table design decisions:

| Aspect | ai.document_embedding | ai.memory_embedding |
|---|---|---|
| FK target | document_id + chunk_id | memory_id |
| Chunk granularity | Yes (chunk_id FK) | No (one embedding per memory field) |
| Retention model | Indefinite (documents are SOR) | TTL-based (memories expire) |
| Search scope | Tenant-wide (all documents) | Per-user (my memories) |
| Metadata schema | document_id, chunk_index, chunk_size, page_number, section_title, tags | user_id, field_name, conversation_id |
| Write frequency | On document upload/update | On every memory write (frequent) |
| Average rows per parent | 10-100 chunks per document | 1-3 embeddings per memory |
| HNSW index strategy | Larger ef_construction (500), higher recall priority | Smaller ef_construction (200), write throughput priority |

Trade-off: The vector column is declared as vector(3072) to accommodate the largest
embedding model (text-embedding-3-large at 3072 dimensions) even when smaller models are
used. This wastes storage for 1536-dimension vectors. The alternative — using vector()
without dimension constraint — is supported in pgvector 0.5+ but disables certain index
optimizations and dimension validation. We accept the overhead (approximately 6KB per row
for 1536-dim vectors stored in a 3072-dim column) because:
- The overhead is approximately 2x storage for 1536-dim vectors, which at typical scale
  (< 10 million embeddings) adds ~60GB — acceptable for an enterprise system.
- Dimension constraint provides type safety: a query written for 1536-dim vectors will
  fail at the database level if accidentally matched against 3072-dim vectors, preventing
  silent corruption of similarity search results.
- Future model upgrades (e.g., 3072-dim) require zero schema migration.

## 8.3 Embedding Metadata

JSONB metadata serves as the flexible filtering layer. Instead of adding a new column for
every filter criterion, metadata is a semi-structured document indexed by a GIN index.

Metadata schema per table:

Document embedding metadata:

    {
        "document_id": "uuid",
        "chunk_index": 3,
        "chunk_size": 512,
        "page_number": 7,
        "section_title": "Architecture Overview",
        "tags": ["technical", "architecture", "database"],
        "author_id": "uuid",
        "visibility": "team"
    }

Memory embedding metadata:

    {
        "user_id": "uuid",
        "field_name": "preferred_name",
        "conversation_id": "uuid",
        "confidence": 0.92,
        "source": "explicit"
    }

Query patterns:

    -- Filter by tag (GIN accelerated)
    SELECT * FROM ai.document_embedding
    WHERE metadata @> '{"tags": ["technical"]}';

    -- Filter by section and page range
    SELECT * FROM ai.document_embedding
    WHERE metadata @> '{"section_title": "Architecture Overview"}'
      AND (metadata->>'page_number')::int BETWEEN 5 AND 10;

    -- Filter by user and field for memory search
    SELECT * FROM ai.memory_embedding
    WHERE metadata @> '{"user_id": "abc-123", "field_name": "preferred_name"}';

Trade-off: JSONB metadata is less performant than native columns for equality filters
(GIN index vs B-tree index). However, metadata is inherently sparse — not every filter
applies to every query, and filter combinations are unpredictable. A GIN-indexed JSONB
column handles arbitrary filter combinations without schema changes. If a specific filter
becomes a hot path (e.g., user_id for memory embeddings), a dedicated B-tree index can
be added alongside the GIN index. The GIN index on metadata costs approximately 10-15%
additional write overhead, which is acceptable for the write volumes expected.

## 8.4 Chunk Metadata

Documents are too large to embed as a single vector. Chunking splits documents into
semantic segments, each embedded independently.

Table: ai.document_chunk

    CREATE TABLE ai.document_chunk (
        chunk_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        document_id     UUID NOT NULL REFERENCES ai.document_document(document_id),
        chunk_index     INTEGER NOT NULL,
        chunk_text      TEXT NOT NULL,
        chunk_size      INTEGER NOT NULL,          -- token count
        overlap_size    INTEGER NOT NULL DEFAULT 64, -- token count
        chunk_hash      VARCHAR(64) NOT NULL,       -- SHA-256 for dedup
        status          VARCHAR(20) NOT NULL DEFAULT 'active', -- active, superseded
        created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE (document_id, chunk_index, status)
    );

    CREATE INDEX idx_document_chunk_document ON ai.document_chunk (document_id);
    CREATE INDEX idx_document_chunk_hash ON ai.document_chunk (chunk_hash);

Chunking is the unit of embedding generation: each chunk generates one embedding vector.
Search retrieval returns chunk-level results, and the application assembles context from
the top-K matching chunks.

    Document Chunking + Embedding Pipeline:

        ┌──────────────┐
        │ Document     │
        │ (raw text)   │
        └──────┬───────┘
               │
               v
        ┌──────────────┐
        │ Text Splitter│
        │ (tokenizer)  │
        │              │
        │ chunk_size=512│
        │ overlap=64   │
        └──────┬───────┘
               │
               v
        ┌───────────────────────────────────────────────┐
        │ Generate Chunks                                │
        │                                               │
        │  Chunk 1 (tokens 0-511)   overlap 64 → Chunk 2│
        │  Chunk 2 (tokens 448-959)  overlap 64 → Chunk 3│
        │  Chunk 3 (tokens 896-1407) ...                 │
        └──────┬───────┬───────┬──────────────────────────┘
               │       │       │
               v       v       v
        ┌──────────┐┌──────────┐┌──────────┐
        │ Embed    ││ Embed    ││ Embed    │
        │ Chunk 1  ││ Chunk 2  ││ Chunk 3  │
        │ (API)    ││ (API)    ││ (API)    │
        └────┬─────┘└────┬─────┘└────┬─────┘
             │           │           │
             v           v           v
        ┌───────────────────────────────────────────────┐
        │ Persist to ai.document_embedding              │
        │                                               │
        │ embedding_id | chunk_id | vector | metadata   │
        │ UUID-1       | c1       | [...]  | {"tags"}   │
        │ UUID-2       | c2       | [...]  | {"tags"}   │
        │ UUID-3       | c3       | [...]  | {"tags"}   │
        └───────────────────────────────────────────────┘

Each chunk_hash is computed as SHA-256(chunk_text). On document re-upload, unchanged
chunks (same hash) are detected and their embeddings are reused, saving API costs.

## 8.5 Chunk Versioning

When a document is updated, its chunks are versioned to maintain consistency between
chunks and embeddings.

Versioning flow:

    1. User uploads new version of document (document_document.version incremented).
    2. New chunks are generated from the updated text.
    3. Old chunks are soft-deleted: UPDATE status = 'superseded'.
    4. New embeddings are generated for new chunks only.
    5. Search queries filter: WHERE status = 'active' AND version = :current_version.

    ┌──────────────┐         ┌──────────────────┐
    │ Document V1  │────────▶│ Chunks V1        │────────▶ Embeddings V1
    │ (version=1)  │         │ (status=active)   │
    └──────┬───────┘         └──────────────────┘
           │
           │ Update document
           v
    ┌──────────────┐         ┌──────────────────┐         ┌──────────────────┐
    │ Document V2  │────────▶│ Chunks V2        │────────▶│ Embeddings V2    │
    │ (version=2)  │         │ (status=active)   │         │ (new vectors)    │
    └──────────────┘         └──────────────────┘         └──────────────────┘
                                   │
                                   v
                             ┌──────────────────┐
                             │ Chunks V1        │
                             │ (status=superseded)│
                             └──────────────────┘

Trade-off: Soft-delete (status=superseded) instead of hard delete preserves the ability
to roll back to a previous document version. The cost is storage bloat from superseded
chunks. This is acceptable because:
- Documents are updated infrequently (avg 2-3 times over lifetime).
- Superseded chunks are tiny (512 tokens each).
- A cleanup job can hard-delete superseded chunks older than 90 days.

## 8.6 Embedding Versioning

Embedding models evolve. When upgrading from text-embedding-3-small (1536-dim) to
text-embedding-3-large (3072-dim), existing embeddings are not invalidated immediately.

Versioning rules:

- Each embedding row stores the model name and dimension that produced it.
- The HNSW index is per-vector-column — mixing dimensions requires separate indexes.
- On model upgrade: new embeddings are generated with the new model. Old embeddings
  remain searchable for backward compatibility.
- Search queries specify the model version they target. If no model is specified, the
  active model (from ai.embedding_model registry) is used.
- A Celery task `reindex_all_embeddings` handles full migration when the old model is
  retired.

    Embedding Evolution Timeline:

        t0: Model A active (text-embedding-3-small, 1536d)
            ┌─────────────────────────────┐
            │ All embeddings use Model A  │
            │ HNSW index for 1536d        │
            └─────────────────────────────┘

        t1: Model B released, set as active
            Model A marked deprecated
            ┌─────────────────────────────┐
            │ New embeddings → Model B    │
            │ Old embeddings → Model A    │
            │ Two HNSW indexes:           │
            │   ix_1536d (Model A)        │
            │   ix_3072d (Model B)        │
            └─────────────────────────────┘

        t2: Migration complete (reindex_all_embeddings)
            Model A retired
            ┌─────────────────────────────┐
            │ All embeddings → Model B    │
            │ ix_1536d dropped            │
            └─────────────────────────────┘

Trade-off: Maintaining two HNSW indexes during transition doubles index storage and
increases write amplification (every new embedding updates one index). This is acceptable
because:
- The transition window is finite (typically 1-7 days for full reindex).
- During transition, the system serves queries from both indexes and merges results.
- Index storage for 10M embeddings at 1536d is approximately 2GB per index; doubling to
  4GB for the transition window is negligible.

## 8.7 Model Version Strategy

A registry table tracks embedding model lifecycle.

Table: ai.embedding_model

    CREATE TABLE ai.embedding_model (
        model_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name            VARCHAR(128) NOT NULL UNIQUE,
        provider        VARCHAR(64) NOT NULL,           -- openai, anthropic, custom
        dimension       INTEGER NOT NULL,
        active          BOOLEAN NOT NULL DEFAULT false,
        deprecated_at   TIMESTAMPTZ,
        retired_at      TIMESTAMPTZ,
        created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
    );

Model lifecycle states:

| State | active | deprecated_at | retired_at | Searchable | Used for new embeddings |
|---|---|---|---|---|---|
| Active | true | NULL | NULL | Yes | Yes |
| Deprecated | false | set | NULL | Yes | No (warning logged) |
| Retired | false | set | set | No | No |

    Model State Machine:

        ┌──────────┐    schedule_release()    ┌──────────┐
        │ Planned  │─────────────────────────▶│ Active   │
        └──────────┘                          └────┬─────┘
                                                   │
                                              deprecate()
                                                   │
                                                   v
                                             ┌────────────┐
                                             │ Deprecated │
                                             └──────┬─────┘
                                                     │
                                                retire()
                                                     │
                                                     v
                                               ┌──────────┐
                                               │ Retired  │
                                               └──────────┘

When a model is deprecated:
- Search continues to work against its embeddings.
- A warning is added to search response headers (X-Model-Deprecated: text-embedding-3-small).
- The Celery task `reindex_all_embeddings` is automatically triggered for migration.

When a model is retired:
- Its HNSW index is dropped.
- Any remaining embeddings using that model are either migrated or deleted (configurable
  per embedding type: documents require migration, transient embeddings are deleted).

## 8.8 Embedding Refresh

Embeddings become stale when the source content changes. Refresh triggers are:

| Trigger | Scope | Action | Worker |
|---|---|---|---|
| Document content changes (document_document.updated_at) | Single document | Re-chunk + re-embed | Celery embedding_worker |
| Memory field updated (ai.memory.updated_at) | Single memory | Re-embed memory field | Celery embedding_worker |
| Model upgrade (embedding_model.deprecated_at set) | All embeddings of model | Full reindex | Celery reindex_worker |
| User requests reindex (admin API) | Specific document/user | Selective reindex | Celery embedding_worker |
| Scheduled refresh (Celery beat) | Modified in last 24h | Partial reindex | Celery embedding_worker |

Refresh flow:

    Trigger fires
        │
        v
    Enqueue Celery task (embedding_refresh)
        │
        v
    Read source entity (document/memory)
        │
        v
    [If document] Re-chunk text → generate new chunk IDs
        │
        v
    [If document] Store new chunks (ai.document_chunk)
        │
        v
    Call embedding API (model = active model from registry)
        │
        v
    Store new embedding (ai.document_embedding or ai.memory_embedding)
        │
        v
    [If document] Deprecate old chunks (status = superseded)
        │
        v
    Delete old embeddings for entity
        │
        v
    Commit transaction

Important: Refresh updates the embedding, not the chunk text. Chunk text is immutable
once written because it is the source text that the embedding represents. Changing chunk
text without re-embedding would create inconsistency (vector represents old text, chunk
stores new text). When document content changes, the entire chunking pipeline runs
again, producing new chunks with new chunk_ids. The old chunks remain as historical
records.

Change tracking relies on `document_document.updated_at`. A periodic Celery beat task
scans for documents where updated_at > last_refresh_at and enqueues refresh tasks.

Trade-off: Polling updated_at is simpler than change data capture (CDC) via pgoutput or
Debezium. At the expected scale (< 1000 document updates/day), polling every 5 minutes
creates negligible database load. If write volume grows, CDC via logical replication
would reduce latency and eliminate polling overhead.

## 8.9 Chunk Refresh

Chunk text changes only when the source document content changes. However, the chunk
strategy (chunk size, overlap percentage) may change independently of content changes.

Chunk strategy change scenarios:

- Performance tuning: increasing chunk size from 512 to 768 tokens to improve embedding
  quality at the cost of granularity.
- Model input limits: a new embedding model supports larger context (8192 tokens instead
  of 8191), allowing larger chunk sizes.
- Domain-specific tuning: code documentation benefits from smaller chunks (256 tokens)
  while prose documents benefit from larger chunks (1024 tokens).

Chunk refresh flow on strategy change:

    1. New chunk strategy parameters are stored in ai.chunk_strategy_config
       (document_type, chunk_size, overlap_size, active boolean).
    2. All documents of the affected type are re-chunked using the new strategy.
    3. New chunks are created with a new version number.
    4. Old chunks are deprecated (status = superseded).
    5. New embeddings are generated for all new chunks.
    6. Search queries filter WHERE version = :current_version.

    ┌────────────────────┐
    │ Strategy Change    │
    │ chunk_size: 512->768│
    │ overlap: 64->96    │
    └─────────┬──────────┘
              │
              v
    ┌────────────────────┐
    │ Re-chunk Document  │
    │ (new chunk_ids)    │
    └─────────┬──────────┘
              │
              v
    ┌────────────────────┐     ┌────────────────────┐
    │ Old Chunks V1      │     │ New Chunks V2      │
    │ status=superseded  │     │ status=active      │
    │ chunk_size=512     │     │ chunk_size=768     │
    └────────────────────┘     └─────────┬──────────┘
                                         │
                                         v
                                  ┌────────────────────┐
                                  │ Embed Chunks V2    │
                                  │ (new embeddings)   │
                                  └────────────────────┘

Trade-off: Re-chunking invalidates all existing embeddings for the document, even if the
text content is identical. This is expensive but unavoidable because the chunk boundaries
change (a token that was in chunk 5 may now be in chunk 4, changing the embedding context).
A hash-based dedup at the chunk level (chunk_hash) identifies identical chunks across
strategy changes, but in practice, different chunk sizes almost always produce different
chunk boundaries.

## 8.10 Re-index Strategy

Re-indexing regenerates embeddings for a set of source entities. Multiple strategies
exist for different use cases.

| Strategy | Cadence | Scope | Triggered by | Duration estimate (1M embeddings) |
|---|---|---|---|---|
| Full reindex | Monthly | All embeddings | Celery beat | 8-12 hours |
| Partial reindex | Hourly | Modified in last 24h | Celery beat | 5-15 minutes |
| On-demand | Manual | Specific document/user | Admin API | Seconds to minutes |

Full reindex flow:

    Celery Beat fires monthly_reindex task
        │
        v
    Create new embedding model version record (if model changed)
        │
        v
    For each document (batch of 100):
        ├── Read document text
        ├── Generate chunks (current strategy)
        ├── Compute chunk hashes
        ├── Compare with existing chunks (skip if hash unchanged)
        ├── Generate embeddings for new/changed chunks
        ├── Mark old embeddings as superseded
        └── Insert new embeddings (single transaction)
        │
        v
    After all documents complete:
        ├── Verify embedding counts match expected
        ├── Rebuild HNSW index (CONCURRENTLY if pgvector 0.7+)
        ├── Update embedding_model registry (mark migration complete)
        └── Send completion notification

Partial reindex flow:

    SELECT document_id FROM ai.document_document
    WHERE updated_at > now() - interval '24 hours'
      AND deleted_at IS NULL;
        │
        v
    For each modified document:
        ├── Re-chunk (only if chunk strategy unchanged)
        ├── Generate embeddings for new chunks
        └── Mark old chunk embeddings as superseded

Reindex runs in batches of 100 documents per Celery task to limit memory usage and
enable checkpointing. Task state is tracked in the Celery result backend (Redis) and
exposed via admin API for progress monitoring:

    GET /admin/embeddings/reindex/status
    Response:
    {
        "task_id": "uuid",
        "state": "PROGRESS",
        "total_documents": 50000,
        "completed": 12300,
        "failed": 3,
        "errors": ["document_id xyz: embedding API timeout"],
        "started_at": "2026-06-30T01:00:00Z",
        "estimated_completion": "2026-06-30T09:00:00Z"
    }

## 8.11 Deletion Strategy

Embedding deletion is driven by source entity lifecycle, not by independent cleanup.

| Trigger | Action | Mechanism |
|---|---|---|
| Document deleted (soft) | Mark associated chunks superseded, delete embeddings | Application layer |
| Document permanently deleted | Hard delete chunks and embeddings | Application layer |
| Memory entry deleted | Delete memory embedding | Application layer |
| Memory TTL expired | Delete memory embedding | Cleanup worker |
| Orphaned embedding detected | Delete embedding with no parent | Cleanup worker (daily) |

Deletion implementation — application layer, not DB CASCADE:

    class DocumentRepository:
        def delete(self, document_id: UUID) -> None:
            with self.db.transaction():
                # Soft-delete document
                self.db.execute("""
                    UPDATE ai.document_document
                    SET deleted_at = now(), deleted_by = :user
                    WHERE document_id = :id
                """, {"id": document_id, "user": current_user_id})

                # Soft-delete chunks
                self.db.execute("""
                    UPDATE ai.document_chunk
                    SET status = 'superseded'
                    WHERE document_id = :id AND status = 'active'
                """, {"id": document_id})

                # Delete embeddings (hard delete — no reason to keep)
                self.db.execute("""
                    DELETE FROM ai.document_embedding
                    WHERE document_id = :id
                """, {"id": document_id})

    class MemoryEmbeddingRepository:
        def delete_by_memory(self, memory_id: UUID) -> None:
            self.db.execute("""
                DELETE FROM ai.memory_embedding
                WHERE memory_id = :id
            """, {"id": memory_id})

Trade-off: Application-layer cascade instead of DB-level ON DELETE CASCADE provides:
- Explicit control: the domain logic decides whether to soft-delete or hard-delete based on
  source entity state (soft-deleted document → soft-delete chunks, permanent delete → hard
  delete embeddings).
- Audit trail: deletion is logged in the audit schema before DB operations execute.
- Rollback capability: if deletion fails mid-cascade (e.g., embedding API rate limit during
  cleanup), the transaction rolls back everything.
- Portability: application logic works identically regardless of whether FKs are enforced.

The cost is additional application code and the risk of orphaned embeddings if a parent is
deleted through a code path that bypasses the repository. To mitigate this, a daily cleanup
worker scans for orphaned embeddings:

    -- Orphaned document embeddings
    SELECT e.embedding_id
    FROM ai.document_embedding e
    LEFT JOIN ai.document_document d ON e.document_id = d.document_id
    WHERE d.document_id IS NULL;

    -- Orphaned memory embeddings
    SELECT e.embedding_id
    FROM ai.memory_embedding e
    LEFT JOIN ai.memory m ON e.memory_id = m.memory_id
    WHERE m.memory_id IS NULL;

## 8.12 Similarity Search

Vector similarity search uses pgvector distance operators.

| Operator | Distance Metric | Use Case | Normalization Required |
|---|---|---|---|
| <-> | Cosine distance | Semantic search (default) | Vectors normalized to unit length |
| <=> | L2/Euclidean distance | Dense retrieval, exact match | No |
| <#> | Inner product | Maximum inner product search | Vectors normalized to unit length |

Default configuration for semantic search:

    -- Cosine similarity search (default)
    SELECT
        e.embedding_id,
        e.document_id,
        e.chunk_id,
        c.chunk_text,
        1 - (e.vector <-> :query_vector) AS similarity
    FROM ai.document_embedding e
    JOIN ai.document_chunk c ON e.chunk_id = c.chunk_id
    JOIN ai.document_document d ON e.document_id = d.document_id
    WHERE d.deleted_at IS NULL
      AND c.status = 'active'
      AND d.version = :current_version
      AND 1 - (e.vector <-> :query_vector) >= :threshold
    ORDER BY e.vector <-> :query_vector
    LIMIT :limit;

Search parameters:

| Parameter | Default | Range | Description |
|---|---|---|---|
| threshold | 0.7 | 0.0 - 1.0 | Minimum similarity score |
| limit | 10 | 1 - 50 | Maximum results returned |
| distance | cosine | cosine, l2, ip | Distance metric |
| model_filter | current active | any model_id | Restrict to specific model |

HNSW index configuration:

    -- Document embeddings (recall-priority)
    CREATE INDEX idx_document_embedding_vector ON ai.document_embedding
    USING hnsw (vector vector_cosine_ops)
    WITH (m = 24, ef_construction = 500);

    -- Memory embeddings (write-priority)
    CREATE INDEX idx_memory_embedding_vector ON ai.memory_embedding
    USING hnsw (vector vector_cosine_ops)
    WITH (m = 16, ef_construction = 200);

| Index Parameter | Document | Memory | Trade-off |
|---|---|---|---|
| m (max connections) | 24 | 16 | Higher m = better recall, slower build, more memory |
| ef_construction | 500 | 200 | Higher ef = better recall, slower build |
| ef_search (query time) | 100-300 | 50-150 | Higher ef = better recall, slower query |

Trade-off: HNSW is chosen over IVFFlat because:
- HNSW provides faster query time at equivalent recall (10x faster at 99% recall).
- HNSW index build time is longer but build is offline or background.
- HNSW memory usage is higher (approximately 1.1x the vector data size vs 0.3x for IVFFlat)
  but at the scale of < 10M vectors, memory cost (~2GB for 1536d vectors) is acceptable.
- HNSW supports incremental inserts efficiently (no periodic rebuild needed).

## 8.13 Hybrid Search

Hybrid search combines vector similarity (semantic) with keyword matching (lexical) for
cases where exact keyword matches are important (e.g., searching for a specific product
name or code snippet).

    Hybrid Search Flow:

        User Query
            │
            v
        ┌──────────────────────────────────────────────────────┐
        │ Query Preprocessing                                   │
        │ 1. Generate embedding vector (embedding API)          │
        │ 2. Extract keywords (tokenize, stem, remove stopwords)│
        └──────────┬───────────────────────────────────────────┘
                   │
                   v
        ┌──────────────────────┐     ┌──────────────────────┐
        │ Vector Search        │     │ Keyword Search       │
        │ (pgvector <->)       │     │ (tsquery)            │
        │                      │     │                      │
        │ Returns: chunks with │     │ Returns: chunks with │
        │ cosine_distance      │     │ ts_rank              │
        └──────────┬───────────┘     └──────────┬───────────┘
                   │                            │
                   v                            v
        ┌──────────────────────────────────────────────────────┐
        │ Score Normalization                                   │
        │                                                     │
        │ vector_score = 1 - cosine_distance                   │
        │   → normalized to [0, 1]                             │
        │                                                     │
        │ keyword_score = ts_rank / max_possible_rank          │
        │   → normalized to [0, 1]                             │
        └──────────────────────┬───────────────────────────────┘
                               │
                               v
        ┌──────────────────────────────────────────────────────┐
        │ Weighted Fusion                                      │
        │                                                     │
        │ combined_score = 0.7 * vector_score                  │
        │                 + 0.3 * keyword_score                │
        │                                                     │
        │ Results sorted by combined_score DESC                │
        │ LIMIT applied after dedup (same chunk may appear     │
        │ in both result sets)                                 │
        └──────────────────────┬───────────────────────────────┘
                               │
                               v
                        Top-K Results

Full-text search setup:

    -- Add tsvector column to document_chunk
    ALTER TABLE ai.document_chunk ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (to_tsvector('english', chunk_text)) STORED;

    -- GIN index for fast full-text search
    CREATE INDEX idx_document_chunk_fts ON ai.document_chunk
        USING GIN (search_vector);

    -- Keyword search query
    SELECT
        c.chunk_id,
        c.chunk_text,
        ts_rank(c.search_vector, query) AS keyword_score
    FROM ai.document_chunk c,
         plainto_tsquery('english', :query_text) AS query
    WHERE c.search_vector @@ query
      AND c.status = 'active';

Configurable weights per search type:

| Search Type | Vector Weight | Keyword Weight | Use Case |
|---|---|---|---|
| Semantic search | 0.9 | 0.1 | General knowledge retrieval |
| Exact match | 0.3 | 0.7 | Code search, product lookup |
| Default hybrid | 0.7 | 0.3 | Balanced retrieval |
| Keyword only | 0.0 | 1.0 | Legacy search, debugging |

Trade-off: Weighted fusion (linear combination) is simpler and more predictable than
reciprocal rank fusion (RRF) or learning-to-rank (LTR). The trade-offs:

- Weighted fusion assumes scores are normalized and weights are static. RRF is rank-based
  and does not require score normalization, but it is less interpretable and harder to tune.
- LTR provides the best accuracy but requires training data and a serving infrastructure
  (e.g., ONNX runtime). For an initial implementation, weighted fusion with tunable weights
  provides 90% of the benefit at 10% of the complexity.
- The weights are configurable per search type and can be evolved over time. A/B testing
  infrastructure (future) can determine optimal weights empirically.

## 8.14 Metadata Filtering

Metadata filtering can happen before or after vector search.

| Strategy | Order | Performance | Recall | Use Case |
|---|---|---|---|---|
| Pre-filter | Filter → Vector search | Faster for selective filters | May miss relevant results if filter is too restrictive | Tenant ID, user ID, document type |
| Post-filter | Vector search → Filter | Consistent query time | Preserves all vector results | Tags, page numbers, sections |

    Pre-filter (default when selectivity > 50%):

        ┌──────────────┐
        │ Query        │
        │ {tags: tech} │
        └──────┬───────┘
               v
        ┌──────────────────┐
        │ Filter metadata  │
        │ (GIN index)      │
        │                  │
        │ Result: matching │
        │ embedding_ids    │
        └──────┬───────────┘
               v
        ┌──────────────────┐
        │ Vector search    │
        │ on filtered set  │
        │ (HNSW index)     │
        └──────┬───────────┘
               v
        ┌──────────────────┐
        │ Ranked results   │
        └──────────────────┘

    Post-filter (default when selectivity ≤ 50%):

        ┌──────────────┐
        │ Query        │
        │ {tags: tech} │
        └──────┬───────┘
               v
        ┌──────────────────┐
        │ Vector search    │
        │ (HNSW index)     │
        │                  │
        │ Result: top-100  │
        │ by similarity    │
        └──────┬───────────┘
               v
        ┌──────────────────┐
        │ Filter metadata  │
        │ (in-memory or    │
        │ JSONB filter)    │
        │                  │
        │ Result: filtered │
        │ ranked results   │
        └──────┬───────────┘
               v
        ┌──────────────────┐
        │ Re-rank results  │
        └──────────────────┘

When to use each strategy:

    -- Pre-filter example (user-specific memory search)
    SELECT * FROM ai.memory_embedding
    WHERE metadata @> '{"user_id": "abc-123"}'       -- pre-filter: 99% selectivity
    ORDER BY vector <-> :query_vector
    LIMIT 10;

    -- Post-filter example (tagged document search)
    SELECT * FROM (
        SELECT * FROM ai.document_embedding
        ORDER BY vector <-> :query_vector
        LIMIT 100                                     -- over-fetch 100
    ) sub
    WHERE sub.metadata @> '{"tags": ["technical"]}'   -- post-filter
    LIMIT 10;

The `QueryHandler` in the application layer decides the strategy based on an estimate of
filter selectivity. The heuristic:

    if estimated_filter_selectivity > 0.5:
        use_pre_filter()
    else:
        use_post_filter()

Selectivity is estimated from:
- Previous query statistics (cached in Redis with 1h TTL).
- For simple metadata filters (user_id, tenant_id), selectivity is known statically
  (e.g., user_id filters typically reduce result set by 99%+).
- For complex filters (tags, date ranges), selectivity is unknown and post-filter is the
  safe default (over-fetch then filter).

Trade-off: Pre-filter can produce zero results if the filter is too restrictive (even
though there are relevant results just outside the filtered set). Post-filter avoids this
but requires over-fetching (LIMIT query * 10) and may miss results beyond the over-fetch
limit. The 50% selectivity threshold is a heuristic that balances both concerns. Future
versions may implement a two-pass strategy: try pre-filter, if results < limit, retry
with post-filter.

## 8.15 Chunk Size Strategy

Chunk size determines the granularity of embedding and search retrieval.

| Chunk Size | Use Case | Retrieval Quality | Storage Cost | Embedding API Cost |
|---|---|---|---|---|
| 256 tokens | Code snippets, technical documentation | High precision, low recall | High (4x chunks) | High (4x API calls) |
| 512 tokens | General prose, emails (default) | Balanced | Baseline | Baseline |
| 768 tokens | Long-form documents, reports | Low precision, high recall | Low (0.67x chunks) | Low (0.67x API calls) |
| 1024 tokens | Legal documents, contracts | Lowest precision, highest recall | Lowest (0.5x chunks) | Lowest (0.5x API calls) |

Chunk size is configurable per document type:

    CREATE TABLE ai.chunk_strategy_config (
        strategy_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        document_type   VARCHAR(64) NOT NULL UNIQUE,
        chunk_size      INTEGER NOT NULL DEFAULT 512,
        overlap_size    INTEGER NOT NULL DEFAULT 64,
        active          BOOLEAN NOT NULL DEFAULT true,
        created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT valid_chunk_size CHECK (chunk_size BETWEEN 256 AND 1024),
        CONSTRAINT valid_overlap CHECK (overlap_size >= 0 AND overlap_size < chunk_size)
    );

Default strategy: 512 tokens. This is the industry-standard default for semantic search
because:
- 512 tokens is approximately one page of text — a natural semantic unit.
- It fits comfortably within the 8191-token context limit of text-embedding-3-small/large.
- It provides sufficient context for the embedding model to capture meaning while being
  small enough to isolate specific topics within a document.

Trade-off: Smaller chunks (256) provide higher precision (each chunk covers one specific
topic) but increase the number of API calls by 4x and storage by 4x. For code
documentation where exact function-level retrieval matters, the higher cost is justified.
For general prose, 512 tokens balances precision, recall, and cost.

## 8.16 Chunk Overlap Strategy

Overlap prevents information loss at chunk boundaries. Without overlap, a sentence or
concept that straddles the boundary between chunk N and chunk N+1 would be split, and
both chunks would lose the context of the other half.

| Overlap | Percentage (of 512) | Context Preservation | Storage Overhead |
|---|---|---|---|
| 0 tokens | 0% | None — boundary information lost | 0% |
| 32 tokens | 6.25% | Minimal — preserves phrase boundaries | 6.25% |
| 64 tokens | 12.5% | Good — preserves sentence boundaries (default) | 12.5% |
| 128 tokens | 25% | Excellent — preserves paragraph boundaries | 25% |
| 256 tokens | 50% | Maximum context preservation | 50% |

Default overlap: 64 tokens (12.5% of 512-token chunk).

    Chunk boundaries with overlap:

        Document: "The quick brown fox jumps over the lazy dog. The dog was not amused."

        No overlap (overlap=0):
            Chunk 1: "The quick brown fox jumps over the lazy dog. The"
            Chunk 2: "dog was not amused."
            ^ The dog reference in Chunk 2 has no context from Chunk 1.

        With overlap (overlap=8 tokens):
            Chunk 1: "The quick brown fox jumps over the lazy dog. The"
            Chunk 2: "over the lazy dog. The dog was not amused."
            ^ Both chunks contain the boundary sentence, preserving context.

Overlap text is duplicated across adjacent chunks. This means the same text appears in
multiple chunks and therefore generates multiple embedding vectors. At search time, the
same text may match multiple chunks, but the application layer deduplicates by chunk_id
after scoring.

Trade-off: Overlap increases API calls and storage by the overlap percentage (12.5% for
the default). The benefits far outweigh the costs:
- Without overlap, search for concepts that fall on chunk boundaries would consistently
  miss relevant results (false negatives).
- The 12.5% overhead is predictable and bounded.
- Dedup at the result layer (ranking highest score per chunk_id) is a trivial O(n)
  operation on the result set.

## 8.17 Future Embedding Models

The architecture anticipates evolution beyond single-vector-per-chunk embeddings.

| Future Model Type | Requirement | Design Change | Complexity |
|---|---|---|---|
| Multi-vector (ColBERT) | Multiple vectors per chunk (token-level) | embedding_type column discriminates single vs multi-vector; separate table ai.document_embedding_multi for per-token embeddings | High |
| Late interaction (ColBERT-v2) | Store per-token embeddings + interaction at query time | Same as multi-vector + compute-intensive search pipeline | Very high |
| Multi-modal (text + image) | Embeddings for image chunks alongside text chunks | embedding_type = 'image' column; separate vector index for image embeddings | Medium |
| Sparse embeddings (SPLADE) | Sparse lexical vectors | Alternative storage in ai.document_embedding_sparse (JSONB of token-weight pairs) | Medium |

Design for extensibility — adding embedding_type column:

    ALTER TABLE ai.document_embedding
    ADD COLUMN embedding_type VARCHAR(20) NOT NULL DEFAULT 'dense';

    Embedding type values:
    - 'dense': Standard dense vector (current)
    - 'sparse': Sparse lexical vector (future)
    - 'multi': Multi-vector (future, ColBERT)
    - 'image': Image embedding (future)

    ALTER TABLE ai.document_embedding
    ADD COLUMN vector_count INTEGER NOT NULL DEFAULT 1;

    -- For multi-vector: one row per embedding with embedding_type='multi'
    -- vector column stores one token-level vector
    -- vector_count indicates total vectors per chunk (for reconstruction)

Alternative approach — separate tables per embedding type:

    ai.document_embedding_dense    (current schema)
    ai.document_embedding_sparse   (sparse lexical, JSONB token-weight pairs)
    ai.document_embedding_multi    (multi-vector, one row per token vector)
    ai.document_embedding_image    (image embeddings, references image chunk)

| Approach | Pros | Cons |
|---|---|---|
| Single table with type column | Simple schema evolution; unified query path | Mixed-dimension vectors in same table; nullable type-specific columns |
| Separate tables per type | Type-specific schema; independent indexing | Schema proliferation; query must union across tables |

Recommendation: Start with single table + embedding_type column. If multi-model
embeddings become the dominant use case, migrate to separate tables. The embedding_type
column in the DDL above is a zero-cost option (defaults to 'dense') that keeps the
migration path open without committing to a full polymorphic schema.

Trade-off: The single-table approach with embedding_type requires application-level
routing (query which table/index based on type). Separate tables require application-level
union queries. The trade-off is between schema complexity (fewer tables, more nullable
columns) and query complexity (fewer columns, more tables). For the initial release,
single-table is preferred because embedding models beyond dense vectors are not yet in
use, and the application layer is simpler with one query path.


 