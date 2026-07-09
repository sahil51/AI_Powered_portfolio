from __future__ import annotations

from application.ai.models import Usage


class LiteLLMTokenCounter:
    def __init__(self) -> None:
        self._approx_chars_per_token = 4.0

    async def count_tokens(self, text: str, model: str | None = None) -> int:
        try:
            import litellm
            return litellm.token_counter(model=model or "", text=text)
        except Exception:
            return self.estimate_tokens(text)

    async def estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        return int(len(text) / self._approx_chars_per_token) + 1

    def estimate_cost(self, model: str, usage: Usage) -> float:
        try:
            import litellm
            result = litellm.cost_per_token(
                model=model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
            )
            if isinstance(result, tuple):
                return float(result[0] + result[1])
            return float(result)
        except Exception:
            return self._rough_cost_estimate(model, usage)

    def _rough_cost_estimate(self, model: str, usage: Usage) -> float:
        if "gemini" in model.lower():
            input_rate = 0.10 / 1_000_000
            output_rate = 0.40 / 1_000_000
        elif "cerebras" in model.lower():
            input_rate = 0.10 / 1_000_000
            output_rate = 0.30 / 1_000_000
        elif "nvidia" in model.lower():
            input_rate = 0.20 / 1_000_000
            output_rate = 0.60 / 1_000_000
        else:
            input_rate = 0.15 / 1_000_000
            output_rate = 0.50 / 1_000_000
        return (usage.prompt_tokens * input_rate) + (usage.completion_tokens * output_rate)
