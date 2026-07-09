# ADR-002: Lead Scoring System Unification

## Status
Proposed

## Context
The PRD contains **two conflicting lead scoring systems**:

### System A — FR-5 (Functional Requirements)
- 4 scoring factors: Company (0.3), Phone (0.2), Meeting Purpose Detail (0.3), Notes Length > 50 chars (0.2)
- Binary threshold: Score >= 0.5 = qualified
- Total possible: 1.0

### System B — Section 25 (Lead Qualification Policy)
- 8 scoring factors with different weights: Company (0.20), Phone (0.10), Meeting Purpose Detail (0.20), Meeting Requested (0.15), Technical Requirements (0.10), Decision Maker Signal (0.10), Industry Relevance (0.05), Urgency Signal (0.10)
- Three-grade system: Hot (>= 0.7), Warm (0.5–0.69), Cold (< 0.5)
- Total possible: 1.0

These conflict on: number of factors, individual weights, and grading scheme.

## Decision
Adopt **Section 25's system** as the canonical lead scoring model. Update FR-5 to reference Section 25 instead of defining its own scoring.

### Rationale
1. Section 25 is more comprehensive (8 factors vs. 4)
2. Three-grade system (Hot/Warm/Cold) provides better prioritization than binary qualification
3. Factors like "Decision Maker Signal" and "Urgency" are valuable for sales prioritization
4. FR-5's binary system loses information that Section 25 preserves

### Mapping FR-5 Factors to Section 25
| FR-5 Factor | Section 25 Equivalent | Notes |
|-------------|----------------------|-------|
| Company presence (0.3) | Company Presence (0.20) | Weight adjusted |
| Phone provided (0.2) | Phone Provided (0.10) | Weight adjusted |
| Meeting purpose detail (0.3) | Meeting Purpose Detail (0.20) | Weight adjusted |
| Notes length > 50 chars (0.2) | (No direct equivalent) | Absorbed into "Technical Requirements" + "Urgency Signal" |

### Implementation
- Lead score is calculated using Section 25.1's weighted formula
- Lead grade is determined using Section 25.2's grade bands
- `BR-028` threshold changes from ">= 0.5" to ">= 0.7 (Hot) or >= 0.5 (Warm)"
- `BR-029` actions are mapped per grade (Hot = immediate notify, Warm = daily digest, Cold = weekly digest)

## Consequences
- FR-5 must be updated to reference Section 25 as the canonical source
- Implementation team builds one scoring system, not two
- Existing `QualifyLeadTool` in code must be updated to 8-factor model
- Lead grading enables more nuanced notification routing

## References
- PRD FR-5: Current lead scoring definition
- PRD Section 25: Enhanced lead qualification policy
- PRD BR-028: Lead qualification threshold
- PRD BR-029: Qualified lead actions
- PRD Section 27: Conversation Analytics (lead conversion metrics)
