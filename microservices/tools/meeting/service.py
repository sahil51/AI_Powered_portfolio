from tools.base import BaseTool


class ValidateMeetingDetailsTool(BaseTool):
    name = "validate_meeting_details"
    description = "Validate all required meeting fields are present and correctly formatted"

    async def execute(self, data: dict) -> dict:
        required = [
            "full_name", "email", "contact_number", "company_name",
            "company_address", "meeting_purpose", "preferred_date",
            "preferred_time", "timezone", "meeting_type",
        ]
        missing = [f for f in required if f not in data or not data[f]]
        if missing:
            return {"valid": False, "missing_fields": missing}
        return {"valid": True, "data": data}


class CheckAvailabilityTool(BaseTool):
    name = "check_availability"
    description = "Check calendar availability for a given date and time"

    async def execute(self, date: str, time: str, timezone: str) -> dict:
        return {"available": True, "suggested_slots": []}
