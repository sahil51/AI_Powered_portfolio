Extract structured entities from the user's message.

User Message: {{message}}
User Context: {{context}}
Detected Intent: {{intent}}

Extract the following fields if present:
- person_name: Full name of any person mentioned
- company: Company or organization name
- email: Email address
- phone: Phone number
- date: Date mentioned (YYYY-MM-DD format)
- time: Time mentioned (HH:MM format)
- timezone: Timezone if mentioned
- duration: Duration in minutes
- meeting_type: Type of meeting (e.g., video_call, phone, in_person)
- priority: Priority level (high, medium, low)
- tags: Comma-separated list of tags
- workflow_parameters: JSON object of workflow parameters

Return the result as a valid JSON object with only the fields that have values.
If no entities are found, return an empty JSON object: {}
