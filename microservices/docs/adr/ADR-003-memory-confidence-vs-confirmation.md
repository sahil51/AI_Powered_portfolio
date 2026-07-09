# ADR-003: Memory Confidence vs. Explicit Confirmation Resolution

## Status
Proposed

## Context
There is a conflict between two PRD requirements:

**Section 20.3 (Memory Update Policy):**
> "High (>= 0.8) — Save automatically to both short-term and long-term memory. No confirmation needed."

**BR-033 (Business Rule):**
> "User identity (name, email) SHALL only be saved after explicit user confirmation."

If a user says "My email is john@example.com" (confidence 0.9 per Section 20.2), Section 20.3 says auto-save, but BR-033 says require confirmation.

## Decision
Introduce a **data classification layer** that separates identity fields from preference fields. Each classification has different memory update rules.

### Data Classification

| Classification | Fields | Auto-Save (High Confidence) | Requires Confirmation |
|---------------|--------|----------------------------|----------------------|
| **Identity** | name, email, phone | No | Always |
| **Business** | company, company_address | Yes (>= 0.8) | No |
| **Preference** | timezone, meeting_type, preferred_time | Yes (>= 0.8) | No |
| **History** | past meetings, summaries | Yes (always) | No |

### Updated Rule
- **BR-033** remains: Identity fields always require confirmation
- **Section 20.3** applies to: Business and Preference fields only
- **Section 20.2 confidence scoring** applies to: All fields for the scoring mechanism, but identity scoring is only used to determine *what to ask*, not *whether to save*

### Example Flow
User says: "My email is john@example.com and I'm usually free evenings"
1. Email (identity) → Confidence 0.9 → Ask confirmation: "Should I save your email for next time?"
2. Preferred time (preference) → Confidence 0.5 (medium) → Ask: "Should I remember you prefer evenings?"
3. Company (business) → No data yet → Do nothing

## Consequences
- BR-033 supersedes Section 20.3 for identity data only
- Section 20.3 applies unchanged for business and preference data
- Implementation team adds data classification to the memory service
- User experience is not degraded — they see confirmation only for sensitive fields

## References
- PRD Section 20.3: Memory update policy by confidence
- PRD BR-033: Identity fields require confirmation
- PRD Section 9.1: Short-term and long-term memory classification
- PRD BR-034: User preferences updated only when explicitly stated or confirmed
