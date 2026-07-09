from application.di.container import container
from application.prompts.registry import PromptRegistry
from infrastructure.llm.litellm_client import LiteLLMClient


class ConfirmationHandler:
    def __init__(self, llm: LiteLLMClient, prompt_registry: PromptRegistry | None = None):
        self.llm = llm
        self.prompt_registry = prompt_registry or container.resolve(PromptRegistry)

    async def generate_confirmation_summary(self, details: dict) -> str:
        prompt = await self.prompt_registry.render(
            "meeting.confirmation",
            {
                "details": details,
            }
        )
        return await self.llm.generate(
            system_prompt="You are a confirmation assistant. Summarize details clearly.",
            user_prompt=prompt,
            temperature=0.3,
            max_tokens=500,
        )

    def parse_confirmation_response(self, response: str) -> dict:
        response_lower = response.lower().strip()
        if "cancel" in response_lower:
            return {"action": "cancel"}
        if "edit" in response_lower or "change" in response_lower or "update" in response_lower:
            return {"action": "edit"}
        if "confirm" in response_lower or "yes" in response_lower or "correct" in response_lower:
            return {"action": "confirm"}
        return {"action": "unknown"}
