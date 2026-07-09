# ADR-008: Meeting Field Collection — Ordered vs. Unordered Strategy

## Status
Proposed

## Context
PRD **Section 8.1 (Google Meet Workflow)** lists 9 meeting fields in a numbered order:
```
1. full_name
2. email
3. contact_number
4. company_name
5. company_address
6. meeting_purpose
7. preferred_date
8. preferred_time
9. timezone
```

However, **FR-3** says "Collection: One field at a time, natural conversation." And **Section 4.2 (Recruiter Journey)** shows: "Assistant collects: Name, Email, Phone, Company, Role, Preferred Date/Time" — a different order.

The PRD does not specify whether the field order is:
- **Strict** (must ask in this exact sequence)
- **Preferred** (ask in this order if user hasn't volunteered any)
- **Suggested** (any order is fine)

This ambiguity affects implementation of the meeting collector agent.

## Decision
Adopt a **flexible collection strategy** with three modes:

### Mode 1: User-Initiated (Preferred)
- If the user volunteers multiple fields in one message (e.g., "I'm John from Acme, my email is john@acme.com"), extract all found fields
- Ask only for remaining missing fields
- This is the "natural conversation" requirement from FR-3

### Mode 2: Ordered Fallback (Default)
- If the user has not volunteered any field, use the Section 8.1 order as the default asking sequence
- Rationale: email first enables identity lookup (see ADR-001), meeting_type last (user needs context to decide)

### Mode 3: Smart Reordering
- If the user has provided `user_type = recruiter`, prioritize `company_name` and `meeting_purpose` (recruiters care about role context)
- If `user_type = client`, prioritize `company_name` and `company_address` (business context)
- This adapts to persona needs without changing the required field set

### Field Determination Algorithm
```
collected = extract_from_message(user_message)
remaining = required_fields - collected

if len(remaining) == 0:
    proceed_to_validation()
elif len(remaining) == 1:
    ask_for(remaining[0])
else:
    next_field = smart_select(remaining, user_type, conversation_context)
    ask_for(next_field)
```

### Validation Timing
- Partial validation runs after each field (email format after email collected)
- Full validation runs only when all 9 fields are collected

## Consequences
- Users who provide all fields at once skip the entire collection flow
- Users who provide nothing get the ordered fallback
- Persona-based reordering reduces friction for common paths
- Implementation is more complex than strict ordering, but delivers a natural conversation experience

## References
- PRD Section 8.1: Google Meet workflow with field order
- PRD FR-3: Meeting scheduling requirements
- PRD Section 10.1: "One field at a time" behavioral rule
- PRD Section 3.2, 3.3: Recruiter and Client persona needs
- PRD BR-012: All 10 required fields must be collected
