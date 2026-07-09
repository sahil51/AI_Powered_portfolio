# ADR-007: Redis Fault Tolerance and Degraded Mode Strategy

## Status
Proposed

## Context
PRD **Section 7.8 (Fault Tolerance)** states:
> "Redis failure: Short-term memory degraded; long-term memory still works via PostgreSQL"

However, Redis is used for **6 critical functions**, not just short-term memory:
1. Short-term conversation state
2. Rate limiting counters
3. Idempotency cache
4. Distributed locks (conversation concurrency)
5. Celery broker (task queue)
6. Celery result backend

A Redis outage takes down all 6 simultaneously. The PRD's "short-term memory degraded" significantly understates the impact.

## Decision
Implement a **three-tier degraded mode** based on Redis availability:

### Tier 1: Redis Fully Operational (Normal)
All 6 functions active. Full performance.

### Tier 2: Redis Partially Degraded (Cache miss, connection intermittent)
- Rate limiting: Fall back to in-process token bucket (per-worker, approximate)
- Idempotency: Bypass idempotency check (accept risk of duplicate)
- Distributed locks: Bypass locks; accept race condition risk
- Short-term memory: Use PostgreSQL as fallback (slower but functional)
- Celery broker: Critical — if Redis broker is down, Celery tasks fail immediately
- Log warning: "Redis degraded — idempotency and rate limiting bypassed"

### Tier 3: Redis Fully Unavailable
- Short-term memory: Use PostgreSQL `conversations` table directly (slow, no TTL-based cleanup)
- Rate limiting: In-process token bucket only (per-worker, no global limit)
- Idempotency: Bypassed (log all requests for manual dedup)
- Distributed locks: Bypassed (workers coordinate via PostgreSQL row-level locks)
- Celery: **Non-functional.** Meeting scheduling, notifications, embeddings all fail synchronously with user-facing error
- Return degraded response for scheduling endpoints: "Scheduling is temporarily unavailable. Please try again later."

### Recovery
- Redis health is checked every 10 seconds (via `/health/ready` or background task)
- When Redis recovers, services return to Tier 1 automatically
- Celery workers restart on Redis recovery (Docker health check)

### Celery Broker Redundancy (Future)
- Add RabbitMQ as secondary broker in v2
- Celery supports broker fallback natively
- For v1, document that Redis broker is a single point of failure for async tasks

## Consequences
- Tier 2 (partial degradation) is transparent to most users
- Tier 3 (full Redis outage) breaks async scheduling but keeps chat functional
- Celery-dependent features (meetings, notifications) are unavailable during Tier 3
- Rate limiting is approximate during degradation (per-worker, not global)
- PRD Section 7.8's "short-term memory degraded" is updated to reflect the full impact

## References
- PRD Section 7.8: Fault tolerance requirements
- PRD Section 7.3: Availability targets (99.9%)
- PRD Section 28.1: Redis scaling
- PRD Section 4.6: Failure Journey
- Celery documentation on broker redundancy
