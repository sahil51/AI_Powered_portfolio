Analyze the user's reply to determine the type of confirmation response.

Conversation History: {{conversation_history}}
Current Intent: {{current_intent}}
Pending Questions: {{pending_questions}}
Pending Fields: {{pending_fields}}
User Reply: {{user_reply}}

Determine the confirmation type:
- positive: User agrees, confirms, says yes, okay, proceed, correct
- negative: User disagrees, says no, not that, incorrect
- partial: User confirms only part of the information
- modification: User requests changes to specific details
- correction: User corrects a specific piece of information
- cancellation: User wants to cancel the entire operation
- ambiguous: Reply is unclear or could have multiple meanings
- unknown: Cannot determine the confirmation type

Extract the following if present:
- confirmed_fields: Fields the user explicitly confirmed (comma-separated)
- modified_fields: Fields the user modified with new values (JSON object)
- corrected_field: The field being corrected
- corrected_value: The corrected value
- missing_fields: Fields still needed that remain unaddressed
- reason: Brief reason for the confirmation type determination
- suggested_follow_up: What information should be requested next

Return the result as a valid JSON object:
{
    "confirmation_type": "positive|negative|partial|modification|correction|cancellation|ambiguous|unknown",
    "confirmed_fields": [],
    "modified_fields": {},
    "corrected_field": null,
    "corrected_value": null,
    "missing_fields": [],
    "reason": "",
    "suggested_follow_up": ""
}
