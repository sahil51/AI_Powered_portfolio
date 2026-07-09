# ADR-004: Intent Classification Confidence Measurement

## Status
Proposed

## Context
PRD **FR-1 (Intent Classification)** requires:
> "Accuracy: >90% classification accuracy on known intents"
> "Fallback: If confidence is low, ask clarifying question"

But the PRD does not define **how confidence is measured**. LLM-based classification via LiteLLM returns a string label, not a probability distribution. The system has no mechanism to distinguish between "high confidence 'schedule_meeting'" and "low confidence 'schedule_meeting'."

## Decision
Implement a **two-stage confidence measurement** strategy:

### Stage 1: Logit-Based Confidence (Primary)
Use the LLM's log probabilities (if available from the provider):
- Request `logprobs=True` in the LiteLLM completion call
- Extract the probability of the top token for the intent label
- Map: logprob > -0.5 → high confidence, logprob -0.5 to -2.0 → medium, logprob < -2.0 → low

### Stage 2: Semantic Confidence (Fallback)
For providers that don't return logprobs (e.g., HuggingFace router), use a secondary check:
- After the LLM returns an intent label, send a second verification prompt:
  "On a scale of 0.0 to 1.0, how confident are you that the user's intent is [label]? Return only a number."
- Parse the float response as confidence

### Confidence Thresholds
| Confidence Level | Score Range | Action |
|-----------------|-------------|--------|
| High | >= 0.85 | Accept intent, proceed with workflow |
| Medium | 0.50 – 0.84 | Accept intent, but add clarifying confirmation in response |
| Low | < 0.50 | Reject intent, ask clarifying question instead |

### Cache
- Intent + message hash → confidence mapping cached in Redis for 1 hour
- Same message from different users still triggers classification (context-dependent)

## Consequences
- Logprob-based confidence is more accurate but only available for some providers
- Semantic verification adds ~1 LLM call per ambiguous classification
- Medium confidence adds a confirmation step but doesn't block the workflow
- This enables the ">90% accuracy" target to be measured

## References
- PRD FR-1: Intent classification requirements
- PRD AC-1: Acceptance criteria for intent classification
- PRD Section 10.1: "Ask clarifying questions" behavioral rule
- PRD Section 12.6: Fallback rate metric
