# ADR-005: Idle Timeout and Short-Term Memory TTL Reconciliation

## Status
Proposed

## Context
Two PRD sections define different time-based behaviors for conversation state:

**Section 9.1 (What to Remember):**
> "Short-term memory expires after 24 hours"

**Section 21.4 (Timeout Handling):**
> 5 min inactivity → "Are you still there?"
> 15 min inactivity → Save current state; mark as idle
> 30 min inactivity → Archive conversation; clear short-term state
> 24h since last message → Short-term memory expired

The conflict: Section 21.4 says short-term state is "cleared" after 30 minutes of inactivity, but Section 9.1 says it "expires after 24 hours." These are different guarantees.

## Decision
Introduce a **two-phase short-term memory lifecycle**:

### Phase 1: Active Window (0–30 min inactivity)
- Full conversation state in Redis
- User can resume instantly with full context
- State machine is in GREETING or active workflow state
- "Are you still there?" warning at 5 min

### Phase 2: Archived Window (30 min – 24h inactivity)
- Conversation is **archived**: Redis state is compressed into a summary and moved to PostgreSQL long-term
- Raw Redis state is **cleared** (to free memory)
- User returning during this window gets: "Welcome back! It seems we left off discussing [summary]."
- State machine starts fresh but with memory context injected
- Workflow state (if mid-meeting) is preserved in PostgreSQL with a "paused" status

### Phase 3: Expired (after 24h of archive)
- Long-term summary remains in PostgreSQL
- No special greeting about previous session
- Standard new conversation flow

### Redis TTL Settings
| Key Pattern | TTL | Contents |
|-------------|-----|----------|
| `conversation:{id}:state` | 30 min (sliding, reset on each message) | Full workflow state |
| `conversation:{id}:recent_messages` | 30 min (sliding) | Last 10 messages |
| `session:{user_id}` | 24h | Session metadata |
| `lock:workflow:{id}` | 30s | Distributed workflow lock |

### PostgreSQL Lifecycle
| Event | Action |
|-------|--------|
| Conversation archived (30 min idle) | Summary saved; state marked as "archived" |
| User returns within 24h | "archived" → "active"; summary loaded as context |
| User returns after 24h | New conversation; previous summary available for reference |
| Conversation completes normally | Final summary saved; state marked as "completed" |

## Consequences
- Short-term memory (Redis) is freed after 30 min, not 24h
- Long-term memory (PostgreSQL) stores archival summaries indefinitely
- Returning users within 24h get context-aware greetings
- Returning users after 24h start fresh but with previous summary accessible

## References
- PRD Section 9.1: Short-term memory TTL definition
- PRD Section 21.4: Timeout handling rules
- PRD BR-006: Idle conversation timeout
- PRD BR-035: Short-term memory expiration
- PRD Section 4.4: Returning User Journey
