from application.di.container import container
from application.prompts.registry import PromptRegistry
from domain.enums.intent import IntentType
from infrastructure.llm.litellm_client import LiteLLMClient


class IntentClassifier:
    def __init__(self, llm: LiteLLMClient, prompt_registry: PromptRegistry | None = None):
        self.llm = llm
        self.prompt_registry = prompt_registry or container.resolve(PromptRegistry)

    async def classify(self, message: str, user_type: str, context: str = "") -> IntentType:
        prompt = await self.prompt_registry.render(
            "classification.intent",
            {
                "user_type": user_type,
                "message": message,
                "context": context,
            }
        )
        try:
            result = await self.llm.generate(
                system_prompt="You are an intent classifier. Return only the intent label.",
                user_prompt=prompt,
                temperature=0.1,
                max_tokens=50,
            )
            result = result.strip().lower()
            return IntentType(result)
        except ValueError:
            return IntentType.UNKNOWN
        except Exception:
            return IntentType.UNKNOWN
