from tools.base import BaseTool


class CreateCalendarEventTool(BaseTool):
    name = "create_calendar_event"
    description = "Create a calendar event. Delegates to n8n for actual execution."

    async def execute(self, meeting_details: dict) -> dict:
        return {"delegated": True, "workflow": "n8n/calendar/create_event"}
