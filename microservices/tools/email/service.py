from tools.base import BaseTool


class SendEmailTool(BaseTool):
    name = "send_email"
    description = "Send an email. Delegates to n8n for actual execution."

    async def execute(self, to: str, subject: str, body: str) -> dict:
        return {"delegated": True, "workflow": "n8n/email/send"}
