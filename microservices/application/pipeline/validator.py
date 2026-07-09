from __future__ import annotations

from application.pipeline.models import PipelineContext


class PipelineValidator:
    def validate(self, ctx: PipelineContext) -> list[str]:
        errors: list[str] = []
        if not ctx.conversation_id or not ctx.conversation_id.strip():
            errors.append("conversation_id is required")
        if not ctx.user_id or not ctx.user_id.strip():
            errors.append("user_id is required")
        if not ctx.prompt_name or not ctx.prompt_name.strip():
            errors.append("prompt_name is required")
        if ctx.max_tokens is not None and ctx.max_tokens < 1:
            errors.append("max_tokens must be >= 1")
        if ctx.temperature is not None and (ctx.temperature < 0.0 or ctx.temperature > 2.0):
            errors.append("temperature must be between 0.0 and 2.0")
        if ctx.top_p is not None and (ctx.top_p < 0.0 or ctx.top_p > 1.0):
            errors.append("top_p must be between 0.0 and 1.0")
        return errors
