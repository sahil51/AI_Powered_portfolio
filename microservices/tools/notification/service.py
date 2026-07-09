from tools.base import BaseTool


class SendNotificationTool(BaseTool):
    name = "send_notification"
    description = "Send notification to Sahil about a new meeting or lead. Delegates to n8n."

    async def execute(self, notification_type: str, data: dict) -> dict:
        return {"delegated": True, "workflow": f"n8n/notifications/{notification_type}"}
