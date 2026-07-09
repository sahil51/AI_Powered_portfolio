import httpx

from config.settings import settings
from monitoring.logger import logger


class N8NWebhookClient:
    def __init__(self):
        self.base_url = settings.n8n_webhook_base_url
        self.meeting_webhook_url = settings.n8n_meeting_webhook_url
        self.client = httpx.AsyncClient(timeout=30)

    async def trigger_workflow(self, workflow_name: str, payload: dict) -> dict:
        if workflow_name == "meeting/schedule" and self.meeting_webhook_url:
            url = self.meeting_webhook_url
        else:
            url = f"{self.base_url}/{workflow_name}"
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"n8n workflow '{workflow_name}' triggered successfully", extra={"payload": payload})
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"n8n workflow '{workflow_name}' failed: {e}", extra={"payload": payload})
            raise

    async def close(self):
        await self.client.aclose()
