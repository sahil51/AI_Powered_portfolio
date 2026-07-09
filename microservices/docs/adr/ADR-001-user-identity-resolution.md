# ADR-001: User Identity Resolution Strategy

## Status
Proposed

## Context
PRD Sections **9 (Memory System)**, **FR-4 (Memory Management)**, and **4.4 (Returning User Journey)** require the system to "remember returning users" and "pre-fill known information." However, no mechanism is defined for **how the system identifies a returning user**.

The entire memory system depends on associating conversations with a user identity. Without a resolution strategy:
- Short-term memory cannot be retrieved across sessions
- Long-term memory has no lookup key
- "Welcome back, John!" is impossible
- Lead deduplication by email (`BR-030`) cannot function on first message

## Decision
Implement a **layered identity resolution** strategy with the following priority:

### Layer 1: JWT Token (Existing Auth)
If the Django frontend passes a JWT token (from an authenticated Django session), extract `sub` (user ID) and `email` claims. This provides deterministic identity.

### Layer 2: Session-Scoped Anonymous ID
If no JWT is present, the Django chat widget SHALL generate a UUID on first widget load and store it in `localStorage`. This UUID is sent as `X-Session-ID` header with every message. The API uses this as a weak identity for short-term memory only.

### Layer 3: Email-Based Recognition
If the user provides their email during conversation (at any point), the system SHALL:
1. Look up the email in PostgreSQL long-term memory
2. If found, merge the session-scoped anonymous ID with the known user profile
3. If not found, create a new user profile

### Identity Hierarchy
```
JWT (deterministic) > Email match (verified) > Session UUID (weak)
```

### When Identity Takes Effect
- Short-term memory: Available immediately with Session UUID
- Long-term memory (read): Available only after Layer 1 or Layer 3
- Long-term memory (write): Available after Layer 1 or Layer 3 with high confidence
- "Welcome back" greeting: Only after Layer 1 or Layer 3 confirmed

## Consequences
- Returning users without JWT or email are treated as new visitors for long-term memory
- Users who provide email mid-conversation get seamless identity merge
- Django frontend must implement `X-Session-ID` header generation
- No PII is stored in session UUID

## References
- PRD Section 9.1: Short-term and Long-term memory definition
- PRD Section 4.4: Returning User Journey
- PRD FR-4: Memory Management requirements
- PRD BR-030: Lead deduplication by email
- PRD BR-038: Returning users greeted with name and context
